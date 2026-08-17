# Modular integration status

This is the mutable implementation ledger for the exact checked-out tree. The normative target remains [`modular-integration-requirements.md`](modular-integration-requirements.md). The attached PDF remains a source proposal, and its current mapping is [`PDF_HARNESS_INTEGRATION_AUDIT.md`](PDF_HARNESS_INTEGRATION_AUDIT.md).

Evidence states:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

`IMPLEMENTED` below means mechanism bytes and deterministic contracts exist. It does not mean a live external subject has passed.

## Audit baseline

```text
repository: ed3c/bettor-arena
local/Forgejo main: 8d47fc1c9dfd1550c1f45504f6c11fc1f04f6a0b
GitHub main:        c72109e145193fdaf059944403477f01064a1c3d
shared tree:        0c51ea279bd2036dce281898c2e980e8378ba1cb
queue head:         order 12 / issue #92
convergence issue:  #68
```

## Current implementation ledger

| Capability / component | Mechanism state | Live / exact-subject state | Authority |
|---|---|---|---|
| root Agent/document routing | `IMPLEMENTED` | current tree checked by document gates | `AGENTS.md`, contracts |
| module catalog and path ownership | `IMPLEMENTED` | exact lock must be current | `.arena/modules`, composition/ownership gates |
| composition requirements and deterministic lock | `IMPLEMENTED` | audit-start `main` lock was stale | requirements + generated lock |
| Context Capsules | `IMPLEMENTED` | live six-host canaries `NOT_EXERCISED` | `.arena/contexts`, context receipts |
| module closure proof identity | `IMPLEMENTED` | release aggregate may remain `NOT_EXERCISED` | `proof-kernel`, `data/module-proof` |
| default-deny stateless MCP | `IMPLEMENTED` | external consumers subject-specific | `loopctl`, MCP policy |
| transactional project bootstrap | `IMPLEMENTED` | external target subject-specific | `project-bootstrapper` |
| GitHub/Forgejo logical-origin contract | `IMPLEMENTED` | current equivalence canary `NOT_EXERCISED` unless receipt exists | `environment-contracts` |
| Browser Contract v2 | `IMPLEMENTED` | signed-in/live routes subject-specific | `environment-contracts` |
| portable Skill contracts | `IMPLEMENTED` | host discovery/live behavior separate | `harness-wiki` |
| universal Skill measurement binding | `IMPLEMENTED` | five-archetype protocol conformance `PASS`; repo-agent-native physical v2 `NOT_EXERCISED` | `skills-shared` closure + consumer binding receipt |
| host-owned typed-argv Skill runner | `IMPLEMENTED` | six-host matrix `NOT_EXERCISED` | `agent-runtime-integration` |
| `repo-agent-native` consumer binding | `IMPLEMENTED` | provider degradation/live A/B separate | `.skill-bindings` |
| OpenWiki update/projection | `IMPLEMENTED` | full model turn subject-specific | `openwiki` |
| Code Truth Graph builder | `IMPLEMENTED` | runtime/production equivalence separate | `code-truth-graph` |
| Serena provider contract | `IMPLEMENTED` | live canary `NOT_EXERCISED` | `knowledge-providers` |
| GrepAI provider contract | `IMPLEMENTED` | live canary `NOT_EXERCISED` | `knowledge-providers` |
| Code-Graph-RAG provider contract | `IMPLEMENTED` | runtime `NOT_IMPLEMENTED` | `knowledge-providers` |
| Mem0 projection contract/runtime | `IMPLEMENTED` | final selection/live use subject-specific | `loopx-decision-memory` |
| fixture-only provider evaluator | `IMPLEMENTED` | live provider convergence remains behind #92 | PR #56 + current machine queue |
| immutable Agent Shield acceptance | contract target exists | issue #24 open; implementation `ABSENT` | issue #24 |
| LoopX Contract/Ledger/Strategy/Gateway mechanisms | `IMPLEMENTED` | not selected into release composition | module manifests + terminal PRs |
| Runtime Fabric/Fleet/GC/LSP mechanisms | `IMPLEMENTED` | physical/live subjects remain scoped or `NOT_EXERCISED` | module manifests + queue |
| Notes/knowledge/context/evolution mechanisms | `IMPLEMENTED` | later ordered acceptance blocked behind #92 | module manifests + queue |
| Observability/Console/benchmark mechanisms | `IMPLEMENTED` | final live/release admission pending | module manifests + queue |
| Git Town typed controller | `IMPLEMENTED` | 13 physical controls PASS; executable `ABSENT` | `scripts/git-town`, `tests/git-town` |

