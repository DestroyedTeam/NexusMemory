"""Broad cross-Harness deterministic readers & bidirectional writers + auto-format loader.

Read + Write supported:
- OpenCode (both split `~/.local/share/opencode/storage/{project,session,message,part}` AND single JSON)
- Pi (`~/.pi/agent/sessions/**/*.jsonl` native tree-DAG `id`/`parentId` round-trip!)
- DeepSeek Harness / DSH (V4 authority > stale V2 + V4 writer)
- Gemini CLI (`~/.gemini/tmp/<slug>/chats/session-*.json` read + write)
- Cline / Roo Code (`tasks/<id>/api_conversation_history.json` read + write)
- Goose (`sessions/<id>.jsonl` read + write)
- Continue (`sessions/<id>.json` read + write)
- Zed / ACP (`threads/<id>.json` read + write)
- Aider (`.aider.chat.history.md` read + write)
- Portable Canonical Bundle (`portable.json` v1 & v2 lossless round-trip)

Read-only (protecting proprietary/live IDE stores):
- Antigravity (`~/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript.jsonl` — read-only!)
- Cursor (`state.vscdb` SQLite `composerData`/`bubbleId` — read-only!)
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import urllib.parse
import uuid
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .chatgpt import parse_export_with_assets
from .claude_code import _coalesce_alternating_turns, parse_claude_code_dir, parse_claude_code_session
from .claude_desktop_3p import parse_claude_desktop_3p_root, parse_local_agent_session
from .codex import parse_codex_app_snapshot, parse_codex_home, parse_rollout
from .harnesses_extended import (
    build_amp_sessions,
    build_kiro_sessions,
    build_t3code_sessions,
    build_trae_sessions,
    build_warp_oz_sessions,
    build_windsurf_sessions,
    build_workbuddy_sessions,
    parse_amp_home,
    parse_amp_thread,
    parse_kiro_home,
    parse_kiro_session,
    parse_t3code_source,
    parse_trae_home,
    parse_trae_trajectory,
    parse_warp_oz_home,
    parse_warp_oz_session,
    parse_warp_sqlite,
    parse_windsurf_home,
    parse_windsurf_session,
    parse_workbuddy_home,
    parse_workbuddy_session,
)
from .model import AssetRecord, ConversationGraph, MessageNode, UsageSummary, content_text, extract_links
from .security import sanitize_single_segment


def _chain_linear(raw_items: list[dict[str, Any]]) -> tuple[tuple[MessageNode, ...], tuple[str, ...], str | None]:
    """O(N) linear node chaining (uses a `set` for ID deduplication instead of O(N^2) scan)."""
    if not raw_items:
        return (), (), None
    nids: list[str] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(raw_items):
        nid = str(item.get("node_id") or f"n-{idx}")
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


def _collect_links(nodes: tuple[MessageNode, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for n in nodes:
        for u in n.links:
            if u not in seen:
                seen.add(u)
                out.append(u)
    return tuple(out)


# ── 1. Portable Canonical Bundle (v1 & v2) ───────────────────────────────────


def parse_portable_bundle(path: str | Path) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_dir():
        p = p / "portable.json"
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    graphs: list[ConversationGraph] = []
    for c in data.get("conversations", []):
        if not isinstance(c, dict):
            continue
        nodes = tuple(
            MessageNode(
                node_id=str(n["node_id"]),
                parent_id=n.get("parent_id"),
                child_ids=tuple(n.get("child_ids", ())),
                role=n.get("role"),
                text=str(n.get("text", "")),
                timestamp=n.get("timestamp"),
                content=n.get("content"),
                raw_record=n.get("raw_record", {}),
                event_type=str(n.get("event_type", "message")),
                parent_tool_use_id=n.get("parent_tool_use_id"),
                attachments=tuple(n.get("attachments", ())),
                links=tuple(n.get("links", ())),
                usage=n.get("usage"),
                interrupted=bool(n.get("interrupted", False)),
                is_sidechain=bool(n.get("is_sidechain", False)),
            )
            for n in c.get("nodes", [])
        )
        assets = tuple(AssetRecord(**a) for a in c.get("assets", []) if isinstance(a, dict))
        raw_usage = c.get("usage")
        usage = UsageSummary(**raw_usage) if isinstance(raw_usage, dict) else None
        graphs.append(
            ConversationGraph(
                source_format=str(c.get("source_format", "portable")),
                source_id=str(c["source_id"]),
                title=c.get("title"),
                workspace=c.get("workspace"),
                nodes=nodes,
                root_ids=tuple(c.get("root_ids", ())),
                active_node_id=c.get("active_node_id"),
                metadata=dict(c.get("metadata", {})),
                raw_source=dict(c.get("raw_source", {})),
                assets=assets,
                usage=usage,
                links=tuple(c.get("links", ())),
                app_mode=c.get("app_mode"),
            )
        )
    return graphs


# ── 2. Antigravity (`transcript.jsonl` — strictly read-only!) ────────────────


def _decode_workspace_uri(raw_uris: str | None) -> str | None:
    if not raw_uris:
        return None
    val = raw_uris.strip()
    uris: list[str] = []
    if val.startswith("["):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                uris = [str(x) for x in parsed if isinstance(x, str) and x.strip()]
        except json.JSONDecodeError:
            pass
    elif val:
        uris = [val]
    for u in uris:
        if u.startswith("file://"):
            decoded = urllib.parse.unquote(u[len("file://") :])
            if decoded and decoded not in {"/", "\\"}:
                return decoded
        elif u.startswith("/") and u != "/":
            return u
    return None


def _load_antigravity_summaries_db(ag_root: Path) -> dict[str, dict[str, Any]]:
    """Read `~/.gemini/antigravity/conversation_summaries.db` (strictly read-only) for real titles, workspaces, projects, and parent/subagent lineage."""
    db_path = ag_root / "conversation_summaries.db"
    if not db_path.is_file():
        return {}
    rows_by_id: dict[str, dict[str, Any]] = {}
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
        con.row_factory = sqlite3.Row
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(conversation_summaries)")}
            if "conversation_id" not in cols:
                return {}
            for r in con.execute(
                """
                SELECT conversation_id, title, workspace_uris, project_id, agent_name,
                       parent_conversation_id, nesting_depth, last_modified_time, group_id, step_count
                FROM conversation_summaries
                """
            ):
                cid = str(r["conversation_id"] or "")
                if not cid:
                    continue
                ws = _decode_workspace_uri(r["workspace_uris"])
                pid = str(r["project_id"] or "").strip()
                if pid == "outside-of-project":
                    pid = ""
                parent_id = str(r["parent_conversation_id"] or "").strip() or None
                rows_by_id[cid] = {
                    "conversation_id": cid,
                    "title": str(r["title"] or "").strip(),
                    "workspace": ws,
                    "project_id": pid or None,
                    "project_name": Path(ws).name if ws else None,
                    "subagent_role": str(r["agent_name"] or "").strip() or None,
                    "parent_session_id": parent_id,
                    "nesting_depth": int(r["nesting_depth"] or 0),
                    "last_modified_time": str(r["last_modified_time"] or "").strip() or None,
                    "section_id": str(r["group_id"] or "").strip() or None,
                    "step_count": int(r["step_count"] or 0),
                }
        finally:
            con.close()
    except sqlite3.Error:
        return {}

    for cid, rec in rows_by_id.items():
        cur = cid
        seen = {cur}
        while True:
            parent = (rows_by_id.get(cur) or {}).get("parent_session_id")
            if not parent or parent in seen or parent not in rows_by_id:
                break
            seen.add(parent)
            cur = parent
        rec["root_session_id"] = cur
    return rows_by_id


def parse_antigravity_transcript(path: str | Path, *, summary: dict[str, Any] | None = None) -> ConversationGraph:
    """Strictly read-only reader for Google Antigravity `transcript.jsonl` + `conversation_summaries.db`/sidecar/artifacts/subagents."""
    p = Path(path).expanduser()
    conv_dir = p
    if p.is_dir():
        cand = p / ".system_generated" / "logs" / "transcript.jsonl"
        p = cand if cand.is_file() else (p / "transcript.jsonl")
    else:
        conv_dir = p.parents[2] if len(p.parents) >= 3 and p.parent.name == "logs" else p.parent
    conv_id = conv_dir.name if (conv_dir / ".system_generated" / "logs" / "transcript.jsonl").is_file() else p.stem

    if summary is None and conv_dir.parent.name == "brain":
        summaries = _load_antigravity_summaries_db(conv_dir.parent.parent)
        summary = summaries.get(conv_id)

    sidecar: dict[str, Any] = {}
    for meta_name in ("metadata.json", "conversation_meta.json"):
        mp = conv_dir / meta_name
        if mp.is_file():
            try:
                loaded = json.loads(mp.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict):
                    sidecar = loaded
                    break
            except (json.JSONDecodeError, OSError):
                pass
    s = summary or {}

    raw_items: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    spawned_subagents: list[dict[str, Any]] = []
    for idx, line in enumerate(p.read_text(encoding="utf-8-sig", errors="replace").splitlines()):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(r, dict):
            continue
        records.append(r)
        rtype = str(r.get("type") or "")
        ts = r.get("created_at")
        if rtype == "USER_INPUT":
            content = str(r.get("content") or "")
            u_start = content.find("<USER_REQUEST>")
            if u_start != -1:
                u_end = content.find("</USER_REQUEST>", u_start + 14)
                clean_text = content[u_start + 14 : u_end].strip() if u_end != -1 else content.strip()
            else:
                clean_text = content.strip()
            if clean_text:
                raw_items.append({"node_id": f"ag-{idx}", "role": "user", "text": clean_text, "timestamp": ts, "content": clean_text, "raw_record": r, "event_type": "message"})
        elif rtype == "PLANNER_RESPONSE":
            text = str(r.get("content") or "").strip()
            tool_calls = r.get("tool_calls") if isinstance(r.get("tool_calls"), list) else []
            if text:
                raw_items.append({"node_id": f"ag-{idx}", "role": "assistant", "text": text, "timestamp": ts, "content": text, "raw_record": r, "event_type": "message"})
            for t_i, tc in enumerate(tool_calls):
                if isinstance(tc, dict):
                    tname = str(tc.get("name") or "tool")
                    call_id = str(tc.get("id") or f"ag-tc-{idx}-{t_i}")
                    args = tc.get("args", tc.get("arguments", {}))
                    if tname == "invoke_subagent" and isinstance(args, dict):
                        spawned_subagents.append({"role": args.get("Role"), "type": args.get("TypeName"), "call_id": call_id})
                    raw_items.append({
                        "node_id": f"ag-{idx}-tc-{t_i}",
                        "role": "tool_call",
                        "text": f"tool:{tname}",
                        "timestamp": ts,
                        "content": {"call_id": call_id, "name": tname, "arguments": args},
                        "raw_record": tc,
                        "event_type": "tool_use",
                    })
        elif rtype == "GENERIC" and r.get("tool"):
            out_str = str(r.get("content") or "")
            if r.get("tool") == "invoke_subagent":
                cm = re.search(r'"conversationId"\s*:\s*"([0-9a-f-]{36})"', out_str)
                if cm:
                    spawned_subagents.append({"child_conversation_id": cm.group(1), "call_id": str(r.get("call_id") or "")})
            raw_items.append({
                "node_id": f"ag-{idx}",
                "role": "tool_result",
                "text": out_str,
                "timestamp": ts,
                "content": {"call_id": str(r.get("call_id") or r.get("tool_call_id") or ""), "tool": r.get("tool"), "output": out_str},
                "raw_record": r,
                "event_type": "tool_result",
            })

    assets: list[AssetRecord] = []
    if conv_dir.is_dir():
        for af in sorted(conv_dir.iterdir()):
            if af.is_file() and not af.name.startswith(".") and af.name not in {"metadata.json", "conversation_meta.json"}:
                assets.append(
                    AssetRecord(
                        asset_id=f"ag-asset-{af.name}",
                        source_ref=str(af.name),
                        filename=af.name,
                        mime_type=mimetypes.guess_type(af.name)[0] or "application/octet-stream",
                        size_bytes=af.stat().st_size,
                        disposition="external_reference_only",
                    )
                )

    nodes, roots, active = _chain_linear(raw_items)
    first_user = next((n.text for n in nodes if n.role == "user" and n.text.strip()), None)
    resolved_ws = sidecar.get("workspace") or sidecar.get("cwd") or s.get("workspace")
    sub_role = sidecar.get("subagent_role") or s.get("subagent_role")
    fallback_title = first_user[:80].splitlines()[0].strip() if first_user else conv_id
    if not (sidecar.get("title") or s.get("title")) and sub_role:
        fallback_title = f"[{sub_role}] {fallback_title}"
    title = str(sidecar.get("title") or s.get("title") or fallback_title)
    parent_sid = sidecar.get("parent_session_id") or s.get("parent_session_id")
    meta: dict[str, Any] = {
        "record_count": len(records),
        "source_file": p.name,
        "project_id": sidecar.get("project_id") or s.get("project_id"),
        "project_name": sidecar.get("project_name") or s.get("project_name") or (Path(resolved_ws).name if resolved_ws else None),
        "section_id": sidecar.get("section_id") or s.get("section_id"),
        "section_name": sidecar.get("section_name"),
        "parent_session_id": parent_sid,
        "root_session_id": s.get("root_session_id") or conv_id,
        "nesting_depth": int(sidecar.get("nesting_depth") or s.get("nesting_depth") or (1 if parent_sid else 0)),
        "subagent_role": sub_role,
        "last_modified_time": s.get("last_modified_time"),
        "spawned_subagents": spawned_subagents,
    }
    return ConversationGraph(
        source_format="antigravity_transcript",
        source_id=conv_id,
        title=title,
        workspace=resolved_ws,
        nodes=nodes,
        root_ids=roots,
        active_node_id=active,
        metadata=meta,
        raw_source={"records_count": len(records), "sidecar": sidecar},
        assets=tuple(assets),
        links=_collect_links(nodes),
        app_mode="ide-extension",
    )


def parse_antigravity_brain_dir(
    brain_dir: str | Path,
    *,
    limit: int | None = None,
    include_subagents: bool = False,
    project_filter: str | None = None,
    section_filter: str | None = None,
    on_progress: Callable[[str, int, int, str], None] | None = None,
) -> list[ConversationGraph]:
    """Read multi-session Antigravity `brain/` directory in parallel using `conversation_summaries.db`."""
    base = Path(brain_dir).expanduser()
    ag_root = base if (base / "brain").is_dir() else (base.parent if base.name == "brain" else base)
    root = base / "brain" if (base / "brain").is_dir() else base
    if (root / ".system_generated" / "logs" / "transcript.jsonl").is_file() or (root / "transcript.jsonl").is_file():
        return [parse_antigravity_transcript(root)]

    summaries = _load_antigravity_summaries_db(ag_root)
    candidates: list[tuple[Path, dict[str, Any] | None]] = []
    children_by_parent: dict[str, list[tuple[Path, dict[str, Any] | None]]] = {}

    for child in root.iterdir():
        if not child.is_dir():
            continue
        tfile = child / ".system_generated" / "logs" / "transcript.jsonl"
        if not tfile.is_file():
            tfile = child / "transcript.jsonl"
        if not tfile.is_file():
            continue
        s = summaries.get(child.name)
        parent_id = (s or {}).get("parent_session_id")
        depth = int((s or {}).get("nesting_depth") or (1 if parent_id else 0))
        if depth > 0 and parent_id:
            children_by_parent.setdefault(parent_id, []).append((child, s))
        else:
            candidates.append((child, s))

    pf = (project_filter or "").strip().lower()
    sf = (section_filter or "").strip().lower()
    if pf or sf:
        filtered: list[tuple[Path, dict[str, Any] | None]] = []
        for child, s in candidates:
            sd = s or {}
            hay_p = " ".join(str(x or "") for x in (sd.get("project_name"), sd.get("workspace"), sd.get("title"), child.name)).lower()
            hay_s = " ".join(str(x or "") for x in (sd.get("section_id"), sd.get("title"))).lower()
            if pf and pf not in hay_p:
                continue
            if sf and sf not in hay_s:
                continue
            filtered.append((child, s))
        candidates = filtered

    candidates.sort(
        key=lambda item: (
            str((item[1] or {}).get("last_modified_time") or ""),
            item[0].stat().st_mtime,
        ),
        reverse=True,
    )
    if limit:
        candidates = candidates[:limit]

    ordered_targets: list[tuple[Path, dict[str, Any] | None]] = []
    if include_subagents:
        # DFS pre-order so each parent session is immediately followed by its nested children (parent-before-child)
        seen_ids: set[str] = set()
        for top_path, top_sum in candidates:
            stack: list[tuple[Path, dict[str, Any] | None]] = [(top_path, top_sum)]
            while stack:
                cur_path, cur_sum = stack.pop()
                if cur_path.name in seen_ids:
                    continue
                seen_ids.add(cur_path.name)
                ordered_targets.append((cur_path, cur_sum))
                kids = sorted(
                    children_by_parent.get(cur_path.name, []),
                    key=lambda x: str((x[1] or {}).get("last_modified_time") or ""),
                    reverse=True,
                )
                for ch_path, ch_sum in kids:
                    if ch_path.name not in seen_ids:
                        stack.append((ch_path, ch_sum))
    else:
        ordered_targets = list(candidates)

    total = len(ordered_targets)
    if on_progress:
        on_progress("parse", 0, total, "准备并发解析 Antigravity 会话")

    def _parse_one(idx_item: tuple[int, tuple[Path, dict[str, Any] | None]]) -> tuple[int, ConversationGraph | None]:
        idx, (cpath, csum) = idx_item
        try:
            g = parse_antigravity_transcript(cpath, summary=csum)
            direct_kids = children_by_parent.get(cpath.name, [])
            if direct_kids:
                g.metadata["child_subagent_count"] = len(direct_kids)
            return idx, g
        except (OSError, ValueError):
            return idx, None

    results: list[tuple[int, ConversationGraph | None]] = []
    if total >= 4:
        workers = min(8, os.cpu_count() or 4, total)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            done_n = 0
            for res in pool.map(_parse_one, enumerate(ordered_targets)):
                results.append(res)
                done_n += 1
                if on_progress:
                    lbl = res[1].title[:40] if res[1] else ""
                    on_progress("parse", done_n, total, lbl)
    else:
        for i, item in enumerate(ordered_targets):
            res = _parse_one((i, item))
            results.append(res)
            if on_progress:
                lbl = res[1].title[:40] if res[1] else ""
                on_progress("parse", i + 1, total, lbl)

    results.sort(key=lambda r: r[0])
    return [g for _, g in results if g is not None]


def build_antigravity_sessions(
    graph: ConversationGraph,
    *,
    cwd: str | Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project ConversationGraph into Antigravity `brain/<conv-id>/.system_generated/logs/transcript.jsonl` + `metadata.json`."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    if not paths:
        losses.append({"feature": "empty_conversation", "disposition": "skipped_zero_node_conversation"})
        return sessions, losses

    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    for branch_index, path in enumerate(paths, 1):
        turns, merged, _ = _coalesce_alternating_turns(path)
        conv_id = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"

        records: list[dict[str, Any]] = []
        source_node_ids: list[str] = []
        for idx, t in enumerate(turns):
            ts = t["timestamp"] if isinstance(t["timestamp"], str) and t["timestamp"] else now_iso
            body = "\n\n".join(t["texts"])
            if t["role"] == "user":
                records.append(
                    {
                        "step_index": idx,
                        "type": "USER_INPUT",
                        "created_at": ts,
                        "source": "user",
                        "status": "DONE",
                        "content": f"<USER_REQUEST>\n{body}\n</USER_REQUEST>",
                    }
                )
            else:
                records.append(
                    {
                        "step_index": idx,
                        "type": "PLANNER_RESPONSE",
                        "created_at": ts,
                        "source": "planner",
                        "status": "DONE",
                        "content": body,
                    }
                )
            source_node_ids.extend(t["source_node_ids"])

        meta_payload = {
            "conversation_id": conv_id,
            "title": title,
            "workspace": resolved_cwd,
            "project_id": graph.metadata.get("project_id"),
            "project_name": graph.metadata.get("project_name"),
            "section_id": graph.metadata.get("section_id"),
            "section_name": graph.metadata.get("section_name"),
            "parent_session_id": graph.metadata.get("parent_session_id"),
            "imported_from": f"nexus-memory:{graph.source_format}:{graph.source_id}",
            "created_at": now_iso,
        }
        sessions.append(
            {
                "session_id": conv_id,
                "branch_index": branch_index,
                "title": title,
                "cwd": resolved_cwd,
                "source_node_ids": source_node_ids,
                "records": records,
                "meta_payload": meta_payload,
            }
        )
        if merged:
            losses.append({"feature": "consecutive_same_role_coalescing", "disposition": f"merged {merged} turn(s) for clean Antigravity replay"})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_antigravity_brain_dir_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 3. OpenCode (`opencode.db` SQLite v1/v2 + `opencode session export` JSON + split `storage/`) ──

_OPENCODE_V2_MIGRATION_IDS: tuple[str, ...] = (
    "20260127222353_familiar_lady_ursula",
    "20260211171708_add_project_commands",
    "20260213144116_wakeful_the_professor",
    "20260225215848_workspace",
    "20260227213759_add_session_workspace_id",
    "20260228203230_blue_harpoon",
    "20260303231226_add_workspace_fields",
    "20260309230000_move_org_to_state",
    "20260312043431_session_message_cursor",
    "20260323234822_events",
    "20260410174513_workspace-name",
    "20260413175956_chief_energizer",
    "20260423070820_add_icon_url_override",
    "20260427172553_slow_nightmare",
    "20260428004200_add_session_path",
    "20260501142318_next_venus",
    "20260504145000_add_sync_owner",
    "20260507164347_add_workspace_time",
    "20260510033149_session_usage",
    "20260511000411_data_migration_state",
    "20260511173437_session-metadata",
    "20260601010001_normalize_storage_paths",
    "20260601202201_amazing_prowler",
    "20260602002951_lowly_union_jack",
    "20260602182828_add_project_directories",
    "20260603001617_session_message_projection_indexes",
    "20260603040000_session_message_projection_order",
    "20260603141458_session_input_inbox",
    "20260603160727_jittery_ezekiel_stane",
    "20260604172448_event_sourced_session_input",
    "20260605003541_add_session_context_snapshot",
    "20260605042240_add_context_epoch_agent",
    "20260611035744_credential",
    "20260611192811_lush_chimera",
    "20260612174303_project_dir_strategy",
    "20260622142730_simplify_session_context_epoch",
    "20260622170816_reset_v2_session_state",
    "20260622202450_simplify_session_input",
    "20260804233008_loose_psylocke",
    "20260805200742_import_legacy_credentials",
    "20260808023530_workspace_domain",
    "20260811161259_execution_claim_attempts",
    "20260812181746_session_inbox",
    "20260812213948_worktree",
    "20260819222447_session_viewed_state",
    "20260823191254_nullable_workspace_binding",
    "20260910120000_clear_v1_session_permission",
    "20260923013825_project_time_active",
    "20261007190000_azure_cli_external_credential",
    "20261010180456_project_time_archived",
    "20261024002554_session_allowance",
    "20261024175301_drop_session_allowance",
    "20261025123711_blob",
    "20261025154125_drop_session_pending",
    "20261026223005_schedule",
    "20261029002625_session_part",
    "20261029073502_session_time_busy",
    "20261029165540_schedule_checks",
    "20261030054400_job",
    "20261116043204_automation",
    "20261116181958_automation_event_position",
    "20261116213417_automation_active_index",
    "20261119211416_machine",
    "20261120004954_machine-key",
)


def parse_opencode_sqlite(
    db_path: str | Path,
    *,
    limit: int | None = None,
    include_subagents: bool = False,
) -> list[ConversationGraph]:
    """Read real OpenCode `opencode.db` (both v2 `session_v2`/`session_message` and v1 `session`/`message`/`part`).

    Strictly read-only (`?mode=ro`); never queries `account`, `control_account`, `credential`, or `session_share`.
    """
    p = Path(db_path).expanduser()
    if not p.is_file():
        return []
    graphs: list[ConversationGraph] = []
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        projects: dict[str, dict[str, Any]] = {}
        if "project" in tables:
            for pr in conn.execute("SELECT id, worktree, name FROM project"):
                projects[str(pr["id"])] = dict(pr)

        stbl = "session_v2" if "session_v2" in tables else ("session" if "session" in tables else None)
        if not stbl:
            return []

        all_sessions = [dict(r) for r in conn.execute(f'SELECT * FROM "{stbl}" ORDER BY time_updated DESC')]
        top_sessions = [s for s in all_sessions if not s.get("parent_id")]
        children_by_parent: dict[str, list[dict[str, Any]]] = {}
        for s in all_sessions:
            pid = s.get("parent_id")
            if pid:
                children_by_parent.setdefault(str(pid), []).append(s)

        if limit and limit > 0:
            top_sessions = top_sessions[:limit]

        selected: list[dict[str, Any]] = []
        if include_subagents:
            seen_sids: set[str] = set()
            for top in top_sessions:
                stack = [top]
                while stack:
                    cur = stack.pop()
                    csid = str(cur.get("id") or "")
                    if not csid or csid in seen_sids:
                        continue
                    seen_sids.add(csid)
                    selected.append(cur)
                    for ch in reversed(children_by_parent.get(csid, [])):
                        stack.append(ch)
        else:
            selected = top_sessions

        use_v2_msgs = "session_message" in tables and (
            stbl == "session_v2"
            and conn.execute("SELECT 1 FROM session_message LIMIT 1").fetchone() is not None
        )

        for srow in selected:
            sid = str(srow.get("id") or "")
            if not sid:
                continue
            proj = projects.get(str(srow.get("project_id") or ""), {})
            ws = str(srow.get("directory") or proj.get("worktree") or "").strip()
            if ws in {"", "/"}:
                ws = None
            raw_items: list[dict[str, Any]] = []
            if use_v2_msgs:
                parts_by_mid: dict[str, list[dict[str, Any]]] = {}
                if "session_part" in tables:
                    for prow in conn.execute(
                        "SELECT message_id, ordinal, type, call_id, data FROM session_part WHERE session_id = ? ORDER BY message_id, ordinal ASC",
                        (sid,),
                    ):
                        try:
                            pdata = json.loads(prow["data"] or "{}")
                        except json.JSONDecodeError:
                            pdata = {}
                        parts_by_mid.setdefault(str(prow["message_id"]), []).append(pdata)
                for mrow in conn.execute(
                    "SELECT id, type, seq, time_created, data FROM session_message WHERE session_id = ? ORDER BY seq ASC, time_created ASC",
                    (sid,),
                ):
                    mid = str(mrow["id"])
                    mtype = str(mrow["type"] or "user")
                    try:
                        mdata = json.loads(mrow["data"] or "{}")
                    except json.JSONDecodeError:
                        mdata = {}
                    if mtype == "user":
                        txt = str(mdata.get("text") or content_text(mdata.get("content", ""))).strip()
                        if txt:
                            raw_items.append({"node_id": mid, "role": "user", "text": txt, "timestamp": mrow["time_created"], "content": txt, "raw_record": mdata})
                    elif mtype in {"assistant", "system"}:
                        c_arr = mdata.get("content") if isinstance(mdata.get("content"), list) else parts_by_mid.get(mid, [])
                        texts: list[str] = []
                        for idx_p, pt in enumerate(c_arr):
                            if not isinstance(pt, dict):
                                continue
                            ptype = pt.get("type")
                            if ptype in {"text", "reasoning"} and pt.get("text"):
                                texts.append(str(pt["text"]))
                            elif ptype == "tool":
                                tname = str(pt.get("name") or pt.get("tool") or "tool")
                                cid = str(pt.get("id") or pt.get("callID") or f"{mid}-tc-{idx_p}")
                                raw_items.append({
                                    "node_id": cid,
                                    "role": "tool_call",
                                    "text": f"tool:{tname}",
                                    "timestamp": mrow["time_created"],
                                    "content": {"call_id": cid, "name": tname, "arguments": (pt.get("state") or {}).get("input", {}) if isinstance(pt.get("state"), dict) else {}},
                                    "raw_record": pt,
                                    "event_type": "tool_use",
                                })
                        joined = "\n\n".join(t for t in texts if t.strip())
                        if not joined and isinstance(mdata.get("text"), str):
                            joined = mdata["text"]
                        if joined.strip():
                            raw_items.append({"node_id": mid, "role": mtype, "text": joined, "timestamp": mrow["time_created"], "content": c_arr or joined, "raw_record": mdata})
            elif "message" in tables:
                parts_by_mid_v1: dict[str, list[dict[str, Any]]] = {}
                if "part" in tables:
                    for prow in conn.execute(
                        "SELECT id, message_id, data FROM part WHERE session_id = ? ORDER BY time_created ASC, id ASC",
                        (sid,),
                    ):
                        try:
                            pdata = json.loads(prow["data"] or "{}")
                        except json.JSONDecodeError:
                            pdata = {}
                        pdata.setdefault("id", prow["id"])
                        parts_by_mid_v1.setdefault(str(prow["message_id"]), []).append(pdata)
                for mrow in conn.execute(
                    "SELECT id, time_created, data FROM message WHERE session_id = ? ORDER BY time_created ASC, id ASC",
                    (sid,),
                ):
                    mid = str(mrow["id"])
                    try:
                        minfo = json.loads(mrow["data"] or "{}")
                    except json.JSONDecodeError:
                        minfo = {}
                    role = str(minfo.get("role") or "user")
                    mparts = parts_by_mid_v1.get(mid, [])
                    texts = [
                        str(pt.get("text") or "")
                        for pt in mparts
                        if isinstance(pt, dict) and pt.get("type") in {"text", "reasoning"} and pt.get("text")
                    ]
                    body = "\n\n".join(t for t in texts if t.strip()) or content_text(minfo.get("content", ""))
                    if body.strip():
                        raw_items.append({"node_id": mid, "role": role, "text": body, "timestamp": mrow["time_created"], "content": mparts or body, "raw_record": {"info": minfo, "parts": mparts}})
                    for idx_p, pt in enumerate(mparts):
                        if isinstance(pt, dict) and pt.get("type") == "tool":
                            tname = str(pt.get("tool") or pt.get("name") or "tool")
                            cid = str(pt.get("callID") or pt.get("id") or f"{mid}-tc-{idx_p}")
                            state = pt.get("state") if isinstance(pt.get("state"), dict) else {}
                            raw_items.append({
                                "node_id": f"{cid}-call",
                                "role": "tool_call",
                                "text": f"tool:{tname}",
                                "timestamp": mrow["time_created"],
                                "content": {"call_id": cid, "name": tname, "arguments": state.get("input", {})},
                                "raw_record": pt,
                                "event_type": "tool_use",
                            })
                            if state.get("output") is not None:
                                out_s = content_text(state["output"])
                                raw_items.append({
                                    "node_id": f"{cid}-out",
                                    "role": "tool_result",
                                    "text": out_s[:4000],
                                    "timestamp": mrow["time_created"],
                                    "content": {"call_id": cid, "output": out_s[:4000]},
                                    "raw_record": state,
                                    "event_type": "tool_result",
                                })

            nodes, roots, active = _chain_linear(raw_items)
            parent_id = str(srow.get("parent_id") or "").strip() or None
            in_tok = int(srow.get("tokens_input") or 0)
            out_tok = int(srow.get("tokens_output") or 0)
            usage = UsageSummary(input_tokens=in_tok, output_tokens=out_tok) if (in_tok or out_tok) else None
            graphs.append(
                ConversationGraph(
                    source_format="opencode_session",
                    source_id=sid,
                    title=str(srow.get("title") or srow.get("slug") or sid),
                    workspace=ws,
                    nodes=nodes,
                    root_ids=roots,
                    active_node_id=active,
                    metadata={
                        "parent_session_id": parent_id,
                        "nesting_depth": 1 if parent_id else 0,
                        "project_id": srow.get("project_id") if srow.get("project_id") != "global" else None,
                        "project_name": proj.get("name") or (Path(ws).name if ws else None),
                        "subagent_role": srow.get("agent") if parent_id else None,
                        "source_file": p.name,
                    },
                    raw_source={"session_id": sid, "version": srow.get("version")},
                    usage=usage,
                    links=_collect_links(nodes),
                    app_mode="cli",
                )
            )
    finally:
        conn.close()
    return graphs


def parse_opencode_session(path: str | Path) -> ConversationGraph:
    """Read an OpenCode v2 `session export` JSON, v1 combined JSON, OR split `storage/` session."""
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    info = data.get("info") if isinstance(data.get("info"), dict) else data
    sid = str(info.get("id") or info.get("sessionID") or p.stem)
    title = info.get("title") or info.get("slug") or sid
    loc = info.get("location") if isinstance(info.get("location"), dict) else {}
    workspace = loc.get("directory") or info.get("directory") or info.get("cwd") or info.get("projectPath")
    parent_id = info.get("parentID") or info.get("parentId")

    raw_items: list[dict[str, Any]] = []
    if isinstance(data.get("messages"), list):
        for idx, msg in enumerate(data["messages"]):
            if not isinstance(msg, dict):
                continue
            m_info = msg.get("info") if isinstance(msg.get("info"), dict) else msg
            role = str(m_info.get("role") or m_info.get("type") or ("user" if "text" in m_info and "content" not in m_info else "assistant"))
            parts = msg.get("parts") if isinstance(msg.get("parts"), list) else (
                m_info.get("content") if isinstance(m_info.get("content"), list) else []
            )
            if parts:
                text = "\n".join(str(pt.get("text") or "") for pt in parts if isinstance(pt, dict) and pt.get("type") in {"text", "reasoning"} and pt.get("text"))
                content: Any = parts
            elif isinstance(m_info.get("text"), str):
                text = m_info["text"]
                content = text
            else:
                content = m_info.get("content", "")
                text = content_text(content)
            raw_items.append({"node_id": str(m_info.get("id") or f"oc-{idx}"), "role": role, "text": text, "timestamp": (m_info.get("time") or {}).get("created") if isinstance(m_info.get("time"), dict) else m_info.get("timestamp"), "content": content, "raw_record": msg})
    else:
        storage_root = p.parents[2] if len(p.parents) >= 3 and p.parents[1].name == "session" else None
        if storage_root and (storage_root / "message" / sid).is_dir():
            msg_files = sorted((storage_root / "message" / sid).glob("*.json"))
            loaded_msgs = []
            for mf in msg_files:
                try:
                    loaded_msgs.append(json.loads(mf.read_text(encoding="utf-8-sig")))
                except (json.JSONDecodeError, OSError):
                    continue
            loaded_msgs.sort(key=lambda m: ((m.get("time") or {}).get("created") or 0, str(m.get("id") or "")))
            for m_info in loaded_msgs:
                mid = str(m_info.get("id") or "")
                parts = []
                pdir = storage_root / "part" / mid
                if pdir.is_dir():
                    for pf in sorted(pdir.glob("*.json")):
                        try:
                            parts.append(json.loads(pf.read_text(encoding="utf-8-sig")))
                        except (json.JSONDecodeError, OSError):
                            continue
                text = "\n".join(str(pt.get("text") or "") for pt in parts if isinstance(pt, dict) and pt.get("type") in {"text", "reasoning"} and pt.get("text"))
                raw_items.append({
                    "node_id": mid or f"oc-{len(raw_items)}",
                    "role": str(m_info.get("role") or "user"),
                    "text": text,
                    "timestamp": (m_info.get("time") or {}).get("created") if isinstance(m_info.get("time"), dict) else None,
                    "content": parts or text,
                    "raw_record": {"info": m_info, "parts": parts},
                })

    nodes, roots, active = _chain_linear(raw_items)
    return ConversationGraph(
        source_format="opencode_session",
        source_id=sid,
        title=str(title),
        workspace=str(workspace) if isinstance(workspace, str) else None,
        nodes=nodes,
        root_ids=roots,
        active_node_id=active,
        metadata={"parent_session_id": parent_id, "project_id": info.get("projectID"), "source_file": p.name},
        raw_source=data,
        links=_collect_links(nodes),
        app_mode="cli",
    )


def parse_opencode_storage_dir(
    storage_dir: str | Path,
    *,
    limit: int | None = None,
    include_subagents: bool = False,
) -> list[ConversationGraph]:
    """Read sessions from real OpenCode `~/.local/share/opencode` (`opencode.db` + `storage/`)."""
    root = Path(storage_dir).expanduser()
    out: list[ConversationGraph] = []
    seen: set[str] = set()
    for db_cand in (root / "opencode.db", root.parent / "opencode.db" if root.name == "storage" else root / "opencode.db"):
        if db_cand.is_file():
            for g in parse_opencode_sqlite(db_cand, limit=limit, include_subagents=include_subagents):
                if g.source_id not in seen:
                    seen.add(g.source_id)
                    out.append(g)
            break
    if limit and len(out) >= limit:
        return out[:limit]
    sroot = root / "storage" if (root / "storage").is_dir() else root
    sess_dir = sroot / "session"
    if sess_dir.is_dir():
        for sf in sorted(sess_dir.rglob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            if not sf.is_file() or sf.stem in seen:
                continue
            try:
                g = parse_opencode_session(sf)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if g.source_id not in seen:
                seen.add(g.source_id)
                out.append(g)
                if limit and len(out) >= limit:
                    break
    return out


def build_opencode_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project a ConversationGraph into OpenCode v2.4 `session import` JSON + split `storage/{session,message,part}`."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    project_hash = hashlib.sha1(resolved_cwd.encode("utf-8")).hexdigest()
    now_ms = int(datetime.now(UTC).timestamp() * 1000)

    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"ses_{uuid.uuid4().hex[:26]}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        export_messages: list[dict[str, Any]] = []
        split_files: dict[str, dict[str, Any]] = {}
        source_node_ids: list[str] = []
        for idx, turn in enumerate(turns):
            mid = f"msg_{uuid.uuid4().hex[:26]}"
            pid = f"prt_{uuid.uuid4().hex[:20]}"
            text = "\n\n".join(turn["texts"])
            t_ms = now_ms + idx * 10
            m_info = {"id": mid, "sessionID": sid, "role": turn["role"], "time": {"created": t_ms}}
            p_obj = {"id": pid, "sessionID": sid, "messageID": mid, "type": "text", "text": text}
            split_files[f"storage/message/{sid}/{mid}.json"] = m_info
            split_files[f"storage/part/{mid}/{pid}.json"] = p_obj
            if turn["role"] == "user":
                export_messages.append({"id": mid, "type": "user", "time": {"created": t_ms}, "text": text})
            else:
                export_messages.append(
                    {
                        "id": mid,
                        "type": "assistant",
                        "agent": "build",
                        "model": {"id": "gpt-5", "providerID": "openai", "variant": "default"},
                        "time": {"created": t_ms, "completed": t_ms + 5},
                        "content": [{"type": "text", "text": text}],
                        "finish": "stop",
                        "cost": 0,
                        "tokens": {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}},
                    }
                )
            source_node_ids.extend(turn["source_node_ids"])
        export_info: dict[str, Any] = {
            "id": sid,
            "projectID": project_hash,
            "agent": "build",
            "model": {"id": "gpt-5", "providerID": "openai", "variant": "default"},
            "cost": 0,
            "tokens": {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}},
            "time": {"created": now_ms, "updated": now_ms + len(turns) * 10},
            "title": title,
            "location": {"directory": resolved_cwd},
        }
        split_sess_info = {
            "id": sid,
            "version": "2.4.1",
            "projectID": project_hash,
            "title": title,
            "directory": resolved_cwd,
            "parentID": graph.metadata.get("parent_session_id"),
            "time": {"created": now_ms, "updated": now_ms + len(turns) * 10},
            "nexusProvenance": {"source_format": graph.source_format, "source_id": graph.source_id},
        }
        split_files[f"storage/session/global/{sid}.json"] = split_sess_info
        sessions.append({
            "session_id": sid,
            "branch_index": branch_index,
            "title": title,
            "cwd": resolved_cwd,
            "source_node_ids": source_node_ids,
            "payload": {"info": export_info, "messages": export_messages},
            "split_files": split_files,
        })
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_opencode_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


def merge_opencode_sessions_batch(
    db_path: str | Path,
    payloads: list[dict[str, Any]],
    *,
    on_collision: str = "refuse",
) -> list[dict[str, Any]]:
    """Batch-merge OpenCode session payloads into `opencode.db` (compatible with both v2.4 `session_v2` and v1 `session`)."""
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    conn = sqlite3.connect(str(db), timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        use_v1 = ("session" in tables) and ("session_v2" not in tables)
        if not use_v1 and "session_v2" not in tables:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS "migration" (id TEXT PRIMARY KEY, time_completed INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS `account` (
                    `id` text PRIMARY KEY, `email` text NOT NULL, `url` text NOT NULL,
                    `access_token` text NOT NULL, `refresh_token` text NOT NULL, `token_expiry` integer,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `account_state` (
                    `id` integer PRIMARY KEY, `active_account_id` text, `active_org_id` text
                );
                CREATE TABLE IF NOT EXISTS `automation` (
                    `id` text PRIMARY KEY, `project_id` text NOT NULL, `session_id` text,
                    `directory` text NOT NULL, `name` text NOT NULL, `trigger` text NOT NULL,
                    `tz` text NOT NULL, `action` text NOT NULL, `status` text DEFAULT 'active' NOT NULL,
                    `next_due_at` integer, `expires_at` integer, `run_count` integer DEFAULT 0 NOT NULL,
                    `failures` integer DEFAULT 0 NOT NULL, `last_run_at` integer, `last_message_id` text,
                    `last_outcome` text, `last_output` text, `retry_at` integer, `state` text,
                    `event_position` text, `time_created` integer NOT NULL, `time_updated` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `blob` (
                    `hash` text PRIMARY KEY, `mime` text NOT NULL, `bytes` integer NOT NULL,
                    `width` integer, `height` integer, `data` blob NOT NULL, `time_created` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `blob_ref` (
                    `session_id` text NOT NULL, `message_id` text NOT NULL, `hash` text NOT NULL, `seq` integer NOT NULL,
                    CONSTRAINT `blob_ref_pk` PRIMARY KEY(`session_id`, `message_id`, `hash`)
                );
                CREATE TABLE IF NOT EXISTS `control_account` (
                    `email` text NOT NULL, `url` text NOT NULL, `access_token` text NOT NULL,
                    `refresh_token` text NOT NULL, `token_expiry` integer, `active` integer NOT NULL,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL,
                    CONSTRAINT `control_account_pk` PRIMARY KEY(`email`, `url`)
                );
                CREATE TABLE IF NOT EXISTS `credential` (
                    `id` text PRIMARY KEY, `integration_id` text, `label` text NOT NULL, `value` text NOT NULL,
                    `connector_id` text, `method_id` text, `active` integer,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `event_sequence` (
                    `aggregate_id` text PRIMARY KEY, `seq` integer NOT NULL, `owner_id` text
                );
                CREATE TABLE IF NOT EXISTS `event` (
                    `id` text PRIMARY KEY, `aggregate_id` text NOT NULL, `seq` integer NOT NULL,
                    `created` integer DEFAULT 0 NOT NULL, `type` text NOT NULL, `data` text NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `instruction_blob` (`hash` text PRIMARY KEY, `value` text);
                CREATE TABLE IF NOT EXISTS `instruction_entry` (
                    `session_id` text NOT NULL, `key` text NOT NULL, `value` text,
                    `removed` integer DEFAULT 0 NOT NULL, `time_created` integer NOT NULL, `time_updated` integer NOT NULL,
                    CONSTRAINT `instruction_entry_pk` PRIMARY KEY(`session_id`, `key`)
                );
                CREATE TABLE IF NOT EXISTS `instruction_state` (
                    `session_id` text PRIMARY KEY, `epoch_start` integer NOT NULL, `through_seq` integer NOT NULL,
                    `initial_values` text NOT NULL, `current_values` text NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `job` (
                    `notification_id` text PRIMARY KEY, `id` text NOT NULL, `session_id` text NOT NULL,
                    `child_session_id` text, `kind` text NOT NULL, `title` text, `status` text NOT NULL,
                    `output` text, `error` text, `recovery` text NOT NULL,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `kv` (
                    `key` text PRIMARY KEY, `value` text NOT NULL, `time_created` integer NOT NULL, `time_updated` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `machine` (`id` text PRIMARY KEY, `key` text, `time_created` integer NOT NULL);
                CREATE TABLE IF NOT EXISTS `permission` (
                    `id` text PRIMARY KEY, `project_id` text NOT NULL, `action` text NOT NULL, `resource` text NOT NULL,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `project` (
                    `id` text PRIMARY KEY, `worktree` text NOT NULL, `vcs` text, `name` text,
                    `icon_url` text, `icon_url_override` text, `icon_color` text,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL, `time_initialized` integer,
                    `time_active` integer DEFAULT 0 NOT NULL, `time_archived` integer, `sandboxes` text NOT NULL, `commands` text
                );
                CREATE TABLE IF NOT EXISTS `project_directory` (
                    `project_id` text NOT NULL, `directory` text NOT NULL, `type` text, `strategy` text, `time_created` integer NOT NULL,
                    CONSTRAINT `project_directory_pk` PRIMARY KEY(`project_id`, `directory`)
                );
                CREATE TABLE IF NOT EXISTS `workspace` (
                    `id` text PRIMARY KEY, `provider` text NOT NULL, `binding` text,
                    `created_at` integer NOT NULL, `last_used_at` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `worktree` (
                    `project_id` text NOT NULL, `directory` text NOT NULL, `strategy` text, `time_created` integer NOT NULL,
                    CONSTRAINT `worktree_pk` PRIMARY KEY(`project_id`, `directory`)
                );
                CREATE TABLE IF NOT EXISTS `session_v2` (
                    `id` text PRIMARY KEY, `project_id` text NOT NULL, `workspace_id` text, `parent_id` text,
                    `fork_session_id` text, `fork_boundary` text, `slug` text NOT NULL, `directory` text NOT NULL,
                    `path` text, `title` text, `version` text NOT NULL, `share_url` text,
                    `summary_additions` integer, `summary_deletions` integer, `summary_files` integer, `summary_diffs` text,
                    `metadata` text, `cost` real DEFAULT 0 NOT NULL, `tokens_input` integer DEFAULT 0 NOT NULL,
                    `tokens_output` integer DEFAULT 0 NOT NULL, `tokens_reasoning` integer DEFAULT 0 NOT NULL,
                    `tokens_cache_read` integer DEFAULT 0 NOT NULL, `tokens_cache_write` integer DEFAULT 0 NOT NULL,
                    `revert` text, `permission` text, `agent` text, `model` text,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL, `time_busy` integer,
                    `time_idle` integer, `time_viewed` integer, `idle_outcome` text, `time_compacting` integer,
                    `time_archived` integer, `time_suspended` integer, `resume_attempts` integer DEFAULT 0 NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `session_inbox` (
                    `id` text PRIMARY KEY, `session_id` text NOT NULL, `type` text NOT NULL,
                    `payload` text NOT NULL, `delivery` text NOT NULL, `enqueued_seq` integer NOT NULL, `time_created` integer NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `session_message` (
                    `id` text PRIMARY KEY, `session_id` text NOT NULL, `type` text NOT NULL, `seq` integer NOT NULL,
                    `time_created` integer NOT NULL, `time_updated` integer NOT NULL, `data` text NOT NULL
                );
                CREATE TABLE IF NOT EXISTS `session_part` (
                    `message_id` text NOT NULL, `session_id` text NOT NULL, `ordinal` integer NOT NULL,
                    `type` text NOT NULL, `call_id` text, `time_created` integer NOT NULL, `time_updated` integer NOT NULL,
                    `data` text NOT NULL,
                    CONSTRAINT `session_part_pk` PRIMARY KEY(`message_id`, `ordinal`)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS `machine_key_idx` ON `machine` (`key`);
                CREATE UNIQUE INDEX IF NOT EXISTS `session_message_session_seq_idx` ON `session_message` (`session_id`,`seq`);
                CREATE INDEX IF NOT EXISTS `session_v2_project_idx` ON `session_v2` (`project_id`);
                CREATE INDEX IF NOT EXISTS `session_v2_parent_idx` ON `session_v2` (`parent_id`);
                """
            )
            for idx_m, mid_name in enumerate(_OPENCODE_V2_MIGRATION_IDS):
                conn.execute("INSERT OR IGNORE INTO migration (id, time_completed) VALUES (?, ?)", (mid_name, now_ms + idx_m))

        proj_by_wt: dict[str, str] = {
            str(r["worktree"]): str(r["id"]) for r in conn.execute("SELECT id, worktree FROM project")
        }
        stbl = "session" if use_v1 else "session_v2"
        existing_sids = {str(r[0]) for r in conn.execute(f'SELECT id FROM "{stbl}"')}
        proj_cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(project)")}
        results: list[dict[str, Any]] = []

        for pld in payloads:
            info = pld.get("info") if isinstance(pld.get("info"), dict) else pld
            sid = str(info.get("id") or f"ses_{uuid.uuid4().hex[:26]}")
            if sid in existing_sids:
                if on_collision == "refuse":
                    raise FileExistsError(f"opencode session already exists in opencode.db: {sid}")
                if on_collision == "skip":
                    results.append({"session_id": sid, "action": "skipped"})
                    continue
                if on_collision == "rename":
                    sid = f"ses_{uuid.uuid4().hex[:26]}"

            loc = info.get("location") if isinstance(info.get("location"), dict) else {}
            cwd_val = str(loc.get("directory") or info.get("directory") or "")
            pid = proj_by_wt.get(cwd_val)
            if not pid:
                pid_git = ""
                if cwd_val and Path(cwd_val).is_dir():
                    try:
                        import subprocess as _sp
                        r_top = _sp.run(["git", "-C", cwd_val, "rev-list", "--max-parents=0", "--all"], capture_output=True, text=True, timeout=2)
                        if r_top.returncode == 0 and r_top.stdout.strip():
                            pid_git = r_top.stdout.strip().splitlines()[0].strip()
                    except Exception:
                        pid_git = ""
                pid = pid_git or str(info.get("projectID") or hashlib.sha1(cwd_val.encode("utf-8")).hexdigest())
                pvals = {
                    "id": pid,
                    "worktree": cwd_val or "/",
                    "vcs": "git" if pid_git else None,
                    "name": Path(cwd_val).name if cwd_val and cwd_val not in {"/", "\\"} else None,
                    "time_created": now_ms,
                    "time_updated": now_ms,
                    "time_active": now_ms,
                    "sandboxes": "[]",
                }
                pcols = [c for c in pvals if c in proj_cols]
                conn.execute(
                    f"INSERT OR IGNORE INTO project ({', '.join(pcols)}) VALUES ({', '.join('?' for _ in pcols)})",
                    tuple(pvals[c] for c in pcols),
                )
                proj_by_wt[cwd_val] = pid

            title = str(info.get("title") or sid)
            t_created = int((info.get("time") or {}).get("created") or now_ms)
            t_updated = int((info.get("time") or {}).get("updated") or now_ms)
            model_json = json.dumps(info.get("model") or {"id": "gpt-5", "providerID": "openai", "variant": "default"})
            msgs = pld.get("messages") if isinstance(pld.get("messages"), list) else []

            if use_v1:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO session (
                        id, project_id, parent_id, slug, directory, title, version,
                        time_created, time_updated, agent, model, cost,
                        tokens_input, tokens_output, tokens_reasoning, tokens_cache_read, tokens_cache_write
                    ) VALUES (?, ?, NULL, ?, ?, ?, '1.18.31', ?, ?, 'build', ?, 0, 0, 0, 0, 0, 0)
                    """,
                    (sid, pid, f"nexus-{sid[-8:]}", cwd_val, title, t_created, t_updated, model_json),
                )
                for idx_m, m in enumerate(msgs):
                    if not isinstance(m, dict):
                        continue
                    mid = str(m.get("id") or f"msg_{uuid.uuid4().hex[:26]}")
                    role = str(m.get("type") or (m.get("info") or {}).get("role") or "user")
                    mc_ts = int((m.get("time") or {}).get("created") or (t_created + idx_m))
                    txt = str(m.get("text") or content_text(m.get("content", m.get("parts", ""))))
                    conn.execute(
                        "INSERT OR REPLACE INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
                        (mid, sid, mc_ts, mc_ts, json.dumps({"role": role, "time": {"created": mc_ts}}, ensure_ascii=False)),
                    )
                    part_id = f"prt_{uuid.uuid4().hex[:20]}"
                    conn.execute(
                        "INSERT OR REPLACE INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?, ?)",
                        (part_id, mid, sid, mc_ts, mc_ts, json.dumps({"type": "text", "text": txt}, ensure_ascii=False)),
                    )
            else:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO session_v2 (
                        id, project_id, parent_id, slug, directory, path, title, version,
                        cost, tokens_input, tokens_output, tokens_reasoning, tokens_cache_read, tokens_cache_write,
                        agent, model, time_created, time_updated, resume_attempts
                    ) VALUES (?, ?, NULL, ?, ?, '', ?, '2.4.1', 0, 0, 0, 0, 0, 0, 'build', ?, ?, ?, 0)
                    """,
                    (sid, pid, f"nexus-{sid[-8:]}", cwd_val, title, model_json, t_created, t_updated),
                )
                seq_num = 0
                for idx_m, m in enumerate(msgs, 1):
                    if not isinstance(m, dict):
                        continue
                    seq_num = idx_m
                    mid = str(m.get("id") or f"msg_{uuid.uuid4().hex[:26]}")
                    mtype = str(m.get("type") or (m.get("info") or {}).get("role") or "user")
                    mc_ts = int((m.get("time") or {}).get("created") or (t_created + idx_m))
                    if mtype == "user":
                        txt = str(m.get("text") or content_text(m.get("content", m.get("parts", ""))))
                        mdata = {"time": {"created": mc_ts}, "text": txt}
                    else:
                        c_arr = m.get("content") if isinstance(m.get("content"), list) else [{"type": "text", "text": content_text(m.get("parts", m.get("text", "")))}]
                        mdata = {
                            "time": {"created": mc_ts, "completed": mc_ts + 5},
                            "agent": "build",
                            "model": {"id": "gpt-5", "providerID": "openai", "variant": "default"},
                            "content": c_arr,
                            "finish": "stop",
                            "cost": 0,
                            "tokens": {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}},
                        }
                    conn.execute(
                        "INSERT OR REPLACE INTO session_message (id, session_id, type, seq, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (mid, sid, mtype, seq_num, mc_ts, now_ms, json.dumps(mdata, ensure_ascii=False)),
                    )
                if "event_sequence" in {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
                    conn.execute(
                        "INSERT OR REPLACE INTO event_sequence (aggregate_id, seq, owner_id) VALUES (?, ?, NULL)",
                        (sid, seq_num),
                    )
            existing_sids.add(sid)
            results.append({"session_id": sid, "project_id": pid, "action": "merged"})
        conn.commit()
        try:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except sqlite3.Error:
            pass
        return results
    finally:
        conn.close()


# ── 4. Pi (native tree DAG JSONL read + write!) ──────────────────────────────


def parse_pi_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    records = [json.loads(line) for line in p.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    header = next((r for r in records if r.get("type") == "session"), {})
    sid = str(header.get("id") or p.stem)
    workspace = header.get("cwd")
    title = header.get("name") or header.get("title") or sid

    entries = [r for r in records if r.get("type") in {"message", "compaction", "branch_summary"}]
    child_map: dict[str, list[str]] = {str(r.get("id") or f"pi-{i}"): [] for i, r in enumerate(entries)}
    raw_list: list[tuple[str, str | None, dict[str, Any]]] = []
    for i, r in enumerate(entries):
        nid = str(r.get("id") or f"pi-{i}")
        pid = str(r["parentId"]) if r.get("parentId") else None
        if pid in child_map and nid not in child_map[pid]:
            child_map[pid].append(nid)
        raw_list.append((nid, pid, r))

    nodes: list[MessageNode] = []
    for nid, pid, r in raw_list:
        if r.get("type") == "message":
            msg = r.get("message") if isinstance(r.get("message"), dict) else {}
            role = str(msg.get("role") or "user")
            content = msg.get("content", "")
            text = content_text(content)
            ev = "message"
        else:
            role, content, text, ev = "system", r.get("summary", ""), str(r.get("summary", "")), "compaction"
        nodes.append(MessageNode(node_id=nid, parent_id=pid, child_ids=tuple(child_map[nid]), role=role, text=text, timestamp=r.get("timestamp"), content=content, raw_record=r, event_type=ev, links=extract_links(text)))
    roots = tuple(n.node_id for n in nodes if n.parent_id is None or n.parent_id not in child_map)
    return ConversationGraph(
        source_format="pi_session",
        source_id=sid,
        title=str(title),
        workspace=str(workspace) if isinstance(workspace, str) else None,
        nodes=tuple(nodes),
        root_ids=roots,
        active_node_id=nodes[-1].node_id if nodes else None,
        metadata={"parent_session_id": header.get("parentSession"), "source_file": p.name},
        raw_source={"header": header, "records": records},
        links=_collect_links(tuple(nodes)),
        app_mode="cli",
    )


def build_pi_session(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project a ConversationGraph into ONE Pi tree-DAG JSONL file (natively preserves branches!)."""
    sid = str(uuid.uuid4())
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
    records: list[dict[str, Any]] = [
        {"type": "session", "version": 3, "id": sid, "timestamp": now_iso, "cwd": resolved_cwd, "name": title, "parentSession": graph.metadata.get("parent_session_id")}
    ]
    valid_ids = {n.node_id for n in graph.nodes}
    source_node_ids: list[str] = []
    for node in graph.nodes:
        ts = node.timestamp if isinstance(node.timestamp, str) else now_iso
        pid = node.parent_id if node.parent_id in valid_ids else None
        records.append({"type": "message", "id": node.node_id, "parentId": pid, "timestamp": ts, "message": {"role": node.role or "user", "content": [{"type": "text", "text": node.text}]}})
        source_node_ids.append(node.node_id)
    losses = [{"feature": "binary_attachments", "disposition": "archived_in_bundle_assets_with_sha256"}] if graph.assets else []
    return [{"session_id": sid, "branch_index": 1, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "records": records, "native_branch_dag_preserved": True}], losses


# ── 5. Cursor (`state.vscdb` SQLite read-only) ───────────────────────────────


def parse_cursor_vscdb(db_path: str | Path) -> list[ConversationGraph]:
    p = Path(db_path).expanduser()
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    graphs: list[ConversationGraph] = []
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        kv_table = "cursorDiskKV" if "cursorDiskKV" in tables else ("ItemTable" if "ItemTable" in tables else None)
        if not kv_table:
            return []
        composers: dict[str, dict[str, Any]] = {}
        bubbles: dict[str, dict[str, Any]] = {}
        for key, raw_val in conn.execute(f"SELECT key, value FROM {kv_table}"):
            if not isinstance(key, str) or raw_val is None:
                continue
            val_str = raw_val.decode("utf-8", "replace") if isinstance(raw_val, bytes) else str(raw_val)
            if key.startswith("composerData:"):
                try:
                    composers[key.split(":", 1)[1]] = json.loads(val_str)
                except json.JSONDecodeError:
                    continue
            elif key.startswith("bubbleId:"):
                try:
                    bubbles[key] = json.loads(val_str)
                except json.JSONDecodeError:
                    continue
        for cid, comp in sorted(composers.items()):
            title = comp.get("name") or comp.get("title") or cid
            raw_items: list[dict[str, Any]] = []
            for idx, entry in enumerate(comp.get("conversation") or comp.get("fullConversationHeadersOnly") or []):
                if not isinstance(entry, dict):
                    continue
                bid = entry.get("bubbleId")
                bubble = bubbles.get(f"bubbleId:{cid}:{bid}", entry) if bid else entry
                role = "user" if bubble.get("type") in {1, "user"} else "assistant"
                text = str(bubble.get("text") or bubble.get("rawText") or "")
                raw_items.append({"node_id": str(bid or f"cur-{idx}"), "role": role, "text": text, "timestamp": bubble.get("createdAt") or comp.get("createdAt"), "content": text, "raw_record": bubble})
            nodes, roots, active = _chain_linear(raw_items)
            graphs.append(ConversationGraph(source_format="cursor_vscdb", source_id=cid, title=str(title), workspace=comp.get("workspacePath") or comp.get("cwd"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name}, raw_source=comp, links=_collect_links(nodes), app_mode="ide-extension"))
    finally:
        conn.close()
    return graphs


def build_cursor_sessions(
    graph: ConversationGraph,
    *,
    cwd: str | Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project ConversationGraph into Cursor `state.vscdb` (`cursorDiskKV`: `composerData:*` + `bubbleId:*`) payload."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    if not paths:
        losses.append({"feature": "empty_conversation", "disposition": "skipped_zero_node_conversation"})
        return sessions, losses

    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        cid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        headers: list[dict[str, Any]] = []
        bubbles: dict[str, dict[str, Any]] = {}
        source_node_ids: list[str] = []
        for idx, t in enumerate(turns):
            bid = str(uuid.uuid4())
            btype = 1 if t["role"] == "user" else 2
            text = "\n\n".join(t["texts"])
            headers.append({"bubbleId": bid, "type": btype})
            bubbles[f"bubbleId:{cid}:{bid}"] = {
                "bubbleId": bid,
                "type": btype,
                "text": text,
                "rawText": text,
                "createdAt": now_ms + idx,
            }
            source_node_ids.extend(t["source_node_ids"])
        composer = {
            "composerId": cid,
            "name": title,
            "workspacePath": resolved_cwd,
            "createdAt": now_ms,
            "lastUpdatedAt": now_ms,
            "fullConversationHeadersOnly": headers,
            "nexusProvenance": {"source_format": graph.source_format, "source_id": graph.source_id},
        }
        sessions.append(
            {
                "session_id": cid,
                "branch_index": branch_index,
                "title": title,
                "cwd": resolved_cwd,
                "source_node_ids": source_node_ids,
                "payload": {"composer_key": f"composerData:{cid}", "composer": composer, "bubbles": bubbles},
            }
        )
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_cursor_composer_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 6. DeepSeek Harness / DSH (Official v0.2+ Format V4 `.jsonl[.zstd]` + legacy V4>V2) ──


def dsh_encode_segment(raw: str) -> str:
    """Match `@deepseek-ai/dsh-session-persistence-jsonl` `encodeSegment` verbatim."""
    if not raw:
        return "session"
    if raw == ".":
        return "~002E"
    if raw == "..":
        return "~002E~002E"
    out: list[str] = []
    for ch in raw:
        if ch != "~" and ch.isascii() and (ch.isalnum() or ch in "._-"):
            out.append(ch)
        else:
            out.append(f"~{ord(ch):04X}")
    return "".join(out)


def dsh_project_key(cwd: str | None) -> str:
    """Match `@deepseek-ai/dsh-session-persistence-jsonl` `projectKey` verbatim."""
    if not cwd:
        return "_no-cwd"
    readable: list[str] = []
    sep_run = False
    for ch in cwd:
        if ch in "/\\:":
            if not sep_run:
                readable.append("-")
            sep_run = True
        elif ch != "~" and ch.isascii() and (ch.isalnum() or ch in "._-"):
            readable.append(ch)
            sep_run = False
        else:
            readable.append(f"~{ord(ch):04X}")
            sep_run = False
    trimmed = "".join(readable).lstrip("-") or "root"
    return f"--{trimmed[:251]}--"


def compress_dsh_zstd_frames(records: list[dict[str, Any]]) -> bytes | None:
    """Encode DSH v4 records into the exact 2-frame checksummed Zstandard layout (`assertZstdHeaderFrame`)."""
    if not records:
        return None
    hdr_bytes = (json.dumps(records[0], ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    body_bytes = (
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records[1:])
    ).encode("utf-8")
    try:
        import zstandard as _zstd  # type: ignore[import-not-found]

        cctx = _zstd.ZstdCompressor(write_checksum=True)
        return cctx.compress(hdr_bytes) + (cctx.compress(body_bytes) if body_bytes else b"")
    except Exception:
        pass
    try:
        r1 = subprocess.run(["zstd", "-qc", "--check"], input=hdr_bytes, capture_output=True, timeout=10)
        if r1.returncode == 0 and r1.stdout:
            if not body_bytes:
                return r1.stdout
            r2 = subprocess.run(["zstd", "-qc", "--check"], input=body_bytes, capture_output=True, timeout=10)
            if r2.returncode == 0 and r2.stdout:
                return r1.stdout + r2.stdout
    except Exception:
        pass
    return None


def _read_dsh_jsonl_records(fp: Path) -> list[dict[str, Any]]:
    raw_bytes = fp.read_bytes()
    if fp.name.endswith((".zstd", ".zst")) or raw_bytes[:4] == b"\x28\xb5\x2f\xfd":
        text_data: str | None = None
        try:
            import io as _io
            import zstandard as _zstd  # type: ignore[import-not-found]

            dctx = _zstd.ZstdDecompressor()
            with dctx.stream_reader(_io.BytesIO(raw_bytes), read_across_frames=True) as reader:
                text_data = reader.read().decode("utf-8", errors="replace")
        except Exception:
            try:
                proc = subprocess.run(["zstd", "-dc"], input=raw_bytes, capture_output=True, timeout=10)
                if proc.returncode == 0:
                    text_data = proc.stdout.decode("utf-8", errors="replace")
            except Exception:
                text_data = None
        if text_data is None:
            return []
    else:
        text_data = raw_bytes.decode("utf-8-sig", errors="replace")
    out: list[dict[str, Any]] = []
    for line in text_data.splitlines():
        if line.strip():
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    out.append(obj)
            except json.JSONDecodeError:
                continue
    return out


def parse_dsh_directory(dsh_dir: str | Path) -> list[ConversationGraph]:
    root = Path(dsh_dir).expanduser()
    if root.is_dir():
        cand_set = set(root.rglob("*.jsonl")) | set(root.rglob("*.jsonl.zstd")) | set(root.rglob("*.jsonl.zst"))
        files = sorted(cand_set)
    else:
        files = [root]
    by_id: dict[str, tuple[int, ConversationGraph]] = {}
    for fp in files:
        if not fp.is_file():
            continue
        records = _read_dsh_jsonl_records(fp)
        if not records:
            continue
        header = records[0] if isinstance(records[0], dict) else {}
        if header.get("type") == "session" and ("isSeeded" in header or "delegationDepth" in header):
            schema_ver = int(header.get("version") or 4)
            sid = str(header.get("id") or fp.parent.name or fp.stem)
            title = sid
            raw_items: list[dict[str, Any]] = []
            for idx, rec in enumerate(records[1:], 1):
                ev_type = str(rec.get("type") or "")
                data = rec.get("data") if isinstance(rec.get("data"), dict) else {}
                ts_ms = rec.get("time")
                ts_iso = (
                    datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=UTC).isoformat().replace("+00:00", "Z")
                    if isinstance(ts_ms, (int, float))
                    else None
                )
                if ev_type == "session/title" and data.get("title"):
                    title = str(data["title"])
                elif ev_type == "user/message":
                    c = data.get("content", "")
                    raw_items.append({"node_id": str(data.get("id") or f"dsh-{idx}"), "role": "user", "text": content_text(c), "timestamp": ts_iso, "content": c, "raw_record": rec})
                elif ev_type in {"assistant/message", "system/message", "developer/message"}:
                    msg = data.get("message") if isinstance(data.get("message"), dict) else data
                    role = "assistant" if ev_type == "assistant/message" else "system"
                    c = msg.get("content", "")
                    raw_items.append({"node_id": str(msg.get("id") or f"dsh-{idx}"), "role": role, "text": content_text(c), "timestamp": ts_iso, "content": c, "raw_record": rec})
                elif ev_type == "tool/call":
                    c = json.dumps({"name": data.get("name"), "arguments": data.get("arguments")}, ensure_ascii=False)
                    raw_items.append({"node_id": str(data.get("callId") or f"dsh-tc-{idx}"), "role": "tool_call", "text": c, "timestamp": ts_iso, "content": c, "raw_record": rec})
                elif ev_type == "tool/result":
                    msg = data.get("message") if isinstance(data.get("message"), dict) else data
                    c = msg.get("content", "")
                    raw_items.append({"node_id": str(msg.get("id") or f"dsh-tr-{idx}"), "role": "tool_result", "text": content_text(c), "timestamp": ts_iso, "content": c, "raw_record": rec})
            nodes, roots, active = _chain_linear(raw_items)
            graph = ConversationGraph(
                source_format=f"dsh_v{schema_ver}",
                source_id=sid,
                title=title,
                workspace=str(header["cwd"]) if header.get("cwd") else None,
                nodes=nodes,
                root_ids=roots,
                active_node_id=active,
                metadata={"dsh_schema_version": schema_ver, "source_file": fp.name},
                raw_source={"records": records},
                links=_collect_links(nodes),
                app_mode="cli",
            )
        else:
            schema_ver = int(header.get("dsh_schema_version") or header.get("schema_version") or (4 if "v4" in fp.name.lower() else 2))
            sid = str(header.get("session_id") or header.get("id") or fp.stem)
            raw_items = []
            for idx, rec in enumerate(records):
                if rec.get("type") in {"session_header", "meta"}:
                    continue
                role = rec.get("role") or rec.get("type")
                if role not in {"user", "assistant", "system", "tool_call", "tool_result"}:
                    continue
                content = rec.get("content", rec.get("text", ""))
                raw_items.append({"node_id": str(rec.get("id") or f"dsh-{idx}"), "role": str(role), "text": content_text(content), "timestamp": rec.get("timestamp"), "content": content, "raw_record": rec})
            nodes, roots, active = _chain_linear(raw_items)
            graph = ConversationGraph(source_format=f"dsh_v{schema_ver}", source_id=sid, title=str(header.get("title") or sid), workspace=str(header.get("cwd") or header.get("workspace")) if (header.get("cwd") or header.get("workspace")) else None, nodes=nodes, root_ids=roots, active_node_id=active, metadata={"dsh_schema_version": schema_ver, "source_file": fp.name}, raw_source={"records": records}, links=_collect_links(nodes), app_mode="cli")
        prev = by_id.get(sid)
        if prev is None or schema_ver >= prev[0]:
            by_id[sid] = (schema_ver, graph)
    return [pair[1] for pair in by_id.values()]


def build_dsh_v4_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build official `@deepseek-ai/dsh@0.2.2` Format V4 sessions passing strict `Session.fromRestore`."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    base_ms = int(datetime.now(UTC).timestamp() * 1000)
    for branch_index, path in enumerate(paths, 1):
        sid = f"session-{uuid.uuid4()}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        created_ms = base_ms + branch_index * 1000
        records: list[dict[str, Any]] = [
            {
                "type": "session",
                "version": 4,
                "id": sid,
                "createdAt": created_ms,
                "cwd": resolved_cwd,
                "isSeeded": False,
                "delegationDepth": 0,
            }
        ]
        seq = 0
        cur_ms = created_ms + 10
        records.append(
            {
                "seq": seq,
                "time": cur_ms,
                "type": "session/title",
                "data": {"title": title, "source": {"kind": "user"}, "messageSeqs": []},
            }
        )
        seq += 1
        cur_ms += 10

        turns, _, _ = _coalesce_alternating_turns(path)
        source_node_ids: list[str] = []
        turn_num = 1
        for t in turns:
            body = "\n\n".join(t["texts"])
            source_node_ids.extend(t["source_node_ids"])
            records.append({"seq": seq, "time": cur_ms, "type": "turn/start", "data": {"turn": turn_num}})
            seq += 1
            cur_ms += 10
            if t["role"] == "user":
                records.append(
                    {
                        "seq": seq,
                        "time": cur_ms,
                        "type": "user/message",
                        "surfaceOp": "append",
                        "data": {
                            "id": f"msg-u-{turn_num}-{uuid.uuid4().hex[:8]}",
                            "role": "user",
                            "timestamp": cur_ms,
                            "source": {"kind": "user"},
                            "content": [{"type": "text", "text": body}],
                        },
                    }
                )
                seq += 1
                cur_ms += 10
            else:
                records.append({"seq": seq, "time": cur_ms, "type": "step/start", "data": {"turn": turn_num, "step": 1}})
                seq += 1
                cur_ms += 10
                records.append(
                    {
                        "seq": seq,
                        "time": cur_ms,
                        "type": "assistant/message",
                        "surfaceOp": "append",
                        "data": {
                            "turn": turn_num,
                            "step": 1,
                            "stream": [],
                            "message": {
                                "id": f"msg-a-{turn_num}-{uuid.uuid4().hex[:8]}",
                                "role": "assistant",
                                "timestamp": cur_ms,
                                "api": "openai-completions",
                                "provider": "deepseek",
                                "model": "deepseek-chat",
                                "usage": {
                                    "input": 0,
                                    "output": 0,
                                    "cacheRead": 0,
                                    "cacheWrite": 0,
                                    "totalTokens": 0,
                                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
                                },
                                "stopReason": "stop",
                                "source": {"kind": "model", "provider": "deepseek", "model": "deepseek-chat"},
                                "content": [{"type": "text", "text": body}],
                            },
                        },
                    }
                )
                seq += 1
                cur_ms += 10
                records.append({"seq": seq, "time": cur_ms, "type": "step/end", "data": {"turn": turn_num, "step": 1}})
                seq += 1
                cur_ms += 10
            records.append(
                {
                    "seq": seq,
                    "time": cur_ms,
                    "type": "turn/end",
                    "data": {"turn": turn_num, "reason": {"kind": "completed"}},
                }
            )
            seq += 1
            cur_ms += 10
            turn_num += 1

        dsh_rel_dir = f"{dsh_project_key(resolved_cwd)}/{dsh_encode_segment(sid)}"
        sessions.append(
            {
                "session_id": sid,
                "branch_index": branch_index,
                "title": title,
                "cwd": resolved_cwd,
                "dsh_rel_dir": dsh_rel_dir,
                "source_node_ids": source_node_ids,
                "records": records,
            }
        )
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_dsh_v4_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


# ── 7. Gemini CLI, Cline/Roo, Goose, Aider, Continue, Zed (Read + Write!) ───


def parse_gemini_cli_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    sid = str(data.get("sessionId") or data.get("id") or p.stem)
    raw_items: list[dict[str, Any]] = []
    for i, m in enumerate(data.get("messages", [])):
        if not isinstance(m, dict):
            continue
        mtype = str(m.get("type") or m.get("role") or "user").lower()
        role = "assistant" if mtype in {"gemini", "model", "assistant"} else "user"
        content = m.get("content", m.get("parts", ""))
        raw_items.append({"node_id": str(m.get("id") or f"gem-{i}"), "role": role, "text": content_text(content), "timestamp": m.get("timestamp"), "content": content, "raw_record": m})
    nodes, roots, active = _chain_linear(raw_items)
    return ConversationGraph(source_format="gemini_cli_session", source_id=sid, title=str(data.get("title") or (nodes[0].text[:80].strip() if nodes else sid)), workspace=data.get("projectPath") or data.get("cwd"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"project_hash": data.get("projectHash"), "source_file": p.name}, raw_source=data, links=_collect_links(nodes), app_mode="cli")


def build_gemini_cli_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project a ConversationGraph into real Gemini CLI 0.33+ `tmp/<slug>/chats/session-*.json`."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    raw_slug = re.sub(r"[^a-z0-9_-]", "", (Path(resolved_cwd).name or "workspace").lower())
    slug = sanitize_single_segment(raw_slug or "workspace", fallback="workspace")
    project_hash = hashlib.sha256(resolved_cwd.encode("utf-8")).hexdigest()
    now_dt = datetime.now(UTC)
    now_iso = now_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    ts_prefix = now_dt.strftime("%Y-%m-%dT%H-%M")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        msgs = []
        source_node_ids: list[str] = []
        for idx, turn in enumerate(turns):
            msgs.append({"id": str(uuid.uuid4()), "timestamp": turn["timestamp"] if isinstance(turn["timestamp"], str) else now_iso, "type": "user" if turn["role"] == "user" else "gemini", "content": "\n\n".join(turn["texts"])})
            source_node_ids.extend(turn["source_node_ids"])
        payload = {"sessionId": sid, "projectHash": project_hash, "startTime": now_iso, "lastUpdated": now_iso, "title": title, "messages": msgs}
        sessions.append({
            "session_id": sid,
            "branch_index": branch_index,
            "title": title,
            "cwd": resolved_cwd,
            "project_slug": slug,
            "project_hash": project_hash,
            "gemini_rel_subpath": f"tmp/{slug}/chats/session-{ts_prefix}-{sid[:8]}.json",
            "source_node_ids": source_node_ids,
            "payload": payload,
        })
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_gemini_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


def parse_cline_roo_task(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    task_dir = p if p.is_dir() else p.parent
    api_file = task_dir / "api_conversation_history.json" if p.is_dir() else p
    messages = json.loads(api_file.read_text(encoding="utf-8-sig"))
    raw_items = [{"node_id": f"cline-{i}", "role": str(m.get("role", "user")), "text": content_text(m.get("content", "")), "timestamp": m.get("ts"), "content": m.get("content", ""), "raw_record": m} for i, m in enumerate(messages) if isinstance(m, dict)]
    nodes, roots, active = _chain_linear(raw_items)
    title = nodes[0].text[:80].strip() if nodes and nodes[0].text.strip() else task_dir.name
    return ConversationGraph(source_format="cline_roo_task", source_id=task_dir.name, title=title, workspace=None, nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": api_file.name}, raw_source={"messages": messages}, links=_collect_links(nodes), app_mode="ide-extension")


def parse_cline_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    """Read Cline / Roo Code home (`tasks/*/api_conversation_history.json` + Cline 3.0 `data/db/sessions.db` + `data/tasks/*`)."""
    root = Path(path).expanduser()
    if root.is_file():
        if root.suffix in {".db", ".sqlite"}:
            con = sqlite3.connect(f"file:{root}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            out_db: list[ConversationGraph] = []
            try:
                for r in con.execute("SELECT * FROM sessions ORDER BY updated_at DESC"):
                    mp = str(r["messages_path"] or "")
                    if mp and Path(mp).is_file():
                        g = parse_cline_roo_task(mp)
                        out_db.append(
                            ConversationGraph(
                                source_format=g.source_format,
                                source_id=str(r["session_id"]),
                                title=str(r["prompt"] or g.title)[:120],
                                workspace=r["workspace_root"] or r["cwd"],
                                nodes=g.nodes,
                                root_ids=g.root_ids,
                                active_node_id=g.active_node_id,
                                metadata={**g.metadata, "model": r["model"], "parent_session_id": r["parent_session_id"]},
                                raw_source=g.raw_source,
                                links=g.links,
                                app_mode="cli",
                            )
                        )
                    if limit and len(out_db) >= limit:
                        break
            finally:
                con.close()
            return out_db
        return [parse_cline_roo_task(root)]
    if (root / "api_conversation_history.json").is_file():
        return [parse_cline_roo_task(root)]

    db_meta: dict[str, dict[str, Any]] = {}
    cdb = root / "data" / "db" / "sessions.db"
    if cdb.is_file():
        try:
            con = sqlite3.connect(f"file:{cdb}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            try:
                if {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}.intersection({"sessions"}):
                    for r in con.execute("SELECT * FROM sessions"):
                        db_meta[str(r["session_id"])] = dict(r)
            finally:
                con.close()
        except sqlite3.Error:
            pass

    raw_graphs = _parse_dir_files(
        root,
        (
            "data/tasks",
            "tasks",
            "User/globalStorage/saoudrizwan.claude-dev/tasks",
            "User/globalStorage/rooveterinaryinc.roo-cline/tasks",
        ),
        ("api_conversation_history.json",),
        parse_cline_roo_task,
        limit=limit,
    )
    seen: set[str] = set()
    out: list[ConversationGraph] = []
    for g in raw_graphs:
        if g.source_id in seen:
            continue
        seen.add(g.source_id)
        dm = db_meta.get(g.source_id)
        if dm:
            out.append(
                ConversationGraph(
                    source_format=g.source_format,
                    source_id=g.source_id,
                    title=str(dm.get("prompt") or g.title)[:120],
                    workspace=dm.get("workspace_root") or dm.get("cwd") or g.workspace,
                    nodes=g.nodes,
                    root_ids=g.root_ids,
                    active_node_id=g.active_node_id,
                    metadata={**g.metadata, "model": dm.get("model"), "parent_session_id": dm.get("parent_session_id")},
                    raw_source=g.raw_source,
                    links=g.links,
                    app_mode="ide-extension",
                )
            )
        else:
            out.append(g)
    return out


def build_cline_roo_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"{now_ms + branch_index}-{uuid.uuid4().hex[:6]}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        payload = [{"role": t["role"], "content": [{"type": "text", "text": "\n\n".join(t["texts"])}]} for t in turns]
        ui_messages = [
            {
                "ts": now_ms + idx,
                "type": "say",
                "say": "user_feedback" if t["role"] == "user" else "text",
                "text": "\n\n".join(t["texts"]),
            }
            for idx, t in enumerate(turns)
        ]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        sessions.append({
            "session_id": sid,
            "branch_index": branch_index,
            "title": title,
            "cwd": resolved_cwd,
            "source_node_ids": source_node_ids,
            "payload": payload,
            "ui_messages": ui_messages,
        })
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_cline_task_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


def merge_cline_sessions_batch(
    db_path: str | Path,
    entries: list[dict[str, Any]],
    *,
    on_collision: str = "refuse",
) -> list[dict[str, Any]]:
    """Batch-merge Cline sessions into Cline 3.0 CLI `data/db/sessions.db`."""
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    conn = sqlite3.connect(str(db), timeout=20.0)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                pid INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                exit_code INTEGER,
                status TEXT NOT NULL,
                status_lock INTEGER NOT NULL DEFAULT 0,
                interactive INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                cwd TEXT NOT NULL,
                workspace_root TEXT NOT NULL,
                team_name TEXT,
                enable_tools INTEGER NOT NULL,
                enable_spawn INTEGER NOT NULL,
                enable_teams INTEGER NOT NULL,
                parent_session_id TEXT,
                parent_agent_id TEXT,
                agent_id TEXT,
                conversation_id TEXT,
                is_subagent INTEGER NOT NULL DEFAULT 0,
                prompt TEXT,
                metadata_json TEXT,
                transcript_path TEXT NOT NULL DEFAULT '',
                hook_path TEXT NOT NULL,
                messages_path TEXT,
                updated_at TEXT NOT NULL
            );
            """
        )
        existing = {str(r[0]) for r in conn.execute("SELECT session_id FROM sessions")}
        results: list[dict[str, Any]] = []
        for entry in entries:
            sid = str(entry.get("session_id") or uuid.uuid4().hex[:12])
            if sid in existing:
                if on_collision == "refuse":
                    raise FileExistsError(f"cline session already exists in sessions.db: {sid}")
                if on_collision == "skip":
                    results.append({"session_id": sid, "action": "skipped"})
                    continue
                if on_collision == "rename":
                    sid = f"{sid}-{uuid.uuid4().hex[:6]}"
            cwd_val = str(entry.get("cwd") or "")
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (
                    session_id, source, pid, started_at, ended_at, exit_code, status, status_lock,
                    interactive, provider, model, cwd, workspace_root, enable_tools, enable_spawn,
                    enable_teams, is_subagent, prompt, metadata_json, transcript_path, hook_path,
                    messages_path, updated_at
                ) VALUES (?, 'cli', 0, ?, ?, 0, 'completed', 0, 1, 'anthropic', 'claude-sonnet-4-5',
                          ?, ?, 1, 0, 0, 0, ?, '{}', ?, '', ?, ?)
                """,
                (
                    sid,
                    now_iso,
                    now_iso,
                    cwd_val,
                    cwd_val,
                    str(entry.get("title") or sid),
                    str(entry.get("ui_messages_path") or ""),
                    str(entry.get("api_history_path") or ""),
                    now_iso,
                ),
            )
            existing.add(sid)
            results.append({"session_id": sid, "action": "merged"})
        conn.commit()
        return results
    finally:
        conn.close()


def parse_goose_sqlite(db_path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    """Read real Block Goose 1.60+ `sessions/sessions.db` SQLite store (`?mode=ro`)."""
    p = Path(db_path).expanduser()
    if not p.is_file():
        return []
    graphs: list[ConversationGraph] = []
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "sessions" not in tables:
            return []
        tags_by_sid: dict[str, dict[str, str]] = {}
        if "session_tags" in tables:
            for tr in conn.execute("SELECT session_id, key, value FROM session_tags"):
                tags_by_sid.setdefault(str(tr["session_id"]), {})[str(tr["key"])] = str(tr["value"])
        sql = "SELECT * FROM sessions ORDER BY updated_at DESC"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        for srow in conn.execute(sql):
            sd = dict(srow)
            sid = str(sd.get("id") or "")
            if not sid:
                continue
            raw_items: list[dict[str, Any]] = []
            if "messages" in tables:
                for mrow in conn.execute(
                    "SELECT id, message_id, role, content_json, created_timestamp FROM messages WHERE session_id = ? ORDER BY created_timestamp ASC, id ASC",
                    (sid,),
                ):
                    try:
                        c_obj = json.loads(mrow["content_json"] or "[]")
                    except json.JSONDecodeError:
                        c_obj = mrow["content_json"] or ""
                    raw_items.append({
                        "node_id": str(mrow["message_id"] or f"goose-{mrow['id']}"),
                        "role": str(mrow["role"] or "user"),
                        "text": content_text(c_obj),
                        "timestamp": mrow["created_timestamp"],
                        "content": c_obj,
                        "raw_record": {"message_id": mrow["message_id"], "role": mrow["role"], "content": c_obj},
                    })
            nodes, roots, active = _chain_linear(raw_items)
            ws = str(sd.get("working_dir") or "").strip() or None
            stags = tags_by_sid.get(sid, {})
            graphs.append(
                ConversationGraph(
                    source_format="goose_session",
                    source_id=sid,
                    title=str(sd.get("name") or sd.get("description") or sid),
                    workspace=ws,
                    nodes=nodes,
                    root_ids=roots,
                    active_node_id=active,
                    metadata={
                        "project_id": sd.get("project_id"),
                        "project_name": Path(ws).name if ws and ws not in {"/", "\\"} else None,
                        "section_name": stags.get("section"),
                        "parent_session_id": sd.get("parent_session_id"),
                        "source_file": p.name,
                    },
                    raw_source={"session_id": sid},
                    links=_collect_links(nodes),
                    app_mode="cli",
                )
            )
    finally:
        conn.close()
    return graphs


def parse_goose_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        if p.suffix in {".db", ".sqlite"}:
            return parse_goose_sqlite(p, limit=limit)
        return [parse_goose_session(p)]
    out: list[ConversationGraph] = []
    seen: set[str] = set()
    for db_cand in (p / "sessions" / "sessions.db", p / "sessions.db"):
        if db_cand.is_file():
            for g in parse_goose_sqlite(db_cand, limit=limit):
                if g.source_id not in seen:
                    seen.add(g.source_id)
                    out.append(g)
            break
    if limit and len(out) >= limit:
        return out[:limit]
    rem = (limit - len(out)) if limit else None
    for g in _parse_dir_files(p, ("sessions",), ("*.jsonl",), parse_goose_session, limit=rem):
        if g.source_id not in seen:
            seen.add(g.source_id)
            out.append(g)
    return out


def merge_goose_sessions_batch(
    db_path: str | Path,
    entries: list[dict[str, Any]],
    *,
    on_collision: str = "refuse",
) -> list[dict[str, Any]]:
    """Batch-merge Goose sessions into Goose 1.60+ `sessions/sessions.db` (`schema_version = 18`)."""
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    now_ts = int(datetime.now(UTC).timestamp())
    conn = sqlite3.connect(str(db), timeout=20.0)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (18, CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                user_set_name BOOLEAN DEFAULT FALSE,
                session_type TEXT NOT NULL DEFAULT 'user',
                working_dir TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extension_data TEXT DEFAULT '{}',
                total_tokens INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cache_read_tokens INTEGER,
                cache_write_tokens INTEGER,
                accumulated_total_tokens INTEGER,
                accumulated_input_tokens INTEGER,
                accumulated_output_tokens INTEGER,
                accumulated_cache_read_tokens INTEGER,
                accumulated_cache_write_tokens INTEGER,
                accumulated_cost REAL,
                schedule_id TEXT,
                recipe_json TEXT,
                user_recipe_values_json TEXT,
                provider_name TEXT,
                model_config_json TEXT,
                goose_mode TEXT NOT NULL DEFAULT 'auto',
                archived_at TIMESTAMP,
                project_id TEXT,
                parent_session_id TEXT,
                system_prompt_override TEXT,
                system_prompt_extras_json TEXT,
                container_id TEXT
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,
                session_id TEXT NOT NULL REFERENCES sessions(id),
                role TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_timestamp INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tokens INTEGER,
                metadata_json TEXT
            );
            CREATE TABLE IF NOT EXISTS usage_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                created_timestamp INTEGER NOT NULL,
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                cache_read_tokens INTEGER,
                cache_write_tokens INTEGER,
                cost REAL,
                cost_source TEXT,
                is_compaction INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS session_tags (
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (session_id, key)
            );
            CREATE TABLE IF NOT EXISTS provider_inventory_entries (
                inventory_key TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                provider_family TEXT NOT NULL,
                last_updated_at TEXT,
                last_refresh_attempt_at TEXT,
                last_refresh_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS provider_inventory_models (
                inventory_key TEXT NOT NULL REFERENCES provider_inventory_entries(inventory_key) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                model_id TEXT NOT NULL,
                name TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                PRIMARY KEY (inventory_key, ordinal)
            );
            """
        )
        existing = {str(r[0]) for r in conn.execute("SELECT id FROM sessions")}
        results: list[dict[str, Any]] = []
        for entry in entries:
            records = entry.get("records") or []
            hdr = records[0] if records and isinstance(records[0], dict) and "role" not in records[0] else {}
            sid = str(hdr.get("id") or entry.get("session_id") or uuid.uuid4())
            if sid in existing:
                if on_collision == "refuse":
                    raise FileExistsError(f"goose session already exists in sessions.db: {sid}")
                if on_collision == "skip":
                    results.append({"session_id": sid, "action": "skipped"})
                    continue
                if on_collision == "rename":
                    sid = str(uuid.uuid4())
            title = str(hdr.get("description") or entry.get("title") or sid)
            wdir = str(hdr.get("working_dir") or entry.get("cwd") or "")
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (
                    id, name, description, user_set_name, session_type, working_dir,
                    created_at, updated_at, extension_data, total_tokens, input_tokens, output_tokens,
                    goose_mode, system_prompt_extras_json
                ) VALUES (?, ?, '', 1, 'user', ?, ?, ?, '{}', 0, 0, 0, 'auto', '{}')
                """,
                (sid, title, wdir, now_str, now_str),
            )
            for idx_m, rec in enumerate(records):
                if not isinstance(rec, dict) or "role" not in rec:
                    continue
                c_val = rec.get("content", [])
                if isinstance(c_val, str):
                    c_val = [{"type": "text", "text": c_val}]
                cts = int(rec.get("created") or (now_ts + idx_m))
                conn.execute(
                    """
                    INSERT INTO messages (message_id, session_id, role, content_json, created_timestamp, timestamp, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, '{"userVisible":true,"agentVisible":true}')
                    """,
                    (f"msg_{sid}_{uuid.uuid4()}", sid, str(rec["role"]), json.dumps(c_val, ensure_ascii=False), cts, now_str),
                )
            existing.add(sid)
            results.append({"session_id": sid, "action": "merged"})
        conn.commit()
        return results
    finally:
        conn.close()


def parse_goose_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    records = [json.loads(l) for l in p.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    meta = records[0] if records and "description" in records[0] and "role" not in records[0] else {}
    raw_items = [{"node_id": str(r.get("id") or f"goose-{i}"), "role": str(r["role"]), "text": content_text(r.get("content", "")), "timestamp": r.get("created"), "content": r.get("content", ""), "raw_record": r} for i, r in enumerate(records) if "role" in r]
    nodes, roots, active = _chain_linear(raw_items)
    return ConversationGraph(source_format="goose_session", source_id=str(meta.get("id") or p.stem), title=str(meta.get("description") or p.stem), workspace=meta.get("working_dir"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name}, raw_source={"records": records}, links=_collect_links(nodes), app_mode="cli")


def build_goose_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ts = int(datetime.now(UTC).timestamp())
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        records: list[dict[str, Any]] = [{"id": sid, "description": title, "working_dir": resolved_cwd, "message_count": len(turns)}]
        source_node_ids: list[str] = []
        for idx, t in enumerate(turns):
            records.append({"id": f"gm-{idx}", "role": t["role"], "created": now_ts + idx, "content": [{"type": "text", "text": "\n\n".join(t["texts"])}]})
            source_node_ids.extend(t["source_node_ids"])
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "records": records})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_goose_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


def parse_aider_history(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    text = p.read_text(encoding="utf-8-sig")
    raw_items: list[dict[str, Any]] = []
    blocks = re.split(r"(?m)^####\s+", text)
    for idx, blk in enumerate(blocks[1:], 1):
        lines = blk.splitlines()
        if not lines:
            continue
        user_line = lines[0].strip()
        asst_body = "\n".join(lines[1:]).strip()
        if user_line:
            raw_items.append({"node_id": f"aider-u-{idx}", "role": "user", "text": user_line, "raw_record": {"turn": idx, "role": "user"}})
        if asst_body:
            raw_items.append({"node_id": f"aider-a-{idx}", "role": "assistant", "text": asst_body, "raw_record": {"turn": idx, "role": "assistant"}})
    nodes, roots, active = _chain_linear(raw_items)
    return ConversationGraph(source_format="aider_history", source_id=p.parent.name or p.stem, title=f"Aider History ({p.parent.name})", workspace=str(p.parent.resolve()), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name}, raw_source={"markdown_length": len(text)}, links=_collect_links(nodes), app_mode="cli")


def build_aider_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())[:12]
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        md_lines = [f"# aider chat started at {now_iso}", f"# Imported by Nexus Memory: {title}", ""]
        source_node_ids: list[str] = []
        for t in turns:
            body = "\n\n".join(t["texts"])
            if t["role"] == "user":
                md_lines.append(f"#### {body.splitlines()[0]}")
                if len(body.splitlines()) > 1:
                    md_lines.extend(body.splitlines()[1:])
            else:
                md_lines.append(body)
            md_lines.append("")
            source_node_ids.extend(t["source_node_ids"])
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "markdown": "\n".join(md_lines) + "\n"})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_aider_history_md_per_leaf_path"})
    return sessions, losses


def parse_continue_session(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and entry.get("sessionId"):
                cand = p.parent / f"{entry['sessionId']}.json"
                if cand.is_file():
                    return parse_continue_session(cand)
        return ConversationGraph(source_format="continue_session", source_id=p.stem, title=p.stem, workspace=None, nodes=(), root_ids=(), active_node_id=None, metadata={"source_file": p.name}, raw_source={"index": data}, app_mode="ide-extension")
    raw_items: list[dict[str, Any]] = []
    for i, item in enumerate(data.get("history", [])):
        msg = item.get("message") if isinstance(item, dict) and isinstance(item.get("message"), dict) else item
        if not isinstance(msg, dict) or "role" not in msg:
            continue
        content = msg.get("content", "")
        raw_items.append({"node_id": f"cont-{i}", "role": str(msg["role"]), "text": content_text(content), "content": content, "raw_record": item})
    nodes, roots, active = _chain_linear(raw_items)
    return ConversationGraph(source_format="continue_session", source_id=str(data.get("sessionId") or p.stem), title=str(data.get("title") or p.stem), workspace=data.get("workspaceDirectory"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name}, raw_source=data, links=_collect_links(nodes), app_mode="ide-extension")


def build_continue_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        history = [{"message": {"role": t["role"], "content": "\n\n".join(t["texts"])}, "contextItems": []} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        sessions.append({
            "session_id": sid,
            "branch_index": branch_index,
            "title": title,
            "cwd": resolved_cwd,
            "source_node_ids": source_node_ids,
            "payload": {"sessionId": sid, "title": title, "dateCreated": now_iso, "workspaceDirectory": resolved_cwd, "history": history},
            "session_index_entry": {"sessionId": sid, "title": title, "dateCreated": now_iso, "workspaceDirectory": resolved_cwd},
        })
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_continue_session_per_leaf_path"})
    return sessions, losses


def parse_zed_threads_db(db_path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    """Read real Zed 1.30+ `threads/threads.db` SQLite store (`threads` table, `json` or `zstd` blob)."""
    p = Path(db_path).expanduser()
    if not p.is_file():
        return []
    graphs: list[ConversationGraph] = []
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "threads" not in tables:
            return []
        sql = "SELECT * FROM threads ORDER BY updated_at DESC"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        for row in conn.execute(sql):
            rd = dict(row)
            tid = str(rd.get("id") or "")
            if not tid:
                continue
            raw_blob = rd.get("data")
            dtype = str(rd.get("data_type") or "json").lower()
            decoded: dict[str, Any] = {}
            if raw_blob is not None:
                raw_bytes = raw_blob if isinstance(raw_blob, bytes) else str(raw_blob).encode("utf-8")
                if dtype == "zstd":
                    try:
                        import zstandard  # type: ignore[import-not-found]
                        raw_bytes = zstandard.ZstdDecompressor().decompress(raw_bytes)
                    except Exception:
                        raw_bytes = b"{}"
                try:
                    decoded = json.loads(raw_bytes.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    decoded = {}
            raw_items: list[dict[str, Any]] = []
            for i, m in enumerate(decoded.get("messages", [])):
                if isinstance(m, dict):
                    role = str(m.get("role") or ("user" if "User" in m else "assistant"))
                    content = m.get("segments", m.get("content", m.get("User", m.get("Agent", ""))))
                    raw_items.append({"node_id": str(m.get("id") or f"zed-{i}"), "role": role.lower(), "text": content_text(content), "timestamp": m.get("timestamp") or rd.get("updated_at"), "content": content, "raw_record": m})
            nodes, roots, active = _chain_linear(raw_items)
            ws = decoded.get("cwd") or decoded.get("worktree")
            if not ws and isinstance(rd.get("folder_paths"), str) and rd["folder_paths"].strip():
                ws = rd["folder_paths"].split("\n")[0].strip() or None
            graphs.append(
                ConversationGraph(
                    source_format="zed_thread",
                    source_id=tid,
                    title=str(rd.get("summary") or decoded.get("summary") or decoded.get("title") or tid),
                    workspace=ws,
                    nodes=nodes,
                    root_ids=roots,
                    active_node_id=active,
                    metadata={"parent_session_id": rd.get("parent_id"), "source_file": p.name},
                    raw_source={"id": tid, "summary": rd.get("summary")},
                    links=_collect_links(nodes),
                    app_mode="ide-extension",
                )
            )
    finally:
        conn.close()
    return graphs


def parse_zed_home(path: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    p = Path(path).expanduser()
    if p.is_file():
        if p.suffix in {".db", ".sqlite"}:
            return parse_zed_threads_db(p, limit=limit)
        return [parse_zed_thread(p)]
    out: list[ConversationGraph] = []
    seen: set[str] = set()
    for db_cand in (p / "threads" / "threads.db", p / "threads.db"):
        if db_cand.is_file():
            for g in parse_zed_threads_db(db_cand, limit=limit):
                if g.source_id not in seen:
                    seen.add(g.source_id)
                    out.append(g)
            break
    if limit and len(out) >= limit:
        return out[:limit]
    rem = (limit - len(out)) if limit else None
    for g in _parse_dir_files(p, ("threads",), ("*.json",), parse_zed_thread, exclude_names={"settings.json"}, limit=rem):
        if g.source_id not in seen:
            seen.add(g.source_id)
            out.append(g)
    return out


def merge_zed_threads_batch(
    db_path: str | Path,
    payloads: list[dict[str, Any]],
    *,
    on_collision: str = "refuse",
) -> list[dict[str, Any]]:
    """Batch-merge Zed thread JSON payloads into Zed 1.30+ `threads/threads.db`."""
    db = Path(db_path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    conn = sqlite3.connect(str(db), timeout=20.0)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                folder_paths TEXT,
                folder_paths_order TEXT,
                summary TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data_type TEXT NOT NULL,
                data BLOB NOT NULL,
                created_at TEXT
            );
            """
        )
        cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(threads)")}
        existing = {str(r[0]) for r in conn.execute("SELECT id FROM threads")}
        results: list[dict[str, Any]] = []
        for pld in payloads:
            tid = str(pld.get("id") or uuid.uuid4())
            if tid in existing:
                if on_collision == "refuse":
                    raise FileExistsError(f"zed thread already exists in threads.db: {tid}")
                if on_collision == "skip":
                    results.append({"thread_id": tid, "action": "skipped"})
                    continue
                if on_collision == "rename":
                    tid = str(uuid.uuid4())
                    pld = {**pld, "id": tid}
            summary = str(pld.get("summary") or pld.get("title") or tid)
            cwd_val = str(pld.get("cwd") or "")
            raw_bytes = json.dumps(pld, ensure_ascii=False).encode("utf-8")
            vals: dict[str, Any] = {
                "id": tid,
                "parent_id": pld.get("parent_id"),
                "folder_paths": cwd_val,
                "folder_paths_order": "0" if cwd_val else "",
                "summary": summary,
                "updated_at": now_iso,
                "data_type": "json",
                "data": raw_bytes,
                "created_at": now_iso,
            }
            icols = [c for c in vals if c in cols]
            conn.execute(
                f"INSERT OR REPLACE INTO threads ({', '.join(icols)}) VALUES ({', '.join('?' for _ in icols)})",
                tuple(vals[c] for c in icols),
            )
            existing.add(tid)
            results.append({"thread_id": tid, "action": "merged"})
        conn.commit()
        return results
    finally:
        conn.close()


