#!/bin/sh
# loopctl.sh — the one CLI over this repo's declared loops.
#
#   loopctl.sh <macro|micro|openwiki|notebooklm|agent-runtime|ctg> <mode> [flags]
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
  echo "usage: loopctl.sh <macro|micro|openwiki|notebooklm|agent-runtime|equivalence|ctg> <mode> [flags]" >&2
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
  workflow)
    # The workflow's own lifecycle: what it is made of, what stamps a commit with
    # it, and how to run the version a commit or tag names.
    case "${2:-}" in
      lock)    python3 "$HERE/workflow_lock.py" build "$ROOT" "$HERE/workflow.lock"; exit $? ;;
      prove)
        if [ "${3:-}" = "--force-receipt" ]; then
          PROVE_FORCE_RECEIPT=1 sh "$ROOT/proof_workflow/prove_workflow.sh"
        else
          sh "$ROOT/proof_workflow/prove_workflow.sh"
        fi
        exit $? ;;
      trailer) python3 "$HERE/lineage.py" trailer "$ROOT" "$HERE/workflow.lock"; exit $? ;;
      replay)
        shift 2
        sh "$HERE/replay.sh" "$@"; exit $? ;;
      test)
        # The control group for the lineage machinery itself: does the thing that
        # senses a moved workflow actually sense it, and does replay execute the
        # version a tag names. Planted defects only, all inside a worktree.
        sh "$ROOT/proof_workflow/control_workflow_lineage.sh"; exit $? ;;
      *) echo "usage: loopctl.sh workflow <lock|trailer|test|replay --at <commit|tag> [--loop <loop>]>" >&2; exit 64 ;;
    esac ;;
  container)
    # The second driver. Everything here goes through container-run.sh so the
    # socket selection and mount decisions live in exactly one place.
    case "${2:-}" in
      build)     sh "$ROOT/loopctl/container-run.sh" build; exit $? ;;
      preflight) sh "$ROOT/loopctl/container-run.sh" preflight; exit $? ;;
      prove)
        # This branch runs BEFORE the contract check, so flags arrive unparsed.
        # --force-receipt is honoured explicitly rather than silently dropped: a
        # dropped flag makes the receipt collide and FATAL, which reads as the
        # proof failing rather than as the flag going missing.
        if [ "${3:-}" = "--force-receipt" ]; then
          PROVE_FORCE_RECEIPT=1 sh "$ROOT/proof_workflow/prove_container.sh"
        else
          sh "$ROOT/proof_workflow/prove_container.sh"
        fi
        exit $? ;;
      test)      sh "$ROOT/proof_workflow/control_container_surface.sh"; exit $? ;;
      *) echo "usage: loopctl.sh container <build|preflight|prove|test>" >&2; exit 64 ;;
    esac ;;
  harness)
    # The instrument measuring itself. Not a cycle: a script's own bytes do not
    # move when the digest moves, unlike workflow.lock which is derived from it.
    case "${2:-}" in
      prove)
        if [ "${3:-}" = "--force-receipt" ]; then
          PROVE_FORCE_RECEIPT=1 sh "$ROOT/proof_workflow/prove_harness.sh"
        else
          sh "$ROOT/proof_workflow/prove_harness.sh"
        fi
        exit $? ;;
      test) sh "$ROOT/proof_workflow/control_harness_coverage.sh"; exit $? ;;
      *) echo "usage: loopctl.sh harness <prove|test>" >&2; exit 64 ;;
    esac ;;
  policy)
    case "${2:-}" in
      prove)
        # Flags arrive unparsed in this pre-contract branch; --force-receipt is
        # honoured rather than dropped, since a dropped flag collides the receipt
        # and reads as the proof failing.
        if [ "${3:-}" = "--force-receipt" ]; then
          PROVE_FORCE_RECEIPT=1 sh "$ROOT/proof_workflow/prove_policy.sh"
        else
          sh "$ROOT/proof_workflow/prove_policy.sh"
        fi
        exit $? ;;
      test) sh "$ROOT/proof_workflow/control_sandbox_policy.sh"; exit $? ;;
      *) echo "usage: loopctl.sh policy <prove|test>" >&2; exit 64 ;;
    esac ;;
  mcp)
    # The external-facing layer. serve is long-lived on purpose: isolation comes
    # from the per-call worktree, not from restarting the process, and a fresh
    # process per call would throw away every cached prefix.
    case "${2:-}" in
      serve)
        shift 2
        # Flags forwarded as given: --ref pins the workflow, --http switches from
        # stdio to a governable transport. Parsing them again here would be a
        # second copy of the server's own argument handling.
        exec python3 "$HERE/mcp_server.py" "$@" ;;
      test)  sh "$ROOT/proof_workflow/control_mcp_surface.sh"; exit $? ;;
      tools) python3 "$HERE/mcp_tools.py" "$CONTRACT"; exit $? ;;
      # The same proof as `policy prove`: the authorization surface is one unit.
      prove)
        if [ "${3:-}" = "--force-receipt" ]; then
          PROVE_FORCE_RECEIPT=1 sh "$ROOT/proof_workflow/prove_policy.sh"
        else
          sh "$ROOT/proof_workflow/prove_policy.sh"
        fi
        exit $? ;;
      *) echo "usage: loopctl.sh mcp <serve [--ref <commit|tag>]|test|tools>" >&2; exit 64 ;;
    esac ;;
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

