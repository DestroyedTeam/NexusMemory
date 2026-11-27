"""Transactional Apply, Verify, and Hash-Verified Rollback Engine.

Safety invariants (distilled from 326 audited repos):
- Dry-run by default (`apply=False`); mutates nothing unless `--apply` is explicitly supplied.
- Enforces two-stage write gate (`corrupt_config` + `cloud_sync_gate`).
- Strict path containment (`ensure_within_root`) on every source and destination path.
- Collision policy defaults to `refuse` (never silently overwrites/merges existing sessions).
- Pre-apply pristine backup tar.gz (`0o600`) + pre-apply tree SHA-256 + `transaction.json` (`0o600`).
- Atomic temp-file + `os.replace` writes (`0o600`).
- Immediate post-write readback verification (including dual-key Claude Desktop 3P Code check
  preventing wrong-project basename false positives!).
- Exact rollback restoring pre-apply pristine tree hash.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .claude_desktop_3p import verify_desktop_3p_code_join
from .lifecycle import (
    DEFAULT_MAX_KEEP_TRANSACTIONS,
    cleanup_transaction_backup,
    prune_reclaimable_storage,
    reclaim_memory,
)
from .security import (
    atomic_copy_file,
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_stream,
    ensure_private_dir,
    ensure_within_root,
    scan_secret_markers,
    sha256_file,
)
from .write_gate import GateConfig, check_write_gate


def _read_first_nonempty_line(path: Path) -> str:
    """Read only the first non-empty line without loading a potentially huge JSONL file into RAM."""
    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped:
                return stripped
    return "{}"


def compute_tree_sha256(root: str | Path) -> tuple[int, str]:
    """Compute deterministic `(file_count, sha256_hex)` over all regular files in `root` using streaming I/O."""
    base = Path(root).expanduser()
    h = hashlib.sha256()
    if not base.exists():
        return 0, h.hexdigest()
    files = sorted(p for p in base.rglob("*") if p.is_file() and not p.is_symlink())
    for fp in files:
        rel = fp.relative_to(base).as_posix().encode("utf-8")
        h.update(rel + b"\x00" + bytes.fromhex(sha256_file(fp)) + b"\n")
    return len(files), h.hexdigest()


def verify_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    """Verify canonical bundle integrity: manifest, portable graph, asset SHA-256s, secret redaction, staged sessions."""
    root = Path(bundle_dir).expanduser().resolve()
    errors: list[str] = []
    checks: dict[str, Any] = {}

    manifest_p = root / "manifest.json"
    portable_p = root / "portable.json"
    if not manifest_p.is_file():
        errors.append("missing manifest.json")
    if not portable_p.is_file():
        errors.append("missing portable.json")
    if errors:
        return {"ok": False, "bundle": str(root), "errors": errors, "checks": checks}

    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    portable = json.loads(portable_p.read_text(encoding="utf-8"))
    checks["schema_manifest"] = manifest.get("schema")
    checks["schema_portable"] = portable.get("schema")

    # 1. Verify every staged target session file exists inside bundle root and parses cleanly
    verified_sessions = 0
    for sess in manifest.get("target_sessions", []):
        rel = sess.get("target_relative_path")
        if not rel:
            continue
        try:
            fp = ensure_within_root(root / rel, root)
        except ValueError as exc:
            errors.append(f"unsafe target_relative_path {rel}: {exc}")
            continue
        if not fp.is_file():
            errors.append(f"missing staged session file: {rel}")
            continue
        if fp.suffix == ".jsonl":
            with fp.open("r", encoding="utf-8") as fh:
                for ln, line in enumerate(fh, 1):
                    if line.strip():
                        try:
                            json.loads(line)
                        except json.JSONDecodeError as exc:
                            errors.append(f"corrupt JSONL in {rel}:{ln}: {exc.msg}")
        elif fp.suffix == ".json":
            try:
                with fp.open("r", encoding="utf-8") as fh:
                    json.load(fh)
            except json.JSONDecodeError as exc:
                errors.append(f"corrupt JSON in {rel}: {exc.msg}")

        # Verify companion sidecar / index / UI files if present
        for extra_key in ("sidecar_relative_path", "index_relative_path", "ui_messages_relative_path"):
            extra_rel = sess.get(extra_key)
            if extra_rel:
                try:
                    ep = ensure_within_root(root / extra_rel, root)
                    if not ep.is_file():
                        errors.append(f"missing companion file {extra_rel}")
                    else:
                        json.loads(ep.read_text(encoding="utf-8"))
                except (ValueError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid companion file {extra_rel}: {exc}")
        for sp_rel in sess.get("split_relative_paths", []) or []:
            try:
                sp = ensure_within_root(root / sp_rel, root)
                if not sp.is_file():
                    errors.append(f"missing split file {sp_rel}")
                else:
                    json.loads(sp.read_text(encoding="utf-8"))
            except (ValueError, json.JSONDecodeError) as exc:
                errors.append(f"invalid split file {sp_rel}: {exc}")
        verified_sessions += 1
    checks["verified_staged_sessions"] = verified_sessions

    # 2. Verify SHA-256 of every binary asset listed in portable.json
    verified_assets = 0
    for asset in portable.get("assets", []):
        rel = asset.get("relative_bundle_path")
        expected_sha = asset.get("sha256")
        if not rel or not expected_sha:
            continue
        try:
            ap = ensure_within_root(root / rel, root)
        except ValueError as exc:
            errors.append(f"unsafe asset path {rel}: {exc}")
            continue
        if not ap.is_file():
            errors.append(f"missing asset binary: {rel}")
            continue
        actual_sha = sha256_file(ap)
        if actual_sha != expected_sha:
            errors.append(f"asset SHA-256 mismatch for {rel}: expected {expected_sha}, got {actual_sha}")
        else:
            verified_assets += 1
    checks["verified_assets"] = verified_assets
    del portable

    # 3. Verify HANDOFF_REPORT.md and resources/mcp.sanitized.json contain ZERO unredacted raw secret markers
    for clean_rel in ("HANDOFF_REPORT.md", "resources/mcp.sanitized.json", "resources/codex-mcp.sanitized.toml"):
        cp = root / clean_rel
        if cp.is_file():
            hits = scan_secret_markers(cp.read_text(encoding="utf-8", errors="replace"))
            if hits:
                errors.append(f"unredacted secret markers found in {clean_rel}: {hits}")
    checks["redaction_audit_clean"] = not any("unredacted secret" in e for e in errors)

    # 4. Verify dual-key Claude Desktop 3P Code join inside staged bundle if applicable
    code_joins = 0
    if manifest.get("target_lane") in {"claude-desktop-3p-code", "claude-desktop-3p-all"}:
        for sess in manifest.get("target_sessions", []):
            idx_rel = sess.get("index_relative_path")
            if idx_rel:
                jres = verify_desktop_3p_code_join(root / idx_rel, root / "claude_sessions")
                if not jres["ok"]:
                    errors.append(f"desktop 3p code join check failed for {idx_rel}: {jres}")
                else:
                    code_joins += 1
    checks["verified_desktop_3p_code_joins"] = code_joins

    file_count, tree_sha = compute_tree_sha256(root)
    checks["bundle_file_count"] = file_count
    checks["bundle_tree_sha256"] = tree_sha
    return {"ok": len(errors) == 0, "bundle": str(root), "errors": errors, "checks": checks}


def _plan_apply_operations(
    bundle_root: Path,
    manifest: dict[str, Any],
    *,
    target_root: Path,
    claude_dir: Path | None = None,
    include_skills: bool = False,
) -> list[tuple[Path, Path, str]]:
    """Return list of `(src_in_bundle, dst_in_target, kind)` operations cleanly validated."""
    ops: list[tuple[Path, Path, str]] = []
    lane = manifest.get("target_lane", "claude-code")

    for sess in manifest.get("target_sessions", []):
        rel = sess.get("target_relative_path")
        if not rel:
            continue
        src = ensure_within_root(bundle_root / rel, bundle_root)

        if lane == "claude-code":
            # Map claude_sessions/<project_key>/conversation-NNN/<sid>.jsonl -> <target_root>/projects/<project_key>/<sid>.jsonl
            parts = Path(rel).parts
            project_key = parts[1] if len(parts) >= 3 else "default"
            dst = ensure_within_root(target_root / "projects" / project_key / Path(rel).name, target_root)
            ops.append((src, dst, "claude-code-transcript"))
        elif lane in {"claude-desktop-3p-chat", "claude-desktop-3p-cowork"}:
            # Map claude_desktop_3p/local-agent-mode-sessions/... -> <target_root>/local-agent-mode-sessions/...
            rel_under_3p = Path(*Path(rel).parts[1:])
            dst_audit = ensure_within_root(target_root / rel_under_3p, target_root)
            ops.append((src, dst_audit, "desktop-3p-audit"))
            side_rel = sess.get("sidecar_relative_path")
            if side_rel:
                side_src = ensure_within_root(bundle_root / side_rel, bundle_root)
                side_under_3p = Path(*Path(side_rel).parts[1:])
                dst_side = ensure_within_root(target_root / side_under_3p, target_root)
                ops.append((side_src, dst_side, "desktop-3p-sidecar"))
        elif lane == "claude-desktop-3p-code":
            idx_rel = sess.get("index_relative_path")
            if idx_rel:
                idx_src = ensure_within_root(bundle_root / idx_rel, bundle_root)
                idx_under_3p = Path(*Path(idx_rel).parts[1:])
                dst_idx = ensure_within_root(target_root / idx_under_3p, target_root)
                ops.append((idx_src, dst_idx, "desktop-3p-code-index"))
            cc_base = claude_dir or (target_root / "_claude_projects_mirror")
            parts = Path(rel).parts
            project_key = parts[1] if len(parts) >= 2 else "default"
            dst_tr = ensure_within_root(cc_base / "projects" / project_key / Path(rel).name, cc_base)
            ops.append((src, dst_tr, "claude-code-transcript"))
        elif lane == "claude-desktop-3p-all":
            if sess.get("index_relative_path"):
                idx_rel = sess["index_relative_path"]
                idx_src = ensure_within_root(bundle_root / idx_rel, bundle_root)
                dst_idx = ensure_within_root(target_root / Path(*Path(idx_rel).parts[1:]), target_root)
                ops.append((idx_src, dst_idx, "desktop-3p-code-index"))
                cc_base = claude_dir or (target_root / "_claude_projects_mirror")
                parts = Path(rel).parts
                project_key = parts[1] if len(parts) >= 2 else "default"
                dst_tr = ensure_within_root(cc_base / "projects" / project_key / Path(rel).name, cc_base)
                ops.append((src, dst_tr, "claude-code-transcript"))
            else:
                rel_under_3p = Path(*Path(rel).parts[1:])
                ops.append((src, ensure_within_root(target_root / rel_under_3p, target_root), "desktop-3p-audit"))
                side_rel = sess.get("sidecar_relative_path")
                if side_rel:
                    side_src = ensure_within_root(bundle_root / side_rel, bundle_root)
                    ops.append((side_src, ensure_within_root(target_root / Path(*Path(side_rel).parts[1:]), target_root), "desktop-3p-sidecar"))
        elif lane == "codex":
            rel_parts = Path(rel).parts
            rel_under_codex = Path(*rel_parts[1:]) if len(rel_parts) >= 2 and rel_parts[0] == "codex_sessions" else (Path("sessions") / Path(rel).name)
            dst = ensure_within_root(target_root / rel_under_codex, target_root)
            ops.append((src, dst, "codex-rollout"))
        elif lane == "antigravity":
            rel_under_ag = Path(*Path(rel).parts[1:])
            dst = ensure_within_root(target_root / rel_under_ag, target_root)
            ops.append((src, dst, "antigravity-transcript"))
            full_src = src.with_name("transcript_full.jsonl")
            if full_src.is_file():
                ops.append((full_src, dst.with_name("transcript_full.jsonl"), "antigravity-transcript-full"))
            side_rel = sess.get("sidecar_relative_path")
            if side_rel:
                side_src = ensure_within_root(bundle_root / side_rel, bundle_root)
                ops.append((side_src, ensure_within_root(target_root / Path(*Path(side_rel).parts[1:]), target_root), "antigravity-meta"))
        elif lane == "cursor":
            db_dst = ensure_within_root(target_root / "User" / "globalStorage" / "state.vscdb", target_root)
            ops.append((src, db_dst, "cursor-vscdb-merge"))
        elif lane == "opencode":
            split_paths = sess.get("split_relative_paths") or []
            if split_paths:
                for sp_rel in split_paths:
                    sp_src = ensure_within_root(bundle_root / sp_rel, bundle_root)
                    sp_under = Path(*Path(sp_rel).parts[1:])
                    ops.append((sp_src, ensure_within_root(target_root / sp_under, target_root), "opencode-split-file"))
            else:
                dst = ensure_within_root(target_root / "storage" / "session" / Path(rel).name, target_root)
                ops.append((src, dst, "opencode-session"))
            db_dst = ensure_within_root(target_root / "opencode.db", target_root)
            ops.append((src, db_dst, "opencode-db-merge"))
        elif lane == "pi":
            parts = Path(rel).parts
            project_key = parts[1] if len(parts) >= 2 else "default"
            dst = ensure_within_root(target_root / "agent" / "sessions" / project_key / Path(rel).name, target_root)
            ops.append((src, dst, "pi-session"))
        elif lane == "dsh":
            rel_parts = Path(rel).parts
            rel_under_dsh = Path(*rel_parts[1:]) if len(rel_parts) >= 2 and rel_parts[0] == "dsh_sessions" else Path(Path(rel).name)
            dst = ensure_within_root(target_root / "sessions" / rel_under_dsh, target_root)
            ops.append((src, dst, "dsh-v4-session"))
            zstd_rel = sess.get("zstd_relative_path")
            if zstd_rel and (bundle_root / zstd_rel).is_file():
                zsrc = ensure_within_root(bundle_root / zstd_rel, bundle_root)
                zparts = Path(zstd_rel).parts
                zunder = Path(*zparts[1:]) if len(zparts) >= 2 and zparts[0] == "dsh_sessions" else Path(Path(zstd_rel).name)
                zdst = ensure_within_root(target_root / "sessions" / zunder, target_root)
                ops.append((zsrc, zdst, "dsh-v4-session-zstd"))
        elif lane == "gemini-cli":
            rel_under = Path(*Path(rel).parts[1:])
            dst = ensure_within_root(target_root / rel_under, target_root)
            ops.append((src, dst, "gemini-cli-session"))
        elif lane == "cline-roo":
            sid = sess.get("session_id") or Path(rel).parent.name
            dst = ensure_within_root(target_root / "tasks" / sid / "api_conversation_history.json", target_root)
            ops.append((src, dst, "cline-roo-task"))
            data_api_dst = ensure_within_root(target_root / "data" / "tasks" / sid / "api_conversation_history.json", target_root)
            ops.append((src, data_api_dst, "cline-roo-task"))
            ui_rel = sess.get("ui_messages_relative_path")
            if ui_rel:
                ui_src = ensure_within_root(bundle_root / ui_rel, bundle_root)
                data_ui_dst = ensure_within_root(target_root / "data" / "tasks" / sid / "ui_messages.json", target_root)
                ops.append((ui_src, data_ui_dst, "cline-ui-messages"))
            db_dst = ensure_within_root(target_root / "data" / "db" / "sessions.db", target_root)
            ops.append((src, db_dst, "cline-db-merge"))
        elif lane == "goose":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "goose-session"))
            db_dst = ensure_within_root(target_root / "sessions" / "sessions.db", target_root)
            ops.append((src, db_dst, "goose-db-merge"))
        elif lane == "continue":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "continue-session"))
        elif lane == "zed":
            dst = ensure_within_root(target_root / "threads" / Path(rel).name, target_root)
            ops.append((src, dst, "zed-thread"))
            db_dst = ensure_within_root(target_root / "threads" / "threads.db", target_root)
            ops.append((src, db_dst, "zed-threads-db-merge"))
        elif lane == "aider":
            total_aider = len(manifest.get("target_sessions", []))
            fname = ".aider.chat.history.md" if total_aider == 1 else f".aider.chat.history.{sess.get('session_id', 'imported')}.md"
            dst = ensure_within_root(target_root / fname, target_root)
            ops.append((src, dst, "aider-history"))
        elif lane == "workbuddy":
            from .harnesses_extended import workbuddy_project_dir_name

            wb_cwd = str(sess.get("cwd") or "")
            wb_proj_key = workbuddy_project_dir_name(wb_cwd) if wb_cwd else "workspace"
            proj_dst = ensure_within_root(target_root / "projects" / wb_proj_key / Path(rel).name, target_root)
            ops.append((src, proj_dst, "workbuddy-project-session"))
            db_dst = ensure_within_root(target_root / "workbuddy.db", target_root)
            ops.append((src, db_dst, "workbuddy-db-merge"))
        elif lane == "t3code":
            db_dst = ensure_within_root(target_root / "userdata" / "statev2.sqlite", target_root)
            ops.append((src, db_dst, "t3code-statev2-merge"))
        elif lane == "kiro":
            dst = ensure_within_root(target_root / "sessions" / "cli" / Path(rel).name, target_root)
            ops.append((src, dst, "kiro-session"))
            db_dst = ensure_within_root(target_root / "data.sqlite3", target_root)
            ops.append((src, db_dst, "kiro-db-merge"))
        elif lane == "amp":
            dst = ensure_within_root(target_root / "threads" / Path(rel).name, target_root)
            ops.append((src, dst, "amp-thread"))
        elif lane == "trae":
            dst = ensure_within_root(target_root / "trajectories" / Path(rel).name, target_root)
            ops.append((src, dst, "trae-trajectory"))
        elif lane == "warp-oz":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "warp-oz-session"))
        elif lane == "windsurf":
            dst = ensure_within_root(target_root / "cascade" / Path(rel).name, target_root)
            ops.append((src, dst, "windsurf-cascade"))

    # Companion index / registry files for codex, continue, & gemini-cli
    if lane == "codex":
        codex_idx = bundle_root / "codex_sessions" / "session_index.jsonl"
        if codex_idx.is_file():
            ops.append((codex_idx, ensure_within_root(target_root / "session_index.jsonl", target_root), "codex-session-index-merge"))
    elif lane == "continue":
        cont_idx = bundle_root / "continue_sessions" / "sessions.json"
        if cont_idx.is_file():
            ops.append((cont_idx, ensure_within_root(target_root / "sessions" / "sessions.json", target_root), "continue-sessions-index-merge"))
    elif lane == "gemini-cli":
        g_tmp = bundle_root / "gemini_sessions" / "tmp"
        if g_tmp.is_dir():
            for pr in sorted(g_tmp.glob("*/.project_root")):
                if pr.is_file():
                    rel_pr = pr.relative_to(bundle_root / "gemini_sessions")
                    ops.append((pr, ensure_within_root(target_root / rel_pr, target_root), "gemini-project-root"))
        g_proj = bundle_root / "gemini_sessions" / "projects.json"
        if g_proj.is_file():
            ops.append((g_proj, ensure_within_root(target_root / "projects.json", target_root), "gemini-projects-merge"))

    if include_skills and (bundle_root / "resources" / "skills").is_dir():
        skills_src = bundle_root / "resources" / "skills"
        skills_dst_root = ensure_within_root(target_root / "skills", target_root)
        for sf in sorted(skills_src.rglob("*")):
            if sf.is_file() and not sf.is_symlink():
                rel_sf = sf.relative_to(skills_src)
                ops.append((ensure_within_root(sf, skills_src), ensure_within_root(skills_dst_root / rel_sf, skills_dst_root), "skill-file"))

    return ops


def _expand_sqlite_companions(paths: list[Path], root: Path) -> list[Path]:
    """Include SQLite `-wal` and `-shm` companion paths for any SQLite DB destination."""
    out: list[Path] = []
    seen: set[Path] = set()
    for p in paths:
        for cand in (
            [p, p.with_name(p.name + "-wal"), p.with_name(p.name + "-shm")]
            if p.suffix in {".sqlite", ".sqlite3", ".db", ".vscdb"}
            else [p]
        ):
            try:
                safe = ensure_within_root(cand, root)
            except ValueError:
                continue
            if safe not in seen:
                seen.add(safe)
                out.append(safe)
    return out


def _create_scoped_backup(
    root: Path,
    touched_paths: list[Path],
    archive_path: Path,
) -> dict[str, Any]:
    """Archive ONLY pre-existing files in `touched_paths` (plus SQLite WAL/SHM companions) into a `0o600` tar.gz.

    Never touches or wipes unrelated files in live Harness homes (e.g. `~/.t3/tools`, `~/.codex`).
    """
    ensure_private_dir(archive_path.parent)
    expanded = _expand_sqlite_companions(touched_paths, root)
    created_rel: list[str] = []
    modified_meta: list[dict[str, Any]] = []
    with tarfile.open(archive_path, "w:gz") as tf:
        for p in sorted(expanded):
            rel = p.relative_to(root).as_posix()
            if p.is_file() and not p.is_symlink():
                tf.add(p, arcname=rel, recursive=False)
                modified_meta.append(
                    {
                        "rel_path": rel,
                        "sha256": sha256_file(p),
                        "mode": p.stat().st_mode & 0o777,
                    }
                )
            else:
                created_rel.append(rel)
    try:
        archive_path.chmod(0o600)
    except OSError:
        pass
    h = hashlib.sha256()
    for item in modified_meta:
        h.update(f"{item['rel_path']}\x00{item['sha256']}\n".encode("utf-8"))
    return {
        "backup_sha256": sha256_file(archive_path),
        "backup_bytes": archive_path.stat().st_size if archive_path.is_file() else 0,
        "scoped_pre_sha256": h.hexdigest(),
        "created_rel_paths": created_rel,
        "modified_files": modified_meta,
    }


def apply_bundle(
    bundle_dir: str | Path,
    *,
    target_root: str | Path,
    claude_dir: str | Path | None = None,
    tx_dir: str | Path | None = None,
    apply: bool = False,
    on_collision: str = "refuse",  # refuse | skip | rename
    include_skills: bool = False,
    gate_config: GateConfig | None = None,
    allow_cloud_sync_path: str | Path | None = None,
    on_progress: Callable[[str, int, int, str], None] | None = None,
    cleanup_backup_after_verify: bool = False,
    auto_prune_keep: int | None = DEFAULT_MAX_KEEP_TRANSACTIONS,
) -> dict[str, Any]:
    """Dry-run or transactionally apply a verified bundle to `target_root` with backup & verification."""
    if on_collision not in {"refuse", "skip", "rename"}:
        raise ValueError(f"invalid on_collision policy: {on_collision}")

    broot = Path(bundle_dir).expanduser().resolve()
    troot = Path(target_root).expanduser().resolve()
    croot = Path(claude_dir).expanduser().resolve() if claude_dir else None

    # Pre-check bundle integrity
    bcheck = verify_bundle(broot)
    if not bcheck["ok"]:
        raise ValueError(f"refusing to apply invalid bundle: {bcheck['errors']}")

    manifest = json.loads((broot / "manifest.json").read_text(encoding="utf-8"))
    ops = _plan_apply_operations(broot, manifest, target_root=troot, claude_dir=croot, include_skills=include_skills)

    # Check collisions deterministically before mutating anything
    resolved_ops: list[dict[str, Any]] = []
    collisions: list[str] = []
    for src, dst, kind in ops:
        final_dst = dst
        action = "create"
        if dst.exists():
            if kind in {
                "codex-session-index-merge",
                "continue-sessions-index-merge",
                "gemini-projects-merge",
                "cursor-vscdb-merge",
                "t3code-statev2-merge",
                "workbuddy-db-merge",
                "opencode-db-merge",
                "goose-db-merge",
                "cline-db-merge",
                "zed-threads-db-merge",
                "kiro-db-merge",
            }:
                action = "merge_existing"
            elif kind == "gemini-project-root":
                action = "skip_existing"
            else:
                collisions.append(str(dst))
                if on_collision == "refuse":
                    action = "collision_refused"
                elif on_collision == "skip":
                    action = "skip_existing"
                elif on_collision == "rename":
                    suffix = uuid.uuid4().hex[:8]
                    final_dst = dst.with_name(f"{dst.stem}-nexus-{suffix}{dst.suffix}")
                    action = "create_renamed"
        resolved_ops.append(
            {
                "kind": kind,
                "src": str(src),
                "dst": str(final_dst),
                "original_dst": str(dst),
                "action": action,
                "src_sha256": sha256_file(src),
            }
        )

    plan_summary = {
        "schema": "nexus-memory.apply-plan.v1",
        "dry_run": not apply,
        "bundle": str(broot),
        "target_root": str(troot),
        "claude_dir": str(croot) if croot else None,
        "target_lane": manifest.get("target_lane"),
        "on_collision": on_collision,
        "operation_count": len(resolved_ops),
        "collisions": collisions,
        "operations": resolved_ops,
    }

    if not apply:
        return plan_summary

    # Stage 1 & 2 Write Gate check
    for write_root in [troot, *([croot] if croot else [])]:
        gate = check_write_gate(write_root, gate_config=gate_config, allow_cloud_sync_path=allow_cloud_sync_path)
        if not gate.allowed:
            raise PermissionError(f"write gate blocked apply on {write_root}: {gate.reason}")

    if collisions and on_collision == "refuse":
        raise FileExistsError(
            f"collision policy 'refuse' blocked apply; {len(collisions)} destination path(s) already exist: {collisions[:3]}"
        )

    tx_id = f"tx-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    journal_root = Path(tx_dir).expanduser().resolve() if tx_dir else (broot / ".transactions" / tx_id)
    ensure_private_dir(journal_root)

    # Record scoped pre-apply pristine backups (only touched files + SQLite WAL/SHM companions; never wipes unrelated files!)
    if on_progress is not None:
        on_progress("backup", 0, 1, "正在打包 0600 写前备份…")
    ensure_private_dir(troot)
    primary_touched = [
        Path(op["dst"])
        for op in resolved_ops
        if op["action"] != "skip_existing" and Path(op["dst"]).resolve().is_relative_to(troot)
    ]
    backup_tar = journal_root / "pristine_target_backup.tar.gz"
    primary_bk = _create_scoped_backup(troot, primary_touched, backup_tar)
    backup_sha = primary_bk["backup_sha256"]
    pre_count = len(primary_bk["modified_files"])
    pre_sha = primary_bk["scoped_pre_sha256"]

    extra_backup: dict[str, Any] | None = None
    if croot is not None:
        ensure_private_dir(croot)
        c_touched = [
            Path(op["dst"])
            for op in resolved_ops
            if op["action"] != "skip_existing" and Path(op["dst"]).resolve().is_relative_to(croot)
        ]
        c_backup_tar = journal_root / "pristine_claude_backup.tar.gz"
        c_bk = _create_scoped_backup(croot, c_touched, c_backup_tar)
        extra_backup = {
            "root": str(croot),
            "rollback_mode": "scoped",
            "pre_file_count": len(c_bk["modified_files"]),
            "pre_tree_sha256": c_bk["scoped_pre_sha256"],
            "backup_archive": str(c_backup_tar),
            "backup_sha256": c_bk["backup_sha256"],
            "created_rel_paths": c_bk["created_rel_paths"],
            "modified_files": c_bk["modified_files"],
        }
    if on_progress is not None:
        on_progress("backup", 1, 1, "0600 原始备份已完成")

    # Execute atomic writes (batching all t3code-statev2-merge ops per SQLite DB into ONE transaction!)
    written_files: list[dict[str, Any]] = []
    active_ops = [op for op in resolved_ops if op["action"] != "skip_existing"]
    total_ops = len(active_ops)
    done_ops = 0

    t3_groups: dict[str, list[dict[str, Any]]] = {}
    wb_groups: dict[str, list[dict[str, Any]]] = {}
    oc_groups: dict[str, list[dict[str, Any]]] = {}
    goose_groups: dict[str, list[dict[str, Any]]] = {}
    cline_groups: dict[str, list[dict[str, Any]]] = {}
    zed_groups: dict[str, list[dict[str, Any]]] = {}
    kiro_groups: dict[str, list[dict[str, Any]]] = {}
    other_ops: list[dict[str, Any]] = []
    for op in active_ops:
        k = op["kind"]
        if k == "t3code-statev2-merge":
            t3_groups.setdefault(str(op["dst"]), []).append(op)
        elif k == "workbuddy-db-merge":
            wb_groups.setdefault(str(op["dst"]), []).append(op)
        elif k == "opencode-db-merge":
            oc_groups.setdefault(str(op["dst"]), []).append(op)
        elif k == "goose-db-merge":
            goose_groups.setdefault(str(op["dst"]), []).append(op)
        elif k == "cline-db-merge":
            cline_groups.setdefault(str(op["dst"]), []).append(op)
        elif k == "zed-threads-db-merge":
            zed_groups.setdefault(str(op["dst"]), []).append(op)
        elif k == "kiro-db-merge":
            kiro_groups.setdefault(str(op["dst"]), []).append(op)
        else:
            other_ops.append(op)

    # Execute other_ops before DB merges that reference task paths (e.g. cline-db-merge)
    for op in other_ops:
        src = Path(op["src"])
        dst = Path(op["dst"])
        if op["action"] == "merge_existing" and op["kind"] == "codex-session-index-merge":
            existing_lines = [l for l in dst.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
            existing_ids: set[str] = set()
            for ln in existing_lines:
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict) and obj.get("id"):
                        existing_ids.add(str(obj["id"]))
                except json.JSONDecodeError:
                    continue
            new_lines = list(existing_lines)
            for ln in src.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict) and str(obj.get("id") or "") not in existing_ids:
                        new_lines.append(ln.strip())
                except json.JSONDecodeError:
                    continue
            atomic_write_bytes(dst, ("\n".join(new_lines) + "\n").encode("utf-8"), mode=0o600)
        elif op["action"] == "merge_existing" and op["kind"] == "continue-sessions-index-merge":
            try:
                cur_arr = json.loads(dst.read_text(encoding="utf-8-sig"))
                if not isinstance(cur_arr, list):
                    cur_arr = []
            except (json.JSONDecodeError, OSError):
                cur_arr = []
            add_arr = json.loads(src.read_text(encoding="utf-8-sig"))
            seen_cids = {str(item.get("sessionId")) for item in cur_arr if isinstance(item, dict) and item.get("sessionId")}
            merged_arr = list(cur_arr)
            for item in add_arr if isinstance(add_arr, list) else []:
                if isinstance(item, dict) and str(item.get("sessionId") or "") not in seen_cids:
                    merged_arr.append(item)
                    if item.get("sessionId"):
                        seen_cids.add(str(item["sessionId"]))
            atomic_write_json(dst, merged_arr, mode=0o600)
        elif op["kind"] == "cursor-vscdb-merge":
            payload = json.loads(src.read_text(encoding="utf-8-sig"))
            ensure_private_dir(dst.parent)
            conn = sqlite3.connect(dst)
            try:
                conn.execute("CREATE TABLE IF NOT EXISTS cursorDiskKV (key TEXT PRIMARY KEY, value TEXT)")
                ckey = str(payload["composer_key"])
                existing = conn.execute("SELECT 1 FROM cursorDiskKV WHERE key = ?", (ckey,)).fetchone()
                if existing and on_collision == "refuse":
                    raise FileExistsError(f"cursor composer key already exists in state.vscdb: {ckey}")
                if not existing or on_collision != "skip":
                    conn.execute(
                        "INSERT OR REPLACE INTO cursorDiskKV (key, value) VALUES (?, ?)",
                        (ckey, json.dumps(payload["composer"], ensure_ascii=False)),
                    )
                    for bkey, bval in (payload.get("bubbles") or {}).items():
                        conn.execute(
                            "INSERT OR REPLACE INTO cursorDiskKV (key, value) VALUES (?, ?)",
                            (str(bkey), json.dumps(bval, ensure_ascii=False)),
                        )
                conn.commit()
            finally:
                conn.close()
            try:
                dst.chmod(0o600)
            except OSError:
                pass
        elif op["action"] == "merge_existing" and op["kind"] == "gemini-projects-merge":
            try:
                cur_obj = json.loads(dst.read_text(encoding="utf-8-sig"))
                if not isinstance(cur_obj, dict):
                    cur_obj = {"projects": {}}
            except (json.JSONDecodeError, OSError):
                cur_obj = {"projects": {}}
            add_obj = json.loads(src.read_text(encoding="utf-8-sig"))
            projs = dict(cur_obj.get("projects") or {})
            for k, v in (add_obj.get("projects") or {}).items():
                projs.setdefault(k, v)
            cur_obj["projects"] = projs
            atomic_write_json(dst, cur_obj, mode=0o600)
        else:
            atomic_copy_file(src, dst, mode=0o600)
        written_files.append({**op, "written_sha256": sha256_file(dst)})
        done_ops += 1
        if on_progress is not None:
            on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Batch-merge T3 Code threads per statev2.sqlite (single SQLite transaction, parent-before-child ordering)
    if t3_groups:
        from .harnesses_extended import merge_t3code_threads_batch

        for dst_str, group_ops in t3_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            payloads = [json.loads(Path(op["src"]).read_text(encoding="utf-8-sig")) for op in group_ops]
            base_done = done_ops

            def _t3_progress(phase: str, done_in_batch: int, batch_total: int, label: str) -> None:
                if on_progress is not None:
                    on_progress("apply", base_done + done_in_batch, max(total_ops, 1), label)

            metas = merge_t3code_threads_batch(
                dst,
                payloads,
                on_collision=on_collision,
                on_progress=_t3_progress if on_progress is not None else None,
            )
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, metas):
                written_files.append({**op, "t3code_thread_id": meta.get("thread_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)

    # Batch-merge WorkBuddy sessions into workbuddy.db
    if wb_groups:
        from .harnesses_extended import merge_workbuddy_sessions_batch

        for dst_str, group_ops in wb_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            wb_entries: list[dict[str, Any]] = []
            for op in group_ops:
                first_line = _read_first_nonempty_line(Path(op["src"]))
                try:
                    hdr = json.loads(first_line)
                except json.JSONDecodeError:
                    hdr = {}
                wb_entries.append(hdr if isinstance(hdr, dict) else {})
            wb_metas = merge_workbuddy_sessions_batch(dst, wb_entries, on_collision=on_collision)
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, wb_metas):
                written_files.append({**op, "workbuddy_session_id": meta.get("session_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)
            if on_progress is not None:
                on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Batch-merge OpenCode sessions into opencode.db (v2.4 session_v2 + v1 compatible)
    if oc_groups:
        from .ecosystem import merge_opencode_sessions_batch

        for dst_str, group_ops in oc_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            payloads = [json.loads(Path(op["src"]).read_text(encoding="utf-8-sig")) for op in group_ops]
            oc_metas = merge_opencode_sessions_batch(dst, payloads, on_collision=on_collision)
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, oc_metas):
                written_files.append({**op, "opencode_session_id": meta.get("session_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)
            if on_progress is not None:
                on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Batch-merge Block Goose sessions into sessions/sessions.db
    if goose_groups:
        from .ecosystem import merge_goose_sessions_batch

        for dst_str, group_ops in goose_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            g_entries = []
            for op in group_ops:
                recs = [json.loads(l) for l in Path(op["src"]).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
                hdr = recs[0] if recs and isinstance(recs[0], dict) and "role" not in recs[0] else {}
                g_entries.append({
                    "session_id": hdr.get("id") or Path(op["src"]).stem,
                    "title": hdr.get("description") or Path(op["src"]).stem,
                    "cwd": hdr.get("working_dir") or "",
                    "records": recs,
                })
            g_metas = merge_goose_sessions_batch(dst, g_entries, on_collision=on_collision)
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, g_metas):
                written_files.append({**op, "goose_session_id": meta.get("session_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)
            if on_progress is not None:
                on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Batch-merge Cline CLI sessions into data/db/sessions.db
    if cline_groups:
        from .ecosystem import merge_cline_sessions_batch

        sess_by_id = {
            str(s.get("session_id")): s for s in manifest.get("target_sessions", []) if isinstance(s, dict)
        }
        for dst_str, group_ops in cline_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            c_entries = []
            for op in group_ops:
                sid = Path(op["src"]).parent.name
                meta_s = sess_by_id.get(sid, {})
                api_path = troot / "data" / "tasks" / sid / "api_conversation_history.json"
                ui_path = troot / "data" / "tasks" / sid / "ui_messages.json"
                c_entries.append({
                    "session_id": sid,
                    "title": meta_s.get("title") or sid,
                    "cwd": meta_s.get("cwd") or str(troot),
                    "api_history_path": str(api_path),
                    "ui_messages_path": str(ui_path) if ui_path.is_file() else "",
                })
            c_metas = merge_cline_sessions_batch(dst, c_entries, on_collision=on_collision)
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, c_metas):
                written_files.append({**op, "cline_session_id": meta.get("session_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)
            if on_progress is not None:
                on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Batch-merge Zed threads into threads/threads.db
    if zed_groups:
        from .ecosystem import merge_zed_threads_batch

        for dst_str, group_ops in zed_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            payloads = [json.loads(Path(op["src"]).read_text(encoding="utf-8-sig")) for op in group_ops]
            z_metas = merge_zed_threads_batch(dst, payloads, on_collision=on_collision)
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, z_metas):
                written_files.append({**op, "zed_thread_id": meta.get("thread_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)
            if on_progress is not None:
                on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Batch-merge AWS Kiro sessions into data.sqlite3
    if kiro_groups:
        from .harnesses_extended import merge_kiro_sessions_batch

        for dst_str, group_ops in kiro_groups.items():
            dst = Path(dst_str)
            ensure_private_dir(dst.parent)
            k_entries = []
            for op in group_ops:
                recs = [json.loads(l) for l in Path(op["src"]).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
                hdr = recs[0] if recs and isinstance(recs[0], dict) and recs[0].get("type") == "kiro_session_meta" else {}
                k_entries.append({
                    "session_id": hdr.get("conversation_id") or Path(op["src"]).stem,
                    "title": hdr.get("title") or Path(op["src"]).stem,
                    "cwd": hdr.get("cwd") or str(troot),
                    "records": recs,
                })
            k_metas = merge_kiro_sessions_batch(dst, k_entries, on_collision=on_collision)
            db_sha = sha256_file(dst) if dst.is_file() else ""
            for op, meta in zip(group_ops, k_metas):
                written_files.append({**op, "kiro_conversation_id": meta.get("session_id"), "written_sha256": db_sha})
            done_ops += len(group_ops)
            if on_progress is not None:
                on_progress("apply", done_ops, max(total_ops, 1), dst.name)

    # Refresh final SHA-256 on shared merge targets (e.g. multiple sessions merged into one SQLite DB)
    final_hash_cache: dict[str, str] = {}
    for wf in written_files:
        if wf.get("action") == "merge_existing" or str(wf.get("kind") or "").endswith("-merge"):
            dpath = str(wf["dst"])
            if dpath not in final_hash_cache and Path(dpath).is_file():
                final_hash_cache[dpath] = sha256_file(dpath)
            if dpath in final_hash_cache:
                wf["written_sha256"] = final_hash_cache[dpath]

    post_count = len(written_files)
    post_h = hashlib.sha256()
    for wf in written_files:
        post_h.update(f"{wf['dst']}\x00{wf['written_sha256']}\n".encode("utf-8"))
    post_sha = post_h.hexdigest()
    total_backup_bytes = int(primary_bk.get("backup_bytes") or 0) + (
        int(Path(extra_backup["backup_archive"]).stat().st_size)
        if extra_backup and Path(extra_backup["backup_archive"]).is_file()
        else 0
    )
    tx_record: dict[str, Any] = {
        "schema": "nexus-memory.transaction.v2",
        "rollback_mode": "scoped",
        "transaction_id": tx_id,
        "applied_at": datetime.now(UTC).isoformat(),
        "bundle": str(broot),
        "target_lane": manifest.get("target_lane"),
        "target_root": str(troot),
        "pre_file_count": pre_count,
        "pre_tree_sha256": pre_sha,
        "post_file_count": post_count,
        "post_tree_sha256": post_sha,
        "backup_archive": str(backup_tar),
        "backup_sha256": backup_sha,
        "backup_bytes": total_backup_bytes,
        "created_rel_paths": primary_bk["created_rel_paths"],
        "modified_files": primary_bk["modified_files"],
        "claude_dir_backup": extra_backup,
        "written_files": written_files,
        "journal_dir": str(journal_root),
    }
    atomic_write_json(journal_root / "transaction.json", tx_record, mode=0o600)

    # Immediate post-write readback verification
    if on_progress is not None:
        on_progress("verify", 0, 1, "正在执行写后 SHA-256 与数据库读回校验…")
    vresult = verify_transaction(journal_root)
    if on_progress is not None:
        on_progress("verify", 1, 1, "读回校验通过" if vresult.get("ok") else "读回校验发现异常")
    tx_record["post_write_verification"] = vresult
    atomic_write_json(journal_root / "transaction.json", tx_record, mode=0o600)

    if vresult.get("ok"):
        if cleanup_backup_after_verify:
            tx_record["auto_cleanup"] = cleanup_transaction_backup(
                journal_root,
                remove_bundle=False,
                mark_confirmed=True,
                keep_receipt=True,
                dry_run=False,
            )
            tx_record["backup_cleaned"] = True
        elif auto_prune_keep is not None and auto_prune_keep > 0 and journal_root.parent.is_dir():
            prune_res = prune_reclaimable_storage(
                extra_roots=[journal_root.parent],
                max_keep_transactions=int(auto_prune_keep),
                clean_sandboxes=False,
                clean_bundles=False,
                include_temp=False,
                include_desktop=False,
                dry_run=False,
            )
            if prune_res.get("pruned_transactions"):
                tx_record["auto_prune"] = prune_res

    reclaim_memory()
    return tx_record


def verify_transaction(tx_dir: str | Path) -> dict[str, Any]:
    """Readback-verify every file written in a transaction (hashes, parse validity, and dual-key 3P Code join)."""
    jroot = Path(tx_dir).expanduser().resolve()
    tx_file = jroot / "transaction.json" if jroot.is_dir() else jroot
    tx = json.loads(tx_file.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked = 0
    code_joins = 0

    cc_root = Path(tx["claude_dir_backup"]["root"]) if tx.get("claude_dir_backup") else (Path(tx["target_root"]) / "_claude_projects_mirror")
    for wf in tx.get("written_files", []):
        dst = Path(wf["dst"])
        if not dst.is_file():
            errors.append(f"missing written file: {dst}")
            continue
        actual = sha256_file(dst)
        expected_hash = wf["written_sha256"] if (wf.get("action") == "merge_existing" or str(wf.get("kind") or "").endswith("-merge")) else wf["src_sha256"]
        if actual != expected_hash:
            errors.append(f"hash mismatch on {dst}: expected {expected_hash}, got {actual}")
        if wf.get("kind") == "t3code-statev2-merge" and wf.get("t3code_thread_id"):
            conn = sqlite3.connect(f"file:{dst}?mode=ro", uri=True)
            try:
                trow = conn.execute(
                    "SELECT 1 FROM orchestration_v2_projection_threads WHERE thread_id = ?",
                    (wf["t3code_thread_id"],),
                ).fetchone()
                if not trow:
                    errors.append(f"t3code thread missing after merge: {wf['t3code_thread_id']}")
            finally:
                conn.close()
        if wf.get("kind") == "desktop-3p-code-index":
            jres = verify_desktop_3p_code_join(dst, cc_root / "projects")
            if not jres["ok"]:
                errors.append(f"3p code dual-key join failed for {dst}: {jres}")
            else:
                code_joins += 1
        checked += 1

    return {
        "ok": len(errors) == 0,
        "transaction_id": tx.get("transaction_id"),
        "checked_files": checked,
        "verified_code_joins": code_joins,
        "errors": errors,
    }


def _prune_empty_parents(path: Path, stop_root: Path) -> None:
    cur = path.parent
    stop = stop_root.resolve()
    while cur.resolve() != stop and cur.resolve().is_relative_to(stop):
        try:
            cur.rmdir()
        except OSError:
            break
        cur = cur.parent


def _restore_scoped_backup(
    root: Path,
    archive_path: Path,
    expected_archive_sha: str,
    expected_scoped_sha: str,
    created_rel_paths: list[str],
    modified_files: list[dict[str, Any]],
) -> dict[str, Any]:
    """Surgically roll back ONLY files created/modified by this transaction — NEVER wipes unrelated files."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"backup archive already cleaned or missing: {archive_path}")
    actual_arch_sha = sha256_file(archive_path)
    if actual_arch_sha != expected_archive_sha:
        raise ValueError(f"backup archive SHA-256 mismatch: expected {expected_archive_sha}, got {actual_arch_sha}")

    # 1. Remove files newly created by this transaction
    for rel in created_rel_paths:
        target_path = ensure_within_root(root / rel, root)
        if target_path.is_file() or target_path.is_symlink():
            target_path.unlink(missing_ok=True)
            _prune_empty_parents(target_path, root)

    # 2. Restore exact pre-apply bytes & permissions of modified files (streaming, constant RAM)
    mode_by_rel = {item["rel_path"]: int(item.get("mode", 0o600)) for item in modified_files}
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.issym() or member.islnk():
                raise ValueError(f"refusing symlink in backup archive: {member.name}")
            if member.isfile():
                target_path = ensure_within_root(root / member.name, root)
                extracted = tf.extractfile(member)
                if extracted is not None:
                    with extracted:
                        mode = mode_by_rel.get(member.name, (member.mode & 0o777) or 0o600)
                        atomic_write_stream(target_path, extracted, mode=mode)

    # 3. Verify every created file is removed and every modified file matches its pre-apply SHA-256
    h = hashlib.sha256()
    all_gone = True
    for rel in created_rel_paths:
        if ensure_within_root(root / rel, root).exists():
            all_gone = False
    for item in modified_files:
        p = ensure_within_root(root / item["rel_path"], root)
        if not p.is_file():
            h.update(b"MISSING\n")
        else:
            h.update(f"{item['rel_path']}\x00{sha256_file(p)}\n".encode("utf-8"))
    restored_sha = h.hexdigest()
    return {
        "root": str(root),
        "rollback_mode": "scoped",
        "restored_file_count": len(modified_files),
        "removed_created_count": len(created_rel_paths),
        "restored_tree_sha256": restored_sha,
        "expected_pristine_sha256": expected_scoped_sha,
        "exact_match": all_gone and (restored_sha == expected_scoped_sha),
    }


