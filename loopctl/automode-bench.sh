#!/bin/sh
# automode-bench.sh — does auto-permission actually cost more tokens?
#
#   sh loopctl/automode-bench.sh --dry-run
#   sh loopctl/automode-bench.sh [--platform claude|codex] [--runs N] [--arm off|on|both]
#   sh loopctl/automode-bench.sh --selftest
#
# A PAIRED experiment, not a demonstration. Two sandboxes run the SAME task on
# the SAME tree and differ in exactly one variable — whether the guard is on:
#
#   claude off   --dangerously-skip-permissions, no .claudeignore.
#                Nothing is refused, so a greedy read is free.
#   claude on    a narrow --allowedTools plus a .claudeignore over the repo's
#                real token bombs. Broad shell search is not available at all.
#
#   codex  off   --dangerously-bypass-approvals-and-sandbox, default limits.
#   codex  on    -a never with tool_output_token_limit, under --strict-config.
#
# WHAT THE CODEX PAIR DOES NOT VARY, and it is not a choice: codex confines its
# own shell commands with bubblewrap, which cannot create a user namespace inside
# this container. Measured, all four cells, one run each: `-s read-only` and
# `-s workspace-write` both die on `bwrap: No permissions to create a new
# namespace`, while `-s danger-full-access` and the bypass flag execute. So the
# sandbox axis is PINNED at full access in both arms and only the approval and
# output-limit axes move. Running the living cells and calling it a 2x2 would
# report a comparison that never happened.
#
# --strict-config is load-bearing on the guarded arm. Without it a misspelled
# config key is silently ignored, the guard quietly becomes a no-op, and the
# experiment compares an arm against itself while every number looks fine.
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
PLATFORM=claude
VENUE=sandbox
while [ $# -gt 0 ]; do
  case "$1" in
    --runs) shift; RUNS=${1:-3} ;;
    --arm) shift; ARM=${1:-both} ;;
    --platform) shift; PLATFORM=${1:-claude} ;;
    --venue) shift; VENUE=${1:-sandbox} ;;
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

# Codex arm flags. Named up here because the selftest asserts properties of them
# and must see the same strings the real run uses, not a copy that can drift.
#   off  full auto, default limits
#   on   approvals off (exec cannot answer a prompt anyway) plus the only output
#        lever this version actually has, validated so a typo cannot disarm it
# Approval is a CONFIG key, not a flag. The first version passed `-a never`,
# taken from `always|never|auto` sitting next to --json in the help output —
# which belongs to `--color`. codex exec rejected it outright and the whole
# guarded arm produced three empty runs. Reading the neighbourhood of a grep hit
# is not reading the interface.
# Claude arm flags, named for the same reason the codex ones are: the selftest
# asserts a relationship BETWEEN them, and a copy it could not see would drift.
#
# The relationship is the whole design. `reduce` must carry the SAME flags as
# `off`, because its entire claim is that the cached prefix is untouched and only
# the ignore file differs. Add one flag to `reduce` and it becomes another `on` —
# a different tool surface, a rewritten cache — while the table still says
# "reduce", which is precisely the shape that would publish a false result.
CLAUDE_OFF_FLAGS='--dangerously-skip-permissions'
CLAUDE_REDUCE_FLAGS='--dangerously-skip-permissions'
CLAUDE_ON_FLAGS='--allowedTools Read,Glob,Grep'

CODEX_OFF_FLAGS='--dangerously-bypass-approvals-and-sandbox'
CODEX_ON_FLAGS='-s danger-full-access --strict-config -c approval_policy=never -c tool_output_token_limit=512'
# The lever alone, appended to the OFF flags so the rest of the invocation is
# untouched. Kept as its own string because the selftest asserts on it.
CODEX_REDUCE_ONLY='--strict-config -c tool_output_token_limit=512'

