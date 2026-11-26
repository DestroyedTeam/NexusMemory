"""PyInstaller top-level entrypoint for standalone Windows GUI `NexusMemory.exe`.

Uses absolute package imports so `nexus_memory` relative imports work cleanly inside frozen bundles.
"""

from __future__ import annotations

from nexus_memory.desktop_ui import launch_desktop


if __name__ == "__main__":
    raise SystemExit(launch_desktop())
