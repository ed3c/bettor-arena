#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/check_contracts.py" --root "$ROOT"
"$PYTHON" "$ROOT/scripts/check_contracts.py" --root "$ROOT" --selftest
"$PYTHON" "$ROOT/scripts/ledger.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_ledger.py" --root "$ROOT"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/ledger_common.py" \
  "$ROOT/scripts/ledger_contract_helpers.py" \
  "$ROOT/scripts/ledger_event.py" \
  "$ROOT/scripts/ledger_contract.py" \
  "$ROOT/scripts/ledger_reduce.py" \
  "$ROOT/scripts/ledger_store.py" \
  "$ROOT/scripts/ledger_engine.py" \
  "$ROOT/scripts/ledger_cli.py" \
  "$ROOT/scripts/ledger_selftest.py" \
  "$ROOT/scripts/ledger.py" \
  "$ROOT/scripts/check_contracts.py" \
  "$ROOT/scripts/control_ledger.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Ledger JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-ledger JSON PASS: {len(paths)} files")
PY
