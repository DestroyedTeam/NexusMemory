"""Reader & Writer for local/self-hosted Claude Code CLI sessions (`~/.claude/projects/`).

Hardened against real Anthropic Messages API & third-party gateway `Invalid Params` errors:
- Strictly merges consecutive same-role messages (`user`+`user`, `assistant`+`assistant`) so
  the projected conversation ALWAYS strictly alternates `user -> assistant -> user -> assistant`.
- Guarantees first turn is `user` (prepends a concise provenance user turn if a source branch
  starts with an `assistant` turn).
- Excludes non-chat `developer` instructions, empty messages, unsigned `thinking` blocks, and
  unpaired `tool_use`/`tool_result` from native transcripts (always preserved in `portable.json`).
- 100% backwards-compatible with v0.1 prototype tests and `verify_workspace_routing.py`.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .model import ConversationGraph, MessageNode, UsageSummary, content_text, extract_links

TESTED_CLAUDE_CODE_VERSION = "2.1.172"


def project_directory_name(cwd: str | Path) -> str:
    """Return the observed Claude Code project-folder key for an absolute path."""
    resolved = str(Path(cwd).expanduser().resolve())
    return re.sub(r"[^A-Za-z0-9]", "-", resolved) or "-"


def writeable_leaf_paths(graph: ConversationGraph) -> list[list[MessageNode]]:
    """Return non-empty user/assistant transcript paths for native projection."""
    return [
        [node for node in path if node.role in {"user", "assistant"} and node.text.strip()]
        for path in graph.branch_paths()
    ]


def has_non_text_content(value: Any) -> bool:
    """Detect content that the text-only native projection cannot carry."""
    if isinstance(value, list):
        return any(has_non_text_content(item) for item in value)
    if isinstance(value, dict):
        if any(key in value for key in ("image", "image_url", "asset_pointer", "file_id", "attachment", "audio", "video")):
            return True
        block_type = value.get("type")
        if isinstance(block_type, str) and block_type not in {"text", "input_text", "output_text"}:
            return True
        return any(has_non_text_content(item) for key, item in value.items() if key != "text")
    return False


def _coalesce_alternating_turns(source_path: list[MessageNode]) -> tuple[list[dict[str, Any]], int, bool]:
    """Merge consecutive same-role turns and ensure first turn is `user` to prevent 400 Invalid Params.

    Returns `(turns, merged_count, prepended_user_opener)`.
    """
    turns: list[dict[str, Any]] = []
    merged_count = 0
    for node in source_path:
        text = node.text.strip()
        if not text or node.role not in {"user", "assistant"}:
            continue
        if turns and turns[-1]["role"] == node.role:
            turns[-1]["texts"].append(text)
            turns[-1]["source_node_ids"].append(node.node_id)
            if node.usage:
                prev_u = turns[-1]["usage"] or {}
                turns[-1]["usage"] = {
                    "input_tokens": int(prev_u.get("input_tokens") or 0) + int(node.usage.get("input_tokens") or 0),
                    "output_tokens": int(prev_u.get("output_tokens") or 0) + int(node.usage.get("output_tokens") or 0),
                    "cache_read_input_tokens": int(prev_u.get("cache_read_input_tokens") or 0) + int(node.usage.get("cache_read_input_tokens") or 0),
                    "cache_creation_input_tokens": int(prev_u.get("cache_creation_input_tokens") or 0) + int(node.usage.get("cache_creation_input_tokens") or 0),
                }
            merged_count += 1
        else:
            turns.append(
                {
                    "role": node.role,
                    "texts": [text],
                    "timestamp": node.timestamp,
                    "usage": dict(node.usage) if isinstance(node.usage, dict) else None,
                    "is_sidechain": bool(node.is_sidechain),
                    "source_node_ids": [node.node_id],
                }
            )

    prepended_opener = False
    if turns and turns[0]["role"] == "assistant":
        turns.insert(
            0,
            {
                "role": "user",
                "texts": ["[Nexus Memory migrated context opener]"],
                "timestamp": turns[0]["timestamp"],
                "usage": None,
                "is_sidechain": False,
                "source_node_ids": [],
            },
        )
        prepended_opener = True
    return turns, merged_count, prepended_opener


def parse_claude_code_session(path: str | Path) -> ConversationGraph:
    """Read a local Claude Code CLI `.jsonl` session file into a ConversationGraph."""
    source_path = Path(path).expanduser()
    records: list[dict[str, Any]] = []
    for line_num, line in enumerate(source_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid Claude Code JSONL at line {line_num}: {exc.msg}") from exc
        if isinstance(rec, dict):
            records.append(rec)

    session_id = source_path.stem
    title: str | None = None
    workspace: str | None = None
    version: str | None = None
    git_branch: str | None = None
    model_name: str | None = None
    compaction_count = 0
    total_in = 0
    total_out = 0
    total_cache_read = 0
    total_cache_create = 0
    all_links: list[str] = []
    seen_links: set[str] = set()

    raw_nodes: list[dict[str, Any]] = []
    seen_uuids: set[str] = set()

    for idx, rec in enumerate(records):
        rtype = rec.get("type")
        if isinstance(rec.get("sessionId"), str) and rec["sessionId"]:
            session_id = rec["sessionId"]
        if not workspace and isinstance(rec.get("cwd"), str) and rec["cwd"]:
            workspace = rec["cwd"]
        if not version and isinstance(rec.get("version"), str) and rec["version"]:
            version = rec["version"]
        if not git_branch and isinstance(rec.get("gitBranch"), str) and rec["gitBranch"]:
            git_branch = rec["gitBranch"]

        if rtype == "custom-title":
            if isinstance(rec.get("customTitle"), str) and rec["customTitle"]:
                title = rec["customTitle"]
            continue
        if rtype == "summary":
            compaction_count += 1
            if not title and isinstance(rec.get("summary"), str) and rec["summary"]:
                title = rec["summary"]
            raw_nodes.append(
                {
                    "node_id": f"summary-{idx}",
                    "parent_id": raw_nodes[-1]["node_id"] if raw_nodes else None,
                    "role": "system",
                    "text": str(rec.get("summary") or ""),
                    "timestamp": rec.get("timestamp"),
                    "content": rec.get("summary"),
                    "raw_record": rec,
                    "event_type": "compaction",
                    "usage": None,
                    "is_sidechain": False,
                }
            )
            continue
        if rtype not in {"user", "assistant", "system"}:
            continue

        msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
        role = str(msg.get("role") or rtype)
        content = msg.get("content")
        if not model_name and isinstance(msg.get("model"), str) and msg["model"]:
            model_name = msg["model"]
        usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else None
        if usage:
            total_in += int(usage.get("input_tokens") or 0)
            total_out += int(usage.get("output_tokens") or 0)
            total_cache_read += int(usage.get("cache_read_input_tokens") or 0)
            total_cache_create += int(usage.get("cache_creation_input_tokens") or 0)

        nid = str(rec.get("uuid") or f"cc-{idx}")
        if nid in seen_uuids:
            nid = f"{nid}-dup-{idx}"
        seen_uuids.add(nid)

        parent_id = rec.get("parentUuid")
        parent_id = str(parent_id) if isinstance(parent_id, str) and parent_id else None
        if parent_id and parent_id not in seen_uuids:
            parent_id = raw_nodes[-1]["node_id"] if raw_nodes else None

        # Extract tool_use / tool_result cleanly when blocks are present
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

        raw_nodes.append(
            {
                "node_id": nid,
                "parent_id": parent_id,
                "role": role,
                "text": text,
                "timestamp": rec.get("timestamp"),
                "content": content,
                "raw_record": rec,
                "event_type": event_type,
                "usage": usage,
                "links": node_links,
                "is_sidechain": bool(rec.get("isSidechain", False)),
            }
        )

    child_map: dict[str, list[str]] = {n["node_id"]: [] for n in raw_nodes}
    for n in raw_nodes:
        pid = n["parent_id"]
        if pid in child_map and n["node_id"] not in child_map[pid]:
            child_map[pid].append(n["node_id"])
    nodes = tuple(
        MessageNode(
            node_id=n["node_id"],
            parent_id=n["parent_id"],
            child_ids=tuple(child_map[n["node_id"]]),
            role=n["role"],
            text=n["text"],
            timestamp=n["timestamp"],
            content=n["content"],
            raw_record=n["raw_record"],
            event_type=n["event_type"],
            links=n.get("links", ()),
            usage=n["usage"],
            is_sidechain=n["is_sidechain"],
        )
        for n in raw_nodes
    )
    root_ids = tuple(n.node_id for n in nodes if n.parent_id is None or n.parent_id not in child_map)
    usage_summary = (
        UsageSummary(
            input_tokens=total_in,
            output_tokens=total_out,
            cache_read_tokens=total_cache_read,
            cache_creation_tokens=total_cache_create,
        )
        if (total_in or total_out or total_cache_read or total_cache_create)
        else None
    )
    return ConversationGraph(
        source_format="claude_code_jsonl",
        source_id=session_id,
        title=title or (nodes[0].text[:80].strip() if nodes and nodes[0].text.strip() else session_id),
        workspace=workspace,
        nodes=nodes,
        root_ids=root_ids,
        active_node_id=nodes[-1].node_id if nodes else None,
        metadata={
            "claude_code_version": version,
            "git_branch": git_branch,
            "model": model_name,
            "encoded_project_dir": source_path.parent.name,
            "compaction_count": compaction_count,
            "record_count": len(records),
            "source_file": source_path.name,
        },
        raw_source={"records": records},
        usage=usage_summary,
        links=tuple(all_links),
        app_mode="cli",
    )


def parse_claude_code_dir(claude_dir: str | Path) -> list[ConversationGraph]:
    """Read all Claude Code CLI sessions under `<claude_dir>/projects/*/*.jsonl`."""
    root = Path(claude_dir).expanduser()
    projects_dir = root / "projects" if (root / "projects").is_dir() else root
    graphs: list[ConversationGraph] = []
    if not projects_dir.is_dir():
        return graphs
    for fp in sorted(projects_dir.rglob("*.jsonl")):
        if not fp.is_file():
            continue
        try:
            graphs.append(parse_claude_code_session(fp))
        except (OSError, ValueError):
            continue
    return graphs


def build_native_sessions(
    graph: ConversationGraph,
    *,
    cwd: str | Path,
    version: str = TESTED_CLAUDE_CODE_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build strictly alternating, gateway-safe Claude Code CLI transcripts (one per source leaf)."""
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    paths = writeable_leaf_paths(graph)
    raw_paths = graph.branch_paths()
    if len(paths) != len(raw_paths):
        raise AssertionError("branch projection unexpectedly changed path count")
    if not paths:
        losses.append({"feature": "empty_conversation", "disposition": "no_writeable_user_assistant_turns"})
        return sessions, losses

    timestamp_fallback = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    resolved_cwd = str(Path(cwd).expanduser().resolve())
    model_name = str(graph.metadata.get("model") or "unknown")
    total_merged = 0

    for branch_index, source_path in enumerate(paths, 1):
        turns, merged_count, prepended_opener = _coalesce_alternating_turns(source_path)
        total_merged += merged_count
        session_id = str(uuid.uuid4())
        records: list[dict[str, Any]] = []
        parent_uuid: str | None = None
        flat_source_ids: list[str] = []

        for turn in turns:
            record_uuid = str(uuid.uuid4())
            timestamp = _timestamp(turn["timestamp"]) or timestamp_fallback
            joined_text = "\n\n".join(turn["texts"])
            flat_source_ids.extend(turn["source_node_ids"])
            common: dict[str, Any] = {
                "parentUuid": parent_uuid,
                "isSidechain": bool(turn["is_sidechain"]),
                "userType": "external",
                "cwd": resolved_cwd,
                "sessionId": session_id,
                "version": version,
                "gitBranch": str(graph.metadata.get("git_branch") or ""),
                "uuid": record_uuid,
                "timestamp": timestamp,
            }
            if turn["role"] == "user":
                common.update({"type": "user", "message": {"role": "user", "content": joined_text}})
            else:
                node_usage = turn["usage"] or {}
                common.update(
                    {
                        "type": "assistant",
                        "message": {
                            "id": f"msg_nexus_{uuid.uuid4().hex}",
                            "type": "message",
                            "role": "assistant",
                            "model": model_name,
                            "content": [{"type": "text", "text": joined_text}],
                            "stop_reason": "end_turn",
                            "stop_sequence": None,
                            "usage": {
                                "input_tokens": int(node_usage.get("input_tokens") or 0),
                                "cache_creation_input_tokens": int(node_usage.get("cache_creation_input_tokens") or 0),
                                "cache_read_input_tokens": int(node_usage.get("cache_read_input_tokens") or 0),
                                "output_tokens": int(node_usage.get("output_tokens") or 0),
                            },
                        },
                    }
                )
            records.append(common)
            parent_uuid = record_uuid

        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(paths) > 1:
            title = f"{title} [branch {branch_index}]"
        records.append({"type": "custom-title", "customTitle": title, "sessionId": session_id})
        sessions.append(
            {
                "session_id": session_id,
                "branch_index": branch_index,
                "title": title,
                "cwd": resolved_cwd,
                "source_node_ids": flat_source_ids,
                "merged_consecutive_turns": merged_count,
                "prepended_user_opener": prepended_opener,
                "records": records,
            }
        )

    if total_merged:
        losses.append(
            {
                "feature": "consecutive_same_role_coalescing",
                "disposition": f"merged {total_merged} consecutive same-role turn(s) for strict user/assistant API alternation; exact per-turn splits kept in portable.json",
            }
        )
    for node in graph.nodes:
        if node.role not in {"user", "assistant"}:
            losses.append(
                {
                    "source_node_id": node.node_id,
                    "feature": node.role or "non_message_record",
                    "disposition": "preserved_in_portable_sidecar_not_written_to_native_transcript",
                }
            )
        if has_non_text_content(node.content):
            losses.append(
                {
                    "source_node_id": node.node_id,
                    "feature": "typed_content_blocks_or_attachments",
                    "disposition": "original_preserved_in_portable_sidecar_text_only_in_native_transcript",
                }
            )
    if len(paths) > 1:
        losses.append(
            {
                "feature": "branch_topology",
                "disposition": "one_native_session_per_leaf_path; exact graph retained in portable.json",
            }
        )
    return sessions, losses


def encode_jsonl(records: list[dict[str, Any]]) -> bytes:
    return ("".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records)).encode("utf-8")


def _timestamp(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(float(value), UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        except (OverflowError, OSError, ValueError):
            return None
    return None
