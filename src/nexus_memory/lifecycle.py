"""Resource lifecycle, automatic backup pruning, post-verify cleanup, and memory reclamation.

Safety & engineering invariants:
- NEVER touches live Harness user data directories (`~/.codex`, `~/.claude`, `~/.t3`, etc.).
- Only removes positively verified Nexus Memory backup archives (`pristine_*_backup.tar.gz` inside
  a `nexus-memory.transaction.*` journal), verified staged bundles (`nexus-memory.bundle-manifest.v1`),
  and Nexus Memory temporary sandbox directories inside the OS temp directory.
- Enforces `ensure_within_root` before unlinking any archive inside a transaction journal.
- Keeps an auditable lightweight receipt (`transaction.json`, ~2 KB) after cleaning bulky `.tar.gz`
  backups unless full bundle removal is explicitly requested.
- Provides deterministic memory reclamation (`gc.collect()` across all generations + optional
  `malloc_trim(0)` on Linux) and stdlib live RSS telemetry on macOS, Linux, and Windows.
"""

from __future__ import annotations

import ctypes
import gc
import json
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .security import atomic_write_json, ensure_within_root

DEFAULT_MAX_KEEP_TRANSACTIONS = 3
DEFAULT_MAX_AGE_DAYS = 7.0
DEFAULT_MAX_TOTAL_BACKUP_MB = 512.0
DEFAULT_SANDBOX_MAX_AGE_HOURS = 24.0

_TEMP_DIR_PREFIXES = (
    "nexus-memory-sandbox",
    "nexus-memory-e2e",
    "nexus-memory-gui-e2e",
    "nexus-memory-version-check",
    "nexus-t3-",
    "nexus-verify-",
)


def get_process_memory_mb() -> float:
    """Return current process resident memory (RSS) in MiB using pure stdlib/OS APIs."""
    # 1. Linux live RSS from /proc/self/statm
    if sys.platform.startswith("linux"):
        try:
            parts = Path("/proc/self/statm").read_text(encoding="ascii").split()
            if len(parts) >= 2:
                pages = int(parts[1])
                page_size = os.sysconf("SC_PAGE_SIZE")
                return round((pages * page_size) / (1024 * 1024), 2)
        except Exception:
            pass
    # 2. macOS live RSS via mach_task_basic_info
    if sys.platform == "darwin":
        try:
            libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib")

            class _TimeValue(ctypes.Structure):
                _fields_ = [("seconds", ctypes.c_int), ("microseconds", ctypes.c_int)]

            class _MachTaskBasicInfo(ctypes.Structure):
                _fields_ = [
                    ("virtual_size", ctypes.c_uint64),
                    ("resident_size", ctypes.c_uint64),
                    ("resident_size_max", ctypes.c_uint64),
                    ("user_time", _TimeValue),
                    ("system_time", _TimeValue),
                    ("policy", ctypes.c_int),
                    ("suspend_count", ctypes.c_int),
                ]

            MACH_TASK_BASIC_INFO = 20
            info = _MachTaskBasicInfo()
            count = ctypes.c_uint32(ctypes.sizeof(info) // ctypes.sizeof(ctypes.c_int32))
            libc.mach_task_self.restype = ctypes.c_uint32
            task = libc.mach_task_self()
            kr = libc.task_info(
                ctypes.c_uint32(task),
                ctypes.c_int(MACH_TASK_BASIC_INFO),
                ctypes.byref(info),
                ctypes.byref(count),
            )
            if kr == 0 and info.resident_size > 0:
                return round(info.resident_size / (1024 * 1024), 2)
        except Exception:
            pass
    # 3. Windows live WorkingSetSize via psapi
    if sys.platform == "win32":
        try:
            class _ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_uint32),
                    ("PageFaultCount", ctypes.c_uint32),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = _ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            hproc = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(hproc, ctypes.byref(counters), counters.cb):
                return round(counters.WorkingSetSize / (1024 * 1024), 2)
        except Exception:
            pass
    # 4. POSIX fallback (peak RSS)
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        divisor = (1024 * 1024) if sys.platform == "darwin" else 1024
        return round(usage / divisor, 2)
    except Exception:
        return 0.0


