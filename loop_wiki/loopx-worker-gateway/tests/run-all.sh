#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/../../.." && pwd)
MODULE="$ROOT/loop_wiki/loopx-worker-gateway"

python3 "$MODULE/scripts/check_contracts.py"
python3 "$MODULE/scripts/check_contracts.py" --selftest
python3 "$MODULE/scripts/gateway.py" selftest
python3 "$MODULE/scripts/control_gateway.py"

python3 -m py_compile \
  "$MODULE/scripts/gateway_common.py" \
  "$MODULE/scripts/gateway_engine.py" \
  "$MODULE/scripts/gateway.py" \
  "$MODULE/scripts/check_contracts.py" \
  "$MODULE/scripts/gateway_selftest.py" \
  "$MODULE/scripts/control_gateway.py" \
  "$MODULE/tests/fixtures/good/fixture_worker.py"

python3 - "$MODULE" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
files = sorted(root.rglob("*.json"))
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-worker-gateway JSON PASS: {len(files)} files")
PY
