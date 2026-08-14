#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/fabric.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/fabric.py" selftest --root "$ROOT"

# The physical control group builds real workspaces and runs real processes.
# It is separate from the selftest on purpose: everything above validates
# shapes, and this is the part that answers "does isolation physically fail".
"$PYTHON" "$ROOT/scripts/control_fabric.py" --root "$ROOT"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/fabric_common.py" \
  "$ROOT/scripts/fabric_lease.py" \
  "$ROOT/scripts/fabric_request.py" \
  "$ROOT/scripts/fabric_local.py" \
  "$ROOT/scripts/fabric_parity.py" \
  "$ROOT/scripts/fabric_contract.py" \
  "$ROOT/scripts/fabric_selftest.py" \
  "$ROOT/scripts/fabric.py" \
  "$ROOT/scripts/control_fabric.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Runtime Fabric JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-runtime-fabric JSON PASS: {len(paths)} files")
PY
