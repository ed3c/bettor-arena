#!/bin/sh
# control_openwiki_entry.sh — the CONTROL GROUP for the openwiki lane's entry point.
#
# prove_openwiki.sh runs the worker's --selftest and one --dry-run against a
# request that already sat in the ledger. This is the independent arrival: it
# manufactures the request the way the system really does — by running the micro
# loop's trigger.sh first — and then feeds THAT to the worker. The hand-off
# between the two loops is therefore executed, not assumed; no proof covers it
# today, because each proof stops at its own edge.
#
# Everything happens inside a disposable detached worktree at HEAD. The request
# and the route-result it points at are both gitignored, so a fresh checkout has
# neither, and copying them in would prove the worker can read files I placed
# rather than files the micro loop produced.
#
# WHAT THIS CONTROL DOES NOT COVER, stated rather than implied: the run is
# --dry-run, so the probabilistic segment — the claude -p turn that regenerates
# the wiki, and the finder/verifier subagent turns — is skipped by name. That is
# not a shortcut around cost; the probe experiment below classifies inputs by
# comparing exit codes across runs, and a segment whose output varies per run
# makes every such comparison meaningless. The receipt records the boundary and
# whether any full-mode receipt exists anywhere to cover it.
#
# Usage: sh proof_workflow/control_openwiki_entry.sh
# Exit:  0 covered · 2 gap, or the entry point itself failed · 64 FATAL
set -u

CAPTURE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$CAPTURE_HOME/lib/capture.sh"
capture_init openwiki-entry
ROOT=$CAPTURE_ROOT
SHORT=$CAPTURE_SHORT

FACTORY_REL=loop_wiki/evolve-perfect-seed-repo-factory
PACKET_REL=$FACTORY_REL/packets/inbox/dr-example.json
WORKER_REL=kb-ingest/port/wiki_update_worker.sh

BASE=$(mktemp -d "${TMPDIR:-/tmp}/control-openwiki.XXXXXX")
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1 || {
  echo "control FATAL: could not create the run worktree — a real run would have to touch the live wiki" >&2
  exit 64; }
ln -s "$ROOT/$FACTORY_REL/node_modules" "$WT/$FACTORY_REL/node_modules"

( cd "$WT" && find . -type f -not -path './.git/*' -not -path "./$FACTORY_REL/node_modules/*" ) \
  | sed 's|^\./||' | sort >"$RUNDIR/tree-before.txt"

# --- upstream: manufacture the request the way the system really does --------
CAPTURE_CWD="$WT"
capture upstream-trigger -- sh "$WT/$FACTORY_REL/trigger.sh" "$WT/$PACKET_REL" "$BASE/out"
TRIGGER_RC=$?
CAPTURE_CWD=""
[ "$TRIGGER_RC" -eq 0 ] || {
  echo "control FATAL: the upstream trigger.sh run failed (exit $TRIGGER_RC) — there is no genuine request to feed the worker" >&2
  exit 64; }
REQUEST=$(ls "$WT"/data/wiki-update/request-*.json 2>/dev/null | sort | tail -1)
[ -n "$REQUEST" ] || { echo "control FATAL: trigger.sh left no wiki-update request" >&2; exit 64; }
echo "  [chain] micro loop produced $(basename "$REQUEST") — feeding it to the worker"

# --- the real run (deterministic chain; model turn skipped by name) ----------
OUTN=0
worker_run() { # id
  OUTN=$((OUTN + 1))
  CAPTURE_CWD="$WT"
  capture "$1" -- env WIKI_UPDATE_FORCE_RECEIPT=1 sh "$WT/$WORKER_REL" "$REQUEST" --dry-run
  _wrc=$?
  CAPTURE_CWD=""
  return "$_wrc"
}

worker_run worker
WORKER_RC=$?
worker_run worker-repeat
REPEAT_RC=$?
[ "$REPEAT_RC" -eq "$WORKER_RC" ] || {
  echo "control FATAL: baseline is not reproducible (exit $WORKER_RC then $REPEAT_RC) — no probe result would mean anything" >&2
  exit 64; }

( cd "$WT" && find . -type f -not -path './.git/*' -not -path "./$FACTORY_REL/node_modules/*" ) \
  | sed 's|^\./||' | sort >"$RUNDIR/tree-after.txt"
comm -13 "$RUNDIR/tree-before.txt" "$RUNDIR/tree-after.txt" >"$RUNDIR/produced-paths.txt"

# --- what it consumes: static literals PLUS the runtime pointers -------------
# Half this entry point's inputs are named by the REQUEST, not by the script:
# fixed_prompt_context and route_result.path are resolved at run time. A static
# scan alone would miss the official prompt assets entirely — the whole
# probabilistic side of the lane — and report a comfortable, wrong answer.
{
  grep -o '\$root/[A-Za-z0-9._/-]*' "$ROOT/$WORKER_REL" | sed 's|\$root/||'
  grep -o '\$HERE/[A-Za-z0-9._/-]*' "$ROOT/$WORKER_REL" | sed 's|\$HERE/|kb-ingest/port/|'
  python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); [print(p) for p in r["fixed_prompt_context"]]; print(r["route_result"]["path"])' "$REQUEST"
} | sort -u >"$RUNDIR/named-paths.txt"

: >"$RUNDIR/input-paths.txt"
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  grep -Fxq "$rel" "$RUNDIR/produced-paths.txt" && continue
  [ -e "$WT/$rel" ] && printf '%s\n' "$rel" >>"$RUNDIR/input-paths.txt"
