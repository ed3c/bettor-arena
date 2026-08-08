#!/bin/sh
# control_macro_entry.sh — the CONTROL GROUP for the macro loop's entry point.
#
# prove_macro_loop.sh records a traversal I authored: it says which paths the
# macro loop runs through. That is a claim. This script is the independent
# arrival against it — it actually RUNS the entry point (`sh bootstrap.sh`),
# keeps the physical trace of that run on disk, derives from the trace and from
# the entry point's own source what it really touches, and then compares that
# against what the macro proof covers. Two arrivals that cannot be fooled by the
# same mistake: one is my step list, the other is the program's own behaviour.
#
# Physical evidence, not inference. Every captured command lands in
#   proof_workflow/data/<run_id>/
#     run.jsonl              one JSON record per executed command: argv, cwd,
#                            exit code, utc, stream paths, stream sha256, bytes
#     streams/<seq>-<id>.out real stdout bytes
#     streams/<seq>-<id>.err real stderr bytes
# run_id = <utc>-<commit12>. The directory is gitignored: gate output embeds
# this machine's absolute repo root, and committing it would either trip the
# root-coupling gate (§3 鐵律 2) or grow the evidence allowlist by one standing
# debt per run. Instead the committed receipt carries every stream's sha256, so
# the on-disk trace is content-addressed by something that IS in git — alter a
# captured byte and it stops matching the commit that vouched for it.
#
# Usage: sh proof_workflow/control_macro_entry.sh
# Exit:  0 the macro proof covers everything the real run touches
#        2 coverage gap (named, never silent) or bootstrap itself failed
#        64 FATAL (no macro receipt at this commit to compare against, etc.)
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel) || {
  echo "control FATAL: not inside a git work tree" >&2; exit 64; }
COMMIT=$(git -C "$ROOT" rev-parse HEAD)
SHORT=$(printf %.12s "$COMMIT")
UTC=$(date -u +%Y%m%dT%H%M%SZ)
RUN_ID="$UTC-$SHORT"
RUNDIR="$ROOT/proof_workflow/data/$RUN_ID"
mkdir -p "$RUNDIR/streams"

sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}
esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

SEQ=0
# capture <id> -- cmd... : run it for real, keep both streams, record the fact.
capture() {
  _id=$1; shift
  [ "${1:-}" = "--" ] && shift
  SEQ=$((SEQ + 1))
  _out="$RUNDIR/streams/$SEQ-$_id.out"
  _err="$RUNDIR/streams/$SEQ-$_id.err"
  _argv=""
  for _a in "$@"; do _argv="$_argv\"$(esc "$_a")\","; done
  _started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  ( cd "$ROOT" && "$@" ) >"$_out" 2>"$_err"
  _rc=$?
  printf '{"seq":%d,"id":"%s","utc":"%s","cwd":"repo-root","argv":[%s],"exit":%d,"stdout":{"path":"streams/%s","sha256":"%s","bytes":%s},"stderr":{"path":"streams/%s","sha256":"%s","bytes":%s}}\n' \
    "$SEQ" "$_id" "$_started" "${_argv%,}" "$_rc" \
    "$(basename "$_out")" "$(sha256 "$_out")" "$(wc -c <"$_out" | tr -d ' ')" \
    "$(basename "$_err")" "$(sha256 "$_err")" "$(wc -c <"$_err" | tr -d ' ')" \
    >>"$RUNDIR/run.jsonl"
  echo "  [ran] $_id — exit $_rc"
  return "$_rc"
}

echo "control[macro-entry] run_id=$RUN_ID commit=$COMMIT"

# --- the real run, plus the state it is supposed to move ---------------------
capture hookspath-before -- git config core.hooksPath
capture bootstrap -- sh bootstrap.sh
BOOTSTRAP_RC=$?
capture hookspath-after -- git config core.hooksPath
# Tool identities: bootstrap's doctor gates on these, so which build answered is
# part of what this run means. Recorded, never asserted against a pinned version.
capture tool-git -- git --version
capture tool-python3 -- python3 -VV
capture tool-bun -- bun --version

