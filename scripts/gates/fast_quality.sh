#!/bin/sh
# fast_quality.sh — the single fast-quality check definition (format / lint /
# type / shell syntax) for bettor-arena. ARCHITECTURE.md §3.5's "same
# definition, different scope" gate:
#
#   mount 1 (this file): staged/preflight scope — pre-commit.staged feeds it
#     the staged file list; any caller may feed any list.
#   mount 2 (same source): the factory sandbox's full-scope mount is
#     loop_wiki/evolve-perfect-seed-repo-factory/verify.sh → `bun run
#     quality:fast` (src/run_fast_quality.ts), same toolchain + configs over
#     the whole sandbox. Neither mount redefines the checks.
#
# Input: file paths as arguments, or newline-separated on stdin when no path
# arguments are given. Lanes by extension:
#   TS lane    (*.ts *.tsx *.mts *.cts): factory sandbox toolchain — prettier
#     --check, eslint, tsc --noEmit from the factory's devDependencies
#     (node_modules/.bin), given files only. TS files OUTSIDE the factory ride
#     the same lane for now and therefore depend on the factory's
#     devDependencies and configs; two honest limits of that ride: eslint
#     skips files outside its base path (warning, not a lie of a green — the
#     receipt still records the stage), and tsc checks given files with the
#     factory tsconfig's compilerOptions mirrored as CLI flags (--project
#     cannot take a file list), so both mounts judge a file identically. The
#     factory's own full-project typecheck lives in mount 2.
#   Python lane (*.py): ruff format --check + ruff check. ruff absent =
#     FATAL 64, named, with install guidance — no network fallback: the gate
#     judges with the locally pinned tool or refuses, it never fetches one.
#   Shell lane  (*.sh *.bash): bash -n (sh -n when bash is absent).
#
# Fail-fast: first failing stage blocks all later stages, which are recorded
# as not_run. Runs no tests, touches no network.
#
# Receipt: JSON to stdout, or to --receipt <path>. Never lands in
# data/receipts/. Carries gate_inputs (sha256 of every involved config file +
# this script) and claim_boundary "preflight-only-not-code-quality-axis":
# green here is a preflight pass only, never a CQ/PU code-quality-axis claim.
#
# Exit codes: 0 pass · 2 check failed · 64 FATAL (usage, missing file,
# missing tool). FAST_QUALITY_FACTORY overrides the factory path (test seam).
set -u

SELF=$(cd "$(dirname "$0")" && pwd -P)/$(basename "$0")
ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
FACTORY=${FAST_QUALITY_FACTORY:-"$ROOT/loop_wiki/evolve-perfect-seed-repo-factory"}
NL='
'

fatal() { echo "fast_quality FATAL: $1" >&2; exit 64; }

RECEIPT=""
FILES=""
while [ $# -gt 0 ]; do
  case "$1" in
    --receipt)
      [ $# -ge 2 ] || fatal "--receipt needs a path"
      RECEIPT=$2; shift 2 ;;
    -*) fatal "unknown flag $1 (usage: fast_quality.sh [--receipt <path>] [file...])" ;;
    *) FILES="$FILES$1$NL"; shift ;;
  esac
done
[ -n "$FILES" ] || FILES=$(cat)

