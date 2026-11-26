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


def _count_skill_dirs(skills_dir: Path) -> int:
    """Count valid skills under `skills_dir`, including 1-level symlinked skill folders (e.g. cc-switch / npx skills)."""
    if not skills_dir.is_dir():
        return 0
    seen_real: set[Path] = set()
    count = 0
    try:
        for child in skills_dir.iterdir():
            if child.name.startswith("."):
                continue
            try:
                if child.is_dir() and (child / "SKILL.md").is_file():
                    rp = (child / "SKILL.md").resolve()
                    if rp not in seen_real:
                        seen_real.add(rp)
                        count += 1
            except OSError:
                continue
    except OSError:
        return 0
    if count > 0:
        return count
    return _count_files(skills_dir, "SKILL.md")


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
    zed_threads_dir = (
        hroot / "Library/Application Support/Zed/threads"
        if plat == "darwin" and (hroot / "Library/Application Support/Zed").exists()
        else hroot / ".local/share/zed/threads"
    )
    zed_root = (
        hroot / "Library/Application Support/Zed"
        if plat == "darwin" and (hroot / "Library/Application Support/Zed").exists()
        else hroot / ".config/zed"
    )
    kiro_cli_db = (
        hroot / "Library/Application Support/kiro-cli/data.sqlite3"
        if plat == "darwin"
        else (hroot / "AppData/Local/kiro-cli/data.sqlite3" if plat == "win32" else hroot / ".local/share/kiro-cli/data.sqlite3")
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
            "session_glob": "local_*.json",
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
            "root": zed_root,
            "session_dir": zed_threads_dir,
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
            "extra_db": kiro_cli_db,
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
        if item["id"] == "warp-oz" and not mcp_p.is_file() and (hroot / ".warp" / ".mcp.json").is_file():
            mcp_p = hroot / ".warp" / ".mcp.json"
        present = root_p.exists() or sess_p.exists() or skills_p.exists() or mcp_p.exists()
        subagent_count = 0
        if item["id"] == "t3code":
            sess_count = 0
            t3_db = root_p / "userdata" / "statev2.sqlite"
            if t3_db.is_file():
                try:
                    import json as _json
                    import sqlite3
                    con = sqlite3.connect(f"file:{t3_db}?mode=ro", uri=True)
                    try:
                        for (pjson,) in con.execute(
                            "SELECT payload_json FROM orchestration_v2_projection_threads WHERE deleted_at IS NULL"
                        ):
                            try:
                                lin = (_json.loads(pjson or "{}").get("lineage") or {})
                            except Exception:
                                lin = {}
                            if isinstance(lin, dict) and lin.get("parentThreadId"):
                                subagent_count += 1
                            else:
                                sess_count += 1
                    finally:
                        con.close()
                except Exception:
                    sess_count = 0
        elif item["id"] == "antigravity":
            ag_db = root_p / "conversation_summaries.db"
            if ag_db.is_file():
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{ag_db}?mode=ro", uri=True)
                    try:
                        top_r = con.execute(
                            "SELECT COUNT(*) FROM conversation_summaries WHERE nesting_depth = 0 AND parent_conversation_id = ''"
                        ).fetchone()
                        sub_r = con.execute(
                            "SELECT COUNT(*) FROM conversation_summaries WHERE nesting_depth > 0 OR parent_conversation_id != ''"
                        ).fetchone()
                        sess_count = int(top_r[0]) if top_r else 0
                        subagent_count = int(sub_r[0]) if sub_r else 0
                    finally:
                        con.close()
                except Exception:
                    sess_count = _count_files(sess_p, item["session_glob"]) if sess_p.is_dir() else 0
            else:
                sess_count = _count_files(sess_p, item["session_glob"]) if sess_p.is_dir() else 0
        elif item["id"] == "opencode":
            oc_top_ids: set[str] = set()
            oc_sub_ids: set[str] = set()
            oc_db = root_p / "opencode.db"
            if oc_db.is_file():
                present = True
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{oc_db}?mode=ro", uri=True)
                    try:
                        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                        stbl = "session_v2" if "session_v2" in tables else ("session" if "session" in tables else None)
                        if stbl:
                            for sid, pid in con.execute(f'SELECT id, parent_id FROM "{stbl}"'):
                                if not sid:
                                    continue
                                if pid:
                                    oc_sub_ids.add(str(sid))
                                else:
                                    oc_top_ids.add(str(sid))
                    finally:
                        con.close()
                except Exception:
                    pass
            split_sess_dir = root_p / "storage" / "session"
            if split_sess_dir.is_dir():
                for fp in split_sess_dir.rglob("*.json"):
                    if fp.is_file() and fp.stem not in oc_top_ids and fp.stem not in oc_sub_ids:
                        oc_top_ids.add(fp.stem)
            elif not oc_top_ids and not oc_sub_ids and sess_p.is_dir():
                sess_count = _count_files(sess_p, item["session_glob"])
            sess_count = len(oc_top_ids) if (oc_top_ids or oc_sub_ids or split_sess_dir.is_dir() or oc_db.is_file()) else (
                _count_files(sess_p, item["session_glob"]) if sess_p.is_dir() else 0
            )
            subagent_count = len(oc_sub_ids)
        elif item["id"] == "goose":
            g_ids: set[str] = set()
            g_sub_ids: set[str] = set()
            if sess_p.is_dir():
                for fp in sess_p.rglob("*.jsonl"):
                    if fp.is_file():
                        g_ids.add(fp.stem)
            g_db = sess_p / "sessions.db"
            if g_db.is_file():
                present = True
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{g_db}?mode=ro", uri=True)
                    try:
                        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                        if "sessions" in tables:
                            cols = {r[1] for r in con.execute("PRAGMA table_info(sessions)")}
                            sql = "SELECT id, parent_session_id FROM sessions" if "parent_session_id" in cols else "SELECT id, NULL FROM sessions"
                            for sid, pid in con.execute(sql):
                                if not sid:
                                    continue
                                if pid:
                                    g_sub_ids.add(str(sid))
                                else:
                                    g_ids.add(str(sid))
                    finally:
                        con.close()
                except Exception:
                    pass
            sess_count = len(g_ids)
            subagent_count = len(g_sub_ids)
        elif item["id"] == "continue":
            sess_count = 0
            if sess_p.is_dir():
                sess_count = sum(
                    1
                    for fp in sess_p.rglob("*.json")
                    if fp.is_file() and fp.name not in {"sessions.json", "config.json"}
                )
        elif item["id"] == "cline":
            cl_ids: set[str] = set()
            cl_sub_ids: set[str] = set()
            for tdir in (sess_p, root_p / "data" / "tasks"):
                if tdir.is_dir():
                    present = True
                    for fp in tdir.rglob("api_conversation_history.json"):
                        if fp.is_file():
                            cl_ids.add(fp.parent.name)
            cl_db = root_p / "data" / "db" / "sessions.db"
            if cl_db.is_file():
                present = True
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{cl_db}?mode=ro", uri=True)
                    try:
                        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                        if "sessions" in tables:
                            for sid, is_sub in con.execute("SELECT session_id, is_subagent FROM sessions"):
                                if not sid:
                                    continue
                                if is_sub:
                                    cl_sub_ids.add(str(sid))
                                else:
                                    cl_ids.add(str(sid))
                    finally:
                        con.close()
                except Exception:
                    pass
            sess_count = len(cl_ids)
            subagent_count = len(cl_sub_ids)
        elif item["id"] == "zed":
            zed_ids: set[str] = set()
            zed_sub_ids: set[str] = set()
            if sess_p.is_dir():
                for fp in sess_p.rglob("*.json"):
                    if fp.is_file() and fp.name != "settings.json":
                        zed_ids.add(fp.stem)
                zdb = sess_p / "threads.db"
                if zdb.is_file():
                    present = True
                    try:
                        import sqlite3
                        con = sqlite3.connect(f"file:{zdb}?mode=ro", uri=True)
                        try:
                            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                            if "threads" in tables:
                                cols = {r[1] for r in con.execute("PRAGMA table_info(threads)")}
                                sql = "SELECT id, parent_id FROM threads" if "parent_id" in cols else "SELECT id, NULL FROM threads"
                                for tid, pid in con.execute(sql):
                                    if not tid:
                                        continue
                                    if pid:
                                        zed_sub_ids.add(str(tid))
                                    else:
                                        zed_ids.add(str(tid))
                        finally:
                            con.close()
                    except Exception:
                        pass
            sess_count = len(zed_ids)
            subagent_count = len(zed_sub_ids)
        elif item["id"] == "kiro":
            kiro_ids: set[str] = set()
            if sess_p.is_dir():
                for fp in list(sess_p.rglob("*.jsonl")) + list(sess_p.rglob("*.json")):
                    if fp.is_file() and fp.name not in {"mcp.json", "settings.json", "cli.json"}:
                        kiro_ids.add(fp.stem)
            for kdb in [item.get("extra_db"), root_p / "data.sqlite3"]:
                if isinstance(kdb, Path) and kdb.is_file():
                    present = True
                    try:
                        import sqlite3
                        con = sqlite3.connect(f"file:{kdb}?mode=ro", uri=True)
                        try:
                            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                            if "conversations_v2" in tables:
                                for (cid,) in con.execute("SELECT conversation_id FROM conversations_v2"):
                                    if cid:
                                        kiro_ids.add(str(cid))
                            if "conversations" in tables:
                                for (ckey,) in con.execute("SELECT key FROM conversations"):
                                    if ckey:
                                        kiro_ids.add(str(ckey))
                        finally:
                            con.close()
                    except Exception:
                        pass
            sess_count = len(kiro_ids)
        elif item["id"] == "cursor":
            sess_count = 0
            vscdb = sess_p / "state.vscdb"
            if vscdb.is_file():
                present = True
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{vscdb}?mode=ro", uri=True)
                    try:
                        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                        kvt = "cursorDiskKV" if "cursorDiskKV" in tables else ("ItemTable" if "ItemTable" in tables else None)
                        if kvt:
                            row = con.execute(f"SELECT COUNT(*) FROM {kvt} WHERE key LIKE 'composerData:%'").fetchone()
                            sess_count = int(row[0]) if row else 0
                    finally:
                        con.close()
                except Exception:
                    sess_count = 1
        elif item["id"] == "workbuddy":
            wb_ids: set[str] = set()
            if sess_p.is_dir():
                for fp in list(sess_p.glob("*.jsonl")) + list(sess_p.glob("*.json")):
                    if fp.is_file():
                        wb_ids.add(fp.stem)
            wb_proj = root_p / "projects"
            if wb_proj.is_dir():
                for fp in wb_proj.rglob("*.jsonl"):
                    if fp.is_file():
                        wb_ids.add(fp.stem)
            wb_db = root_p / "workbuddy.db"
            if wb_db.is_file():
                try:
                    import sqlite3
                    con = sqlite3.connect(f"file:{wb_db}?mode=ro", uri=True)
                    try:
                        for (sid,) in con.execute("SELECT id FROM sessions WHERE deleted_at IS NULL"):
                            if sid:
                                wb_ids.add(str(sid))
                    finally:
                        con.close()
                except Exception:
                    pass
            sess_count = len(wb_ids)
        elif item["id"] == "claude-desktop-3p-code":
            sess_count = 0
            if sess_p.is_dir():
                import json as _json
                for fp in sess_p.rglob("local_*.json"):
                    if not fp.is_file():
                        continue
                    try:
                        obj = _json.loads(fp.read_text(encoding="utf-8-sig", errors="replace"))
                    except Exception:
                        obj = {}
                    if isinstance(obj, dict) and obj.get("spawnedFrom"):
                        subagent_count += 1
                    else:
                        sess_count += 1
        elif item["id"] == "warp-oz":
            sess_count = _count_files(sess_p, item["session_glob"]) if sess_p.is_dir() else 0
            if plat == "darwin":
                warp_db = (
                    hroot
                    / "Library/Group Containers/2BBY89MBSN.dev.warp/Library/Application Support/dev.warp.Warp-Stable/warp.sqlite"
                )
                if warp_db.is_file():
                    present = True
                    try:
                        import sqlite3
                        con = sqlite3.connect(f"file:{warp_db}?mode=ro", uri=True)
                        try:
                            row = con.execute("SELECT COUNT(*) FROM agent_conversations").fetchone()
                            sess_count += int(row[0]) if row else 0
                        finally:
                            con.close()
                    except Exception:
                        pass
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
                "subagent_count": subagent_count,
                "skills_dir": str(skills_p),
                "skill_count": _count_skill_dirs(skills_p),
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