def reclaim_memory() -> dict[str, Any]:
    """Run full cyclic GC and optional OS allocator trim to release memory after heavy jobs."""
    before = get_process_memory_mb()
    collected = 0
    for gen in (0, 1, 2):
        collected += gc.collect(gen)
    if sys.platform.startswith("linux"):
        try:
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception:
            pass
    after = get_process_memory_mb()
    return {
        "before_rss_mb": before,
        "after_rss_mb": after,
        "freed_mb": round(max(0.0, before - after), 2),
        "gc_collected": collected,
    }


def _dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    if path.is_file() and not path.is_symlink():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    for root, _dirs, files in os.walk(path, followlinks=False):
        for fn in files:
            fp = Path(root) / fn
            try:
                if not fp.is_symlink():
                    total += fp.stat().st_size
            except OSError:
                continue
    return total


def _is_verified_bundle_dir(path: Path) -> bool:
    manifest_p = path / "manifest.json"
    portable_p = path / "portable.json"
    if not manifest_p.is_file() or manifest_p.is_symlink() or not portable_p.is_file():
        return False
    try:
        obj = json.loads(manifest_p.read_text(encoding="utf-8"))
        schema = str(obj.get("schema") or "") if isinstance(obj, dict) else ""
        return schema.startswith(("nexus-memory.migration-manifest.", "nexus-memory.bundle-manifest."))
    except (OSError, json.JSONDecodeError):
        return False


