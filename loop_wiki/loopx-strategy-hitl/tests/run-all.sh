#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/check_contracts.py" --root "$ROOT"
"$PYTHON" "$ROOT/scripts/check_contracts.py" --root "$ROOT" --selftest
"$PYTHON" "$ROOT/scripts/hitl.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/hitl.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_strategy.py" --root "$ROOT"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/strategy_common.py" \
  "$ROOT/scripts/strategy_checkpoint.py" \
  "$ROOT/scripts/strategy_decision.py" \
  "$ROOT/scripts/strategy_engine.py" \
  "$ROOT/scripts/strategy_contract.py" \
  "$ROOT/scripts/strategy_selftest.py" \
  "$ROOT/scripts/hitl.py" \
  "$ROOT/scripts/check_contracts.py" \
  "$ROOT/scripts/control_strategy.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Strategy + HITL JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-strategy-hitl JSON PASS: {len(paths)} files")
PY
