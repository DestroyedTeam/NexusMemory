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
    parse_amp_thread,
    parse_kiro_session,
    parse_t3code_source,
    parse_trae_trajectory,
    parse_warp_oz_session,
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


# ── 3. OpenCode (real split `storage/{session,message,part}` + single JSON) ──


def parse_opencode_session(path: str | Path) -> ConversationGraph:
    """Read either a combined OpenCode JSON OR one session inside real `~/.local/share/opencode/storage/`."""
    p = Path(path).expanduser()
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    info = data.get("info") if isinstance(data.get("info"), dict) else data
    sid = str(info.get("id") or info.get("sessionID") or p.stem)
    title = info.get("title") or info.get("slug") or sid
    workspace = info.get("directory") or info.get("cwd") or info.get("projectPath")
    parent_id = info.get("parentID") or info.get("parentId")

    raw_items: list[dict[str, Any]] = []
    if isinstance(data.get("messages"), list):
        for idx, msg in enumerate(data["messages"]):
            if not isinstance(msg, dict):
                continue
            m_info = msg.get("info") if isinstance(msg.get("info"), dict) else msg
            role = str(m_info.get("role") or "user")
            parts = msg.get("parts") if isinstance(msg.get("parts"), list) else []
            if parts:
                text = "\n".join(str(pt.get("text") or "") for pt in parts if isinstance(pt, dict) and pt.get("type") in {"text", "reasoning"} and pt.get("text"))
                content: Any = parts
            else:
                content = m_info.get("content", "")
                text = content_text(content)
            raw_items.append({"node_id": str(m_info.get("id") or f"oc-{idx}"), "role": role, "text": text, "timestamp": (m_info.get("time") or {}).get("created") if isinstance(m_info.get("time"), dict) else m_info.get("timestamp"), "content": content, "raw_record": msg})
    else:
        # Real OpenCode split storage: storage/session/<proj>/<ses>.json -> storage/message/<ses>/*.json -> storage/part/<msg>/*.json
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
                parts: list[dict[str, Any]] = []
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


def parse_opencode_storage_dir(storage_dir: str | Path, *, limit: int | None = None) -> list[ConversationGraph]:
    """Read sessions from real OpenCode `~/.local/share/opencode/storage/`."""
    root = Path(storage_dir).expanduser()
    if (root / "storage").is_dir():
        root = root / "storage"
    sess_dir = root / "session"
    if not sess_dir.is_dir():
        return []
    out: list[ConversationGraph] = []
    for sf in sorted(sess_dir.rglob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if not sf.is_file():
            continue
        try:
            out.append(parse_opencode_session(sf))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if limit and len(out) >= limit:
            break
    return out


def build_opencode_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project a ConversationGraph into OpenCode session JSON + real split `storage/{session,message,part}` files."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ms = int(datetime.now(UTC).timestamp() * 1000)

    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = f"ses_{uuid.uuid4().hex[:20]}"
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        messages: list[dict[str, Any]] = []
        split_files: dict[str, dict[str, Any]] = {}
        source_node_ids: list[str] = []
        for idx, turn in enumerate(turns):
            mid = f"msg_{uuid.uuid4().hex[:16]}"
            pid = f"prt_{uuid.uuid4().hex[:12]}"
            text = "\n\n".join(turn["texts"])
            m_info = {"id": mid, "sessionID": sid, "role": turn["role"], "time": {"created": now_ms + idx}}
            p_obj = {"id": pid, "sessionID": sid, "messageID": mid, "type": "text", "text": text}
            messages.append({"info": m_info, "parts": [p_obj]})
            split_files[f"storage/message/{sid}/{mid}.json"] = m_info
            split_files[f"storage/part/{mid}/{pid}.json"] = p_obj
            source_node_ids.extend(turn["source_node_ids"])
        sess_info = {
            "id": sid,
            "version": "1.0.0",
            "projectID": "global",
            "title": title,
            "directory": resolved_cwd,
            "parentID": graph.metadata.get("parent_session_id"),
            "time": {"created": now_ms, "updated": now_ms},
            "nexusProvenance": {"source_format": graph.source_format, "source_id": graph.source_id},
        }
        split_files[f"storage/session/global/{sid}.json"] = sess_info
        sessions.append({
            "session_id": sid,
            "branch_index": branch_index,
            "title": title,
            "cwd": resolved_cwd,
            "source_node_ids": source_node_ids,
            "payload": {"info": sess_info, "messages": messages},
            "split_files": split_files,
        })
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_opencode_session_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


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


# ── 6. DeepSeek Harness / DSH (V4 authority > stale V2 + V4 writer) ──────────


def parse_dsh_directory(dsh_dir: str | Path) -> list[ConversationGraph]:
    root = Path(dsh_dir).expanduser()
    files = sorted(root.rglob("*.jsonl")) if root.is_dir() else [root]
    by_id: dict[str, tuple[int, ConversationGraph]] = {}
    for fp in files:
        if not fp.is_file():
            continue
        records = [json.loads(l) for l in fp.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
        if not records:
            continue
        header = records[0] if isinstance(records[0], dict) else {}
        schema_ver = int(header.get("dsh_schema_version") or header.get("schema_version") or (4 if "v4" in fp.name.lower() else 2))
        sid = str(header.get("session_id") or header.get("id") or fp.stem)
        raw_items: list[dict[str, Any]] = []
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
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for branch_index, path in enumerate(paths, 1):
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        records: list[dict[str, Any]] = [{"type": "session_header", "dsh_schema_version": 4, "session_id": sid, "title": title, "cwd": resolved_cwd, "timestamp": now_iso}]
        source_node_ids: list[str] = []
        for node in path:
            if node.role in {"user", "assistant", "system", "tool_call", "tool_result"}:
                records.append({"id": node.node_id, "role": node.role, "content": node.text, "timestamp": node.timestamp or now_iso})
                source_node_ids.append(node.node_id)
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "records": records})
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