# Where each CLI actually looks for skills inside a sandbox, read out of the
# shipped binaries rather than assumed (`.claude/skills` with a CLAUDE_SKILL_DIR
# override; `.codex/skills`). HOME in the sandbox is /sandbox. One function so
# the selftest can call the same code the run uses — a second copy in the test
# would pass against a broken implementation.
skills_target() { # <platform> -> path, or exit 1 for an unknown platform
  case "$1" in
    claude) echo /sandbox/.claude/skills ;;
    codex)  echo /sandbox/.codex/skills ;;
    *) return 1 ;;
  esac
}

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
  # A guard that is silently ignored turns the guarded arm into a second copy of
  # the unguarded one, and every number still looks reasonable. The only thing
  # standing between that and a published false result is --strict-config, so
  # its presence on the codex guarded arm is asserted rather than trusted.
  case "$CODEX_ON_FLAGS" in
    *--strict-config*) echo "  [ok]   codex-guarded-arm-validates-its-config" ;;
    *) echo "  [RED]  codex-guarded-arm-validates-its-config — without --strict-config a misspelled key makes the guard a no-op and the arms identical" >&2; RED=1 ;;
  esac
  case "$CODEX_ON_FLAGS" in
    *tool_output_token_limit*) echo "  [ok]   codex-guard-uses-a-key-this-version-has" ;;
    *) echo "  [RED]  codex-guard-uses-a-key-this-version-has — the reference document's max_stdout_lines/max_stdout_bytes do not exist in codex 0.147" >&2; RED=1 ;;
  esac
  # The reduce arm's entire claim is "same prefix as off, one ignore file more".
  # Asserted, because the day someone adds a flag here the arm silently becomes a
  # second `on` — different tool surface, rewritten cache — while the report still
  # labels it `reduce` and the conclusion inverts with nothing going red.
  say "reduce-keeps-the-baseline-prefix" "$CLAUDE_REDUCE_FLAGS" "$CLAUDE_OFF_FLAGS"
  case "$CLAUDE_ON_FLAGS" in
    "$CLAUDE_OFF_FLAGS") echo "  [RED]  on-really-does-move-the-prefix — if it matched off, the expensive arm and the baseline would be the same run and the 22% finding would be noise" >&2; RED=1 ;;
    *) echo "  [ok]   on-really-does-move-the-prefix" ;;
  esac
  # Same shape on the codex side: reduce is off PLUS the lever, nothing else.
  case "$CODEX_REDUCE_ONLY" in
    *approval_policy*|*danger-full-access*) echo "  [RED]  codex-reduce-changes-only-the-output-lever — it moved an axis other than output, so it is not comparable to off" >&2; RED=1 ;;
    *tool_output_token_limit*) echo "  [ok]   codex-reduce-changes-only-the-output-lever" ;;
    *) echo "  [RED]  codex-reduce-changes-only-the-output-lever — the lever is missing entirely" >&2; RED=1 ;;
  esac
  # A bundle uploaded where the CLI does not look is indistinguishable from no
  # bundle at all — same numbers, same silence — so both targets are asserted by
  # calling the REAL resolver. The first version of these two cases re-derived
  # the literal inside the test, which is a tautology: it would have passed
  # against any implementation, including a broken one.
  say "claude-skills-target-is-the-surface-claude-reads" "$(skills_target claude)" /sandbox/.claude/skills
  say "codex-skills-target-is-the-surface-codex-reads" "$(skills_target codex)" /sandbox/.codex/skills
  skills_target nonsense >/dev/null 2>&1
  say "unknown-platform-has-no-target" $? 1
  [ "$RED" -eq 0 ] && { echo "SELFTEST GREEN"; exit 0; }
  echo "SELFTEST RED" >&2; exit 2
fi

# Only the sandbox venue needs the gateway. Requiring it for `direct` would turn
# a machine that can perfectly well run the measurement into a FATAL about a
# component the run never touches.
if [ "$VENUE" = sandbox ]; then
  command -v openshell >/dev/null 2>&1 || { echo "FATAL: openshell is not on PATH (needed by --venue sandbox; --venue direct does not use it)" >&2; exit 64; }
