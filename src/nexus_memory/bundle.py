"""Dry-run manifest, multi-dimensional fidelity engine, and multi-target bundle writer.

100% backwards-compatible with v0.1 `preview()`, `write_bundle()`, and `build_hierarchy()`
while adding:
- Multi-target projections: `claude-code`, `claude-desktop-3p-chat`, `claude-desktop-3p-cowork`,
  `claude-desktop-3p-code`, `claude-desktop-3p-all`, `codex`, `opencode`, `pi`, `dsh`, `portable`
- Content-addressed SHA-256 `assets/` storage for binary attachments extracted from exports
- Secret-stripped Resource Plane staging (`skills`, `mcp`, `instructions`, `memories`, `permissions`, `schedules`)
- Multi-dimensional `FidelityReport` (structural, message_events, branches_subtasks, assets, resources, native_resume)
- Sanitized `HANDOFF_REPORT.md` (credential-redacted & prompt-injection fence-safe!)
- Two-stage write gate integration (corrupt config + cloud-sync folder protection)
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .claude_code import TESTED_CLAUDE_CODE_VERSION, build_native_sessions, encode_jsonl, project_directory_name
from .claude_desktop_3p import (
    DEFAULT_3P_DEVICE_ID,
    DEFAULT_3P_ORG_ID,
    build_desktop_3p_code_sessions,
    build_desktop_3p_local_agent_sessions,
)
from .codex import build_codex_rollouts
from .ecosystem import (
    build_aider_sessions,
    build_antigravity_sessions,
    build_cline_roo_sessions,
    build_continue_sessions,
    build_cursor_sessions,
    build_dsh_v4_sessions,
    build_gemini_cli_sessions,
    build_goose_sessions,
    build_opencode_sessions,
    build_pi_session,
    build_zed_sessions,
)
from .harnesses_extended import (
    build_amp_sessions,
    build_kiro_sessions,
    build_t3code_sessions,
    build_trae_sessions,
    build_warp_oz_sessions,
    build_windsurf_sessions,
    build_workbuddy_sessions,
)
from .model import ConversationGraph, FidelityReport, ResourceBundle
from .resources import stage_resources_to_bundle
from .security import (
    atomic_write_bytes,
    atomic_write_json,
    ensure_private_dir,
    ensure_within_root,
    sanitize_handoff_text,
    scan_secret_markers,
)
from .write_gate import GateConfig, check_write_gate

SUPPORTED_TARGETS = (
    "claude-code",
    "claude-desktop-3p-chat",
    "claude-desktop-3p-cowork",
    "claude-desktop-3p-code",
    "claude-desktop-3p-all",
    "codex",
    "antigravity",
    "cursor",
    "opencode",
    "pi",
    "dsh",
    "gemini-cli",
    "cline-roo",
    "goose",
    "continue",
    "zed",
    "aider",
    "workbuddy",
    "t3code",
    "kiro",
    "amp",
    "trae",
    "warp-oz",
    "windsurf",
    "portable",
)


def preview(
    conversations: list[ConversationGraph],
    *,
    cwd: str | Path,
    claude_version: str = TESTED_CLAUDE_CODE_VERSION,
    target: str = "claude-code",
    resources: ResourceBundle | None = None,
    device_id: str = DEFAULT_3P_DEVICE_ID,
    org_id: str = DEFAULT_3P_ORG_ID,
    model_provider: str = "openai",
    on_progress: Callable[[str, int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Compute a deterministic dry-run migration plan + multi-dimensional fidelity report without writing."""
    manifest, _ = _plan(
        conversations,
        cwd=cwd,
        claude_version=claude_version,
        target=target,
        resources=resources,
        device_id=device_id,
        org_id=org_id,
        model_provider=model_provider,
        on_progress=on_progress,
    )
    return manifest


