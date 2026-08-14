#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/check_gateway.py" --root "$ROOT"
"$PYTHON" "$ROOT/scripts/check_gateway.py" --root "$ROOT" --selftest
"$PYTHON" "$ROOT/scripts/control_gateway.py" --root "$ROOT"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/gateway_common.py" \
  "$ROOT/scripts/gateway_contract.py" \
  "$ROOT/scripts/gateway_runtime.py" \
  "$ROOT/scripts/gateway.py" \
  "$ROOT/scripts/fake_worker.py" \
  "$ROOT/scripts/check_gateway.py" \
  "$ROOT/scripts/control_gateway.py" \
  "$ROOT/adapters/unimplemented.py"

"$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import json
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no Worker Gateway JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-worker-gateway JSON PASS: {len(paths)} files")
PY
