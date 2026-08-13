#!/bin/sh
# Traversal proof for the host-owned portable Skill runner.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init skill-execution "typed request + independent assertions -> disposable worktree -> subject-bound receipt"
prove_context repo-context CONTEXT.md "repository route -> bounded authority and multi-hop documentation"
prove_context skill-context .agents/skills/harness-wiki/CONTEXT.md "harness-wiki route -> portable execution vocabulary and authority"
prove_context runner-design .agents/skills/harness-wiki/modules/portable-runner.md "public port -> isolation claims, named gaps and state boundary"
prove_harness request-schema .agents/skills/harness-wiki/contracts/skill-execution-request.schema.json "proposal -> closed executable/argv/sandbox subject"
prove_harness assertion-schema .agents/skills/harness-wiki/contracts/skill-assertion-set.schema.json "expected property -> independent hard/advisory assertion"
prove_harness receipt-schema .agents/skills/harness-wiki/contracts/skill-execution-receipt.schema.json "observed execution -> exact receipt shape"
prove_harness runner .agents/skills/harness-wiki/scripts/run_portable_skill.py \
  "exact Git subject -> local-process execution and independent assertion verdict" \
  -- python3 .agents/skills/harness-wiki/scripts/run_portable_skill.py selftest
prove_note physical-sandbox .arena/modules/agent-runtime-integration/README.md \
  "network deny and OS filesystem isolation remain NOT_EXERCISED in the local-process adapter; a physical sandbox adapter is required before either can be TESTED"
prove_note live-hosts .agents/skills/harness-wiki/modules/host-skill-compatibility.md \
  "Codex CLI, Claude Code, Grok Build, OpenCode, Pi and Ante live canaries remain separate; portable runner PASS is not a host/provider PASS"
prove_note independent-control proof_workflow/control_skill_execution_entry.sh \
  "drives the public loopctl path with one positive and ten planted defects"
prove_emit
