#!/bin/sh
# control_workflow_lineage.sh — the CONTROL GROUP for the lineage machinery itself.
#
#   sh loopctl/loopctl.sh workflow test
#
# The other controls ask whether each loop's proof covers what its entry point
# really touches. This one asks the question one level up: does the machinery
# that senses a moved workflow actually sense it, and does replay actually
# execute the version a commit or a tag names?
#
# Every check is a PLANTED DEFECT, because a mechanism only ever seen agreeing is
# not known to be able to disagree. A file in the manifest is really modified and
# really staged; the trailer must name it, with the right kind. The lock is left
# describing older bytes; the gate must refuse the commit. A file OUTSIDE the
# manifest is staged; the trailer must stay silent, or every commit in the repo
# would carry a lineage stamp and the signal would mean nothing.
#
# All of it happens inside a disposable detached worktree at HEAD. The live tree
# is never staged, never committed to, and never left with a modified index —
# which also makes this safe to run while someone else is editing, and that is
# not hypothetical: the staleness gate first fired here because a file changed
# between a proof and its commit.
#
# Exit: 0 every planted defect was caught and every honest case passed
#       2 the machinery missed something it must catch
#       64 FATAL (no worktree, no lock at HEAD to test against)
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init workflow-lineage
ROOT=$CAPTURE_ROOT

BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-lineage.XXXXXX")
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1 || {
  echo "control FATAL: could not create the worktree — the planted defects would have to go in the live tree" >&2
  exit 64; }
git -C "$WT" config user.email control@local
git -C "$WT" config user.name control
[ -f "$WT/loopctl/workflow.lock" ] || {
  echo "control FATAL: no workflow.lock at HEAD — there is no manifest to test the machinery against" >&2
  exit 64; }

RED=0
expect() { # name got want
  if [ "$2" = "$3" ]; then
    echo "  [ok]   $1 — $2"
  else
    echo "  [RED]  $1 — got $2, want $3" >&2
    RED=1
  fi
}

