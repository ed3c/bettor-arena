#!/bin/sh
# control_equivalence_entry.sh — independent control group for technical equivalence.
#
# The proof is a handwritten traversal claim.  This script instead checks the
# committed mechanism in a disposable worktree, removes core inputs one at a
# time, plants three load-bearing defects, and derives the complete canonical
# inventory from Git.  Its verdict therefore does not reuse the proof's step list
# or the live working tree.
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init equivalence-entry
ROOT=$CAPTURE_ROOT
SHORT=$CAPTURE_SHORT

PROOF="$ROOT/data/proof-workflow/equivalence-$SHORT.json"
[ -f "$PROOF" ] || {
  echo "control FATAL: no clean equivalence proof at current HEAD $SHORT; commit first, then run equivalence prove" >&2
  exit 64
}
CONTROL_RECEIPT="$ROOT/data/proof-workflow/control-equivalence-$SHORT.json"
if [ -e "$CONTROL_RECEIPT" ] && [ "${CONTROL_EQUIVALENCE_FORCE_RECEIPT:-0}" != "1" ]; then
  echo "control FATAL: receipt already exists: ${CONTROL_RECEIPT#"$ROOT"/}; rerun through loopctl with --force-receipt to overwrite explicitly" >&2
  exit 64
fi

BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-equivalence.XXXXXX")
WT="$BASE/repo"
PROOF_SNAPSHOT="$BASE/${PROOF##*/}"
cp "$PROOF" "$PROOF_SNAPSHOT" || {
  echo "control FATAL: could not snapshot the equivalence proof before the long-running control" >&2
  exit 64
}
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1 || {
  echo "control FATAL: could not create disposable worktree" >&2
  exit 64
}

LOOP="$WT/loop_wiki/evolve-technical-equivalence-research"
PY3=$(command -v python3) || { echo "control FATAL: python3 absent" >&2; exit 64; }
SOURCE_PEER=${ANTIGRAVITY_PEER:-$ROOT/../antigravity}
TARGET_PEER=${SKILL_BETTOR_PEER:-$ROOT/../skill-bettor}
RED=0
expect() {
  if [ "$2" = "$3" ]; then echo "  [ok]   $1 — $2"
  else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi
}

require_contract_exit() {
  case "$2" in
    0|2|64) return 0 ;;
    *) echo "control FATAL: $1 returned undeclared exit $2 (want 0, 2, or 64)" >&2; return 64 ;;
  esac
}

run_offline() {
  _id=$1
  _receipt=$2
  CAPTURE_CWD="$WT"
  capture "$_id" -- env \
    ANTIGRAVITY_PEER="$SOURCE_PEER" \
    SKILL_BETTOR_PEER="$TARGET_PEER" \
    EQUIVALENCE_RECEIPT_PATH="$_receipt" \
    EQUIVALENCE_FORCE_RECEIPT=1 \
    sh "$LOOP/selftest.sh"
  _rc=$?
  CAPTURE_CWD=""
  return "$_rc"
}

# Positive control: the committed, unmodified offline mechanism must pass.
run_offline offline-unplanted "$BASE/offline-receipt.json"
OFFLINE_RC=$?
require_contract_exit "unplanted offline entry" "$OFFLINE_RC" || exit $?
expect "unplanted-offline-surface-is-green" "$OFFLINE_RC" 0
[ "$OFFLINE_RC" -ne 64 ] || {
  echo "control FATAL: unplanted offline entry returned 64" >&2
  exit 64
}

# The selftest receipt must keep all authority edges distinct.
CAPTURE_CWD="$WT"
capture offline-assurance-shape -- "$PY3" - "$BASE/offline-receipt.json" <<'PY'
import json, sys
try:
    r = json.load(open(sys.argv[1], encoding="utf-8"))
    a = r["assurance"]
    assert a["offline_surface"] == "EXERCISED_PASS"
    assert a["live_carrier"] == "NOT_EXERCISED"
    assert a["fresh_semantic_judge"] == "NOT_EXERCISED_REQUIRES_TWO_BLINDED_BATCHES"
    assert a["human_admit"] == "NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN"
    assert a["maximum_claim"] == "offline_surface_implemented"
except AssertionError:
    raise SystemExit(2)
PY
ASSURANCE_RC=$?
CAPTURE_CWD=""
require_contract_exit "offline assurance check" "$ASSURANCE_RC" || exit $?
[ "$ASSURANCE_RC" -ne 64 ] || exit 64
expect "offline-green-does-not-promote-authority" "$ASSURANCE_RC" 0

# Remove each load-bearing input in isolation and let the entry point classify it.
: >"$RUNDIR/path-class.txt"
for rel in \
  loop_wiki/evolve-technical-equivalence-research/equivalence.py \
  loop_wiki/evolve-technical-equivalence-research/drift.py \
  loop_wiki/evolve-technical-equivalence-research/profile/technical-equivalence.md \
  loop_wiki/evolve-technical-equivalence-research/adapter-registry.json \
  loop_wiki/evolve-technical-equivalence-research/schemas
