"""Extended Bidirectional AI Harness Adapters (Read + Write, Zero-AI, Strict Protocol Validity).

Adds 6 popular modern AI Harnesses to bring Nexus Memory to 20 bidirectional targets:
1. WorkBuddy (Tencent WorkBuddy — `~/.workbuddy/workbuddy.db` + `sessions/<id>.jsonl`)
2. T3 Code (`pingdotgg/t3code` — `~/.t3/userdata/statev2.sqlite` + JSON thread export)
3. AWS Kiro (`~/.kiro/sessions/cli/<id>.jsonl` + `/chat save` JSON)
4. Sourcegraph Amp (`~/.local/share/amp/threads/<id>.json`)
5. ByteDance Trae / Trae Agent (trajectory `.json`)
6. Warp / Oz Agent (`~/.warp/sessions/<id>.json` portable agent session exchange)

Every writer enforces strict alternating user/assistant turns via `_coalesce_alternating_turns`,
preserves paired tool metadata without creating API `Invalid Params`, and records explicit
losses for anything retained only in `portable.json`.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .claude_code import _coalesce_alternating_turns
from .model import ConversationGraph, MessageNode, UsageSummary, content_text, extract_links


def _chain(raw_items: list[dict[str, Any]]) -> tuple[tuple[MessageNode, ...], tuple[str, ...], str | None]:
    """O(N) linear node chaining using a set for ID deduplication."""
    if not raw_items:
        return (), (), None
    nids: list[str] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(raw_items):
        nid = str(item.get("node_id") or f"ext-{idx}")
        if nid in seen_ids:
            nid = f"{nid}-{idx}"
        seen_ids.add(nid)
        nids.append(nid)

    total = len(raw_items)
    nodes: list[MessageNode] = []
    for idx, item in enumerate(raw_items):
        nid = nids[idx]
        prev_id = nids[idx - 1] if idx > 0 else None
        child_ids = (nids[idx + 1],) if idx + 1 < total else ()
        text = str(item.get("text") or "")
        nodes.append(
            MessageNode(
                node_id=nid,
                parent_id=prev_id,
                child_ids=child_ids,
                role=item.get("role"),
                text=text,
                timestamp=item.get("timestamp"),
                content=item.get("content", text),
                raw_record=item.get("raw_record", {}),
                event_type=item.get("event_type", "message"),
                parent_tool_use_id=item.get("parent_tool_use_id"),
                links=extract_links(text),
                usage=item.get("usage"),
                interrupted=bool(item.get("interrupted", False)),
            )
        )
    return tuple(nodes), (nids[0],), nids[-1]


def _links(nodes: tuple[MessageNode, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for n in nodes:
        for u in n.links:
            if u not in seen:
                seen.add(u)
                out.append(u)
    return tuple(out)


# ── 1. Tencent WorkBuddy (`~/.workbuddy/workbuddy.db` + `projects/*/*.jsonl` + `sessions/*.jsonl`) ──

_WB_USER_QUERY_RE = re.compile(r"<user_query>([\s\S]*?)</user_query>")
_WB_SYS_REMINDER_RE = re.compile(r"<system-reminder\b[^>]*>[\s\S]*?</system-reminder>\s*")


def _clean_workbuddy_user_text(text: str) -> tuple[str, bool]:
    """Extract clean user query from WorkBuddy `<user_query>` / `<system-reminder>` wrappers.

    Returns `(cleaned_text, is_compaction_summary)`.
    """
    if "<cb_summary>" in text and "<user_query>" not in text:
        return text.strip(), True
    m = _WB_USER_QUERY_RE.search(text)
    if m:
        return m.group(1).strip(), False
    cleaned = _WB_SYS_REMINDER_RE.sub("", text).strip()
    return cleaned, False


def parse_workbuddy_session(path: str | Path) -> ConversationGraph:
    """Read a WorkBuddy JSONL/JSON session file (both native `projects/<cwd>/<id>.jsonl` and `sessions/<id>.jsonl`)."""
    p = Path(path).expanduser()
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    raw_items: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"source_file": p.name}
    sid = p.stem
    title = ""
    workspace: str | None = None
    records: list[dict[str, Any]] = []

    if p.suffix == ".jsonl":
        for idx, ln in enumerate(text.splitlines()):
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if not isinstance(r, dict):
                continue
            records.append(r)
            rtype = str(r.get("type") or "")
            if rtype == "workbuddy_session_meta":
                sid = str(r.get("id") or sid)
                title = str(r.get("custom_title") or r.get("title") or title)
                workspace = r.get("cwd") or workspace
                for k in ("project_id", "project_name", "group_id", "group_title", "space_id", "model", "mode", "parent_session_id"):
                    if r.get(k) is not None:
                        meta[k] = r[k]
                if r.get("group_title") and not meta.get("section_name"):
                    meta["section_name"] = r["group_title"]
                if r.get("group_id") and not meta.get("section_id"):
                    meta["section_id"] = r["group_id"]
                continue
            if rtype == "session-meta":
                sid = str(r.get("sessionId") or r.get("id") or sid)
                workspace = r.get("cwd") or workspace
                continue
            if rtype == "ai-title":
                if r.get("aiTitle") and not title:
                    title = str(r["aiTitle"])
                workspace = r.get("cwd") or workspace
                continue
            if rtype == "function_call":
                workspace = r.get("cwd") or workspace
                cname = str(r.get("name") or "tool")
                cid = str(r.get("callId") or r.get("id") or f"wb-tc-{idx}")
                raw_items.append({
                    "node_id": str(r.get("id") or cid),
                    "role": "tool_call",
                    "text": f"tool:{cname}",
                    "timestamp": r.get("timestamp"),
                    "content": {"call_id": cid, "name": cname, "arguments": r.get("arguments", {})},
                    "raw_record": r,
                    "event_type": "tool_use",
                })
                continue
            if rtype == "function_call_output":
                workspace = r.get("cwd") or workspace
                cid = str(r.get("callId") or "")
                out_str = content_text(r.get("output", r.get("content", "")))
                raw_items.append({
                    "node_id": str(r.get("id") or f"wb-tr-{idx}"),
                    "role": "tool_result",
                    "text": out_str,
                    "timestamp": r.get("timestamp"),
                    "content": {"call_id": cid, "output": out_str},
                    "raw_record": r,
                    "event_type": "tool_result",
                })
                continue

            role = str(r.get("role") or (rtype if rtype in {"user", "assistant", "system", "tool_call", "tool_result"} else ""))
            if role in {"user", "assistant", "system", "tool_call", "tool_result"}:
                workspace = r.get("cwd") or workspace
                if isinstance(r.get("sessionId"), str) and r["sessionId"]:
                    sid = r["sessionId"]
                c = r.get("content", r.get("text", ""))
                extracted = content_text(c)
                ev_type = str(r.get("event_type") or ("tool_use" if role == "tool_call" else "message"))
                if role == "user":
                    cleaned, is_compaction = _clean_workbuddy_user_text(extracted)
                    if is_compaction:
                        role = "system"
                        ev_type = "compaction"
                        extracted = cleaned
                    elif cleaned:
                        extracted = cleaned
                    else:
                        # Pure empty system-reminder wrapper without user query
                        continue
                if not extracted.strip() and role in {"user", "assistant"}:
                    continue
                raw_items.append({
                    "node_id": str(r.get("id") or f"wb-{idx}"),
                    "role": role,
                    "text": extracted,
                    "timestamp": r.get("timestamp") or r.get("created_at"),
                    "content": c,
                    "raw_record": r,
                    "event_type": ev_type,
                    "parent_tool_use_id": r.get("parent_tool_use_id"),
                })
    else:
        obj = json.loads(text)
        if isinstance(obj, dict):
            sid = str(obj.get("id") or obj.get("sessionId") or sid)
            title = str(obj.get("custom_title") or obj.get("title") or title)
            workspace = obj.get("cwd")
            if obj.get("group_title"):
                meta["section_name"] = obj["group_title"]
            if obj.get("project_id"):
                meta["project_id"] = obj["project_id"]
            for idx, m in enumerate(obj.get("messages", [])):
                if isinstance(m, dict):
                    c = m.get("content", "")
                    raw_items.append({"node_id": str(m.get("id") or f"wb-{idx}"), "role": str(m.get("role") or "user"), "text": content_text(c), "timestamp": m.get("timestamp"), "content": c, "raw_record": m})

    nodes, roots, active = _chain(raw_items)
    if not title:
        first_u = next((n.text for n in nodes if n.role == "user" and n.text.strip()), "")
        title = first_u.splitlines()[0][:80].strip() if first_u else sid
    if workspace and not meta.get("project_name"):
        meta["project_name"] = Path(workspace).name or None
    return ConversationGraph(
        source_format="workbuddy_session",
        source_id=sid,
        title=title,
        workspace=workspace,
        nodes=nodes,
        root_ids=roots,
        active_node_id=active,
        metadata=meta,
        raw_source={"records_count": len(records) or len(raw_items)},
        links=_links(nodes),
        app_mode="desktop-app",
    )


def parse_workbuddy_home(wb_home: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    """Read WorkBuddy `~/.workbuddy` (`workbuddy.db` + `projects/<cwd>/<id>.jsonl` + `sessions/`)."""
    root = Path(wb_home).expanduser()
    file_by_sid: dict[str, Path] = {}

    # 1. Discover transcript files across both `projects/*/*.jsonl` (real WorkBuddy) and `sessions/*`
    pdir = root / "projects"
    if pdir.is_dir():
        for fp in sorted(pdir.rglob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
            if fp.is_file():
                file_by_sid.setdefault(fp.stem, fp)
    sdir = root / "sessions"
    if sdir.is_dir():
        for fp in sorted(list(sdir.glob("*.jsonl")) + list(sdir.glob("*.json")), key=lambda x: x.stat().st_mtime, reverse=True):
            if fp.is_file():
                file_by_sid.setdefault(fp.stem, fp)

    # 2. Read metadata rows from `workbuddy.db` (strictly read-only!) and join onto transcripts
    db_rows: list[dict[str, Any]] = []
    spaces: dict[str, str] = {}
    db = root / "workbuddy.db"
    if db.is_file():
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if "spaces" in tables:
                    for r in conn.execute("SELECT id, name FROM spaces"):
                        spaces[str(r["id"])] = str(r["name"] or "")
                if "sessions" in tables:
                    for r in conn.execute("SELECT * FROM sessions WHERE deleted_at IS NULL ORDER BY updated_at DESC"):
                        db_rows.append(dict(r))
            finally:
                conn.close()
        except sqlite3.Error:
            pass

    graphs: list[ConversationGraph] = []
    seen: set[str] = set()

    for d in db_rows:
        sid = str(d.get("id") or "")
        if not sid or sid in seen:
            continue
        seen.add(sid)
        db_cwd = str(d.get("cwd") or "").strip() or None
        db_title = str(d.get("custom_title") or d.get("title") or "").strip()
        space_name = spaces.get(str(d.get("space_id") or "")) or None
        fp = file_by_sid.get(sid)
        if fp is not None:
            g = parse_workbuddy_session(fp)
            merged_meta = dict(g.metadata)
            ws = g.workspace or db_cwd
            merged_meta.update(
                {
                    "project_id": d.get("project_id") or d.get("space_id") or merged_meta.get("project_id"),
                    "project_name": space_name or merged_meta.get("project_name") or (Path(ws).name if ws else None),
                    "section_id": d.get("group_id") or merged_meta.get("section_id"),
                    "section_name": d.get("group_title") or merged_meta.get("section_name"),
                    "model": d.get("model") or merged_meta.get("model"),
                    "mode": d.get("mode") or merged_meta.get("mode"),
                }
            )
            graphs.append(
                ConversationGraph(
                    source_format=g.source_format,
                    source_id=sid,
                    title=db_title or g.title or sid,
                    workspace=ws,
                    nodes=g.nodes,
                    root_ids=g.root_ids,
                    active_node_id=g.active_node_id,
                    metadata=merged_meta,
                    raw_source=g.raw_source,
                    links=g.links,
                    app_mode="desktop-app",
                )
            )
        else:
            graphs.append(
                ConversationGraph(
                    source_format="workbuddy_sqlite",
                    source_id=sid,
                    title=db_title or sid,
                    workspace=db_cwd,
                    nodes=(),
                    root_ids=(),
                    active_node_id=None,
                    metadata={
                        "project_id": d.get("project_id") or d.get("space_id"),
                        "project_name": space_name or (Path(db_cwd).name if db_cwd else None),
                        "section_id": d.get("group_id"),
                        "section_name": d.get("group_title"),
                        "model": d.get("model"),
                        "mode": d.get("mode"),
                        "source_file": db.name,
                    },
                    raw_source={"session_row": d},
                    app_mode="desktop-app",
                )
            )
        if limit and len(graphs) >= limit:
            return graphs

    # 3. Any standalone session files not yet indexed in workbuddy.db
    for sid, fp in file_by_sid.items():
        if sid in seen:
            continue
        g = parse_workbuddy_session(fp)
        if g.source_id not in seen:
            seen.add(g.source_id)
            graphs.append(g)
            if limit and len(graphs) >= limit:
                break
    return graphs


def workbuddy_project_dir_name(cwd: str | Path) -> str:
    """Encode a workspace path using WorkBuddy's `projects/<encoded-cwd>` convention."""
    resolved = str(Path(cwd).expanduser().resolve())
    return re.sub(r"[^A-Za-z0-9._-]", "-", resolved).strip("-") or "workspace"