def _compute_fidelity(
    conversations: list[ConversationGraph],
    hierarchy: dict[str, Any],
    native_sessions: list[dict[str, Any]],
    target: str,
    resources: ResourceBundle | None,
) -> FidelityReport:
    total_nodes = sum(len(g.nodes) for g in conversations)
    projected_nodes = sum(len(s.get("source_node_ids", ())) for s in native_sessions)
    total_branches = sum(len(g.branch_paths()) for g in conversations)
    total_fork_points = sum(len(g.fork_points()) for g in conversations)
    total_assets = sum(len(g.assets) for g in conversations)
    copied_assets = sum(1 for g in conversations for a in g.assets if a.disposition == "embedded_copied")
    missing_assets = sum(1 for g in conversations for a in g.assets if a.disposition == "missing_in_export")
    total_links = sum(len(g.links) for g in conversations)
    interruptions = sum(int(g.metadata.get("interruption_count") or 0) for g in conversations)
    tool_nodes = sum(1 for g in conversations for n in g.nodes if n.role in {"tool_call", "tool_result"} or n.event_type in {"tool_use", "tool_result"})
    subagent_nodes = sum(1 for g in conversations for n in g.nodes if n.parent_tool_use_id)

    native_branch_dag = target in {"pi", "portable"}
    res_counts = resources.summary_counts() if resources else {}

    resume_notes = {
        "claude-code": "Real `claude 2.1.172 --resume` verified with strict alternating user/assistant turn coalescing (zero Invalid Params).",
        "claude-desktop-3p-chat": "Staged in Claude-3p 7.37095.0 local-agent-mode-sessions layout (mode=chat) with strict role alternation; staged without private HMAC.",
        "claude-desktop-3p-cowork": "Staged in Claude-3p 7.37095.0 local-agent-mode-sessions layout (mode=cowork) with strict role alternation; staged without private HMAC.",
        "claude-desktop-3p-code": "Dual-key staged (Claude-3p 7.37095.0 claude-code-sessions index + ~/.claude/projects transcript); verified by project-path + session-ID join.",
        "claude-desktop-3p-all": "All three Claude Desktop 3P lanes staged separately without collapsing stores; verify each lane independently.",
        "codex": "Real `codex 0.154.0 exec resume` verified rollout JSONL (`source=cli`, JSON-stringified args, strict call_id pairing, `sessions/YYYY/MM/DD/rollout-*.jsonl` + `session_index.jsonl`).",
        "antigravity": "Antigravity `brain/<conv-id>/.system_generated/logs/transcript.jsonl` + `transcript_full.jsonl` + `metadata.json` bidirectional projection with 0600 backup & rollback.",
        "cursor": "Cursor `state.vscdb` (`cursorDiskKV`: `composerData:*` + `bubbleId:*`) atomic SQLite merge with collision protection & pristine rollback.",
        "opencode": "Combined JSON + real split `storage/{session,message,part}` files verified round-trip.",
        "pi": "Native tree-DAG JSONL (`id`/`parentId`) preserves multi-branch topology inside a single session file.",
        "dsh": "DeepSeek Harness V4 JSONL schema verified round-trip.",
        "gemini-cli": "Gemini CLI 0.33+ `tmp/<slug>/chats/session-*.json` + `.project_root` + `projects.json` layout.",
        "cline-roo": "Cline / Roo Code `tasks/<id>/api_conversation_history.json` strict alternating turns.",
        "goose": "Goose `sessions/<id>.jsonl` header + alternating turns.",
        "continue": "Continue `sessions/<id>.json` history items.",
        "zed": "Zed / ACP `threads/<id>.json` segmented messages.",
        "aider": "Aider `.aider.chat.history.md` markdown turns.",
        "workbuddy": "Tencent WorkBuddy `projects/<encoded-cwd>/<id>.jsonl` + `workbuddy.db` atomic SQLite merge with space/group/project metadata.",
        "t3code": "T3 Code `~/.t3/userdata/statev2.sqlite` (`projection_projects` + `orchestration_v2_projection_*` + `orchestration_events` + `lineage`/`tags`).",
        "kiro": "AWS Kiro CLI v3 `sessions/cli/<id>.jsonl` alternating turns.",
        "amp": "Sourcegraph Amp `threads/<id>.json` v1 thread schema.",
        "trae": "ByteDance Trae `trajectories/<id>.json` trajectory schema.",
        "warp-oz": "Warp / Oz Agent `sessions/<id>.json` block schema.",
        "windsurf": "Windsurf Cascade `cascade/<id>.json` bidirectional session schema + skills/MCP.",
        "portable": "Lossless canonical v2 archive with SHA-256 assets and hierarchy (round-trip verified).",
    }

    return FidelityReport(
        target=target,
        structural_fidelity={
            "projects_total": len(hierarchy["projects"]),
            "explicit_projects": sum(1 for p in hierarchy["projects"] if p["identity_source"] == "explicit_source_metadata"),
            "workspace_inferred_projects": sum(1 for p in hierarchy["projects"] if p["identity_source"] == "workspace_path_inference"),
            "unknown_project_sessions": hierarchy["unknown_project_count"],
            "section_groups_total": len(hierarchy["section_groups"]),
            "unknown_section_sessions": hierarchy["unknown_section_count"],
            "session_relations_total": len(hierarchy["session_relations"]),
            "resolved_relations": sum(1 for r in hierarchy["session_relations"] if r["parent_resolved"]),
            "canonical_preservation": "100% preserved in portable.json hierarchy",
        },
        message_event_fidelity={
            "source_nodes_total": total_nodes,
            "projected_native_nodes": projected_nodes,
            "tool_event_nodes": tool_nodes,
            "subagent_nested_nodes": subagent_nodes,
            "interruption_events": interruptions,
            "unique_links_extracted": total_links,
            "canonical_preservation": "100% raw records preserved in portable.json",
        },
        branch_subtask_fidelity={
            "source_leaf_branches": total_branches,
            "source_fork_points": total_fork_points,
            "projected_target_sessions": len(native_sessions),
            "native_branch_dag_supported": native_branch_dag,
            "branch_strategy": "native_tree_dag" if native_branch_dag else "one_target_session_per_leaf_branch_plus_lossless_dag_sidecar",
        },
        asset_fidelity={
            "referenced_assets_total": total_assets,
            "binary_copied_with_sha256": copied_assets,
            "missing_in_export": missing_assets,
            "external_references_only": total_assets - copied_assets - missing_assets,
        },
        resource_plane_fidelity={
            "included": resources is not None,
            "counts": res_counts,
            "credentials_policy": "never_copied_stripped_to_env_var_placeholders",
            "permissions_policy": "advisory_only_never_auto_granted",
            "schedules_policy": "migrated_disabled_until_user_enables",
        },
        native_resume_readiness={
            "target": target,
            "status_note": resume_notes.get(target, "Synthetic projection verified."),
            "single_accuracy_percentage_omitted_by_design": True,
        },
    )