def _restore_from_backup(root: Path, archive_path: Path, expected_archive_sha: str, expected_tree_sha: str) -> dict[str, Any]:
    """Legacy full-tree restore (safe non-destructive extraction preserving original file modes)."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"backup archive already cleaned or missing: {archive_path}")
    actual_arch_sha = sha256_file(archive_path)
    if actual_arch_sha != expected_archive_sha:
        raise ValueError(f"backup archive SHA-256 mismatch: expected {expected_archive_sha}, got {actual_arch_sha}")
    ensure_private_dir(root)
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.issym() or member.islnk():
                continue
            target_path = ensure_within_root(root / member.name, root, allow_root=True)
            if member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                extracted = tf.extractfile(member)
                if extracted is not None:
                    with extracted:
                        mode = (member.mode & 0o777) or 0o600
                        atomic_write_stream(target_path, extracted, mode=mode)
    restored_count, restored_sha = compute_tree_sha256(root)
    return {
        "root": str(root),
        "restored_file_count": restored_count,
        "restored_tree_sha256": restored_sha,
        "expected_pristine_sha256": expected_tree_sha,
        "exact_match": restored_sha == expected_tree_sha,
    }


def rollback_transaction(tx_dir: str | Path, *, cleanup_backup: bool = False) -> dict[str, Any]:
    """Restore target directory (and optional claude_dir) to exact pre-apply pristine SHA-256."""
    jroot = Path(tx_dir).expanduser().resolve()
    tx_file = jroot / "transaction.json" if jroot.is_dir() else jroot
    tx = json.loads(tx_file.read_text(encoding="utf-8"))

    if tx.get("rollback_mode") == "scoped":
        primary = _restore_scoped_backup(
            Path(tx["target_root"]),
            Path(tx["backup_archive"]),
            tx["backup_sha256"],
            tx["pre_tree_sha256"],
            tx.get("created_rel_paths", []),
            tx.get("modified_files", []),
        )
    else:
        primary = _restore_from_backup(
            Path(tx["target_root"]),
            Path(tx["backup_archive"]),
            tx["backup_sha256"],
            tx["pre_tree_sha256"],
        )
    extra = None
    if tx.get("claude_dir_backup"):
        cb = tx["claude_dir_backup"]
        if cb.get("rollback_mode") == "scoped":
            extra = _restore_scoped_backup(
                Path(cb["root"]),
                Path(cb["backup_archive"]),
                cb["backup_sha256"],
                cb["pre_tree_sha256"],
                cb.get("created_rel_paths", []),
                cb.get("modified_files", []),
            )
        else:
            extra = _restore_from_backup(
                Path(cb["root"]),
                Path(cb["backup_archive"]),
                cb["backup_sha256"],
                cb["pre_tree_sha256"],
            )

    ok = primary["exact_match"] and (extra["exact_match"] if extra is not None else True)
    cleanup_res = None
    if ok:
        tx["rolled_back"] = True
        tx["rolled_back_at"] = datetime.now(UTC).isoformat()
        atomic_write_json(tx_file, tx, mode=0o600)
        if cleanup_backup:
            cleanup_res = cleanup_transaction_backup(
                tx_file.parent,
                remove_bundle=False,
                mark_confirmed=False,
                keep_receipt=True,
                dry_run=False,
            )
    reclaim_memory()
    return {
        "ok": ok,
        "transaction_id": tx.get("transaction_id"),
        "primary_restore": primary,
        "claude_dir_restore": extra,
        "backup_cleanup": cleanup_res,
    }
