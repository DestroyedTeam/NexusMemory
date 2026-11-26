"""Read-only cross-platform Harness auto-discovery (macOS / Windows / Linux).

Detects installed Harnesses, session stores, Skills roots, and MCP config paths without
reading or printing credential values. Explicitly separates:
- `claude-code` (local/self-hosted CLI, `~/.claude/`)
- `claude-desktop-3p` (`Claude-3p/` — Chat, Cowork, Code lanes)
- `claude-desktop-standard` (`Claude/` — legacy/consumer standard Desktop)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .claude_desktop_3p import default_claude_desktop_root


def _count_files(path: Path, pattern: str) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for p in path.rglob(pattern) if p.is_file())


def discover_harnesses(
    *,
    home: str | Path | None = None,
    project_dir: str | Path | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Deterministically discover Harness roots and session/resource presence (strictly read-only)."""
    hroot = Path(home).expanduser() if home is not None else Path.home()
    proot = Path(project_dir).expanduser() if project_dir is not None else None
    plat = platform or sys.platform

    c3p = default_claude_desktop_root(home=hroot, platform=plat, third_party=True)
    cstd = default_claude_desktop_root(home=hroot, platform=plat, third_party=False)
    cursor_base = (
        hroot / "Library/Application Support/Cursor"
        if plat == "darwin"
        else (hroot / "AppData/Roaming/Cursor" if plat == "win32" else hroot / ".config/Cursor")
    )

    probes: list[dict[str, Any]] = [
        {
            "id": "claude-code",
            "display_name": "Claude Code CLI (local / self-hosted API key or gateway)",
            "root": hroot / ".claude",
            "session_dir": hroot / ".claude/projects",
            "session_glob": "*.jsonl",
            "skills_dir": hroot / ".claude/skills",
            "mcp_config": hroot / ".claude.json",
        },
        {
            "id": "claude-desktop-3p-chat-cowork",
            "display_name": "Claude Desktop 3P (Chat & Cowork local-agent-mode-sessions)",
            "root": c3p,
            "session_dir": c3p / "local-agent-mode-sessions",
            "session_glob": "local_*.json",
            "skills_dir": hroot / ".claude/skills",
            "mcp_config": c3p / "claude_desktop_config.json",
        },
        {
            "id": "claude-desktop-3p-code",
            "display_name": "Claude Desktop 3P (Code claude-code-sessions index)",
            "root": c3p,
            "session_dir": c3p / "claude-code-sessions",
            "session_glob": "*.json",
            "skills_dir": hroot / ".claude/skills",
            "mcp_config": c3p / "claude_desktop_config.json",
        },
        {
            "id": "claude-desktop-standard",
            "display_name": "Claude Desktop (standard / non-3P root — kept distinct from Claude-3p)",
            "root": cstd,
            "session_dir": cstd / "local-agent-mode-sessions",
            "session_glob": "local_*.json",
            "skills_dir": hroot / ".claude/skills",
            "mcp_config": cstd / "claude_desktop_config.json",
        },
        {
            "id": "codex",
            "display_name": "OpenAI Codex CLI / App",
            "root": hroot / ".codex",
            "session_dir": hroot / ".codex/sessions",
            "session_glob": "*.jsonl*",
            "skills_dir": hroot / ".codex/skills",
            "mcp_config": hroot / ".codex/config.toml",
        },
        {
            "id": "opencode",
            "display_name": "OpenCode",
            "root": hroot / ".local/share/opencode",
            "session_dir": hroot / ".local/share/opencode/storage",
            "session_glob": "*.json",
            "skills_dir": hroot / ".config/opencode/skills",
            "mcp_config": hroot / ".config/opencode/opencode.json",
        },
        {
            "id": "cursor",
            "display_name": "Cursor",
            "root": cursor_base,
            "session_dir": cursor_base / "User/globalStorage",
            "session_glob": "state.vscdb",
            "skills_dir": hroot / ".cursor/skills",
            "mcp_config": hroot / ".cursor/mcp.json",
        },
        {
            "id": "windsurf",
            "display_name": "Windsurf",
            "root": hroot / ".codeium/windsurf",
            "session_dir": hroot / ".codeium/windsurf",
            "session_glob": "*.json",
            "skills_dir": hroot / ".windsurf/skills",
            "mcp_config": hroot / ".codeium/windsurf/mcp_config.json",
        },
        {
            "id": "dsh",
            "display_name": "DeepSeek Harness (DSH)",
            "root": hroot / ".dsh",
            "session_dir": hroot / ".dsh/sessions",
            "session_glob": "*.jsonl",
            "skills_dir": hroot / ".dsh/skills",
            "mcp_config": hroot / ".dsh/config.json",
        },
        {
            "id": "cline",
            "display_name": "Cline",
            "root": hroot / ".cline",
            "session_dir": hroot / ".cline/tasks",
            "session_glob": "api_conversation_history.json",
            "skills_dir": hroot / ".cline/skills",
            "mcp_config": hroot / ".cline/cline_mcp_settings.json",
        },
        {
            "id": "roo",
            "display_name": "Roo Code",
            "root": hroot / ".roo",
            "session_dir": hroot / ".roo/tasks",
            "session_glob": "api_conversation_history.json",
            "skills_dir": hroot / ".roo/skills",
            "mcp_config": hroot / ".roo/mcp.json",
        },
        {
            "id": "gemini-cli",
            "display_name": "Gemini CLI",
            "root": hroot / ".gemini",
            "session_dir": hroot / ".gemini/tmp",
            "session_glob": "session-*.json",
            "skills_dir": hroot / ".gemini/skills",
            "mcp_config": hroot / ".gemini/settings.json",
        },
        {
            "id": "antigravity",
            "display_name": "Google Antigravity",
            "root": hroot / ".gemini/antigravity",
            "session_dir": hroot / ".gemini/antigravity/brain",
            "session_glob": "transcript.jsonl",
            "skills_dir": hroot / ".gemini/config/skills",
            "mcp_config": hroot / ".gemini/config/mcp_config.json",
        },
        {
            "id": "pi",
            "display_name": "Pi Coding Agent",
            "root": hroot / ".pi",
            "session_dir": hroot / ".pi/agent/sessions",
            "session_glob": "*.jsonl",
            "skills_dir": hroot / ".pi/agent/skills",
            "mcp_config": hroot / ".pi/agent/settings.json",
        },
        {
            "id": "goose",
            "display_name": "Goose",
            "root": hroot / ".local/share/goose",
            "session_dir": hroot / ".local/share/goose/sessions",
            "session_glob": "*.jsonl",
            "skills_dir": hroot / ".config/goose/skills",
            "mcp_config": hroot / ".config/goose/config.yaml",
        },
        {
            "id": "continue",
            "display_name": "Continue",
            "root": hroot / ".continue",
            "session_dir": hroot / ".continue/sessions",
            "session_glob": "*.json",
            "skills_dir": hroot / ".continue/skills",
            "mcp_config": hroot / ".continue/config.json",
        },
        {
            "id": "zed",
            "display_name": "Zed / ACP",
            "root": hroot / ".config/zed",
            "session_dir": hroot / ".local/share/zed/threads",
            "session_glob": "*.json",
            "skills_dir": hroot / ".config/zed/skills",
            "mcp_config": hroot / ".config/zed/settings.json",
        },
        {
            "id": "kiro",
            "display_name": "AWS Kiro (CLI / IDE)",
            "root": hroot / ".kiro",
            "session_dir": hroot / ".kiro/sessions",
            "session_glob": "*.jsonl",
            "skills_dir": hroot / ".kiro/skills",
            "mcp_config": hroot / ".kiro/settings/mcp.json",
        },
        {
            "id": "workbuddy",
            "display_name": "Tencent WorkBuddy",
            "root": hroot / ".workbuddy",
            "session_dir": hroot / ".workbuddy/sessions",
            "session_glob": "*.jsonl",
            "skills_dir": hroot / ".workbuddy/skills",
            "mcp_config": hroot / ".workbuddy/mcp.json",
        },
        {
            "id": "t3code",
            "display_name": "T3 Code (t3code)",
            "root": hroot / ".t3",
            "session_dir": hroot / ".t3/userdata",
            "session_glob": "*.json",
            "skills_dir": hroot / ".t3/skills",
            "mcp_config": hroot / ".t3/userdata/settings.json",
        },
        {
            "id": "amp",
            "display_name": "Sourcegraph Amp",
            "root": hroot / ".local/share/amp",
            "session_dir": hroot / ".local/share/amp/threads",
            "session_glob": "*.json",
            "skills_dir": hroot / ".config/amp/skills",
            "mcp_config": hroot / ".config/amp/settings.json",
        },
        {
            "id": "trae",
            "display_name": "ByteDance Trae / Trae Agent",
            "root": hroot / ".trae",
            "session_dir": hroot / ".trae/trajectories",
            "session_glob": "*.json",
            "skills_dir": hroot / ".trae/skills",
            "mcp_config": hroot / ".trae/mcp.json",
        },
        {
            "id": "warp-oz",
            "display_name": "Warp / Oz Agent",
            "root": (hroot / "Library/Application Support/dev.warp.Warp-Stable") if plat == "darwin" else (hroot / ".warp"),
            "session_dir": hroot / ".warp/sessions",
            "session_glob": "*.json",
            "skills_dir": hroot / ".warp/skills",
            "mcp_config": hroot / ".warp/mcp.json",
        },
    ]

    detected: list[dict[str, Any]] = []
    for item in probes:
        root_p: Path = item["root"]
        sess_p: Path = item["session_dir"]
        skills_p: Path = item["skills_dir"]
        mcp_p: Path = item["mcp_config"]
        present = root_p.exists() or sess_p.exists() or skills_p.exists() or mcp_p.exists()
        if item["id"] == "t3code":
            sess_count = 0
            t3_db = root_p / "userdata" / "statev2.sqlite"
            if t3_db.is_file():
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{t3_db}?mode=ro", uri=True)
                    try:
                        row = con.execute(
                            "SELECT COUNT(*) FROM orchestration_v2_projection_threads WHERE deleted_at IS NULL"
                        ).fetchone()
                        sess_count = int(row[0]) if row else 0
                    finally:
                        con.close()
                except Exception:
                    sess_count = 0
        else:
            sess_count = _count_files(sess_p, item["session_glob"]) if sess_p.is_dir() else 0
        detected.append(
            {
                "id": item["id"],
                "display_name": item["display_name"],
                "detected": present,
                "root_path": str(root_p),
                "session_dir": str(sess_p),
                "session_file_count": sess_count,
                "skills_dir": str(skills_p),
                "skill_count": _count_files(skills_p, "SKILL.md") if skills_p.is_dir() else 0,
                "mcp_config_present": mcp_p.is_file(),
                "mcp_config_path": str(mcp_p),
            }
        )

    project_markers: dict[str, bool] = {}
    if proot and proot.is_dir():
        for name in (
            "CLAUDE.md",
            "AGENTS.md",
            ".mcp.json",
            ".claude/skills",
            ".codex/skills",
            ".agents/skills",
            ".cursor/rules",
            ".cursorrules",
            ".windsurfrules",
            ".clinerules",
            ".kiro/steering",
            ".aider.chat.history.md",
        ):
            project_markers[name] = (proot / name).exists()

    return {
        "schema": "nexus-memory.discovery.v1",
        "platform": plat,
        "home": str(hroot),
        "project_dir": str(proot) if proot else None,
        "detected_count": sum(1 for d in detected if d["detected"]),
        "harnesses": detected,
        "project_markers": project_markers,
        "privacy_note": "Read-only filesystem presence scan only; no credentials, tokens, or session bodies were exported or transmitted.",
    }