fi
case "$VENUE" in sandbox|direct) ;; *) echo "FATAL: --venue must be sandbox or direct" >&2; exit 64 ;; esac
CODEX_AUTH=""
# Credentials are a SANDBOX concern only. Run directly, both CLIs use the host's
# own session — which is also the honest difference between the two venues, and
# the reason the direct numbers are not interchangeable with the sandbox ones.
case "$VENUE:$PLATFORM" in
  direct:*)
    command -v "$PLATFORM" >/dev/null 2>&1 || {
      echo "FATAL: $PLATFORM is not on PATH — the direct venue runs the host's own CLI" >&2; exit 64; }
    ;;
  sandbox:claude)
    # Three outcomes, not two. `... 2>/dev/null | grep -q` folded "the gateway
    # could not be reached" into "the provider is not there", and it said so out
    # loud: with the socket unreachable this printed a confident instruction to
    # create a provider that already existed. Asking and being told no is a
    # different repair from not being able to ask.
    PROVIDERS=$(openshell provider list 2>&1); PROVIDERS_RC=$?
    if [ "$PROVIDERS_RC" -ne 0 ]; then
      echo "FATAL: could not ask the gateway which providers exist (exit $PROVIDERS_RC) — this is NOT 'the provider is missing', and creating one would be the wrong repair. First line of its complaint:" >&2
      printf '%s\n' "$PROVIDERS" | head -1 >&2
      exit 64
    fi
    printf '%s\n' "$PROVIDERS" | grep -q "^claude-code " || {
      echo "FATAL: the gateway answered, and it has no 'claude-code' provider — the sandbox would have no credential." >&2
      echo "       openshell provider create --name claude-code --type generic --credential CLAUDE_CODE_OAUTH_TOKEN" >&2
      exit 64; }
    ;;
  sandbox:codex)
    # codex cannot use the provider placeholder — it parses its credential as a
    # JWT before any request — so the session goes in as a real value. Same trade
    # as codex-sandbox.sh, and the same reason it is stated rather than buried.
    CODEX_AUTH=$(python3 - "${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
except OSError:
    sys.exit("FATAL: no codex session at %s — run `codex login` on the host first" % sys.argv[1])
if d.get("auth_mode") != "chatgpt":
    sys.exit("FATAL: codex auth_mode is %r, not 'chatgpt'" % d.get("auth_mode"))
print(json.dumps(d, separators=(",", ":")))
PY
) || exit 64
    ;;
  *) echo "FATAL: --platform must be claude or codex (got '$PLATFORM')" >&2; exit 64 ;;
esac
if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
  DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"; export DOCKER_HOST
  echo "DOCKER_HOST -> orbstack socket"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$ROOT/data/automode-bench/$STAMP"
WORK="/sandbox/$(basename "$ROOT")"

# The shared skills, once per invocation rather than once per arm — three arms
# rebuilding the same bundle would be three chances for them to differ, and an
# experiment whose arms carry different skills is not measuring the guard.
#
# THE TARGET PATH IS PER PLATFORM and getting it wrong is invisible: uploading to
# a directory the CLI does not read looks exactly like not uploading at all, and
# every number would still come back. Read out of the shipped binaries rather
# than assumed — claude reads ~/.claude/skills (with a CLAUDE_SKILL_DIR
# override), codex reads ~/.codex/skills — and HOME inside the sandbox is
# /sandbox.
SKILLS_ARGS=""
SKILLS_TARGET=$(skills_target "$PLATFORM") || {
  echo "FATAL: no skills surface known for platform '$PLATFORM'" >&2; exit 64; }
SKILLS_LINE="skills-bundle: not carried (SANDBOX_SKILLS=1 to include them)"
if [ "${SANDBOX_SKILLS:-0}" = 1 ] && [ "$VENUE" = sandbox ]; then
  if SKILLS_LINE=$(sh "$ROOT/loopctl/skills-bundle.sh" "$OUT/skills-bundle" 2>&1); then
    SKILLS_ARGS="--upload $OUT/skills-bundle/skills:$SKILLS_TARGET"
  else
    printf '%s\n' "$SKILLS_LINE" >&2
    echo "FATAL: skills were asked for and could not be named — arms carrying an unnameable version cannot be compared to anything later" >&2
    exit 64
  fi
