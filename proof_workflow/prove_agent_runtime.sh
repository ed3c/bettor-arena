#!/bin/sh
# Portable traversal proof for the aggregate Agent module set. Live carrier
# canaries are deliberately separate: hashed-not-run is not a live PASS.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init agent-runtime "consumer requirements -> resolved bindings -> aggregate offline gate"
prove_context architecture ARCHITECTURE.md "repo entry -> engineering placement and invariants"
prove_context integration-doc docs/agent-runtime-integration.md "Agent -> concrete update and verdict contract"
prove_harness module-set .agents/module-set.json "two upstream closures + two carriers -> aggregate interface"
prove_harness shared-requirements .agents/shared-skills.requirements.json "desired shared names -> resolver input"
prove_harness shared-binding .agents/bindings/bettor-arena.json "shared resolver -> pinned skill closure"
prove_harness runtime-requirements .runtime-env/requirements.json "desired runtime modules -> resolver input"
prove_harness runtime-binding .runtime-env/bindings/bettor-arena-local.json "runtime resolver -> pinned module closure"
prove_harness aggregate-gate scripts/agent_runtime.py \
  "module set -> offline closure verdict; adapter/live remain named absences" \
  -- python3 scripts/agent_runtime.py check --offline
prove_harness runtime-projection-gate scripts/gates/check_runtime_env_binding.py \
  "runtime binding/workload/policies/example -> consumer-local integrity verdict" \
  -- python3 scripts/gates/check_runtime_env_binding.py
prove_note live-carriers data/agent-runtime/live.json \
  "not fired by proof because it spends two real model turns; strict agent-runtime run requires a same-HEAD receipt and treats absence as NOT_EXERCISED"
prove_note control-owned-by-harness proof_workflow/control_agent_runtime_entry.sh \
  "independent fixture plants shared/runtime/Claude/Codex defects; harness proof owns control bytes"
prove_emit
