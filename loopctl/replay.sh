#!/bin/sh
# replay.sh — run the workflow as it was at a commit or a tag.
#
#   loopctl.sh workflow replay --at <commit|tag> [--loop macro|micro|openwiki]
#
# That ref is checked out into a disposable detached worktree and THAT version's
# loopctl runs there, so what executes is the workflow as it was rather than
# today's workflow wearing an old commit's name. Today's tree is never touched.
#
# Two questions, answered separately because they fail for different reasons:
#
#   VERIFY  is the workflow's committed content still what that commit recorded?
#           Every tracked file in that ref's workflow.lock is re-hashed straight
#           out of git and compared. Fully deterministic — no run required.
#   RUN     does that version still execute? That ref's own `loopctl <loop> run`
#           is invoked for real in the worktree, and its exit code is reported.
#
# The proof digest is deliberately NOT the verdict. Proofs hash runtime evidence
# — a post-commit receipt for the current HEAD, a route-result, an exchange
# context — and none of that exists in a fresh checkout of an old commit. A
# comparison that can only pass in the tree where the run happened is not a
# replay; the first version of this file demanded exactly that and failed on its
# first real use, which is how the untracked half of the manifest was found.
#
# Exit: 0 both questions answered green · 2 tracked content drifted, or the run
# failed · 64 FATAL (ref does not resolve, no worktree, no lock at that ref).
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel) || { echo "replay FATAL: not a work tree" >&2; exit 64; }

REF=""
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --at)   REF=${2:-}; shift 2 ;;
    --loop) ONLY=${2:-}; shift 2 ;;
    *) echo "replay FATAL: unknown flag $1" >&2; exit 64 ;;
  esac
done
[ -n "$REF" ] || { echo "replay FATAL: --at <commit|tag> is required" >&2; exit 64; }

RESOLVED=$(python3 "$HERE/lineage.py" resolve "$ROOT" "$REF") || exit 64
COMMIT=$(printf '%s' "$RESOLVED" | python3 -c 'import json,sys; print(json.load(sys.stdin)["commit"])')
TAGS=$(printf '%s' "$RESOLVED" | python3 -c 'import json,sys; print(" ".join(json.load(sys.stdin)["tags"]))')
echo "replay: ref=$REF commit=$COMMIT${TAGS:+ tags=$TAGS}"

# --- VERIFY: the workflow's committed content, straight out of git -----------
# `git cat-file` rather than a checkout: the question is what the commit carries,
# and reading it from a working tree would let a local edit answer for it.
VERIFY=$(python3 - "$ROOT" "$COMMIT" <<'PY'
import hashlib, json, subprocess, sys

root, commit = sys.argv[1], sys.argv[2]


def show(path):
    p = subprocess.run(["git", "-C", root, "show", f"{commit}:{path}"],
                       capture_output=True, check=False)
    return p.stdout if p.returncode == 0 else None


raw = show("loopctl/workflow.lock")
if raw is None:
    print("FATAL no workflow.lock at that ref — nothing records what its workflow was")
    raise SystemExit(0)
lock = json.loads(raw)
drifted, absent, checked = [], [], 0
for path, meta in lock["files"].items():
    blob = show(path)
    if blob is None:
        # Untracked at that ref: runtime evidence, which a commit never carries.
        absent.append(path)
        continue
    checked += 1
    if hashlib.sha256(blob).hexdigest() != meta["sha256"]:
        drifted.append(path)
print(json.dumps({"checked": checked, "untracked": len(absent), "drifted": drifted,
                  "workflow_commit": lock["workflow_commit"],
                  "tags": lock.get("workflow_tags", [])}))
PY
) || exit 64
case "$VERIFY" in
  "FATAL "*) echo "replay FATAL: ${VERIFY#FATAL }" >&2; exit 64 ;;
esac
DRIFTED=$(printf '%s' "$VERIFY" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("\n".join(d["drifted"]))')
printf '%s' "$VERIFY" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ok = d['checked'] - len(d['drifted'])
print(f\"  [verify] {ok}/{d['checked']} tracked workflow file(s) match the lock; \"
      f\"{d['untracked']} runtime path(s) a commit never carries were skipped by name\")
"
RC=0
if [ -n "$DRIFTED" ]; then
  echo "  [verify] DRIFTED:" >&2
  printf '%s\n' "$DRIFTED" | sed 's/^/    /' >&2
  RC=2
fi

# --- RUN: that version's own CLI, in a disposable worktree -------------------
BASE=$(mktemp -d "${TMPDIR:-/tmp}/loopctl-replay.XXXXXX")
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" "$COMMIT" >/dev/null 2>&1 \
  || { echo "replay FATAL: could not check out $COMMIT into a worktree" >&2; exit 64; }
[ -f "$WT/loopctl/loopctl.sh" ] || {
  echo "replay FATAL: $COMMIT predates loopctl/ — there is no CLI at that ref to replay" >&2
  exit 64; }
# The factory's dependencies are gitignored, so no historical checkout carries
# them. Borrowing today's is bounded and stated: whether a clean install suffices
# is portability.sh's claim, and reinstalling per replay would cost minutes.
FACTORY=loop_wiki/evolve-perfect-seed-repo-factory
[ -d "$ROOT/$FACTORY/node_modules" ] && [ ! -e "$WT/$FACTORY/node_modules" ] \
  && ln -s "$ROOT/$FACTORY/node_modules" "$WT/$FACTORY/node_modules"

run_loop() { # loop, extra args
  _loop=$1; shift
  OUT=$( (cd "$WT" && sh loopctl/loopctl.sh "$_loop" run "$@") 2>&1 )
  _rc=$?
  if [ "$_rc" -eq 0 ]; then
    echo "  [run] $_loop executed at that ref — exit 0"
  else
    echo "  [run] $_loop FAILED at that ref — exit $_rc" >&2
    printf '%s\n' "$OUT" | tail -4 >&2
    RC=2
  fi
}

for LOOP in macro micro openwiki; do
  [ -z "$ONLY" ] || [ "$ONLY" = "$LOOP" ] || continue
  case "$LOOP" in
    macro) run_loop macro ;;
    micro) run_loop micro --packet "$WT/$FACTORY/packets/inbox/dr-example.json" --output "$BASE/seed" ;;
    openwiki)
      # The worker's input is the micro loop's output, so a replay of this loop
      # only means anything after that one has run in the same worktree.
      REQ=$(ls "$WT"/data/wiki-update/request-*.json 2>/dev/null | sort | tail -1)
      if [ -z "$REQ" ]; then
        echo "  [run] openwiki skipped: no request in this worktree — replay micro first (its output is this loop's input)"
      else
        run_loop openwiki --request "$REQ" --force-receipt
      fi ;;
  esac
done

if [ "$RC" -eq 0 ]; then
  echo "PASS: the workflow at ${TAGS:-$COMMIT} still carries what it recorded and still executes"
else
  echo "FAIL: replay of ${TAGS:-$COMMIT} did not hold" >&2
fi
exit "$RC"
