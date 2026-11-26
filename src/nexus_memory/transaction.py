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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .claude_desktop_3p import verify_desktop_3p_code_join
from .security import (
    atomic_write_bytes,
    atomic_write_json,
    ensure_private_dir,
    ensure_within_root,
    scan_secret_markers,
)
from .write_gate import GateConfig, check_write_gate


def compute_tree_sha256(root: str | Path) -> tuple[int, str]:
    """Compute deterministic `(file_count, sha256_hex)` over all regular files in `root`."""
    base = Path(root).expanduser()
    h = hashlib.sha256()
    if not base.exists():
        return 0, h.hexdigest()
    files = sorted(p for p in base.rglob("*") if p.is_file() and not p.is_symlink())
    for fp in files:
        rel = fp.relative_to(base).as_posix().encode("utf-8")
        h.update(rel + b"\x00" + hashlib.sha256(fp.read_bytes()).digest() + b"\n")
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
            for ln, line in enumerate(fp.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip():
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append(f"corrupt JSONL in {rel}:{ln}: {exc.msg}")
        elif fp.suffix == ".json":
            try:
                json.loads(fp.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"corrupt JSON in {rel}: {exc.msg}")

        # Verify companion sidecar / index / split files if present
        for extra_key in ("sidecar_relative_path", "index_relative_path"):
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
        actual_sha = hashlib.sha256(ap.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            errors.append(f"asset SHA-256 mismatch for {rel}: expected {expected_sha}, got {actual_sha}")
        else:
            verified_assets += 1
    checks["verified_assets"] = verified_assets

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
        elif lane == "pi":
            parts = Path(rel).parts
            project_key = parts[1] if len(parts) >= 2 else "default"
            dst = ensure_within_root(target_root / "agent" / "sessions" / project_key / Path(rel).name, target_root)
            ops.append((src, dst, "pi-session"))
        elif lane == "dsh":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "dsh-v4-session"))
        elif lane == "gemini-cli":
            rel_under = Path(*Path(rel).parts[1:])
            dst = ensure_within_root(target_root / rel_under, target_root)
            ops.append((src, dst, "gemini-cli-session"))
        elif lane == "cline-roo":
            sid = sess.get("session_id") or Path(rel).parent.name
            dst = ensure_within_root(target_root / "tasks" / sid / "api_conversation_history.json", target_root)
            ops.append((src, dst, "cline-roo-task"))
        elif lane == "goose":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "goose-session"))
        elif lane == "continue":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "continue-session"))
        elif lane == "zed":
            dst = ensure_within_root(target_root / "threads" / Path(rel).name, target_root)
            ops.append((src, dst, "zed-thread"))
        elif lane == "aider":
            total_aider = len(manifest.get("target_sessions", []))
            fname = ".aider.chat.history.md" if total_aider == 1 else f".aider.chat.history.{sess.get('session_id', 'imported')}.md"
            dst = ensure_within_root(target_root / fname, target_root)
            ops.append((src, dst, "aider-history"))
        elif lane == "workbuddy":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "workbuddy-session"))
        elif lane == "t3code":
            dst = ensure_within_root(target_root / "userdata" / "threads" / Path(rel).name, target_root)
            ops.append((src, dst, "t3code-thread"))
        elif lane == "kiro":
            dst = ensure_within_root(target_root / "sessions" / "cli" / Path(rel).name, target_root)
            ops.append((src, dst, "kiro-session"))
        elif lane == "amp":
            dst = ensure_within_root(target_root / "threads" / Path(rel).name, target_root)
            ops.append((src, dst, "amp-thread"))
        elif lane == "trae":
            dst = ensure_within_root(target_root / "trajectories" / Path(rel).name, target_root)
            ops.append((src, dst, "trae-trajectory"))
        elif lane == "warp-oz":
            dst = ensure_within_root(target_root / "sessions" / Path(rel).name, target_root)
            ops.append((src, dst, "warp-oz-session"))

    # Companion index / registry files for codex & gemini-cli
    if lane == "codex":
        codex_idx = bundle_root / "codex_sessions" / "session_index.jsonl"
        if codex_idx.is_file():
            ops.append((codex_idx, ensure_within_root(target_root / "session_index.jsonl", target_root), "codex-session-index-merge"))
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


