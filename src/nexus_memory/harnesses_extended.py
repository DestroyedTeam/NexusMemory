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
import sqlite3
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .claude_code import _coalesce_alternating_turns
from .model import ConversationGraph, MessageNode, UsageSummary, content_text, extract_links


def _chain(raw_items: list[dict[str, Any]]) -> tuple[tuple[MessageNode, ...], tuple[str, ...], str | None]:
    nodes: list[MessageNode] = []
    prev_id: str | None = None
    for idx, item in enumerate(raw_items):
        nid = str(item.get("node_id") or f"ext-{idx}")
        if any(n.node_id == nid for n in nodes):
            nid = f"{nid}-{idx}"
        if nodes:
            p = nodes[-1]
            nodes[-1] = MessageNode(
                p.node_id, p.parent_id, (nid,), p.role, p.text, p.timestamp, p.content, p.raw_record,
                event_type=p.event_type, parent_tool_use_id=p.parent_tool_use_id,
                attachments=p.attachments, links=p.links, usage=p.usage,
                interrupted=p.interrupted, is_sidechain=p.is_sidechain,
            )
        text = str(item.get("text") or "")
        nodes.append(
            MessageNode(
                node_id=nid,
                parent_id=prev_id,
                child_ids=(),
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
        prev_id = nid
    return tuple(nodes), ((nodes[0].node_id,) if nodes else ()), (nodes[-1].node_id if nodes else None)


def _links(nodes: tuple[MessageNode, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for n in nodes:
        for u in n.links:
            if u not in seen:
                seen.add(u)
                out.append(u)
    return tuple(out)


# ── 1. Tencent WorkBuddy (`~/.workbuddy/workbuddy.db` + `sessions/*.jsonl`) ──


def parse_workbuddy_session(path: str | Path) -> ConversationGraph:
    """Read a WorkBuddy JSONL/JSON session file."""
    p = Path(path).expanduser()
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    raw_items: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"source_file": p.name}
    sid = p.stem
    title = p.stem
    workspace: str | None = None
    records: list[dict[str, Any]] = []

    if p.suffix == ".jsonl":
        for idx, ln in enumerate(text.splitlines()):
            if not ln.strip():
                continue
            r = json.loads(ln)
            if not isinstance(r, dict):
                continue
            records.append(r)
            if r.get("type") == "workbuddy_session_meta":
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
            role = str(r.get("role") or r.get("type") or "")
            if role in {"user", "assistant", "system", "tool_call", "tool_result"}:
                c = r.get("content", r.get("text", ""))
                raw_items.append({
                    "node_id": str(r.get("id") or f"wb-{idx}"),
                    "role": role,
                    "text": content_text(c),
                    "timestamp": r.get("timestamp") or r.get("created_at"),
                    "content": c,
                    "raw_record": r,
                    "event_type": str(r.get("event_type") or ("tool_use" if role == "tool_call" else "message")),
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
    """Read WorkBuddy `~/.workbuddy` (`workbuddy.db` + `sessions/`)."""
    root = Path(wb_home).expanduser()
    graphs: list[ConversationGraph] = []
    seen: set[str] = set()

    # 1. Read session files under sessions/
    sdir = root / "sessions"
    if sdir.is_dir():
        for fp in sorted(list(sdir.glob("*.jsonl")) + list(sdir.glob("*.json"))):
            if fp.is_file():
                g = parse_workbuddy_session(fp)
                graphs.append(g)
                seen.add(g.source_id)
                if limit and len(graphs) >= limit:
                    return graphs

    # 2. Enrich or read metadata rows from workbuddy.db (strictly read-only!)
    db = root / "workbuddy.db"
    if db.is_file():
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            spaces: dict[str, str] = {}
            if "spaces" in tables:
                for r in conn.execute("SELECT id, name FROM spaces"):
                    spaces[str(r["id"])] = str(r["name"] or "")
            if "sessions" in tables:
                for r in conn.execute("SELECT * FROM sessions WHERE deleted_at IS NULL"):
                    d = dict(r)
                    sid = str(d.get("id") or "")
                    if not sid or sid in seen:
                        continue
                    graphs.append(
                        ConversationGraph(
                            source_format="workbuddy_sqlite",
                            source_id=sid,
                            title=str(d.get("custom_title") or d.get("title") or sid),
                            workspace=d.get("cwd"),
                            nodes=(),
                            root_ids=(),
                            active_node_id=None,
                            metadata={
                                "project_id": d.get("project_id") or d.get("space_id"),
                                "project_name": spaces.get(str(d.get("space_id") or "")) or None,
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
                    seen.add(sid)
                    if limit and len(graphs) >= limit:
                        break
            conn.close()
        except sqlite3.Error:
            pass
    return graphs


def build_workbuddy_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project ConversationGraph into WorkBuddy `sessions/<id>.jsonl` with space/group metadata."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
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
                "title": title,
                "custom_title": title,
                "cwd": resolved_cwd,
                "project_id": graph.metadata.get("project_id"),
                "project_name": graph.metadata.get("project_name"),
                "group_id": graph.metadata.get("section_id"),
                "group_title": graph.metadata.get("section_name"),
                "parent_session_id": graph.metadata.get("parent_session_id"),
                "model": graph.metadata.get("model") or "auto",
                "mode": "agent",
                "created_at": now_iso,
            }
        ]
        source_node_ids: list[str] = []
        for idx, t in enumerate(turns):
            records.append({
                "id": f"wbm-{idx}",
                "role": t["role"],
                "content": "\n\n".join(t["texts"]),
                "timestamp": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso,
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


def merge_t3code_thread_into_statev2(
    db_path: str | Path,
    payload: dict[str, Any],
    *,
    on_collision: str = "refuse",
) -> dict[str, Any]:
    """Merge a staged `t3code.thread.v2` payload natively into T3 Code's `statev2.sqlite`.

    Follows T3 Code's official `agentSessionImporter.ts` (`importRecentAgentThreadsV2` +
    `messageEvents`) contract verbatim:
    - Creates/reuses a valid `projection_projects` entry (never `/` root; falls back to `No project`)
    - Emits `historyOrigin: "v1_import"` thread into `orchestration_v2_projection_threads` + `thread.created`
    - Emits run-less (`runId: null, nodeId: null`) messages & turn items (`ordinal = 1..N`) into
      `orchestration_v2_projection_messages`, `orchestration_v2_projection_turn_items`,
      `orchestration_v2_turn_item_positions`, and `orchestration_events` (`application_event_version = 2`)
    - Advances `orchestration_v2_projection_metadata.last_sequence`; native SQLite triggers
      automatically maintain FTS5 search and turn-item count tables.
    """
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_dt = datetime.now(UTC)
    now_iso = now_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    import_prefix = "agent-session-import:v2"

    sid = str(payload.get("threadId") or uuid.uuid4())
    raw_title = str(payload.get("title") or "").strip()
    title = (raw_title or "Untitled thread")[:240]
    workspace_path = str(payload.get("workspacePath") or "").strip()
    # Never create a bogus "/" filesystem-root project in T3 Code
    if workspace_path in {"", "/", "\\"}:
        workspace_path = ""
    else:
        wp = Path(workspace_path)
        if len(wp.parts) <= 1:
            workspace_path = ""

    def _iso_utc(val: Any, fallback: str) -> str:
        if isinstance(val, str) and val.strip():
            s = val.strip()
            if s.endswith("Z") or "+" in s[10:]:
                return s
            if "T" in s:
                return s + "Z"
        return fallback

    created_at = _iso_utc(payload.get("createdAt"), now_iso)
    updated_at = _iso_utc(payload.get("updatedAt"), created_at)
    parent_tid = payload.get("parentThreadId")
    raw_provider = str(payload.get("provider") or "").strip()
    provider_id, default_model = _t3code_provider_for_source(raw_provider)
    if raw_provider in {"antigravity", "codex", "claudeAgent", "cursor", "opencode", "pi", "kiro"}:
        provider_id = raw_provider
    messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []

    conn = sqlite3.connect(str(db), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_t3code_statev2_schema(conn)
        existing = conn.execute(
            "SELECT thread_id FROM orchestration_v2_projection_threads WHERE thread_id = ?",
            (sid,),
        ).fetchone()
        if existing:
            if on_collision == "refuse":
                raise FileExistsError(f"t3code thread_id already exists in statev2.sqlite: {sid}")
            if on_collision == "skip":
                return {"thread_id": sid, "action": "skipped", "message_count": 0}
            if on_collision == "rename":
                sid = str(uuid.uuid4())

        # Reuse configured modelSelection from an existing thread using the same provider if present
        existing_model_row = conn.execute(
            "SELECT payload_json FROM orchestration_v2_projection_threads WHERE default_provider = ? LIMIT 1",
            (provider_id,),
        ).fetchone()
        model_selection: dict[str, Any] = {
            "instanceId": provider_id,
            "model": default_model,
        }
        if existing_model_row:
            try:
                ep = json.loads(existing_model_row[0])
                if isinstance(ep.get("modelSelection"), dict):
                    model_selection = ep["modelSelection"]
            except json.JSONDecodeError:
                pass

        # Resolve or create project in `projection_projects` (matching T3 Code's project.created schema)
        project_id: str | None = None
        if workspace_path:
            prow = conn.execute(
                "SELECT project_id FROM projection_projects WHERE workspace_root = ? AND deleted_at IS NULL LIMIT 1",
                (workspace_path,),
            ).fetchone()
            if prow:
                project_id = str(prow["project_id"])
            else:
                project_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"nexus-t3code-project:{workspace_path}"))
                proj_title = Path(workspace_path).name or "Imported Project"
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
        if not project_id:
            fallback_row = conn.execute(
                "SELECT project_id FROM projection_projects WHERE deleted_at IS NULL ORDER BY created_at LIMIT 1"
            ).fetchone()
            if fallback_row:
                project_id = str(fallback_row["project_id"])
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

        # Exact `appThread` shape from T3 Code's `agentSessionImporter.ts`
        thread_payload = {
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
                "parentThreadId": parent_tid if isinstance(parent_tid, str) and parent_tid.strip() else None,
                "relationshipToParent": None,
                "rootThreadId": sid,
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

        # Exact run-less `messageEvents` shape from T3 Code's `agentSessionImporter.ts`
        inserted_msgs = 0
        for idx, m in enumerate(messages):
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

        # Keep projection sequence watermark aligned with orchestration_events
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
        return {"thread_id": sid, "project_id": project_id, "action": "merged", "message_count": inserted_msgs}
    finally:
        conn.close()


def parse_t3code_source(path: str | Path) -> list[ConversationGraph]:
    """Read T3 Code `statev2.sqlite` (v2 `orchestration_v2_projection_*` or legacy tables) or thread JSON."""
    p = Path(path).expanduser()
    if p.is_dir():
        db = p / "userdata" / "statev2.sqlite"
        if db.is_file():
            return parse_t3code_source(db)
        out: list[ConversationGraph] = []
        for fp in sorted(p.rglob("*.json")):
            if fp.name != "settings.json":
                try:
                    out.extend(parse_t3code_source(fp))
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
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
                    lineage = tp.get("lineage") if isinstance(tp.get("lineage"), dict) else {}
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
                                "parent_session_id": lineage.get("parentThreadId"),
                                "provider": td.get("provider_instance_id") or td.get("default_provider"),
                                "source_file": p.name,
                            },
                            raw_source={"thread": tp or td},
                            links=_links(nodes),
                            app_mode="desktop-app",
                        )
                    )
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
    """Project ConversationGraph into T3 Code v2 thread payloads (merged into `userdata/statev2.sqlite`)."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    provider_id, _ = _t3code_provider_for_source(graph.metadata.get("provider") or graph.source_format)
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        msgs = [{"id": str(uuid.uuid4()), "role": t["role"], "content": "\n\n".join(t["texts"]), "createdAt": t["timestamp"] if isinstance(t["timestamp"], str) else now_iso} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        payload = {
            "schema": "t3code.thread.v2",
            "threadId": sid,
            "title": title,
            "workspacePath": resolved_cwd,
            "projectId": graph.metadata.get("project_id"),
            "projectName": graph.metadata.get("project_name"),
            "sectionName": graph.metadata.get("section_name"),
            "parentThreadId": graph.metadata.get("parent_session_id"),
            "provider": provider_id,
            "createdAt": now_iso,
            "updatedAt": now_iso,
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


# ── 7. Windsurf Cascade (`~/.codeium/windsurf/cascade/<id>.json`) ────────────


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
