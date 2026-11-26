"""Reader for ChatGPT JSON/ZIP exports (offline; no account API or browser access).

Preserves:
- Full `mapping` DAG (parent/child edges, fork/regeneration points, `current_node`)
- Explicit Projects & Section Groups (both per-conversation fields and optional
  `projects.json` / `sections.json` sidecar files inside a ZIP export)
- User follow-ups, interruptions / stopped generations (`finish_details`, `status`)
- Tool messages, citations/links, model slug, and token usage when present
- Attachment/image binary extraction from ZIP exports with SHA-256 content addressing
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import zipfile
from pathlib import Path
from typing import Any

from .model import AssetRecord, ConversationGraph, MessageNode, UsageSummary, content_text, extract_links
from .security import sanitize_single_segment

MAX_EXPORT_MEMBER_BYTES = 256 * 1024 * 1024
MAX_SINGLE_ASSET_BYTES = 64 * 1024 * 1024


def _read_zip_payload(path: Path) -> tuple[Any, dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, tuple[str, bytes]]]:
    """Read conversations.json, optional projects/sections metadata, and binary assets from ZIP."""
    projects_by_id: dict[str, dict[str, Any]] = {}
    sections_by_conv: dict[str, dict[str, Any]] = {}
    zip_assets: dict[str, tuple[str, bytes]] = {}  # lowercase basename / stem key -> (orig_name, bytes)

    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        conv_candidates = sorted(
            (info for info in infos if not info.is_dir() and Path(info.filename).name.lower() == "conversations.json"),
            key=lambda i: i.filename,
        )
        if not conv_candidates:
            raise ValueError("ZIP export has no conversations.json")
        conv_info = conv_candidates[0]
        if conv_info.file_size > MAX_EXPORT_MEMBER_BYTES:
            raise ValueError("conversations.json exceeds the 256 MiB safety limit")
        with archive.open(conv_info) as member:
            raw = member.read(MAX_EXPORT_MEMBER_BYTES + 1)
        if len(raw) > MAX_EXPORT_MEMBER_BYTES:
            raise ValueError("conversations.json exceeds the 256 MiB safety limit")
        payload = json.loads(raw.decode("utf-8-sig"))

        for info in infos:
            if info.is_dir():
                continue
            name_lower = Path(info.filename).name.lower()
            if name_lower == "projects.json" and info.file_size <= 32 * 1024 * 1024:
                try:
                    proj_data = json.loads(archive.read(info).decode("utf-8-sig"))
                    items = proj_data if isinstance(proj_data, list) else proj_data.get("projects", [])
                    for item in items:
                        if isinstance(item, dict):
                            pid = _first_string(item.get("id"), item.get("project_id"), item.get("gizmo_id"))
                            if pid:
                                projects_by_id[pid] = item
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            elif name_lower in {"sections.json", "section_groups.json"} and info.file_size <= 32 * 1024 * 1024:
                try:
                    sec_data = json.loads(archive.read(info).decode("utf-8-sig"))
                    items = sec_data if isinstance(sec_data, list) else sec_data.get("sections", [])
                    for sec in items:
                        if not isinstance(sec, dict):
                            continue
                        sid = _first_string(sec.get("id"), sec.get("section_id"))
                        sname = _first_string(sec.get("name"), sec.get("title"))
                        for cid in sec.get("conversation_ids", sec.get("session_ids", [])):
                            if isinstance(cid, str):
                                sections_by_conv[cid] = {"section_id": sid, "section_name": sname}
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            elif name_lower not in {"conversations.json", "user.json", "chat.html", "message_feedback.json", "model_comparisons.json", "shared_conversations.json"}:
                if info.file_size <= MAX_SINGLE_ASSET_BYTES:
                    data = archive.read(info)
                    base = Path(info.filename).name
                    zip_assets[base.lower()] = (base, data)
                    stem = Path(base).stem.lower()
                    zip_assets.setdefault(stem, (base, data))
                    # Also index by leading file-XXXX prefix (ChatGPT names files like `file-abc123-photo.png`)
                    for token in base.split("-"):
                        if token.lower().startswith("file_") and len(token) >= 8:
                            zip_assets.setdefault(token.lower(), (base, data))
                    if base.lower().startswith("file-") and len(base) > 10:
                        prefix = "-".join(base.split("-")[:2]).lower()
                        zip_assets.setdefault(prefix, (base, data))

    return payload, projects_by_id, sections_by_conv, zip_assets


def _read_json(path: Path) -> Any:
    if zipfile.is_zipfile(path):
        payload, _, _, _ = _read_zip_payload(path)
        return payload
    if path.stat().st_size > MAX_EXPORT_MEMBER_BYTES:
        raise ValueError("JSON export exceeds the 256 MiB safety limit")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_export(path: str | Path) -> list[ConversationGraph]:
    """Read ChatGPT JSON or ZIP export into canonical ConversationGraphs."""
    graphs, _ = parse_export_with_assets(path)
    return graphs


def parse_export_with_assets(path: str | Path) -> tuple[list[ConversationGraph], dict[str, bytes]]:
    """Read ChatGPT JSON or ZIP export and return `(graphs, sha256_to_asset_bytes)`."""
    source_path = Path(path).expanduser()
    projects_by_id: dict[str, dict[str, Any]] = {}
    sections_by_conv: dict[str, dict[str, Any]] = {}
    zip_assets: dict[str, tuple[str, bytes]] = {}

    if zipfile.is_zipfile(source_path):
        payload, projects_by_id, sections_by_conv, zip_assets = _read_zip_payload(source_path)
    else:
        payload = _read_json(source_path)

    if isinstance(payload, dict) and isinstance(payload.get("conversations"), list):
        for proj in payload.get("projects", []):
            if isinstance(proj, dict):
                pid = _first_string(proj.get("id"), proj.get("project_id"), proj.get("gizmo_id"))
                if pid:
                    projects_by_id[pid] = proj
        for sec in payload.get("sections", []):
            if isinstance(sec, dict):
                sid = _first_string(sec.get("id"), sec.get("section_id"))
                sname = _first_string(sec.get("name"), sec.get("title"))
                for cid in sec.get("conversation_ids", sec.get("session_ids", [])):
                    if isinstance(cid, str):
                        sections_by_conv[cid] = {"section_id": sid, "section_name": sname}
        payload = payload["conversations"]

    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("ChatGPT export must contain a conversation object or list")

    asset_bytes: dict[str, bytes] = {}
    graphs = [
        _parse_conversation(item, index, source_path, projects_by_id, sections_by_conv, zip_assets, asset_bytes)
        for index, item in enumerate(payload)
        if isinstance(item, dict)
    ]
    return graphs, asset_bytes


def filter_conversations(
    conversations: list[ConversationGraph],
    *,
    project: str | None = None,
    section: str | None = None,
    query: str | None = None,
    session_id: str | None = None,
) -> list[ConversationGraph]:
    """Deterministically filter conversations by project (e.g. 'Destruction Era'), section, query, or ID."""
    out = list(conversations)
    if project:
        needle = project.casefold()
        out = [
            g for g in out
            if needle in str(g.metadata.get("project_name") or "").casefold()
            or needle in str(g.metadata.get("project_id") or "").casefold()
            or needle in str(g.workspace or "").casefold()
        ]
    if section:
        needle = section.casefold()
        out = [
            g for g in out
            if needle in str(g.metadata.get("section_name") or "").casefold()
            or needle in str(g.metadata.get("section_id") or "").casefold()
        ]
    if session_id:
        needle = session_id.casefold()
        out = [g for g in out if g.source_id.casefold().startswith(needle)]
    if query:
        needle = query.casefold()
        matched: list[ConversationGraph] = []
        for g in out:
            if needle in (g.title or "").casefold() or any(needle in n.text.casefold() for n in g.nodes):
                matched.append(g)
        out = matched
    return out


def _first_string(*values: Any) -> str | None:
    return next((value for value in values if isinstance(value, str) and value), None)


def _extract_node_attachments(
    content: Any,
    msg_meta: dict[str, Any],
    node_id: str,
    zip_assets: dict[str, tuple[str, bytes]],
    asset_bytes: dict[str, bytes],
) -> tuple[list[dict[str, Any]], list[AssetRecord]]:
    """Extract image/file pointers and match them to ZIP binaries when present."""
    refs: list[dict[str, Any]] = []
    records: list[AssetRecord] = []
    seen_refs: set[str] = set()

    def register(source_ref: str, filename_hint: str | None, mime_hint: str | None) -> None:
        if not source_ref or source_ref in seen_refs:
            return
        seen_refs.add(source_ref)
        clean_ref = source_ref.replace("file-service://", "").replace("sediment://", "")
        matched: tuple[str, bytes] | None = None
        for probe in (
            (filename_hint or "").lower(),
            clean_ref.lower(),
            Path(clean_ref).name.lower(),
            Path(clean_ref).stem.lower(),
        ):
            if probe and probe in zip_assets:
                matched = zip_assets[probe]
                break
        if matched is None:
            # Substring fallback on file ID inside ZIP filenames
            for key, val in zip_assets.items():
                if len(clean_ref) >= 6 and clean_ref.lower() in key:
                    matched = val
                    break

        if matched is not None:
            orig_name, raw_data = matched
            digest = hashlib.sha256(raw_data).hexdigest()
            asset_bytes[digest] = raw_data
            mime = mime_hint or mimetypes.guess_type(orig_name)[0] or "application/octet-stream"
            safe_name = sanitize_single_segment(orig_name, fallback=f"asset-{digest[:12]}")
            rec = AssetRecord(
                asset_id=f"sha256:{digest[:16]}",
                source_ref=source_ref,
                filename=safe_name,
                mime_type=mime,
                sha256=digest,
                size_bytes=len(raw_data),
                disposition="embedded_copied",
                relative_bundle_path=f"assets/{digest[:16]}-{safe_name}",
                source_node_id=node_id,
            )
        else:
            fname = sanitize_single_segment(filename_hint or Path(clean_ref).name or "attachment", fallback="attachment")
            mime = mime_hint or mimetypes.guess_type(fname)[0] or "application/octet-stream"
            rec = AssetRecord(
                asset_id=f"ref:{hashlib.sha256(source_ref.encode('utf-8')).hexdigest()[:16]}",
                source_ref=source_ref,
                filename=fname,
                mime_type=mime,
                sha256=None,
                size_bytes=None,
                disposition="missing_in_export" if zip_assets else "external_reference",
                relative_bundle_path=None,
                source_node_id=node_id,
                notes="Binary payload not present in export archive; pointer preserved.",
            )
        records.append(rec)
        refs.append({"asset_id": rec.asset_id, "source_ref": source_ref, "filename": rec.filename, "disposition": rec.disposition})

    def walk(val: Any) -> None:
        if isinstance(val, list):
            for item in val:
                walk(item)
        elif isinstance(val, dict):
            ptr = _first_string(val.get("asset_pointer"), val.get("file_id"), val.get("image_url"))
            if ptr:
                register(ptr, _first_string(val.get("name"), val.get("filename")), _first_string(val.get("mime_type"), val.get("content_type")))
            for k, v in val.items():
                if k not in {"text", "asset_pointer", "file_id"}:
                    walk(v)

    walk(content)
    for att in msg_meta.get("attachments", []) if isinstance(msg_meta.get("attachments"), list) else []:
        if isinstance(att, dict):
            ptr = _first_string(att.get("id"), att.get("file_id"), att.get("name"))
            if ptr:
                register(ptr, _first_string(att.get("name"), att.get("filename")), _first_string(att.get("mime_type"), att.get("mimeType")))
    return refs, records


def _classify_node(role: str | None, message: dict[str, Any]) -> tuple[str, bool]:
    """Detect interruptions, tool calls/results, system events, and normal turns."""
    meta = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
    finish = meta.get("finish_details") if isinstance(meta.get("finish_details"), dict) else {}
    finish_type = str(finish.get("type") or "").lower()
    status = str(message.get("status") or "").lower()
    interrupted = finish_type in {"interrupted", "max_tokens", "stop_interrupted"} or status in {"in_progress", "interrupted", "cancelled"}
    if role == "tool":
        return "tool_result", interrupted
    if role == "system":
        return "system", interrupted
    if interrupted:
        return "interruption", True
    return "message", False


def _parse_conversation(
    value: dict[str, Any],
    index: int,
    source_path: Path,
    projects_by_id: dict[str, dict[str, Any]],
    sections_by_conv: dict[str, dict[str, Any]],
    zip_assets: dict[str, tuple[str, bytes]],
    asset_bytes: dict[str, bytes],
) -> ConversationGraph:
    conversation_id = _first_string(
        value.get("id"), value.get("conversation_id"), value.get("session_id")
    ) or f"conversation-{index}"
    title = _first_string(value.get("title"), value.get("name"))
    raw_mapping = value.get("mapping")
    nodes: list[MessageNode] = []
    all_assets: list[AssetRecord] = []
    all_links: list[str] = []
    seen_links: set[str] = set()
    total_in = 0
    total_out = 0
    model_slug = _first_string(value.get("default_model_slug"), value.get("model"))
    interruption_count = 0

    def add_links(urls: tuple[str, ...]) -> None:
        for u in urls:
            if u not in seen_links:
                seen_links.add(u)
                all_links.append(u)

    if isinstance(raw_mapping, dict):
        pending: list[tuple[str, dict[str, Any]]] = [
            (str(key), entry)
            for key, entry in raw_mapping.items()
            if isinstance(entry, dict)
        ]
        child_map: dict[str, list[str]] = {key: [] for key, _ in pending}
        parents: dict[str, str | None] = {}
        for key, entry in pending:
            parent = entry.get("parent")
            parent_id = str(parent) if parent is not None else None
            parents[key] = parent_id
            children = entry.get("children")
            if isinstance(children, list):
                for child in children:
                    child_id = str(child)
                    if child_id in child_map and child_id not in child_map[key]:
                        child_map[key].append(child_id)
        for key, entry in pending:
            parent_id = parents[key]
            if parent_id in child_map and key not in child_map[parent_id]:
                child_map[parent_id].append(key)
            message = entry.get("message")
            message = message if isinstance(message, dict) else {}
            author = message.get("author")
            author = author if isinstance(author, dict) else {}
            msg_meta = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
            if not model_slug:
                model_slug = _first_string(msg_meta.get("model_slug"), msg_meta.get("default_model_slug"))
            content = message.get("content")
            role = _first_string(author.get("role"), message.get("role"))
            text = content_text(content)
            event_type, interrupted = _classify_node(role, message)
            if interrupted:
                interruption_count += 1
            att_refs, att_records = _extract_node_attachments(content, msg_meta, key, zip_assets, asset_bytes)
            all_assets.extend(att_records)
            node_links = extract_links(text)
            # Also collect citations/links in metadata
            for cite in msg_meta.get("citations", []) if isinstance(msg_meta.get("citations"), list) else []:
                if isinstance(cite, dict):
                    u = _first_string(cite.get("url"), (cite.get("metadata") or {}).get("url") if isinstance(cite.get("metadata"), dict) else None)
                    if u and u not in node_links:
                        node_links = (*node_links, u)
            add_links(node_links)
            usage = msg_meta.get("usage") if isinstance(msg_meta.get("usage"), dict) else None
            if usage:
                total_in += int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
                total_out += int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
            nodes.append(
                MessageNode(
                    node_id=key,
                    parent_id=parent_id,
                    child_ids=tuple(child_map[key]),
                    role=role,
                    text=text,
                    timestamp=message.get("create_time", entry.get("create_time")),
                    content=content,
                    raw_record=entry,
                    event_type=event_type,
                    attachments=tuple(att_refs),
                    links=node_links,
                    usage=usage,
                    interrupted=interrupted,
                )
            )
        root_ids = tuple(
            key for key, _ in pending if parents[key] is None or parents[key] not in child_map
        )
        active_node_id = _first_string(value.get("current_node"))
    elif isinstance(value.get("messages"), list):
        previous: str | None = None
        for message_index, message in enumerate(value["messages"]):
            if not isinstance(message, dict):
                continue
            node_id = _first_string(message.get("id"), message.get("message_id")) or str(
                message_index
            )
            content = message.get("content")
            role = _first_string(message.get("role"), message.get("author"))
            text = content_text(content)
            event_type, interrupted = _classify_node(role, message)
            if interrupted:
                interruption_count += 1
            msg_meta = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
            att_refs, att_records = _extract_node_attachments(content, msg_meta, node_id, zip_assets, asset_bytes)
            all_assets.extend(att_records)
            node_links = extract_links(text)
            add_links(node_links)
            if previous is not None and nodes:
                prev = nodes[-1]
                nodes[-1] = MessageNode(
                    node_id=prev.node_id,
                    parent_id=prev.parent_id,
                    child_ids=(node_id,),
                    role=prev.role,
                    text=prev.text,
                    timestamp=prev.timestamp,
                    content=prev.content,
                    raw_record=prev.raw_record,
                    event_type=prev.event_type,
                    parent_tool_use_id=prev.parent_tool_use_id,
                    attachments=prev.attachments,
                    links=prev.links,
                    usage=prev.usage,
                    interrupted=prev.interrupted,
                    is_sidechain=prev.is_sidechain,
                )
            nodes.append(
                MessageNode(
                    node_id=node_id,
                    parent_id=previous,
                    child_ids=(),
                    role=role,
                    text=text,
                    timestamp=message.get("timestamp", message.get("create_time")),
                    content=content,
                    raw_record=message,
                    event_type=event_type,
                    attachments=tuple(att_refs),
                    links=node_links,
                    interrupted=interrupted,
                )
            )
            previous = node_id
        root_ids = (nodes[0].node_id,) if nodes else ()
        active_node_id = nodes[-1].node_id if nodes else None
    else:
        raise ValueError(f"conversation {conversation_id} has neither mapping nor messages")

    # Resolve project & section metadata from conversation fields + optional ZIP sidecars
    project_id = _first_string(value.get("project_id"), value.get("projectId"), value.get("gizmo_id"))
    project_name = _first_string(
        value.get("project_name"), value.get("projectName"), value.get("project_title")
    )
    if project_id and not project_name and project_id in projects_by_id:
        project_name = _first_string(projects_by_id[project_id].get("name"), projects_by_id[project_id].get("title"))

    sec_sidecar = sections_by_conv.get(conversation_id, {})
    section_id = _first_string(value.get("section_id"), value.get("sectionId"), sec_sidecar.get("section_id"))
    section_name = _first_string(value.get("section_name"), value.get("sectionName"), sec_sidecar.get("section_name"))

    usage_summary = UsageSummary(input_tokens=total_in, output_tokens=total_out) if (total_in or total_out) else None

    metadata = {
        "create_time": value.get("create_time"),
        "update_time": value.get("update_time"),
        "model": model_slug,
        "is_archived": bool(value.get("is_archived", False)),
        "project_id": project_id,
        "project_name": project_name,
        "section_id": section_id,
        "section_name": section_name,
        "parent_conversation_id": _first_string(
            value.get("parent_conversation_id"), value.get("parentConversationId"), value.get("forked_from")
        ),
        "branch_id": _first_string(value.get("branch_id"), value.get("branchId")),
        "interruption_count": interruption_count,
        "source_file": source_path.name,
    }
    return ConversationGraph(
        source_format="chatgpt_export",
        source_id=conversation_id,
        title=title,
        workspace=None,
        nodes=tuple(nodes),
        root_ids=root_ids,
        active_node_id=active_node_id,
        metadata=metadata,
        raw_source=value,
        assets=tuple(all_assets),
        usage=usage_summary,
        links=tuple(all_links),
        app_mode="web-export",
    )
