#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/knowledge.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/knowledge.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_knowledge.py" --root "$ROOT" >/dev/null
echo "loopx-knowledge-compiler physical control PASS: 4 lease controls on a real tree"

# The public port must reach CANDIDATE and stop there. Run as a separate
# process so the terminal state is read from the emitted receipt rather than
# from an object still held in the interpreter that produced it.
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
"$PYTHON" "$ROOT/scripts/knowledge.py" compile --root "$ROOT" \
  --output-root "$TMP/candidate" --output "$TMP/compile.json" >/dev/null
"$PYTHON" - "$TMP/compile.json" "$TMP/receipt.json" <<'PY'
import json, sys
from pathlib import Path
result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if result["state_trace"][-1] != "CANDIDATE_RECEIPT":
    raise SystemExit(f"compile ended at {result['state_trace'][-1]!r}, not CANDIDATE_RECEIPT")
receipt = result["receipt"]
if receipt["state"] != "CANDIDATE" or receipt["admit_required"] is not True:
    raise SystemExit("the compiler emitted something other than a candidate awaiting admit")
Path(sys.argv[2]).write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(f"loopx-knowledge-compiler port PASS: {len(result['state_trace'])} states, receipt CANDIDATE")
PY
"$PYTHON" "$ROOT/scripts/knowledge.py" verify-receipt --receipt "$TMP/receipt.json"

# Without --output-root the compile must render into a disposable tree and take
# it with it. Run from an empty directory and require that directory to stay
# empty: a compiler that defaulted to the caller's cwd would eventually be run
# from a checkout, and the candidate scaffold would land in it.
mkdir -p "$TMP/cwd"
(cd "$TMP/cwd" && "$PYTHON" "$ROOT/scripts/knowledge.py" compile --root "$ROOT" >/dev/null)
LEFTOVER=$(find "$TMP/cwd" -mindepth 1 | wc -l | tr -d ' ')
test "$LEFTOVER" = "0" || {
  echo "the default compile left $LEFTOVER path(s) in the working directory" >&2
  exit 2
}
echo "loopx-knowledge-compiler disposable-tree PASS: default compile left an empty cwd"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/kc_common.py" \
  "$ROOT/scripts/kc_source.py" \
  "$ROOT/scripts/kc_assertion.py" \
  "$ROOT/scripts/kc_card.py" \
  "$ROOT/scripts/kc_spec.py" \
  "$ROOT/scripts/kc_codeop.py" \
  "$ROOT/scripts/kc_scaffold.py" \
  "$ROOT/scripts/kc_compile.py" \
  "$ROOT/scripts/kc_contract.py" \
  "$ROOT/scripts/kc_selftest.py" \
  "$ROOT/scripts/knowledge.py" \
  "$ROOT/scripts/control_knowledge.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Knowledge Compiler JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-knowledge-compiler JSON PASS: {len(paths)} files")
PY
