#!/usr/bin/env python3
"""Build a universal Debian/Ubuntu `.deb` package (`Architecture: all`) for Nexus Memory.

Works on Debian 12/13, Ubuntu 22.04/24.04+, Linux Mint, etc. across both `amd64` and `arm64`.
Uses `dpkg-deb --root-owner-group` when available on Linux, or writes an exact Debian `ar`
archive (`debian-binary` + `control.tar.gz` + `data.tar.gz`) in pure Python stdlib so it
builds cleanly even on macOS.
"""

from __future__ import annotations

import argparse
import gzip
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0B1120"/>
      <stop offset="50%" stop-color="#111C36"/>
      <stop offset="100%" stop-color="#1A274A"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#818CF8"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="224" height="224" rx="52" fill="url(#bg)" stroke="url(#accent)" stroke-width="5"/>
  <path d="M80 90 L176 90 L128 176 Z" fill="none" stroke="url(#accent)" stroke-width="10" stroke-linejoin="round"/>
  <circle cx="80" cy="90" r="18" fill="#38BDF8"/>
  <circle cx="80" cy="90" r="8" fill="#F8FAFC"/>
  <circle cx="176" cy="90" r="18" fill="#38BDF8"/>
  <circle cx="176" cy="90" r="8" fill="#F8FAFC"/>
  <circle cx="128" cy="176" r="18" fill="#818CF8"/>
  <circle cx="128" cy="176" r="8" fill="#F8FAFC"/>
</svg>
"""

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=Nexus Memory
GenericName=AI Harness Migration Console
Comment=Local-first, zero-AI deterministic migration across 23 AI agent Harnesses
Exec=/usr/bin/nexus-memory-desktop
Icon=nexus-memory
Terminal=false
Categories=Development;Utility;
Keywords=AI;Agent;Migration;Codex;Claude;Antigravity;Cursor;Windsurf;
StartupNotify=true
"""

CLI_WRAPPER = """#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/usr/lib/nexus-memory${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m nexus_memory "$@"
"""

DESKTOP_WRAPPER = """#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/usr/lib/nexus-memory${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m nexus_memory.desktop_ui "$@"
"""


def _ar_entry(name: str, data: bytes, mtime: int) -> bytes:
    header = (
        f"{name:<16}"
        f"{mtime:<12}"
        f"{'0':<6}"
        f"{'0':<6}"
        f"{'100644':<8}"
        f"{len(data):<10}"
        "`\n"
    ).encode("ascii")
    assert len(header) == 60
    pad = b"\n" if len(data) % 2 == 1 else b""
    return header + data + pad


def _tar_gz_from_dir(root: Path, mtime: int) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=mtime) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tf:
            for item in sorted(root.rglob("*")):
                rel = "./" + item.relative_to(root).as_posix()
                info = tarfile.TarInfo(name=rel)
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                info.mtime = mtime
                if item.is_dir():
                    info.type = tarfile.DIRTYPE
                    info.mode = 0o755
                    tf.addfile(info)
                elif item.is_file():
                    data = item.read_bytes()
                    info.type = tarfile.REGTYPE
                    info.size = len(data)
                    info.mode = 0o755 if os.access(item, os.X_OK) else 0o644
                    tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def build_deb(repo_root: Path, out_dir: Path) -> Path:
    sys.path.insert(0, str(repo_root / "src"))
    from nexus_memory import __version__ as version

    out_dir.mkdir(parents=True, exist_ok=True)
    deb_path = out_dir / f"nexus-memory_{version}_all.deb"

    with tempfile.TemporaryDirectory(prefix="nexus_deb_") as td:
        stage = Path(td) / "pkg"
        debian_dir = stage / "DEBIAN"
        lib_dir = stage / "usr" / "lib" / "nexus-memory" / "nexus_memory"
        bin_dir = stage / "usr" / "bin"
        apps_dir = stage / "usr" / "share" / "applications"
        icons_dir = stage / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
        doc_dir = stage / "usr" / "share" / "doc" / "nexus-memory"

        for d in (debian_dir, bin_dir, apps_dir, icons_dir, doc_dir):
            d.mkdir(parents=True, exist_ok=True)

        shutil.copytree(
            repo_root / "src" / "nexus_memory",
            lib_dir,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

        cli_bin = bin_dir / "nexus-memory"
        cli_bin.write_text(CLI_WRAPPER, encoding="utf-8")
        cli_bin.chmod(0o755)

        gui_bin = bin_dir / "nexus-memory-desktop"
        gui_bin.write_text(DESKTOP_WRAPPER, encoding="utf-8")
        gui_bin.chmod(0o755)

        (apps_dir / "nexus-memory.desktop").write_text(DESKTOP_ENTRY, encoding="utf-8")
        (icons_dir / "nexus-memory.svg").write_text(ICON_SVG, encoding="utf-8")
        if (repo_root / "README.md").is_file():
            shutil.copy2(repo_root / "README.md", doc_dir / "README.md")

        total_bytes = sum(p.stat().st_size for p in (stage / "usr").rglob("*") if p.is_file())
        installed_kb = max(1, (total_bytes + 1023) // 1024)

        control = (
            f"Package: nexus-memory\n"
            f"Version: {version}\n"
            f"Section: devel\n"
            f"Priority: optional\n"
            f"Architecture: all\n"
            f"Installed-Size: {installed_kb}\n"
            f"Depends: python3 (>= 3.11)\n"
            f"Recommends: xdg-utils\n"
            f"Maintainer: DestroyedTeam <https://github.com/DestroyedTeam/NexusMemory>\n"
            f"Homepage: https://github.com/DestroyedTeam/NexusMemory\n"
            f"Description: Local-first deterministic AI Harness migration tool\n"
            f" Migrates Projects, Section Groups, Session DAGs, attachments, Skills,\n"
            f" and secret-stripped MCP configs across 23 bidirectional AI agent\n"
            f" Harnesses (Codex, Claude Code, Antigravity, Cursor, Windsurf, etc.).\n"
        )
        (debian_dir / "control").write_text(control, encoding="utf-8")

        dpkg_deb = shutil.which("dpkg-deb")
        if dpkg_deb:
            subprocess.run(
                [dpkg_deb, "--build", "--root-owner-group", str(stage), str(deb_path)],
                check=True,
            )
        else:
            mtime = int(time.time())
            data_root = Path(td) / "data_root"
            data_root.mkdir()
            shutil.copytree(stage / "usr", data_root / "usr")
            control_tar_gz = _tar_gz_from_dir(debian_dir, mtime)
            data_tar_gz = _tar_gz_from_dir(data_root, mtime)
            deb_bytes = (
                b"!<arch>\n"
                + _ar_entry("debian-binary", b"2.0\n", mtime)
                + _ar_entry("control.tar.gz", control_tar_gz, mtime)
                + _ar_entry("data.tar.gz", data_tar_gz, mtime)
            )
            deb_path.write_bytes(deb_bytes)

    return deb_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Debian/Ubuntu .deb package for Nexus Memory")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "dist")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    deb = build_deb(repo_root, args.out_dir.expanduser().resolve())
    print(f"Built Debian package: {deb} ({deb.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
