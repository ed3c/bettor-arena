#!/bin/sh
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)

python3 "$ROOT/scripts/agent_runtime.py" check --offline | grep -q '^PASS agent module set level=offline$'
sh "$ROOT/proof_workflow/control_agent_runtime_entry.sh" | \
  grep -q '^PASS: missing live evidence stayed incomplete and all four planted module-set defects were detected$'
sh "$ROOT/loopctl/loopctl.sh" --selftest | grep -q '^SELFTEST GREEN$'

echo "PASS: aggregate Agent module-set seam"
