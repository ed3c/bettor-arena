#!/usr/bin/env sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_ROOT=$(CDPATH= cd -- "$HERE/.." && pwd)

python3 "$SKILL_ROOT/scripts/check_portable_execution_contract.py" --selftest
python3 "$SKILL_ROOT/scripts/check_portable_execution_contract.py" --root "$HERE/fixtures/good"
python3 "$HERE/run-mutation-matrix.py"
python3 "$SKILL_ROOT/scripts/run_portable_skill.py" selftest

for schema in "$SKILL_ROOT"/contracts/*.schema.json; do
  python3 -m json.tool "$schema" >/dev/null
done

python3 -m compileall -q \
  "$SKILL_ROOT/scripts/check_portable_execution_contract.py" \
  "$SKILL_ROOT/scripts/run_portable_skill.py" \
  "$HERE/run-mutation-matrix.py" \
  "$HERE/run-execution-selftest.py"
