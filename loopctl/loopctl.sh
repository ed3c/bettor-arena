#!/bin/sh
# loopctl.sh — the one CLI over this repo's three loops.
#
#   loopctl.sh <macro|micro|openwiki> <run|prove|test> [flags]
#   loopctl.sh contract      print the declared surface and its sha256
#   loopctl.sh --selftest    prove the surface and the wiring still agree
#
# Why this exists: each loop's entry point has its own argument shape, its own
# env switches and its own idea of what an exit code means. A caller that learns
# those internals ends up editing them when a call site is inconvenient, and the
# loop drifts to fit its caller instead of the other way round. Here the surface
# is declared once in contract.json and the internals are reachable only through
# it.
#
# Surface versus wiring. contract.json holds what a caller may say — loops,
# modes, required and optional flags, what each writes. This file holds how each
# target is actually invoked. They are separate so the surface can be diffed and
# hashed without the wiring moving underneath it, and --selftest fails if either
# side gains a command the other lacks, so they cannot drift apart quietly.
#
# Exit codes are the target's own, passed through untouched: 0 ok · 2 the loop's
# check failed · 64 usage, contract violation, or a FATAL from the target. This
# CLI never re-maps them — a wrapper that flattens exit codes destroys the only
# signal its caller has.
#
# Depth-independent by construction: the repo root is resolved with git from
# this file's own location, and every target is named repo-relative in the
# contract. Nothing here assumes loopctl/ sits one level down.
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
CONTRACT="$HERE/contract.json"

usage() {
  echo "usage: loopctl.sh <macro|micro|openwiki> <run|prove|test> [flags]" >&2
  echo "       loopctl.sh contract | --selftest" >&2
  echo "       flags per command: loopctl.sh contract" >&2
}

fatal() { echo "loopctl FATAL: $*" >&2; exit 64; }

sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

ROOT=$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null) \
  || fatal "not inside a git work tree: $HERE"
[ -f "$CONTRACT" ] || fatal "contract.json missing next to loopctl.sh — the surface is gone, and guessing it is exactly what this CLI exists to prevent"

# ------------------------------------------------------------------ meta
case "${1:-}" in
  contract)
    cat "$CONTRACT"
    echo "contract_sha256: $(sha256 "$CONTRACT")"
    # The one a caller should pin: it covers what may be SAID, and internal
    # iteration underneath it leaves it untouched.
    echo "surface_digest: $(python3 "$HERE/surface_digest.py" digest "$CONTRACT")"
    exit 0 ;;
  surface-relock)
    python3 "$HERE/surface_digest.py" relock "$CONTRACT" "$HERE/surface.lock"
    exit $? ;;
  --selftest) . "$HERE/selftest.sh"; loopctl_selftest; exit $? ;;
  -h|--help|"") usage; exit 64 ;;
esac

LOOP=$1
MODE=${2:-}
[ -n "$MODE" ] || { usage; exit 64; }
shift 2

# ------------------------------------------------- contract enforcement
# The check is driven by contract.json, not by a second copy of the rules here.
# A flag the contract does not list is refused rather than forwarded: forwarding
# unknown flags is how a caller starts depending on a target's private switches.
CHECK=$(LOOPCTL_ARGS="$*" python3 - "$CONTRACT" "$LOOP" "$MODE" <<'PY'
import json, os, sys

contract = json.load(open(sys.argv[1], encoding="utf-8"))
loop, mode = sys.argv[2], sys.argv[3]
entry = next(
    (c for c in contract["commands"] if c["loop"] == loop and c["mode"] == mode), None
)
if entry is None:
    loops = sorted({c["loop"] for c in contract["commands"]})
    modes = sorted({c["mode"] for c in contract["commands"] if c["loop"] == loop})
    if loop not in loops:
        print(f"ERR unknown loop {loop!r}; declared: {loops}")
    else:
        print(f"ERR unknown mode {mode!r} for {loop}; declared: {modes}")
    raise SystemExit(0)

args = (os.environ.get("LOOPCTL_ARGS") or "").split()
allowed = set(entry["required"]) | set(entry["optional"])
flags = [a for a in args if a.startswith("-")]
unknown = [f for f in flags if f not in allowed]
if unknown:
    print(f"ERR flag(s) {unknown} are not on the surface for {loop} {mode}; declared: {sorted(allowed)}")
    raise SystemExit(0)
missing = [f for f in entry["required"] if f not in flags]
if missing:
    print(f"ERR missing required flag(s) {missing} for {loop} {mode}")
    raise SystemExit(0)
print("OK " + entry["target"])
PY
) || fatal "contract check could not run"

case "$CHECK" in
  "ERR "*) echo "loopctl FATAL: ${CHECK#ERR }" >&2; exit 64 ;;
esac
TARGET=${CHECK#OK }
[ -f "$ROOT/$TARGET" ] || fatal "contract names a target that is not here: $TARGET"

# ------------------------------------------------------------ dispatch
# One branch per contract command. --selftest asserts this list and the contract
# name the same set, in both directions.
value_of() { # flag, from the saved argument list
  _want=$1; shift
  while [ $# -gt 0 ]; do
    [ "$1" = "$_want" ] && { echo "${2:-}"; return 0; }
    shift
  done
  echo ""
}
has_flag() {
  _want=$1; shift
  while [ $# -gt 0 ]; do [ "$1" = "$_want" ] && return 0; shift; done
  return 1
}

case "$LOOP/$MODE" in
  macro/run)
    _ollama=$(value_of --ollama-url "$@")
    if [ -n "$_ollama" ]; then OLLAMA_URL="$_ollama" sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  macro/prove)    if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  macro/test)     sh "$ROOT/$TARGET" ;;
  micro/run)      sh "$ROOT/$TARGET" "$(value_of --packet "$@")" "$(value_of --output "$@")" ;;
  micro/prove)    if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  micro/test)     sh "$ROOT/$TARGET" ;;
  openwiki/run)
    _env=""
    has_flag --force-receipt "$@" && _env="$_env WIKI_UPDATE_FORCE_RECEIPT=1"
    has_flag --defer-partials "$@" && _env="$_env WIKI_UPDATE_DEFER_PARTIALS=1"
    _mode=--dry-run
    has_flag --full "$@" && _mode=""
    # shellcheck disable=SC2086 # _env is a deliberate list of NAME=VALUE pairs
    env $_env sh "$ROOT/$TARGET" "$(value_of --request "$@")" $_mode ;;
  openwiki/prove) if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  openwiki/test)  if has_flag --full "$@"; then CONTROL_OPENWIKI_FULL=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  *) fatal "no dispatch for $LOOP/$MODE — the contract lists it and this file does not (--selftest exists to catch exactly this)" ;;
esac
RC=$?

echo "loopctl: loop=$LOOP mode=$MODE target=$TARGET exit=$RC"
exit "$RC"