do
  away="$BASE/away-$(printf '%s' "$rel" | tr '/.' '--')"
  mv "$WT/$rel" "$away"
  run_offline "without-$(printf '%s' "$rel" | tr '/.' '--')" "$BASE/without-receipt.json"
  rc=$?
  mv "$away" "$WT/$rel"
  require_contract_exit "$rel ablation" "$rc" || exit $?
  case "$rc" in
    0) class=optional ;;
    2) class=required ;;
    64) echo "control FATAL: $rel ablation returned 64" >&2; exit 64 ;;
  esac
  printf '%s\t%s\t%s\n' "$rel" "$class" "$rc" >>"$RUNDIR/path-class.txt"
  expect "$rel-is-required" "$class" required
done

plant_and_require_red() {
  _id=$1; _anchor=$2; _replacement=$3
  _path="$LOOP/equivalence.py"
  "$PY3" - "$_path" "$_anchor" "$_replacement" <<'PY'
import hashlib, pathlib, sys
p = pathlib.Path(sys.argv[1])
src, anchor, replacement = p.read_text(encoding="utf-8"), sys.argv[2], sys.argv[3]
if src.count(anchor) != 1:
    raise SystemExit(f"plant anchor count is {src.count(anchor)}, want 1")
changed = src.replace(anchor, replacement, 1)
if hashlib.sha256(changed.encode()).digest() == hashlib.sha256(src.encode()).digest():
    raise SystemExit("plant did not change bytes")
p.write_text(changed, encoding="utf-8")
PY
  _plant_rc=$?
  if [ "$_plant_rc" -ne 0 ]; then
    echo "control FATAL: $_id plant could not be installed" >&2
    return 64
  fi
  run_offline "planted-$_id" "$BASE/planted-receipt.json"
  _rc=$?
  git -C "$WT" restore -- loop_wiki/evolve-technical-equivalence-research/equivalence.py
  require_contract_exit "planted $_id run" "$_rc" || return $?
  if [ "$_rc" -eq 64 ]; then
    echo "control FATAL: planted $_id run returned 64" >&2
    return 64
  elif [ "$_rc" -eq 2 ]; then expect "planted-$_id-goes-red" red red
  else expect "planted-$_id-goes-red" green red; fi
}

plant_and_require_red request-digest \
  '    if request["request_digest"] != expected:' \
  '    if False:' || exit $?
plant_and_require_red judge-authority \
  '    if (
        execution.get("judge_packet_digest") != judge_packet_digest' \
  '    if False and (
        execution.get("judge_packet_digest") != judge_packet_digest' || exit $?
plant_and_require_red committed-source-binding \
  '    if result.returncode != 0 or result.stdout != current_bytes:' \
  '    if False:' || exit $?

LIVE_STATE=NOT_EXERCISED
if [ "${CONTROL_EQUIVALENCE_LIVE:-0}" = "1" ]; then
  # This path is stable for one mechanism commit. A failed provider edge leaves
  # an immutable adapter receipt here, so the next explicit live run can reuse
  # successful digest-bound invocations instead of spending the primary turn
  # again. HEAD is part of the path, so changed mechanism bytes never inherit it.
  LIVE_RUN_ROOT=${EQUIVALENCE_CONTROL_LIVE_RUN_ROOT:-$ROOT/proof_workflow/data/equivalence-live-$SHORT}
  CAPTURE_CWD="$WT"
  capture live-carrier -- env \
    ANTIGRAVITY_PEER="$SOURCE_PEER" \
    SKILL_BETTOR_PEER="$TARGET_PEER" \
    EQUIVALENCE_LIVE=1 \
    EQUIVALENCE_LIVE_RUN_ROOT="$LIVE_RUN_ROOT" \
    EQUIVALENCE_RECEIPT_PATH="$LIVE_RUN_ROOT/selftest-receipt.json" \
    EQUIVALENCE_FORCE_RECEIPT=1 \
    sh "$LOOP/selftest.sh"
  LIVE_RC=$?
  CAPTURE_CWD=""
  require_contract_exit "live carrier" "$LIVE_RC" || exit $?
  if [ "$LIVE_RC" -eq 0 ]; then LIVE_STATE=CARRIER_EXERCISED_PASS
  elif [ "$LIVE_RC" -eq 64 ]; then
    echo "control FATAL: live carrier returned 64" >&2
    exit 64
  else LIVE_STATE=CARRIER_EXERCISED_FAIL; RED=1; fi
else
  echo "  [note] live carrier NOT EXERCISED — pass --live to spend the Gemini turn"
  echo "         fresh judge and Human admit remain separate regardless of this arm"
fi

CONTROL_RC=$OFFLINE_RC
[ "$RED" -eq 0 ] || CONTROL_RC=2
"$PY3" "$ROOT/proof_workflow/lib/equivalence_control.py" \
  "$ROOT" "$RUNDIR" "$PROOF_SNAPSHOT" "$CONTROL_RECEIPT" "$OFFLINE_RC" "$CONTROL_RC" "$LIVE_STATE"
COMPARE_RC=$?
echo "control[equivalence-entry] trace=proof_workflow/data/$RUN_ID"
exit "$COMPARE_RC"
