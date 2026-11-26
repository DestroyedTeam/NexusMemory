"""Two-stage write protection gate (corrupt-config fail-safe + cloud-sync folder guard).

Adapted from Apache-2.0 architectural patterns observed in `rpeck/claude-explorer`:
1. Corrupt config guard: a malformed config file never crashes read-only commands,
   surfaces an explicit `config_corrupt_reason`, and blocks writes until fixed.
2. Cloud-sync guard: refuses mutating writes inside cloud-synced folders (Dropbox,
   iCloud Drive, OneDrive, Google Drive) unless the caller explicitly consents to
   the exact resolved target path (`allow_writes_in_cloud_sync`). Moving the target
   automatically re-closes the gate.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CLOUD_SYNC_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("iCloud Drive", ("library/mobile documents", "com~apple~clouddocs")),
    ("Dropbox", ("/dropbox/", "/dropbox")),
    ("OneDrive", ("/onedrive", "/cloudstorage/onedrive")),
    ("Google Drive", ("/google drive", "/cloudstorage/googledrive")),
    ("Box", ("/cloudstorage/box-box", "/box sync")),
)


@dataclass(frozen=True, slots=True)
class GateConfig:
    config_path: Path | None = None
    allow_writes_in_cloud_sync: str | None = None
    config_corrupt_reason: str | None = None


@dataclass(frozen=True, slots=True)
class WriteGateDecision:
    allowed: bool
    reason: str | None = None
    cloud_provider: str | None = None
    resolved_target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "cloud_provider": self.cloud_provider,
            "resolved_target": self.resolved_target,
        }


def _norm_path(path: str | Path) -> str:
    real = os.path.realpath(str(Path(path).expanduser()))
    return real.casefold() if sys.platform in ("darwin", "win32") else real


def load_gate_config(config_path: Path | None = None) -> GateConfig:
    """Safely load optional Nexus Memory config without crashing on corrupt JSON."""
    if config_path is None:
        return GateConfig()
    resolved = Path(config_path).expanduser()
    if not resolved.exists():
        return GateConfig(config_path=resolved)
    try:
        parsed = json.loads(resolved.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            return GateConfig(
                config_path=resolved,
                config_corrupt_reason=f"{resolved}: root is not a JSON object",
            )
        allowed = parsed.get("allow_writes_in_cloud_sync")
        return GateConfig(
            config_path=resolved,
            allow_writes_in_cloud_sync=allowed if isinstance(allowed, str) and allowed else None,
            config_corrupt_reason=None,
        )
    except (json.JSONDecodeError, OSError, ValueError, TypeError) as exc:
        return GateConfig(
            config_path=resolved,
            config_corrupt_reason=f"{resolved}: {type(exc).__name__}: {exc}",
        )


def detect_cloud_sync(path: str | Path) -> str | None:
    """Return cloud-sync provider name if `path` resolves inside a known synced folder."""
    real = os.path.realpath(str(Path(path).expanduser())).replace("\\", "/").lower()
    padded = real if real.endswith("/") else real + "/"
    for provider, markers in CLOUD_SYNC_MARKERS:
        for marker in markers:
            if marker in padded:
                return provider
    return None


def check_write_gate(
    target_path: str | Path,
    *,
    gate_config: GateConfig | None = None,
    allow_cloud_sync_path: str | Path | None = None,
) -> WriteGateDecision:
    """Evaluate Stage 1 (corrupt config) and Stage 2 (cloud-sync folder) before writing."""
    resolved_str = os.path.realpath(str(Path(target_path).expanduser()))
    cfg = gate_config or GateConfig()

    if cfg.config_corrupt_reason:
        return WriteGateDecision(
            allowed=False,
            reason=f"corrupt_config: {cfg.config_corrupt_reason}",
            resolved_target=resolved_str,
        )

    provider = detect_cloud_sync(resolved_str)
    if provider is not None:
        consented = allow_cloud_sync_path or cfg.allow_writes_in_cloud_sync
        if consented and _norm_path(consented) == _norm_path(resolved_str):
            return WriteGateDecision(
                allowed=True,
                cloud_provider=provider,
                resolved_target=resolved_str,
            )
        return WriteGateDecision(
            allowed=False,
            reason=(
                f"cloud_sync_gate: target resolves inside {provider}-synced folder; "
                "pass explicit --allow-cloud-sync-path matching the exact target path to opt in"
            ),
            cloud_provider=provider,
            resolved_target=resolved_str,
        )

    return WriteGateDecision(allowed=True, resolved_target=resolved_str)
