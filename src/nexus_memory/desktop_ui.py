"""Futuristic Local Desktop App Server & UI for Nexus Memory (macOS .app + Windows .exe).

Design & UX Architecture:
- Unified Obsidian Neural Console with identical visual icon-card language for BOTH Source & Target Harnesses.
- Guided 4-Step End-to-End Flow right on the primary workspace (zero tab-hunting!):
    Step 1: Select Source <-> Target via symmetric visual icon cards (with 1-click Swap & Scope Filter)
    Step 2: Read-Only Dry-Run Preview WITH inline full conversation message reader (secret-redacted!)
    Step 3: Generate & SHA-256 Verify Local Bundle (auto-binds exact written path + opens full split-pane offline viewer)
    Step 4: Auto-Backup & Apply to Sandbox or Live Target Harness + 1-Click Exact Pristine-Hash Rollback
- Pure Python 3.11+ stdlib (`ThreadingHTTPServer` bound strictly to `127.0.0.1:0`, per-launch `X-Nexus-Token`, strict CSP).
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import __version__
from .bundle import SUPPORTED_TARGETS, preview, write_bundle
from .chatgpt import filter_conversations
from .claude_desktop_3p import default_claude_desktop_root
from .discovery import discover_harnesses
from .ecosystem import load_any_source
from .matrix import build_matrix_data
from .resources import scan_resources
from .security import redact_text
from .transaction import apply_bundle, rollback_transaction, verify_bundle, verify_transaction
from .viewer import _node_display_text, make_viewer_handler


def _pick_native_path(mode: str = "file") -> str | None:
    """Invoke a native OS file/folder picker cleanly on macOS or Windows."""
    if sys.platform == "darwin":
        script = (
            'POSIX path of (choose folder with prompt "选择目录")'
            if mode == "dir"
            else 'POSIX path of (choose file with prompt "选择 AI 会话文件或导出包")'
        )
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip().rstrip("/")
        return None
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        picked = filedialog.askdirectory() if mode == "dir" else filedialog.askopenfilename()
        root.destroy()
        return picked or None
    except Exception:
        return None


def _default_target_roots() -> dict[str, dict[str, str]]:
    """Compute platform-accurate live & sandbox destination directories for every target Harness."""
    home = Path.home()
    c3p = str(default_claude_desktop_root(home=home, third_party=True))
    sandbox_base = Path(tempfile.gettempdir()) / "nexus-memory-sandbox"
    mapping: dict[str, tuple[str, str]] = {
        "claude-code": (str(home / ".claude"), ""),
        "claude-desktop-3p-all": (c3p, str(home / ".claude")),
        "claude-desktop-3p-code": (c3p, str(home / ".claude")),
        "claude-desktop-3p-cowork": (c3p, ""),
        "claude-desktop-3p-chat": (c3p, ""),
        "codex": (str(home / ".codex"), ""),
        "antigravity": (str(home / ".gemini" / "antigravity"), ""),
        "cursor": (
            str(
                (home / "Library" / "Application Support" / "Cursor")
                if sys.platform == "darwin"
                else ((home / "AppData" / "Roaming" / "Cursor") if sys.platform == "win32" else (home / ".config" / "Cursor"))
            ),
            "",
        ),
        "workbuddy": (str(home / ".workbuddy"), ""),
        "t3code": (str(home / ".t3"), ""),
        "opencode": (str(home / ".local" / "share" / "opencode"), ""),
        "pi": (str(home / ".pi"), ""),
        "gemini-cli": (str(home / ".gemini"), ""),
        "kiro": (str(home / ".kiro"), ""),
        "amp": (str(home / ".local" / "share" / "amp"), ""),
        "trae": (str(home / ".trae"), ""),
        "warp-oz": (str(home / ".warp"), ""),
        "windsurf": (str(home / ".codeium" / "windsurf"), ""),
        "dsh": (str(home / ".dsh"), ""),
        "cline-roo": (str(home / ".cline"), ""),
        "goose": (str(home / ".local" / "share" / "goose"), ""),
        "continue": (str(home / ".continue"), ""),
        "zed": (str(home / ".local" / "share" / "zed"), ""),
        "aider": (str(Path.cwd()), ""),
        "portable": (str(home / "Desktop" / "nexus-portable-archive"), ""),
    }
    out: dict[str, dict[str, str]] = {}
    for k, (live_dir, cc_dir) in mapping.items():
        out[k] = {
            "live_target_root": live_dir,
            "live_claude_dir": cc_dir,
            "sandbox_target_root": str(sandbox_base / k),
            "sandbox_claude_dir": str(sandbox_base / f"{k}-claude") if cc_dir else "",
        }
    return out


def _serialize_conversations_preview(graphs: list[Any], *, max_turns: int = 80) -> list[dict[str, Any]]:
    """Build secret-redacted inline conversation previews so users see real message content in Step 2."""
    previews: list[dict[str, Any]] = []
    for g in graphs:
        title, _ = redact_text(str(g.title or g.source_id))
        turns: list[dict[str, Any]] = []
        for n in g.nodes[:max_turns]:
            raw_dict = {
                "text": n.text,
                "content": n.content,
            }
            disp = _node_display_text(raw_dict)
            red, _ = redact_text(disp)
            if len(red) > 2400:
                red = red[:2400] + "\n…（内容较长，完整内容请查看迁移包或离线浏览器）"
            turns.append(
                {
                    "node_id": n.node_id,
                    "role": str(n.role or "system"),
                    "event_type": str(n.event_type or "message"),
                    "timestamp": str(n.timestamp or ""),
                    "text": red,
                }
            )
        previews.append(
            {
                "source_id": g.source_id,
                "source_format": g.source_format,
                "title": title,
                "workspace": g.workspace,
                "project_name": g.metadata.get("project_name"),
                "section_name": g.metadata.get("section_name"),
                "total_nodes": len(g.nodes),
                "shown_nodes": len(turns),
                "branch_count": len(g.branch_paths()),
                "asset_count": len(g.assets),
                "turns": turns,
            }
        )
    return previews


DESKTOP_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Nexus Memory — AI Harness 跨端记忆迁移控制台</title>
<style>
  :root {
    --bg: #080B12;
    --bg-mesh-1: rgba(56, 189, 248, 0.10);
    --bg-mesh-2: rgba(99, 102, 241, 0.11);
    --sidebar: rgba(12, 17, 29, 0.88);
    --surface: rgba(17, 24, 39, 0.80);
    --surface-solid: #101726;
    --surface-2: rgba(26, 35, 54, 0.74);
    --border: rgba(148, 163, 184, 0.16);
    --border-hi: rgba(56, 189, 248, 0.48);
    --text-1: #F1F5F9;
    --text-2: #94A3B8;
    --text-3: #64748B;
    --accent: #38BDF8;
    --accent-2: #818CF8;
    --accent-grad: linear-gradient(135deg, #0EA5E9 0%, #6366F1 100%);
    --accent-soft: rgba(56, 189, 248, 0.13);
    --target-soft: rgba(99, 102, 241, 0.15);
    --safe: #10B981;
    --safe-soft: rgba(16, 185, 129, 0.13);
    --warn: #F59E0B;
    --warn-soft: rgba(245, 158, 11, 0.14);
    --danger: #F43F5E;
    --danger-soft: rgba(244, 63, 94, 0.14);
    --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Segoe UI Variable", "Microsoft YaHei UI", sans-serif;
    --font-mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    --shadow-card: 0 12px 32px rgba(0, 0, 0, 0.34);
  }
  [data-theme="light"] {
    --bg: #F3F6FB;
    --bg-mesh-1: rgba(14, 165, 233, 0.08);
    --bg-mesh-2: rgba(99, 102, 241, 0.08);
    --sidebar: rgba(238, 242, 249, 0.92);
    --surface: rgba(255, 255, 255, 0.92);
    --surface-solid: #FFFFFF;
    --surface-2: rgba(241, 245, 249, 0.90);
    --border: rgba(15, 23, 42, 0.10);
    --border-hi: rgba(14, 165, 233, 0.50);
    --text-1: #0F172A;
    --text-2: #475569;
    --text-3: #64748B;
    --accent: #0284C7;
    --accent-2: #4F46E5;
    --accent-grad: linear-gradient(135deg, #0284C7 0%, #4F46E5 100%);
    --accent-soft: rgba(2, 132, 199, 0.10);
    --target-soft: rgba(79, 70, 229, 0.10);
    --safe: #059669;
    --safe-soft: rgba(5, 150, 105, 0.10);
    --warn: #D97706;
    --warn-soft: rgba(217, 119, 6, 0.10);
    --danger: #E11D48;
    --danger-soft: rgba(225, 29, 72, 0.10);
    --shadow-card: 0 8px 24px rgba(15, 23, 42, 0.06);
  }
  * { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: rgba(148,163,184,0.28) transparent; }
  ::-webkit-scrollbar { width: 7px; height: 7px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.26); border-radius: 999px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(148,163,184,0.44); }
  html, body { height: 100%; margin: 0; }
  body {
    font-family: var(--font-sans);
    background:
      radial-gradient(640px 420px at 14% -6%, var(--bg-mesh-1), transparent 70%),
      radial-gradient(680px 460px at 92% 4%, var(--bg-mesh-2), transparent 72%),
      var(--bg);
    color: var(--text-1);
    display: grid;
    grid-template-columns: 218px 1fr 292px;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
  }
  @media (max-width: 1040px) {
    body { grid-template-columns: 196px 1fr; }
    .inspector { display: none; }
  }

  /* Left Sidebar */
  .sidebar {
    background: var(--sidebar);
    backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px);
    border-right: 1px solid var(--border);
    padding: 36px 12px 14px;
    display: flex; flex-direction: column; gap: 16px; user-select: none;
  }
  .brand { display: flex; align-items: center; gap: 10px; padding: 4px 6px; }
  .brand-orb {
    width: 32px; height: 32px; border-radius: 10px; flex-shrink: 0;
    background: var(--accent-grad); box-shadow: 0 0 18px rgba(56,189,248,0.34);
    display: grid; place-items: center;
  }
  .brand-title { font-size: 14px; font-weight: 700; letter-spacing: -0.015em; }
  .brand-sub { font-size: 10.5px; color: var(--text-3); margin-top: 1px; }

  .nav-group { display: flex; flex-direction: column; gap: 4px; }
  .nav-cap { font-size: 10.5px; font-weight: 600; color: var(--text-3); padding: 4px 10px; letter-spacing: 0.08em; text-transform: uppercase; }
  .nav-btn {
    display: flex; align-items: center; justify-content: space-between;
    padding: 9px 10px; border-radius: 10px; border: 1px solid transparent;
    background: transparent; color: var(--text-2); font-size: 12.5px; font-weight: 500;
    cursor: pointer; font-family: inherit; transition: all 140ms ease; text-align: left;
  }
  .nav-btn:hover { background: rgba(148,163,184,0.09); color: var(--text-1); }
  .nav-btn.active { background: var(--accent-soft); border-color: rgba(56,189,248,0.28); color: var(--text-1); font-weight: 600; }
  .nav-btn-l { display: flex; align-items: center; gap: 8px; }
  .pill-cnt {
    font-size: 10.5px; font-variant-numeric: tabular-nums; padding: 1px 7px;
    border-radius: 999px; background: rgba(148,163,184,0.14); color: var(--text-2); white-space: nowrap;
  }
  .nav-btn.active .pill-cnt { background: var(--accent); color: #04111D; font-weight: 700; }

  .side-foot { margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }
  .foot-card { padding: 10px; border-radius: 10px; background: var(--surface-2); border: 1px solid var(--border); font-size: 11px; color: var(--text-2); line-height: 1.45; }
  .foot-card b { color: var(--safe); }
  .theme-btn { height: 32px; border-radius: 9px; border: 1px solid var(--border); background: var(--surface); color: var(--text-2); font-size: 11.5px; cursor: pointer; font-family: inherit; }
  .theme-btn:hover { color: var(--text-1); border-color: var(--border-hi); }

  /* Main Column */
  .main { display: flex; flex-direction: column; overflow: hidden; }
  .topbar {
    height: 54px; padding: 0 22px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    -webkit-app-region: drag;
  }
  .topbar h1 { margin: 0; font-size: 15px; font-weight: 680; }
  .topbar-sub { font-size: 11.5px; color: var(--text-3); margin-top: 2px; }
  .live-badge {
    display: inline-flex; align-items: center; gap: 7px; padding: 4px 11px; border-radius: 999px;
    font-size: 11.5px; font-weight: 600; background: var(--safe-soft); color: var(--safe);
    border: 1px solid rgba(16,185,129,0.28); white-space: nowrap;
  }
  .pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--safe); box-shadow: 0 0 8px var(--safe); }

  .scroll { flex: 1; overflow-y: auto; padding: 16px 22px 28px; display: flex; flex-direction: column; gap: 14px; }

  /* 4-Step Top Guided Stepper */
  .stepper {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  }
  .st-btn {
    display: flex; align-items: center; gap: 8px; padding: 9px 11px; border-radius: 11px;
    border: 1px solid var(--border); background: var(--surface); color: var(--text-2);
    font-size: 12px; font-weight: 500; cursor: pointer; font-family: inherit; text-align: left;
    transition: all 150ms ease;
  }
  .st-btn:hover { border-color: var(--border-hi); color: var(--text-1); }
  .st-btn.active { border-color: var(--accent); background: var(--accent-soft); color: var(--text-1); font-weight: 650; }
  .st-btn.done { border-color: rgba(16,185,129,0.38); color: var(--text-1); }
  .st-num {
    width: 22px; height: 22px; border-radius: 999px; flex-shrink: 0;
    display: grid; place-items: center; font-size: 11px; font-weight: 700;
    background: rgba(148,163,184,0.16); color: var(--text-2);
  }
  .st-btn.active .st-num { background: var(--accent); color: #04111D; }
  .st-btn.done .st-num { background: var(--safe); color: #04111D; }
  .st-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* Contextual Guidance Banner */
  .guide-banner {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 11px 15px; border-radius: 12px;
    background: linear-gradient(90deg, rgba(14,165,233,0.12), rgba(99,102,241,0.10));
    border: 1px solid rgba(56,189,248,0.28); font-size: 12.5px; line-height: 1.45;
  }
  .guide-banner.ok {
    background: linear-gradient(90deg, rgba(16,185,129,0.15), rgba(14,165,233,0.08));
    border-color: rgba(16,185,129,0.36);
  }
  .guide-banner.err {
    background: var(--danger-soft); border-color: rgba(244,63,94,0.42);
  }

  .glass {
    background: var(--surface); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
    border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; box-shadow: var(--shadow-card);
  }
  .card-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 10px; flex-wrap: wrap; }
  .card-title { font-size: 13.5px; font-weight: 680; display: flex; align-items: center; gap: 8px; }
  .card-desc { font-size: 11.5px; color: var(--text-2); margin-top: 2px; }
  .step-tag { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: var(--accent-soft); color: var(--accent); letter-spacing: 0.04em; }

  /* Active Route Bridge Bar */
  .bridge-bar {
    display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center;
    padding: 12px 14px; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--border);
    margin-bottom: 14px;
  }
  .bridge-end { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .bridge-end-meta { min-width: 0; }
  .bridge-role { font-size: 10px; font-weight: 700; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; }
  .bridge-name { font-size: 13.5px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bridge-sub { font-size: 11px; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .swap-btn {
    height: 34px; padding: 0 12px; border-radius: 999px; border: 1px solid var(--border-hi);
    background: var(--accent-soft); color: var(--accent); font-size: 12px; font-weight: 650;
    cursor: pointer; font-family: inherit; white-space: nowrap; transition: all 140ms ease;
  }
  .swap-btn:hover { background: var(--accent); color: #04111D; }
  .swap-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* Symmetric Source & Target Visual Icon Card Grids */
  .picker-toolbar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .seg { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; background: var(--surface-solid); }
  .seg button {
    border: none; background: transparent; color: var(--text-2); padding: 5px 10px;
    font-size: 11.5px; font-weight: 550; cursor: pointer; font-family: inherit;
  }
  .seg button.active { background: var(--accent-soft); color: var(--accent); font-weight: 650; }
  .mini-search { width: 146px !important; height: 29px !important; font-size: 11.5px !important; padding: 0 9px !important; }

  .harness-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(154px, 1fr)); gap: 8px;
    max-height: 236px; overflow-y: auto; padding: 2px;
  }
  .h-card {
    display: flex; align-items: center; gap: 9px; padding: 9px 10px; border-radius: 11px;
    border: 1px solid var(--border); background: var(--surface-2); color: inherit;
    cursor: pointer; text-align: left; font-family: inherit; transition: all 140ms ease; min-width: 0;
  }
  .h-card:hover { border-color: var(--border-hi); transform: translateY(-1px); }
  .h-card.sel-src {
    border-color: var(--accent); background: var(--accent-soft);
    box-shadow: 0 0 0 2px rgba(56,189,248,0.18);
  }
  .h-card.sel-dst {
    border-color: var(--accent-2); background: var(--target-soft);
    box-shadow: 0 0 0 2px rgba(129,140,248,0.22);
  }
  .h-icon {
    width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
    display: grid; place-items: center; color: #fff;
  }
  .h-body { min-width: 0; flex: 1; }
  .h-top { display: flex; align-items: center; justify-content: space-between; gap: 4px; }
  .h-title { font-size: 12px; font-weight: 650; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .h-sub { font-size: 10.5px; color: var(--text-2); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .h-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; background: var(--safe); }
  .h-dot.ro { background: var(--warn); }
  .h-dot.off { background: rgba(148,163,184,0.35); }

  /* Forms */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label { font-size: 11.5px; font-weight: 600; color: var(--text-2); }
  .input-row { display: flex; gap: 7px; }
  input[type="text"], input[type="number"], select {
    width: 100%; height: 36px; border-radius: 9px; border: 1px solid var(--border);
    background: var(--surface-solid); color: var(--text-1); padding: 0 10px;
    font-size: 12.5px; font-family: inherit; outline: none;
  }
  input:focus, select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(56,189,248,0.14); }
  .btn-ghost {
    height: 36px; padding: 0 11px; border-radius: 9px; border: 1px solid var(--border);
    background: var(--surface-2); color: var(--text-1); font-size: 12px; font-weight: 500;
    cursor: pointer; white-space: nowrap; font-family: inherit;
  }
  .btn-ghost:hover { border-color: var(--border-hi); }

  /* Step 2 Inline Split Conversation Reader */
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 9px; margin-bottom: 12px; }
  .kpi { padding: 11px 12px; border-radius: 10px; background: var(--surface-2); border: 1px solid var(--border); }
  .kpi-v { font-size: 19px; font-weight: 720; font-variant-numeric: tabular-nums; }
  .kpi-l { font-size: 11px; color: var(--text-2); margin-top: 2px; }

  .preview-split {
    display: grid; grid-template-columns: 270px 1fr; gap: 12px; min-height: 320px;
  }
  .sess-col {
    border: 1px solid var(--border); border-radius: 11px; background: var(--surface-2);
    max-height: 380px; overflow-y: auto;
  }
  .sess-row {
    width: 100%; border: none; border-bottom: 1px solid var(--border); background: transparent;
    color: inherit; padding: 10px 12px; text-align: left; cursor: pointer; font-family: inherit;
    display: block; transition: background 120ms ease;
  }
  .sess-row:hover { background: rgba(56,189,248,0.08); }
  .sess-row.active { background: var(--accent-soft); border-left: 3px solid var(--accent); }
  .sess-row-t { font-size: 12.5px; font-weight: 650; margin-bottom: 3px; word-break: break-word; }
  .sess-row-s { font-size: 11px; color: var(--text-2); display: flex; gap: 6px; flex-wrap: wrap; }

  .reader-col {
    border: 1px solid var(--border); border-radius: 11px; background: var(--surface-solid);
    max-height: 380px; overflow-y: auto; padding: 12px 14px; display: flex; flex-direction: column; gap: 10px;
  }
  .msg-turn {
    border: 1px solid var(--border); border-left: 3px solid var(--border);
    border-radius: 9px; padding: 9px 12px; background: var(--surface-2);
  }
  .msg-turn.user { border-left-color: var(--accent); background: rgba(56,189,248,0.06); }
  .msg-turn.assistant { border-left-color: var(--safe); }
  .msg-turn.tool { border-left-color: #A78BFA; background: rgba(167,139,250,0.06); }
  .msg-head { display: flex; align-items: center; gap: 7px; margin-bottom: 5px; font-size: 11px; }
  .msg-body { white-space: pre-wrap; word-break: break-word; font-size: 12.5px; line-height: 1.52; color: var(--text-1); margin: 0; font-family: inherit; }
  .msg-turn.tool .msg-body { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-2); }

  /* Step 4 Mode Cards (Sandbox vs Live) */
  .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
  .mode-card {
    border: 1.5px solid var(--border); border-radius: 11px; padding: 12px 14px;
    background: var(--surface-2); cursor: pointer; text-align: left; color: inherit; font-family: inherit;
  }
  .mode-card.active { border-color: var(--accent); background: var(--accent-soft); }
  .mode-card.warn-active { border-color: var(--warn); background: var(--warn-soft); }
  .mode-card-t { font-size: 13px; font-weight: 680; margin-bottom: 3px; display: flex; justify-content: space-between; }
  .mode-card-d { font-size: 11.5px; color: var(--text-2); line-height: 1.45; }

  .resume-box {
    margin-top: 12px; padding: 12px 14px; border-radius: 10px;
    background: var(--safe-soft); border: 1px solid rgba(16,185,129,0.34); font-size: 12.5px;
  }
  .resume-cmd {
    margin-top: 6px; padding: 8px 10px; border-radius: 8px; background: rgba(0,0,0,0.28);
    font-family: var(--font-mono); font-size: 11.5px; color: var(--accent); word-break: break-all;
  }
  [data-theme="light"] .resume-cmd { background: #E2E8F0; color: #0F172A; }

  /* Tables & Badges */
  .list-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  .list-table th { text-align: left; font-size: 11px; font-weight: 600; color: var(--text-3); padding: 7px 8px; border-bottom: 1px solid var(--border); }
  .list-table td { padding: 8px; border-bottom: 1px solid var(--border); vertical-align: middle; }
  .list-table tr:last-child td { border-bottom: none; }
  .badge { display: inline-block; font-size: 10.5px; padding: 2px 7px; border-radius: 6px; font-weight: 600; white-space: nowrap; }
  .badge.ok { background: var(--safe-soft); color: var(--safe); }
  .badge.info { background: var(--accent-soft); color: var(--accent); }
  .badge.warn { background: var(--warn-soft); color: var(--warn); }
  .badge.err { background: var(--danger-soft); color: var(--danger); }

  /* Right Inspector Rail */
  .inspector {
    background: var(--sidebar); backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px);
    border-left: 1px solid var(--border); padding: 18px 15px 15px;
    display: flex; flex-direction: column; gap: 13px; overflow-y: auto;
  }
  .insp-title { font-size: 10.5px; font-weight: 700; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; }
  .progress-card {
    padding: 12px; border-radius: 12px; background: var(--surface); border: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 8px;
  }
  .p-item { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-2); }
  .p-item.active { color: var(--text-1); font-weight: 650; }
  .p-item.done { color: var(--safe); }
  .p-dot { width: 18px; height: 18px; border-radius: 50%; display: grid; place-items: center; font-size: 10px; font-weight: 700; background: rgba(148,163,184,0.16); flex-shrink: 0; }
  .p-item.active .p-dot { background: var(--accent); color: #04111D; }
  .p-item.done .p-dot { background: var(--safe); color: #04111D; }

  .tele-list { display: flex; flex-direction: column; gap: 6px; }
  .tele-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; border-radius: 9px; background: var(--surface); border: 1px solid var(--border); font-size: 11.5px; }

  .action-stack { margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }
  .next-hint { font-size: 11.5px; color: var(--accent); font-weight: 600; line-height: 1.4; }
  .btn-primary {
    height: 40px; border-radius: 10px; border: none; background: var(--accent-grad); color: #fff;
    font-size: 13px; font-weight: 650; cursor: pointer; font-family: inherit;
    box-shadow: 0 6px 20px rgba(14,165,233,0.28); transition: transform 140ms ease, filter 140ms ease;
  }
  .btn-primary:hover { filter: brightness(1.08); transform: translateY(-1px); }
  .btn-primary:disabled { opacity: 0.52; cursor: wait; transform: none; }
  .btn-sec {
    height: 35px; border-radius: 9px; border: 1px solid var(--border); background: var(--surface);
    color: var(--text-1); font-size: 12px; font-weight: 550; cursor: pointer; font-family: inherit;
  }
  .btn-sec:hover { border-color: var(--border-hi); }
  .btn-sec:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-danger {
    height: 35px; border-radius: 9px; border: 1px solid rgba(244,63,94,0.40);
    background: var(--danger-soft); color: var(--danger); font-size: 12px; font-weight: 600;
    cursor: pointer; font-family: inherit;
  }
  details.raw { font-size: 11.5px; color: var(--text-2); margin-top: 8px; }
  details.raw pre {
    background: rgba(0,0,0,0.28); border: 1px solid var(--border); border-radius: 9px;
    padding: 10px; max-height: 200px; overflow: auto; font-family: var(--font-mono); font-size: 11px; color: var(--text-1);
  }
  [data-theme="light"] details.raw pre { background: #F1F5F9; }
  .hidden { display: none !important; }
</style>
</head>
<body>
  <!-- Left Rail -->
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-orb" aria-hidden="true">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
          <circle cx="6" cy="7" r="2.5" stroke="#fff" stroke-width="2"/>
          <circle cx="18" cy="7" r="2.5" stroke="#fff" stroke-width="2"/>
          <circle cx="12" cy="17.5" r="2.5" stroke="#fff" stroke-width="2"/>
          <path d="M8.3 8.2L10.7 15.2M15.7 8.2L13.3 15.2M8.5 7H15.5" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <div class="brand-title">Nexus Memory</div>
        <div class="brand-sub">v__VERSION__ · Neural Bridge</div>
      </div>
    </div>

    <nav class="nav-group" aria-label="主导航">
      <div class="nav-cap">工作区</div>
      <button class="nav-btn active" id="nav-migrate" onclick="switchTab('migrate', this)">
        <span class="nav-btn-l"><span>⚡</span><span>一站式迁移</span></span>
        <span class="pill-cnt">4 步</span>
      </button>
      <button class="nav-btn" id="nav-discover" onclick="switchTab('discover', this)">
        <span class="nav-btn-l"><span>🛰</span><span>本机发现</span></span>
        <span class="pill-cnt" id="cnt-detected">…</span>
      </button>
      <button class="nav-btn" id="nav-matrix" onclick="switchTab('matrix', this)">
        <span class="nav-btn-l"><span>🧬</span><span>互转矩阵</span></span>
        <span class="pill-cnt" id="cnt-matrix">25</span>
      </button>
      <button class="nav-btn" id="nav-rollback" onclick="switchTab('rollback', this)">
        <span class="nav-btn-l"><span>🛡</span><span>历史回滚</span></span>
        <span class="pill-cnt">SHA-256</span>
      </button>
    </nav>

    <div class="side-foot">
      <div class="foot-card">
        <b>全流程闭环 · 零 AI 猜测</b><br/>
        选图标 → 看对话 → 生成包 → 备份正式迁入，随时一键撤销。
      </div>
      <button class="theme-btn" onclick="toggleTheme()">🌓 切换深空 / 浅色外观</button>
    </div>
  </aside>

  <!-- Main Workspace -->
  <main class="main">
    <header class="topbar">
      <div>
        <h1 id="page-title">一站式跨 Harness 迁移向导</h1>
        <div class="topbar-sub" id="page-sub">统一图标选来源与目标 · 直接预览对话内容 · 写前自动备份随时回滚</div>
      </div>
      <span class="live-badge" id="global-status"><span class="pulse"></span><span>第 1 步 · 选择来源与目标</span></span>
    </header>

    <div class="scroll" id="main-scroll">
      <!-- TAB 1: UNIFIED 4-STEP MIGRATION WORKFLOW -->
      <div id="tab-migrate">
        <!-- Always-visible 4-Step Guided Progress Bar -->
        <nav class="stepper" aria-label="迁移四步流程">
          <button class="st-btn active" id="st-1" onclick="jumpStep(1)"><span class="st-num">1</span><span class="st-label">选来源与目标</span></button>
          <button class="st-btn" id="st-2" onclick="jumpStep(2)"><span class="st-num">2</span><span class="st-label">预演与看内容</span></button>
          <button class="st-btn" id="st-3" onclick="jumpStep(3)"><span class="st-num">3</span><span class="st-label">生成并校验包</span></button>
          <button class="st-btn" id="st-4" onclick="jumpStep(4)"><span class="st-num">4</span><span class="st-label">备份正式迁入</span></button>
        </nav>

        <!-- Dynamic Next-Step Guidance Banner -->
        <div class="guide-banner" id="guide-banner" style="margin-top:12px;">
          <span id="guide-text"><b>引导提示：</b>先在下方对称图标区点选「来源」和「目标」AI Harness（已自动选中本机最活跃工具），然后点击右侧蓝色按钮开始只读预演。</span>
        </div>

        <!-- STEP 1: SYMMETRIC VISUAL SOURCE <-> TARGET PICKER -->
        <section class="glass" id="sec-step-1" style="margin-top:12px;">
          <!-- Active Bridge Summary + Swap -->
          <div class="bridge-bar">
            <div class="bridge-end">
              <div class="h-icon" id="bridge-src-icon"></div>
              <div class="bridge-end-meta">
                <div class="bridge-role">来源 FROM（全程只读）</div>
                <div class="bridge-name" id="bridge-src-name">OpenAI Codex</div>
                <div class="bridge-sub" id="bridge-src-sub">~/.codex</div>
              </div>
            </div>
            <button class="swap-btn" id="btn-swap" onclick="swapDirection()" title="互换来源与目标">⇄ 互换方向</button>
            <div class="bridge-end" style="justify-content:flex-end;text-align:right;">
              <div class="bridge-end-meta">
                <div class="bridge-role">目标 TO（原生格式）</div>
                <div class="bridge-name" id="bridge-dst-name">Claude Code CLI</div>
                <div class="bridge-sub" id="bridge-dst-sub">E5 实测 · 零 Invalid Params</div>
              </div>
              <div class="h-icon" id="bridge-dst-icon"></div>
            </div>
          </div>

          <!-- SOURCE ICON GRID -->
          <div class="card-hd" style="margin-bottom:8px;">
            <div>
              <div class="card-title"><span class="step-tag">FROM</span> 选择来源 Harness</div>
            </div>
            <div class="picker-toolbar">
              <div class="seg">
                <button class="active" id="src-filter-inst" onclick="setSrcFilter('installed', this)">本机已发现</button>
                <button id="src-filter-all" onclick="setSrcFilter('all', this)">全部 24 款</button>
              </div>
              <input type="text" class="mini-search" id="src-search" placeholder="搜索来源…" oninput="renderSourceGrid()" />
              <button class="btn-ghost" style="height:29px;font-size:11.5px;" onclick="pickExternalSource()">+ 导入文件/ZIP</button>
            </div>
          </div>
          <div class="harness-grid" id="source-grid"></div>

          <!-- TARGET ICON GRID (IDENTICAL VISUAL STYLE!) -->
          <div class="card-hd" style="margin-top:16px;margin-bottom:8px;">
            <div>
              <div class="card-title"><span class="step-tag" style="background:var(--target-soft);color:var(--accent-2);">TO</span> 选择目标 Harness（23 款全双向 + 3P 全通道 + 无损归档）</div>
            </div>
            <div class="picker-toolbar">
              <div class="seg">
                <button class="active" id="dst-filter-top" onclick="setDstFilter('popular', this)">主流常用</button>
                <button id="dst-filter-all" onclick="setDstFilter('all', this)">全部 25 目标</button>
              </div>
              <input type="text" class="mini-search" id="dst-search" placeholder="搜索目标…" oninput="renderTargetGrid()" />
            </div>
          </div>
          <div class="harness-grid" id="target-grid"></div>

          <!-- Scope & Options -->
          <div class="grid-2" style="margin-top:14px;padding-top:12px;border-top:1px solid var(--border);">
            <div class="field">
              <label>精准筛选分组 / Section（推荐，如 Destruction Era）</label>
              <input type="text" id="filter-section" placeholder="留空则不按分组筛选" />
            </div>
            <div class="field">
              <label>项目关键词 & 安全条数上限（避免一次全量迁移）</label>
              <div class="input-row">
                <input type="text" id="filter-project" placeholder="项目名称关键词（可选）" />
                <input type="number" id="filter-limit" value="5" min="1" max="500" style="width:88px;" />
              </div>
            </div>
          </div>
          <div class="grid-2" style="margin-top:10px;">
            <div class="field">
              <label>来源路径（已随图标自动填入，可手动微调）</label>
              <div class="input-row">
                <input type="text" id="src-path" />
                <button class="btn-ghost" onclick="pickPath('src-path', 'dir')">改目录</button>
              </div>
            </div>
            <div class="field">
              <label>目标工作区 CWD（用于映射项目路径）</label>
              <div class="input-row">
                <input type="text" id="cwd-path" value="__DEFAULT_CWD__" />
                <button class="btn-ghost" onclick="pickPath('cwd-path', 'dir')">选择</button>
              </div>
            </div>
          </div>
          <div style="margin-top:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;font-size:12px;color:var(--text-2);">
            <label style="display:inline-flex;align-items:center;gap:7px;cursor:pointer;">
              <input type="checkbox" id="opt-resources" checked /> 同步资源层（Copy 模式 Skills + 密钥脱敏 <code>${ENV_VAR}</code> MCP）
            </label>
            <span style="font-size:11.5px;">暂存包路径：<code id="out-preview-label">__DEFAULT_OUT__</code></span>
          </div>
        </section>

        <!-- STEP 2: DRY-RUN PREVIEW + INLINE CONVERSATION CONTENT READER -->
        <section class="glass" id="sec-step-2" style="margin-top:14px;">
          <div class="card-hd">
            <div>
              <div class="card-title"><span class="step-tag">STEP 2</span> 预演清单 & 直接核对会话内容</div>
              <div class="card-desc">点选左侧任意会话即可直接在右侧阅读真实消息内容（已自动脱敏密钥），确认无误再进入第 3 步</div>
            </div>
            <span class="badge info" id="preview-badge">等待执行第 1 步预演</span>
          </div>

          <div class="kpi-row">
            <div class="kpi"><div class="kpi-v" id="k-convs">—</div><div class="kpi-l">命中会话</div></div>
            <div class="kpi"><div class="kpi-v" id="k-nodes">—</div><div class="kpi-l">消息 / 工具节点</div></div>
            <div class="kpi"><div class="kpi-v" id="k-sess">—</div><div class="kpi-l">目标原生文件</div></div>
            <div class="kpi"><div class="kpi-v" id="k-sec" style="color:var(--safe);">0</div><div class="kpi-l">已自动脱敏凭据</div></div>
          </div>

          <div class="preview-split">
            <div class="sess-col" id="preview-sess-list">
              <div style="padding:26px 14px;text-align:center;color:var(--text-3);font-size:12px;">点击右侧「1. 只读预演并查看内容」，命中会话列表将显示在这里</div>
            </div>
            <div class="reader-col" id="preview-reader">
              <div style="padding:48px 18px;text-align:center;color:var(--text-3);font-size:12.5px;">选中左侧任意会话后，这里将直接展示完整的用户/助手对话与工具记录，无需猜测内容是否正确。</div>
            </div>
          </div>

          <details class="raw">
            <summary style="cursor:pointer;">查看底层保真报告 JSON（高级）</summary>
            <pre id="raw-json">{}</pre>
          </details>
        </section>

        <!-- STEP 3: BUNDLE RECEIPT -->
        <section class="glass" id="sec-step-3" style="margin-top:14px;">
          <div class="card-hd">
            <div>
              <div class="card-title"><span class="step-tag">STEP 3</span> 本地迁移包暂存与完整性校验</div>
              <div class="card-desc">生成含 <code>portable.json</code> 无损副本与目标原生文件的本地包（0600 私有权限），此时仍未修改目标软件目录</div>
            </div>
            <span class="badge info" id="bundle-badge">尚未生成</span>
          </div>
          <div class="input-row">
            <input type="text" id="out-path" value="__DEFAULT_OUT__" />
            <button class="btn-ghost" onclick="pickPath('out-path', 'dir')">改输出位置</button>
            <button class="btn-ghost" id="btn-inline-viewer" onclick="openViewer()" disabled>在离线浏览器中查看 ↗</button>
          </div>
          <div id="bundle-receipt" class="hidden" style="margin-top:10px;font-size:12px;color:var(--safe);"></div>
        </section>

        <!-- STEP 4: DIRECT BACKUP & APPLY + ONE-CLICK ROLLBACK (RIGHT IN THE MAIN FLOW!) -->
        <section class="glass" id="sec-step-4" style="margin-top:14px;">
          <div class="card-hd">
            <div>
              <div class="card-title"><span class="step-tag" style="background:var(--safe-soft);color:var(--safe);">STEP 4</span> 自动备份并正式迁入目标软件（支持随时一键回滚）</div>
              <div class="card-desc">完成第 3 步生成迁移包后，在这里直接把会话写入目标软件！建议先选「沙箱试运行」，确认满意再写入真实目录</div>
            </div>
            <span class="badge info" id="apply-badge">等待第 3 步迁移包</span>
          </div>

          <div class="mode-grid">
            <button class="mode-card active" id="mode-sandbox" onclick="setApplyMode('sandbox')">
              <div class="mode-card-t"><span>🧪 沙箱目录试迁</span><span class="badge ok">推荐先试</span></div>
              <div class="mode-card-d">写入独立临时目录，零风险测试安装与回滚，完全不触碰你真实安装的目标软件。</div>
            </button>
            <button class="mode-card" id="mode-live" onclick="setApplyMode('live')">
              <div class="mode-card-t"><span>🚀 正式写入目标软件</span><span class="badge warn">自动 0600 备份</span></div>
              <div class="mode-card-d">写入目标软件真实配置目录（写前自动打包原始 SHA-256 备份，默认拒绝覆盖同名会话）。</div>
            </button>
          </div>

          <div class="grid-2">
            <div class="field">
              <label>目标写入目录（随目标图标与模式自动切换）</label>
              <div class="input-row">
                <input type="text" id="apply-target-root" />
                <button class="btn-ghost" onclick="pickPath('apply-target-root', 'dir')">选择</button>
              </div>
            </div>
            <div class="field" id="apply-claude-dir-wrap">
              <label>配套 Claude Projects 目录（仅 Claude 3P Code 通道需要）</label>
              <div class="input-row">
                <input type="text" id="apply-claude-dir" placeholder="非 3P Code 目标可留空" />
                <button class="btn-ghost" onclick="pickPath('apply-claude-dir', 'dir')">选择</button>
              </div>
            </div>
          </div>

          <div class="grid-2" style="margin-top:10px;">
            <div class="field">
              <label>同名文件冲突保护策略</label>
              <select id="apply-collision">
                <option value="refuse">拒绝覆盖（最安全默认）</option>
                <option value="rename">自动重命名保留双方</option>
                <option value="skip">跳过已存在文件</option>
              </select>
            </div>
            <div class="field" style="justify-content:flex-end;">
              <label style="display:inline-flex;align-items:center;gap:7px;cursor:pointer;height:36px;">
                <input type="checkbox" id="apply-include-skills" /> 同时将脱敏 Skills 复制到目标目录
              </label>
            </div>
          </div>

          <div id="apply-success-box" class="resume-box hidden"></div>
        </section>
      </div>

      <!-- TAB 2: DISCOVER -->
      <div id="tab-discover" class="hidden">
        <section class="glass">
          <div class="card-hd">
            <div>
              <div class="card-title">本机已自动探测的 AI Harness（严格只读）</div>
              <div class="card-desc">点「设为来源」或「设为目标」会直接回到主向导并同步图标状态</div>
            </div>
            <button class="btn-ghost" onclick="loadDiscover()">↻ 重新扫描</button>
          </div>
          <table class="list-table">
            <thead><tr><th>Harness</th><th>会话根目录</th><th>会话数</th><th>Skills</th><th>快捷操作</th></tr></thead>
            <tbody id="discover-tbody"></tbody>
          </table>
        </section>
      </div>

      <!-- TAB 3: MATRIX -->
      <div id="tab-matrix" class="hidden">
        <section class="glass">
          <div class="card-hd">
            <div>
              <div class="card-title">25 个 AI Harness / Lane 互转能力矩阵</div>
              <div class="card-desc">全部 23 个本地 AI Harness 均已开放全双向 Read + Write（含 Codex / Antigravity / Cursor / Windsurf / Claude 3P / WorkBuddy / T3 Code）</div>
            </div>
            <input type="text" id="matrix-search" placeholder="搜索 Harness…" style="width:190px;height:32px;" oninput="renderMatrix()" />
          </div>
          <table class="list-table">
            <thead><tr><th>Harness / Lane</th><th>证据</th><th>读</th><th>写</th><th>多分支</th><th>说明</th></tr></thead>
            <tbody id="matrix-tbody"></tbody>
          </table>
        </section>
      </div>

      <!-- TAB 4: PAST ROLLBACKS -->
      <div id="tab-rollback" class="hidden">
        <section class="glass">
          <div class="card-hd">
            <div>
              <div class="card-title">历史迁移包校验 & 手动事务回滚工具</div>
              <div class="card-desc">用于独立校验任意历史迁移包，或指定历史 <code>.transactions/tx-...</code> 目录执行原哈希回滚</div>
            </div>
          </div>
          <div class="field">
            <label>迁移包目录或事务日志目录</label>
            <div class="input-row">
              <input type="text" id="rb-bundle" value="__DEFAULT_OUT__" />
              <button class="btn-ghost" onclick="pickPath('rb-bundle', 'dir')">选择目录</button>
            </div>
          </div>
          <div style="display:flex;gap:10px;margin-top:12px;">
            <button class="btn-sec" style="padding:0 14px;" onclick="doManualVerify()">✓ 校验完整性与脱敏</button>
            <button class="btn-danger" style="padding:0 14px;" onclick="doManualRollback()">↺ 按原始哈希一键回滚</button>
          </div>
          <details class="raw" open>
            <summary style="cursor:pointer;">回执详情</summary>
            <pre id="rb-json">{}</pre>
          </details>
        </section>
      </div>
    </div>
  </main>

  <!-- Right Live Progress & Unified Next-Step CTA Rail -->
  <aside class="inspector">
    <div class="insp-title">当前迁移进度</div>
    <div class="progress-card">
      <div class="p-item active" id="rp-1"><span class="p-dot">1</span><span>选定来源与目标图标</span></div>
      <div class="p-item" id="rp-2"><span class="p-dot">2</span><span>只读预演 & 核对对话</span></div>
      <div class="p-item" id="rp-3"><span class="p-dot">3</span><span>生成并校验本地迁移包</span></div>
      <div class="p-item" id="rp-4"><span class="p-dot">4</span><span>备份并正式迁入目标</span></div>
    </div>

    <div class="insp-title">实时安全护盾</div>
    <div class="tele-list">
      <div class="tele-row"><span>引擎模式</span><b style="color:var(--accent);">零 AI 确定性</b></div>
      <div class="tele-row"><span>协议防错</span><b style="color:var(--safe);">零 Invalid Params</b></div>
      <div class="tele-row"><span>密钥脱敏</span><b style="color:var(--safe);">${ENV_VAR} 自动替换</b></div>
      <div class="tele-row"><span>写前备份</span><b>0600 tar.gz + SHA-256</b></div>
    </div>

    <div class="action-stack">
      <div class="next-hint" id="cta-hint">下一步：先执行只读预演，查看真实会话内容</div>
      <button class="btn-primary" id="btn-main-cta" onclick="runNextStep()">1. 只读预演并查看内容 →</button>
      <button class="btn-sec" id="btn-rail-viewer" onclick="openViewer()" disabled>打开独立离线浏览器 ↗</button>
      <button class="btn-danger hidden" id="btn-rail-rollback" onclick="runCurrentRollback()">↺ 一键撤销本次迁入（回滚）</button>
    </div>
  </aside>

<script>
const TOKEN = "__NEXUS_TOKEN__";
const TARGET_ROOTS = __TARGET_ROOTS_JSON__;

// Unified Icon + Metadata Registry for ALL 24 Harnesses (100% consistent visual language!)
const HARNESS_CATALOG = [
  { id:"codex", discoverId:"codex", fmt:"codex", name:"OpenAI Codex", sub:"CLI / App · .jsonl.zst", ev:"E5", read:true, write:true, pop:true, color:"linear-gradient(135deg,#10B981,#059669)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M8 7l-4 5 4 5M16 7l4 5-4 5M13.5 5l-3 14" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  { id:"claude-code", discoverId:"claude-code", fmt:"claude-code", name:"Claude Code", sub:"CLI · API Key / 3P 网关", ev:"E5", read:true, write:true, pop:true, color:"linear-gradient(135deg,#F97316,#EA580C)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 3v18M4.5 7.5l15 9M19.5 7.5l-15 9" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/></svg>` },
  { id:"claude-desktop-3p-all", discoverId:"claude-desktop-3p-code", fmt:"claude-desktop-3p", name:"Claude 3P 全通道", sub:"Chat + Cowork + Code", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#FB923C,#C2410C)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="4.5" rx="2" stroke="#fff" stroke-width="1.9"/><rect x="3" y="10" width="18" height="4.5" rx="2" stroke="#fff" stroke-width="1.9"/><rect x="3" y="16" width="18" height="4.5" rx="2" stroke="#fff" stroke-width="1.9"/></svg>` },
  { id:"claude-desktop-3p-code", discoverId:"claude-desktop-3p-code", fmt:"claude-desktop-3p-code", name:"Claude 3P · Code", sub:"双键路径校验", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#F59E0B,#D97706)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="14" rx="3" stroke="#fff" stroke-width="2"/><path d="M8 10l2.5 2L8 14M12.5 14H16" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>` },
  { id:"claude-desktop-3p-cowork", discoverId:"claude-desktop-3p-chat-cowork", fmt:"claude-desktop-3p-cowork", name:"Claude 3P · Cowork", sub:"本地 Agent 模式", ev:"E4", read:true, write:true, pop:false, color:"linear-gradient(135deg,#F59E0B,#B45309)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="9" cy="9" r="3" stroke="#fff" stroke-width="2"/><circle cx="16" cy="15" r="3" stroke="#fff" stroke-width="2"/><path d="M11.5 11l2 2" stroke="#fff" stroke-width="2"/></svg>` },
  { id:"claude-desktop-3p-chat", discoverId:"claude-desktop-3p-chat-cowork", fmt:"claude-desktop-3p-chat", name:"Claude 3P · Chat", sub:"桌面对话通道", ev:"E4", read:true, write:true, pop:false, color:"linear-gradient(135deg,#EA580C,#9A3412)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 6a3 3 0 013-3h10a3 3 0 013 3v8a3 3 0 01-3 3H9l-5 4V6z" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>` },
  { id:"antigravity", discoverId:"antigravity", fmt:"antigravity", name:"Antigravity", sub:"全双向 · 含 Subagent", ev:"E5", read:true, write:true, pop:true, color:"linear-gradient(135deg,#38BDF8,#2563EB)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 3l8 17H4L12 3z" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="14" r="2" fill="#fff"/></svg>` },
  { id:"workbuddy", discoverId:"workbuddy", fmt:"workbuddy", name:"WorkBuddy", sub:"腾讯桌面 Agent", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#06B6D4,#0284C7)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 6l3.5 12L12 9l4.5 9L20 6" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  { id:"t3code", discoverId:"t3code", fmt:"t3code", name:"T3 Code", sub:"t3code v2 Thread", ev:"E3", read:true, write:true, pop:true, color:"linear-gradient(135deg,#8B5CF6,#6D28D9)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 6h10M9 6v12M15 9h5l-3 4 3 4h-5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  { id:"opencode", discoverId:"opencode", fmt:"opencode", name:"OpenCode", sub:"拆分 storage / JSON", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#3B82F6,#1D4ED8)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="4" y="4" width="16" height="16" rx="4" stroke="#fff" stroke-width="2"/><circle cx="12" cy="12" r="3" stroke="#fff" stroke-width="2"/></svg>` },
  { id:"pi", discoverId:"pi", fmt:"pi", name:"Pi Agent", sub:"原生多分支树 DAG", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#EC4899,#BE185D)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 7h14M9 7v11M15 7v9a2 2 0 002 2" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/></svg>` },
  { id:"gemini-cli", discoverId:"gemini-cli", fmt:"gemini-cli", name:"Gemini CLI", sub:"Google CLI 0.33+", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#60A5FA,#6366F1)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 2l2.6 7.4L22 12l-7.4 2.6L12 22l-2.6-7.4L2 12l7.4-2.6L12 2z" stroke="#fff" stroke-width="1.9" stroke-linejoin="round"/></svg>` },
  { id:"zed", discoverId:"zed", fmt:"zed", name:"Zed / Z Code", sub:"ACP Thread JSON", ev:"E3", read:true, write:true, pop:true, color:"linear-gradient(135deg,#0EA5E9,#0369A1)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 6h14L5 18h14" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  { id:"dsh", discoverId:"dsh", fmt:"dsh", name:"DeepSeek DSH", sub:"V4 Schema JSONL", ev:"E3", read:true, write:true, pop:true, color:"linear-gradient(135deg,#4F46E5,#312E81)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 5h6a7 7 0 010 14H5V5z" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>` },
  { id:"kiro", discoverId:"kiro", fmt:"kiro", name:"AWS Kiro", sub:"CLI v3 / IDE", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#A855F7,#7E22CE)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M6 4v16M18 4L9 12l9 8" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  { id:"amp", discoverId:"amp", fmt:"amp", name:"Sourcegraph Amp", sub:"Thread JSON", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#14B8A6,#0F766E)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M13 2L4 14h7l-1 8 10-12h-7l0-8z" stroke="#fff" stroke-width="1.9" stroke-linejoin="round"/></svg>` },
  { id:"trae", discoverId:"trae", fmt:"trae", name:"Trae / Agent", sub:"Trajectory JSON", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#22C55E,#15803D)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M12 6v13" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>` },
  { id:"warp-oz", discoverId:"warp-oz", fmt:"warp-oz", name:"Warp / Oz", sub:"Terminal Agent", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#06B6D4,#2563EB)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="3" stroke="#fff" stroke-width="2"/><path d="M7 10l3 2-3 2" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>` },
  { id:"cline-roo", discoverId:"cline", fmt:"cline", name:"Cline / Roo", sub:"VS Code Task JSON", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#6366F1,#4338CA)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M17 7a7 7 0 100 10" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>` },
  { id:"goose", discoverId:"goose", fmt:"goose", name:"Block Goose", sub:"Session JSONL", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#64748B,#334155)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="7" stroke="#fff" stroke-width="2"/><path d="M12 12h6" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>` },
  { id:"continue", discoverId:"continue", fmt:"continue", name:"Continue IDE", sub:"Session JSON", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#0EA5E9,#4F46E5)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M7 6l10 6-10 6V6z" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>` },
  { id:"aider", discoverId:"aider", fmt:"aider", name:"Aider", sub:"Markdown History", ev:"E3", read:true, write:true, pop:false, color:"linear-gradient(135deg,#10B981,#047857)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 19L12 5l7 14M8.5 13.5h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  { id:"chatgpt-export", discoverId:"", fmt:"chatgpt", name:"ChatGPT ZIP", sub:"离线导出包 · 含附件", ev:"E3", read:true, write:false, pop:true, color:"linear-gradient(135deg,#10A37F,#0D8A6B)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="7" stroke="#fff" stroke-width="2"/><path d="M12 5v14M5 12h14" stroke="#fff" stroke-width="1.6"/></svg>` },
  { id:"cursor", discoverId:"cursor", fmt:"cursor", name:"Cursor", sub:"全双向 state.vscdb", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#475569,#1E293B)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 4l14 7-6 2-2 6L5 4z" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>` },
  { id:"windsurf", discoverId:"windsurf", fmt:"windsurf", name:"Windsurf", sub:"全双向 Cascade JSON", ev:"E3", read:true, write:true, pop:true, color:"linear-gradient(135deg,#06B6D4,#0891B2)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 16c3-6 7-10 14-11-2 6-5 10-10 13" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/></svg>` },
  { id:"portable", discoverId:"", fmt:"portable", name:"无损通用归档", sub:"portable.json v2", ev:"E4", read:true, write:true, pop:true, color:"linear-gradient(135deg,#38BDF8,#818CF8)", svg:`<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 7l8-4 8 4v10l-8 4-8-4V7z" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>` }
];

const state = {
  step: 1,              // 1=select, 2=previewed, 3=bundled, 4=applied
  srcId: "codex",
  srcFmt: "codex",
  dstId: "claude-code",
  srcFilter: "installed",
  dstFilter: "popular",
  applyMode: "sandbox", // sandbox | live
  discoveredById: {},
  matrixCache: [],
  previewConvs: [],
  activePreviewIdx: 0,
  lastBundlePath: null,
  lastTxDir: null,
  lastApplySessions: []
};

async function api(path, body) {
  const opts = {
    method: body ? "POST" : "GET",
    headers: { "X-Nexus-Token": TOKEN, "Content-Type": "application/json" }
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
}

function getHarness(id) {
  return HARNESS_CATALOG.find(h => h.id === id) || HARNESS_CATALOG[0];
}

function toggleTheme() {
  const h = document.documentElement;
  h.dataset.theme = h.dataset.theme === "dark" ? "light" : "dark";
}

function switchTab(id, btn) {
  ["migrate","discover","matrix","rollback"].forEach(t => {
    document.getElementById("tab-" + t).classList.toggle("hidden", t !== id);
  });
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
}

function jumpStep(n) {
  const el = document.getElementById("sec-step-" + n);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setGuide(htmlMsg, kind) {
  const b = document.getElementById("guide-banner");
  b.className = "guide-banner" + (kind ? " " + kind : "");
  document.getElementById("guide-text").innerHTML = htmlMsg;
}

function updateProgressUI() {
  const s = state.step;
  [1,2,3,4].forEach(i => {
    const st = document.getElementById("st-" + i);
    const rp = document.getElementById("rp-" + i);
    st.className = "st-btn" + (i < s ? " done" : (i === s ? " active" : ""));
    rp.className = "p-item" + (i < s ? " done" : (i === s ? " active" : ""));
    st.querySelector(".st-num").textContent = i < s ? "✓" : String(i);
    rp.querySelector(".p-dot").textContent = i < s ? "✓" : String(i);
  });

  const cta = document.getElementById("btn-main-cta");
  const hint = document.getElementById("cta-hint");
  const gStat = document.getElementById("global-status");
  const hasBundle = Boolean(state.lastBundlePath);
  document.getElementById("btn-rail-viewer").disabled = !hasBundle;
  document.getElementById("btn-inline-viewer").disabled = !hasBundle;
  document.getElementById("btn-rail-rollback").classList.toggle("hidden", !state.lastTxDir);

  if (s === 1) {
    cta.textContent = "1. 只读预演并查看内容 →";
    hint.textContent = "下一步：点击预演，直接查看命中的真实对话内容（零写入）";
    gStat.innerHTML = `<span class="pulse"></span><span>第 1 步 · 选择来源与目标</span>`;
  } else if (s === 2) {
    cta.textContent = "2. 生成并校验本地迁移包 →";
    hint.textContent = "已看清对话内容？下一步生成 0600 迁移包并通过 SHA-256 校验";
    gStat.innerHTML = `<span class="pulse"></span><span>第 2 步 · 已预演对话内容</span>`;
  } else if (s === 3) {
    cta.textContent = state.applyMode === "sandbox" ? "3. 试迁入沙箱目录（零风险）→" : "3. 自动备份并正式迁入目标 →";
    hint.textContent = "迁移包已就绪！点击即可在第 4 步备份并正式迁入目标软件";
    gStat.innerHTML = `<span class="pulse"></span><span>第 3 步 · 迁移包已校验，等待迁入</span>`;
  } else {
    cta.textContent = "↻ 开启新一次迁移";
    hint.textContent = "✓ 本次迁移已正式完成！下方可随时一键回滚或离线浏览";
    gStat.innerHTML = `<span class="pulse"></span><span>✓ 第 4 步 · 已正式迁入目标</span>`;
  }
}

function updateBridgeBar() {
  const sh = getHarness(state.srcId);
  const dh = getHarness(state.dstId);
  const si = document.getElementById("bridge-src-icon");
  si.style.background = sh.color; si.innerHTML = sh.svg;
  document.getElementById("bridge-src-name").textContent = sh.name;
  document.getElementById("bridge-src-sub").textContent = document.getElementById("src-path").value || sh.sub;

  const di = document.getElementById("bridge-dst-icon");
  di.style.background = dh.color; di.innerHTML = dh.svg;
  document.getElementById("bridge-dst-name").textContent = dh.name;
  document.getElementById("bridge-dst-sub").textContent = `${dh.ev} · ${dh.sub}`;

  // Can swap only if source supports write and target supports read
  document.getElementById("btn-swap").disabled = !(sh.write && dh.read);
}

function syncApplyTargetPaths() {
  const cfg = TARGET_ROOTS[state.dstId] || TARGET_ROOTS["claude-code"];
  const isLive = state.applyMode === "live";
  document.getElementById("apply-target-root").value = isLive ? cfg.live_target_root : cfg.sandbox_target_root;
  const ccVal = isLive ? cfg.live_claude_dir : cfg.sandbox_claude_dir;
  document.getElementById("apply-claude-dir").value = ccVal;
  document.getElementById("apply-claude-dir-wrap").style.opacity = ccVal ? "1" : "0.55";
  updateProgressUI();
}

function setApplyMode(mode) {
  state.applyMode = mode;
  document.getElementById("mode-sandbox").className = "mode-card" + (mode === "sandbox" ? " active" : "");
  document.getElementById("mode-live").className = "mode-card" + (mode === "live" ? " warn-active" : "");
  syncApplyTargetPaths();
}

function selectSource(id) {
  state.srcId = id;
  const h = getHarness(id);
  state.srcFmt = h.fmt;
  const disc = state.discoveredById[h.discoverId];
  if (disc && disc.root_path) {
    document.getElementById("src-path").value = disc.root_path;
  } else if (TARGET_ROOTS[id]) {
    document.getElementById("src-path").value = TARGET_ROOTS[id].live_target_root;
  }
  if (id === "codex" && !document.getElementById("filter-section").value) {
    document.getElementById("filter-section").value = "Destruction Era";
  } else if (id !== "codex" && document.getElementById("filter-section").value === "Destruction Era") {
    document.getElementById("filter-section").value = "";
  }
  state.step = 1;
  renderSourceGrid();
  updateBridgeBar();
  updateProgressUI();
}

function selectTarget(id) {
  state.dstId = id;
  if (state.step > 1) state.step = 1;
  renderTargetGrid();
  updateBridgeBar();
  syncApplyTargetPaths();
}

function swapDirection() {
  const oldSrc = state.srcId;
  const oldDst = state.dstId;
  const sh = getHarness(oldSrc);
  const dh = getHarness(oldDst);
  if (!sh.write || !dh.read) return;
  selectSource(oldDst);
  selectTarget(oldSrc);
  setGuide(`<b>已互换迁移方向：</b>${dh.name} → ${sh.name}。点击右侧按钮即可重新只读预演。`, "");
}

function setSrcFilter(mode, btn) {
  state.srcFilter = mode;
  document.getElementById("src-filter-inst").classList.toggle("active", mode === "installed");
  document.getElementById("src-filter-all").classList.toggle("active", mode === "all");
  renderSourceGrid();
}

function setDstFilter(mode, btn) {
  state.dstFilter = mode;
  document.getElementById("dst-filter-top").classList.toggle("active", mode === "popular");
  document.getElementById("dst-filter-all").classList.toggle("active", mode === "all");
  renderTargetGrid();
}

function renderSourceGrid() {
  const q = (document.getElementById("src-search").value || "").toLowerCase();
  let list = HARNESS_CATALOG.filter(h => h.read);
  if (state.srcFilter === "installed" && !q) {
    const inst = list.filter(h => {
      const d = state.discoveredById[h.discoverId];
      return (d && d.detected) || h.id === state.srcId;
    });
    if (inst.length) list = inst;
  }
  if (q) list = list.filter(h => h.name.toLowerCase().includes(q) || h.id.toLowerCase().includes(q) || h.sub.toLowerCase().includes(q));
  list.sort((a, b) => {
    const da = state.discoveredById[a.discoverId];
    const db = state.discoveredById[b.discoverId];
    return ((db && db.detected ? (db.session_file_count || 1) : 0) - (da && da.detected ? (da.session_file_count || 1) : 0));
  });

  document.getElementById("source-grid").innerHTML = list.map(h => {
    const d = state.discoveredById[h.discoverId];
    const detected = d && d.detected;
    const sub = detected ? `${d.session_file_count} 会话 · ${d.skill_count} Skills` : h.sub;
    const dotCls = !h.write ? "ro" : (detected ? "" : "off");
    return `<button class="h-card ${h.id === state.srcId ? "sel-src" : ""}" onclick="selectSource('${h.id}')">
      <div class="h-icon" style="background:${h.color};">${h.svg}</div>
      <div class="h-body">
        <div class="h-top"><span class="h-title">${esc(h.name)}</span><span class="h-dot ${dotCls}" title="${!h.write ? "离线导出包" : (detected ? "本机已发现" : "可手动指定路径")}"></span></div>
        <div class="h-sub">${esc(sub)}</div>
      </div>
    </button>`;
  }).join("");
}

function renderTargetGrid() {
  const q = (document.getElementById("dst-search").value || "").toLowerCase();
  let list = HARNESS_CATALOG.filter(h => h.write);
  if (state.dstFilter === "popular" && !q) {
    list = list.filter(h => h.pop || h.id === state.dstId);
  }
  if (q) list = list.filter(h => h.name.toLowerCase().includes(q) || h.id.toLowerCase().includes(q) || h.sub.toLowerCase().includes(q));

  document.getElementById("target-grid").innerHTML = list.map(h => `
    <button class="h-card ${h.id === state.dstId ? "sel-dst" : ""}" onclick="selectTarget('${h.id}')">
      <div class="h-icon" style="background:${h.color};">${h.svg}</div>
      <div class="h-body">
        <div class="h-top"><span class="h-title">${esc(h.name)}</span><span class="badge ${h.ev === "E5" ? "ok" : "info"}" style="font-size:9.5px;padding:1px 5px;">${h.ev}</span></div>
        <div class="h-sub">${esc(h.sub)}</div>
      </div>
    </button>
  `).join("");
}

// Native picker bridge
window.__nexusPickerResolve = null;
window.__nexusNativePicked = function(val) {
  if (window.__nexusPickerResolve) {
    const fn = window.__nexusPickerResolve;
    window.__nexusPickerResolve = null;
    fn(val || null);
  }
};

async function pickPath(inputId, mode) {
  try {
    let picked = null;
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nexusNative) {
      picked = await new Promise(resolve => {
        window.__nexusPickerResolve = resolve;
        window.webkit.messageHandlers.nexusNative.postMessage({ action: "pick", mode });
      });
    } else {
      const r = await api("/api/pick-path", { mode });
      picked = r.path;
    }
    if (picked) {
      document.getElementById(inputId).value = picked;
      if (inputId === "src-path") updateBridgeBar();
      if (inputId === "out-path") document.getElementById("out-preview-label").textContent = picked;
    }
  } catch (e) {
    setGuide("<b>路径选择失败：</b>" + esc(e.message), "err");
  }
}

async function pickExternalSource() {
  await pickPath("src-path", "file");
  state.srcFmt = "auto";
  updateBridgeBar();
}

function collectPayload() {
  return {
    source: document.getElementById("src-path").value.trim(),
    source_format: state.srcFmt || "auto",
    target: state.dstId,
    section: document.getElementById("filter-section").value.trim() || null,
    project: document.getElementById("filter-project").value.trim() || null,
    limit: parseInt(document.getElementById("filter-limit").value, 10) || 5,
    out: document.getElementById("out-path").value.trim(),
    cwd: document.getElementById("cwd-path").value.trim(),
    include_resources: document.getElementById("opt-resources").checked
  };
}

function renderInlineConversation(idx) {
  state.activePreviewIdx = idx;
  document.querySelectorAll(".sess-row").forEach((el, i) => el.classList.toggle("active", i === idx));
  const conv = state.previewConvs[idx];
  const box = document.getElementById("preview-reader");
  if (!conv) {
    box.innerHTML = `<div style="padding:36px;text-align:center;color:var(--text-3);">无会话内容</div>`;
    return;
  }
  const roleLabel = { user:"用户", assistant:"AI 助手", tool_call:"工具调用", tool_result:"工具返回", system:"系统", developer:"系统指令" };
  const head = `<div style="padding-bottom:8px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
    <b style="font-size:13.5px;">${esc(conv.title)}</b>
    <div style="display:flex;gap:5px;">
      ${conv.section_name ? `<span class="badge info">分组：${esc(conv.section_name)}</span>` : ""}
      ${conv.project_name ? `<span class="badge ok">项目：${esc(conv.project_name)}</span>` : ""}
      <span class="badge">${conv.shown_nodes}/${conv.total_nodes} 条消息</span>
    </div>
  </div>`;
  const turns = (conv.turns || []).map(t => {
    const cls = t.role === "user" ? "user" : (t.role === "assistant" ? "assistant" : (t.role.includes("tool") ? "tool" : ""));
    const fold = (cls === "tool" || t.role === "developer" || t.role === "system") && (t.text || "").length > 260;
    const bodyEl = fold
      ? `<details style="font-size:11.5px;color:var(--text-2);"><summary style="cursor:pointer;">展开${cls === "tool" ? "工具详情" : "系统上下文"}（${t.text.length} 字符）</summary><pre class="msg-body" style="margin-top:6px;">${esc(t.text)}</pre></details>`
      : `<pre class="msg-body">${esc(t.text)}</pre>`;
    return `<div class="msg-turn ${cls}">
      <div class="msg-head">
        <span class="badge ${cls === "user" ? "info" : (cls === "assistant" ? "ok" : "warn")}">${esc(roleLabel[t.role] || t.role)}</span>
        <span style="color:var(--text-3);">${esc(t.event_type)}</span>
        ${t.timestamp ? `<span style="margin-left:auto;color:var(--text-3);font-family:var(--font-mono);">${esc(t.timestamp.slice(0,19))}</span>` : ""}
      </div>
      ${bodyEl}
    </div>`;
  }).join("");
  box.innerHTML = head + (turns || `<div style="padding:24px;color:var(--text-3);">该会话仅包含元数据，无文本消息节点。</div>`);
}

function renderPreviewData(manifest, convPreviews) {
  document.getElementById("k-convs").textContent = manifest.conversation_count ?? 0;
  document.getElementById("k-nodes").textContent = manifest.node_count ?? 0;
  document.getElementById("k-sess").textContent = manifest.native_session_count ?? 0;
  const secTotal = Object.values(manifest.secret_marker_counts || {}).reduce((a, b) => a + b, 0);
  document.getElementById("k-sec").textContent = secTotal;
  document.getElementById("raw-json").textContent = JSON.stringify(manifest, null, 2);

  state.previewConvs = convPreviews || [];
  const listEl = document.getElementById("preview-sess-list");
  if (!state.previewConvs.length) {
    listEl.innerHTML = `<div style="padding:24px;text-align:center;color:var(--warn);font-size:12px;">当前筛选条件下未命中会话，请清空分组/项目关键词重试。</div>`;
    document.getElementById("preview-reader").innerHTML = `<div style="padding:36px;text-align:center;color:var(--text-3);">无命中会话</div>`;
    return;
  }
  listEl.innerHTML = state.previewConvs.map((c, idx) => `
    <button class="sess-row ${idx === 0 ? "active" : ""}" onclick="renderInlineConversation(${idx})">
      <div class="sess-row-t">${esc(c.title)}</div>
      <div class="sess-row-s">
        <span>${esc(c.section_name || c.project_name || "未分组")}</span>
        <span>·</span>
        <span>${c.total_nodes} 节点</span>
        <span>·</span>
        <span>${c.branch_count} 分支</span>
      </div>
    </button>
  `).join("");
  renderInlineConversation(0);
}

async function runNextStep() {
  if (state.step === 1) return doStep2Preview();
  if (state.step === 2) return doStep3Stage();
  if (state.step === 3) return doStep4Apply();
  // Restart
  state.step = 1;
  state.lastTxDir = null;
  document.getElementById("apply-success-box").classList.add("hidden");
  updateProgressUI();
  jumpStep(1);
  setGuide("<b>已就绪：</b>请重新选择来源与目标，开启下一次迁移。", "");
}

async function doStep2Preview() {
  const btn = document.getElementById("btn-main-cta");
  btn.disabled = true;
  try {
    const res = await api("/api/preview", collectPayload());
    renderPreviewData(res.manifest, res.conversations_preview);
    document.getElementById("preview-badge").textContent = `✓ 已命中 ${res.manifest.conversation_count} 条会话`;
    document.getElementById("preview-badge").className = "badge ok";
    if (res.manifest.conversation_count > 0) {
      state.step = 2;
      setGuide(`<b>第 2 步完成（零写入）：</b>已在下方直接展开真实对话内容。核对无误后，点击右侧 <b>「2. 生成并校验本地迁移包 →」</b>。`, "ok");
    } else {
      setGuide(`<b>未命中会话：</b>请检查「分组 / 项目」筛选条件（留空可查看该来源全部会话）。`, "err");
    }
    updateProgressUI();
    jumpStep(2);
  } catch (e) {
    setGuide("<b>预演失败：</b>" + esc(e.message), "err");
  } finally { btn.disabled = false; }
}

async function doStep3Stage() {
  const btn = document.getElementById("btn-main-cta");
  btn.disabled = true;
  try {
    const res = await api("/api/convert", collectPayload());
    state.lastBundlePath = res.written_to;
    state.lastApplySessions = res.manifest.target_sessions || [];
    document.getElementById("out-path").value = res.written_to;
    document.getElementById("out-preview-label").textContent = res.written_to;
    document.getElementById("rb-bundle").value = res.written_to;
    document.getElementById("bundle-badge").textContent = res.verify.ok ? "✓ SHA-256 与脱敏校验通过" : "✗ 校验异常";
    document.getElementById("bundle-badge").className = "badge " + (res.verify.ok ? "ok" : "err");
    const rec = document.getElementById("bundle-receipt");
    rec.innerHTML = `✓ 已生成本地迁移包：<code>${esc(res.written_to)}</code>（共 ${res.verify.checks.bundle_file_count} 个文件，零未脱敏密钥）。<br/>👉 <b>下一步：</b>可点「在离线浏览器中查看」核对完整富文本，或直接点击右侧蓝色按钮执行 <b>第 4 步：备份并正式迁入目标软件</b>！`;
    rec.classList.remove("hidden");
    state.step = 3;
    document.getElementById("apply-badge").textContent = "已就绪 · 等待迁入";
    document.getElementById("apply-badge").className = "badge info";
    setGuide(`<b>第 3 步完成：</b>迁移包已安全落盘并校验通过！现在请在第 4 步选择「沙箱试迁」或「正式写入」，点击右侧蓝色按钮完成最终迁移。`, "ok");
    updateProgressUI();
    jumpStep(4);
  } catch (e) {
    setGuide("<b>生成迁移包失败：</b>" + esc(e.message), "err");
  } finally { btn.disabled = false; }
}

async function doStep4Apply() {
  if (!state.lastBundlePath) {
    setGuide("<b>请先完成第 3 步：</b>先生成并校验本地迁移包，再正式迁入目标软件。", "err");
    return;
  }
  const target_root = document.getElementById("apply-target-root").value.trim();
  const claude_dir = document.getElementById("apply-claude-dir").value.trim() || null;
  if (!target_root) {
    setGuide("<b>请填写目标写入目录</b>后再执行迁入。", "err");
    return;
  }
  const btn = document.getElementById("btn-main-cta");
  btn.disabled = true;
  try {
    const res = await api("/api/apply", {
      bundle: state.lastBundlePath,
      target_root,
      claude_dir,
      on_collision: document.getElementById("apply-collision").value,
      include_skills: document.getElementById("apply-include-skills").checked,
      apply: true
    });
    state.lastTxDir = res.journal_dir;
    document.getElementById("rb-bundle").value = res.journal_dir;
    document.getElementById("apply-badge").textContent = res.post_write_verification.ok ? "✓ 已正式迁入并读回校验通过" : "⚠ 读回校验异常";
    document.getElementById("apply-badge").className = "badge " + (res.post_write_verification.ok ? "ok" : "err");

    const firstSid = (state.lastApplySessions[0] || {}).session_id || "<session-id>";
    let resumeTip = `目标目录：${target_root}`;
    if (state.dstId === "claude-code") resumeTip = `在终端续聊：CLAUDE_CONFIG_DIR="${target_root}" claude --resume ${firstSid}`;
    else if (state.dstId === "codex") resumeTip = `在终端续聊：CODEX_HOME="${target_root}" codex exec resume ${firstSid}`;
    else if (state.dstId === "gemini-cli") resumeTip = `在终端查看：gemini --list-sessions`;
    else if (state.dstId.startsWith("claude-desktop-3p")) resumeTip = `重启或刷新 Claude Desktop 3P 客户端即可在对应通道看到已迁入会话`;

    const sbox = document.getElementById("apply-success-box");
    sbox.innerHTML = `
      <b>✓ 迁移已正式生效！（写入 ${res.written_files.length} 个文件，已创建 0600 原始备份）</b><br/>
      <span style="color:var(--text-2);font-size:12px;">事务备份日志：<code>${esc(res.journal_dir)}</code></span>
      <div class="resume-cmd">${esc(resumeTip)}</div>
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
        <button class="btn-danger" style="padding:0 12px;" onclick="runCurrentRollback()">↺ 不满意？一键撤销并按原哈希恢复</button>
        <button class="btn-sec" style="padding:0 12px;" onclick="openViewer()">打开离线浏览器核对 ↗</button>
      </div>
    `;
    sbox.classList.remove("hidden");
    state.step = 4;
    setGuide(`<b>🎉 全部 4 步已完成！</b>会话已正式迁入 <b>${esc(target_root)}</b> 并通过写后读回校验。如需撤销，随时点「一键回滚」。`, "ok");
    updateProgressUI();
  } catch (e) {
    setGuide("<b>正式迁入被安全拦截或失败：</b>" + esc(e.message), "err");
  } finally { btn.disabled = false; }
}

async function runCurrentRollback() {
  if (!state.lastTxDir) return;
  try {
    const res = await api("/api/rollback", { tx_dir: state.lastTxDir });
    if (res.ok) {
      state.lastTxDir = null;
      state.step = 3;
      document.getElementById("apply-badge").textContent = "↺ 已精确回滚至迁移前原状";
      document.getElementById("apply-badge").className = "badge warn";
      document.getElementById("apply-success-box").classList.add("hidden");
      setGuide(`<b>↺ 一键回滚成功！</b>目标目录已逐字节还原为迁移前的原始 SHA-256（<code>${esc(res.primary_restore.restored_tree_sha256.slice(0,16))}…</code>）。`, "ok");
      updateProgressUI();
    }
  } catch (e) {
    setGuide("<b>回滚失败：</b>" + esc(e.message), "err");
  }
}

async function openViewer() {
  try {
    const bundle = state.lastBundlePath || document.getElementById("out-path").value.trim();
    const res = await api("/api/open-viewer", { bundle });
    setGuide(`<b>离线安全浏览器已打开：</b><a href="${esc(res.url)}" target="_blank" style="color:var(--accent);">${esc(res.url)}</a>（包含完整会话消息流与保真报告）。看完后回到此处点第 4 步即可正式迁入！`, "ok");
  } catch (e) {
    setGuide("<b>无法打开离线浏览器：</b>" + esc(e.message), "err");
  }
}

async function doManualVerify() {
  try {
    const res = await api("/api/verify", { target: document.getElementById("rb-bundle").value.trim() });
    document.getElementById("rb-json").textContent = JSON.stringify(res, null, 2);
  } catch (e) { document.getElementById("rb-json").textContent = JSON.stringify({ error: e.message }, null, 2); }
}

async function doManualRollback() {
  try {
    const res = await api("/api/rollback", { tx_dir: document.getElementById("rb-bundle").value.trim() });
    document.getElementById("rb-json").textContent = JSON.stringify(res, null, 2);
  } catch (e) { document.getElementById("rb-json").textContent = JSON.stringify({ error: e.message }, null, 2); }
}

async function loadDiscover() {
  try {
    const data = await api("/api/discover");
    const list = data.harnesses || [];
    state.discoveredById = {};
    list.forEach(h => { state.discoveredById[h.id] = h; });
    const found = list.filter(h => h.detected);
    document.getElementById("cnt-detected").textContent = found.length;

    // Auto-select the busiest detected readable Harness on first boot
    const best = [...found]
      .filter(h => h.id !== "claude-desktop-standard")
      .sort((a, b) => (b.session_file_count || 0) - (a.session_file_count || 0))[0];
    if (best) {
      const cat = HARNESS_CATALOG.find(c => c.discoverId === best.id);
      if (cat) selectSource(cat.id);
    } else {
      renderSourceGrid();
    }
    renderTargetGrid();
    updateBridgeBar();
    syncApplyTargetPaths();

    document.getElementById("discover-tbody").innerHTML = list.map(h => {
      const cat = HARNESS_CATALOG.find(c => c.discoverId === h.id);
      return `<tr>
        <td><b>${esc(h.display_name)}</b><br/><span style="color:var(--text-3);font-size:11px;">${esc(h.id)}</span></td>
        <td style="font-family:var(--font-mono);font-size:11px;color:var(--text-2);">${esc(h.root_path)}</td>
        <td style="font-variant-numeric:tabular-nums;">${h.session_file_count}</td>
        <td style="font-variant-numeric:tabular-nums;">${h.skill_count}</td>
        <td style="display:flex;gap:6px;">${cat && h.detected ? `<button class="btn-ghost" style="height:26px;font-size:11px;" onclick="pickFromDiscover('${cat.id}','src')">设为来源</button>${cat.write ? `<button class="btn-ghost" style="height:26px;font-size:11px;" onclick="pickFromDiscover('${cat.id}','dst')">设为目标</button>` : ""}` : `<span style="color:var(--text-3);font-size:11px;">${h.detected ? "仅探测" : "未安装"}</span>`}</td>
      </tr>`;
    }).join("");
  } catch (e) { console.error(e); }
}

function pickFromDiscover(id, side) {
  if (side === "src") selectSource(id); else selectTarget(id);
  switchTab("migrate", document.getElementById("nav-migrate"));
}

async function loadMatrix() {
  try {
    const data = await api("/api/matrix");
    state.matrixCache = data.harnesses || [];
    document.getElementById("cnt-matrix").textContent = state.matrixCache.length;
    renderMatrix();
  } catch (e) { console.error(e); }
}

function renderMatrix() {
  const q = (document.getElementById("matrix-search").value || "").toLowerCase();
  const rows = state.matrixCache.filter(h => !q || h.display_name.toLowerCase().includes(q) || h.id.toLowerCase().includes(q));
  document.getElementById("matrix-tbody").innerHTML = rows.map(h => `
    <tr>
      <td><b>${esc(h.display_name)}</b><br/><span style="color:var(--text-3);font-size:11px;">${esc(h.id)}</span></td>
      <td><span class="badge ${h.evidence_level === "E5" ? "ok" : (h.evidence_level === "E4" ? "info" : "warn")}">${esc(h.evidence_level)}</span></td>
      <td>${h.read_supported ? "✓" : "—"}</td>
      <td>${h.write_supported ? "✓" : (h.id === "claude-cloud-hosted" ? "云端托管" : "导出包")}</td>
      <td>${h.native_branch_dag ? "<b style='color:var(--accent)'>原生 DAG</b>" : "拆分+侧车"}</td>
      <td style="font-size:11.5px;color:var(--text-2);max-width:260px;">${esc(h.notes || "")}</td>
    </tr>
  `).join("");
}

loadDiscover();
loadMatrix();
updateProgressUI();
</script>
</body>
</html>
"""


