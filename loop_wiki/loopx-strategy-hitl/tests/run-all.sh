#!/bin/sh
set -eu
MODULE=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

python3 "$MODULE/scripts/hitl.py" check
python3 "$MODULE/scripts/hitl.py" selftest
python3 "$MODULE/scripts/hitl.py" control
python3 -m py_compile "$MODULE/scripts/hitl.py"

python3 - "$MODULE" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
files = sorted(root.rglob("*.json"))
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-strategy-hitl JSON PASS: {len(files)} files")
PY
