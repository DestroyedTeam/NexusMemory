"""Claude Desktop Third-Party Inference (`Claude-3p`, v7.37095.0 aligned) 3-Lane Adapter.

Strictly separates all 3 confirmed Claude Desktop 3P lanes and aligns sidecar schemas
with observed real `Claude-3p` (`7.37095.0`) files on macOS:
- Lane 1 (`claude-desktop-3p-chat`): `Claude-3p/local-agent-mode-sessions/<dev>/<org>/local_<uuid>/`
- Lane 2 (`claude-desktop-3p-cowork`): `Claude-3p/local-agent-mode-sessions/<dev>/<org>/local_<uuid>/`
- Lane 3 (`claude-desktop-3p-code`): `Claude-3p/claude-code-sessions/<dev>/<org>/local_<uuid>.json`
  strictly dual-key joined to `~/.claude/projects/<encoded-cwd>/<cliSessionId>.jsonl`
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .claude_code import (
    TESTED_CLAUDE_CODE_VERSION,
    _coalesce_alternating_turns,
    build_native_sessions,
    encode_jsonl,
    parse_claude_code_session,
    project_directory_name,
)
from .model import ConversationGraph, MessageNode, UsageSummary, content_text, extract_links
from .security import sanitize_single_segment

DEFAULT_3P_DEVICE_ID = "ant-did-nexus-staged"
DEFAULT_3P_ORG_ID = "org-nexus-staged"

SIDECAR_PII_KEYS = frozenset({"accountName", "emailAddress", "userEmail", "authToken", "sessionKey", "cookie"})


def default_claude_desktop_root(
    *,
    home: str | Path | None = None,
    platform: str | None = None,
    third_party: bool = True,
) -> Path:
    """Return platform-correct Claude Desktop root (`Claude-3p` vs standard `Claude`)."""
    base_home = Path(home).expanduser() if home is not None else Path.home()
    plat = platform or sys.platform
    app_name = "Claude-3p" if third_party else "Claude"
    if plat == "darwin":
        return base_home / "Library" / "Application Support" / app_name
    if plat == "win32":
        return base_home / "AppData" / "Roaming" / app_name
    return base_home / ".config" / app_name


def _sanitize_sidecar(sidecar: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in sidecar.items() if k not in SIDECAR_PII_KEYS}


def _detect_local_agent_mode(sidecar: dict[str, Any], session_dir: Path) -> str:
    explicit = str(sidecar.get("sessionMode") or sidecar.get("mode") or sidecar.get("surface") or "").lower()
    if explicit == "chat":
        return "claude-desktop-3p-chat"
    if explicit == "cowork":
        return "claude-desktop-3p-cowork"
    if (
        sidecar.get("processName")
        or sidecar.get("vmProcessName")
        or sidecar.get("userSelectedFolders")
        or (session_dir / ".claude" / "todos").is_dir()
    ):
        return "claude-desktop-3p-cowork"
    return "claude-desktop-3p-chat"


def parse_local_agent_session(
    session_dir: str | Path,
    *,
    lane_override: str | None = None,
) -> ConversationGraph:
    """Read one Claude Desktop 3P `local_<uuid>/` session (Chat or Cowork) without silent data loss."""
    sdir = Path(session_dir).expanduser()
    sidecar_path = sdir.with_suffix(".json")
    raw_sidecar: dict[str, Any] = {}
    if sidecar_path.is_file():
        try:
            loaded = json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
            if isinstance(loaded, dict):
                raw_sidecar = loaded
        except (json.JSONDecodeError, OSError):
            pass
    sidecar = _sanitize_sidecar(raw_sidecar)
    lane = lane_override or _detect_local_agent_mode(sidecar, sdir)

    raw_sid = str(sidecar.get("sessionId") or sdir.name)
    session_id = raw_sid.removeprefix("local_").removeprefix("remote_")
    audit_path = sdir / "audit.jsonl"

    records: list[dict[str, Any]] = []
    transcript_source = "audit.jsonl"
    if audit_path.is_file():
        for line_num, line in enumerate(audit_path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    records.append(entry)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid audit.jsonl at line {line_num}: {exc.msg}") from exc
    else:
        embedded_projects = sdir / ".claude" / "projects"
        if embedded_projects.is_dir():
            candidates = sorted(embedded_projects.rglob("*.jsonl"), key=lambda p: p.stat().st_size, reverse=True)
            if candidates:
                embedded = parse_claude_code_session(candidates[0])
                meta = dict(embedded.metadata)
                meta.update(
                    {
                        "desktop_lane": lane,
                        "sidecar": sidecar,
                        "transcript_source": str(candidates[0].relative_to(sdir)),
                        "is_archived": bool(sidecar.get("isArchived", False)),
                    }
                )
                return ConversationGraph(
                    source_format=lane.replace("-", "_"),
                    source_id=session_id,
                    title=str(sidecar.get("title") or embedded.title or "Untitled"),
                    workspace=(sidecar.get("userSelectedFolders") or [None])[0] or sidecar.get("cwd") or embedded.workspace,
                    nodes=embedded.nodes,
                    root_ids=embedded.root_ids,
                    active_node_id=embedded.active_node_id,
                    metadata=meta,
                    raw_source={"sidecar": sidecar, "embedded": embedded.raw_source},
                    usage=embedded.usage,
                    links=embedded.links,
                    app_mode=lane,
                )
        transcript_source = "metadata_only_no_transcript"

    nodes: list[MessageNode] = []
    seen_nids: set[str] = set()
    prev_id: str | None = None
    all_links: list[str] = []
    seen_links: set[str] = set()
    total_in = 0
    total_out = 0
    total_cost = 0.0
    has_cost = False
    hmac_present_count = 0
    subagent_turn_count = 0
    interruption_count = 0

    for idx, entry in enumerate(records):
        if entry.get("_audit_hmac"):
            hmac_present_count += 1
        etype = entry.get("type")
        ts = entry.get("_audit_timestamp") or entry.get("timestamp")
        parent_tu = entry.get("parent_tool_use_id")
        if parent_tu:
            subagent_turn_count += 1

        if etype in {"user", "assistant", "system"}:
            msg = entry.get("message") if isinstance(entry.get("message"), dict) else {}
            role = str(msg.get("role") or etype)
            content = msg.get("content", "")
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else None
            if usage:
                total_in += int(usage.get("input_tokens") or 0)
                total_out += int(usage.get("output_tokens") or 0)
            event_type = "message"
            if isinstance(content, list):
                btypes = {b.get("type") for b in content if isinstance(b, dict)}
                if "tool_result" in btypes and "text" not in btypes:
                    event_type = "tool_result"
                elif "tool_use" in btypes and "text" not in btypes:
                    event_type = "tool_use"
            text = content_text(content)
            node_links = extract_links(text)
            for u in node_links:
                if u not in seen_links:
                    seen_links.add(u)
                    all_links.append(u)
            nid = str(entry.get("uuid") or f"audit-{idx}")
            if nid in seen_nids:
                nid = f"{nid}-{idx}"
            seen_nids.add(nid)
            if nodes:
                prev = nodes[-1]
                nodes[-1] = MessageNode(
                    prev.node_id, prev.parent_id, (nid,), prev.role, prev.text, prev.timestamp,
                    prev.content, prev.raw_record, event_type=prev.event_type,
                    parent_tool_use_id=prev.parent_tool_use_id, attachments=prev.attachments,
                    links=prev.links, usage=prev.usage, interrupted=prev.interrupted,
                    is_sidechain=prev.is_sidechain,
                )
            nodes.append(
                MessageNode(
                    node_id=nid,
                    parent_id=prev_id,
                    child_ids=(),
                    role=role,
                    text=text,
                    timestamp=ts,
                    content=content,
                    raw_record=entry,
                    event_type=event_type,
                    parent_tool_use_id=str(parent_tu) if parent_tu else None,
                    links=node_links,
                    usage=usage,
                    is_sidechain=bool(parent_tu),
                )
            )
            prev_id = nid
        elif etype == "result":
            subtype = str(entry.get("subtype") or "")
            if entry.get("total_cost_usd") is not None:
                total_cost += float(entry.get("total_cost_usd") or 0.0)
                has_cost = True
            usage = entry.get("usage") if isinstance(entry.get("usage"), dict) else None
            if usage and not total_in and not total_out:
                total_in += int(usage.get("input_tokens") or 0)
                total_out += int(usage.get("output_tokens") or 0)
            interrupted = subtype not in {"", "success"}
            if interrupted:
                interruption_count += 1
            nid = f"result-{idx}"
            if nodes:
                prev = nodes[-1]
                nodes[-1] = MessageNode(
                    prev.node_id, prev.parent_id, (nid,), prev.role, prev.text, prev.timestamp,
                    prev.content, prev.raw_record, event_type=prev.event_type,
                    parent_tool_use_id=prev.parent_tool_use_id, attachments=prev.attachments,
                    links=prev.links, usage=prev.usage, interrupted=prev.interrupted,
                    is_sidechain=prev.is_sidechain,
                )
            nodes.append(
                MessageNode(
                    node_id=nid,
                    parent_id=prev_id,
                    child_ids=(),
                    role="system",
                    text=f"result:{subtype or 'success'}",
                    timestamp=ts,
                    content=entry,
                    raw_record=entry,
                    event_type="interruption" if interrupted else "result",
                    usage=usage,
                    interrupted=interrupted,
                )
            )
            prev_id = nid

    todos_dir = sdir / ".claude" / "todos"
    todo_files = sorted(p.name for p in todos_dir.glob("*.json")) if todos_dir.is_dir() else []
    uploads = sorted(p.name for p in (sdir / "uploads").rglob("*") if p.is_file()) if (sdir / "uploads").is_dir() else []
    outputs = sorted(p.name for p in (sdir / "outputs").rglob("*") if p.is_file()) if (sdir / "outputs").is_dir() else []

    folders = sidecar.get("userSelectedFolders") if isinstance(sidecar.get("userSelectedFolders"), list) else []
    workspace = folders[0] if folders else (sidecar.get("cwd") if isinstance(sidecar.get("cwd"), str) else None)
    usage_summary = (
        UsageSummary(
            input_tokens=total_in,
            output_tokens=total_out,
            total_cost_usd=round(total_cost, 6) if has_cost else None,
        )
        if (total_in or total_out or has_cost)
        else None
    )

    return ConversationGraph(
        source_format=lane.replace("-", "_"),
        source_id=session_id,
        title=str(sidecar.get("title") or "Untitled"),
        workspace=workspace,
        nodes=tuple(nodes),
        root_ids=(nodes[0].node_id,) if nodes else (),
        active_node_id=nodes[-1].node_id if nodes else None,
        metadata={
            "desktop_lane": lane,
            "model": sidecar.get("model"),
            "is_archived": bool(sidecar.get("isArchived", False)),
            "process_name": sidecar.get("processName"),
            "user_selected_folders": folders,
            "project_id": sidecar.get("projectId") or sidecar.get("project_id"),
            "project_name": sidecar.get("projectName") or sidecar.get("project_name"),
            "transcript_source": transcript_source,
            "audit_hmac_line_count": hmac_present_count,
            "subagent_turn_count": subagent_turn_count,
            "interruption_count": interruption_count,
            "todo_files": todo_files,
            "upload_files": uploads,
            "output_files": outputs,
            "device_scope": sdir.parent.parent.name if sdir.parent.parent != sdir.parent else None,
            "org_scope": sdir.parent.name,
            "source_file": sdir.name,
        },
        raw_source={"sidecar": sidecar, "records": records},
        usage=usage_summary,
        links=tuple(all_links),
        app_mode=lane,
    )


def parse_claude_desktop_3p_root(
    app_root: str | Path,
    *,
    claude_dir: str | Path | None = None,
    lanes: tuple[str, ...] = ("chat", "cowork", "code"),
) -> dict[str, list[ConversationGraph]]:
    """Read all three Claude Desktop 3P lanes separately (never conflated)."""
    root = Path(app_root).expanduser()
    out: dict[str, list[ConversationGraph]] = {"chat": [], "cowork": [], "code": []}

    lam_root = root / "local-agent-mode-sessions"
    if lam_root.is_dir() and ("chat" in lanes or "cowork" in lanes):
        seen_dirs: set[Path] = set()
        for sidecar in sorted(lam_root.rglob("local_*.json")):
            if not sidecar.is_file():
                continue
            sdir = sidecar.with_suffix("")
            if sdir in seen_dirs:
                continue
            seen_dirs.add(sdir)
            try:
                g = parse_local_agent_session(sdir)
            except (OSError, ValueError):
                continue
            if g.app_mode == "claude-desktop-3p-chat" and "chat" in lanes:
                out["chat"].append(g)
            elif g.app_mode == "claude-desktop-3p-cowork" and "cowork" in lanes:
                out["cowork"].append(g)

    ccs_root = root / "claude-code-sessions"
    cc_projects = (Path(claude_dir).expanduser() / "projects") if claude_dir else None
    if ccs_root.is_dir() and "code" in lanes:
        for idx_file in sorted(ccs_root.rglob("local_*.json")):
            if not idx_file.is_file():
                continue
            try:
                raw_meta = json.loads(idx_file.read_text(encoding="utf-8-sig"))
                if not isinstance(raw_meta, dict):
                    continue
            except (json.JSONDecodeError, OSError):
                continue
            meta = _sanitize_sidecar(raw_meta)
            cli_sid = str(meta.get("cliSessionId") or meta.get("sessionId") or idx_file.stem).removeprefix("local_")
            cwd = meta.get("cwd") or meta.get("originCwd") or meta.get("projectPath")
            matched_transcript: Path | None = None
            transcript_verified = False
            if cc_projects and cc_projects.is_dir() and isinstance(cwd, str) and cwd:
                expected_dir = cc_projects / project_directory_name(cwd)
                candidate = expected_dir / f"{cli_sid}.jsonl"
                if candidate.is_file():
                    matched_transcript = candidate
                    transcript_verified = True
            if matched_transcript is not None:
                g = parse_claude_code_session(matched_transcript)
                g_meta = dict(g.metadata)
                g_meta.update(
                    {
                        "desktop_lane": "claude-desktop-3p-code",
                        "desktop_code_index_file": idx_file.name,
                        "desktop_code_sidecar": meta,
                        "transcript_project_verified": transcript_verified,
                        "device_scope": idx_file.parent.parent.name,
                        "org_scope": idx_file.parent.name,
                    }
                )
                out["code"].append(
                    ConversationGraph(
                        source_format="claude_desktop_3p_code",
                        source_id=cli_sid,
                        title=str(meta.get("title") or g.title or cli_sid),
                        workspace=str(cwd),
                        nodes=g.nodes,
                        root_ids=g.root_ids,
                        active_node_id=g.active_node_id,
                        metadata=g_meta,
                        raw_source={"code_index": meta, "transcript": g.raw_source},
                        usage=g.usage,
                        links=g.links,
                        app_mode="claude-desktop-3p-code",
                    )
                )
            else:
                out["code"].append(
                    ConversationGraph(
                        source_format="claude_desktop_3p_code",
                        source_id=cli_sid,
                        title=str(meta.get("title") or cli_sid),
                        workspace=str(cwd) if isinstance(cwd, str) else None,
                        nodes=(),
                        root_ids=(),
                        active_node_id=None,
                        metadata={
                            "desktop_lane": "claude-desktop-3p-code",
                            "desktop_code_index_file": idx_file.name,
                            "desktop_code_sidecar": meta,
                            "transcript_project_verified": False,
                            "device_scope": idx_file.parent.parent.name,
                            "org_scope": idx_file.parent.name,
                        },
                        raw_source={"code_index": meta},
                        app_mode="claude-desktop-3p-code",
                    )
                )
    return out


def build_desktop_3p_local_agent_sessions(
    graph: ConversationGraph,
    *,
    lane: str,
    cwd: str | Path,
    device_id: str = DEFAULT_3P_DEVICE_ID,
    org_id: str = DEFAULT_3P_ORG_ID,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage Claude Desktop 3P Chat OR Cowork `local-agent-mode-sessions` aligned to Claude 7.37095.0."""
    if lane not in {"claude-desktop-3p-chat", "claude-desktop-3p-cowork"}:
        raise ValueError(f"unsupported local-agent lane: {lane}")

    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = graph.branch_paths()
    if not paths:
        losses.append({"feature": "empty_conversation", "disposition": "skipped_zero_node_conversation"})
        return sessions, losses

    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_ms = int(time.time() * 1000)
    now_iso = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    mode_tag = "chat" if lane == "claude-desktop-3p-chat" else "cowork"
    safe_dev = sanitize_single_segment(device_id, fallback=DEFAULT_3P_DEVICE_ID)
    safe_org = sanitize_single_segment(org_id, fallback=DEFAULT_3P_ORG_ID)

    for branch_index, path in enumerate(paths, 1):
        turns, merged_count, _ = _coalesce_alternating_turns(path)
        sid = str(uuid.uuid4())
        cli_sid = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"

        audit_records: list[dict[str, Any]] = [
            {
                "type": "system",
                "subtype": "init",
                "session_id": f"local_{sid}",
                "_audit_timestamp": now_iso,
                "cwd": resolved_cwd,
                "nexus_provenance": {
                    "source_format": graph.source_format,
                    "source_id": graph.source_id,
                    "lane": lane,
                },
            }
        ]
        source_node_ids: list[str] = []
        initial_msg = ""
        for turn in turns:
            ts = turn["timestamp"] if isinstance(turn["timestamp"], str) and turn["timestamp"] else now_iso
            joined = "\n\n".join(turn["texts"])
            if not initial_msg and turn["role"] == "user":
                initial_msg = joined[:240]
            content_payload: Any = joined if turn["role"] == "user" else [{"type": "text", "text": joined}]
            rec: dict[str, Any] = {
                "type": turn["role"],
                "session_id": f"local_{sid}",
                "uuid": str(uuid.uuid4()),
                "_audit_timestamp": ts,
                "message": {"role": turn["role"], "content": content_payload},
            }
            if turn["usage"]:
                rec["message"]["usage"] = turn["usage"]
            audit_records.append(rec)
            source_node_ids.extend(turn["source_node_ids"])

        if graph.usage and not graph.usage.is_empty():
            audit_records.append(
                {
                    "type": "result",
                    "subtype": "success",
                    "session_id": f"local_{sid}",
                    "_audit_timestamp": now_iso,
                    "num_turns": len(turns),
                    "total_cost_usd": graph.usage.total_cost_usd or 0.0,
                    "usage": {
                        "input_tokens": graph.usage.input_tokens,
                        "output_tokens": graph.usage.output_tokens,
                    },
                }
            )

        # Aligned with observed Claude Desktop 7.37095.0 `Claude-3p/local-agent-mode-sessions` sidecar fields
        sidecar: dict[str, Any] = {
            "sessionId": f"local_{sid}",
            "cliSessionId": cli_sid,
            "sessionMode": mode_tag,
            "title": title,
            "initialMessage": initial_msg,
            "model": str(graph.metadata.get("model") or "unknown"),
            "createdAt": now_ms,
            "lastActivityAt": now_ms,
            "isArchived": bool(graph.metadata.get("is_archived", False)),
            "cwd": resolved_cwd,
            "userSelectedFolders": [resolved_cwd] if mode_tag == "cowork" else [],
            "memoryEnabled": True,
            "skillsEnabled": True,
            "pluginsEnabled": False,
            "nexusProvenance": {
                "source_format": graph.source_format,
                "source_id": graph.source_id,
                "project_name": graph.metadata.get("project_name"),
                "section_name": graph.metadata.get("section_name"),
                "lane": lane,
                "merged_consecutive_turns": merged_count,
            },
        }

        rel_prefix = Path("claude_desktop_3p") / "local-agent-mode-sessions" / safe_dev / safe_org
        sessions.append(
            {
                "session_id": sid,
                "lane": lane,
                "branch_index": branch_index,
                "title": title,
                "cwd": resolved_cwd,
                "source_node_ids": source_node_ids,
                "sidecar_relative_path": (rel_prefix / f"local_{sid}.json").as_posix(),
                "audit_relative_path": (rel_prefix / f"local_{sid}" / "audit.jsonl").as_posix(),
                "target_relative_path": (rel_prefix / f"local_{sid}" / "audit.jsonl").as_posix(),
                "sidecar": sidecar,
                "records": audit_records,
            }
        )

    if len(paths) > 1:
        losses.append(
            {
                "feature": "branch_topology",
                "disposition": f"one_{mode_tag}_session_per_leaf_path; exact graph retained in portable.json",
            }
        )
    losses.append(
        {
            "feature": "desktop_3p_hmac_and_runtime_acceptance",
            "disposition": "staged_without_private_hmac_key; validate inside Claude Desktop 3P UI",
        }
    )
    if graph.metadata.get("section_name"):
        losses.append(
            {
                "feature": "sidebar_section_group",
                "disposition": "preserved_in_portable_hierarchy_and_sidecar_provenance; no public 3P section-import API",
            }
        )
    return sessions, losses


