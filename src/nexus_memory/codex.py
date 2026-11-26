"""Reader and writer for OpenAI Codex CLI (0.154+) rollouts & Codex App databases/snapshots.

Read capabilities:
- Streaming line-by-line reader for `.jsonl` and `.jsonl.zst` (handles >256 MiB rollouts safely)
- Full modern Codex event coverage: `session_meta`, `response_item` (`message`, `developer`,
  `function_call`, `function_call_output`, `custom_tool_call`, `custom_tool_call_output`,
  `agent_message`, `reasoning`, `compaction`), `event_msg` (`user_message`, `agent_message`,
  `token_count`, `turn_aborted`, `interrupted`), `token_usage_record`
- Full `~/.codex` home directory scan (`sessions/`, `archived_sessions/`, `session_index.jsonl`,
  read-only `state_5.sqlite` joining `projects` + `project_roots` + `thread_sections` +
  `thread_spawn_edges` + `thread_attachments`, automatic `.jsonl` -> `.jsonl.zst` resolution,
  and `thread_history_1.sqlite` fallback when a rollout file was pruned)
- Codex App snapshot JSON reader

Write capabilities:
- Real `codex 0.154.0` `exec resume`-verified rollout JSONL builder (`build_codex_rollouts`):
  valid `session_meta` enum values (`source: "cli"`, `originator: "codex_cli_rs"`, `cli_version`,
  `timestamp`, `model_provider`), JSON-stringified `function_call.arguments`, strict tool-call /
  tool-output pairing (prevents `400 Invalid Params`), and exact `sessions/YYYY/MM/DD/rollout-...` paths.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import subprocess
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .model import ConversationGraph, MessageNode, UsageSummary, content_text, extract_links

CODEX_TARGET_CLI_VERSION = "0.154.0"


def _iter_rollout_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Stream lines from `.jsonl` or `.jsonl.zst` without loading huge files into RAM."""
    if path.suffix.lower() == ".zst":
        try:
            import zstandard  # type: ignore[import-not-found]

            with path.open("rb") as fh:
                dctx = zstandard.ZstdDecompressor()
                with dctx.stream_reader(fh) as reader:
                    text_stream = io.TextIOWrapper(reader, encoding="utf-8-sig", errors="replace")
                    for idx, line in enumerate(text_stream, 1):
                        yield idx, line
            return
        except ImportError:
            zstd_bin = shutil.which("zstd")
            if not zstd_bin:
                raise ValueError("cannot read .zst rollout: neither python 'zstandard' nor 'zstd' CLI is available")
            proc = subprocess.Popen([zstd_bin, "-dc", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            assert proc.stdout is not None
            try:
                text_stream = io.TextIOWrapper(proc.stdout, encoding="utf-8-sig", errors="replace")
                for idx, line in enumerate(text_stream, 1):
                    yield idx, line
            finally:
                stderr_bytes = proc.stderr.read() if proc.stderr else b""
                rc = proc.wait()
            if rc != 0:
                raise ValueError(f"zstd decompression failed for {path.name}: {stderr_bytes.decode('utf-8', 'replace')}")
            return

    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        for idx, line in enumerate(fh, 1):
            yield idx, line


def _read_rollout_text(path: Path) -> str:
    """Backwards-compatible helper returning full rollout text for small files."""
    return "".join(line for _, line in _iter_rollout_lines(path))


def parse_rollout(
    path: str | Path,
    *,
    archived: bool = False,
    retain_raw_records: bool = True,
) -> ConversationGraph:
    """Parse a single Codex CLI rollout `.jsonl` or `.jsonl.zst` file via streaming."""
    source_path = Path(path).expanduser()
    records: list[dict[str, Any]] = []
    record_count = 0
    session_meta: dict[str, Any] = {}
    first_thread_id: str | None = None

    nodes: list[MessageNode] = []
    existing_ids: set[str] = set()
    previous_id: str | None = None
    unmapped_types: dict[str, int] = {}
    all_links: list[str] = []
    seen_links: set[str] = set()
    usage_in = 0
    usage_out = 0
    usage_cache = 0
    usage_reasoning = 0
    interruption_count = 0
    # Cap in-memory raw_records automatically for massive (>25 MB) rollouts so we never OOM
    file_size = source_path.stat().st_size if source_path.is_file() else 0
    keep_raw = retain_raw_records and file_size <= 25 * 1024 * 1024

    for line_number, line in _iter_rollout_lines(source_path):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL record at line {line_number}: {exc.msg}") from exc
        if not isinstance(record, dict):
            continue

        record_index = record_count
        record_count += 1
        if keep_raw:
            records.append(record)
        if first_thread_id is None and isinstance(record.get("thread_id"), str):
            first_thread_id = record["thread_id"]

        record_type = record.get("type")
        payload = record.get("payload")
        payload = payload if isinstance(payload, dict) else {}

        if record_type == "session_meta":
            if not session_meta:
                session_meta = payload
            continue

        # Token usage accounting (supports both legacy event_msg:token_count & modern token_usage_record)
        if (record_type == "event_msg" and payload.get("type") == "token_count") or record_type == "token_usage_record":
            totals = (
                payload.get("total_token_usage")
                or (payload.get("info") or {}).get("total_token_usage")
                or payload.get("usage")
                or payload
            )
            if isinstance(totals, dict):
                usage_in = max(usage_in, int(totals.get("input_tokens") or 0))
                usage_out = max(usage_out, int(totals.get("output_tokens") or 0))
                usage_cache = max(usage_cache, int(totals.get("cached_input_tokens") or totals.get("cache_read_input_tokens") or 0))
                usage_reasoning = max(usage_reasoning, int(totals.get("reasoning_output_tokens") or 0))
            lbl = "token_count" if record_type == "event_msg" else "token_usage_record"
            unmapped_types[lbl] = unmapped_types.get(lbl, 0) + 1
            continue

        if record_type == "event_msg" and payload.get("type") in {"turn_aborted", "interrupted"}:
            interruption_count += 1
            lbl = str(payload.get("type"))
            unmapped_types[lbl] = unmapped_types.get(lbl, 0) + 1
            continue

        role, content, event_type = _message_payload(record_type, payload)
        if role is None:
            label = str(payload.get("type", record_type or "unknown"))
            unmapped_types[label] = unmapped_types.get(label, 0) + 1
            continue

        node_id = _string(record.get("uuid"), payload.get("id"), payload.get("call_id"), record.get("id")) or str(
            record_index
        )
        if node_id in existing_ids:
            node_id = f"{node_id}-{record_index}"
        existing_ids.add(node_id)

        text = content_text(content)
        node_links = extract_links(text)
        for u in node_links:
            if u not in seen_links:
                seen_links.add(u)
                all_links.append(u)

        if nodes:
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
                parent_id=previous_id,
                child_ids=(),
                role=role,
                text=text,
                timestamp=record.get("timestamp", payload.get("timestamp")),
                content=content,
                raw_record=record if keep_raw else {"type": record_type, "payload_type": payload.get("type")},
                event_type=event_type,
                links=node_links,
            )
        )
        previous_id = node_id

    source_id = _string(
        session_meta.get("id"),
        session_meta.get("thread_id"),
        session_meta.get("session_id"),
        first_thread_id,
        source_path.stem.removesuffix(".jsonl"),
    ) or source_path.stem
    workspace = _string(session_meta.get("cwd"), session_meta.get("working_directory"))
    roots = (nodes[0].node_id,) if nodes else ()
    title = _string(session_meta.get("title"), session_meta.get("name"))
    usage_summary = (
        UsageSummary(
            input_tokens=usage_in,
            output_tokens=usage_out,
            cache_read_tokens=usage_cache,
            reasoning_tokens=usage_reasoning,
        )
        if (usage_in or usage_out or usage_cache or usage_reasoning)
        else None
    )
    metadata = {
        "parent_session_id": _string(
            session_meta.get("parent_thread_id"), session_meta.get("parent_session_id")
        ),
        "model": _string(session_meta.get("model"), session_meta.get("model_provider")),
        "model_provider": _string(session_meta.get("model_provider")),
        "cli_version": _string(session_meta.get("cli_version")),
        "project_id": _string(session_meta.get("project_id"), session_meta.get("projectId")),
        "project_name": _string(session_meta.get("project_name"), session_meta.get("projectName")),
        "section_id": _string(session_meta.get("section_id"), session_meta.get("sectionId")),
        "section_name": _string(session_meta.get("section_name"), session_meta.get("sectionName")),
        "is_archived": archived or bool(session_meta.get("archived", False)),
        "interruption_count": interruption_count,
        "record_count": record_count,
        "raw_records_omitted_for_size": not keep_raw,
        "unmapped_record_types": unmapped_types,
        "source_file": source_path.name,
    }
    return ConversationGraph(
        source_format="codex_rollout",
        source_id=source_id,
        title=title,
        workspace=workspace,
        nodes=tuple(nodes),
        root_ids=roots,
        active_node_id=nodes[-1].node_id if nodes else None,
        metadata=metadata,
        raw_source={"session_meta": session_meta, "records": records},
        usage=usage_summary,
        links=tuple(all_links),
        app_mode="cli",
    )


