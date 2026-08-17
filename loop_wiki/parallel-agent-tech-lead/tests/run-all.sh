#!/bin/sh
set -eu
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
python3 "$ROOT/loop_wiki/parallel-agent-tech-lead/tests/test_plan.py"
python3 -m py_compile \
  "$ROOT/loop_wiki/parallel-agent-tech-lead/scripts/plan.py" \
  "$ROOT/loop_wiki/parallel-agent-tech-lead/tests/test_plan.py"
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "loop_wiki/parallel-agent-tech-lead"
for path in sorted(root.rglob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
print("parallel-agent-tech-lead JSON PASS")
PY