def build_desktop_3p_code_sessions(
    graph: ConversationGraph,
    *,
    cwd: str | Path,
    device_id: str = DEFAULT_3P_DEVICE_ID,
    org_id: str = DEFAULT_3P_ORG_ID,
    claude_version: str = TESTED_CLAUDE_CODE_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage Claude Desktop 3P Code lane aligned to Claude 7.37095.0 `claude-code-sessions` + `~/.claude/projects`."""
    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    project_key = project_directory_name(resolved_cwd)
    cc_sessions, losses = build_native_sessions(graph, cwd=resolved_cwd, version=claude_version)
    now_ms = int(time.time() * 1000)
    safe_dev = sanitize_single_segment(device_id, fallback=DEFAULT_3P_DEVICE_ID)
    safe_org = sanitize_single_segment(org_id, fallback=DEFAULT_3P_ORG_ID)

    staged: list[dict[str, Any]] = []
    for item in cc_sessions:
        sid = item["session_id"]
        transcript_rel = (Path("claude_sessions") / project_key / f"{sid}.jsonl").as_posix()
        index_rel = (Path("claude_desktop_3p") / "claude-code-sessions" / safe_dev / safe_org / f"local_{sid}.json").as_posix()
        # Aligned with observed real Claude 7.37095.0 `claude-code-sessions/local_<uuid>.json` fields
        index_payload = {
            "sessionId": f"local_{sid}",
            "cliSessionId": sid,
            "sessionMode": "code",
            "title": item["title"],
            "titleSource": "nexus-memory",
            "cwd": resolved_cwd,
            "originCwd": resolved_cwd,
            "encodedProjectDir": project_key,
            "model": str(graph.metadata.get("model") or "unknown"),
            "permissionMode": "default",
            "completedTurns": max(1, len(item["records"]) // 2),
            "createdAt": now_ms,
            "lastActivityAt": now_ms,
            "indexedAt": now_ms,
            "isArchived": bool(graph.metadata.get("is_archived", False)),
            "importedFrom": f"nexus-memory:{graph.source_format}",
            "nexusProvenance": {
                "source_format": graph.source_format,
                "source_id": graph.source_id,
                "project_name": graph.metadata.get("project_name"),
                "section_name": graph.metadata.get("section_name"),
                "lane": "claude-desktop-3p-code",
            },
        }
        staged.append(
            {
                **item,
                "lane": "claude-desktop-3p-code",
                "encoded_project_dir": project_key,
                "target_relative_path": transcript_rel,
                "index_relative_path": index_rel,
                "index_payload": index_payload,
            }
        )

    losses.append(
        {
            "feature": "desktop_3p_code_index_join",
            "disposition": "dual_key_staged_with_encoded_project_dir_and_cliSessionId; verified against real claude 2.1.172 resume",
        }
    )
    return staged, losses


def verify_desktop_3p_code_join(
    index_json_path: str | Path,
    claude_projects_dir: str | Path,
) -> dict[str, Any]:
    """Strictly verify a Claude Desktop 3P Code index points to the RIGHT encoded project dir + session ID."""
    idx_p = Path(index_json_path).expanduser()
    cc_root = Path(claude_projects_dir).expanduser()
    meta = json.loads(idx_p.read_text(encoding="utf-8-sig"))
    cli_sid = str(meta.get("cliSessionId") or meta.get("sessionId") or "").removeprefix("local_")
    cwd = meta.get("cwd") or meta.get("originCwd") or meta.get("projectPath")
    if not cli_sid or not isinstance(cwd, str) or not cwd:
        return {"ok": False, "reason": "missing_cliSessionId_or_cwd", "cli_session_id": cli_sid, "cwd": cwd}

    expected_key = project_directory_name(cwd)
    expected_path = cc_root / expected_key / f"{cli_sid}.jsonl"
    if expected_path.is_file():
        return {
            "ok": True,
            "cli_session_id": cli_sid,
            "expected_project_key": expected_key,
            "transcript_path": str(expected_path),
        }

    wrong_matches = [str(p) for p in cc_root.rglob(f"{cli_sid}.jsonl") if p.is_file()]
    return {
        "ok": False,
        "reason": "transcript_in_wrong_project_directory" if wrong_matches else "transcript_missing",
        "cli_session_id": cli_sid,
        "expected_project_key": expected_key,
        "expected_transcript_path": str(expected_path),
        "misplaced_matches": wrong_matches,
    }


__all__ = [
    "DEFAULT_3P_DEVICE_ID",
    "DEFAULT_3P_ORG_ID",
    "default_claude_desktop_root",
    "parse_local_agent_session",
    "parse_claude_desktop_3p_root",
    "build_desktop_3p_local_agent_sessions",
    "build_desktop_3p_code_sessions",
    "verify_desktop_3p_code_join",
    "encode_jsonl",
]
