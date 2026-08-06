#!/usr/bin/env bash
# setup-prototype.sh <plan_name> <repo_name> [--mvp] [pip_pkg ...]
# Scaffold a workspace in the skill-bettor mastery convention location
# (symmetric to setup-repo.sh's /repo/<r>/<r>/):
#   ROOT = <host_root>/prototype/<plan_name>/<repo_name>/   (/prototype/ is gitignored)
# <host_root> = the checkout this module is installed in, derived via git at run time
# (override with SKILL_BETTOR_PROTOTYPE_ROOT); never a hardcoded machine path.
#
# TWO modes (Fable-5 review 2026-07-11: the earlier version claimed "八大基座 scaffolder" but only built a
# venv — that overclaim is now made TRUE by --mvp):
#   default (feasibility prototype): venv + NOTES.md + independent git. THROWAWAY — answers ONE feasibility
#     question via a PROTOTYPE_*.py, banks the ANSWER in NOTES.md upstream, then gets deleted.
#   --mvp (prototype→MVP repo): ALSO scaffolds the real 八大基座 (PROMPT/PLAN/CLAUDE/run.sh/verify.sh +
#     DESIGN-SCORE.md + dispatches/ + scripts//tests/). This is a self-driving sandbox that GRADUATES to a
#     product (see PLAN.md "graduation homing" — a graduated MVP must leave gitignored /prototype/ for a
#     remote or /repo/, else it is a single-machine orphan).
#   Run:  bash kb-ingest/setup-prototype.sh llm-timeline-editing cutplan --mvp opentimelineio
set -uo pipefail

PLAN="${1:?plan_name (e.g. llm-timeline-editing)}"; NAME="${2:?repo_name (e.g. cutplan)}"; shift 2 || true
MVP=false; PKGS=()
for a in "$@"; do [ "$a" = "--mvp" ] && MVP=true || PKGS+=("$a"); done

HOST_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null)" || true
[ -n "${SKILL_BETTOR_PROTOTYPE_ROOT:-}" ] || [ -n "$HOST_ROOT" ] || \
  { echo "FATAL: module is not inside a git work tree — set SKILL_BETTOR_PROTOTYPE_ROOT" >&2; exit 1; }
ROOT="${SKILL_BETTOR_PROTOTYPE_ROOT:-"$HOST_ROOT/prototype"}/$PLAN/$NAME"
PY="$(command -v python3.12 || command -v python3)"
mkdir -p "$ROOT"

if [ -x "$ROOT/venv/bin/python" ]; then echo "venv already present → $ROOT/venv (skipping)"
else echo "Creating venv ($("$PY" --version 2>&1)) → $ROOT/venv ..."; "$PY" -m venv "$ROOT/venv" || { echo "FATAL: venv create failed" >&2; exit 1; }; fi
if [ "${#PKGS[@]}" -gt 0 ]; then echo "Installing: ${PKGS[*]}"; "$ROOT/venv/bin/pip" install --quiet --disable-pip-version-check "${PKGS[@]}" || echo "WARN: pip install error — check ${PKGS[*]}" >&2; fi

seed() { [ -f "$2" ] || { printf '%s' "$1" > "$2"; echo "  seeded $(basename "$2")"; }; }

if [ "$MVP" = false ]; then
  # ── feasibility prototype (verification anchor) ──
  seed "# PROTOTYPE ANSWER — $PLAN / $NAME