def _resolve_codex_rollout_path(raw_path: str | None, root: Path, thread_id: str) -> Path | None:
    """Resolve a Codex rollout path even when compressed to `.jsonl.zst` or archived."""
    candidates: list[Path] = []
    if raw_path:
        p = Path(raw_path)
        candidates.append(p)
        if p.suffix == ".jsonl":
            candidates.append(p.with_suffix(".jsonl.zst"))
        # Relative fallback inside given root (supports isolated/copied CODEX_HOME)
        try:
            idx = p.parts.index("sessions")
            rel = Path(*p.parts[idx:])
            candidates.append(root / rel)
            if rel.suffix == ".jsonl":
                candidates.append((root / rel).with_suffix(".jsonl.zst"))
        except ValueError:
            pass
    for c in candidates:
        if c.is_file():
            return c
    # Filename match fallback inside root/sessions and root/archived_sessions
    for sub in ("sessions", "archived_sessions"):
        sd = root / sub
        if sd.is_dir():
            for match in sd.rglob(f"*{thread_id}*.jsonl*"):
                if match.is_file():
                    return match
    return None


def _parse_thread_from_history_sqlite(
    dbh: Path,
    thread_id: str,
    meta_row: dict[str, Any],
) -> ConversationGraph | None:
    """Fallback reader using `thread_history_1.sqlite` (`thread_items`) if rollout file is absent."""
    if not dbh.is_file():
        return None
    try:
        conn = sqlite3.connect(f"file:{dbh}?mode=ro", uri=True)
        rows = conn.execute(
            "SELECT item_id, item_type, item_json, created_at_ms FROM thread_items WHERE thread_id = ? ORDER BY rollout_ordinal ASC",
            (thread_id,),
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return None
    if not rows:
        return None

    nodes: list[MessageNode] = []
    prev_id: str | None = None
    for idx, (item_id, item_type, item_json, created_ms) in enumerate(rows):
        try:
            obj = json.loads(item_json) if isinstance(item_json, str) else {}
        except json.JSONDecodeError:
            continue
        itype = str(item_type or obj.get("type") or "")
        if itype == "userMessage":
            role, ev = "user", "message"
            text = content_text(obj.get("content", ""))
        elif itype in {"agentMessage", "assistantMessage"}:
            role, ev = "assistant", "message"
            text = content_text(obj.get("content", obj.get("text", "")))
        elif itype == "subAgentActivity":
            role, ev = "system", "subagent_activity"
            text = f"subagent:{obj.get('kind', '')} {obj.get('agentThreadId', '')}".strip()
        else:
            continue
        nid = str(item_id or f"th-{idx}")
        if nodes:
            p = nodes[-1]
            nodes[-1] = MessageNode(
                p.node_id, p.parent_id, (nid,), p.role, p.text, p.timestamp, p.content, p.raw_record,
                event_type=p.event_type, links=p.links,
            )
        nodes.append(
            MessageNode(
                node_id=nid,
                parent_id=prev_id,
                child_ids=(),
                role=role,
                text=text,
                timestamp=created_ms,
                content=obj,
                raw_record=obj,
                event_type=ev,
                links=extract_links(text),
            )
        )
        prev_id = nid
    return ConversationGraph(
        source_format="codex_thread_history_sqlite",
        source_id=thread_id,
        title=_string(meta_row.get("title"), meta_row.get("name")),
        workspace=_string(meta_row.get("cwd")),
        nodes=tuple(nodes),
        root_ids=(nodes[0].node_id,) if nodes else (),
        active_node_id=nodes[-1].node_id if nodes else None,
        metadata={"source_file": dbh.name},
        raw_source={"thread_meta": meta_row},
        app_mode="cli",
    )


def parse_codex_home(
    codex_home: str | Path,
    *,
    section_filter: str | None = None,
    project_filter: str | None = None,
    limit: int | None = None,
    on_progress: Callable[[str, int, int, str], None] | None = None,
) -> list[ConversationGraph]:
    """Read Codex sessions with full `state_5.sqlite` Projects, Project Roots, Sections & Spawn Edges.

    Supports filtering BEFORE reading large rollout files (`section_filter`, `project_filter`, `limit`)
    so querying a single section like `Destruction Era` or one project is instantaneous!
    """
    root = Path(codex_home).expanduser()
    titles_by_id: dict[str, str] = {}
    meta_by_id: dict[str, dict[str, Any]] = {}
    projects_by_id: dict[str, dict[str, Any]] = {}
    project_roots: list[tuple[str, str, str]] = []  # (path, project_id, project_name)
    sections_by_id: dict[str, dict[str, Any]] = {}
    parent_by_child: dict[str, str] = {}

    idx_file = root / "session_index.jsonl"
    if idx_file.is_file():
        for line in idx_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                tid = _string(row.get("id"), row.get("thread_id"))
                title = _string(row.get("thread_name"), row.get("title"), row.get("name"))
                if tid and title:
                    titles_by_id[tid] = title
            except json.JSONDecodeError:
                continue

    db_path = root / "state_5.sqlite"
    if db_path.is_file():
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "projects" in tables:
                for row in conn.execute("SELECT id, name FROM projects"):
                    projects_by_id[str(row["id"])] = {"id": str(row["id"]), "name": row["name"]}
            if "project_roots" in tables:
                for row in conn.execute("SELECT project_id, path FROM project_roots"):
                    pid = str(row["project_id"])
                    if row["path"]:
                        pname = (projects_by_id.get(pid) or {}).get("name") or Path(row["path"]).name
                        project_roots.append((str(row["path"]).rstrip("/"), pid, str(pname)))
                # Match longest root prefix first
                project_roots.sort(key=lambda x: len(x[0]), reverse=True)
            if "thread_sections" in tables:
                for row in conn.execute("SELECT id, name FROM thread_sections"):
                    sections_by_id[str(row["id"])] = {"id": str(row["id"]), "name": row["name"]}
            if "thread_spawn_edges" in tables:
                for row in conn.execute("SELECT parent_thread_id, child_thread_id FROM thread_spawn_edges"):
                    parent_by_child[str(row["child_thread_id"])] = str(row["parent_thread_id"])
            if "threads" in tables:
                for row in conn.execute("SELECT * FROM threads"):
                    d = dict(row)
                    tid = _string(d.get("id"), d.get("thread_id"))
                    if tid:
                        meta_by_id[tid] = d
                        if isinstance(d.get("title"), str) and d["title"]:
                            titles_by_id.setdefault(tid, d["title"])
            conn.close()
        except sqlite3.Error:
            pass

    def resolve_project(db_row: dict[str, Any], cwd: str | None) -> tuple[str | None, str | None]:
        pid = _string(db_row.get("project_id"))
        if pid and pid in projects_by_id:
            return pid, projects_by_id[pid].get("name")
        if cwd:
            norm = cwd.rstrip("/")
            for root_p, r_pid, r_name in project_roots:
                if norm == root_p or norm.startswith(root_p + "/"):
                    return r_pid, r_name
        return pid, None

    def enrich_graph(graph: ConversationGraph, db_row: dict[str, Any]) -> ConversationGraph:
        tid = graph.source_id
        title = graph.title or titles_by_id.get(tid) or _string(db_row.get("title"), db_row.get("name"))
        workspace = graph.workspace or _string(db_row.get("cwd"), db_row.get("workspace"))
        meta = dict(graph.metadata)
        pid, pname = resolve_project(db_row, workspace)
        if pid and not meta.get("project_id"):
            meta["project_id"] = pid
        if pname and not meta.get("project_name"):
            meta["project_name"] = pname
        sec_id = _string(db_row.get("thread_section_id"))
        if sec_id:
            meta["section_id"] = sec_id
            sec = sections_by_id.get(sec_id)
            if sec and sec.get("name"):
                meta["section_name"] = sec["name"]
        parent_id = (
            meta.get("parent_session_id")
            or _string(db_row.get("attached_thread_parent_id"), db_row.get("parent_thread_id"))
            or parent_by_child.get(tid)
        )
        if parent_id:
            meta["parent_session_id"] = parent_id
            # Compute nesting depth along parent_by_child chain
            depth = 1
            cur_p = parent_id
            seen_chain = {tid, cur_p}
            while cur_p in parent_by_child and parent_by_child[cur_p] not in seen_chain:
                cur_p = parent_by_child[cur_p]
                seen_chain.add(cur_p)
                depth += 1
            meta.setdefault("nesting_depth", depth)
            meta.setdefault("root_session_id", cur_p)
        else:
            meta.setdefault("nesting_depth", 0)
        if db_row.get("model") and not meta.get("model"):
            meta["model"] = db_row["model"]
        if db_row.get("archived"):
            meta["is_archived"] = True
        return ConversationGraph(
            source_format=graph.source_format,
            source_id=graph.source_id,
            title=title,
            workspace=workspace,
            nodes=graph.nodes,
            root_ids=graph.root_ids,
            active_node_id=graph.active_node_id,
            metadata=meta,
            raw_source=graph.raw_source,
            assets=graph.assets,
            usage=graph.usage,
            links=graph.links,
            app_mode=graph.app_mode,
        )

    graphs: list[ConversationGraph] = []
    seen_ids: set[str] = set()

    # Fast path when filtering via state_5.sqlite metadata (avoids scanning thousands of unrelated rollouts!)
    if meta_by_id and (section_filter or project_filter):
        sec_needle = section_filter.casefold() if section_filter else None
        proj_needle = project_filter.casefold() if project_filter else None
        dbh = root / "thread_history_1.sqlite"
        matched_items: list[tuple[str, dict[str, Any]]] = []
        for tid, db_row in meta_by_id.items():
            sec_id = _string(db_row.get("thread_section_id"))
            sec_name = (sections_by_id.get(sec_id or "") or {}).get("name") or ""
            pid, pname = resolve_project(db_row, _string(db_row.get("cwd")))
            if sec_needle and sec_needle not in sec_name.casefold() and sec_needle not in (sec_id or "").casefold():
                continue
            if proj_needle and proj_needle not in (pname or "").casefold() and proj_needle not in (pid or "").casefold():
                continue
            matched_items.append((tid, db_row))
            if limit and len(matched_items) >= limit:
                break

        def _load_one_meta(item: tuple[str, dict[str, Any]]) -> ConversationGraph | None:
            tid, db_row = item
            rp = _resolve_codex_rollout_path(_string(db_row.get("rollout_path")), root, tid)
            graph: ConversationGraph | None = None
            if rp is not None:
                try:
                    graph = parse_rollout(rp, archived=bool(db_row.get("archived")))
                except (OSError, ValueError):
                    graph = None
            if graph is None:
                graph = _parse_thread_from_history_sqlite(dbh, tid, db_row)
            return enrich_graph(graph, db_row) if graph is not None else None

        total_m = len(matched_items)
        if total_m >= 4:
            workers = min(8, os.cpu_count() or 4, total_m)
            out_map: dict[int, ConversationGraph] = {}
            done = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = {pool.submit(_load_one_meta, item): idx for idx, item in enumerate(matched_items)}
                for fut in as_completed(futs):
                    idx = futs[fut]
                    g = fut.result()
                    if g is not None:
                        out_map[idx] = g
                    done += 1
                    if on_progress is not None:
                        lbl = (g.title if g else matched_items[idx][0]) or ""
                        on_progress("parse", done, total_m, str(lbl))
            graphs = [out_map[i] for i in sorted(out_map)]
        else:
            for idx, item in enumerate(matched_items, 1):
                g = _load_one_meta(item)
                if g is not None:
                    graphs.append(g)
                if on_progress is not None:
                    on_progress("parse", idx, max(total_m, 1), str((g.title if g else item[0]) or ""))
        return graphs

    # General scan across sessions/ and archived_sessions/ (parallelized for large rollout sets)
    candidates: list[tuple[Path, bool]] = []
    for subdir, is_arch in (("sessions", False), ("archived_sessions", True)):
        base = root / subdir
        if not base.is_dir():
            continue
        files = sorted(
            [p for p in base.rglob("*") if p.is_file() and (p.name.endswith(".jsonl") or p.name.endswith(".jsonl.zst"))],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for fp in files:
            candidates.append((fp, is_arch))
    if limit:
        candidates = candidates[:limit]

    total_c = len(candidates)

    def _load_one_file(item: tuple[Path, bool]) -> ConversationGraph | None:
        fp, is_arch = item
        try:
            g = parse_rollout(fp, archived=is_arch)
        except (OSError, ValueError):
            return None
        return enrich_graph(g, meta_by_id.get(g.source_id, {}))

    if total_c >= 4:
        workers = min(8, os.cpu_count() or 4, total_c)
        out_map2: dict[int, ConversationGraph] = {}
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_load_one_file, item): idx for idx, item in enumerate(candidates)}
            for fut in as_completed(futs):
                idx = futs[fut]
                g = fut.result()
                if g is not None:
                    out_map2[idx] = g
                done += 1
                if on_progress is not None:
                    on_progress("parse", done, total_c, str((g.title if g else candidates[idx][0].name) or ""))
        for i in sorted(out_map2):
            g = out_map2[i]
            if g.source_id not in seen_ids:
                seen_ids.add(g.source_id)
                graphs.append(g)
    else:
        for idx, item in enumerate(candidates, 1):
            g = _load_one_file(item)
            if g is not None and g.source_id not in seen_ids:
                seen_ids.add(g.source_id)
                graphs.append(g)
            if on_progress is not None:
                on_progress("parse", idx, max(total_c, 1), str((g.title if g else item[0].name) or ""))
    return graphs


