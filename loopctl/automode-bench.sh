#!/bin/sh
# automode-bench.sh — does auto-permission actually cost more tokens?
#
#   sh loopctl/automode-bench.sh --dry-run
#   sh loopctl/automode-bench.sh [--runs N] [--arm off|on|both]
#   sh loopctl/automode-bench.sh --selftest
#
# A PAIRED experiment, not a demonstration. Two sandboxes run the SAME task on
# the SAME tree and differ in exactly one variable — whether the guard is on:
#
#   off   claude --dangerously-skip-permissions, no .claudeignore.
#         Nothing is refused, so a greedy read is free.
#   on    a narrow --allowedTools plus a .claudeignore over the repo's real
#         token bombs. Broad shell search is not available at all.
#
# The claim under test comes from a document, and a document is one solution, not
# a measurement. It predicts blowup by import cascade, whole-suite test logs, and
# giant `find`/`grep` payloads. If that does not reproduce here, the honest
# result is "it did not reproduce here", and the numbers below are what says so.
#
# WHY THE TASK HAS A CHECKABLE ANSWER: an arm that is refused everything spends
# fewer tokens by failing, and scoring that as a win would make the whole
# comparison a lie. Every run is graded before it is counted, and a wrong run is
# reported separately rather than averaged in.
#
# Exit: 0 both arms produced counted runs · 2 an arm produced none · 64 FATAL
set -u

RUNS=3
ARM=both
DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --runs) shift; RUNS=${1:-3} ;;
    --arm) shift; ARM=${1:-both} ;;
    --dry-run) DRY=1 ;;
    --selftest) SELFTEST=1 ;;
    -h|--help) sed -n '2,12p' "$0" >&2; exit 64 ;;
    *) echo "unknown flag: $1" >&2; exit 64 ;;
  esac
  shift
done

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FATAL: not inside a git work tree" >&2; exit 64; }

# The task walks several proof scripts to find one declared exclusion, so a
# greedy strategy has somewhere to be greedy. The answer is one path, which makes
# grading a string match rather than a judgement.
TASK='Exactly one file in this repository is deliberately excluded from every proof receipt, because hashing it would make its own digest depend on itself. Answer with ONLY that file'"'"'s repo-relative path, nothing else.'
EXPECT='loopctl/workflow.lock'

# .claudeignore for the ON arm. Taken from the reference document and then
# CORRECTED: its template blocks `*.lock`, which here would hide
# loopctl/workflow.lock and loopctl/surface.lock — a manifest and a surface
# contract, neither of them a dependency lockfile, and both among the files an
# agent most needs. A blanket rule copied from a document that never saw this
# tree would blind the agent to the very thing the task asks about.
IGNORE='# dependency lockfiles, named rather than globbed (see automode-bench.sh)
bun.lock
uv.lock
package-lock.json
yarn.lock
pnpm-lock.yaml
Cargo.lock
poetry.lock
# generated corpora and receipts: high token count, low semantic value per byte
data/receipts/molecular-corpus-parity.json
*.min.js
*.min.css
*.map
coverage/
htmlcov/
*.log
*.snap
node_modules/
vendor/
.venv/
__pycache__/
dist/
build/
*.png
*.jpg
*.pdf
*.zip
'

if [ "${SELFTEST:-0}" = 1 ]; then
  RED=0
  say() { if [ "$2" = "$3" ]; then echo "  [ok]   $1"; else echo "  [RED]  $1 — got $2, want $3" >&2; RED=1; fi; }
  # The grader is the part that can silently invert the result, so it is the part
  # with a test: a refused arm that answers nothing must not grade as correct.
  grade() { printf '%s' "$1" | grep -Fq "$EXPECT" && echo correct || echo wrong; }
  say "exact-answer-grades-correct" "$(grade 'loopctl/workflow.lock')" correct
  say "answer-in-a-sentence-grades-correct" "$(grade 'It is loopctl/workflow.lock, because of the cycle.')" correct
  say "empty-answer-grades-wrong" "$(grade '')" wrong
  say "plausible-but-wrong-answer-grades-wrong" "$(grade 'loopctl/surface.lock')" wrong
  say "refusal-grades-wrong" "$(grade 'I was not permitted to read the repository.')" wrong
  # The corrected ignore list must not hide the two files this repo depends on.
  printf '%s' "$IGNORE" | grep -qx 'workflow.lock' && { echo "  [RED]  ignore-list-does-not-blind-the-manifest" >&2; RED=1; } || echo "  [ok]   ignore-list-does-not-blind-the-manifest"
  printf '%s' "$IGNORE" | grep -qx '\*.lock' && { echo "  [RED]  ignore-list-has-no-blanket-lock-glob" >&2; RED=1; } || echo "  [ok]   ignore-list-has-no-blanket-lock-glob"
  [ "$RED" -eq 0 ] && { echo "SELFTEST GREEN"; exit 0; }
  echo "SELFTEST RED" >&2; exit 2
