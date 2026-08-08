#!/bin/sh
# control_ctg_entry.sh — behavior-derived CTG input/output coverage control.
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init ctg-entry
ROOT=$CAPTURE_ROOT
SHORT=$CAPTURE_SHORT
HELPER="$CAPTURE_HOME/ctg_control.py"

BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-ctg.XXXXXX") || exit 64
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT HUP INT TERM
git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1 || {
  echo "control FATAL: could not create detached CTG run worktree" >&2
  exit 64
}

F=loop_wiki/code-truth-graph
PYTHONPATH="$WT/$F/src" python3 -m code_truth_graph.fixture --out "$BASE/frozen" >/dev/null || exit 64
PACKET_REL=ctg-input.json

run_case() { # id bundle-dir output-dir
  CAPTURE_CWD="$WT"
  capture "$1" -- sh "$WT/loopctl/loopctl.sh" ctg run \
    --packet "$2/$PACKET_REL" --output "$3"
  _rc=$?
  CAPTURE_CWD=""
  return "$_rc"
}

cp -R "$BASE/frozen" "$BASE/baseline-1"
run_case baseline-1 "$BASE/baseline-1" "$BASE/out-baseline-1"
BASE_RC=$?
[ "$BASE_RC" -eq 0 ] || {
  echo "control FAIL: CTG baseline exited $BASE_RC" >&2
  exit 2
}
BASE_PROJECTION=$(python3 "$HELPER" projection --result "$BASE/out-baseline-1/ctg-route-result.json") || exit 64

cp -R "$BASE/frozen" "$BASE/baseline-2"
run_case baseline-2 "$BASE/baseline-2" "$BASE/out-baseline-2"
REPEAT_RC=$?
REPEAT_PROJECTION=$(python3 "$HELPER" projection --result "$BASE/out-baseline-2/ctg-route-result.json") || exit 64
[ "$REPEAT_RC" -eq "$BASE_RC" ] && [ "$REPEAT_PROJECTION" = "$BASE_PROJECTION" ] || {
  echo "control FATAL: same frozen packet produced nondeterministic exit/projection" >&2
  exit 64
}

python3 "$HELPER" candidates --packet "$BASE/frozen/$PACKET_REL" >"$RUNDIR/candidate-inputs.txt" || exit 64
[ -s "$RUNDIR/candidate-inputs.txt" ] || {
  echo "control FATAL: candidate closure is empty" >&2
  exit 64
}
: >"$RUNDIR/input-class.txt"
RED=0
N=0
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  N=$((N + 1))
  BUNDLE="$BASE/probe-$N"
  OUTPUT="$BASE/out-probe-$N"
  cp -R "$BASE/frozen" "$BUNDLE"
  [ -f "$BUNDLE/$rel" ] || {
    printf '%s\tunprobeable\t64\tABSENT\n' "$rel" >>"$RUNDIR/input-class.txt"
    RED=1
    continue
  }
  mv "$BUNDLE/$rel" "$BUNDLE/$rel.away"
  run_case "probe-$N" "$BUNDLE" "$OUTPUT"
  RC=$?
  PROJECTION=$(python3 "$HELPER" projection --result "$OUTPUT/ctg-route-result.json") || exit 64
  if [ "$RC" -ne "$BASE_RC" ]; then
    CLASS=required
  elif [ "$PROJECTION" != "$BASE_PROJECTION" ]; then
    CLASS=optional-consumed
  else
    CLASS=unused
    RED=1
  fi
  printf '%s\t%s\t%s\t%s\n' "$rel" "$CLASS" "$RC" "$PROJECTION" >>"$RUNDIR/input-class.txt"
  echo "  [probe] $rel -> $CLASS (exit $RC, baseline $BASE_RC)"
done <"$RUNDIR/candidate-inputs.txt"