elif [ "${SANDBOX_SKILLS:-0}" = 1 ]; then
  # Direct runs use the host's own surfaces, which is a different thing entirely
  # and must not be reported as if the bundle had been applied.
  SKILLS_LINE="skills-bundle: not applicable to --venue direct (the host's own skills are in force)"
fi

if [ "$DRY" -eq 1 ]; then
  echo "dry-run — preconditions ran, nothing was created"
  echo "  platform  $PLATFORM      venue $VENUE      arms $ARM      runs per arm: $RUNS"
  case "$VENUE" in
    direct) echo "            direct = host CLI, host session, cwd = a DISPOSABLE worktree at HEAD" ;;
    sandbox) echo "            sandbox = OpenShell, policy-governed egress, credentials injected" ;;
  esac
  echo "  task      \"$(printf '%s' "$TASK" | cut -c1-58)...\""
  echo "  graded on the answer containing: $EXPECT"
  if [ "$PLATFORM" = claude ]; then
    echo "  off       claude $CLAUDE_OFF_FLAGS, no .claudeignore"
    echo "  on        claude $CLAUDE_ON_FLAGS + .claudeignore ($(printf '%s' "$IGNORE" | grep -cv '^#') patterns)"
    echo "  reduce    claude $CLAUDE_REDUCE_FLAGS + .claudeignore  <- SAME flags as off; only the ignore file differs"
  else
    echo "  off       codex $CODEX_OFF_FLAGS"
    echo "  on        codex $CODEX_ON_FLAGS"
    echo "  reduce    codex $CODEX_OFF_FLAGS $CODEX_REDUCE_ONLY  <- off PLUS the output lever, nothing else"
    echo "  NOT VARIED: the sandbox axis. bwrap cannot create a namespace here, so"
    echo "              read-only and workspace-write do not execute at all."
  fi
  echo "  skills    $SKILLS_LINE"
  echo "  results   -> $OUT"
  exit 0
fi

mkdir -p "$OUT"

run_arm() { # <arm>
  arm=$1
  name="automode-$PLATFORM-$arm-$STAMP"
  ENV_ARGS=""
  CRED_ARGS=""

  # Everything the arm differs by is assembled HERE, in one place, so a reader can
  # see the single variable rather than diffing two long command lines.
  inner='
set -u
cd '"$WORK"' || exit 64
'
  if [ "$PLATFORM" = claude ]; then
    case "$arm" in
      off) flags="$CLAUDE_OFF_FLAGS"; write_ignore=0 ;;
      on)  flags="$CLAUDE_ON_FLAGS"; write_ignore=1 ;;
      # The arm the measurement asked for. `on` narrows the TOOL SURFACE, which
      # changes the cached prefix and forces it to be rewritten — measured at
      # roughly twice the cache writes and about 22% more money than `off`, in
      # the opposite direction to the document's prediction. `reduce` therefore
      # keeps the prefix byte-identical to `off` and differs by ONE thing: the
      # ignore file. Same permission flags, same tool set, so any difference is
      # attributable to what was kept out of reads rather than to a cache reset.
      reduce) flags="$CLAUDE_REDUCE_FLAGS"; write_ignore=1 ;;
      *) echo "FATAL: unknown arm $arm" >&2; exit 64 ;;
    esac
    CRED_ARGS="--provider claude-code"
    # base64, because the gateway refuses an --env value containing a newline
    # ("spec.environment value ... contains newline or carriage return
    # characters") — and it refused for BOTH arms on the first attempt, since the
    # variable was passed unconditionally and killed the arm that never reads it.
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
  else
    case "$arm" in
      off) flags="$CODEX_OFF_FLAGS" ;;
      on)  flags="$CODEX_ON_FLAGS" ;;
      # Same single-variable discipline: `off` plus the one output lever this
      # version has, and nothing else moved.
      reduce) flags="$CODEX_OFF_FLAGS $CODEX_REDUCE_ONLY" ;;
      *) echo "FATAL: unknown arm $arm" >&2; exit 64 ;;
    esac
    ENV_ARGS="--env CODEX_AUTH_JSON=$CODEX_AUTH"
    inner='