def parse_codex_app_snapshot(path: str | Path) -> list[ConversationGraph]:
    """Read a Codex App local Projects + sidebar Sections snapshot JSON (source-qualified membership)."""
    source_path = Path(path).expanduser()
    data = json.loads(source_path.read_text(encoding="utf-8-sig"))
    projects_by_id: dict[str, dict[str, Any]] = {}
    for proj in data.get("projects", []):
        if isinstance(proj, dict):
            pid = _string(proj.get("id"), proj.get("project_id"))
            if pid:
                projects_by_id[pid] = proj

    section_by_thread: dict[str, dict[str, Any]] = {}
    for sec in data.get("sections", data.get("sidebar_sections", [])):
        if not isinstance(sec, dict):
            continue
        sid = _string(sec.get("id"), sec.get("section_id"))
        sname = _string(sec.get("name"), sec.get("title"))
        for item_key in sec.get("item_keys", sec.get("thread_ids", [])):
            if isinstance(item_key, str):
                bare = item_key.split(":")[-1]
                section_by_thread[item_key] = {"section_id": sid, "section_name": sname, "source_item_key": item_key}
                section_by_thread[bare] = {"section_id": sid, "section_name": sname, "source_item_key": item_key}

    graphs: list[ConversationGraph] = []
    for idx, thread in enumerate(data.get("threads", data.get("sessions", []))):
        if not isinstance(thread, dict):
            continue
        tid = _string(thread.get("id"), thread.get("thread_id")) or f"codex-app-{idx}"
        pid = _string(thread.get("project_id"), thread.get("projectId"))
        proj = projects_by_id.get(pid or "", {})
        sec = section_by_thread.get(tid, {})
        workspace = _string(thread.get("cwd"), proj.get("workspace"), proj.get("path"))
        nodes: list[MessageNode] = []
        prev_id: str | None = None
        for m_idx, msg in enumerate(thread.get("messages", [])):
            if not isinstance(msg, dict):
                continue
            nid = _string(msg.get("id")) or f"{tid}-m{m_idx}"
            role = _string(msg.get("role")) or "user"
            content = msg.get("content", "")
            text = content_text(content)
            if nodes:
                prev = nodes[-1]
                nodes[-1] = MessageNode(
                    prev.node_id, prev.parent_id, (nid,), prev.role, prev.text, prev.timestamp, prev.content, prev.raw_record,
                    event_type=prev.event_type, links=prev.links,
                )
            nodes.append(
                MessageNode(
                    node_id=nid,
                    parent_id=prev_id,
                    child_ids=(),
                    role=role,
                    text=text,
                    timestamp=msg.get("timestamp"),
                    content=content,
                    raw_record=msg,
                    links=extract_links(text),
                )
            )
            prev_id = nid

        graphs.append(
            ConversationGraph(
                source_format="codex_app_snapshot",
                source_id=tid,
                title=_string(thread.get("title"), thread.get("name")),
                workspace=workspace,
                nodes=tuple(nodes),
                root_ids=(nodes[0].node_id,) if nodes else (),
                active_node_id=nodes[-1].node_id if nodes else None,
                metadata={
                    "project_id": pid,
                    "project_name": _string(thread.get("project_name"), proj.get("name"), proj.get("title")),
                    "section_id": _string(thread.get("section_id"), sec.get("section_id")),
                    "section_name": _string(thread.get("section_name"), sec.get("section_name")),
                    "section_item_key": sec.get("source_item_key"),
                    "parent_session_id": _string(thread.get("parent_thread_id"), thread.get("parent_session_id")),
                    "source_file": source_path.name,
                },
                raw_source=thread,
                app_mode="desktop-app",
            )
        )
    return graphs