def _create_pristine_backup(root: Path, archive_path: Path) -> str:
    """Archive current state of `root` into a `0o600` tar.gz and return its SHA-256."""
    ensure_private_dir(archive_path.parent)
    with tarfile.open(archive_path, "w:gz") as tf:
        if root.exists():
            for p in sorted(root.rglob("*")):
                if p.is_symlink():
                    continue
                tf.add(p, arcname=p.relative_to(root).as_posix(), recursive=False)
    try:
        archive_path.chmod(0o600)
    except OSError:
        pass
    return hashlib.sha256(archive_path.read_bytes()).hexdigest()


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
            if kind in {"codex-session-index-merge", "gemini-projects-merge", "cursor-vscdb-merge"}:
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
                "src_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
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

    # Record pre-apply pristine tree hashes and create 0o600 backup archives
    ensure_private_dir(troot)
    pre_count, pre_sha = compute_tree_sha256(troot)
    backup_tar = journal_root / "pristine_target_backup.tar.gz"
    backup_sha = _create_pristine_backup(troot, backup_tar)

    extra_backup: dict[str, Any] | None = None
    if croot is not None:
        ensure_private_dir(croot)
        c_pre_count, c_pre_sha = compute_tree_sha256(croot)
        c_backup_tar = journal_root / "pristine_claude_backup.tar.gz"
        c_backup_sha = _create_pristine_backup(croot, c_backup_tar)
        extra_backup = {
            "root": str(croot),
            "pre_file_count": c_pre_count,
            "pre_tree_sha256": c_pre_sha,
            "backup_archive": str(c_backup_tar),
            "backup_sha256": c_backup_sha,
        }

    # Execute atomic writes
    written_files: list[dict[str, Any]] = []
    for op in resolved_ops:
        if op["action"] == "skip_existing":
            continue
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
            data = src.read_bytes()
            atomic_write_bytes(dst, data, mode=0o600)
        written_files.append({**op, "written_sha256": hashlib.sha256(dst.read_bytes()).hexdigest()})

    post_count, post_sha = compute_tree_sha256(troot)
    tx_record: dict[str, Any] = {
        "schema": "nexus-memory.transaction.v1",
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
        "claude_dir_backup": extra_backup,
        "written_files": written_files,
        "journal_dir": str(journal_root),
    }
    atomic_write_json(journal_root / "transaction.json", tx_record, mode=0o600)

    # Immediate post-write readback verification
    vresult = verify_transaction(journal_root)
    tx_record["post_write_verification"] = vresult
    atomic_write_json(journal_root / "transaction.json", tx_record, mode=0o600)
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
        actual = hashlib.sha256(dst.read_bytes()).hexdigest()
        expected_hash = wf["written_sha256"] if (wf.get("action") == "merge_existing" or wf.get("kind") == "cursor-vscdb-merge") else wf["src_sha256"]
        if actual != expected_hash:
            errors.append(f"hash mismatch on {dst}: expected {expected_hash}, got {actual}")
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


def _restore_from_backup(root: Path, archive_path: Path, expected_archive_sha: str, expected_tree_sha: str) -> dict[str, Any]:
    actual_arch_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if actual_arch_sha != expected_archive_sha:
        raise ValueError(f"backup archive SHA-256 mismatch: expected {expected_archive_sha}, got {actual_arch_sha}")
    if root.exists():
        shutil.rmtree(root)
    ensure_private_dir(root)
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.issym() or member.islnk():
                raise ValueError(f"refusing symlink in backup archive: {member.name}")
            target_path = ensure_within_root(root / member.name, root, allow_root=True)
            if member.isdir():
                ensure_private_dir(target_path)
            elif member.isfile():
                extracted = tf.extractfile(member)
                if extracted is not None:
                    atomic_write_bytes(target_path, extracted.read(), mode=0o600)
    restored_count, restored_sha = compute_tree_sha256(root)
    return {
        "root": str(root),
        "restored_file_count": restored_count,
        "restored_tree_sha256": restored_sha,
        "expected_pristine_sha256": expected_tree_sha,
        "exact_match": restored_sha == expected_tree_sha,
    }


def rollback_transaction(tx_dir: str | Path) -> dict[str, Any]:
    """Restore target directory (and optional claude_dir) to exact pre-apply pristine SHA-256."""
    jroot = Path(tx_dir).expanduser().resolve()
    tx_file = jroot / "transaction.json" if jroot.is_dir() else jroot
    tx = json.loads(tx_file.read_text(encoding="utf-8"))

    primary = _restore_from_backup(
        Path(tx["target_root"]),
        Path(tx["backup_archive"]),
        tx["backup_sha256"],
        tx["pre_tree_sha256"],
    )
    extra = None
    if tx.get("claude_dir_backup"):
        cb = tx["claude_dir_backup"]
        extra = _restore_from_backup(
            Path(cb["root"]),
            Path(cb["backup_archive"]),
            cb["backup_sha256"],
            cb["pre_tree_sha256"],
        )

    ok = primary["exact_match"] and (extra["exact_match"] if extra is not None else True)
    return {
        "ok": ok,
        "transaction_id": tx.get("transaction_id"),
        "primary_restore": primary,
        "claude_dir_restore": extra,
    }