def make_desktop_handler(token: str) -> type[BaseHTTPRequestHandler]:
    default_out = str((Path.home() / "Desktop" / "nexus-memory-bundle").expanduser())
    default_cwd = str(Path.cwd())
    target_roots_json = json.dumps(_default_target_roots(), ensure_ascii=False)
    rendered_html = (
        DESKTOP_HTML.replace("__VERSION__", __version__)
        .replace("__NEXUS_TOKEN__", token)
        .replace("__DEFAULT_OUT__", default_out)
        .replace("__DEFAULT_CWD__", default_cwd)
        .replace("__TARGET_ROOTS_JSON__", target_roots_json)
        .encode("utf-8")
    )
    viewer_servers: list[HTTPServer] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'self'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, code: int, payload: Any) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _check_token(self) -> bool:
            return self.headers.get("X-Nexus-Token") == token

        def _read_json(self) -> dict[str, Any]:
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n) if n else b"{}"
            obj = json.loads(raw.decode("utf-8"))
            return obj if isinstance(obj, dict) else {}

        def do_GET(self) -> None:
            path = urllib.parse.urlsplit(self.path).path
            if path in {"/", "/index.html"}:
                self._send(HTTPStatus.OK, rendered_html, "text/html; charset=utf-8")
                return
            if path == "/api/health":
                self._send_json(HTTPStatus.OK, {"ok": True, "version": __version__})
                return
            if not self._check_token():
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "invalid session token"})
                return
            try:
                if path == "/api/discover":
                    self._send_json(HTTPStatus.OK, discover_harnesses())
                    return
                if path == "/api/matrix":
                    self._send_json(HTTPStatus.OK, build_matrix_data())
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

        def do_POST(self) -> None:
            path = urllib.parse.urlsplit(self.path).path
            if not self._check_token():
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "invalid session token"})
                return
            try:
                body = self._read_json()
                if path == "/api/pick-path":
                    picked = _pick_native_path(str(body.get("mode") or "file"))
                    self._send_json(HTTPStatus.OK, {"path": picked})
                    return

                if path in {"/api/preview", "/api/convert"}:
                    src = str(body.get("source") or "").strip()
                    if not src:
                        raise ValueError("请先在左侧选择来源 Harness 图标或导入本地文件")
                    fmt = str(body.get("source_format") or "auto")
                    target = str(body.get("target") or "claude-code")
                    if target not in SUPPORTED_TARGETS:
                        raise ValueError(f"不支持的目标格式: {target}")
                    section = body.get("section") or None
                    project = body.get("project") or None
                    limit = int(body["limit"]) if body.get("limit") else None
                    cwd = body.get("cwd") or default_cwd
                    graphs, assets = load_any_source(
                        src, source_format=fmt, section_filter=section, project_filter=project, limit=limit
                    )
                    graphs = filter_conversations(graphs, project=project, section=section)
                    if limit:
                        graphs = graphs[:limit]
                    res_bundle = scan_resources(project_dir=cwd) if body.get("include_resources") else None
                    if path == "/api/preview":
                        manifest = preview(graphs, cwd=cwd, target=target, resources=res_bundle)
                        self._send_json(
                            HTTPStatus.OK,
                            {
                                "manifest": manifest,
                                "conversations_preview": _serialize_conversations_preview(graphs),
                            },
                        )
                        return
                    out = str(body.get("out") or default_out).strip()
                    out_p = Path(out).expanduser()
                    if out_p.exists():
                        stamp = secrets.token_hex(3)
                        out_p = out_p.with_name(f"{out_p.name}-{stamp}")
                    manifest = write_bundle(
                        graphs, out=out_p, cwd=cwd, target=target, asset_bytes=assets, resources=res_bundle
                    )
                    vcheck = verify_bundle(out_p)
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "written_to": str(out_p.resolve()),
                            "manifest": manifest,
                            "verify": vcheck,
                            "conversations_preview": _serialize_conversations_preview(graphs),
                        },
                    )
                    return

                if path == "/api/verify":
                    tp = Path(str(body.get("target") or "")).expanduser()
                    res = (
                        verify_transaction(tp)
                        if ((tp / "transaction.json").is_file() or tp.name == "transaction.json")
                        else verify_bundle(tp)
                    )
                    self._send_json(HTTPStatus.OK, res)
                    return

                if path == "/api/apply":
                    res = apply_bundle(
                        str(body.get("bundle") or ""),
                        target_root=str(body.get("target_root") or ""),
                        claude_dir=body.get("claude_dir") or None,
                        on_collision=str(body.get("on_collision") or "refuse"),
                        include_skills=bool(body.get("include_skills", False)),
                        apply=bool(body.get("apply", False)),
                    )
                    self._send_json(HTTPStatus.OK, res)
                    return

                if path == "/api/rollback":
                    res = rollback_transaction(str(body.get("tx_dir") or ""))
                    self._send_json(HTTPStatus.OK, res)
                    return

                if path == "/api/open-viewer":
                    bdir = Path(str(body.get("bundle") or "")).expanduser()
                    if not (bdir / "manifest.json").is_file():
                        raise ValueError("该目录还不是有效迁移包（缺少 manifest.json），请先执行第 3 步生成迁移包")
                    vsrv = HTTPServer(("127.0.0.1", 0), make_viewer_handler(bdir))
                    vport = vsrv.server_address[1]
                    viewer_servers.append(vsrv)
                    threading.Thread(target=vsrv.serve_forever, daemon=True).start()
                    url = f"http://127.0.0.1:{vport}/"
                    webbrowser.open(url)
                    self._send_json(HTTPStatus.OK, {"url": url})
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    return Handler


