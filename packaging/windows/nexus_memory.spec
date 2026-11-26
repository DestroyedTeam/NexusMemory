# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building standalone Windows GUI `NexusMemory.exe`.

Launches the futuristic Obsidian Neural Console desktop UI in chromeless Edge/Chrome app mode
(with native Windows file/folder pickers and zero console window flash), plus `--cli` passthrough.

Build on Windows (PowerShell):
    pip install pyinstaller
    pyinstaller packaging/windows/nexus_memory.spec
"""

from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(REPO_ROOT / "src" / "nexus_memory" / "desktop_ui.py")],
    pathex=[str(REPO_ROOT / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "nexus_memory.bundle",
        "nexus_memory.chatgpt",
        "nexus_memory.claude_code",
        "nexus_memory.claude_desktop_3p",
        "nexus_memory.cli",
        "nexus_memory.codex",
        "nexus_memory.desktop_ui",
        "nexus_memory.discovery",
        "nexus_memory.ecosystem",
        "nexus_memory.harnesses_extended",
        "nexus_memory.matrix",
        "nexus_memory.model",
        "nexus_memory.resources",
        "nexus_memory.security",
        "nexus_memory.transaction",
        "nexus_memory.viewer",
        "nexus_memory.write_gate",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="NexusMemory",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
