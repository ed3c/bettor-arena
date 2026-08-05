#!/bin/sh
# Seam: replay_corpus_parity.py precondition exits. The measurement itself needs
# bun + a source checkout; what this test pins is that every missing
# precondition dies FATAL 64 with a diagnostic, never a bare traceback.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TOOL="$ROOT/tests/tools/replay_corpus_parity.py"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $1" >&2; exit 1; }

PY=$(command -v python3) || fail "python3 not found"

# 1) bun completely absent from PATH → FATAL 64, diagnostic names bun.
#    /usr/bin:/bin carries python3+git but never bun (bun installs under $HOME).
set +e
ERR=$(env PATH=/usr/bin:/bin "$PY" "$TOOL" --source-repo "$TMP" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "bun-absent run exited $RC, want 64 — output: $ERR"
echo "$ERR" | grep -qi "bun" || fail "bun-absent diagnostic does not name bun: $ERR"
echo "$ERR" | grep -q "Traceback" && fail "bun-absent run leaked a traceback: $ERR"

# 2) positive control for the die() path with bun present: missing original
#    validator → FATAL 64 naming it (proves 64s are deliberate, not accidents).
command -v bun >/dev/null || { echo "SKIP: bun not installed, control 2 skipped"; exit 0; }
set +e
ERR=$(env "$PY" "$TOOL" --source-repo "$TMP" 2>&1)
RC=$?
set -e
[ "$RC" -eq 64 ] || fail "missing-validator run exited $RC, want 64 — output: $ERR"
echo "$ERR" | grep -q "original validator missing" || fail "diagnostic does not name the missing validator: $ERR"

echo "PASS: replay_corpus_parity preconditions die FATAL 64 with diagnostics"
