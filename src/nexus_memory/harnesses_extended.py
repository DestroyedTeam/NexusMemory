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


# ── 2. T3 Code (`~/.t3/userdata/threads/<id>.json` + `statev2.sqlite`) ───────


def parse_t3code_source(path: str | Path) -> list[ConversationGraph]:
    """Read T3 Code thread JSON OR `statev2.sqlite` (`threads`/`messages` tables)."""
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
            if "threads" in tables:
                msg_by_tid: dict[str, list[dict[str, Any]]] = {}
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
    """Project ConversationGraph into T3 Code thread JSON (`userdata/threads/<id>.json`)."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
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
            "provider": "portable",
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
