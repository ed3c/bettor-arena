#!/bin/sh
# replay.sh — run the workflow as it was at a commit or a tag.
#
#   loopctl.sh workflow replay --at <commit|tag> [--loop macro|micro|openwiki]
#
# The point is not "run today's scripts against an old tree". It checks that ref
# out into a disposable detached worktree and runs THAT version's loopctl and
# THAT version's proofs, so what executes is the workflow as it was, not today's
# workflow wearing an old commit's name. Today's code touches nothing but the
# comparison at the end.
#
# The verdict is the digest. A traversal at a given commit produced a specific
# proof_digest, recorded in that commit's receipt; replaying it must reproduce
# the same number. Equal means the workflow at that ref still executes to the same
# bytes. Different means something it depends on has moved out from under it —
# which is a real answer, not a failure of the replay, so it is reported as a
# comparison rather than swallowed as an error.
#
# A tag is resolved through git, so `--at v1.0` and `--at <that commit>` are the
# same run; the tag is recorded alongside so the receipt says which name was used.
#
# Exit: 0 replayed and every digest matched · 2 a digest differs, or a proof
# failed at that ref · 64 FATAL (ref does not resolve, no worktree, no receipt
# to compare against).
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
SHORT=$(printf %.12s "$COMMIT")
echo "replay: ref=$REF commit=$COMMIT${TAGS:+ tags=$TAGS}"

BASE=$(mktemp -d "${TMPDIR:-/tmp}/loopctl-replay.XXXXXX")
WT="$BASE/repo"
cleanup() { git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; }
trap cleanup EXIT
git -C "$ROOT" worktree add --detach "$WT" "$COMMIT" >/dev/null 2>&1 \
  || { echo "replay FATAL: could not check out $COMMIT into a worktree" >&2; exit 64; }

# The factory's dependencies are gitignored, so no historical checkout carries
# them. Borrowing today's is deliberate and bounded: whether a clean install
# suffices is portability.sh's claim, and re-installing per replay would make a
# replay cost minutes instead of seconds.
FACTORY=loop_wiki/evolve-perfect-seed-repo-factory
[ -d "$ROOT/$FACTORY/node_modules" ] && [ ! -e "$WT/$FACTORY/node_modules" ] \
  && ln -s "$ROOT/$FACTORY/node_modules" "$WT/$FACTORY/node_modules"

[ -f "$WT/loopctl/loopctl.sh" ] || {
  echo "replay FATAL: $COMMIT predates loopctl/ — there is no CLI at that ref to replay" >&2
  exit 64; }

RC=0
for LOOP in macro micro openwiki; do
  [ -z "$ONLY" ] || [ "$ONLY" = "$LOOP" ] || continue
  RECORDED=$(python3 - "$ROOT" "$LOOP" "$SHORT" <<'PY'
import json, sys
from pathlib import Path
root, loop, short = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
for name in (f"{loop}-{short}.json", f"{loop}-{short}-dirty.json"):
    path = root / "data" / "proof-workflow" / name
    if path.is_file():
        print(json.loads(path.read_text(encoding="utf-8"))["molecular_hardening"]["proof_digest"])
        break
PY
)
  if [ -z "$RECORDED" ]; then
    echo "  [$LOOP] no receipt at $SHORT to compare against — replay would prove nothing" >&2
    RC=64
    continue
  fi
  # That ref's own CLI, that ref's own proof. --force-receipt because the replay
  # writes into the disposable worktree's ledger, never this one's.
  OUT=$( (cd "$WT" && sh loopctl/loopctl.sh "$LOOP" prove --force-receipt) 2>&1 )
  PROVE_RC=$?
  NOW=$(printf '%s' "$OUT" | sed -n 's/.*digest=\([0-9a-f]\{64\}\).*/\1/p' | head -1)
  if [ "$PROVE_RC" -ne 0 ]; then
    echo "  [$LOOP] the proof failed at that ref (exit $PROVE_RC)" >&2
    printf '%s\n' "$OUT" | tail -5 >&2
    RC=2
  elif [ "$NOW" = "$RECORDED" ]; then
    echo "  [$LOOP] digest matches: $(printf %.12s "$NOW")"
  else
    echo "  [$LOOP] DIGEST MOVED: recorded $(printf %.12s "$RECORDED") -> replayed $(printf %.12s "${NOW:-none}")" >&2
    RC=2
  fi
done

if [ "$RC" -eq 0 ]; then
  echo "PASS: the workflow at ${TAGS:-$SHORT} still executes to the digests it recorded"
else
  echo "FAIL: replay of ${TAGS:-$SHORT} did not reproduce what was recorded" >&2
fi
exit "$RC"