cp -R "$BASE/frozen" "$BASE/after"
run_case baseline-after-probes "$BASE/after" "$BASE/out-after"
AFTER_RC=$?
AFTER_PROJECTION=$(python3 "$HELPER" projection --result "$BASE/out-after/ctg-route-result.json") || exit 64
[ "$AFTER_RC" -eq "$BASE_RC" ] && [ "$AFTER_PROJECTION" = "$BASE_PROJECTION" ] || {
  echo "control FATAL: baseline changed after probes; probe damage invalidates classifications" >&2
  exit 64
}

python3 "$HELPER" produced --result "$BASE/out-baseline-1/ctg-route-result.json" >"$RUNDIR/produced-paths.txt" || exit 64

PROVE_FORCE_RECEIPT=1 sh "$ROOT/proof_workflow/prove_ctg_loop.sh" >/dev/null || exit $?
PROOF="$ROOT/data/proof-workflow/ctg-$SHORT.json"
[ -f "$PROOF" ] || PROOF="$ROOT/data/proof-workflow/ctg-$SHORT-dirty.json"
[ -f "$PROOF" ] || {
  echo "control FATAL: same-call CTG proof receipt is absent" >&2
  exit 64
}
PROOF_DIGEST=$(python3 "$HELPER" proof-check --receipt "$PROOF") || exit 64

RECEIPT="$ROOT/data/proof-workflow/control-ctg-$SHORT.json"
CONTROL_RECEIPT="$RECEIPT" CONTROL_COMMIT="$CAPTURE_COMMIT" CONTROL_RUN_ID="$RUN_ID" \
CONTROL_ENTRY_RC="$BASE_RC" CONTROL_PROJECTION="$BASE_PROJECTION" CONTROL_PROOF_DIGEST="$PROOF_DIGEST" \
CONTROL_CLASSES="$RUNDIR/input-class.txt" CONTROL_PRODUCED="$RUNDIR/produced-paths.txt" CONTROL_RUNS="$RUNDIR/run.jsonl" \
CONTROL_STATUS="$([ "$RED" -eq 0 ] && echo passed || echo failed)" \
python3 - <<'PY' || exit 64
import json
import os
from pathlib import Path

def lines(name):
    return [line for line in Path(os.environ[name]).read_text().splitlines() if line]

classes = []
for line in lines("CONTROL_CLASSES"):
    ref, classification, exit_code, projection = line.split("\t")
    classes.append({"artifact_ref": ref, "classification": classification, "exit": int(exit_code), "projection": projection})
receipt = {
    "schema_version": "bettor-arena-ctg-control@1.0.0",
    "commit": os.environ["CONTROL_COMMIT"],
    "run_id": os.environ["CONTROL_RUN_ID"],
    "status": os.environ["CONTROL_STATUS"],
    "baseline": {"exit": int(os.environ["CONTROL_ENTRY_RC"]), "canonical_projection": os.environ["CONTROL_PROJECTION"], "repeat_count": 3},
    "input_classifications": classes,
    "produced_artifacts": lines("CONTROL_PRODUCED"),
    "proof_digest": os.environ["CONTROL_PROOF_DIGEST"],
    "runs": [
        {
            "seq": run["seq"],
            "id": run["id"],
            "cwd": run["cwd"],
            "exit": run["exit"],
            "stdout": {"sha256": run["stdout"]["sha256"], "bytes": run["stdout"]["bytes"]},
            "stderr": {"sha256": run["stderr"]["sha256"], "bytes": run["stderr"]["bytes"]},
        }
        for run in (json.loads(line) for line in lines("CONTROL_RUNS"))
    ],
    "claim_boundary": "copied deterministic packet closure only; no live PROD/device side effect",
}
Path(os.environ["CONTROL_RECEIPT"]).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
PY

if [ "$RED" -ne 0 ]; then
  echo "control FAIL: unused or unprobeable CTG input; receipt=$RECEIPT" >&2
  exit 2
fi
echo "control PASS: copied closure classified, baseline stable, proof linked; receipt=$RECEIPT"
exit 0