def start_desktop_server(port: int = 0) -> tuple[ThreadingHTTPServer, str, str]:
    """Start the hardened 127.0.0.1 desktop API+UI server and return `(server, url, token)`."""
    token = secrets.token_urlsafe(24)
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_desktop_handler(token))
    actual_port = srv.server_address[1]
    return srv, f"http://127.0.0.1:{actual_port}/", token


def _open_standalone_window(url: str) -> None:
    """Open URL in chromeless app mode (Edge/Chrome/Chromium `--app=`) on Windows/Linux, else system browser."""
    if sys.platform == "win32":
        candidates = [
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
        ]
        for exe in candidates:
            if exe.is_file():
                subprocess.Popen([str(exe), f"--app={url}", "--window-size=1260,820"])
                return
    elif sys.platform.startswith("linux"):
        for browser in ("chromium", "chromium-browser", "google-chrome", "microsoft-edge", "brave-browser"):
            found = shutil.which(browser)
            if found:
                subprocess.Popen(
                    [found, f"--app={url}", "--window-size=1260,820"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
        for opener in ("xdg-open", "firefox-esr", "firefox"):
            found = shutil.which(opener)
            if found:
                subprocess.Popen(
                    [found, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
    webbrowser.open(url)


def _safe_emit(text: str, *, out_file: str | None = None) -> None:
    """Safely emit output even in Windows GUI (`console=False`) mode where `sys.stdout` can be None."""
    if out_file:
        Path(out_file).expanduser().write_text(text + "\n", encoding="utf-8")
    if sys.stdout is not None:
        try:
            print(text, flush=True)
        except OSError:
            pass


def _pop_flag_value(args: list[str], flag: str) -> str | None:
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            val = args[idx + 1]
            del args[idx : idx + 2]
            return val
    return None


def launch_desktop(argv: list[str] | None = None) -> int:
    """Unified entrypoint for `--server-only` (macOS Swift WKWebView host) or standalone GUI (Windows .exe)."""
    args = list(sys.argv[1:] if argv is None else argv)
    out_file = _pop_flag_value(args, "--out-file")
    ready_file = _pop_flag_value(args, "--ready-file")

    if args and args[0] == "--self-test":
        payload = json.dumps({"app": "Nexus Memory Desktop", "version": __version__, "self_test": "ok"}, ensure_ascii=False)
        _safe_emit(payload, out_file=out_file)
        return 0
    if args and args[0] == "--cli":
        import contextlib
        import io
        from .cli import main as cli_main

        if out_file or sys.stdout is None:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cli_main(args[1:])
            _safe_emit(buf.getvalue().rstrip("\n"), out_file=out_file)
            return rc
        return cli_main(args[1:])

    server_only = "--server-only" in args
    port_str = _pop_flag_value(args, "--port")
    port = int(port_str) if port_str else 0

    srv, url, _ = start_desktop_server(port=port)
    if server_only:
        ready_json = json.dumps({"ready": True, "url": url, "version": __version__}, ensure_ascii=False)
        _safe_emit(ready_json, out_file=ready_file or out_file)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            srv.server_close()
        return 0

    threading.Thread(target=srv.serve_forever, daemon=True).start()
    _open_standalone_window(url)
    _safe_emit(f"Nexus Memory Desktop running at {url} (Press Ctrl+C to quit)")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(launch_desktop())
