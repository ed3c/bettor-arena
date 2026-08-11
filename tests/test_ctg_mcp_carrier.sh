#!/bin/sh
# Stable compatibility entrypoint for the Bun/TypeScript external MCP canary.
set -u
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
REF=${CTG_MCP_REF:-$(git -C "$ROOT" rev-parse HEAD)}
command -v bun >/dev/null 2>&1 || {
  echo "CTG MCP TEST FATAL: bun not on PATH" >&2
  exit 64
}
exec bun "$ROOT/tests/mcp_consumer_canary.ts" --ref "$REF"
