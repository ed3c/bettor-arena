#!/bin/sh
# control_ctg_entry.sh — behavior-derived CTG input/output coverage control.
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init ctg-entry
ROOT=$CAPTURE_ROOT
SHORT=$CAPTURE_SHORT
HELPER="$CAPTURE_HOME/ctg_control.py"

PROOF="$ROOT/data/proof-workflow/ctg-$SHORT.json"
[ -f "$PROOF" ] || {
  echo "control FATAL: no clean CTG proof at current HEAD $SHORT; run ctg prove after committing the mechanism" >&2
  exit 64
}
PROOF_DIGEST=$(python3 "$HELPER" proof-check --repo "$ROOT" --receipt "$PROOF") || exit 64

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
: >"$RUNDIR/axis-positive.txt"
: >"$RUNDIR/plants.txt"

run_case() { # id bundle-dir output-dir
  CAPTURE_CWD="$WT"
  capture "$1" -- sh "$WT/loopctl/loopctl.sh" ctg run \
    --packet "$2/$PACKET_REL" --output "$3"
  _rc=$?
  CAPTURE_CWD=""
  return "$_rc"
}

run_contract_test() { # id script
  CAPTURE_CWD="$WT"
  capture "$1" -- sh -c 'sh "$1"; rc=$?; case "$rc" in 0|2|64) exit "$rc" ;; *) exit 2 ;; esac' sh "$2"
  _rc=$?
  CAPTURE_CWD=""
  return "$_rc"
}

axis_positive() { # axis id script
  run_contract_test "$2" "$3"
  _rc=$?
  printf '%s\t%s\n' "$1" "$_rc" >>"$RUNDIR/axis-positive.txt"
  if [ "$_rc" -ne 0 ]; then
    echo "control RED: $1 positive control exited $_rc" >&2
    RED=1
  fi
}

plant_and_require_red() { # id axis target anchor replacement test-script
  _id=$1
  _axis=$2
  _target=$3
  _anchor=$4
  _replacement=$5
  _test=$6
  python3 - "$WT/$_target" "$_anchor" "$_replacement" <<'PY'
import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
source, anchor, replacement = path.read_text(encoding="utf-8"), sys.argv[2], sys.argv[3]
if source.count(anchor) != 1:
    raise SystemExit(f"plant anchor count is {source.count(anchor)}, want 1")
changed = source.replace(anchor, replacement, 1)
if hashlib.sha256(changed.encode()).digest() == hashlib.sha256(source.encode()).digest():
    raise SystemExit("plant did not change bytes")
path.write_text(changed, encoding="utf-8")
PY
  _plant_rc=$?
  if [ "$_plant_rc" -ne 0 ]; then
    echo "control FATAL: $_id plant could not be installed" >&2
    exit 64
  fi
  run_contract_test "planted-$_id" "$WT/$_test"
  _rc=$?
  git -C "$WT" restore -- "$_target" || exit 64
  case "$_rc" in
    0)
      _caught=false
      RED=1
      echo "control RED: planted $_id remained green" >&2
      ;;
    2) _caught=true ;;
    64)
      echo "control FATAL: planted $_id hit an environmental/tool failure" >&2
      exit 64
      ;;
  esac
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$_id" "$_axis" "$_target" "$_rc" "$_caught" >>"$RUNDIR/plants.txt"
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

# Each non-portable surface gets an unmodified positive control and a planted
# defect in the detached worktree. Portable packet coverage already has four
# behavior-derived ablations above.
PORTABLE_STATUS=$([ "$RED" -eq 0 ] && echo passed || echo failed)
axis_positive verifier_negative_control verifier-unplanted "$WT/$F/selftest.sh"
axis_positive relocation relocation-unplanted "$WT/$F/portability.sh"
axis_positive trusted_local local-unplanted "$WT/tests/test_ctg_local_build.sh"
axis_positive mcp_inline_carrier mcp-unplanted "$WT/tests/test_ctg_mcp_carrier.sh"

plant_and_require_red verifier-missing-human-gate verifier_negative_control \
  "$F/src/code_truth_graph/verify_artifacts.py" \
  '    "human_gate",' '' "$F/selftest.sh"
plant_and_require_red relocation-root-coupling relocation \
  "$F/run.sh" \
  'HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64' \
  "HERE='$WT/$F'" "$F/portability.sh"