fi

command -v openshell >/dev/null 2>&1 || { echo "FATAL: openshell is not on PATH" >&2; exit 64; }
openshell provider list 2>/dev/null | grep -q "^claude-code " || {
  echo "FATAL: no 'claude-code' provider on this gateway — the sandbox would have no credential." >&2
  echo "       openshell provider create --name claude-code --type generic --credential CLAUDE_CODE_OAUTH_TOKEN" >&2
  exit 64; }
if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"; export DOCKER_HOST
  echo "DOCKER_HOST -> orbstack socket"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$ROOT/data/automode-bench/$STAMP"
WORK="/sandbox/$(basename "$ROOT")"

if [ "$DRY" -eq 1 ]; then
  cat <<EOF
dry-run — preconditions ran, nothing was created
  arms      $ARM   runs per arm: $RUNS
  task      "$(printf '%s' "$TASK" | cut -c1-64)..."
  graded on the answer containing: $EXPECT
  off       claude --dangerously-skip-permissions, no .claudeignore
  on        claude --allowedTools Read,Glob,Grep + .claudeignore ($(printf '%s' "$IGNORE" | grep -cv '^#') patterns)
  results   -> $OUT
EOF
  exit 0
fi

mkdir -p "$OUT"

run_arm() { # <arm>
  arm=$1
  name="automode-$arm-$STAMP"
  case "$arm" in
    off) flags='--dangerously-skip-permissions'; write_ignore=0 ;;
    on)  flags='--allowedTools Read,Glob,Grep'; write_ignore=1 ;;
    *) echo "FATAL: unknown arm $arm" >&2; exit 64 ;;
  esac

  # Everything the arm differs by is assembled HERE, in one place, so a reader can
  # see the single variable rather than diffing two long command lines.
  inner='
set -u
cd '"$WORK"' || exit 64
'
  # base64, because the gateway refuses an --env value containing a newline
  # ("spec.environment value ... contains newline or carriage return
  # characters") — and it refused for BOTH arms on the first attempt, since the
  # variable was passed unconditionally and killed the arm that never reads it.
  ENV_ARGS=""
  if [ "$write_ignore" -eq 1 ]; then
    IGNORE_B64=$(printf '%s' "$IGNORE" | base64 | tr -d '\n')
    ENV_ARGS="--env BENCH_IGNORE_B64=$IGNORE_B64"
    inner="$inner"'
printf "%s" "$BENCH_IGNORE_B64" | base64 -d >.claudeignore
'
  fi
  inner="$inner"'
i=1
while [ "$i" -le '"$RUNS"' ]; do
  claude -p "$BENCH_TASK" --output-format json '"$flags"' >"/sandbox/run-$i.json" 2>"/sandbox/run-$i.err" || true
  echo "run $i done"
  i=$((i + 1))
done
tar cf /sandbox/bench.tar -C /sandbox $(cd /sandbox && ls run-*.json run-*.err 2>/dev/null)
'
  echo "=== arm $arm: $RUNS run(s) in $name"
  openshell sandbox delete "$name" >/dev/null 2>&1
  openshell sandbox create --name "$name" --no-tty \
    --policy "$ROOT/loopctl/sandbox-policy.yaml" \
    --provider claude-code \
    --env "BENCH_TASK=$TASK" \
    $ENV_ARGS \
    --from "$ROOT/loopctl/Dockerfile" --upload "$ROOT" \
    -- sh -c "$inner"
  mkdir -p "$OUT/$arm"
  openshell sandbox download "$name" /sandbox/bench.tar "$OUT/$arm" >/dev/null 2>&1 &&
    ( cd "$OUT/$arm" && tar xf bench.tar && rm -f bench.tar ) ||
    echo "  WARNING: nothing came back from arm $arm"
  openshell sandbox delete "$name" >/dev/null 2>&1
}

case "$ARM" in
  both) run_arm off; run_arm on ;;
  off|on) run_arm "$ARM" ;;
  *) echo "FATAL: --arm must be off, on or both" >&2; exit 64 ;;
esac

python3 "$ROOT/loopctl/automode_report.py" "$OUT" "$EXPECT"
