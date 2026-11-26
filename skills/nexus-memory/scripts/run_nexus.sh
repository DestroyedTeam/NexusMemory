#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SKILL_DIR/../.." && pwd)
PYTHON_BIN="${NEXUS_MEMORY_PYTHON:-python3}"
if [ -x "/opt/anaconda3/bin/python3" ] && ! "$PYTHON_BIN" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
  PYTHON_BIN="/opt/anaconda3/bin/python3"
fi
if [ -d "$SKILL_DIR/lib/nexus_memory" ]; then
  exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SKILL_DIR/lib${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m nexus_memory "$@"
fi
if [ -n "${NEXUS_MEMORY_SRC:-}" ] && [ -d "$NEXUS_MEMORY_SRC/nexus_memory" ]; then
  exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$NEXUS_MEMORY_SRC${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m nexus_memory "$@"
fi
if [ -d "$REPO_ROOT/src/nexus_memory" ]; then
  exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m nexus_memory "$@"
fi
if command -v nexus-memory >/dev/null 2>&1; then
  exec nexus-memory "$@"
fi
echo "nexus-memory runtime not found; reinstall skill or set NEXUS_MEMORY_SRC" >&2
exit 127
