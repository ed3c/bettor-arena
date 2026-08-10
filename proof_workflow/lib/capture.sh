#!/bin/sh
# capture.sh — physical trace recorder shared by the control-group scripts.
#
# A proof receipt says which paths a traversal walked. That is a claim about
# structure. A control group instead RUNS the thing, and what it leaves behind
# has to be evidence that the run happened: the exact argv, the exit code, and
# both output streams as bytes on disk with a sha256 each. Nothing here
# summarises or interprets — interpretation belongs to the comparator.
#
# Sourced, never executed:
#   CAPTURE_HOME=<proof_workflow dir>; . "$CAPTURE_HOME/lib/capture.sh"
#   capture_init macro-entry          # sets RUN_ID, RUNDIR, creates them
#   capture bootstrap -- sh bootstrap.sh
#   $?  is the captured command's own exit code, passed through unchanged
#
# Layout under proof_workflow/data/<run_id>/:
#   run.jsonl              one record per executed command
#   streams/<seq>-<id>.out real stdout bytes
#   streams/<seq>-<id>.err real stderr bytes
#
# The directory is gitignored: gate output embeds this machine's absolute repo
# root, so committing it would either trip the root-coupling gate (§3 鐵律 2) or
# add one standing allowlist debt per run. The committed control receipt carries
# every stream's sha256 instead, which is what binds the trace to a commit.
#
# CAPTURE_CWD may be set before a call to run that one command somewhere else
# (a disposable worktree); it is recorded, so a trace never implies the wrong
# working tree.

capture_sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

capture_esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

capture_init() { # label
  CAPTURE_ROOT=$(git -C "${CAPTURE_HOME:?CAPTURE_HOME must be set before sourcing capture.sh}" \
    rev-parse --show-toplevel) || { echo "capture FATAL: not a git work tree" >&2; exit 64; }
  CAPTURE_COMMIT=$(git -C "$CAPTURE_ROOT" rev-parse HEAD)
  CAPTURE_SHORT=$(printf %.12s "$CAPTURE_COMMIT")
  mkdir -p "$CAPTURE_ROOT/proof_workflow/data"
  RUNDIR=$(mktemp -d "$CAPTURE_ROOT/proof_workflow/data/$(date -u +%Y%m%dT%H%M%SZ)-$CAPTURE_SHORT.XXXXXX") \
    || { echo "capture FATAL: could not allocate unique run directory" >&2; exit 64; }
  RUN_ID=${RUNDIR##*/}
  mkdir "$RUNDIR/streams"
  CAPTURE_SEQ=0
  # OrbStack redirects the docker CLI through a context, so `docker ps` works
  # while /var/run/docker.sock refuses — and OpenShell, which dials the socket
  # directly, fails with "Connection refused (os error 61)" on an otherwise
  # healthy machine. Selected HERE rather than in each control: three copies had
  # accumulated (the policy control, codex-sandbox.sh, automode-bench.sh) and the
  # fourth caller forgot, which is a shape problem, not a discipline one. Every
  # control already routes through capture_init, so forgetting becomes impossible.
  if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.orbstack/run/docker.sock" ]; then
    DOCKER_HOST="unix://$HOME/.orbstack/run/docker.sock"
    export DOCKER_HOST
  fi
  echo "control[$1] run_id=$RUN_ID commit=$CAPTURE_COMMIT"
}

capture() { # id -- cmd...
  _cid=$1
  shift
  [ "${1:-}" = "--" ] && shift
  CAPTURE_SEQ=$((CAPTURE_SEQ + 1))
  _cout="$RUNDIR/streams/$CAPTURE_SEQ-$_cid.out"
  _cerr="$RUNDIR/streams/$CAPTURE_SEQ-$_cid.err"
  _cargv=""
  for _ca in "$@"; do _cargv="$_cargv\"$(capture_esc "$_ca")\","; done
  _cwd=${CAPTURE_CWD:-$CAPTURE_ROOT}
  _cstarted=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  ( cd "$_cwd" && "$@" ) >"$_cout" 2>"$_cerr"
  _crc=$?
  printf '{"seq":%d,"id":"%s","utc":"%s","cwd":"%s","argv":[%s],"exit":%d,"stdout":{"path":"streams/%s","sha256":"%s","bytes":%s},"stderr":{"path":"streams/%s","sha256":"%s","bytes":%s}}\n' \
    "$CAPTURE_SEQ" "$_cid" "$_cstarted" \
    "$([ "$_cwd" = "$CAPTURE_ROOT" ] && echo repo-root || echo disposable-worktree)" \
    "${_cargv%,}" "$_crc" \
    "$(basename "$_cout")" "$(capture_sha256 "$_cout")" "$(wc -c <"$_cout" | tr -d ' ')" \
    "$(basename "$_cerr")" "$(capture_sha256 "$_cerr")" "$(wc -c <"$_cerr" | tr -d ' ')" \
    >>"$RUNDIR/run.jsonl"
  echo "  [ran] $_cid — exit $_crc"
  return "$_crc"
}

_capture_selftest() {
  CAPTURE_HOME=$(cd "$(dirname "$0")/.." && pwd -P)
  capture_init collision-a >/dev/null
  _first=$RUNDIR
  capture_init collision-b >/dev/null
  _second=$RUNDIR
  if [ "$_first" = "$_second" ]; then
    echo "SELFTEST RED: two same-HEAD allocations collided" >&2
    return 2
  fi
  echo "SELFTEST GREEN"
  return 0
}

case "$0" in
  */capture.sh) [ "${1:-}" = "--selftest" ] && _capture_selftest ;;
esac
