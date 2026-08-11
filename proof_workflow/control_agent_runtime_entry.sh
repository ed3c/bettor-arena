#!/bin/sh
# Independent control: a clean synthetic module set passes, then four isolated
# defects must each turn the public validator red.
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init agent-runtime-entry
ROOT=$CAPTURE_ROOT
HELPER="$ROOT/proof_workflow/agent_runtime_control.py"
SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/agent-runtime-control.XXXXXX")
trap 'rm -rf "$SCRATCH"' EXIT
RED=0

make_case() {
  python3 "$HELPER" make "$ROOT" "$SCRATCH/$1" || exit 64
}

make_case baseline
CAPTURE_CWD="$SCRATCH/baseline" capture baseline-offline -- \
  python3 scripts/agent_runtime.py check --offline
[ "$?" -eq 0 ] || RED=1
CAPTURE_CWD="$SCRATCH/baseline" capture baseline-adapter -- \
  python3 scripts/agent_runtime.py check --adapter
[ "$?" -eq 0 ] || RED=1
CAPTURE_CWD="$SCRATCH/baseline" capture live-not-exercised -- \
  python3 scripts/agent_runtime.py check
[ "$?" -eq 2 ] || RED=1

for kind in shared-binding runtime-requirements claude-surface codex-surface; do
  make_case "$kind"
  python3 "$HELPER" mutate "$SCRATCH/$kind" "$kind" || exit 64
  level=--offline
  case "$kind" in *-surface) level=--adapter ;; esac
  CAPTURE_CWD="$SCRATCH/$kind" capture "planted-$kind" -- \
    python3 scripts/agent_runtime.py check "$level"
  [ "$?" -eq 2 ] || {
    echo "control RED: planted $kind returned $? instead of 2" >&2
    RED=1
  }
done

echo "control[agent-runtime-entry] trace=proof_workflow/data/$RUN_ID"
[ "$RED" -eq 0 ] && { echo "PASS: missing live evidence stayed incomplete and all four planted module-set defects were detected"; exit 0; }
echo "FAIL: agent-runtime control did not detect every planted defect" >&2
exit 2