# --json turns the whole invocation into one machine-readable result. Without it
# a wrapper has to parse the human line, which is the same reaching-past-the-CLI
# this file exists to stop — just one layer up. With it, the target's streams are
# captured into the result rather than dropped, because a caller that only gets
# an exit code cannot tell a red gate from a crash.
JSON=0
has_flag --json "$@" && JSON=1
if [ "$JSON" -eq 1 ]; then
  CAPTURE=$(mktemp -d "${TMPDIR:-/tmp}/loopctl-json.XXXXXX")
  exec 3>&1
  exec 1>"$CAPTURE/out" 2>"$CAPTURE/err"
fi

case "$LOOP/$MODE" in
  macro/run)
    _ollama=$(value_of --ollama-url "$@")
    if [ -n "$_ollama" ]; then OLLAMA_URL="$_ollama" sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  macro/prove)    if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  macro/test)     sh "$ROOT/$TARGET" ;;
  micro/run)
    # Two ways in, and exactly one must be chosen: a packet you already have, or
    # a source the CLI ingests into one. Accepting both would silently pick a
    # winner, and accepting neither would reach trigger.sh with empty arguments.
    _packet=$(value_of --packet "$@")
    _source=$(value_of --source "$@")
    if [ -n "$_packet" ] && [ -n "$_source" ]; then
      fatal "--packet and --source are two ways to say the same thing; give one"
    fi
    _out=$(value_of --output "$@")
    if [ -n "$_source" ]; then
      _task=$(value_of --task "$@")
      [ -n "$_task" ] || fatal "--source needs --task: the seed repo is built to answer something"
      _ingest_dir="$ROOT/data/ingest/$(date -u +%Y%m%dT%H%M%SZ)"
      _kind=$(value_of --kind "$@")
      [ -n "$_kind" ] || _kind=dr
      _pid=$(value_of --packet-id "$@")
      if [ -n "$_pid" ]; then
        _packet=$(python3 "$HERE/ingest.py" packet --source "$_source" --task "$_task" \
          --kind "$_kind" --out "$_ingest_dir" --packet-id "$_pid") || exit $?
      else
        _packet=$(python3 "$HERE/ingest.py" packet --source "$_source" --task "$_task" \
          --kind "$_kind" --out "$_ingest_dir") || exit $?
      fi
      echo "loopctl: ingested $_source -> ${_packet#"$ROOT"/} (provenance beside it)"
      [ -n "$_out" ] || _out="$_ingest_dir/seed"
    fi
    [ -n "$_packet" ] || fatal "micro run needs --packet or --source"
    [ -n "$_out" ] || fatal "micro run needs --output"
    sh "$ROOT/$TARGET" "$_packet" "$_out" ;;
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
  notebooklm/run)
    # Values are read out first, then the argument list is rebuilt from scratch,
    # so nothing the contract does not name can ride through into the target.
    # Two ways in and exactly one must be chosen; that check lives in the target
    # rather than here, so a direct call and a call through the CLI get the same
    # refusal and the same exit code.
    _ntarget=$(value_of --target "$@")
    _title=$(value_of --notebook-title "$@")
    _stitle=$(value_of --source-title "$@")
    _nreg=$(value_of --registry "$@")
    _nout=$(value_of --out "$@")
    _ntimeout=$(value_of --timeout "$@")
    _follow=0; has_flag --follow "$@" && _follow=1
    _nb_dry=0; has_flag --dry-run "$@" && _nb_dry=1
    set --
    [ -n "$_ntarget" ] && set -- "$@" --target "$_ntarget"
    [ -n "$_title" ] && set -- "$@" --notebook-title "$_title"
    [ -n "$_stitle" ] && set -- "$@" --source-title "$_stitle"
    [ -n "$_nreg" ] && set -- "$@" --registry "$_nreg"
    [ -n "$_nout" ] && set -- "$@" --out "$_nout"
    [ -n "$_ntimeout" ] && set -- "$@" --timeout "$_ntimeout"
    [ "$_follow" -eq 1 ] && set -- "$@" --follow
    [ "$_nb_dry" -eq 1 ] && set -- "$@" --dry-run
    python3 "$ROOT/$TARGET" run "$@" ;;
  notebooklm/prove) if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  notebooklm/test)  if has_flag --live "$@"; then CONTROL_NOTEBOOKLM_LIVE=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  agent-runtime/run)
    _agent_offline=0; has_flag --offline "$@" && _agent_offline=1
    _agent_live=0; has_flag --live "$@" && _agent_live=1
    _agent_force=0; has_flag --force-receipt "$@" && _agent_force=1
    [ "$_agent_offline" -eq 1 ] && [ "$_agent_live" -eq 1 ] && fatal "agent-runtime run accepts --offline or --live, not both"
    [ "$_agent_force" -eq 1 ] && [ "$_agent_live" -ne 1 ] && fatal "--force-receipt applies only with --live"
    if [ "$_agent_live" -eq 1 ]; then
      if [ "$_agent_force" -eq 1 ]; then python3 "$ROOT/$TARGET" live --force-receipt; else python3 "$ROOT/$TARGET" live; fi
    elif [ "$_agent_offline" -eq 1 ]; then
      python3 "$ROOT/$TARGET" check --offline
    else
      python3 "$ROOT/$TARGET" check
    fi ;;
  agent-runtime/prove) if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  agent-runtime/test) sh "$ROOT/$TARGET" ;;
  ctg/run)
    _ctg_packet=$(value_of --packet "$@")
    _ctg_output=$(value_of --output "$@")
    sh "$ROOT/$TARGET" "$_ctg_packet" "$_ctg_output" ;;
  ctg/build-local)
    _ctg_manifest=$(value_of --manifest "$@")
    _ctg_output=$(value_of --output "$@")
    sh "$ROOT/$TARGET" "$_ctg_manifest" "$_ctg_output" ;;
  ctg/prove) if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  ctg/test) sh "$ROOT/$TARGET" ;;
  equivalence/run)
    _erequest=$(value_of --request "$@")
    _etarget=$(value_of --target-peer "$@")
    _esource=$(value_of --source-peer "$@")
    _eresult=$(value_of --research-result "$@")
    _elive=0; has_flag --execute-gemini "$@" && _elive=1
    set -- run --request "$_erequest" --target-peer "$_etarget"
    [ -n "$_esource" ] && set -- "$@" --source-peer "$_esource"
    [ -n "$_eresult" ] && set -- "$@" --research-result "$_eresult"
    [ "$_elive" -eq 1 ] && set -- "$@" --execute-gemini
    python3 "$ROOT/$TARGET" "$@" ;;
  equivalence/prove) if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;
  equivalence/test)
    _control_live=0; has_flag --live "$@" && _control_live=1
    _control_force=0; has_flag --force-receipt "$@" && _control_force=1
    if [ "$_control_live" -eq 1 ] && [ "$_control_force" -eq 1 ]; then
      CONTROL_EQUIVALENCE_LIVE=1 CONTROL_EQUIVALENCE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"
    elif [ "$_control_live" -eq 1 ]; then
      CONTROL_EQUIVALENCE_LIVE=1 sh "$ROOT/$TARGET"
    elif [ "$_control_force" -eq 1 ]; then
      CONTROL_EQUIVALENCE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"
    else
      sh "$ROOT/$TARGET"
    fi ;;
  *) fatal "no dispatch for $LOOP/$MODE — the contract lists it and this file does not (--selftest exists to catch exactly this)" ;;
esac
RC=$?

if [ "$JSON" -eq 1 ]; then
  exec 1>&3
  LOOPCTL_LOOP="$LOOP" LOOPCTL_MODE="$MODE" LOOPCTL_TARGET="$TARGET" \
  LOOPCTL_EXIT="$RC" LOOPCTL_CAPTURE="$CAPTURE" LOOPCTL_ROOT="$ROOT" \
    python3 "$HERE/result_json.py"
  exit "$RC"
fi

echo "loopctl: loop=$LOOP mode=$MODE target=$TARGET exit=$RC"
exit "$RC"