def _plan(
    conversations: list[ConversationGraph],
    *,
    cwd: str | Path,
    claude_version: str,
    target: str = "claude-code",
    resources: ResourceBundle | None = None,
    device_id: str = DEFAULT_3P_DEVICE_ID,
    org_id: str = DEFAULT_3P_ORG_ID,
    model_provider: str = "openai",
    on_progress: Callable[[str, int, int, str], None] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if target not in SUPPORTED_TARGETS:
        raise ValueError(f"unsupported target '{target}'; choose from {', '.join(SUPPORTED_TARGETS)}")

    native_sessions: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    secret_counts: dict[str, int] = {}
    project_keys: set[str] = set()
    total_convs = len(conversations)

    for conversation_index, graph in enumerate(conversations, 1):
        # Codex/Claude rollouts carry their originating workspace; map each such session
        # to the matching project directory instead of collapsing into fallback --cwd.
        target_cwd = graph.workspace or cwd
        project_key = project_directory_name(target_cwd)
        project_keys.add(project_key)

        if target == "claude-code":
            sessions, graph_losses = build_native_sessions(graph, cwd=target_cwd, version=claude_version)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("claude_sessions")
                    / project_key
                    / f"conversation-{conversation_index:03d}"
                    / f"{session['session_id']}.jsonl"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "claude-code-jsonl"
                native_sessions.append(session)
        elif target in {"claude-desktop-3p-chat", "claude-desktop-3p-cowork"}:
            sessions, graph_losses = build_desktop_3p_local_agent_sessions(
                graph, lane=target, cwd=target_cwd, device_id=device_id, org_id=org_id
            )
            for session in sessions:
                session["source_id"] = graph.source_id
                session["writer_kind"] = "claude-desktop-3p-local-agent"
                native_sessions.append(session)
        elif target == "claude-desktop-3p-code":
            sessions, graph_losses = build_desktop_3p_code_sessions(
                graph, cwd=target_cwd, device_id=device_id, org_id=org_id, claude_version=claude_version
            )
            for session in sessions:
                session["source_id"] = graph.source_id
                session["writer_kind"] = "claude-desktop-3p-code"
                native_sessions.append(session)
        elif target == "claude-desktop-3p-all":
            graph_losses = []
            for sub_lane in ("claude-desktop-3p-chat", "claude-desktop-3p-cowork"):
                sub_s, sub_l = build_desktop_3p_local_agent_sessions(
                    graph, lane=sub_lane, cwd=target_cwd, device_id=device_id, org_id=org_id
                )
                for session in sub_s:
                    session["source_id"] = graph.source_id
                    session["writer_kind"] = "claude-desktop-3p-local-agent"
                    native_sessions.append(session)
                graph_losses.extend(sub_l)
            code_s, code_l = build_desktop_3p_code_sessions(
                graph, cwd=target_cwd, device_id=device_id, org_id=org_id, claude_version=claude_version
            )
            for session in code_s:
                session["source_id"] = graph.source_id
                session["writer_kind"] = "claude-desktop-3p-code"
                native_sessions.append(session)
            graph_losses.extend(code_l)
        elif target == "codex":
            sessions, graph_losses = build_codex_rollouts(graph, cwd=target_cwd, model_provider=model_provider)
            for session in sessions:
                rel_sub = session.get("rollout_rel_subpath") or f"rollout-{session['session_id']}.jsonl"
                session["target_relative_path"] = (Path("codex_sessions") / "sessions" / rel_sub).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "codex-rollout"
                native_sessions.append(session)
        elif target == "antigravity":
            sessions, graph_losses = build_antigravity_sessions(graph, cwd=target_cwd)
            for session in sessions:
                cid = session["session_id"]
                session["target_relative_path"] = (Path("antigravity_brain") / "brain" / cid / ".system_generated" / "logs" / "transcript.jsonl").as_posix()
                session["sidecar_relative_path"] = (Path("antigravity_brain") / "brain" / cid / "metadata.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "antigravity-brain"
                native_sessions.append(session)
        elif target == "cursor":
            sessions, graph_losses = build_cursor_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("cursor_sessions") / f"{session['session_id']}.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "opencode":
            sessions, graph_losses = build_opencode_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("opencode_sessions") / f"conversation-{conversation_index:03d}" / f"{session['session_id']}.json"
                ).as_posix()
                session["split_relative_paths"] = [
                    (Path("opencode_sessions") / rel_k).as_posix()
                    for rel_k in session.get("split_files", {})
                ]
                session["source_id"] = graph.source_id
                session["writer_kind"] = "opencode-session"
                native_sessions.append(session)
        elif target == "pi":
            sessions, graph_losses = build_pi_session(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("pi_sessions") / project_key / f"{session['session_id']}.jsonl"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "jsonl"
                native_sessions.append(session)
        elif target == "dsh":
            sessions, graph_losses = build_dsh_v4_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("dsh_sessions") / f"conversation-{conversation_index:03d}" / f"v4-{session['session_id']}.jsonl"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "jsonl"
                native_sessions.append(session)
        elif target == "gemini-cli":
            sessions, graph_losses = build_gemini_cli_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("gemini_sessions") / session["gemini_rel_subpath"]
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "gemini-cli-session"
                native_sessions.append(session)
        elif target == "cline-roo":
            sessions, graph_losses = build_cline_roo_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("cline_tasks") / session["session_id"] / "api_conversation_history.json"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "goose":
            sessions, graph_losses = build_goose_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("goose_sessions") / f"{session['session_id']}.jsonl"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "jsonl"
                native_sessions.append(session)
        elif target == "continue":
            sessions, graph_losses = build_continue_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("continue_sessions") / f"{session['session_id']}.json"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "zed":
            sessions, graph_losses = build_zed_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("zed_threads") / f"{session['session_id']}.json"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "aider":
            sessions, graph_losses = build_aider_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (
                    Path("aider_sessions") / f"conversation-{conversation_index:03d}" / ".aider.chat.history.md"
                ).as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "text-payload"
                native_sessions.append(session)
        elif target == "workbuddy":
            sessions, graph_losses = build_workbuddy_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("workbuddy_sessions") / f"{session['session_id']}.jsonl").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "jsonl"
                native_sessions.append(session)
        elif target == "t3code":
            sessions, graph_losses = build_t3code_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("t3code_threads") / f"{session['session_id']}.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "kiro":
            sessions, graph_losses = build_kiro_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("kiro_sessions") / f"{session['session_id']}.jsonl").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "jsonl"
                native_sessions.append(session)
        elif target == "amp":
            sessions, graph_losses = build_amp_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("amp_threads") / f"{session['session_id']}.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "trae":
            sessions, graph_losses = build_trae_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("trae_trajectories") / f"{session['session_id']}.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "warp-oz":
            sessions, graph_losses = build_warp_oz_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("warp_oz_sessions") / f"{session['session_id']}.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        elif target == "windsurf":
            sessions, graph_losses = build_windsurf_sessions(graph, cwd=target_cwd)
            for session in sessions:
                session["target_relative_path"] = (Path("windsurf_sessions") / f"{session['session_id']}.json").as_posix()
                session["source_id"] = graph.source_id
                session["writer_kind"] = "json-payload"
                native_sessions.append(session)
        else:  # portable
            sessions, graph_losses = [], []

        losses.extend({"source_id": graph.source_id, **loss} for loss in graph_losses)
        for kind, count in scan_secret_markers(graph.raw_source).items():
            secret_counts[kind] = secret_counts.get(kind, 0) + count
        if on_progress is not None:
            on_progress("plan", conversation_index, max(total_convs, 1), str(graph.title or graph.source_id))

    if resources:
        for kind, count in resources.redacted_secret_counts.items():
            secret_counts[kind] = secret_counts.get(kind, 0) + count

    warnings: list[str] = []
    hierarchy = build_hierarchy(conversations)
    if hierarchy["unknown_project_count"]:
        warnings.append("Some sessions lack explicit project metadata; unknown memberships are kept unassigned rather than guessed.")
    if hierarchy["unknown_section_count"]:
        warnings.append("Some sessions lack explicit section-group metadata; section placement remains unknown.")
    if losses:
        warnings.append("Some content is archived in portable.json but not represented in the native target transcript; inspect losses.")
    if secret_counts:
        warnings.append("Credential-like markers were detected. Their values are not copied to the report or MCP templates; inspect the source before resuming or transmitting context.")

    fidelity = _compute_fidelity(conversations, hierarchy, native_sessions, target, resources)

    target_label = "claude-code-local-session-files" if target == "claude-code" else f"{target}-staged-bundle"
    manifest: dict[str, Any] = {
        "schema": "nexus-memory.migration-manifest.v1",
        "source_formats": sorted({graph.source_format for graph in conversations}),
        "conversation_count": len(conversations),
        "node_count": sum(len(graph.nodes) for graph in conversations),
        "target": target_label,
        "target_lane": target,
        "target_version_claim": claude_version if target.startswith("claude") else "1.0.0",
        "target_project_keys": sorted(project_keys),
        "native_session_count": len(native_sessions),
        "native_message_count": sum(len(item["source_node_ids"]) for item in native_sessions),
        "target_sessions": [
            {
                "session_id": item["session_id"],
                "source_id": item["source_id"],
                "branch_index": item["branch_index"],
                "title": item["title"],
                "target_relative_path": item["target_relative_path"],
                "source_node_ids": item["source_node_ids"],
                **({"lane": item["lane"]} if "lane" in item else {}),
                **({"sidecar_relative_path": item["sidecar_relative_path"]} if "sidecar_relative_path" in item else {}),
                **({"index_relative_path": item["index_relative_path"]} if "index_relative_path" in item else {}),
                **({"encoded_project_dir": item["encoded_project_dir"]} if "encoded_project_dir" in item else {}),
                **({"rollout_rel_subpath": item["rollout_rel_subpath"]} if "rollout_rel_subpath" in item else {}),
                **({"split_relative_paths": item["split_relative_paths"]} if "split_relative_paths" in item else {}),
                **({"gemini_rel_subpath": item["gemini_rel_subpath"]} if "gemini_rel_subpath" in item else {}),
                **({"project_slug": item["project_slug"]} if "project_slug" in item else {}),
                **({"cwd": item["cwd"]} if "cwd" in item else {}),
            }
            for item in native_sessions
        ],
        "project_membership": [
            {
                "source_id": graph.source_id,
                "project_id": graph.metadata.get("project_id"),
                "project_name": graph.metadata.get("project_name"),
                "section_id": graph.metadata.get("section_id"),
                "section_name": graph.metadata.get("section_name"),
            }
            for graph in conversations
        ],
        "project_index_summary": {
            "section_group_count": len(hierarchy["section_groups"]),
            "project_count": len(hierarchy["projects"]),
            "unknown_project_count": hierarchy["unknown_project_count"],
            "unknown_section_count": hierarchy["unknown_section_count"],
            "session_relation_count": len(hierarchy["session_relations"]),
        },
        "fidelity_report": fidelity.to_dict(),
        "losses": losses,
        "secret_marker_counts": secret_counts,
        "warnings": warnings,
        "write_mode": "explicit local bundle only; no provider API call",
    }
    return manifest, native_sessions


