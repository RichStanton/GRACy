#!/bin/bash
# smoke_assembly.sh — heavy end-to-end smoke test of the GRACy assembly pipeline (issue #11).
#
# Thin wrapper around tests/harness/smoke_assembly.py: it picks the bundled interpreter (which
# has PyQt5 + Biopython), forces headless Qt, and enforces an outer time budget. The Python
# driver does the real work; see its docstring for why it drives the Qt widget directly.
#
# Usage:   bash tests/harness/smoke_assembly.sh [extra args passed through to the .py]
#   e.g.   bash tests/harness/smoke_assembly.sh --golden tests/expected/smoke_assembly.fingerprint
# Env:     TIMEOUT (default 3600s) outer wall-clock budget for the whole run.
# Runs for many minutes and needs the toolchain (src/conda + src/conda2) installed.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$REPO/src/conda/bin/python"
[ -x "$PY" ] || { echo "FATAL: bundled interpreter not found at $PY — run install.sh first"; exit 2; }

export QT_QPA_PLATFORM=offscreen
TIMEOUT="${TIMEOUT:-3600}"
echo "interpreter: $PY"
echo "time budget: ${TIMEOUT}s"
exec timeout "$TIMEOUT" "$PY" "$REPO/tests/harness/smoke_assembly.py" "$@"
