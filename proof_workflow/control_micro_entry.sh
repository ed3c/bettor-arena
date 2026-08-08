#!/bin/sh
# control_micro_entry.sh — the CONTROL GROUP for the micro loop's entry point.
#
# prove_micro_loop.sh hashes trigger.sh and records it hashed-not-run, for a
# good reason: trigger.sh writes a route-result and a wiki-update request into
# ledgers the proof is supposed to be judging, and a proof that rewrites its own
# evidence is not a proof. But "we never run it" leaves the largest question in
# the micro loop unanswered — what does the entry point ACTUALLY do — and a step
# list cannot catch what it forgot to list.
#
# This is that second, independent arrival. It runs trigger.sh for real inside a
# disposable detached worktree at HEAD, so the run is genuine while the real
# ledgers are never touched. node_modules is symlinked in rather than installed:
# whether a clean install suffices is portability.sh's claim, not this one, and
# borrowing it keeps a control run at seconds instead of minutes.
#
# Three facts are derived from the run itself rather than from reading the
# script, because reading is how you learn what someone MEANT:
#   produced paths  everything that appeared in the worktree after the run —
#                   the entry point's real output set
#   input paths     the repo paths it names minus the ones it produced
#   required/optional  each input removed in turn and trigger.sh re-run: the
#                   exit code decides, not `fatal` vs `warn` in the source
#
# The verdict compares those against the union of the proof receipts at this
# commit. A produced path or a required input that no proof covers is a gap in
# the proof, reported by name.
#
# Usage: sh proof_workflow/control_micro_entry.sh
# Exit:  0 covered · 2 gap, or the entry point itself failed · 64 FATAL
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init micro-entry
ROOT=$CAPTURE_ROOT
SHORT=$CAPTURE_SHORT

FACTORY_REL=loop_wiki/evolve-perfect-seed-repo-factory
PACKET_REL=$FACTORY_REL/packets/inbox/dr-example.json

# --- disposable worktree at HEAD --------------------------------------------
BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-micro.XXXXXX")
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1 || {
  echo "control FATAL: could not create the run worktree — a real run would have to touch the real ledgers" >&2
  exit 64; }
ln -s "$ROOT/$FACTORY_REL/node_modules" "$WT/$FACTORY_REL/node_modules"

# Everything present before the run, so "produced" is measured, not assumed.
( cd "$WT" && find . -type f -not -path './.git/*' -not -path "./$FACTORY_REL/node_modules/*" ) \
  | sed 's|^\./||' | sort >"$RUNDIR/tree-before.txt"

# --- the real run ------------------------------------------------------------
# Every run gets its own output directory. cli.ts:23 refuses an output path that
# already exists, so reusing one makes every run after the first fail at step one
# — and a probe that fails for that reason classifies whatever it removed as
# load-bearing, which is a confound that looks exactly like a finding. (It did:
# the first version of this script called all seven inputs required, at the same
# exit code, because of precisely this.)
OUTN=0
trigger_run() { # id
  OUTN=$((OUTN + 1))
  CAPTURE_CWD="$WT"
  capture "$1" -- sh "$WT/$FACTORY_REL/trigger.sh" "$WT/$PACKET_REL" "$BASE/out-$OUTN"
  _trc=$?
  CAPTURE_CWD=""
  return "$_trc"
}

trigger_run trigger
TRIGGER_RC=$?
# Reproducibility control: the same tree twice must give the same verdict, or
# every classification below is measuring noise rather than the removed file.
trigger_run trigger-repeat
REPEAT_RC=$?
[ "$REPEAT_RC" -eq "$TRIGGER_RC" ] || {
  echo "control FATAL: baseline is not reproducible (exit $TRIGGER_RC then $REPEAT_RC) — no probe result would mean anything" >&2
  exit 64; }

( cd "$WT" && find . -type f -not -path './.git/*' -not -path "./$FACTORY_REL/node_modules/*" ) \
  | sed 's|^\./||' | sort >"$RUNDIR/tree-after.txt"
comm -13 "$RUNDIR/tree-before.txt" "$RUNDIR/tree-after.txt" >"$RUNDIR/produced-paths.txt"

# --- what it names, minus what it produced, is what it consumes --------------
# $ROOT inside trigger.sh is the factory dir and $ARENA is the repo root, so the
# two prefixes resolve to different repo-relative homes; collapsing them would
# invent paths that do not exist.
{
  grep -o '\$ROOT/[A-Za-z0-9._/-]*' "$ROOT/$FACTORY_REL/trigger.sh" | sed "s|\$ROOT/|$FACTORY_REL/|"
  grep -o '\$ARENA/[A-Za-z0-9._/-]*' "$ROOT/$FACTORY_REL/trigger.sh" | sed 's|\$ARENA/||'
} | sort -u >"$RUNDIR/named-paths.txt"
# A named path that exists at HEAD and was not produced by the run is an input.
: >"$RUNDIR/input-paths.txt"
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  grep -Fxq "$rel" "$RUNDIR/produced-paths.txt" && continue
  [ -e "$ROOT/$rel" ] && printf '%s\n' "$rel" >>"$RUNDIR/input-paths.txt"
done <"$RUNDIR/named-paths.txt"

# --- required or optional: one variable at a time, decided by exit code ------
: >"$RUNDIR/input-class.txt"
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  AWAY="$BASE/$(printf '%s' "$rel" | tr '/' '_').away"
  mv "$WT/$rel" "$AWAY" 2>/dev/null || continue
  trigger_run "probe-without-$(printf '%s' "$rel" | tr '/.' '--')"
  RC=$?
  mv "$AWAY" "$WT/$rel"
  if [ "$RC" -ne "$TRIGGER_RC" ]; then CLASS=required; else CLASS=optional; fi
  printf '%s\t%s\t%s\n' "$rel" "$CLASS" "$RC" >>"$RUNDIR/input-class.txt"
  echo "  [probe] $rel -> $CLASS (trigger exit $RC vs baseline $TRIGGER_RC)"
done <"$RUNDIR/input-paths.txt"

# Damage control: after every removal has been restored, the tree must still
# behave like the baseline. If it does not, some probe left wreckage behind and
# the later classifications were reading that instead of the removed file.
trigger_run trigger-after-probes
AFTER_RC=$?
[ "$AFTER_RC" -eq "$TRIGGER_RC" ] || {
  echo "control FATAL: the tree no longer reproduces the baseline after probing (exit $AFTER_RC vs $TRIGGER_RC) — a probe left damage and the classifications above are unsound" >&2
  exit 64; }

# --- compare against the proof receipts at this commit -----------------------
MICRO_RECEIPT="$ROOT/data/proof-workflow/micro-$SHORT.json"
[ -f "$MICRO_RECEIPT" ] || MICRO_RECEIPT="$ROOT/data/proof-workflow/micro-$SHORT-dirty.json"
[ -f "$MICRO_RECEIPT" ] || {
  echo "control FATAL: no micro receipt at this commit ($SHORT), clean or dirty — run prove_micro_loop.sh first" >&2
  exit 64; }

CONTROL_MODE=micro \
CONTROL_RUN_ID="$RUN_ID" CONTROL_RUNDIR="$RUNDIR" CONTROL_COMMIT="$CAPTURE_COMMIT" \
CONTROL_ENTRY_RC="$TRIGGER_RC" CONTROL_RECEIPT="$ROOT/data/proof-workflow/control-micro-$SHORT.json" \
CONTROL_MACRO_RECEIPT="$MICRO_RECEIPT" \
python3 "$CAPTURE_HOME/lib/compare_control.py"
exit $?