def _load_tx_record(tx_dir: Path) -> tuple[Path, dict[str, Any]] | None:
    tx_file = tx_dir / "transaction.json" if tx_dir.is_dir() else tx_dir
    if not tx_file.is_file() or tx_file.is_symlink():
        return None
    try:
        obj = json.loads(tx_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(obj, dict) or not str(obj.get("schema") or "").startswith("nexus-memory.transaction."):
        return None
    return tx_file.parent.resolve(), obj


def _parse_iso_age_hours(ts: str | None, fallback_path: Path) -> float:
    now = time.time()
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return max(0.0, (now - dt.timestamp()) / 3600.0)
        except ValueError:
            pass
    try:
        return max(0.0, (now - fallback_path.stat().st_mtime) / 3600.0)
    except OSError:
        return 0.0


def _collect_tx_backup_files(jroot: Path, tx: dict[str, Any]) -> list[Path]:
    """Return existing backup archive files strictly contained within `jroot`."""
    candidates: list[Path] = []
    for raw_p in (
        tx.get("backup_archive"),
        (tx.get("claude_dir_backup") or {}).get("backup_archive") if isinstance(tx.get("claude_dir_backup"), dict) else None,
        str(jroot / "pristine_target_backup.tar.gz"),
        str(jroot / "pristine_claude_backup.tar.gz"),
    ):
        if not raw_p:
            continue
        try:
            safe = ensure_within_root(Path(str(raw_p)), jroot)
        except ValueError:
            continue
        if safe.is_file() and not safe.is_symlink() and safe not in candidates:
            candidates.append(safe)
    return candidates


def _describe_transaction(jroot: Path, tx: dict[str, Any]) -> dict[str, Any]:
    backup_files = _collect_tx_backup_files(jroot, tx)
    backup_bytes = sum(_dir_size_bytes(f) for f in backup_files)
    total_bytes = _dir_size_bytes(jroot)
    pv = tx.get("post_write_verification") if isinstance(tx.get("post_write_verification"), dict) else {}
    return {
        "transaction_id": str(tx.get("transaction_id") or jroot.name),
        "journal_dir": str(jroot),
        "bundle": str(tx.get("bundle") or ""),
        "target_lane": str(tx.get("target_lane") or ""),
        "target_root": str(tx.get("target_root") or ""),
        "applied_at": str(tx.get("applied_at") or ""),
        "age_hours": round(_parse_iso_age_hours(tx.get("applied_at"), jroot), 2),
        "verified_ok": bool(pv.get("ok", False)),
        "backup_exists": len(backup_files) > 0,
        "backup_cleaned": bool(tx.get("backup_cleaned", False)),
        "rolled_back": bool(tx.get("rolled_back", False)),
        "backup_bytes": backup_bytes,
        "total_bytes": total_bytes,
    }


def _allowed_temp_roots() -> list[Path]:
    roots: list[Path] = []
    candidates: list[Path | None] = [Path(tempfile.gettempdir()), Path("/tmp") if os.name != "nt" else None]
    if sys.platform == "darwin":
        try:
            buf = ctypes.create_string_buffer(1024)
            # _CS_DARWIN_USER_TEMP_DIR = 65537 (finds macOS per-user /var/folders/.../T even when TMPDIR is overridden)
            n = ctypes.CDLL("/usr/lib/libSystem.B.dylib").confstr(65537, buf, len(buf))
            if n > 0 and buf.value:
                candidates.append(Path(buf.value.decode("utf-8", errors="ignore")))
        except Exception:
            pass
    for cand in candidates:
        if cand is None:
            continue
        try:
            resolved = cand.resolve()
        except OSError:
            continue
        if resolved.is_dir() and resolved not in roots:
            roots.append(resolved)
    return roots


def _is_verified_temp_dir(path: Path) -> bool:
    if not path.is_dir() or path.is_symlink():
        return False
    name = path.name
    if not any(name == pfx or name.startswith(pfx) for pfx in _TEMP_DIR_PREFIXES):
        return False
    resolved = path.resolve()
    return any(resolved.is_relative_to(tr) and resolved != tr for tr in _allowed_temp_roots())


def scan_reclaimable_storage(
    *,
    extra_roots: Sequence[str | Path] | None = None,
    include_temp: bool = True,
    include_desktop: bool = True,
) -> dict[str, Any]:
    """Read-only inventory of reclaimable Nexus Memory backups, staged bundles, and temp sandboxes."""
    seen_tx: dict[Path, dict[str, Any]] = {}
    seen_bundles: dict[Path, dict[str, Any]] = {}
    seen_sandboxes: dict[Path, dict[str, Any]] = {}

    candidate_dirs: list[Path] = []
    if include_desktop:
        desktop = Path.home() / "Desktop"
        if desktop.is_dir():
            for child in sorted(desktop.iterdir()):
                if child.is_dir() and not child.is_symlink() and child.name.startswith("nexus-memory-bundle"):
                    candidate_dirs.append(child)
    if extra_roots:
        for raw in extra_roots:
            p = Path(raw).expanduser()
            if not p.exists() or p.is_symlink():
                continue
            if p.is_dir():
                candidate_dirs.append(p)
                # Also inspect direct bundle/transaction children under a container folder
                if not _is_verified_bundle_dir(p) and not (p / "transaction.json").is_file():
                    try:
                        for child in sorted(p.iterdir()):
                            if child.is_dir() and not child.is_symlink():
                                if _is_verified_bundle_dir(child) or (child / "transaction.json").is_file() or child.name == ".transactions":
                                    candidate_dirs.append(child)
                    except OSError:
                        pass

    for cdir in candidate_dirs:
        try:
            rc = cdir.resolve()
        except OSError:
            continue
        loaded = _load_tx_record(rc)
        if loaded is not None:
            jroot, tx = loaded
            seen_tx[jroot] = _describe_transaction(jroot, tx)
            continue
        if rc.name == ".transactions":
            try:
                for tx_child in sorted(rc.iterdir()):
                    loaded_t = _load_tx_record(tx_child)
                    if loaded_t is not None:
                        jroot, tx = loaded_t
                        seen_tx[jroot] = _describe_transaction(jroot, tx)
            except OSError:
                pass
            continue
        if _is_verified_bundle_dir(rc):
            tx_parent = rc / ".transactions"
            tx_count = 0
            has_active_bk = False
            if tx_parent.is_dir():
                for tx_child in sorted(tx_parent.iterdir()):
                    loaded_t = _load_tx_record(tx_child)
                    if loaded_t is not None:
                        jroot, tx = loaded_t
                        desc = _describe_transaction(jroot, tx)
                        seen_tx[jroot] = desc
                        tx_count += 1
                        if desc["backup_exists"]:
                            has_active_bk = True
            try:
                m_obj = json.loads((rc / "manifest.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                m_obj = {}
            seen_bundles[rc] = {
                "path": str(rc),
                "name": rc.name,
                "target_lane": str(m_obj.get("target_lane") or ""),
                "conversation_count": int(m_obj.get("conversation_count") or 0),
                "size_bytes": _dir_size_bytes(rc),
                "age_hours": round(_parse_iso_age_hours(None, rc), 2),
                "tx_count": tx_count,
                "has_active_backup": has_active_bk,
            }

    if include_temp:
        for troot in _allowed_temp_roots():
            try:
                children = sorted(troot.iterdir())
            except OSError:
                continue
            for child in children:
                if _is_verified_temp_dir(child):
                    rc = child.resolve()
                    if rc not in seen_sandboxes:
                        seen_sandboxes[rc] = {
                            "path": str(rc),
                            "name": rc.name,
                            "size_bytes": _dir_size_bytes(rc),
                            "age_hours": round(_parse_iso_age_hours(None, rc), 2),
                        }

    transactions = sorted(seen_tx.values(), key=lambda x: x["age_hours"])
    bundles = sorted(seen_bundles.values(), key=lambda x: x["age_hours"])
    sandboxes = sorted(seen_sandboxes.values(), key=lambda x: x["age_hours"])

    active_backup_bytes = sum(t["backup_bytes"] for t in transactions if t["backup_exists"])
    bundle_bytes = sum(b["size_bytes"] for b in bundles)
    sandbox_bytes = sum(s["size_bytes"] for s in sandboxes)
    # Bundles already include their nested `.transactions/` size; compute non-overlapping total
    bundle_roots = [Path(b["path"]).resolve() for b in bundles]
    standalone_tx_bytes = sum(
        t["backup_bytes"]
        for t in transactions
        if t["backup_exists"] and not any(Path(t["journal_dir"]).resolve().is_relative_to(br) for br in bundle_roots)
    )
    total_reclaimable_bytes = bundle_bytes + standalone_tx_bytes + sandbox_bytes

    return {
        "schema": "nexus-memory.storage-inventory.v1",
        "transactions": transactions,
        "bundles": bundles,
        "sandboxes": sandboxes,
        "summary": {
            "active_backup_count": sum(1 for t in transactions if t["backup_exists"]),
            "total_transaction_count": len(transactions),
            "active_backup_bytes": active_backup_bytes,
            "bundle_count": len(bundles),
            "bundle_bytes": bundle_bytes,
            "sandbox_count": len(sandboxes),
            "sandbox_bytes": sandbox_bytes,
            "total_reclaimable_bytes": total_reclaimable_bytes,
            "total_reclaimable_mb": round(total_reclaimable_bytes / (1024 * 1024), 2),
            "process_rss_mb": get_process_memory_mb(),
        },
    }


def cleanup_transaction_backup(
    tx_dir: str | Path,
    *,
    remove_bundle: bool = False,
    mark_confirmed: bool = True,
    keep_receipt: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Delete pristine `.tar.gz` backup archives for a verified/confirmed transaction (and optionally its staged bundle)."""
    loaded = _load_tx_record(Path(tx_dir).expanduser())
    if loaded is None:
        raise ValueError(f"not a valid Nexus Memory transaction directory: {tx_dir}")
    jroot, tx = loaded
    backup_files = _collect_tx_backup_files(jroot, tx)
    reclaimed = 0
    removed: list[str] = []

    if remove_bundle:
        bundle_raw = tx.get("bundle")
        bundle_p = Path(str(bundle_raw)).expanduser().resolve() if bundle_raw else None
        if bundle_p is None or not _is_verified_bundle_dir(bundle_p):
            raise ValueError(f"refusing remove_bundle: not a verified Nexus Memory bundle directory ({bundle_raw})")
        bsize = _dir_size_bytes(bundle_p)
        reclaimed += bsize
        removed.append(str(bundle_p))
        if not dry_run:
            shutil.rmtree(bundle_p)
            # If journal lived outside the bundle, clean its backup archives too
            if jroot.exists() and not jroot.is_relative_to(bundle_p):
                for bf in backup_files:
                    if bf.is_file():
                        reclaimed += _dir_size_bytes(bf)
                        bf.unlink(missing_ok=True)
                        removed.append(str(bf))
        return {
            "ok": True,
            "dry_run": dry_run,
            "transaction_id": tx.get("transaction_id"),
            "removed_bundle": True,
            "reclaimed_bytes": reclaimed,
            "reclaimed_mb": round(reclaimed / (1024 * 1024), 2),
            "removed_paths": removed,
            "memory": reclaim_memory() if not dry_run else None,
        }

    for bf in backup_files:
        sz = _dir_size_bytes(bf)
        reclaimed += sz
        removed.append(str(bf))
        if not dry_run:
            bf.unlink(missing_ok=True)

    if not keep_receipt:
        extra_sz = max(0, _dir_size_bytes(jroot) - (0 if not dry_run else reclaimed))
        reclaimed += extra_sz if dry_run else _dir_size_bytes(jroot)
        removed.append(str(jroot))
        if not dry_run:
            shutil.rmtree(jroot, ignore_errors=True)
            parent = jroot.parent
            if parent.name == ".transactions":
                try:
                    parent.rmdir()
                except OSError:
                    pass
    elif not dry_run:
        tx["backup_cleaned"] = True
        tx["confirmed_by_user"] = bool(mark_confirmed)
        tx["backup_cleaned_at"] = datetime.now(UTC).isoformat()
        tx["reclaimed_backup_bytes"] = int(tx.get("reclaimed_backup_bytes") or 0) + reclaimed
        atomic_write_json(jroot / "transaction.json", tx, mode=0o600)

    return {
        "ok": True,
        "dry_run": dry_run,
        "transaction_id": tx.get("transaction_id"),
        "removed_bundle": False,
        "keep_receipt": keep_receipt,
        "reclaimed_bytes": reclaimed,
        "reclaimed_mb": round(reclaimed / (1024 * 1024), 2),
        "removed_paths": removed,
        "memory": reclaim_memory() if not dry_run else None,
    }


def delete_bundle_dir(bundle_dir: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Safely delete a verified Nexus Memory staged bundle directory (checks `manifest.json` schema first)."""
    broot = Path(bundle_dir).expanduser().resolve()
    if not _is_verified_bundle_dir(broot):
        raise ValueError(f"refusing to delete non-Nexus directory (missing valid manifest.json): {broot}")
    size = _dir_size_bytes(broot)
    if not dry_run:
        shutil.rmtree(broot)
    return {
        "ok": True,
        "dry_run": dry_run,
        "path": str(broot),
        "reclaimed_bytes": size,
        "reclaimed_mb": round(size / (1024 * 1024), 2),
        "memory": reclaim_memory() if not dry_run else None,
    }


def prune_reclaimable_storage(
    *,
    extra_roots: Sequence[str | Path] | None = None,
    max_keep_transactions: int = DEFAULT_MAX_KEEP_TRANSACTIONS,
    max_age_days: float = DEFAULT_MAX_AGE_DAYS,
    max_total_backup_mb: float = DEFAULT_MAX_TOTAL_BACKUP_MB,
    clean_sandboxes: bool = True,
    sandbox_max_age_hours: float = DEFAULT_SANDBOX_MAX_AGE_HOURS,
    clean_bundles: bool = False,
    bundle_max_keep: int = 2,
    dry_run: bool = True,
    include_temp: bool = True,
    include_desktop: bool = True,
) -> dict[str, Any]:
    """Apply retention policy to prune stale transaction backups, temp sandboxes, and optional old bundles."""
    inv = scan_reclaimable_storage(
        extra_roots=extra_roots,
        include_temp=include_temp,
        include_desktop=include_desktop,
    )
    pruned_txs: list[dict[str, Any]] = []
    pruned_sandboxes: list[dict[str, Any]] = []
    pruned_bundles: list[dict[str, Any]] = []
    reclaimed_bytes = 0

    # 1. Prune active transaction backup archives (sorted newest-first by age_hours)
    active_txs = [t for t in inv["transactions"] if t["backup_exists"]]
    kept_bytes = 0
    kept_count = 0
    max_budget_bytes = int(max(0.0, max_total_backup_mb) * 1024 * 1024)
    max_age_hours = max(0.0, max_age_days) * 24.0
    min_keep = 1 if max_keep_transactions >= 1 else 0

    for t in active_txs:
        reasons: list[str] = []
        if kept_count >= max_keep_transactions:
            reasons.append(f"exceeds keep limit ({max_keep_transactions})")
        if max_age_days >= 0 and t["age_hours"] > max_age_hours and kept_count >= min_keep:
            reasons.append(f"older than {max_age_days:g}d")
        if max_budget_bytes > 0 and (kept_bytes + t["backup_bytes"]) > max_budget_bytes and kept_count >= min_keep:
            reasons.append(f"exceeds {max_total_backup_mb:g} MB budget")

        if reasons:
            res = cleanup_transaction_backup(
                t["journal_dir"],
                remove_bundle=False,
                mark_confirmed=False,
                keep_receipt=True,
                dry_run=dry_run,
            )
            reclaimed_bytes += res["reclaimed_bytes"]
            pruned_txs.append(
                {
                    "transaction_id": t["transaction_id"],
                    "journal_dir": t["journal_dir"],
                    "reclaimed_bytes": res["reclaimed_bytes"],
                    "reasons": reasons,
                }
            )
        else:
            kept_count += 1
            kept_bytes += t["backup_bytes"]

    # 2. Prune expired temp sandboxes / test directories
    if clean_sandboxes:
        for sb in inv["sandboxes"]:
            if sandbox_max_age_hours <= 0 or sb["age_hours"] >= sandbox_max_age_hours:
                sbp = Path(sb["path"]).resolve()
                if _is_verified_temp_dir(sbp):
                    sz = sb["size_bytes"]
                    if not dry_run:
                        shutil.rmtree(sbp, ignore_errors=True)
                    reclaimed_bytes += sz
                    pruned_sandboxes.append({"path": sb["path"], "reclaimed_bytes": sz})

    # 3. Optionally prune older staged bundles (keeping newest `bundle_max_keep`)
    if clean_bundles:
        for idx, b in enumerate(inv["bundles"]):
            if idx >= max(0, bundle_max_keep):
                bp = Path(b["path"]).resolve()
                if bp.is_dir() and _is_verified_bundle_dir(bp):
                    sz = _dir_size_bytes(bp)
                    if not dry_run:
                        shutil.rmtree(bp, ignore_errors=True)
                    reclaimed_bytes += sz
                    pruned_bundles.append({"path": b["path"], "reclaimed_bytes": sz})

    mem = reclaim_memory() if not dry_run else None
    after_inv = (
        scan_reclaimable_storage(
            extra_roots=extra_roots,
            include_temp=include_temp,
            include_desktop=include_desktop,
        )
        if not dry_run
        else inv
    )
    return {
        "ok": True,
        "dry_run": dry_run,
        "pruned_transactions": pruned_txs,
        "pruned_sandboxes": pruned_sandboxes,
        "pruned_bundles": pruned_bundles,
        "reclaimed_bytes": reclaimed_bytes,
        "reclaimed_mb": round(reclaimed_bytes / (1024 * 1024), 2),
        "remaining_summary": after_inv["summary"],
        "memory": mem,
    }