def merge_workbuddy_sessions_batch(
    db_path: str | Path,
    entries: list[dict[str, Any]],
    *,
    on_collision: str = "refuse",
) -> list[dict[str, Any]]:
    """Merge migrated sessions into WorkBuddy `workbuddy.db` (`sessions` + `workspaces` tables)."""
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_ms = int(time.time() * 1000)
    conn = sqlite3.connect(str(db), timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                cwd TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT 'local-user',
                title TEXT,
                custom_title TEXT,
                status TEXT NOT NULL DEFAULT 'completed',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                last_activity_at INTEGER,
                deleted_at INTEGER,
                is_playground INTEGER NOT NULL DEFAULT 0,
                source_mode TEXT,
                mode TEXT,
                model TEXT,
                permission_mode TEXT,
                project_id TEXT,
                transport TEXT NOT NULL DEFAULT 'local',
                group_id TEXT,
                group_title TEXT,
                unread INTEGER NOT NULL DEFAULT 0,
                space_id TEXT
            );
            CREATE TABLE IF NOT EXISTS workspaces (
                path TEXT PRIMARY KEY,
                last_opened_at INTEGER NOT NULL
            );
            """
        )
        cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(sessions)")}
        ws_cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(workspaces)")}
        default_uid = "local-user"
        if "user_id" in cols:
            urow = conn.execute("SELECT user_id FROM sessions WHERE user_id IS NOT NULL AND user_id != '' LIMIT 1").fetchone()
            if urow and urow[0]:
                default_uid = str(urow[0])
        existing_ids = {str(r[0]) for r in conn.execute("SELECT id FROM sessions")}
        results: list[dict[str, Any]] = []
        for item in entries:
            sid = str(item.get("id") or uuid.uuid4())
            if sid in existing_ids:
                if on_collision == "refuse":
                    raise FileExistsError(f"workbuddy session already exists in workbuddy.db: {sid}")
                if on_collision == "skip":
                    results.append({"session_id": sid, "action": "skipped"})
                    continue
                if on_collision == "rename":
                    sid = str(uuid.uuid4())
            cwd_val = str(item.get("cwd") or "")
            title_val = str(item.get("title") or sid)
            candidate_vals: dict[str, Any] = {
                "id": sid,
                "cwd": cwd_val,
                "user_id": default_uid,
                "title": title_val,
                "custom_title": str(item.get("custom_title") or title_val),
                "status": "completed",
                "created_at": now_ms,
                "updated_at": now_ms,
                "last_activity_at": now_ms,
                "deleted_at": None,
                "is_playground": 0,
                "source_mode": "craft",
                "mode": str(item.get("mode") or "craft"),
                "model": str(item.get("model") or "auto"),
                "permission_mode": "fullAccess",
                "project_id": item.get("project_id"),
                "transport": "local",
                "group_id": item.get("group_id"),
                "group_title": item.get("group_title"),
                "unread": 0,
                "space_id": item.get("space_id"),
            }
            insert_cols = [c for c in candidate_vals if c in cols]
            placeholders = ", ".join("?" for _ in insert_cols)
            conn.execute(
                f"INSERT OR REPLACE INTO sessions ({', '.join(insert_cols)}) VALUES ({placeholders})",
                tuple(candidate_vals[c] for c in insert_cols),
            )
            if cwd_val and {"path", "last_opened_at"}.issubset(ws_cols):
                conn.execute(
                    "INSERT OR REPLACE INTO workspaces (path, last_opened_at) VALUES (?, ?)",
                    (cwd_val, now_ms),
                )
            existing_ids.add(sid)
            results.append({"session_id": sid, "action": "merged"})
        conn.commit()
        try:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except sqlite3.Error:
            pass
        return results
    finally:
        conn.close()


def build_workbuddy_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project ConversationGraph into real WorkBuddy JSONL (`session-meta` + `ai-title` + `message`) + metadata."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ms = int(time.time() * 1000)
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, merged, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        records: list[dict[str, Any]] = [
            {
                "type": "workbuddy_session_meta",
                "schema": "workbuddy.session.v1",
                "id": sid,
                "sessionId": sid,
                "title": title,
                "custom_title": title,
                "cwd": resolved_cwd,
                "project_id": graph.metadata.get("project_id"),
                "project_name": graph.metadata.get("project_name"),
                "group_id": graph.metadata.get("section_id"),
                "group_title": graph.metadata.get("section_name"),
                "parent_session_id": graph.metadata.get("parent_session_id"),
                "model": graph.metadata.get("model") or "auto",
                "mode": "craft",
                "created_at": now_iso,
            },
            {
                "type": "session-meta",
                "id": str(uuid.uuid4()),
                "sessionId": sid,
                "cwd": resolved_cwd,
                "timestamp": now_ms,
                "meta": {"importedBy": "nexus-memory"},
            },
            {
                "type": "ai-title",
                "id": str(uuid.uuid4()),
                "sessionId": sid,
                "cwd": resolved_cwd,
                "aiTitle": title,
                "timestamp": now_ms,
            },
        ]
        source_node_ids: list[str] = []
        for idx, t in enumerate(turns):
            body = "\n\n".join(t["texts"])
            ctype = "input_text" if t["role"] == "user" else "output_text"
            records.append({
                "id": str(uuid.uuid4()),
                "type": "message",
                "sessionId": sid,
                "cwd": resolved_cwd,
                "role": t["role"],
                "content": [{"type": ctype, "text": body}],
                "timestamp": now_ms + idx + 1,
            })
            source_node_ids.extend(t["source_node_ids"])
        sessions.append({
            "session_id": sid,
            "branch_index": branch_index,
            "title": title,
            "cwd": resolved_cwd,
            "source_node_ids": source_node_ids,
            "records": records,
        })
        if merged:
            losses.append({"feature": "consecutive_same_role_coalescing", "disposition": f"merged {merged} turn(s) for API validity"})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_workbuddy_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 2. T3 Code (`~/.t3/userdata/statev2.sqlite` + legacy thread JSON) ────────


_T3CODE_PROVIDER_MAP = {
    "antigravity": ("antigravity", "gemini-4-carbon"),
    "codex": ("codex", "gpt-5-codex"),
    "codex_rollout": ("codex", "gpt-5-codex"),
    "codex_app_snapshot": ("codex", "gpt-5-codex"),
    "claude": ("claudeAgent", "claude-sonnet-4-5"),
    "claude_code_jsonl": ("claudeAgent", "claude-sonnet-4-5"),
    "claude_desktop_3p": ("claudeAgent", "claude-sonnet-4-5"),
    "cursor": ("cursor", "auto"),
    "cursor_vscdb": ("cursor", "auto"),
    "opencode": ("opencode", "default"),
    "pi": ("pi", "default"),
    "kiro": ("kiro", "default"),
}


def _t3code_provider_for_source(source_format: str | None) -> tuple[str, str]:
    fmt = (source_format or "").lower()
    for prefix, val in _T3CODE_PROVIDER_MAP.items():
        if fmt == prefix or fmt.startswith(prefix):
            return val
    return ("codex", "gpt-5-codex")


def _ensure_t3code_statev2_schema(conn: sqlite3.Connection) -> None:
    """Ensure the real T3 Code v2 SQLite projection & event tables exist (for fresh sandboxes)."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS projection_projects (
            project_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            workspace_root TEXT NOT NULL,
            scripts_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT,
            default_model_selection_json TEXT,
            default_thread_env_mode TEXT,
            favicon_path TEXT,
            auto_pull INTEGER NOT NULL DEFAULT 0,
            project_icon_json TEXT,
            pinned_at TEXT,
            archived_at TEXT,
            has_custom_title INTEGER NOT NULL DEFAULT 0,
            tracked_folders_json TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS orchestration_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            aggregate_kind TEXT NOT NULL,
            stream_id TEXT NOT NULL,
            stream_version INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            command_id TEXT,
            causation_event_id TEXT,
            correlation_id TEXT,
            actor_kind TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            application_event_version INTEGER NOT NULL DEFAULT 2
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_projection_metadata (
            projection_name TEXT PRIMARY KEY,
            schema_version INTEGER NOT NULL,
            last_sequence INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_projection_threads (
            thread_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            default_provider TEXT NOT NULL,
            runtime_mode TEXT NOT NULL,
            interaction_mode TEXT NOT NULL,
            active_provider_thread_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            archived_at TEXT,
            deleted_at TEXT,
            payload_json TEXT NOT NULL,
            provider_instance_id TEXT,
            fork_run_ids_json TEXT
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_projection_runs (
            run_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            provider TEXT NOT NULL,
            provider_thread_id TEXT,
            status TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            completed_at TEXT,
            payload_json TEXT NOT NULL,
            provider_instance_id TEXT
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_projection_nodes (
            node_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            run_id TEXT,
            parent_node_id TEXT,
            root_node_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            provider_thread_id TEXT,
            provider_turn_id TEXT,
            runtime_request_id TEXT,
            checkpoint_scope_id TEXT,
            started_at TEXT,
            completed_at TEXT,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_projection_messages (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            run_id TEXT,
            node_id TEXT,
            role TEXT NOT NULL,
            streaming INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            search_text TEXT
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_projection_turn_items (
            turn_item_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            run_id TEXT,
            node_id TEXT,
            provider_thread_id TEXT,
            provider_turn_id TEXT,
            parent_item_id TEXT,
            ordinal INTEGER NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            inline_work_output INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS orchestration_v2_turn_item_positions (
            thread_id TEXT NOT NULL,
            turn_item_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            PRIMARY KEY (thread_id, turn_item_id),
            UNIQUE (thread_id, ordinal)
        );
        """
    )


def _t3code_deterministic_uuid(source_format: str, source_id: str, branch_index: int = 1) -> str:
    """Stable deterministic UUIDv5 so parent/root/child thread links resolve identically across sessions."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"nexus-t3code:{source_format}:{source_id}:{branch_index}"))


def merge_t3code_threads_batch(
    db_path: str | Path,
    payloads: list[dict[str, Any]],
    *,
    on_collision: str = "refuse",
    on_progress: Any = None,
) -> list[dict[str, Any]]:
    """Batch-merge N `t3code.thread.v2` payloads into `statev2.sqlite` inside ONE SQLite transaction.

    - Sorts parents before children (`nestingDepth ASC`) so child `lineage.parentThreadId` resolves cleanly.
    - Preserves per-session real Projects (`workspacePath` -> `projection_projects`), Section Groups
      (`tags` -> `StoredThreadTags`), and Parent-Child Subagent/Fork `lineage`.
    - Performs ONE commit + ONE `PRAGMA wal_checkpoint(PASSIVE)` for 10x-30x faster bulk migrations.
    """
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_dt = datetime.now(UTC)
    now_iso = now_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    import_prefix = "agent-session-import:v2"

    def _iso_utc(val: Any, fallback: str) -> str:
        if isinstance(val, str) and val.strip():
            s = val.strip().replace(" ", "T")
            if s.endswith("Z") or "+" in s[10:]:
                return s.replace("+00:00", "Z")
            if "T" in s:
                return s + "Z"
        return fallback

    # Sort parent threads before child subagents while preserving original index to return aligned results
    indexed = sorted(
        enumerate(payloads),
        key=lambda item: (int(item[1].get("nestingDepth") or 0), item[0]),
    )
    results: list[dict[str, Any]] = [{} for _ in payloads]
    total = len(indexed)

    conn = sqlite3.connect(str(db), timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_t3code_statev2_schema(conn)
        # Cache existing threads, model selections, and projects for O(1) lookups inside batch
        known_threads = {
            str(r[0]) for r in conn.execute("SELECT thread_id FROM orchestration_v2_projection_threads")
        }
        model_by_provider: dict[str, dict[str, Any]] = {}
        for row in conn.execute(
            "SELECT default_provider, payload_json FROM orchestration_v2_projection_threads"
        ):
            prov = str(row[0] or "")
            if prov and prov not in model_by_provider:
                try:
                    ep = json.loads(row[1])
                    if isinstance(ep.get("modelSelection"), dict):
                        model_by_provider[prov] = ep["modelSelection"]
                except json.JSONDecodeError:
                    pass
        project_by_ws: dict[str, str] = {}
        fallback_project_id: str | None = None
        for prow in conn.execute(
            "SELECT project_id, workspace_root FROM projection_projects WHERE deleted_at IS NULL ORDER BY created_at"
        ):
            pid_s = str(prow["project_id"])
            ws_s = str(prow["workspace_root"] or "")
            if fallback_project_id is None:
                fallback_project_id = pid_s
            if ws_s:
                project_by_ws[ws_s] = pid_s

        for step_i, (orig_idx, payload) in enumerate(indexed, 1):
            sid = str(payload.get("threadId") or uuid.uuid4())
            raw_title = str(payload.get("title") or "").strip()
            title = (raw_title or "Untitled thread")[:240]
            workspace_path = str(payload.get("workspacePath") or "").strip()
            if workspace_path in {"", "/", "\\"} or len(Path(workspace_path).parts) <= 1:
                workspace_path = ""

            created_at = _iso_utc(payload.get("createdAt"), now_iso)
            updated_at = _iso_utc(payload.get("updatedAt"), created_at)
            raw_parent_tid = payload.get("parentThreadId")
            raw_root_tid = payload.get("rootThreadId")
            rel_to_parent = payload.get("relationshipToParent")
            raw_tags = payload.get("tags") if isinstance(payload.get("tags"), list) else []
            tags = [str(t).strip() for t in raw_tags if isinstance(t, str) and t.strip()]
            raw_provider = str(payload.get("provider") or "").strip()
            provider_id, default_model = _t3code_provider_for_source(raw_provider)
            if raw_provider in {"antigravity", "codex", "claudeAgent", "cursor", "opencode", "pi", "kiro"}:
                provider_id = raw_provider
            messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []

            if sid in known_threads:
                if on_collision == "refuse":
                    raise FileExistsError(f"t3code thread_id already exists in statev2.sqlite: {sid}")
                if on_collision == "skip":
                    results[orig_idx] = {"thread_id": sid, "action": "skipped", "message_count": 0}
                    if on_progress:
                        on_progress("apply", step_i, total, title[:40])
                    continue
                if on_collision == "rename":
                    sid = str(uuid.uuid4())

            model_selection = model_by_provider.get(
                provider_id,
                {"instanceId": provider_id, "model": default_model},
            )

            project_id: str | None = None
            if workspace_path:
                project_id = project_by_ws.get(workspace_path)
                if not project_id:
                    project_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"nexus-t3code-project:{workspace_path}"))
                    proj_title = str(payload.get("projectName") or Path(workspace_path).name or "Imported Project")
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO projection_projects (
                            project_id, title, workspace_root, scripts_json, created_at, updated_at,
                            deleted_at, default_model_selection_json, default_thread_env_mode,
                            favicon_path, auto_pull, project_icon_json, pinned_at, archived_at,
                            has_custom_title, tracked_folders_json
                        ) VALUES (?, ?, ?, '[]', ?, ?, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, 0, '[]')
                        """,
                        (project_id, proj_title, workspace_path, created_at, now_iso),
                    )
                    proj_cmd = f"nexus-import-project:{project_id}"
                    proj_evt_payload = {
                        "projectId": project_id,
                        "title": proj_title,
                        "workspaceRoot": workspace_path,
                        "defaultModelSelection": None,
                        "faviconPath": None,
                        "projectIcon": None,
                        "scripts": [],
                        "createdAt": created_at,
                        "updatedAt": now_iso,
                    }
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO orchestration_events (
                            event_id, aggregate_kind, stream_id, stream_version, event_type,
                            occurred_at, command_id, causation_event_id, correlation_id,
                            actor_kind, payload_json, metadata_json, application_event_version
                        ) VALUES (?, 'project', ?, 0, 'project.created', ?, ?, NULL, ?, 'client', ?, '{}', 2)
                        """,
                        (
                            f"event:nexus-project:{project_id}:{uuid.uuid4()}",
                            project_id,
                            now_iso,
                            proj_cmd,
                            proj_cmd,
                            json.dumps(proj_evt_payload, ensure_ascii=False),
                        ),
                    )
                    project_by_ws[workspace_path] = project_id
            if not project_id:
                if fallback_project_id:
                    project_id = fallback_project_id
                else:
                    project_id = str(uuid.uuid4())
                    scratch_root = str(db.parent.parent / "scratch")
                    conn.execute(
                        """
                        INSERT INTO projection_projects (
                            project_id, title, workspace_root, scripts_json, created_at, updated_at,
                            deleted_at, project_icon_json, tracked_folders_json
                        ) VALUES (?, 'No project', ?, '[]', ?, ?, NULL, NULL, '[]')
                        """,
                        (project_id, scratch_root, created_at, now_iso),
                    )
                    fallback_project_id = project_id

            # Resolve parent/root lineage ONLY when parent exists in T3 Code; otherwise keep visible top-level
            resolved_parent: str | None = None
            resolved_rel: str | None = None
            resolved_root = sid
            if isinstance(raw_parent_tid, str) and raw_parent_tid in known_threads and raw_parent_tid != sid:
                resolved_parent = raw_parent_tid
                resolved_rel = rel_to_parent if rel_to_parent in {"fork", "subagent"} else "subagent"
                if isinstance(raw_root_tid, str) and raw_root_tid in known_threads:
                    resolved_root = raw_root_tid
                else:
                    resolved_root = resolved_parent

            stream_ver = 0
            cmd_id = f"nexus-import:{sid}"

            def emit_event(event_id: str, event_type: str, evt_payload: dict[str, Any], meta: dict[str, Any], occurred: str) -> None:
                nonlocal stream_ver
                conn.execute(
                    """
                    INSERT INTO orchestration_events (
                        event_id, aggregate_kind, stream_id, stream_version, event_type,
                        occurred_at, command_id, causation_event_id, correlation_id,
                        actor_kind, payload_json, metadata_json, application_event_version
                    ) VALUES (?, 'thread', ?, ?, ?, ?, ?, NULL, ?, 'server', ?, ?, 2)
                    """,
                    (
                        event_id,
                        sid,
                        stream_ver,
                        event_type,
                        occurred,
                        cmd_id,
                        cmd_id,
                        json.dumps(evt_payload, ensure_ascii=False),
                        json.dumps(meta, ensure_ascii=False),
                    ),
                )
                stream_ver += 1

            thread_payload: dict[str, Any] = {
                "createdBy": "system",
                "creationSource": "server",
                "id": sid,
                "projectId": project_id,
                "title": title,
                "providerInstanceId": provider_id,
                "modelSelection": model_selection,
                "runtimeMode": "full-access",
                "interactionMode": "default",
                "branch": None,
                "worktreePath": None,
                "linkedPullRequest": None,
                "branchPullRequest": None,
                "activeProviderThreadId": None,
                "historyOrigin": "v1_import",
                "lineage": {
                    "parentThreadId": resolved_parent,
                    "relationshipToParent": resolved_rel,
                    "rootThreadId": resolved_root,
                },
                "forkedFrom": None,
                "createdAt": created_at,
                "updatedAt": updated_at,
                "archivedAt": None,
                "settledOverride": "active",
                "settledAt": None,
                "unsettledAt": updated_at,
                "snoozedUntil": None,
                "snoozedAt": None,
                "pinnedAt": None,
                "pinOrderKey": None,
                "activeOrderKey": None,
                "lastVisitedAt": None,
                "deletedAt": None,
            }
            if tags:
                thread_payload["tags"] = tags

            conn.execute(
                """
                INSERT OR REPLACE INTO orchestration_v2_projection_threads (
                    thread_id, project_id, title, default_provider, runtime_mode, interaction_mode,
                    active_provider_thread_id, created_at, updated_at, archived_at, deleted_at,
                    payload_json, provider_instance_id, fork_run_ids_json
                ) VALUES (?, ?, ?, ?, 'full-access', 'default', NULL, ?, ?, NULL, NULL, ?, ?, NULL)
                """,
                (
                    sid,
                    project_id,
                    title,
                    provider_id,
                    created_at,
                    updated_at,
                    json.dumps(thread_payload, ensure_ascii=False),
                    provider_id,
                ),
            )
            emit_event(
                f"{import_prefix}:thread:{sid}:created",
                "thread.created",
                thread_payload,
                {"providerInstanceId": provider_id},
                created_at,
            )
            known_threads.add(sid)

            inserted_msgs = 0
            for m in messages:
                if not isinstance(m, dict):
                    continue
                role = "assistant" if str(m.get("role") or "").lower() == "assistant" else "user"
                text = content_text(m.get("content", m.get("text", "")))
                if not text.strip():
                    continue
                ordinal = inserted_msgs + 1
                suffix = f"{inserted_msgs:06d}"
                msg_id = f"{sid}:{suffix}"
                turn_item_id = f"{import_prefix}:turn-item:{sid}:{suffix}"
                mts = _iso_utc(m.get("createdAt"), updated_at)

                msg_payload = {
                    "createdBy": "user" if role == "user" else "agent",
                    "creationSource": "server",
                    "id": msg_id,
                    "threadId": sid,
                    "runId": None,
                    "nodeId": None,
                    "role": role,
                    "text": text,
                    "attachments": [],
                    "streaming": False,
                    "createdAt": mts,
                    "updatedAt": mts,
                }
                conn.execute(
                    """
                    INSERT OR REPLACE INTO orchestration_v2_projection_messages (
                        message_id, thread_id, run_id, node_id, role, streaming,
                        created_at, updated_at, payload_json, search_text
                    ) VALUES (?, ?, NULL, NULL, ?, 0, ?, ?, ?, NULL)
                    """,
                    (msg_id, sid, role, mts, mts, json.dumps(msg_payload, ensure_ascii=False)),
                )
                emit_event(f"{import_prefix}:message:{sid}:{suffix}", "message.updated", msg_payload, {}, mts)

                common_item: dict[str, Any] = {
                    "id": turn_item_id,
                    "threadId": sid,
                    "runId": None,
                    "nodeId": None,
                    "providerThreadId": None,
                    "providerTurnId": None,
                    "nativeItemRef": None,
                    "parentItemId": None,
                    "ordinal": ordinal,
                    "status": "completed",
                    "title": None,
                    "startedAt": mts,
                    "completedAt": mts,
                    "updatedAt": mts,
                }
                if role == "user":
                    item_type = "user_message"
                    item_payload = {
                        **common_item,
                        "createdBy": "user",
                        "creationSource": "server",
                        "type": "user_message",
                        "messageId": msg_id,
                        "inputIntent": "turn_start",
                        "text": text,
                        "attachments": [],
                    }
                else:
                    item_type = "assistant_message"
                    item_payload = {
                        **common_item,
                        "type": "assistant_message",
                        "messageId": msg_id,
                        "text": text,
                        "streaming": False,
                    }

                conn.execute(
                    """
                    INSERT OR REPLACE INTO orchestration_v2_projection_turn_items (
                        turn_item_id, thread_id, run_id, node_id, provider_thread_id, provider_turn_id,
                        parent_item_id, ordinal, type, status, updated_at, payload_json, inline_work_output
                    ) VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, 'completed', ?, ?, 0)
                    """,
                    (
                        turn_item_id,
                        sid,
                        ordinal,
                        item_type,
                        mts,
                        json.dumps(item_payload, ensure_ascii=False),
                    ),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO orchestration_v2_turn_item_positions (thread_id, turn_item_id, ordinal) VALUES (?, ?, ?)",
                    (sid, turn_item_id, ordinal),
                )
                emit_event(turn_item_id, "turn-item.updated", item_payload, {}, mts)
                inserted_msgs += 1

            results[orig_idx] = {
                "thread_id": sid,
                "project_id": project_id,
                "parent_thread_id": resolved_parent,
                "action": "merged",
                "message_count": inserted_msgs,
            }
            if on_progress:
                on_progress("apply", step_i, total, title[:40])

        max_seq_row = conn.execute("SELECT COALESCE(MAX(sequence), 0) FROM orchestration_events").fetchone()
        max_seq = int(max_seq_row[0]) if max_seq_row else 0
        conn.execute(
            """
            INSERT INTO orchestration_v2_projection_metadata (projection_name, schema_version, last_sequence, updated_at)
            VALUES ('thread-projections', 2, ?, ?)
            ON CONFLICT(projection_name) DO UPDATE SET last_sequence = excluded.last_sequence, updated_at = excluded.updated_at
            """,
            (max_seq, now_iso),
        )
        conn.commit()
        try:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except sqlite3.Error:
            pass
        return results
    finally:
        conn.close()


def merge_t3code_thread_into_statev2(
    db_path: str | Path,
    payload: dict[str, Any],
    *,
    on_collision: str = "refuse",
) -> dict[str, Any]:
    """Single-thread wrapper around `merge_t3code_threads_batch`."""
    return merge_t3code_threads_batch(db_path, [payload], on_collision=on_collision)[0]


def parse_t3code_source(
    path: str | Path,
    *,
    limit: int | None = None,
    include_subagents: bool = True,
) -> list[ConversationGraph]:
    """Read T3 Code `statev2.sqlite` (v2 `orchestration_v2_projection_*` or legacy tables) or thread JSON."""
    p = Path(path).expanduser()
    if p.is_dir():
        db = p / "userdata" / "statev2.sqlite"
        if db.is_file():
            return parse_t3code_source(db, limit=limit, include_subagents=include_subagents)
        out: list[ConversationGraph] = []
        for fp in sorted(p.rglob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            if fp.name != "settings.json":
                try:
                    out.extend(parse_t3code_source(fp))
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
                if limit and len(out) >= limit:
                    return out[:limit]
        return out

    if p.suffix in {".sqlite", ".db"}:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        graphs: list[ConversationGraph] = []
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "orchestration_v2_projection_threads" in tables:
                projects_by_id: dict[str, dict[str, Any]] = {}
                if "projection_projects" in tables:
                    for pr in conn.execute("SELECT project_id, title, workspace_root FROM projection_projects"):
                        projects_by_id[str(pr["project_id"])] = dict(pr)
                msg_by_tid: dict[str, list[dict[str, Any]]] = {}
                if "orchestration_v2_projection_messages" in tables:
                    for mr in conn.execute(
                        "SELECT message_id, thread_id, role, created_at, payload_json FROM orchestration_v2_projection_messages ORDER BY created_at, rowid"
                    ):
                        md = dict(mr)
                        try:
                            pj = json.loads(md.get("payload_json") or "{}")
                        except json.JSONDecodeError:
                            pj = {}
                        md["_payload"] = pj
                        msg_by_tid.setdefault(str(md["thread_id"]), []).append(md)
                for tr in conn.execute(
                    "SELECT * FROM orchestration_v2_projection_threads WHERE deleted_at IS NULL ORDER BY updated_at DESC"
                ):
                    td = dict(tr)
                    tid = str(td["thread_id"])
                    try:
                        tp = json.loads(td.get("payload_json") or "{}")
                    except json.JSONDecodeError:
                        tp = {}
                    lineage = tp.get("lineage") if isinstance(tp.get("lineage"), dict) else {}
                    parent_tid = lineage.get("parentThreadId")
                    if not include_subagents and parent_tid:
                        continue
                    proj = projects_by_id.get(str(td.get("project_id") or ""), {})
                    raw_items = []
                    for idx, m in enumerate(msg_by_tid.get(tid, [])):
                        pj = m.get("_payload") or {}
                        text = str(pj.get("text") or "")
                        raw_items.append(
                            {
                                "node_id": str(m.get("message_id") or f"t3-{idx}"),
                                "role": str(m.get("role") or pj.get("role") or "user"),
                                "text": text,
                                "timestamp": m.get("created_at") or pj.get("createdAt"),
                                "content": text,
                                "raw_record": pj or m,
                            }
                        )
                    nodes, roots, active = _chain(raw_items)
                    tags = tp.get("tags") if isinstance(tp.get("tags"), list) else []
                    graphs.append(
                        ConversationGraph(
                            source_format="t3code_thread",
                            source_id=tid,
                            title=str(td.get("title") or tid),
                            workspace=tp.get("worktreePath") or proj.get("workspace_root"),
                            nodes=nodes,
                            root_ids=roots,
                            active_node_id=active,
                            metadata={
                                "project_id": td.get("project_id"),
                                "project_name": proj.get("title"),
                                "section_name": str(tags[0]) if tags else None,
                                "parent_session_id": parent_tid,
                                "root_session_id": lineage.get("rootThreadId") or tid,
                                "nesting_depth": 1 if parent_tid else 0,
                                "provider": td.get("provider_instance_id") or td.get("default_provider"),
                                "source_file": p.name,
                            },
                            raw_source={"thread": tp or td},
                            links=_links(nodes),
                            app_mode="desktop-app",
                        )
                    )
                    if limit and len(graphs) >= limit:
                        break
                return graphs
            if "threads" in tables:
                msg_by_tid = {}
                if "messages" in tables:
                    for mr in conn.execute("SELECT * FROM messages"):
                        md = dict(mr)
                        tid = str(md.get("thread_id") or md.get("threadId") or "")
                        if tid:
                            msg_by_tid.setdefault(tid, []).append(md)
                for tr in conn.execute("SELECT * FROM threads"):
                    td = dict(tr)
                    tid = str(td.get("id") or "")
                    raw_items = []
                    for idx, m in enumerate(msg_by_tid.get(tid, [])):
                        c = m.get("content", m.get("text", ""))
                        raw_items.append({"node_id": str(m.get("id") or f"t3-{idx}"), "role": str(m.get("role") or "user"), "text": content_text(c), "timestamp": m.get("created_at") or m.get("createdAt"), "content": c, "raw_record": m})
                    nodes, roots, active = _chain(raw_items)
                    graphs.append(ConversationGraph(
                        source_format="t3code_thread",
                        source_id=tid or p.stem,
                        title=str(td.get("title") or tid),
                        workspace=td.get("cwd") or td.get("projectPath") or td.get("workspace"),
                        nodes=nodes, root_ids=roots, active_node_id=active,
                        metadata={"project_id": td.get("project_id") or td.get("projectId"), "project_name": td.get("project_name"), "section_name": td.get("section_name"), "parent_session_id": td.get("parent_thread_id"), "source_file": p.name},
                        raw_source={"thread": td}, links=_links(nodes), app_mode="desktop-app",
                    ))
        finally:
            conn.close()
        return graphs

    data = json.loads(p.read_text(encoding="utf-8-sig"))
    sid = str(data.get("threadId") or data.get("id") or p.stem)
    raw_items = []
    for idx, m in enumerate(data.get("messages", [])):
        if isinstance(m, dict):
            c = m.get("content", m.get("text", ""))
            raw_items.append({"node_id": str(m.get("id") or f"t3-{idx}"), "role": str(m.get("role") or "user"), "text": content_text(c), "timestamp": m.get("createdAt") or m.get("timestamp"), "content": c, "raw_record": m})
    nodes, roots, active = _chain(raw_items)
    return [ConversationGraph(
        source_format="t3code_thread",
        source_id=sid,
        title=str(data.get("title") or sid),
        workspace=data.get("workspacePath") or data.get("cwd"),
        nodes=nodes, root_ids=roots, active_node_id=active,
        metadata={"project_id": data.get("projectId"), "project_name": data.get("projectName"), "section_name": data.get("sectionName"), "parent_session_id": data.get("parentThreadId"), "provider": data.get("provider"), "source_file": p.name},
        raw_source=data, links=_links(nodes), app_mode="desktop-app",
    )]


def build_t3code_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project ConversationGraph into T3 Code v2 thread payloads (preserving Project, Section tags, and Parent/Subagent lineage)."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    raw_ws = str(graph.workspace or "").strip()
    if raw_ws and raw_ws not in {"/", "\\"}:
        resolved_cwd = str(Path(raw_ws).expanduser().resolve())
    else:
        fallback_ws = str(cwd or "").strip()
        resolved_cwd = str(Path(fallback_ws).expanduser().resolve()) if fallback_ws and fallback_ws not in {"/", "\\"} else ""
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    provider_id, _ = _t3code_provider_for_source(graph.metadata.get("provider") or graph.source_format)
    parent_src_id = graph.metadata.get("parent_session_id")
    root_src_id = graph.metadata.get("root_session_id")
    nesting_depth = int(graph.metadata.get("nesting_depth") or (1 if parent_src_id else 0))
    subagent_role = graph.metadata.get("subagent_role")
    section_name = graph.metadata.get("section_name")

    mapped_parent_id = (
        _t3code_deterministic_uuid(graph.source_format, str(parent_src_id), 1)
        if isinstance(parent_src_id, str) and parent_src_id.strip()
        else None
    )
    mapped_root_id = (
        _t3code_deterministic_uuid(graph.source_format, str(root_src_id), 1)
        if isinstance(root_src_id, str) and root_src_id.strip()
        else None
    )

    tags: list[str] = []
    if isinstance(section_name, str) and section_name.strip():
        tags.append(section_name.strip())
    if isinstance(subagent_role, str) and subagent_role.strip():
        tags.append(subagent_role.strip())

    first_branch_sid: str | None = None
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = _t3code_deterministic_uuid(graph.source_format, graph.source_id, branch_index)
        if branch_index == 1:
            first_branch_sid = sid
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        msgs = [{"id": str(uuid.uuid4()), "role": t["role"], "content": "\n\n".join(t["texts"]), "createdAt": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        branch_parent = first_branch_sid if branch_index > 1 else mapped_parent_id
        branch_rel = "fork" if branch_index > 1 else ("subagent" if mapped_parent_id else None)
        branch_depth = nesting_depth + (1 if branch_index > 1 else 0)
        created_ts = next((m["createdAt"] for m in msgs if isinstance(m.get("createdAt"), str)), now_iso)
        updated_ts = graph.metadata.get("last_modified_time") or (msgs[-1]["createdAt"] if msgs else now_iso)
        payload = {
            "schema": "t3code.thread.v2",
            "threadId": sid,
            "title": title,
            "workspacePath": resolved_cwd,
            "projectId": graph.metadata.get("project_id"),
            "projectName": graph.metadata.get("project_name"),
            "sectionName": section_name,
            "parentThreadId": branch_parent,
            "rootThreadId": mapped_root_id or first_branch_sid or sid,
            "relationshipToParent": branch_rel,
            "nestingDepth": branch_depth,
            "subagentRole": subagent_role,
            "tags": tags,
            "provider": provider_id,
            "createdAt": created_ts,
            "updatedAt": updated_ts,
            "messages": msgs,
        }
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": payload})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_t3code_thread_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 3. AWS Kiro (`~/.kiro/sessions/cli/<id>.jsonl` + `/chat save` JSON) ──────


def parse_kiro_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    raw_items: list[dict[str, Any]] = []
    sid = p.stem
    title = p.stem
    workspace: str | None = None
    meta: dict[str, Any] = {"source_file": p.name}
    if p.suffix == ".jsonl":
        for idx, ln in enumerate(text.splitlines()):
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r.get("type") == "kiro_session_meta":
                sid = str(r.get("conversation_id") or r.get("id") or sid)
                title = str(r.get("title") or title)
                workspace = r.get("cwd") or workspace
                continue
            role = str(r.get("role") or "")
            if role in {"user", "assistant", "system"}:
                c = r.get("content", "")
                raw_items.append({"node_id": str(r.get("id") or f"kiro-{idx}"), "role": role, "text": content_text(c), "timestamp": r.get("timestamp"), "content": c, "raw_record": r})
    else:
        data = json.loads(text)
        sid = str(data.get("conversation_id") or data.get("id") or sid)
        title = str(data.get("title") or sid)
        workspace = data.get("cwd") or data.get("workspace")
        for idx, entry in enumerate(data.get("history", data.get("messages", []))):
            if isinstance(entry, dict):
                if "user" in entry and "assistant" in entry:
                    raw_items.append({"node_id": f"kiro-u-{idx}", "role": "user", "text": content_text(entry["user"]), "content": entry["user"], "raw_record": entry})
                    raw_items.append({"node_id": f"kiro-a-{idx}", "role": "assistant", "text": content_text(entry["assistant"]), "content": entry["assistant"], "raw_record": entry})
                elif "role" in entry:
                    c = entry.get("content", "")
                    raw_items.append({"node_id": str(entry.get("id") or f"kiro-{idx}"), "role": str(entry["role"]), "text": content_text(c), "timestamp": entry.get("timestamp"), "content": c, "raw_record": entry})
    nodes, roots, active = _chain(raw_items)
    return ConversationGraph(source_format="kiro_session", source_id=sid, title=title, workspace=workspace, nodes=nodes, root_ids=roots, active_node_id=active, metadata=meta, raw_source={"nodes": len(nodes)}, links=_links(nodes), app_mode="cli")


def build_kiro_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        records: list[dict[str, Any]] = [{"type": "kiro_session_meta", "schema": "kiro.cli.v3", "conversation_id": sid, "title": title, "cwd": resolved_cwd, "timestamp": now_iso}]
        source_node_ids: list[str] = []
        for idx, t in enumerate(turns):
            records.append({"id": f"km-{idx}", "role": t["role"], "content": "\n\n".join(t["texts"]), "timestamp": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso})
            source_node_ids.extend(t["source_node_ids"])
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "records": records})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_kiro_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 4. Sourcegraph Amp (`~/.local/share/amp/threads/<id>.json`) ──────────────


def parse_amp_thread(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    sid = str(data.get("id") or data.get("threadId") or p.stem)
    raw_items: list[dict[str, Any]] = []
    for idx, m in enumerate(data.get("messages", [])):
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "user")
        c = m.get("content", "")
        raw_items.append({"node_id": str(m.get("id") or f"amp-{idx}"), "role": role, "text": content_text(c), "timestamp": m.get("createdAt") or m.get("timestamp"), "content": c, "raw_record": m})
    nodes, roots, active = _chain(raw_items)
    env = data.get("env") if isinstance(data.get("env"), dict) else {}
    ws = data.get("workspace") or data.get("cwd") or (env.get("initial") or {}).get("cwd") if isinstance(env.get("initial"), dict) else data.get("cwd")
    return ConversationGraph(source_format="amp_thread", source_id=sid, title=str(data.get("title") or sid), workspace=ws, nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name, "amp_version": data.get("v")}, raw_source=data, links=_links(nodes), app_mode="cli")


def build_amp_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ms = int(time.time() * 1000)
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"T-{uuid.uuid4()}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        msgs = [{"role": t["role"], "content": [{"type": "text", "text": "\n\n".join(t["texts"])}]} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        payload = {"v": 1, "id": sid, "title": title, "created": now_ms, "env": {"initial": {"cwd": resolved_cwd}}, "messages": msgs}
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": payload})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_amp_thread_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 5. ByteDance Trae / Trae Agent (`trajectory-*.json`) ─────────────────────


def parse_trae_trajectory(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    sid = str(data.get("task_id") or data.get("id") or p.stem)
    raw_items: list[dict[str, Any]] = []
    if data.get("task"):
        raw_items.append({"node_id": "trae-task", "role": "user", "text": str(data["task"]), "content": data["task"], "raw_record": {"task": data["task"]}})
    for idx, step in enumerate(data.get("llm_interactions", data.get("messages", []))):
        if not isinstance(step, dict):
            continue
        if "role" in step:
            c = step.get("content", "")
            raw_items.append({"node_id": f"trae-{idx}", "role": str(step["role"]), "text": content_text(c), "timestamp": step.get("timestamp"), "content": c, "raw_record": step})
        elif "response" in step:
            resp = step["response"]
            txt = content_text(resp.get("content", resp) if isinstance(resp, dict) else resp)
            if txt:
                raw_items.append({"node_id": f"trae-resp-{idx}", "role": "assistant", "text": txt, "timestamp": step.get("timestamp"), "content": resp, "raw_record": step})
    nodes, roots, active = _chain(raw_items)
    return ConversationGraph(source_format="trae_trajectory", source_id=sid, title=str(data.get("title") or (str(data.get("task") or "")[:80] or sid)), workspace=data.get("workspace") or data.get("cwd"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name, "model": data.get("model")}, raw_source=data, links=_links(nodes), app_mode="ide-extension")


def build_trae_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"trae-{uuid.uuid4().hex[:12]}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        msgs = [{"role": t["role"], "content": "\n\n".join(t["texts"]), "timestamp": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        payload = {"schema": "trae.trajectory.v1", "id": sid, "title": title, "workspace": resolved_cwd, "model": graph.metadata.get("model") or "auto", "messages": msgs}
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": payload})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_trae_trajectory_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 6. Warp / Oz Agent (`~/.warp/sessions/<id>.json`) ────────────────────────


def parse_warp_oz_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    sid = str(data.get("conversation_id") or data.get("id") or p.stem)
    raw_items: list[dict[str, Any]] = []
    for idx, b in enumerate(data.get("blocks", data.get("messages", []))):
        if not isinstance(b, dict):
            continue
        role = str(b.get("role") or ("user" if b.get("kind") == "user_query" else "assistant"))
        c = b.get("content", b.get("text", ""))
        raw_items.append({"node_id": str(b.get("id") or f"warp-{idx}"), "role": role, "text": content_text(c), "timestamp": b.get("timestamp"), "content": c, "raw_record": b})
    nodes, roots, active = _chain(raw_items)
    return ConversationGraph(source_format="warp_oz_session", source_id=sid, title=str(data.get("title") or sid), workspace=data.get("cwd") or data.get("working_directory"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name, "agent_mode": data.get("agent_mode", "oz")}, raw_source=data, links=_links(nodes), app_mode="terminal-agent")


def build_warp_oz_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"oz-{uuid.uuid4().hex[:12]}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        blocks = [{"id": str(uuid.uuid4()), "kind": "user_query" if t["role"] == "user" else "agent_response", "role": t["role"], "text": "\n\n".join(t["texts"]), "timestamp": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        payload = {"schema": "warp.oz.session.v1", "conversation_id": sid, "title": title, "working_directory": resolved_cwd, "agent_mode": "oz", "blocks": blocks}
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": payload})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_warp_oz_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


def _scan_dir_sessions(
    root: Path,
    subdirs: tuple[str, ...],
    patterns: tuple[str, ...],
    parser_fn: Any,
    *,
    exclude_names: set[str] | None = None,
    limit: int | None = None,
) -> list[ConversationGraph]:
    skip = exclude_names or set()
    candidates: list[Path] = []
    seen_paths: set[Path] = set()
    bases = [root / sub for sub in subdirs if (root / sub).is_dir()]
    if not bases:
        bases = [root]
    for base in bases:
        for pat in patterns:
            for fp in base.rglob(pat):
                if fp.is_file() and fp.name not in skip and fp not in seen_paths:
                    seen_paths.add(fp)
                    candidates.append(fp)
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    out: list[ConversationGraph] = []
    for fp in candidates:
        try:
            out.append(parser_fn(fp))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if limit and len(out) >= limit:
            break
    return out


def parse_kiro_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        return [parse_kiro_session(p)]
    return _scan_dir_sessions(p, ("sessions",), ("*.jsonl", "*.json"), parse_kiro_session, exclude_names={"mcp.json", "settings.json"}, limit=limit)


def parse_amp_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        return [parse_amp_thread(p)]
    return _scan_dir_sessions(p, ("threads",), ("*.json",), parse_amp_thread, exclude_names={"settings.json"}, limit=limit)


def parse_trae_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        return [parse_trae_trajectory(p)]
    return _scan_dir_sessions(p, ("trajectories",), ("*.json",), parse_trae_trajectory, exclude_names={"mcp.json", "settings.json"}, limit=limit)


def parse_warp_sqlite(db_path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    """Read real Warp `warp.sqlite` (`agent_conversations` + `ai_queries`, strictly read-only & token-redacted)."""
    p = Path(db_path).expanduser()
    if not p.is_file():
        return []
    graphs: list[ConversationGraph] = []
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "agent_conversations" not in tables:
            return []
        queries_by_cid: dict[str, list[dict[str, Any]]] = {}
        if "ai_queries" in tables:
            for qr in conn.execute(
                "SELECT exchange_id, conversation_id, start_ts, input, working_directory, model_id FROM ai_queries ORDER BY start_ts ASC, id ASC"
            ):
                qd = dict(qr)
                queries_by_cid.setdefault(str(qd.get("conversation_id") or ""), []).append(qd)

        sql = "SELECT conversation_id, summary, last_modified_at FROM agent_conversations ORDER BY last_modified_at DESC"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        for cr in conn.execute(sql):
            cid = str(cr["conversation_id"] or "")
            if not cid:
                continue
            try:
                summary_obj = json.loads(cr["summary"] or "{}") if isinstance(cr["summary"], str) else {}
            except json.JSONDecodeError:
                summary_obj = {}
            if not isinstance(summary_obj, dict):
                summary_obj = {}
            title = str(summary_obj.get("title") or summary_obj.get("initial_query") or cid)[:160]
            ws = summary_obj.get("initial_working_directory")
            raw_items: list[dict[str, Any]] = []
            model_id = None
            for idx, q in enumerate(queries_by_cid.get(cid, [])):
                ws = ws or q.get("working_directory")
                model_id = model_id or q.get("model_id")
                try:
                    inp_arr = json.loads(q.get("input") or "[]")
                except json.JSONDecodeError:
                    inp_arr = []
                if isinstance(inp_arr, list):
                    for sub_i, part in enumerate(inp_arr):
                        if not isinstance(part, dict):
                            continue
                        if isinstance(part.get("Query"), dict):
                            qtxt = str(part["Query"].get("text") or "").strip()
                            if qtxt:
                                raw_items.append({
                                    "node_id": f"{q.get('exchange_id') or idx}-q-{sub_i}",
                                    "role": "user",
                                    "text": qtxt,
                                    "timestamp": q.get("start_ts"),
                                    "content": qtxt,
                                    "raw_record": {"exchange_id": q.get("exchange_id"), "query": qtxt},
                                })
                        elif isinstance(part.get("ActionResult"), dict):
                            ar = part["ActionResult"]
                            out_txt = content_text(ar.get("result", ""))
                            if out_txt.strip():
                                raw_items.append({
                                    "node_id": str(ar.get("id") or f"{idx}-ar-{sub_i}"),
                                    "role": "tool_result",
                                    "text": out_txt[:4000],
                                    "timestamp": q.get("start_ts"),
                                    "content": {"call_id": str(ar.get("id") or ""), "output": out_txt[:4000]},
                                    "raw_record": {"exchange_id": q.get("exchange_id")},
                                    "event_type": "tool_result",
                                })
            if not raw_items and summary_obj.get("initial_query"):
                iq = str(summary_obj["initial_query"]).strip()
                if iq:
                    raw_items.append({"node_id": f"{cid}-init", "role": "user", "text": iq, "timestamp": cr["last_modified_at"], "content": iq, "raw_record": summary_obj})
            nodes, roots, active = _chain(raw_items)
            graphs.append(
                ConversationGraph(
                    source_format="warp_oz_session",
                    source_id=cid,
                    title=title,
                    workspace=str(ws) if isinstance(ws, str) and ws else None,
                    nodes=nodes,
                    root_ids=roots,
                    active_node_id=active,
                    metadata={
                        "source_file": p.name,
                        "agent_mode": "oz",
                        "model": model_id,
                        "project_name": Path(str(ws)).name if isinstance(ws, str) and ws not in {"", "/"} else None,
                        "last_modified_time": str(cr["last_modified_at"] or ""),
                    },
                    raw_source={"summary": summary_obj},  # Never copy `server_conversation_token`!
                    links=_links(nodes),
                    app_mode="terminal-agent",
                )
            )
    finally:
        conn.close()
    return graphs


def parse_warp_oz_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        if p.suffix in {".sqlite", ".db"}:
            return parse_warp_sqlite(p, limit=limit)
        return [parse_warp_oz_session(p)]
    graphs = _scan_dir_sessions(p, ("sessions",), ("*.json",), parse_warp_oz_session, exclude_names={"mcp.json", ".mcp.json"}, limit=limit)
    if limit and len(graphs) >= limit:
        return graphs[:limit]
    rem = (limit - len(graphs)) if limit else None
    candidate_dbs = [p / "warp.sqlite"]
    if sys.platform == "darwin":
        candidate_dbs.append(
            Path.home()
            / "Library/Group Containers/2BBY89MBSN.dev.warp/Library/Application Support/dev.warp.Warp-Stable/warp.sqlite"
        )
    for db_cand in candidate_dbs:
        if db_cand.is_file():
            seen = {g.source_id for g in graphs}
            for g in parse_warp_sqlite(db_cand, limit=rem):
                if g.source_id not in seen:
                    seen.add(g.source_id)
                    graphs.append(g)
                    if limit and len(graphs) >= limit:
                        return graphs[:limit]
            break
    return graphs


def parse_windsurf_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        return [parse_windsurf_session(p)]
    return _scan_dir_sessions(p, ("cascade",), ("*.json",), parse_windsurf_session, exclude_names={"mcp_config.json"}, limit=limit)


def parse_windsurf_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    sid = str(data.get("cascadeId") or data.get("id") or p.stem)
    raw_items: list[dict[str, Any]] = []
    for idx, step in enumerate(data.get("steps", data.get("messages", []))):
        if not isinstance(step, dict):
            continue
        role = str(step.get("role") or ("user" if step.get("type") == "user_input" else "assistant"))
        c = step.get("content", step.get("text", ""))
        raw_items.append({"node_id": str(step.get("id") or f"ws-{idx}"), "role": role, "text": content_text(c), "timestamp": step.get("timestamp"), "content": c, "raw_record": step})
    nodes, roots, active = _chain(raw_items)
    return ConversationGraph(source_format="windsurf_cascade", source_id=sid, title=str(data.get("title") or sid), workspace=data.get("workspace") or data.get("cwd"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name}, raw_source=data, links=_links(nodes), app_mode="ide-extension")


def build_windsurf_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"ws-{uuid.uuid4().hex[:12]}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        steps = [{"id": str(uuid.uuid4()), "type": "user_input" if t["role"] == "user" else "planner_response", "role": t["role"], "text": "\n\n".join(t["texts"]), "timestamp": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        payload = {"schema": "windsurf.cascade.v1", "cascadeId": sid, "title": title, "workspace": resolved_cwd, "steps": steps}
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": payload})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_windsurf_cascade_per_leaf_path; exact graph in portable.json"})
    return sessions, losses
