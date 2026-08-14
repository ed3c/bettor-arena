#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/check_contracts.py"
"$PYTHON" "$ROOT/scripts/check_contracts.py" --selftest
"$PYTHON" "$ROOT/scripts/control_contracts.py"
"$PYTHON" -m py_compile \
  "$ROOT/scripts/contract_common.py" \
  "$ROOT/scripts/contract_validate.py" \
  "$ROOT/scripts/check_contracts.py" \
  "$ROOT/scripts/control_contracts.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-contracts JSON PASS: {len(paths)} files")
PY
