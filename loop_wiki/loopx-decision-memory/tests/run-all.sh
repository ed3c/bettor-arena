#!/bin/sh
set -eu
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
python3 "$ROOT/loop_wiki/loopx-decision-memory/scripts/memory.py" check
python3 "$ROOT/loop_wiki/loopx-decision-memory/scripts/memory.py" selftest
python3 -m py_compile "$ROOT/loop_wiki/loopx-decision-memory/scripts/memory.py"
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "loop_wiki/loopx-decision-memory"
files = sorted(root.rglob("*.json"))
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-decision-memory JSON PASS: {len(files)} files")
PY