TS=""; PY=""; SH=""
OLDIFS=$IFS; IFS=$NL
for f in $FILES; do
  [ -n "$f" ] || continue
  case "$f" in /*) ;; *) f="$PWD/$f" ;; esac  # lanes cd elsewhere; anchor now
  [ -f "$f" ] || fatal "input file missing: $f (deleted paths must be filtered out by the caller)"
  case "$f" in
    *.ts|*.tsx|*.mts|*.cts) TS="$TS$f$NL" ;;
    *.py)                   PY="$PY$f$NL" ;;
    *.sh|*.bash)            SH="$SH$f$NL" ;;
  esac
done
IFS=$OLDIFS

# ------------------------------------------------- tool presence (FATAL 64)
if [ -n "$PY" ]; then
  command -v ruff >/dev/null 2>&1 \
    || fatal "ruff not on PATH (Python lane cannot run; install it: brew install ruff, or pipx install ruff)"
fi
if [ -n "$TS" ]; then
  [ -d "$FACTORY/node_modules/.bin" ] \
    || fatal "factory toolchain missing at $FACTORY (TS lane cannot run; bun install in the factory)"
  command -v node >/dev/null 2>&1 \
    || fatal "node not on PATH (factory .bin shims cannot run; TS lane blocked)"
fi
SHELLCHECKER="sh"
command -v bash >/dev/null 2>&1 && SHELLCHECKER="bash"

# ------------------------------------------------------------ stage machinery
json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

STAGES=""
BLOCKED=0
FAILED_STAGE=""

record() { # id status exit_code
  [ -n "$STAGES" ] && STAGES="$STAGES,"
  STAGES="$STAGES{\"id\":\"$1\",\"status\":\"$2\",\"exit_code\":$3}"
}

# run_stage <id> <lane-file-list> <cmd...> — appends the lane files as args.
run_stage() {
  _id=$1; _lane=$2; shift 2
  [ -n "$_lane" ] || return 0
  if [ "$BLOCKED" -eq 1 ]; then record "$_id" not_run null; return 0; fi
  OLDIFS=$IFS; IFS=$NL
  for _f in $_lane; do set -- "$@" "$_f"; done
  IFS=$OLDIFS
  _out=$("$@" 2>&1); _rc=$?
  if [ "$_rc" -eq 0 ]; then
    record "$_id" passed "$_rc"
  else
    record "$_id" failed "$_rc"
    BLOCKED=1
    FAILED_STAGE=$_id
    printf '%s\n' "fast_quality stage $_id FAILED:" "$_out" >&2
  fi
}

in_factory() { (cd "$FACTORY" && "$@"); }

# Cheap lanes first so a cheap red spares the expensive TS toolchain spin-up.
run_stage sh-syntax  "$SH" "$SHELLCHECKER" -n
run_stage py-format  "$PY" ruff format --check
run_stage py-lint    "$PY" ruff check --quiet
run_stage ts-format  "$TS" in_factory ./node_modules/.bin/prettier --config prettier.config.mjs --check
run_stage ts-lint    "$TS" in_factory ./node_modules/.bin/eslint --config eslint.config.mjs
# Mirrors the factory tsconfig.json compilerOptions (tsc --project cannot take
# a file list, so the flags ride the CLI); if the factory tsconfig changes,
# change this line with it — gate_inputs hashes both so drift is visible.
run_stage ts-typecheck "$TS" in_factory ./node_modules/.bin/tsc --noEmit \
  --strict --noUncheckedIndexedAccess --exactOptionalPropertyTypes \
  --noImplicitOverride --noFallthroughCasesInSwitch --noImplicitReturns \
  --useUnknownInCatchVariables --skipLibCheck \
  --target es2022 --module esnext --moduleResolution bundler --lib es2022 --types bun

# ------------------------------------------------------------------ receipt
sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

GATE_INPUTS="\"$(json_escape "scripts/gates/fast_quality.sh")\":\"$(sha256 "$SELF")\""
add_input() { [ -f "$1" ] && GATE_INPUTS="$GATE_INPUTS,\"$(json_escape "$2")\":\"$(sha256 "$1")\""; return 0; }
if [ -n "$TS" ]; then
  for c in package.json bun.lock prettier.config.mjs eslint.config.mjs tsconfig.json; do
    add_input "$FACTORY/$c" "factory/$c"
  done
fi
if [ -n "$PY" ]; then
  for c in pyproject.toml ruff.toml .ruff.toml; do
    add_input "$ROOT/$c" "$c"
  done
fi

count() { [ -n "$1" ] && printf '%s' "$1" | grep -c . || echo 0; }
STATUS=passed; [ "$BLOCKED" -eq 1 ] && STATUS=failed

OUT=$(printf '{"schema_version":"bettor-arena-fast-quality-receipt@1.0.0","gate":"fast_quality","claim_boundary":"preflight-only-not-code-quality-axis","utc":"%s","status":"%s","counts":{"ts":%s,"py":%s,"shell":%s},"gate_inputs":{%s},"stages":[%s]}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$STATUS" \
  "$(count "$TS")" "$(count "$PY")" "$(count "$SH")" \
  "$GATE_INPUTS" "$STAGES")

if [ -n "$RECEIPT" ]; then printf '%s\n' "$OUT" > "$RECEIPT"; else printf '%s\n' "$OUT"; fi

[ "$BLOCKED" -eq 0 ] || { echo "fast_quality FAIL at stage $FAILED_STAGE" >&2; exit 2; }
exit 0
