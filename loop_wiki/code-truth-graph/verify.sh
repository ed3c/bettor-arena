#!/bin/sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64
for required in AGENTS.md CLAUDE.md PROMPT.md PLAN.md ROUTES.md trigger.sh local-trigger.sh run.sh selftest.sh portability.sh modules/eight-base-laws.md modules/exchange-formats.md schemas/ctg-input.schema.json schemas/ctg-route-result.schema.json schemas/ctg-local-build-receipt.schema.json src/code_truth_graph/verify_artifacts.py; do
  [ -f "$HERE/$required" ] || {
    echo "FAIL: missing CTG base artifact $required" >&2
    exit 2
  }
done

command -v ruff >/dev/null 2>&1 || {
  echo "verify FATAL: ruff is required" >&2
  exit 64
}
ruff format --check "$HERE/src" || exit 2
ruff check --quiet "$HERE/src" || exit 2
sh "$HERE/selftest.sh" || exit $?
sh "$HERE/portability.sh" || exit $?
sh "$HERE/../../tests/test_ctg_cli.sh" || exit $?
sh "$HERE/../../tests/test_ctg_java_core.sh" || exit $?
sh "$HERE/../../tests/test_ctg_local_build.sh" || exit $?

echo "PASS: Code Truth Graph candidate verified"