def build_cline_roo_sessions(graph: ConversationGraph, *, cwd: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(int(datetime.now(UTC).timestamp() * 1000) + branch_index)
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        payload = [{"role": t["role"], "content": [{"type": "text", "text": "\n\n".join(t["texts"])}]} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": payload})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_cline_task_per_leaf_path; exact graph in portable.json"})
    return sessions, losses


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
    for branch_index, path in enumerate(paths, 1):
        turns, _, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        history = [{"message": {"role": t["role"], "content": "\n\n".join(t["texts"])}, "contextItems": []} for t in turns]
        source_node_ids = [nid for t in turns for nid in t["source_node_ids"]]
        sessions.append({"session_id": sid, "branch_index": branch_index, "title": title, "cwd": resolved_cwd, "source_node_ids": source_node_ids, "payload": {"sessionId": sid, "title": title, "workspaceDirectory": resolved_cwd, "history": history}})
    if len(paths) > 1:
        losses.append({"feature": "branch_topology", "disposition": "one_continue_session_per_leaf_path"})
    return sessions, losses


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
    if fmt in {"claude-desktop-3p", "claude-desktop-3p-chat", "claude-desktop-3p-cowork", "claude-desktop-3p-code"}:
        if p.is_dir() and p.name.startswith("local_"):
            return [parse_local_agent_session(p)], {}
        lanes = ("chat", "cowork", "code") if fmt == "claude-desktop-3p" else (fmt.rsplit("-", 1)[-1],)
        by_lane = parse_claude_desktop_3p_root(p, claude_dir=claude_dir, lanes=lanes)
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
        return parse_t3code_source(p), {}
    if fmt == "kiro":
        return [parse_kiro_session(p)], {}
    if fmt == "amp":
        return [parse_amp_thread(p)], {}
    if fmt == "trae":
        return [parse_trae_trajectory(p)], {}
    if fmt in {"warp-oz", "warp", "oz"}:
        return [parse_warp_oz_session(p)], {}
    if fmt == "windsurf":
        return [parse_windsurf_session(p)], {}
    if fmt == "opencode":
        return (parse_opencode_storage_dir(p, limit=limit) if p.is_dir() else [parse_opencode_session(p)]), {}
    if fmt == "pi":
        return [parse_pi_session(p)], {}
    if fmt == "cursor":
        if p.is_dir():
            db = p / "User" / "globalStorage" / "state.vscdb"
            if db.is_file():
                return parse_cursor_vscdb(db), {}
        return parse_cursor_vscdb(p), {}
    if fmt == "dsh":
        return parse_dsh_directory(p), {}
    if fmt in {"cline", "roo"}:
        return [parse_cline_roo_task(p)], {}
    if fmt in {"gemini", "gemini-cli"}:
        return [parse_gemini_cli_session(p)], {}
    if fmt == "goose":
        return [parse_goose_session(p)], {}
    if fmt == "aider":
        return [parse_aider_history(p)], {}
    if fmt == "continue":
        return [parse_continue_session(p)], {}
    if fmt == "zed":
        return [parse_zed_thread(p)], {}
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
            return parse_t3code_source(p), {}
        if (p / "local-agent-mode-sessions").is_dir() or (p / "claude-code-sessions").is_dir():
            by_lane = parse_claude_desktop_3p_root(p, claude_dir=claude_dir)
            return [*by_lane["chat"], *by_lane["cowork"], *by_lane["code"]], {}
        if p.name.startswith("local_") and ((p / "audit.jsonl").is_file() or p.with_suffix(".json").is_file()):
            return [parse_local_agent_session(p)], {}
        if (p / "storage" / "session").is_dir() or (p / "session").is_dir() and (p / "message").is_dir():
            return parse_opencode_storage_dir(p, limit=limit), {}
        if (p / "state_5.sqlite").is_file() or (p / "session_index.jsonl").is_file() or (p / "archived_sessions").is_dir():
            return parse_codex_home(p, section_filter=section_filter, project_filter=project_filter, limit=limit), {}
        if (p / "sessions").is_dir():
            sample_jl = next((f for f in sorted((p / "sessions").rglob("*.jsonl")) if f.is_file()), None)
            if sample_jl is not None:
                try:
                    fl = next((l for l in sample_jl.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()), "{}")
                    hdr = json.loads(fl)
                    if isinstance(hdr, dict):
                        if hdr.get("type") == "session_header" or "dsh_schema_version" in hdr:
                            return parse_dsh_directory(p / "sessions"), {}
                        if hdr.get("type") == "workbuddy_session_meta":
                            return parse_workbuddy_home(p, limit=limit), {}
                        if hdr.get("type") == "kiro_session_meta":
                            return [parse_kiro_session(f) for f in sorted((p / "sessions").rglob("*.jsonl")) if f.is_file()], {}
                        if "description" in hdr or "working_dir" in hdr:
                            return [parse_goose_session(f) for f in sorted((p / "sessions").rglob("*.jsonl")) if f.is_file()], {}
                except (OSError, json.JSONDecodeError):
                    pass
            return parse_codex_home(p, section_filter=section_filter, project_filter=project_filter, limit=limit), {}
        if (p / "projects").is_dir():
            return parse_claude_code_dir(p), {}
        if (p / "api_conversation_history.json").is_file():
            return [parse_cline_roo_task(p)], {}
        if any(p.glob("*.jsonl")):
            return parse_dsh_directory(p), {}
        raise ValueError(f"cannot auto-detect harness source format for directory: {p}")

    name_lower = p.name.lower()
    if zipfile.is_zipfile(p):
        return parse_export_with_assets(p)
    if name_lower.endswith(".vscdb") or name_lower.endswith(".sqlite") or name_lower.endswith(".db"):
        return parse_cursor_vscdb(p), {}
    if name_lower.endswith(".md") and "aider" in name_lower:
        return [parse_aider_history(p)], {}
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
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "role" in raw[0] and "mapping" not in raw[0]:
        return [parse_cline_roo_task(p)], {}
    return parse_export_with_assets(p)
