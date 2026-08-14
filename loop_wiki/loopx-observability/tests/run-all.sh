#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/observability.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/observability.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_observability.py" --root "$ROOT"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/obs_common.py" \
  "$ROOT/scripts/obs_redaction.py" \
  "$ROOT/scripts/obs_envelope.py" \
  "$ROOT/scripts/obs_action.py" \
  "$ROOT/scripts/obs_contract.py" \
  "$ROOT/scripts/obs_selftest.py" \
  "$ROOT/scripts/observability.py" \
  "$ROOT/scripts/control_observability.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Observability JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-observability JSON PASS: {len(paths)} files")
PY