plant_and_require_red local-receipt-open-schema trusted_local \
  "$F/schemas/ctg-local-build-receipt.schema.json" \
  '"required": ["schema_version", "runner", "subject", "artifacts", "overall", "claim_boundary"],' \
  '"required": ["schema_version", "runner", "subject", "artifacts", "overall"],' \
  tests/test_ctg_local_build.sh
plant_and_require_red mcp-local-artifact-list-leak mcp_inline_carrier \
  loopctl/mcp_server.py \
  '    payload["artifacts"] = []
    payload["stdout"] = "[CTG MCP streams redacted; typed artifacts delivered inline]"' \
  '    payload["artifacts"] = payload.get("artifacts", [])
    payload["stdout"] = "[CTG MCP streams redacted; typed artifacts delivered inline]"' \
  tests/test_ctg_mcp_carrier.sh

RECEIPT="$ROOT/data/proof-workflow/control-ctg-$SHORT.json"
CONTROL_RECEIPT="$RECEIPT" CONTROL_COMMIT="$CAPTURE_COMMIT" CONTROL_RUN_ID="$RUN_ID" \
  CONTROL_ENTRY_RC="$BASE_RC" CONTROL_PROJECTION="$BASE_PROJECTION" CONTROL_PROOF_DIGEST="$PROOF_DIGEST" \
  CONTROL_CLASSES="$RUNDIR/input-class.txt" CONTROL_PRODUCED="$RUNDIR/produced-paths.txt" CONTROL_RUNS="$RUNDIR/run.jsonl" \
  CONTROL_AXES="$RUNDIR/axis-positive.txt" CONTROL_PLANTS="$RUNDIR/plants.txt" \
  CONTROL_PORTABLE_STATUS="$PORTABLE_STATUS" \
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
axes = {}
for line in lines("CONTROL_AXES"):
    axis, exit_code = line.split("\t")
    axes[axis] = "EXERCISED_PASS" if int(exit_code) == 0 else "EXERCISED_FAIL"
plants = []
for line in lines("CONTROL_PLANTS"):
    plant_id, axis, target, exit_code, caught = line.split("\t")
    plants.append({
        "id": plant_id,
        "axis": axis,
        "target": target,
        "byte_guard": True,
        "exit": int(exit_code),
        "caught": caught == "true",
    })
portable = "EXERCISED_PASS" if os.environ["CONTROL_PORTABLE_STATUS"] == "passed" else "EXERCISED_FAIL"
all_offline = portable == "EXERCISED_PASS" and all(
    value == "EXERCISED_PASS" for value in axes.values()
) and all(item["caught"] for item in plants)
receipt = {
    "schema_version": "bettor-arena-ctg-control@2.0.0",
    "commit": os.environ["CONTROL_COMMIT"],
    "run_id": os.environ["CONTROL_RUN_ID"],
    "status": os.environ["CONTROL_STATUS"],
    "baseline": {"exit": int(os.environ["CONTROL_ENTRY_RC"]), "canonical_projection": os.environ["CONTROL_PROJECTION"], "repeat_count": 3},
    "input_classifications": classes,
    "produced_artifacts": lines("CONTROL_PRODUCED"),
    "proof_digest": os.environ["CONTROL_PROOF_DIGEST"],
    "planted_defects": plants,
    "assurance": {
        "portable_packet": portable,
        **axes,
        "live_prod_device": "NOT_EXERCISED_REQUIRES_EXTERNAL_ENVIRONMENT",
        "human_admit": "NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN",
        "maximum_claim": "offline_multi_surface_implemented" if all_offline else "no_positive_claim",
    },
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
    "claim_boundary": "portable packet, verifier, relocation, trusted-local and MCP inline surfaces at this commit; no live PROD/device side effect and no Human admit",
}
Path(os.environ["CONTROL_RECEIPT"]).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
PY
python3 "$HELPER" control-check --receipt "$RECEIPT" >/dev/null || exit 64

if [ "$RED" -ne 0 ]; then
  echo "control FAIL: at least one CTG assurance axis or planted defect is red; receipt=$RECEIPT" >&2
  exit 2
fi
echo "control PASS: five offline surfaces exercised, four planted defects caught, proof linked; receipt=$RECEIPT"
exit 0