**Question (feasibility, one only):** <what end-to-end claim is this prototype checking?>
**Run:** \`venv/bin/python PROTOTYPE_*.py\`

## Verdict
<FILL BEFORE CLOSING — 推導→實測 which claims flipped, what broke, the load-bearing finding>
## What this does NOT prove (honest)
<real-app import? LLM step simulated? edge cases deferred?>
## Disposition
Verification anchor. Absorb the ANSWER upstream, then KEEP this dir (gitignored, own git) as the
re-runnable proof for the SYNTHESIS claim it closed. Never promote its code into src/.
" "$ROOT/NOTES.md"
  printf 'venv/\n__pycache__/\n*.pyc\n' > "$ROOT/.gitignore.tmp"; [ -f "$ROOT/.gitignore" ] || mv "$ROOT/.gitignore.tmp" "$ROOT/.gitignore"; rm -f "$ROOT/.gitignore.tmp" 2>/dev/null || true
else
  # ── MVP repo: real 八大基座 sandbox (Fable-5 mechanisms baked in) ──
  mkdir -p "$ROOT/src" "$ROOT/tests" "$ROOT/scripts" "$ROOT/dispatches"
  printf 'venv/\n__pycache__/\n*.pyc\n.pytest_cache/\n.verify_tmp/\ndist/\nbuild/\n*.egg-info/\n' > "$ROOT/.gi.tmp"; [ -f "$ROOT/.gitignore" ] || cp "$ROOT/.gi.tmp" "$ROOT/.gitignore"; rm -f "$ROOT/.gi.tmp"
  seed "# PROMPT — $NAME MVP goal contract (八大基座 #7)
## Mission
<one line: what this MVP does; upstream design SSOT (answer-key) = <path to SYNTHESIS/plan>>
## Success Criteria (verify.sh is the machine gate; each SC MUST have a regression test in tests/)
- [ ] SC1 <...>
## Dual-score graduation gate
- **Design score** (before build): every golden-path element of the design SSOT is either a done SC or a
  *designed cut* justified in PLAN.md — tracked in DESIGN-SCORE.md (a MISS cell = FAIL). NOT SYNTHESIS
  vibe-approval: the DESIGN-SCORE.md table makes it mechanically visible; graduation runs a fresh
  zero-context subagent design-judge over it (never fed the big-loop's rationale).
- **Impl score** (after build): verify.sh exit 0 (LIVE/RIP — real run).
- Graduate only when a human LAND-DECISION admits both scores green — THEN home the repo out of gitignored
  /prototype/ (remote or /repo/), else it is a single-machine orphan.
## Stop-loss
- 3 no-progress rounds OR un-revertible-to-green verify.sh → STOP, write failure trace to PLAN.md, SURFACE.
" "$ROOT/PROMPT.md"
  seed "# PLAN — $NAME state ledger (八大基座 #8)
STATUS: executing
## Iteration log (append per round; never git commit mid-iteration)
- round 00 (seed): scaffolded 八大基座 via setup-prototype.sh --mvp.
## Input-side record (Fable-5: fresh-driver must be auditable/replayable)
- each round's dispatch brief -> dispatches/round-NN.md (verbatim) + driver invocation metadata (model/tier/isolation).
## Deviations / gate exceptions (Fable-5: any modified/DELETED existing test needs a HUMAN-AUTHORIZED mark HERE)
- format: '- round NN HUMAN-AUTHORIZED: <who/why> deleted/changed tests/<f>'
- ⚠ E2 (cc-20260712): this mark is an AUDIT TRIPWIRE, not proof of "human" — a driver can write it. The real gate is the judge reviewing your git diff at commit (where a forged mark is caught). Do not treat the grep as enforcement.
## Failure traces
- (none yet)
" "$ROOT/PLAN.md"
  seed "# CLAUDE.md — $NAME MVP sandbox driver rules (八大基座 #1)
You are the small-loop driver iterating this MVP toward the open SC in PROMPT.md. Fresh zero-context per round.
## Loop rules (violate -> stop)
1. Read PROMPT.md (goal+SC), PLAN.md (state+failures), src/ (impl). **domain/goal live in PROMPT.md — not restated here (single SSOT).**
2. Close ONE open SC/round; add its regression test in tests/. verify.sh is the gate.
3. **Never edit tests to pass; never weaken verify.sh; never delete a passing test** (design-gate *tripwires* a deleted/changed test with a PLAN HUMAN-AUTHORIZED mark — but the grep can't verify "human", a driver could forge it; the REAL gate is the judge reviewing your diff at commit, where forgery is caught).
4. No git commit mid-iteration. Append round outcome to PLAN.md; on 3 no-progress rounds STOP + SURFACE.
" "$ROOT/CLAUDE.md"
  seed "#!/usr/bin/env bash
# run.sh <driver> <target> [feedback_file]  — 八大基座 dispatcher (Fable-5: bind target, no hardcoded SC)
set -uo pipefail; cd \"\$(dirname \"\${BASH_SOURCE[0]}\")\"
DRIVER=\"\${1:?driver: claude|agy|subagent}\"; TARGET=\"\${2:?target: absolute path the driver modifies}\"
FB=\"\"; [ -n \"\${3:-}\" ] && [ -f \"\${3}\" ] && FB=\"\$(cat \"\${3}\")\"
read -r -d '' TASK <<EOF || true
Small-loop driver. Read CLAUDE.md/PROMPT.md/PLAN.md and TARGET=\${TARGET}. Close ONE open SC; add a regression
test; append outcome to PLAN.md. Do NOT weaken verify.sh or delete passing tests.
\${FB:+Graduation-judge feedback to address:
\$FB}
EOF
case \"\$DRIVER\" in
  claude) exec claude -p \"\$TASK\" --permission-mode acceptEdits < /dev/null ;;
  agy) exec agy --mode accept-edits --add-dir \"\$(pwd)\" -p \"\$TASK\" < /dev/null ;;
  subagent) printf '%s\\n' \"\$TASK\" ;;
  *) echo 'usage: run.sh <claude|agy|subagent> <target> [feedback]' >&2; exit 64 ;;
esac
" "$ROOT/run.sh"; chmod +x "$ROOT/run.sh"
  seed "#!/usr/bin/env bash
# verify.sh — $NAME T0 hard gate (八大基座 分層驗證). Exit 0=PASS, 2=FAIL. Fable-5 mechanisms baked in.
#   --fast : hermetic only (skip real integrations / heavy models) for the iterate inner loop.
set -uo pipefail; HERE=\"\$(cd \"\$(dirname \"\${BASH_SOURCE[0]}\")\" && pwd)\"; PY=\"\$HERE/venv/bin/python\"
FAST=false; [ \"\${1:-}\" = \"--fast\" ] && FAST=true
fail() { echo \"VERIFY: FAIL — \$1\" >&2; exit 2; }
[ -x \"\$PY\" ] || fail 'no venv python'
\"\$PY\" -c 'import pytest' 2>/dev/null || \"\$HERE/venv/bin/pip\" install --quiet pytest >/dev/null 2>&1

# design-gate (Fable-5): every [x] SC must have a tests/ reference; any deleted/changed EXISTING test must
# leave a PLAN.md HUMAN-AUTHORIZED mark. NOTE: --diff-filter=MD scopes this to Modified/Deleted only — a purely
# ADDED test file (even if staged) must NOT trip the gate (skillgate cc-20260711: new tests aren't a weakening).
# ⚠ E2 (cc-20260712): this grep is an AUDIT TRIPWIRE, NOT enforcement of \"human\" — a driver CAN write the mark
# (round-10 agy forged one). The REAL gate is the judge reviewing git diff before commit (that caught the forgery);
# recipe-not-engine = commit gate always human. Don't over-claim \"design-gate enforces\".
for sc in \$(grep -oE '\\[x\\] SC[0-9]+' \"\$HERE/PROMPT.md\" 2>/dev/null | grep -oE 'SC[0-9]+'); do
  grep -rwqE \"\$sc\" \"\$HERE/tests/\" 2>/dev/null || fail \"design-gate: \$sc marked done but no tests/ reference\"
done
if git -C \"\$HERE\" rev-parse --git-dir >/dev/null 2>&1; then
  changed=\$(git -C \"\$HERE\" diff --name-only --diff-filter=MD -- 'tests/*' 2>/dev/null; git -C \"\$HERE\" diff --cached --name-only --diff-filter=MD -- 'tests/*' 2>/dev/null)
  if [ -n \"\$changed\" ] && ! grep -qE '^- round [0-9]+[a-z]* HUMAN-AUTHORIZED:' \"\$HERE/PLAN.md\" 2>/dev/null; then
    fail \"design-gate: existing test(s) changed [\$changed] but no HUMAN-AUTHORIZED entry in PLAN.md\"
  fi
fi

echo \"VERIFY: pytest\"
if \$FAST; then \"\$PY\" -m pytest \"\$HERE/tests\" -q -m 'not integration' || fail 'pytest (fast) red'
else \"\$PY\" -m pytest \"\$HERE/tests\" -q || fail 'pytest red'; fi
echo \"VERIFY: PASS\"; exit 0
" "$ROOT/verify.sh"; chmod +x "$ROOT/verify.sh"
  seed "# DESIGN-SCORE — $NAME (Fable-5: design score mechanized, not SYNTHESIS vibe-approval)
Fill from the design SSOT's golden path. A MISS cell = design-score FAIL. Graduation runs a fresh
zero-context subagent design-judge over THIS table (not fed the big-loop's rationale).

| golden-path element | status: done SC-id | designed-cut @ PLAN line | MISS |
|---|---|---|---|
| <element 1> |  |  |  |
" "$ROOT/DESIGN-SCORE.md"
  seed "# dispatch briefs (Fable-5: input-side record so fresh-driver is auditable/replayable)
one file per round: round-NN.md = the verbatim brief given to that round's driver + invocation metadata.
" "$ROOT/dispatches/README.md"
  echo "  scaffolded 八大基座: PROMPT.md PLAN.md CLAUDE.md run.sh verify.sh DESIGN-SCORE.md dispatches/ src/ tests/ scripts/"
fi

# NOTES.md (both modes) + independent git
seed "# NOTES — $PLAN / $NAME\nSee PROMPT.md (goal) / PLAN.md (state).\n" "$ROOT/NOTES.md"
if [ ! -d "$ROOT/.git" ]; then
  git -C "$ROOT" init -q && echo "git: independent repo initialised at $ROOT"
  git -C "$ROOT" add -A 2>/dev/null
  git -C "$ROOT" commit -q -m "scaffold: $PLAN/$NAME$([ "$MVP" = true ] && echo ' (--mvp 八大基座)')" 2>/dev/null \
    && echo "git: scaffold commit made" || echo "git: NOTE — set a git identity then commit in $ROOT"
else echo "git: independent repo already present"; fi

echo "OK — $ROOT ready ($([ "$MVP" = true ] && echo 'MVP 八大基座 sandbox' || echo 'feasibility prototype'), independent git, gitignored)."
