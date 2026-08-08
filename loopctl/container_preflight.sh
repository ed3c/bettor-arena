#!/bin/sh
# container_preflight.sh — is this container actually able to serve the CLI?
#
#   sh loopctl/container_preflight.sh
#
# Run this INSIDE the container before wiring an MCP server to it. Everything it
# checks is something that, when missing, fails later as a different-looking
# error: an unauthenticated driver looks like a model refusal, an absent git
# identity looks like a broken worktree, a read-only mount looks like a gate bug.
#
# The one that matters most and cannot be checked from outside: both drivers need
# an AUTHENTICATED subscription session. A container that has the binary but no
# session will run, print something, and fail in a way that reads like the prompt
# was wrong. So the driver checks here do not test `--version`; they spend one
# real turn and require an answer back. A binary that is present but cannot
# answer is reported as present-but-unauthenticated, which is a different fix
# from absent.
#
# Nothing here is fatal by itself except the deterministic base: the drivers are
# reported per role, because the read-only roles and the writing role are allowed
# to come from different hosts and a container may legitimately serve only one.
#
# Exit: 0 ready for the roles it reports · 2 the deterministic base is broken
#       64 not a work tree / no CLI here
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null) || {
  echo "preflight FATAL: not inside a git work tree — the CLI resolves everything from the repo root" >&2
  exit 64; }

RED=0
say() { printf '  %-28s %s\n' "$1" "$2"; }
bad() { printf '  %-28s %s\n' "$1" "$2" >&2; RED=1; }

echo "preflight: root=$ROOT"

# --- deterministic base: without these nothing else is worth checking --------
for tool in git python3 bun; do
  if command -v "$tool" >/dev/null 2>&1; then
    say "$tool" "$(command -v "$tool")"
  else
    bad "$tool" "ABSENT — the loops' own doctor exits 64 without it"
  fi
done

# A container often has git but no identity, and `git worktree add` then works
# while any commit inside it fails. The isolation model depends on worktrees, so
# this is checked by really making one.
WT=$(mktemp -d "${TMPDIR:-/tmp}/preflight.XXXXXX")/probe
if git -C "$ROOT" worktree add --detach "$WT" HEAD >/dev/null 2>&1; then
  say "git worktree add" "ok (isolation model is available)"
  git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1
else
  bad "git worktree add" "FAILED — every external call is meant to run in its own worktree"
fi

# --- the CLI's own surface ---------------------------------------------------
if sh "$HERE/loopctl.sh" --selftest >/dev/null 2>&1; then
  say "loopctl --selftest" "GREEN"
else
  bad "loopctl --selftest" "RED — the surface and its wiring disagree here"
fi
if sh "$HERE/loopctl.sh" macro prove --force-receipt --json >/dev/null 2>&1; then
  say "loopctl --json" "produces a result"
else
  bad "loopctl --json" "FAILED — a wrapper would have to parse human output"
fi

# --- drivers: presence is not readiness --------------------------------------
# One real turn each. `--version` proves the binary exists and nothing about
# whether it can answer, which is the failure this section exists to separate.
probe_driver() { # label, command...
  _label=$1; shift
  if ! command -v "$1" >/dev/null 2>&1; then
    say "$_label" "absent — this container cannot serve that role"
    return 0
  fi
  _out=$("$@" 2>&1)
  _rc=$?
  if [ "$_rc" -eq 0 ] && [ -n "$_out" ]; then
    say "$_label" "authenticated (answered a real turn)"
  else
    bad "$_label" "present but NOT authenticated (exit $_rc) — this fails later looking like a model refusal, not like a missing session"
  fi
}
probe_driver "claude -p (writing role)" claude -p --model sonnet "Reply with the single word: ready"
probe_driver "codex exec (read-only role)" codex exec -s read-only --skip-git-repo-check --ephemeral "Reply with the single word: ready"

# --- prompt cache reality check ----------------------------------------------
echo "  note: cache reuse needs a LIVE session and a stable prefix. A server that"
echo "        starts a fresh process per call gets none of it — keep the server"
echo "        long-lived and isolate each call with a worktree instead, or the"
echo "        fixed context lane is re-billed on every request."

if [ "$RED" -eq 0 ]; then
  echo "PASS: this container can serve the CLI for the roles reported above"
  exit 0
fi
echo "FAIL: fix the lines on stderr before pointing an MCP server at this container" >&2
exit 2
