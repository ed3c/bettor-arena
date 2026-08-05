#!/bin/sh
# bootstrap — idempotent per-clone activation for bettor-arena.
#
# git cannot version core.hooksPath, and hook registration must never depend
# on where this tree was cloned. Everything here derives from this script's
# own location; rerunning is always safe.
#
# Exit codes: 0 activated · 64 missing tool or precondition (diagnosable,
# distinct from any gate's FAIL 2).
set -eu
ROOT=$(cd "$(dirname "$0")" && pwd)

fatal() { echo "bootstrap FATAL: $1" >&2; exit 64; }

git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1 \
  || fatal "not a git work tree: $ROOT (clone the repo, then run bootstrap)"

# Doctor: required tools fail loud and name themselves. A missing tool must
# never be readable as "checks passed".
command -v git >/dev/null 2>&1 || fatal "git not on PATH"
command -v python3 >/dev/null 2>&1 || fatal "python3 not on PATH (gates are Python)"
command -v bun >/dev/null 2>&1 || fatal "bun not on PATH (factory toolchain; install from https://bun.sh)"

# Relative hooksPath: valid from any checkout location, versioned hooks.
git -C "$ROOT" config core.hooksPath .githooks

python3 "$ROOT/scripts/gates/check_root_coupling.py" --selftest >/dev/null \
  || fatal "root-coupling gate selftest RED — do not trust its green"

echo "bootstrap OK: hooksPath=.githooks, doctor green (git/python3/bun)"

# MCP approval is a human gate. This script prints the steps and never
# performs them: auto-enabling project MCP servers would be self-approval.
cat <<'EOF'
MCP approval (human-owned, not automated):
  1. Claude Code: open this repo fresh; when prompted for the project .mcp.json
     servers (grepai / repo-context-pack / serena), review and approve yourself.
  2. Codex: .codex/config.toml ships only portable MCP declarations; add the
     host sections (permissions/network/sockets) by hand before trusting.
EOF