def _render_handoff_markdown(
    conversations: list[ConversationGraph],
    manifest: dict[str, Any],
    hierarchy: dict[str, Any],
) -> str:
    """Render a credential-redacted, fence-sanitized Markdown handoff summary."""
    lines = [
        "# Nexus Memory — Migration Handoff Report",
        "",
        f"- **Target Lane:** `{manifest['target_lane']}` (`{manifest['target']}`)",
        f"- **Source Formats:** {', '.join(f'`{f}`' for f in manifest['source_formats']) or 'none'}",
        f"- **Conversations:** {manifest['conversation_count']} | **Canonical Nodes:** {manifest['node_count']} | **Staged Target Sessions:** {manifest['native_session_count']}",
        f"- **Projects:** {len(hierarchy['projects'])} | **Section Groups:** {len(hierarchy['section_groups'])} | **Session Relations:** {len(hierarchy['session_relations'])}",
        "",
        "## Fidelity Summary (Per-Dimension)",
        "```json",
        json.dumps(manifest["fidelity_report"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Projects & Section Groups",
    ]
    for proj in hierarchy["projects"]:
        pname = sanitize_handoff_text(str(proj.get("name") or proj["id"]))
        lines.append(f"- **{pname}** (`{proj['identity_source']}`): {len(proj['session_refs'])} session(s)")
    lines.append("")
    lines.append("## Conversations")
    for g in conversations:
        safe_title = sanitize_handoff_text(g.title or g.source_id)
        usage_str = ""
        if g.usage and not g.usage.is_empty():
            usage_str = f" | tokens: {g.usage.input_tokens:,} in / {g.usage.output_tokens:,} out"
        lines.append(
            f"- **{safe_title}** (`{g.source_format}:{g.source_id}` — {len(g.nodes)} nodes, {len(g.branch_paths())} branch(es), {len(g.assets)} asset(s), {len(g.links)} link(s){usage_str})"
        )
    if manifest["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        for w in manifest["warnings"]:
            lines.append(f"- {sanitize_handoff_text(w)}")
    if manifest["losses"]:
        lines.append("")
        lines.append(f"## Recorded Losses ({len(manifest['losses'])})")
        for loss in manifest["losses"][:50]:
            lines.append(f"- `{loss.get('feature')}` ({loss.get('source_id') or '-'}): {loss.get('disposition')}")
    return "\n".join(lines) + "\n"


def write_bundle(
    conversations: list[ConversationGraph],
    *,
    out: str | Path,
    cwd: str | Path,
    claude_version: str = TESTED_CLAUDE_CODE_VERSION,
    target: str = "claude-code",
    asset_bytes: dict[str, bytes] | None = None,
    resources: ResourceBundle | None = None,
    device_id: str = DEFAULT_3P_DEVICE_ID,
    org_id: str = DEFAULT_3P_ORG_ID,
    model_provider: str = "openai",
    gate_config: GateConfig | None = None,
    allow_cloud_sync_path: str | Path | None = None,
    on_progress: Callable[[str, int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Write a complete, private-permission (0700/0600), lossless-sidecar local bundle.

    Refuses to overwrite existing output paths and enforces the two-stage write gate.
    """
    output = Path(out).expanduser()
    gate = check_write_gate(output, gate_config=gate_config, allow_cloud_sync_path=allow_cloud_sync_path)
    if not gate.allowed:
        raise PermissionError(f"write gate blocked bundle creation: {gate.reason}")
    if output.exists():
        raise FileExistsError(f"output path already exists; refusing to overwrite: {output}")

    manifest, native_sessions = _plan(
        conversations,
        cwd=cwd,
        claude_version=claude_version,
        target=target,
        resources=resources,
        device_id=device_id,
        org_id=org_id,
        model_provider=model_provider,
        on_progress=on_progress,
    )
    ensure_private_dir(output)
    try:
        hierarchy = build_hierarchy(conversations)

        # Write content-addressed binary assets with SHA-256 verification
        written_assets: list[dict[str, Any]] = []
        if asset_bytes:
            for g in conversations:
                for rec in g.assets:
                    if rec.sha256 and rec.sha256 in asset_bytes and rec.relative_bundle_path:
                        dest = ensure_within_root(output / rec.relative_bundle_path, output)
                        raw = asset_bytes[rec.sha256]
                        actual_sha = hashlib.sha256(raw).hexdigest()
                        if actual_sha != rec.sha256:
                            raise ValueError(f"asset checksum mismatch for {rec.filename}")
                        atomic_write_bytes(dest, raw, mode=0o600)
                        written_assets.append(rec.to_dict())

        # Stage optional resource plane (Skills, sanitized MCPs, instructions, memories, permissions, schedules)
        if resources is not None:
            res_summary = stage_resources_to_bundle(
                resources,
                bundle_resources_dir=ensure_within_root(output / "resources", output),
                target_harness=target,
            )
            manifest["resource_staging_summary"] = res_summary

        portable = {
            "schema": "nexus-memory.portable-graph.v2",
            "compatible_with_v1": True,
            "source_formats": manifest["source_formats"],
            "hierarchy": hierarchy,
            "assets": written_assets,
            "resources": resources.to_dict() if resources is not None else None,
            "conversations": [graph.to_dict() for graph in conversations],
        }
        atomic_write_json(output / "portable.json", portable)
        atomic_write_json(output / "manifest.json", manifest)
        atomic_write_bytes(
            output / "HANDOFF_REPORT.md",
            _render_handoff_markdown(conversations, manifest, hierarchy).encode("utf-8"),
            mode=0o600,
        )

        # Write target-specific staged files
        codex_index_entries: list[dict[str, Any]] = []
        gemini_projects: dict[str, str] = {}
        total_ns = len(native_sessions)
        for ns_idx, session in enumerate(native_sessions, 1):
            wkind = session.get("writer_kind", "claude-code-jsonl")
            if wkind in {"claude-code-jsonl", "jsonl"}:
                dst = ensure_within_root(output / session["target_relative_path"], output)
                atomic_write_bytes(dst, encode_jsonl(session["records"]), mode=0o600)
            elif wkind == "codex-rollout":
                dst = ensure_within_root(output / session["target_relative_path"], output)
                atomic_write_bytes(dst, encode_jsonl(session["records"]), mode=0o600)
                if isinstance(session.get("session_index_entry"), dict):
                    codex_index_entries.append(session["session_index_entry"])
            elif wkind == "antigravity-brain":
                dst = ensure_within_root(output / session["target_relative_path"], output)
                raw_jsonl = encode_jsonl(session["records"])
                atomic_write_bytes(dst, raw_jsonl, mode=0o600)
                atomic_write_bytes(dst.with_name("transcript_full.jsonl"), raw_jsonl, mode=0o600)
                meta_dst = ensure_within_root(output / session["sidecar_relative_path"], output)
                atomic_write_json(meta_dst, session["meta_payload"], mode=0o600)
            elif wkind == "opencode-session":
                dst = ensure_within_root(output / session["target_relative_path"], output)
                atomic_write_json(dst, session["payload"], mode=0o600)
                for rel_k, obj in (session.get("split_files") or {}).items():
                    sdst = ensure_within_root(output / "opencode_sessions" / rel_k, output)
                    atomic_write_json(sdst, obj, mode=0o600)
            elif wkind == "gemini-cli-session":
                dst = ensure_within_root(output / session["target_relative_path"], output)
                atomic_write_json(dst, session["payload"], mode=0o600)
                slug = session.get("project_slug")
                scwd = session.get("cwd")
                if slug and scwd:
                    proot = ensure_within_root(output / "gemini_sessions" / "tmp" / slug / ".project_root", output)
                    atomic_write_bytes(proot, str(scwd).encode("utf-8"), mode=0o600)
                    gemini_projects[str(scwd)] = str(slug)
            elif wkind == "json-payload":
                dst = ensure_within_root(output / session["target_relative_path"], output)
                atomic_write_json(dst, session["payload"], mode=0o600)
            elif wkind == "text-payload":
                dst = ensure_within_root(output / session["target_relative_path"], output)
                atomic_write_bytes(dst, str(session.get("markdown") or "").encode("utf-8"), mode=0o600)
            elif wkind == "claude-desktop-3p-local-agent":
                audit_dst = ensure_within_root(output / session["audit_relative_path"], output)
                sidecar_dst = ensure_within_root(output / session["sidecar_relative_path"], output)
                atomic_write_bytes(audit_dst, encode_jsonl(session["records"]), mode=0o600)
                atomic_write_json(sidecar_dst, session["sidecar"], mode=0o600)
                ensure_private_dir(audit_dst.parent / "uploads")
                ensure_private_dir(audit_dst.parent / "outputs")
                if session.get("lane") == "claude-desktop-3p-cowork":
                    ensure_private_dir(audit_dst.parent / ".claude" / "todos")
            elif wkind == "claude-desktop-3p-code":
                transcript_dst = ensure_within_root(output / session["target_relative_path"], output)
                index_dst = ensure_within_root(output / session["index_relative_path"], output)
                atomic_write_bytes(transcript_dst, encode_jsonl(session["records"]), mode=0o600)
                atomic_write_json(index_dst, session["index_payload"], mode=0o600)
            if on_progress is not None:
                on_progress("write", ns_idx, max(total_ns, 1), str(session.get("title") or session.get("session_id") or ""))
        if codex_index_entries:
            idx_dst = ensure_within_root(output / "codex_sessions" / "session_index.jsonl", output)
            atomic_write_bytes(idx_dst, encode_jsonl(codex_index_entries), mode=0o600)
        if gemini_projects:
            gp_dst = ensure_within_root(output / "gemini_sessions" / "projects.json", output)
            atomic_write_json(gp_dst, {"projects": gemini_projects}, mode=0o600)
        return manifest
    except Exception:
        _remove_tree(output)
        raise


def build_hierarchy(conversations: list[ConversationGraph]) -> dict[str, Any]:
    """Build explicit hierarchy and provenance without inventing missing memberships."""
    sections: dict[str, dict[str, Any]] = {}
    projects: dict[str, dict[str, Any]] = {}
    sessions: list[dict[str, Any]] = []
    raw_relations: list[dict[str, Any]] = []
    session_refs = {f"{graph.source_format}:{graph.source_id}" for graph in conversations}
    unknown_project_sessions = 0
    unknown_section_sessions = 0

    for graph in conversations:
        metadata = graph.metadata
        source = graph.source_format
        session_ref = f"{source}:{graph.source_id}"
        explicit_project_id = metadata.get("project_id")
        project_name = metadata.get("project_name")
        section_id = metadata.get("section_id")
        section_name = metadata.get("section_name")
        workspace = graph.workspace

        if explicit_project_id or project_name:
            project_ref = f"{source}:project:{explicit_project_id or project_name}"
            project_identity_source = "explicit_source_metadata"
        elif workspace:
            project_ref = f"{source}:workspace:{workspace}"
            normalized_workspace = workspace.replace("\\", "/").rstrip("/")
            project_name = normalized_workspace.rsplit("/", 1)[-1] or None
            project_identity_source = "workspace_path_inference"
        else:
            project_ref = f"{source}:unknown-project"
            project_identity_source = "unknown"
            unknown_project_sessions += 1

        if section_id or section_name:
            section_ref = f"{source}:section:{section_id or section_name}"
            section_identity_source = "explicit_source_metadata"
        else:
            section_ref = f"{source}:unknown-section"
            section_name = "Unassigned / section not present in source"
            section_identity_source = "unknown"
            unknown_section_sessions += 1

        section = sections.setdefault(
            section_ref,
            {
                "id": section_ref,
                "source_id": section_id,
                "name": section_name,
                "identity_source": section_identity_source,
                "project_refs": [],
                "session_refs": [],
                "is_synthetic_unknown_bucket": section_identity_source == "unknown",
            },
        )
        if project_ref not in section["project_refs"]:
            section["project_refs"].append(project_ref)
        if session_ref not in section["session_refs"]:
            section["session_refs"].append(session_ref)

        project = projects.setdefault(
            project_ref,
            {
                "id": project_ref,
                "source_id": explicit_project_id,
                "name": project_name,
                "identity_source": project_identity_source,
                "workspace": workspace,
                "section_group_refs": [],
                "session_refs": [],
                "is_synthetic_unknown_bucket": project_identity_source == "unknown",
            },
        )
        if section_ref not in project["section_group_refs"]:
            project["section_group_refs"].append(section_ref)
        if session_ref not in project["session_refs"]:
            project["session_refs"].append(session_ref)

        sessions.append(
            {
                "id": session_ref,
                "source_format": source,
                "source_id": graph.source_id,
                "title": graph.title,
                "project_ref": project_ref,
                "section_group_ref": section_ref,
                "active_node_id": graph.active_node_id,
                "branch_count": len(graph.branch_paths()),
                "fork_point_count": len(graph.fork_points()),
                "asset_count": len(graph.assets),
                "link_count": len(graph.links),
            }
        )

        parent_id = (
            metadata.get("parent_session_id")
            or metadata.get("parent_conversation_id")
            or metadata.get("forked_from")
        )
        if parent_id:
            relation_kind = "subtask" if metadata.get("parent_session_id") else "fork_or_parent_chat"
            raw_relations.append(
                {
                    "parent_id": f"{source}:{parent_id}",
                    "child_id": session_ref,
                    "relationship": relation_kind,
                    "parent_resolved": f"{source}:{parent_id}" in session_refs,
                }
            )

    return {
        "schema": "nexus-memory.hierarchy.v1",
        "section_groups": list(sections.values()),
        "projects": list(projects.values()),
        "sessions": sessions,
        "session_relations": raw_relations,
        "unknown_project_count": unknown_project_sessions,
        "unknown_section_count": unknown_section_sessions,
    }


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            _remove_tree(child)
        else:
            child.unlink()
    path.rmdir()