# Pick a real harness file out of the manifest rather than naming one here: a
# hardcoded path would keep testing a file the workflow may have dropped.
VICTIM=$(python3 -c '
import json, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
for path, meta in sorted(lock["files"].items()):
    if meta["kind"] == "harness" and path.endswith(".sh"):
        print(path); break
' "$WT/loopctl/workflow.lock")
[ -n "$VICTIM" ] || { echo "control FATAL: the manifest lists no harness script to plant into" >&2; exit 64; }
echo "control[workflow-lineage] planting into $VICTIM"

# --- 1. a modified workflow file must be sensed, with its kind ---------------
printf '\n# control-group planted line\n' >>"$WT/$VICTIM"
git -C "$WT" add "$VICTIM"
CAPTURE_CWD="$WT"
capture trailer-after-plant -- python3 "$WT/loopctl/lineage.py" trailer "$WT" "$WT/loopctl/workflow.lock"
CAPTURE_CWD=""
TRAILER_OUT="$RUNDIR/streams/$CAPTURE_SEQ-trailer-after-plant.out"
grep -q "^Workflow-Lineage: " "$TRAILER_OUT" && SENSED=yes || SENSED=no
expect "modified-workflow-file-is-sensed" "$SENSED" yes
grep -q "^Workflow-Touched: harness:.*:$VICTIM$" "$TRAILER_OUT" && KINDED=yes || KINDED=no
expect "touched-line-carries-kind-and-path" "$KINDED" yes

# --- 2. the stale lock must refuse the commit -------------------------------
# The plant changed the file but not the lock, which is exactly the shape that
# shipped a stale lock inside the commit that invalidated it.
printf 'subject\n\nWorkflow-Lineage: %s\n' "$(git -C "$WT" rev-parse HEAD)" >"$BASE/msg"
CAPTURE_CWD="$WT"
capture check-stale-lock -- python3 "$WT/loopctl/lineage.py" check "$WT" "$WT/loopctl/workflow.lock" "$BASE/msg"
STALE_RC=$?
CAPTURE_CWD=""
expect "stale-lock-refuses-the-commit" "$STALE_RC" 2

# --- 3. an unstamped commit must be refused too ------------------------------
# Re-lock first, so this case is testing the missing trailer and not the staleness
# from case 2 — one variable at a time, or the second check proves nothing.
CAPTURE_CWD="$WT"
capture relock-in-worktree -- sh -c "cd '$WT' && for l in macro micro openwiki; do sh loopctl/loopctl.sh \$l prove --force-receipt >/dev/null 2>&1; done; sh loopctl/loopctl.sh workflow lock"
CAPTURE_CWD=""
git -C "$WT" add loopctl/workflow.lock 2>/dev/null || true
printf 'subject with no trailer\n' >"$BASE/bare.msg"
CAPTURE_CWD="$WT"
capture check-unstamped -- python3 "$WT/loopctl/lineage.py" check "$WT" "$WT/loopctl/workflow.lock" "$BASE/bare.msg"
BARE_RC=$?
CAPTURE_CWD=""
expect "unstamped-commit-is-refused" "$BARE_RC" 2

# --- 4. the honest case must pass, or the gate is just noise -----------------
printf 'subject\n\nWorkflow-Lineage: %s\n' "$(git -C "$WT" rev-parse HEAD)" >"$BASE/good.msg"
CAPTURE_CWD="$WT"
capture check-stamped -- python3 "$WT/loopctl/lineage.py" check "$WT" "$WT/loopctl/workflow.lock" "$BASE/good.msg"
GOOD_RC=$?
CAPTURE_CWD=""
expect "stamped-and-fresh-commit-passes" "$GOOD_RC" 0

# --- 5. a file outside the manifest must stay silent -------------------------
# Without this the trailer would appear on every commit in the repo, and a stamp
# that is always there says nothing about the commits that matter.
git -C "$WT" reset -q
printf 'not part of the workflow\n' >"$WT/control-outsider.txt"
git -C "$WT" add control-outsider.txt
CAPTURE_CWD="$WT"
capture trailer-for-outsider -- python3 "$WT/loopctl/lineage.py" trailer "$WT" "$WT/loopctl/workflow.lock"
CAPTURE_CWD=""
OUTSIDER="$RUNDIR/streams/$CAPTURE_SEQ-trailer-for-outsider.out"
[ -s "$OUTSIDER" ] && QUIET=no || QUIET=yes
expect "non-workflow-file-emits-no-trailer" "$QUIET" yes

# --- 6. replay must resolve a tag and execute that version -------------------
TAG=$(git -C "$ROOT" tag --list 'v*' | sort -V | tail -1)
if [ -n "$TAG" ]; then
  CAPTURE_CWD="$ROOT"
  capture replay-at-tag -- sh "$ROOT/loopctl/replay.sh" --at "$TAG" --loop macro
  REPLAY_RC=$?
  CAPTURE_CWD=""
  REPLAY_OUT="$RUNDIR/streams/$CAPTURE_SEQ-replay-at-tag.out"
  grep -q "^  \[run\] macro executed at that ref" "$REPLAY_OUT" && RAN=yes || RAN=no
  expect "replay-executes-the-tagged-version" "$RAN" yes
  echo "  [note] replay --at $TAG exit=$REPLAY_RC (verify drift is reported separately, not swallowed)"
else
  echo "  [note] no v* tag in this repo yet — the tag path of replay is NOT covered by this run"
fi

echo "control[workflow-lineage] trace=proof_workflow/data/$RUN_ID"
if [ "$RED" -eq 0 ]; then
  echo "PASS: the lineage machinery caught every planted defect and passed every honest case"
  exit 0
fi
echo "FAIL: the lineage machinery missed something it must catch — fix it before trusting a stamp" >&2
exit 2