# --- derive what the entry point really touches ------------------------------
# From its own source, not from memory: every repo path literal it names, and
# every external command it gates on.
grep -o '\$ROOT/[A-Za-z0-9._/-]*' "$ROOT/bootstrap.sh" | sed 's|\$ROOT/||' | sort -u >"$RUNDIR/named-paths.txt"
grep -o 'command -v [a-z0-9]*' "$ROOT/bootstrap.sh" | awk '{print $3}' | sort -u >"$RUNDIR/tools-named.txt"

# --- required or optional? make the program answer, do not read it -----------
# Whether a path is load-bearing is exactly the kind of thing that looks obvious
# in the source and is wrong: `fatal` and `warn` sit three lines apart in the
# same file. So this is a one-variable experiment instead — remove the path in a
# throwaway worktree at HEAD, run bootstrap, and let its exit code classify it.
# The worktree is disposable and detached; the real tree is never touched. Every
# probe's streams and exit land in run.jsonl next to the primary run, so the
# classification is physical evidence, not a reading of the script.
WT=$(mktemp -d "${TMPDIR:-/tmp}/control-macro-wt.XXXXXX")
rmdir "$WT"
if git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1; then
  : >"$RUNDIR/path-class.txt"
  capture probe-baseline-worktree -- sh -c "cd '$WT' && sh bootstrap.sh"
  BASELINE_RC=$?
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    AWAY="$WT/../$(basename "$rel").away.$$"
    if [ -e "$WT/$rel" ]; then
      mv "$WT/$rel" "$AWAY"
    else
      # Already absent at HEAD (a gitignored host asset). Its absence is the
      # experiment; nothing to move, and that is itself the finding.
      AWAY=""
    fi
    capture "probe-without-$(printf '%s' "$rel" | tr '/.' '--')" -- sh -c "cd '$WT' && sh bootstrap.sh"
    RC=$?
    [ -n "$AWAY" ] && mv "$AWAY" "$WT/$rel"
    if [ "$RC" -ne "$BASELINE_RC" ]; then CLASS=required; else CLASS=optional; fi
    printf '%s\t%s\t%s\n' "$rel" "$CLASS" "$RC" >>"$RUNDIR/path-class.txt"
    echo "  [probe] $rel -> $CLASS (bootstrap exit $RC vs baseline $BASELINE_RC)"
  done <"$RUNDIR/named-paths.txt"
  git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1
else
  echo "control FATAL: could not create the probe worktree — classification would be a guess" >&2
  exit 64
fi
# From the run itself: which of its message lanes actually fired this time.
cat "$RUNDIR/streams/2-bootstrap.out" "$RUNDIR/streams/2-bootstrap.err" 2>/dev/null \
  | grep -E '^bootstrap (OK|ok|WARN|FATAL)' | sort >"$RUNDIR/fired-lanes.txt" || true

# --- compare against the macro proof's own receipt ---------------------------
# The receipt, not the script: comparing against prove_macro_loop.sh's source
# would re-parse my claim, whereas the receipt is what that claim actually
# produced. If it is missing at this commit there is nothing to compare and
# that is FATAL, never an empty green.
# A clean stamp is preferred but a dirty one is still a real traversal of this
# commit's step list; refusing it would force a commit before the control could
# ever run on new work. Which one was used rides on the receipt, because a
# comparison against a dirty stamp is a weaker basis and must not read as a
# clean one.
MACRO_RECEIPT="$ROOT/data/proof-workflow/macro-$SHORT.json"
if [ ! -f "$MACRO_RECEIPT" ]; then
  MACRO_RECEIPT="$ROOT/data/proof-workflow/macro-$SHORT-dirty.json"
fi
[ -f "$MACRO_RECEIPT" ] || {
  echo "control FATAL: no macro receipt at this commit ($SHORT), clean or dirty — run prove_macro_loop.sh first" >&2
  exit 64; }

RECEIPT="$ROOT/data/proof-workflow/control-macro-$SHORT.json"
CONTROL_RUN_ID="$RUN_ID" CONTROL_RUNDIR="$RUNDIR" CONTROL_COMMIT="$COMMIT" \
CONTROL_BOOTSTRAP_RC="$BOOTSTRAP_RC" CONTROL_RECEIPT="$RECEIPT" \
CONTROL_MACRO_RECEIPT="$MACRO_RECEIPT" \
python3 "$HERE/lib/compare_control.py"
exit $?
