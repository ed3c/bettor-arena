#!/bin/sh
# Seam: the repo-local runtime-env binding gate proves both positive and
# negative controls, and pre-commit invokes its staged-index mode.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GATE="$ROOT/scripts/gates/check_runtime_env_binding.py"

python3 "$GATE" --selftest
grep -Fq 'python3 scripts/gates/check_runtime_env_binding.py --staged' \
  "$ROOT/.githooks/pre-commit" || {
  echo "FAIL: pre-commit does not run the staged runtime-env binding gate" >&2
  exit 1
}

grep -Fq 'verify-consumer' "$GATE" || {
  echo "FAIL: repo-local gate does not delegate to the installed runtime-env public seam" >&2
  exit 1
}
grep -Fq 'bettor-arena-local' "$GATE" || {
  echo "FAIL: repo-local gate does not pin the bettor-arena binding id" >&2
  exit 1
}

python3 "$GATE"

echo "PASS: runtime-env binding gate seam"