def parse_zed_thread(path: str | Path) -> ConversationGraph:
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    raw_items: list[dict[str, Any]] = []
    for i, m in enumerate(data.get("messages", [])):
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "user")
        content = m.get("segments", m.get("content", ""))
        raw_items.append({"node_id": str(m.get("id") or f"zed-{i}"), "role": role, "text": content_text(content), "timestamp": m.get("timestamp"), "content": content, "raw_record": m})
    nodes, roots, active = _chain_linear(raw_items)
    return ConversationGraph(source_format="zed_thread", source_id=str(data.get("id") or p.stem), title=str(data.get("summary") or data.get("title") or p.stem), workspace=data.get("cwd") or data.get("worktree"), nodes=nodes, root_ids=roots, active_node_id=active, metadata={"source_file": p.name}, raw_source=data, links=_collect_links(nodes), app_mode="ide-extension")


def build_zed_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        msgs = [{"id": str(uuid.uuid4()), "role": t["role"], "timestamp": now_iso, "segments": [{"type": "text", "text": "\n\n".join(t["texts"])}]} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": {"id": sid, "summary": title, "cwd": resolved_cwd, "messages": msgs}})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_zed_thread_per_leaf_path"})
    return sessions, losses


def _parse_dir_files(
    root: Path,
    subdirs: tuple[str, ...],
    patterns: tuple[str, ...],
    parser_fn: Callable[[Path], ConversationGraph],
    *,
    exclude_names: set[str] | None = None,
    limit: int | None = None,
) -> list[ConversationGraph]:
    skip = exclude_names or set()
    bases = [root / sub for sub in subdirs if (root / sub).is_dir()]
    if not bases:
        bases = [root]
    files: list[Path] = []
    seen: set[Path] = set()
    for b in bases:
        for pat in patterns:
            for fp in b.rglob(pat):
                if fp.is_file() and fp.name not in skip and fp not in seen:
                    seen.add(fp)
                    files.append(fp)
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    out: list[ConversationGraph] = []
    for fp in files:
        try:
            out.append(parser_fn(fp))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if limit and len(out) >= limit:
            break
    return out