set -u
mkdir -p "$HOME/.codex"
printenv CODEX_AUTH_JSON >"$HOME/.codex/auth.json"
chmod 600 "$HOME/.codex/auth.json"
cd '"$WORK"' || exit 64
i=1
while [ "$i" -le '"$RUNS"' ]; do
  codex exec --skip-git-repo-check --json '"$flags"' "$BENCH_TASK" >"/sandbox/run-$i.jsonl" 2>"/sandbox/run-$i.err" || true
  # Abort the arm on the first empty run instead of repeating it N times. A
  # rejected flag produced three identical empty results and three wasted turns
  # before anyone read the .err sitting next to them; one probe is enough to
  # know the arm cannot run at all.
  if [ ! -s "/sandbox/run-$i.jsonl" ]; then
    echo "run $i produced NOTHING — aborting this arm. stderr follows:"
    head -c 400 "/sandbox/run-$i.err"
    break
  fi
  echo "run $i done"
  i=$((i + 1))
done
tar cf /sandbox/bench.tar -C /sandbox $(cd /sandbox && ls run-*.jsonl run-*.err 2>/dev/null)
'
  fi

  if [ "$VENUE" = direct ]; then
    # Host process, DISPOSABLE WORKTREE — never the live tree. The baseline arm
    # carries --dangerously-skip-permissions, which is the exact thing sandboxes
    # exist to contain; pointing that at the checkout someone is working in would
    # trade a measurement for an unbounded write. A worktree at HEAD gives the
    # same bytes with none of that, and it is the pattern the controls already
    # use. `direct` therefore measures the CLI without the container, not without
    # isolation — a distinction worth keeping, because the second one is not on
    # offer here.
    echo "=== $PLATFORM arm $arm: $RUNS run(s) directly, in a worktree at HEAD"
    DWT="$OUT/.wt-$arm"
    git -C "$ROOT" worktree add --detach "$DWT" HEAD >/dev/null 2>&1 || {
      echo "FATAL: could not create the worktree for the direct venue" >&2; exit 64; }
    [ "${write_ignore:-0}" -eq 1 ] && printf '%s' "$IGNORE" >"$DWT/.claudeignore"
    mkdir -p "$OUT/$arm"
    i=1
    while [ "$i" -le "$RUNS" ]; do
      if [ "$PLATFORM" = claude ]; then
        ( cd "$DWT" && claude -p "$TASK" --output-format json $flags ) \
          >"$OUT/$arm/run-$i.json" 2>"$OUT/$arm/run-$i.err" || true
        produced="$OUT/$arm/run-$i.json"
      else
        ( cd "$DWT" && codex exec --skip-git-repo-check --json $flags "$TASK" ) \
          >"$OUT/$arm/run-$i.jsonl" 2>"$OUT/$arm/run-$i.err" || true
        produced="$OUT/$arm/run-$i.jsonl"
      fi
      if [ ! -s "$produced" ]; then
        echo "run $i produced NOTHING — aborting this arm. stderr follows:"
        head -c 400 "$OUT/$arm/run-$i.err"
        break
      fi
      echo "run $i done"
      i=$((i + 1))
    done
    git -C "$ROOT" worktree remove --force "$DWT" >/dev/null 2>&1
    return 0
  fi

  echo "=== $PLATFORM arm $arm: $RUNS run(s) in $name"
  openshell sandbox delete "$name" >/dev/null 2>&1
  openshell sandbox create --name "$name" --no-tty \
    --policy "$ROOT/loopctl/sandbox-policy.yaml" \
    $CRED_ARGS \
    --env "BENCH_TASK=$TASK" \
    $ENV_ARGS \
    $SKILLS_ARGS \
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
  all) run_arm off; run_arm on; run_arm reduce ;;
  off|on|reduce) run_arm "$ARM" ;;
  *) echo "FATAL: --arm must be off, on, reduce, both or all" >&2; exit 64 ;;
esac

python3 "$ROOT/loopctl/automode_report.py" --platform "$PLATFORM" "$OUT" "$EXPECT"