done <"$RUNDIR/named-paths.txt"

# --- required or optional, decided by exit code ------------------------------
: >"$RUNDIR/input-class.txt"
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  AWAY="$BASE/$(printf '%s' "$rel" | tr '/' '_').away"
  mv "$WT/$rel" "$AWAY" 2>/dev/null || continue
  worker_run "probe-without-$(printf '%s' "$rel" | tr '/.' '--')"
  RC=$?
  mv "$AWAY" "$WT/$rel"
  if [ "$RC" -ne "$WORKER_RC" ]; then CLASS=required; else CLASS=optional; fi
  printf '%s\t%s\t%s\n' "$rel" "$CLASS" "$RC" >>"$RUNDIR/input-class.txt"
  echo "  [probe] $rel -> $CLASS (worker exit $RC vs baseline $WORKER_RC)"
done <"$RUNDIR/input-paths.txt"

worker_run worker-after-probes
AFTER_RC=$?
[ "$AFTER_RC" -eq "$WORKER_RC" ] || {
  echo "control FATAL: the tree no longer reproduces the baseline after probing (exit $AFTER_RC vs $WORKER_RC) — a probe left damage and the classifications above are unsound" >&2
  exit 64; }

# The named absence: has the probabilistic segment ever been exercised anywhere?
grep -l '"mode": *"full"' "$ROOT"/data/wiki-update/receipt-*.json 2>/dev/null \
  | sed "s|$ROOT/||" | sort >"$RUNDIR/full-mode-receipts.txt" || true

# --- opt-in: exercise the probabilistic segment once, as an existence proof ---
# CONTROL_OPENWIKI_FULL=1 runs the worker in full mode inside the same worktree.
# It runs AFTER every probe and after the damage check, and its output is never
# read back into the classification: a segment whose result varies per run cannot
# take part in an exit-code comparison, which is exactly why the probes are
# dry-run. The only claim this run makes is that the path executes end to end.
#
# That claim is checked on the worker's own stage line, not on its exit code. A
# red verifier gate exits 2 while having genuinely spent a model turn, so exit
# alone cannot distinguish "the segment ran and found problems" from "the segment
# never ran". Absence of the [regenerate] line means it never ran, and with the
# flag set that is a failure of the thing that was asked for.
: >"$RUNDIR/full-run.txt"
if [ "${CONTROL_OPENWIKI_FULL:-0}" = "1" ]; then
  command -v claude >/dev/null 2>&1 || {
    echo "control FATAL: CONTROL_OPENWIKI_FULL=1 but the claude CLI is not on PATH — the segment cannot be exercised, and skipping it silently is what the flag exists to stop" >&2
    exit 64; }
  echo "  [full] exercising the probabilistic segment — real model turns, worktree only"
  CAPTURE_CWD="$WT"
  capture worker-full -- env WIKI_UPDATE_FORCE_RECEIPT=1 sh "$WT/$WORKER_REL" "$REQUEST"
  FULL_RC=$?
  CAPTURE_CWD=""
  FULL_LOG="$RUNDIR/streams/$CAPTURE_SEQ-worker-full.out"
  if grep -q '^\[regenerate\] model=' "$FULL_LOG" 2>/dev/null; then
    FULL_EXERCISED=true
  else
    FULL_EXERCISED=false
  fi
  # Which stage it reached last, from the worker's own progress lines.
  FULL_STAGE=$(grep -oE '^\[(parse|preflight|regenerate|gates|post|backlog)\]' "$FULL_LOG" 2>/dev/null | tail -1 | tr -d '[]')
  {
    printf 'exercised=%s\n' "$FULL_EXERCISED"
    printf 'worker_exit=%s\n' "$FULL_RC"
    printf 'last_stage=%s\n' "${FULL_STAGE:-none}"
    printf 'regenerate_line=%s\n' "$(grep -m1 '^\[regenerate\] model=' "$FULL_LOG" 2>/dev/null || echo none)"
  } >"$RUNDIR/full-run.txt"
  echo "  [full] exercised=$FULL_EXERCISED worker_exit=$FULL_RC last_stage=${FULL_STAGE:-none}"
  [ "$FULL_EXERCISED" = true ] || {
    echo "control FATAL: full mode was requested but the model turn never happened (last stage: ${FULL_STAGE:-none}) — see $FULL_LOG" >&2
    exit 64; }
fi

RECEIPT_SRC="$ROOT/data/proof-workflow/openwiki-$SHORT.json"
[ -f "$RECEIPT_SRC" ] || RECEIPT_SRC="$ROOT/data/proof-workflow/openwiki-$SHORT-dirty.json"
[ -f "$RECEIPT_SRC" ] || {
  echo "control FATAL: no openwiki receipt at this commit ($SHORT), clean or dirty — run prove_openwiki.sh first" >&2
  exit 64; }

CONTROL_MODE=openwiki \
CONTROL_RUN_ID="$RUN_ID" CONTROL_RUNDIR="$RUNDIR" CONTROL_COMMIT="$CAPTURE_COMMIT" \
CONTROL_ENTRY_RC="$WORKER_RC" CONTROL_RECEIPT="$ROOT/data/proof-workflow/control-openwiki-$SHORT.json" \
CONTROL_MACRO_RECEIPT="$RECEIPT_SRC" \
python3 "$CAPTURE_HOME/lib/compare_control.py"
exit $?