# ── Unified Auto-Detect Loader ───────────────────────────────────────────────


def load_any_source(
    path: str | Path,
    *,
    source_format: str | None = None,
    claude_dir: str | Path | None = None,
    section_filter: str | None = None,
    project_filter: str | None = None,
    limit: int | None = None,
    include_subagents: bool = False,
    on_progress: Callable[[str, int, int, str], None] | None = None,
) -> tuple[list[ConversationGraph], dict[str, bytes]]:
    p = Path(path).expanduser()
    fmt = (source_format or "auto").lower()

    if fmt == "chatgpt":
        return parse_export_with_assets(p)
    if fmt == "codex":
        return (
            parse_codex_home(
                p,
                section_filter=section_filter,
                project_filter=project_filter,
                limit=limit,
                on_progress=on_progress,
            )
            if p.is_dir()
            else [parse_rollout(p)]
        ), {}
    if fmt == "codex-app":
        return parse_codex_app_snapshot(p), {}
    if fmt == "claude-code":
        cc_limit = limit if not (project_filter or section_filter) else None
        return (
            parse_claude_code_dir(p, limit=cc_limit, on_progress=on_progress)
            if p.is_dir()
            else [parse_claude_code_session(p)]
        ), {}
    if fmt in {"claude-desktop-3p", "claude-desktop-3p-all", "claude-desktop-3p-chat", "claude-desktop-3p-cowork", "claude-desktop-3p-code"}:
        if p.is_dir() and p.name.startswith("local_"):
            return [parse_local_agent_session(p)], {}
        lanes = ("chat", "cowork", "code") if fmt in {"claude-desktop-3p", "claude-desktop-3p-all"} else (fmt.rsplit("-", 1)[-1],)
        by_lane = parse_claude_desktop_3p_root(
            p,
            claude_dir=claude_dir,
            lanes=lanes,
            limit=limit if not (project_filter or section_filter) else None,
            include_subagents=include_subagents,
        )
        return [*by_lane["chat"], *by_lane["cowork"], *by_lane["code"]], {}
    if fmt == "antigravity":
        return (
            parse_antigravity_brain_dir(
                p,
                limit=limit,
                include_subagents=include_subagents,
                project_filter=project_filter,
                section_filter=section_filter,
                on_progress=on_progress,
            )
            if p.is_dir()
            else [parse_antigravity_transcript(p)]
        ), {}
    if fmt == "workbuddy":
        return (parse_workbuddy_home(p, limit=limit) if p.is_dir() else [parse_workbuddy_session(p)]), {}
    if fmt in {"t3code", "t3-code"}:
        return parse_t3code_source(p, limit=limit, include_subagents=True if p.is_file() else (include_subagents or True)), {}
    if fmt == "kiro":
        return parse_kiro_home(p, limit=limit), {}
    if fmt == "amp":
        return parse_amp_home(p, limit=limit), {}
    if fmt == "trae":
        return parse_trae_home(p, limit=limit), {}
    if fmt in {"warp-oz", "warp", "oz"}:
        return parse_warp_oz_home(p, limit=limit), {}
    if fmt == "windsurf":
        return parse_windsurf_home(p, limit=limit), {}
    if fmt == "opencode":
        if p.is_file() and p.suffix in {".db", ".sqlite"}:
            return parse_opencode_sqlite(p, limit=limit, include_subagents=include_subagents), {}
        return (parse_opencode_storage_dir(p, limit=limit, include_subagents=include_subagents) if p.is_dir() else [parse_opencode_session(p)]), {}
    if fmt == "pi":
        return (
            _parse_dir_files(p, ("agent/sessions", "sessions"), ("*.jsonl",), parse_pi_session, limit=limit)
            if p.is_dir()
            else [parse_pi_session(p)]
        ), {}
    if fmt == "cursor":
        if p.is_dir():
            db = p / "User" / "globalStorage" / "state.vscdb"
            if db.is_file():
                return parse_cursor_vscdb(db), {}
        return parse_cursor_vscdb(p), {}
    if fmt == "dsh":
        return parse_dsh_directory(p), {}
    if fmt in {"cline", "roo", "cline-roo"}:
        return parse_cline_home(p, limit=limit), {}
    if fmt in {"gemini", "gemini-cli"}:
        if p.is_dir():
            return _parse_dir_files(p, ("tmp",), ("session-*.json",), parse_gemini_cli_session, exclude_names={"projects.json", "settings.json"}, limit=limit), {}
        return [parse_gemini_cli_session(p)], {}
    if fmt == "goose":
        return parse_goose_home(p, limit=limit), {}
    if fmt == "aider":
        if p.is_dir():
            return _parse_dir_files(p, (), (".aider.chat.history*.md",), parse_aider_history, limit=limit), {}
        return [parse_aider_history(p)], {}
    if fmt == "continue":
        if p.is_dir():
            return _parse_dir_files(p, ("sessions",), ("*.json",), parse_continue_session, exclude_names={"config.json", "sessions.json"}, limit=limit), {}
        return [parse_continue_session(p)], {}
    if fmt == "zed":
        return parse_zed_home(p, limit=limit), {}
    if fmt == "portable":
        return parse_portable_bundle(p), {}

    # Deterministic auto-detection
    if p.is_dir():
        if (p / "portable.json").is_file():
            return parse_portable_bundle(p / "portable.json"), {}
        if (p / ".system_generated" / "logs" / "transcript.jsonl").is_file() or (p / "transcript.jsonl").is_file():
            return [parse_antigravity_transcript(p)], {}
        if (p / "brain").is_dir() or any((c / ".system_generated" / "logs" / "transcript.jsonl").is_file() for c in p.iterdir() if c.is_dir()):
            return parse_antigravity_brain_dir(
                p,
                limit=limit,
                include_subagents=include_subagents,
                project_filter=project_filter,
                section_filter=section_filter,
                on_progress=on_progress,
            ), {}
        if (p / "User" / "globalStorage" / "state.vscdb").is_file():
            return parse_cursor_vscdb(p / "User" / "globalStorage" / "state.vscdb"), {}
        if (p / "workbuddy.db").is_file() or (p / "edge-sync-mapping-v4.db").is_file():
            return parse_workbuddy_home(p, limit=limit), {}
        if (p / "userdata" / "statev2.sqlite").is_file():
            return parse_t3code_source(p, limit=limit), {}
        if (p / "local-agent-mode-sessions").is_dir() or (p / "claude-code-sessions").is_dir():
            by_lane = parse_claude_desktop_3p_root(p, claude_dir=claude_dir, limit=limit, include_subagents=include_subagents)
            return [*by_lane["chat"], *by_lane["cowork"], *by_lane["code"]], {}
        if p.name.startswith("local_") and ((p / "audit.jsonl").is_file() or p.with_suffix(".json").is_file()):
            return [parse_local_agent_session(p)], {}
        if (p / "opencode.db").is_file() or (p / "storage" / "session").is_dir() or ((p / "session").is_dir() and (p / "message").is_dir()):
            return parse_opencode_storage_dir(p, limit=limit, include_subagents=include_subagents), {}
        if (p / "data.sqlite3").is_file():
            return parse_kiro_home(p, limit=limit), {}
        if (p / "sessions" / "sessions.db").is_file():
            return parse_goose_home(p, limit=limit), {}
        if (p / "data" / "db" / "sessions.db").is_file() or ((p / "data" / "tasks").is_dir() and any((p / "data" / "tasks").rglob("api_conversation_history.json"))):
            return parse_cline_home(p, limit=limit), {}
        if (p / "agent" / "sessions").is_dir():
            return _parse_dir_files(p, ("agent/sessions",), ("*.jsonl",), parse_pi_session, limit=limit), {}
        if (p / "state_5.sqlite").is_file() or (p / "session_index.jsonl").is_file() or (p / "archived_sessions").is_dir():
            return parse_codex_home(p, section_filter=section_filter, project_filter=project_filter, limit=limit), {}
        if (p / "cascade").is_dir():
            return parse_windsurf_home(p, limit=limit), {}
        if (p / "trajectories").is_dir():
            return parse_trae_home(p, limit=limit), {}
        if (p / "threads").is_dir() or (p / "threads.db").is_file():
            if (p / "threads" / "threads.db").is_file() or (p / "threads.db").is_file():
                return parse_zed_home(p, limit=limit), {}
            sample_t = next((f for f in sorted((p / "threads").rglob("*.json")) if f.is_file()), None)
            if sample_t is not None and sample_t.name.startswith("T-"):
                return parse_amp_home(p, limit=limit), {}
            return parse_zed_home(p, limit=limit), {}
        if (p / "tasks").is_dir() and any((p / "tasks").rglob("api_conversation_history.json")):
            return parse_cline_home(p, limit=limit), {}
        if (p / "tmp").is_dir() and (any((p / "tmp").rglob("session-*.json")) or any((p / "tmp").rglob(".project_root"))):
            return _parse_dir_files(p, ("tmp",), ("session-*.json",), parse_gemini_cli_session, exclude_names={"projects.json", "settings.json"}, limit=limit), {}
        if (p / "sessions").is_dir():
            if any((p / "sessions").rglob("*.jsonl.zstd")) or any((p / "sessions").rglob("session.v*.jsonl")):
                return parse_dsh_directory(p / "sessions"), {}
            sample_jl = next((f for f in sorted((p / "sessions").rglob("*.jsonl")) if f.is_file()), None)
            if sample_jl is not None:
                try:
                    fl = next((l for l in sample_jl.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()), "{}")
                    hdr = json.loads(fl)
                    if isinstance(hdr, dict):
                        if hdr.get("type") == "session_header" or "dsh_schema_version" in hdr:
                            return parse_dsh_directory(p / "sessions"), {}
                        if hdr.get("type") == "session" and ("isSeeded" in hdr or "delegationDepth" in hdr):
                            return parse_dsh_directory(p / "sessions"), {}
                        if hdr.get("type") in {"workbuddy_session_meta", "session-meta"}:
                            return parse_workbuddy_home(p, limit=limit), {}
                        if hdr.get("type") == "kiro_session_meta":
                            return parse_kiro_home(p, limit=limit), {}
                        if hdr.get("type") == "session" and "version" in hdr:
                            return _parse_dir_files(p, ("sessions",), ("*.jsonl",), parse_pi_session, limit=limit), {}
                        if "description" in hdr or "working_dir" in hdr:
                            return _parse_dir_files(p, ("sessions",), ("*.jsonl",), parse_goose_session, limit=limit), {}
                except (OSError, json.JSONDecodeError):
                    pass
            sample_js = next((f for f in sorted((p / "sessions").rglob("*.json")) if f.is_file() and f.name != "config.json"), None)
            if sample_js is not None:
                try:
                    jhdr = json.loads(sample_js.read_text(encoding="utf-8-sig", errors="replace"))
                    if isinstance(jhdr, dict):
                        if str(jhdr.get("schema") or "").startswith("warp.oz.") or "blocks" in jhdr:
                            return parse_warp_oz_home(p, limit=limit), {}
                        if "history" in jhdr and "sessionId" in jhdr:
                            return _parse_dir_files(p, ("sessions",), ("*.json",), parse_continue_session, exclude_names={"config.json", "sessions.json"}, limit=limit), {}
                        if "conversation_id" in jhdr:
                            return parse_kiro_home(p, limit=limit), {}
                except (OSError, json.JSONDecodeError):
                    pass
            return parse_codex_home(p, section_filter=section_filter, project_filter=project_filter, limit=limit), {}
        if (p / "projects").is_dir():
            # Distinguish WorkBuddy `projects/*/*.jsonl` (`session-meta`) from Claude Code `projects/*/*.jsonl`
            sample_pj = next((f for f in sorted((p / "projects").rglob("*.jsonl")) if f.is_file()), None)
            if sample_pj is not None:
                try:
                    fl = next((l for l in sample_pj.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()), "{}")
                    if json.loads(fl).get("type") in {"session-meta", "workbuddy_session_meta"}:
                        return parse_workbuddy_home(p, limit=limit), {}
                except (OSError, json.JSONDecodeError):
                    pass
            return parse_claude_code_dir(p, limit=limit, on_progress=on_progress), {}
        if (p / "api_conversation_history.json").is_file():
            return [parse_cline_roo_task(p)], {}
        if any(p.glob(".aider.chat.history*.md")):
            return _parse_dir_files(p, (), (".aider.chat.history*.md",), parse_aider_history, limit=limit), {}
        if (p / "warp.sqlite").is_file() or p.name == "dev.warp.Warp-Stable" or p.name == ".warp":
            return parse_warp_oz_home(p, limit=limit), {}
        if any(p.glob("*.jsonl")):
            sample_root_jl = next((f for f in sorted(p.glob("*.jsonl")) if f.is_file()), None)
            if sample_root_jl is not None:
                try:
                    fl = next((l for l in sample_root_jl.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()), "{}")
                    if json.loads(fl).get("type") == "session":
                        return _parse_dir_files(p, (), ("*.jsonl",), parse_pi_session, limit=limit), {}
                except (OSError, json.JSONDecodeError):
                    pass
            return parse_dsh_directory(p), {}
        raise ValueError(f"cannot auto-detect harness source format for directory: {p}")

    name_lower = p.name.lower()
    if zipfile.is_zipfile(p):
        return parse_export_with_assets(p)
    if name_lower.endswith((".vscdb", ".sqlite", ".sqlite3", ".db")):
        try:
            con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
            try:
                tbls = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            finally:
                con.close()
        except sqlite3.Error:
            tbls = set()
        if "orchestration_v2_projection_threads" in tbls:
            return parse_t3code_source(p, limit=limit, include_subagents=include_subagents), {}
        if "session_v2" in tbls or ("session" in tbls and "project" in tbls and ("message" in tbls or "session_message" in tbls)):
            return parse_opencode_sqlite(p, limit=limit, include_subagents=include_subagents), {}
        if "conversations_v2" in tbls:
            return parse_kiro_home(p, limit=limit), {}
        if "agent_conversations" in tbls:
            return parse_warp_sqlite(p, limit=limit), {}
        if "threads" in tbls and name_lower == "threads.db":
            return parse_zed_threads_db(p, limit=limit), {}
        if "sessions" in tbls and "schema_version" in tbls and "messages" in tbls:
            return parse_goose_sqlite(p, limit=limit), {}
        if "sessions" in tbls and "subagent_spawn_queue" in tbls:
            return parse_cline_home(p, limit=limit), {}
        if "sessions" in tbls and "workspaces" in tbls:
            return parse_workbuddy_home(p.parent, limit=limit), {}
        return parse_cursor_vscdb(p), {}
    if name_lower.endswith(".md") and "aider" in name_lower:
        return [parse_aider_history(p)], {}
    if name_lower.endswith(".jsonl.zstd"):
        return parse_dsh_directory(p), {}
    if name_lower.endswith(".jsonl.zst"):
        return [parse_rollout(p)], {}
    if name_lower in {"transcript.jsonl", "transcript_full.jsonl"}:
        return [parse_antigravity_transcript(p)], {}
    if name_lower.endswith(".jsonl"):
        first_line = next((l for l in p.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()), "{}")
        first = json.loads(first_line)
        if first.get("type") in {"USER_INPUT", "PLANNER_RESPONSE", "SYSTEM_MESSAGE", "GENERIC"} and "step_index" in first:
            return [parse_antigravity_transcript(p)], {}
        if first.get("type") == "workbuddy_session_meta":
            return [parse_workbuddy_session(p)], {}
        if first.get("type") == "kiro_session_meta":
            return [parse_kiro_session(p)], {}
        if first.get("type") == "session_meta" or first.get("type") in {"response_item", "event_msg"}:
            return [parse_rollout(p)], {}
        if first.get("type") == "session" and ("isSeeded" in first or "delegationDepth" in first):
            return parse_dsh_directory(p), {}
        if first.get("type") == "session" and "version" in first:
            return [parse_pi_session(p)], {}
        if first.get("type") == "session_header" or "dsh_schema_version" in first:
            return parse_dsh_directory(p), {}
        if "parentUuid" in first or "sessionId" in first:
            return [parse_claude_code_session(p)], {}
        if "description" in first or ("role" in first and "created" in first):
            return [parse_goose_session(p)], {}
        return [parse_rollout(p)], {}

    raw = json.loads(p.read_text(encoding="utf-8-sig"))
    if isinstance(raw, dict):
        schema = str(raw.get("schema") or "")
        if schema.startswith("nexus-memory.portable-graph."):
            return parse_portable_bundle(p), {}
        if schema.startswith("t3code.thread.") or ("threadId" in raw and "messages" in raw and "workspacePath" in raw):
            return parse_t3code_source(p), {}
        if schema.startswith("trae.trajectory.") or ("llm_interactions" in raw and "task" in raw):
            return [parse_trae_trajectory(p)], {}
        if schema.startswith("warp.oz.") or ("blocks" in raw and "working_directory" in raw):
            return [parse_warp_oz_session(p)], {}
        if schema.startswith("windsurf.cascade.") or ("cascadeId" in raw and "steps" in raw):
            return [parse_windsurf_session(p)], {}
        if "v" in raw and "env" in raw and "messages" in raw and str(raw.get("id", "")).startswith("T-"):
            return [parse_amp_thread(p)], {}
        if "conversation_id" in raw and ("history" in raw or "messages" in raw):
            return [parse_kiro_session(p)], {}
        if "projects" in raw and ("threads" in raw or "sidebar_sections" in raw):
            return parse_codex_app_snapshot(p), {}
        if ("info" in raw and "messages" in raw) or ("projectID" in raw and "directory" in raw):
            return [parse_opencode_session(p)], {}
        if "history" in raw and "sessionId" in raw:
            return [parse_continue_session(p)], {}
        if "sessionId" in raw and "messages" in raw and "mapping" not in raw:
            return [parse_gemini_cli_session(p)], {}
        if "messages" in raw and ("summary" in raw or "worktree" in raw) and "mapping" not in raw:
            return [parse_zed_thread(p)], {}
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        if "sessionId" in raw[0] and "role" not in raw[0]:
            out_cont: list[ConversationGraph] = []
            for entry in raw:
                if isinstance(entry, dict) and entry.get("sessionId"):
                    cand = p.parent / f"{entry['sessionId']}.json"
                    if cand.is_file():
                        out_cont.append(parse_continue_session(cand))
            if out_cont:
                return out_cont, {}
        if "role" in raw[0] and "mapping" not in raw[0]:
            return [parse_cline_roo_task(p)], {}
    return parse_export_with_assets(p)