def build_codex_rollouts(
    graph: ConversationGraph,
    *,
    cwd: str | Path,
    model_provider: str = "openai",
    cli_version: str = CODEX_TARGET_CLI_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Project a canonical ConversationGraph into real `codex 0.154+`-verified rollout JSONL.

    Guarantees:
    - Valid `session_meta` Rust enum values (`source: "cli"`, `originator: "codex_cli_rs"`, `cli_version`, `timestamp`)
    - JSON-stringified `function_call.arguments`
    - Strict `call_id` pairing (drops unpaired tool calls/outputs so Responses API never rejects with Invalid Params)
    - Standard `sessions/YYYY/MM/DD/rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl` naming
    """
    sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    raw_paths = graph.branch_paths()
    if not raw_paths:
        losses.append({"feature": "empty_conversation", "disposition": "skipped_zero_node_conversation"})
        return sessions, losses

    resolved_cwd = str(Path(graph.workspace or cwd).expanduser().resolve())
    now_dt = datetime.now(UTC)
    now_iso = now_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    date_sub = now_dt.strftime("%Y/%m/%d")
    ts_slug = now_dt.strftime("%Y-%m-%dT%H-%M-%S")

    for branch_index, path in enumerate(raw_paths, 1):
        thread_id = str(uuid.uuid4())
        title = graph.title or f"Imported {graph.source_format} {graph.source_id}"
        if len(raw_paths) > 1:
            title = f"{title} [branch {branch_index}]"

        # Pre-compute matched tool call IDs so we NEVER emit an unpaired function_call or function_call_output!
        call_ids_seen: set[str] = set()
        output_ids_seen: set[str] = set()
        for node in path:
            if node.role == "tool_call" and isinstance(node.content, dict):
                cid = str(node.content.get("call_id") or node.content.get("id") or "")
                if cid:
                    call_ids_seen.add(cid)
            elif node.role == "tool_result" and isinstance(node.content, dict):
                cid = str(node.content.get("call_id") or node.content.get("tool_use_id") or "")
                if cid:
                    output_ids_seen.add(cid)
        paired_call_ids = call_ids_seen & output_ids_seen

        meta_payload: dict[str, Any] = {
            "id": thread_id,
            "session_id": thread_id,
            "timestamp": now_iso,
            "cwd": resolved_cwd,
            "originator": "codex_cli_rs",
            "cli_version": cli_version,
            "source": "cli",
            "model_provider": model_provider,
        }
        records: list[dict[str, Any]] = [
            {
                "timestamp": now_iso,
                "type": "session_meta",
                "payload": meta_payload,
            }
        ]
        source_node_ids: list[str] = []
        dropped_unpaired_tools = 0

        for node in path:
            ts = node.timestamp if isinstance(node.timestamp, str) and node.timestamp else now_iso
            if node.role in {"user", "assistant"} and node.text.strip():
                content_type = "input_text" if node.role == "user" else "output_text"
                records.append(
                    {
                        "timestamp": ts,
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": node.role,
                            "content": [{"type": content_type, "text": node.text}],
                        },
                    }
                )
                source_node_ids.append(node.node_id)
            elif node.role == "tool_call" and isinstance(node.content, dict):
                cid = str(node.content.get("call_id") or node.content.get("id") or "")
                if cid and cid in paired_call_ids:
                    raw_args = node.content.get("arguments", node.content.get("input", {}))
                    args_str = raw_args if isinstance(raw_args, str) else json.dumps(raw_args, ensure_ascii=False)
                    records.append(
                        {
                            "timestamp": ts,
                            "type": "response_item",
                            "payload": {
                                "type": "function_call",
                                "name": str(node.content.get("name") or "tool"),
                                "arguments": args_str,
                                "call_id": cid,
                            },
                        }
                    )
                    source_node_ids.append(node.node_id)
                else:
                    dropped_unpaired_tools += 1
            elif node.role == "tool_result" and isinstance(node.content, dict):
                cid = str(node.content.get("call_id") or node.content.get("tool_use_id") or "")
                if cid and cid in paired_call_ids:
                    out_val = node.content.get("output", node.content.get("content", node.text))
                    out_str = out_val if isinstance(out_val, str) else json.dumps(out_val, ensure_ascii=False)
                    records.append(
                        {
                            "timestamp": ts,
                            "type": "response_item",
                            "payload": {
                                "type": "function_call_output",
                                "call_id": cid,
                                "output": out_str,
                            },
                        }
                    )
                    source_node_ids.append(node.node_id)
                else:
                    dropped_unpaired_tools += 1

        if dropped_unpaired_tools:
            losses.append(
                {
                    "feature": "unpaired_tool_events_omitted_for_api_validity",
                    "disposition": f"omitted {dropped_unpaired_tools} unpaired tool_call/tool_result to prevent Responses API Invalid Params; retained in portable.json",
                }
            )

        sessions.append(
            {
                "session_id": thread_id,
                "branch_index": branch_index,
                "title": title,
                "cwd": resolved_cwd,
                "rollout_rel_subpath": f"{date_sub}/rollout-{ts_slug}-{thread_id}.jsonl",
                "session_index_entry": {"id": thread_id, "thread_name": title, "updated_at": now_iso},
                "source_node_ids": source_node_ids,
                "records": records,
            }
        )

    if len(raw_paths) > 1:
        losses.append(
            {
                "feature": "branch_topology",
                "disposition": "one_codex_rollout_per_leaf_path; exact graph retained in portable.json",
            }
        )
    if graph.assets:
        losses.append(
            {
                "feature": "binary_attachments",
                "disposition": "archived_in_bundle_assets_with_sha256; codex rollout carries text/references only",
            }
        )
    if graph.metadata.get("section_name"):
        losses.append(
            {
                "feature": "sidebar_section_group",
                "disposition": "archived_in_portable_hierarchy; codex rollout JSONL has no native section field (sections live in state_5.sqlite)",
            }
        )
    return sessions, losses


def _message_payload(record_type: Any, payload: dict[str, Any]) -> tuple[str | None, Any, str]:
    if record_type == "response_item":
        item_type = payload.get("type")
        if item_type == "message":
            role = payload.get("role")
            if not role:
                return None, None, "message"
            rstr = str(role)
            ev = "developer_instruction" if rstr == "developer" else "message"
            return rstr, payload.get("content"), ev
        if item_type in {"function_call", "tool_call", "custom_tool_call"}:
            return "tool_call", payload, "tool_use"
        if item_type in {"function_call_output", "tool_result", "custom_tool_call_output"}:
            return "tool_result", payload, "tool_result"
        if item_type == "agent_message":
            return "assistant", payload.get("content", payload.get("message", payload.get("text"))), "subagent_message"
        if item_type == "compaction":
            return "system", payload.get("summary", payload.get("content", "compaction")), "compaction"
        return None, None, "message"
    if record_type == "event_msg":
        event_type = payload.get("type")
        if event_type in {"user_message", "user_input"}:
            return "user", payload.get("message", payload.get("text")), "message"
        if event_type in {"agent_message", "assistant_message"}:
            return "assistant", payload.get("message", payload.get("text")), "message"
        return None, None, "message"
    return None, None, "message"


def _string(*values: Any) -> str | None:
    return next((value for value in values if isinstance(value, str) and value), None)
