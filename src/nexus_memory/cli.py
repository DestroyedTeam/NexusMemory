"""Unified CLI for Nexus Memory — deterministic cross-Harness portability without AI guesswork.

Subcommands:
- `discover`  : Read-only detection of installed Harnesses, session stores, Skills, and MCP configs
- `inspect`   : Read-only inspection of any supported Harness export/store (with project/section filters)
- `convert`   : Dry-run by default; `--write` creates a lossless-sidecar local migration bundle
- `apply`     : Dry-run by default; `--apply` executes transactional write with backup & readback verify
- `verify`    : Verifies bundle integrity, asset SHA-256s, secret redaction, or applied transactions
- `rollback`  : Restores exact pre-apply pristine snapshot and verifies SHA-256 equality
- `matrix`    : Prints the deterministic Cross-Harness Compatibility & Fidelity Matrix (JSON/Markdown)
- `resources` : Scans and exports secret-stripped Skills, MCP servers, instructions, memories, permissions, schedules
- `viewer`    : Launches the hardened `127.0.0.1` offline bundle viewer
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Sequence

from . import __version__
from .bundle import SUPPORTED_TARGETS, preview, write_bundle
from .chatgpt import filter_conversations
from .claude_code import TESTED_CLAUDE_CODE_VERSION
from .claude_desktop_3p import DEFAULT_3P_DEVICE_ID, DEFAULT_3P_ORG_ID
from .discovery import discover_harnesses
from .ecosystem import load_any_source
from .matrix import build_matrix_data, evaluate_pair, render_matrix_markdown
from .resources import scan_resources, stage_resources_to_bundle
from .transaction import apply_bundle, rollback_transaction, verify_bundle, verify_transaction
from .viewer import serve_bundle
from .write_gate import load_gate_config


def load_conversations(path: str | Path, *, source_format: str | None = None, claude_dir: str | Path | None = None):
    graphs, _ = load_any_source(path, source_format=source_format, claude_dir=claude_dir)
    return graphs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-memory",
        description="Local-first, deterministic, loss-aware portability across AI agent Harnesses.",
    )
    parser.add_argument("--version", action="version", version=f"nexus-memory {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover
    p_disc = subparsers.add_parser("discover", help="read-only auto-discovery of local Harnesses and resource roots")
    p_disc.add_argument("--home", type=Path, default=None, help="override HOME directory (useful for isolated probes)")
    p_disc.add_argument("--project", type=Path, default=None, help="optional project workspace to inspect for markers")
    p_disc.add_argument("--platform", choices=["darwin", "win32", "linux"], default=None)

    # inspect
    p_insp = subparsers.add_parser("inspect", help="read and summarize any supported Harness source without writing")
    p_insp.add_argument("source", type=Path)
    p_insp.add_argument("--from", dest="source_format", default="auto", help="explicit source format (default: auto)")
    p_insp.add_argument("--claude-dir", type=Path, default=None, help="optional ~/.claude root for Desktop 3P Code join")
    p_insp.add_argument("--project", default=None, help="filter by project name/ID (e.g. 'Destruction Era')")
    p_insp.add_argument("--section", default=None, help="filter by section group name/ID")
    p_insp.add_argument("--query", default=None, help="filter by title/message substring")
    p_insp.add_argument("--session-id", default=None, help="filter by session ID prefix")
    p_insp.add_argument("--limit", type=int, default=None, help="maximum conversations to load/return")

    # convert
    p_conv = subparsers.add_parser("convert", help="preview by default; --write creates a local bundle")
    p_conv.add_argument("source", type=Path)
    p_conv.add_argument("--from", dest="source_format", default="auto", help="explicit source format (default: auto)")
    p_conv.add_argument("--to", choices=list(SUPPORTED_TARGETS), required=True)
    p_conv.add_argument("--cwd", type=Path, default=Path.cwd())
    p_conv.add_argument("--out", type=Path, required=True)
    p_conv.add_argument("--claude-version", default=TESTED_CLAUDE_CODE_VERSION)
    p_conv.add_argument("--claude-dir", type=Path, default=None)
    p_conv.add_argument("--model-provider", default="openai", help="Codex target model_provider in session_meta (default: openai)")
    p_conv.add_argument("--device-id", default=DEFAULT_3P_DEVICE_ID, help="Claude Desktop 3P device ant-did scope")
    p_conv.add_argument("--org-id", default=DEFAULT_3P_ORG_ID, help="Claude Desktop 3P organization scope")
    p_conv.add_argument("--project", default=None, help="filter by project name/ID (e.g. 'Destruction Era')")
    p_conv.add_argument("--section", default=None, help="filter by section group name/ID")
    p_conv.add_argument("--query", default=None, help="filter by title/message substring")
    p_conv.add_argument("--session-id", default=None, help="filter by session ID prefix")
    p_conv.add_argument("--limit", type=int, default=None, help="maximum conversations to load/convert")
    p_conv.add_argument("--include-resources", action="store_true", help="also scan & stage secret-stripped Skills/MCP/Instructions")
    p_conv.add_argument("--resources-home", type=Path, default=None, help="HOME root for --include-resources scan")
    p_conv.add_argument("--config", type=Path, default=None, help="optional Nexus Memory config.json for write gate")
    p_conv.add_argument("--allow-cloud-sync-path", type=Path, default=None, help="explicit opt-in path when target is cloud-synced")
    p_conv.add_argument("--write", action="store_true", help="create the local bundle; otherwise print preview plan")

    # apply
    p_app = subparsers.add_parser("apply", help="dry-run by default; --apply transactionally installs bundle with backup")
    p_app.add_argument("bundle", type=Path)
    p_app.add_argument("--target-root", type=Path, required=True, help="target Harness data directory (e.g. ~/.claude or Claude-3p)")
    p_app.add_argument("--claude-dir", type=Path, default=None, help="target ~/.claude dir when applying claude-desktop-3p-code")
    p_app.add_argument("--tx-dir", type=Path, default=None, help="custom transaction journal & pristine backup directory")
    p_app.add_argument("--on-collision", choices=["refuse", "skip", "rename"], default="refuse")
    p_app.add_argument("--include-skills", action="store_true", help="also install staged bundle skills into target")
    p_app.add_argument("--config", type=Path, default=None)
    p_app.add_argument("--allow-cloud-sync-path", type=Path, default=None)
    p_app.add_argument("--apply", action="store_true", help="execute transactional writes (default is dry-run)")

    # verify
    p_ver = subparsers.add_parser("verify", help="verify a canonical bundle OR an applied transaction journal")
    p_ver.add_argument("target", type=Path, help="path to bundle directory or transaction directory")

    # rollback
    p_rb = subparsers.add_parser("rollback", help="restore target directory from an applied transaction's pristine backup")
    p_rb.add_argument("tx_dir", type=Path, help="path to transaction directory or transaction.json")

    # matrix
    p_mat = subparsers.add_parser("matrix", help="print deterministic Cross-Harness Compatibility & Fidelity Matrix")
    p_mat.add_argument("--format", choices=["json", "markdown"], default="markdown")
    p_mat.add_argument("--from", dest="from_harness", default=None, help="evaluate a specific source harness ID")
    p_mat.add_argument("--to", dest="to_harness", default=None, help="evaluate a specific target harness ID")

    # resources
    p_res = subparsers.add_parser("resources", help="scan or stage secret-stripped Skills, MCPs, instructions, memory, schedules")
    p_res.add_argument("--home", type=Path, default=None)
    p_res.add_argument("--project", type=Path, default=None)
    p_res.add_argument("--target", default="claude-code", help="target harness for staged skill deployment mode")
    p_res.add_argument("--stage-out", type=Path, default=None, help="optional directory to stage sanitized resources")

    # viewer
    p_view = subparsers.add_parser("viewer", help="launch hardened 127.0.0.1 offline bundle viewer")
    p_view.add_argument("bundle", type=Path)
    p_view.add_argument("--port", type=int, default=8765)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "discover":
            result = discover_harnesses(home=args.home, project_dir=args.project, platform=args.platform)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "matrix":
            if args.from_harness and args.to_harness:
                pair = evaluate_pair(args.from_harness, args.to_harness)
                print(json.dumps(pair, ensure_ascii=False, indent=2))
                return 0
            if args.format == "markdown":
                print(render_matrix_markdown(), end="")
            else:
                print(json.dumps(build_matrix_data(), ensure_ascii=False, indent=2))
            return 0

        if args.command == "resources":
            res = scan_resources(home=args.home, project_dir=args.project)
            payload: dict[str, object] = {"summary": res.summary_counts(), "resources": res.to_dict()}
            if args.stage_out:
                payload["staged"] = stage_resources_to_bundle(
                    res, bundle_resources_dir=args.stage_out.expanduser(), target_harness=args.target
                )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "viewer":
            serve_bundle(args.bundle, port=args.port)
            return 0

        if args.command == "verify":
            target_p = args.target.expanduser()
            if (target_p / "transaction.json").is_file() or target_p.name == "transaction.json":
                result = verify_transaction(target_p)
            else:
                result = verify_bundle(target_p)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("ok") else 1

        if args.command == "rollback":
            result = rollback_transaction(args.tx_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("ok") else 1

        if args.command == "apply":
            gate_cfg = load_gate_config(args.config)
            result = apply_bundle(
                args.bundle,
                target_root=args.target_root,
                claude_dir=args.claude_dir,
                tx_dir=args.tx_dir,
                apply=args.apply,
                on_collision=args.on_collision,
                include_skills=args.include_skills,
                gate_config=gate_cfg,
                allow_cloud_sync_path=args.allow_cloud_sync_path,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "inspect":
            conversations, _ = load_any_source(
                args.source,
                source_format=args.source_format,
                claude_dir=args.claude_dir,
                section_filter=args.section,
                project_filter=args.project,
                limit=args.limit,
            )
            conversations = filter_conversations(
                conversations,
                project=args.project,
                section=args.section,
                query=args.query,
                session_id=args.session_id,
            )
            if args.limit:
                conversations = conversations[: args.limit]
            result = {
                "source": str(args.source.expanduser()),
                "conversation_count": len(conversations),
                "conversations": [
                    {
                        "source_id": graph.source_id,
                        "title": graph.title,
                        "source_format": graph.source_format,
                        "app_mode": graph.app_mode,
                        "workspace": graph.workspace,
                        "node_count": len(graph.nodes),
                        "branch_count": len(graph.branch_paths()),
                        "fork_point_count": len(graph.fork_points()),
                        "asset_count": len(graph.assets),
                        "link_count": len(graph.links),
                        "active_node_id": graph.active_node_id,
                        "project_id": graph.metadata.get("project_id"),
                        "project_name": graph.metadata.get("project_name"),
                        "section_name": graph.metadata.get("section_name"),
                        "usage": graph.usage.to_dict() if graph.usage else None,
                    }
                    for graph in conversations
                ],
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "convert":
            conversations, asset_bytes = load_any_source(
                args.source,
                source_format=args.source_format,
                claude_dir=args.claude_dir,
                section_filter=args.section,
                project_filter=args.project,
                limit=args.limit,
            )
            conversations = filter_conversations(
                conversations,
                project=args.project,
                section=args.section,
                query=args.query,
                session_id=args.session_id,
            )
            if args.limit:
                conversations = conversations[: args.limit]
            res_bundle = (
                scan_resources(home=args.resources_home, project_dir=args.cwd)
                if args.include_resources
                else None
            )
            gate_cfg = load_gate_config(args.config)
            if args.write:
                result = write_bundle(
                    conversations,
                    out=args.out,
                    cwd=args.cwd,
                    claude_version=args.claude_version,
                    target=args.to,
                    asset_bytes=asset_bytes,
                    resources=res_bundle,
                    device_id=args.device_id,
                    org_id=args.org_id,
                    model_provider=args.model_provider,
                    gate_config=gate_cfg,
                    allow_cloud_sync_path=args.allow_cloud_sync_path,
                )
                result = {**result, "written_to": str(args.out.expanduser().resolve())}
            else:
                result = {
                    **preview(
                        conversations,
                        cwd=args.cwd,
                        claude_version=args.claude_version,
                        target=args.to,
                        resources=res_bundle,
                        device_id=args.device_id,
                        org_id=args.org_id,
                        model_provider=args.model_provider,
                    ),
                    "preview_only": True,
                    "proposed_output": str(args.out.expanduser().resolve()),
                }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        raise AssertionError("unreachable command")
    except (OSError, ValueError, PermissionError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
