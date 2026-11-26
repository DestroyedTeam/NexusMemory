"""Security primitives: secret scanning/redaction, fence sanitization, and path containment.

Incorporates concrete lessons from the 326-repo Nexus Memory audit:
- Precision-over-recall secret redaction (never breaks UUIDs/git SHAs/token_count,
  always strips credentials before MCP configs, derived summaries, or handoff prompts).
- Fence-breaking prompt-injection sanitization for titles/metadata embedded in handoffs.
- Strict `Path.resolve().is_relative_to(root.resolve())` containment and symlink checks
  (prevents `../` traversal and sibling prefix-collision bypasses).
- Single-segment safe filesystem name sanitizer.
- Private file/directory permissions (`0o700` dirs, `0o600` files) and atomic writes.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

# Ordered: multi-line PEM blocks first, then vendor-prefixed high-precision tokens.
# Keys for original prototype patterns remain identical for test compatibility.
PATTERNS: dict[str, re.Pattern[str]] = {
    "private_key_block": re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"
        r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "anthropic_api_key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai_api_key": re.compile(r"sk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{24,}"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{22,})\b"),
    "aws_access_key_id": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "stripe_key": re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[0-9A-Za-z]{16,}\b"),
    "slack_token": re.compile(r"\bxox[abposr]-[0-9A-Za-z-]{10,}\b"),
    "npm_token": re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b"),
    "jwt_token": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
}

BEARER_RE = re.compile(r"\b(Bearer\s+)[A-Za-z0-9._~+/=-]{20,}")
ASSIGNMENT_RE = re.compile(
    r"\b([A-Za-z0-9_]*(?:api[_-]?key|secret|token|passw(?:or)?d|_pat|auth_header)\b"
    r"[\"']?\s*[:=]\s*[\"']?)([^\s\"'`,;)}\]]{12,})",
    re.IGNORECASE,
)

SECRET_ENV_KEY_RE = re.compile(
    r"(?:^|_)(?:key|api_?key|secret|token|pass|password|pwd|auth|authorization|cookie|session|credential|pat|bearer|dsn|private)(?:$|_)",
    re.IGNORECASE,
)

FENCE_TAG_RE = re.compile(r"</?\s*(?:historical_context|nexus_handoff|system|instructions|tool_output)\b[^>]*>", re.IGNORECASE)


def scan_secret_markers(value: Any) -> dict[str, int]:
    """Return secret marker counts by category; never return matched secret values."""
    serialized = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    found: Counter[str] = Counter()
    for label, pattern in PATTERNS.items():
        count = len(pattern.findall(serialized))
        if count:
            found[label] = count
    bearer_count = len(BEARER_RE.findall(serialized))
    if bearer_count:
        found["bearer_token"] = bearer_count
    return {label: count for label, count in sorted(found.items()) if count}


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    """Redact credentials in text while preserving variable labels for human/agent diagnostics."""
    if not isinstance(text, str) or len(text) < 12:
        return (text if isinstance(text, str) else ""), {}
    counts: Counter[str] = Counter()
    out = text
    for label, pattern in PATTERNS.items():
        out, n = pattern.subn(f"[REDACTED:{label}]", out)
        if n:
            counts[label] += n
    out, n = BEARER_RE.subn(r"\1[REDACTED:bearer_token]", out)
    if n:
        counts["bearer_token"] += n
    out, n = ASSIGNMENT_RE.subn(r"\1[REDACTED:secret_assignment]", out)
    if n:
        counts["secret_assignment"] += n
    return out, {k: v for k, v in sorted(counts.items()) if v}


def is_secret_env_key(key: str) -> bool:
    """Return True if an env var or HTTP header name likely carries a credential."""
    if not key:
        return False
    normalized = key.replace("-", "_")
    return bool(SECRET_ENV_KEY_RE.search(normalized))


def sanitize_mcp_mapping(mapping: dict[str, Any] | None) -> tuple[dict[str, str], tuple[str, ...], dict[str, int]]:
    """Convert raw MCP env/headers into safe `${VAR}` templates without copying secrets."""
    if not isinstance(mapping, dict):
        return {}, (), {}
    safe: dict[str, str] = {}
    stripped: list[str] = []
    counts: Counter[str] = Counter()
    for raw_key, raw_val in mapping.items():
        key = str(raw_key)
        val = "" if raw_val is None else str(raw_val)
        already_placeholder = val.startswith("${") and val.endswith("}")
        val_hits = scan_secret_markers(val)
        if is_secret_env_key(key) or val_hits:
            env_ref = re.sub(r"[^A-Za-z0-9_]", "_", key).upper()
            safe[key] = val if already_placeholder else f"${{{env_ref}}}"
            if not already_placeholder and val:
                stripped.append(key)
                counts["mcp_secret_env"] += 1
                for k, v in val_hits.items():
                    counts[k] += v
        else:
            redacted, rcounts = redact_text(val)
            safe[key] = redacted
            for k, v in rcounts.items():
                counts[k] += v
    return safe, tuple(sorted(set(stripped))), dict(counts)


def sanitize_handoff_text(text: str) -> str:
    """Neutralize prompt-injection fence tags and redact credentials before handoff rendering."""
    redacted, _ = redact_text(text)
    return FENCE_TAG_RE.sub(lambda m: m.group(0).replace("<", "&lt;").replace(">", "&gt;"), redacted)


def sanitize_single_segment(name: str, *, fallback: str = "unnamed", max_len: int = 128) -> str:
    """Sanitize a caller/source-supplied directory or skill name to one safe path segment."""
    cleaned = re.sub(r"[/\\\x00:*?\"<>|\r\n\t]", "_", name or "")
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    cleaned = cleaned.strip(". ")
    if not cleaned or cleaned in {".", ".."}:
        return fallback
    return cleaned[:max_len]


def ensure_within_root(target: str | Path, root: str | Path, *, allow_root: bool = False) -> Path:
    """Verify `target` resolves strictly inside `root` without traversal or symlink escape."""
    root_resolved = Path(root).expanduser().resolve()
    target_path = Path(target).expanduser()
    # Reject raw null bytes or unnormalized '..' escapes before and after resolution
    if "\x00" in str(target_path):
        raise ValueError("path contains NUL byte")
    resolved = target_path.resolve()
    if resolved == root_resolved:
        if allow_root:
            return resolved
        raise ValueError(f"path resolves to root itself: {target}")
    if not resolved.is_relative_to(root_resolved):
        raise ValueError(f"path escapes allowed root ({root_resolved}): {target}")
    return resolved


def ensure_private_dir(path: Path) -> Path:
    """Create directory with owner-only `0o700` permissions."""
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def atomic_write_bytes(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    """Atomically write bytes via a same-directory temp file + `os.replace` with `0o600` mode."""
    ensure_private_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    closed = False
    try:
        if os.name != "nt":
            try:
                os.chmod(fd, mode)
            except OSError:
                pass
        with os.fdopen(fd, "wb") as handle:
            closed = True
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        if os.name != "nt":
            try:
                path.chmod(mode)
            except OSError:
                pass
    except Exception:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, value: Any, *, mode: int = 0o600) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    atomic_write_bytes(path, payload, mode=mode)