## PDF architecture status

| PDF area | State |
|---|---|
| modular control/evidence foundation | `IMPLEMENTED` |
| Objective/Todos/Gates/Evidence/Quota task kernel | mechanism `IMPLEMENTED`; release not selected |
| append-only single-writer ledger and reducer | mechanism `IMPLEMENTED`; release not selected |
| canonical quota/retry accounting | mechanism `IMPLEMENTED`; live end-to-end not exercised |
| Strategy/HITL interrupt-resume | mechanism `IMPLEMENTED`; live end-to-end not exercised |
| evidence-bound decision-memory lifecycle | mechanism `IMPLEMENTED`; final composition pending |
| Grok/OpenCode/Pi/Codex/Claude/Ante live matrix | `NOT_EXERCISED` |
| Serena/GrepAI live canaries | `NOT_EXERCISED` |
| Code-Graph-RAG runtime | `NOT_EXERCISED`; issue #41 open |
| Mem0 projection mechanism | `IMPLEMENTED`; live/runtime admission subject-specific |
| cloud/local same-workload canary | `NOT_EXERCISED` |
| observability projection | mechanism `IMPLEMENTED`; external backend/live subject-specific |
| Harness evidence/HITL console | mechanism `IMPLEMENTED`; release/live subject-specific |
| repo-level Git Town configuration | `ABSENT` |

Full matrix: [`pdf-harness-integration.matrix.json`](pdf-harness-integration.matrix.json).

## Selected-composition boundary

The desired lock and aggregate release receipt currently contain the same 14 base modules. That coherence is narrower than the PDF target: catalogued LoopX terminal modules are deliberately not selected, and every aggregate module proof/control/mutation lane is `NOT_EXERCISED`. Issue #68 owns any final selection and receipt regeneration.

## Active molecular leaves

### Ordered terminal head

```text
orders 0–11       COMPLETE
order 12 / #92    ACTIVE — live Serena/GrepAI canaries
order 13 / #41    BLOCKED_BY_PREDECESSOR
order 25 / #68    FINAL_CONVERGENCE
```

Later implementation PRs may already be merged. The queue state remains blocked until predecessor acceptance settles; issue/PR closure is not a substitute.

### Agent Shield acceptance

Issue #24 remains open. Historical branch `feat/agent-shield-reference` is behind `main` and has zero unique commits; it is not implementation evidence.

Full topology: [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## Git Town status

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    NOT_SELECTED
typed admission/controller mechanism  IMPLEMENTED
13 physical controls                  PASS with executable-absent lane
actual Git Town execution             NOT_EXERCISED
```

Do not claim Git Town configuration. The issue/PR policy still distinguishes sibling, true child, terminal and convergence roles.

## Verification

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
bun scripts/gates/check_mcp_policy.ts
bun scripts/gates/check_project_bootstrap.ts
bun scripts/gates/check_environment_contracts.ts
```

## Completion condition

The modular foundation may be described as coherent only when:

```text
requirements module IDs == lock module IDs == release-receipt module IDs
all tracked paths have one owner or reviewed class
all required Context Capsule paths are exact tracked files
all selected module proof/control/mutation subjects are generated
all applicable exact-head checks pass
remaining live/non-live states are named
automated admission is explicit
```

The complete PDF architecture is not yet admitted. Its principal mechanism leaves now exist; the remaining blockers are strict queue acceptance from #92 onward, final module selection, exact-subject proof/control/mutation aggregation, live host/provider/runtime canaries, origin receipt refresh and #68 release/rollback admission.
