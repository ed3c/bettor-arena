#!/bin/sh
# Aggregate independent controls for both loops owned by agent-runtime-integration.
set -u
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
RED=0
sh "$ROOT/proof_workflow/control_agent_runtime_entry.sh" || RED=1
sh "$ROOT/proof_workflow/control_skill_execution_entry.sh" || RED=1
[ "$RED" -eq 0 ] && { echo "agent-runtime module control: PASS"; exit 0; }
echo "agent-runtime module control: FAIL" >&2
exit 2
