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
main commit at audit start: d291523856988cfa54316dba967fea8470194b72
main tree at audit start:   71d7b874dfd181e15d6b614cd6d3bf7fb47d8c43
convergence issue:          #38
convergence branch:         integration/pdf-harness-convergence-v1
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
| host-owned typed-argv Skill runner | `IMPLEMENTED` | six-host matrix `NOT_EXERCISED` | `agent-runtime-integration` |
| `repo-agent-native` consumer binding | `IMPLEMENTED` | provider degradation/live A/B separate | `.skill-bindings` |
| OpenWiki update/projection | `IMPLEMENTED` | full model turn subject-specific | `openwiki` |
| Code Truth Graph builder | `IMPLEMENTED` | runtime/production equivalence separate | `code-truth-graph` |
| Serena provider contract | `IMPLEMENTED` | live canary `NOT_EXERCISED` | `knowledge-providers` |
| GrepAI provider contract | `IMPLEMENTED` | live canary `NOT_EXERCISED` | `knowledge-providers` |
| Code-Graph-RAG provider contract | `IMPLEMENTED` | runtime `NOT_IMPLEMENTED` | `knowledge-providers` |
| Mem0 proposal-only contract | `IMPLEMENTED` | runtime/writeback `NOT_IMPLEMENTED` | `knowledge-providers` |
| fixture-only provider evaluator | active PR #56 | focused eval PASS; modular gates FAIL at observed head | PR #56 exact metadata/checks |
| immutable Agent Shield acceptance | contract target exists | issue #24 open; implementation `ABSENT` | issue #24 |

## PDF architecture status

| PDF area | State |
|---|---|
| modular control/evidence foundation | `IMPLEMENTED` |
| Objective/Todos/Gates/Evidence/Quota task kernel | `NOT_IMPLEMENTED` |
| append-only single-writer ledger and reducer | `NOT_IMPLEMENTED` |
| canonical quota/retry accounting | `NOT_IMPLEMENTED` |
| LangGraph strategy/HITL interrupt-resume | `NOT_IMPLEMENTED` |
| evidence-bound episodic-memory capsule | `NOT_IMPLEMENTED` |
| Grok/OpenCode/Pi/Codex/Claude/Ante live matrix | `NOT_EXERCISED` |
| Serena/GrepAI live canaries | `NOT_EXERCISED` |
| Code-Graph-RAG/Mem0 runtime | `NOT_IMPLEMENTED` |
| cloud/local same-workload canary | `NOT_EXERCISED` |
| Langfuse/OpenTelemetry plane | `NOT_IMPLEMENTED` |
| Harness evidence/HITL console | `NOT_IMPLEMENTED` |
| repo-level Git Town configuration | `ABSENT` |

Full matrix: [`pdf-harness-integration.matrix.json`](pdf-harness-integration.matrix.json).

## Integration drift observed at audit start

The baseline `main` tree selected `knowledge-providers` in
`.arena/compositions/bettor-arena.requirements.json`, but the checked
`.arena/locks/bettor-arena.lock.json` and
`data/module-proof/release-receipt.json` omitted it.

State:

```text
focused provider contract tests     PASS
coherent selected/locked/released   FAIL
```

This convergence branch must regenerate:

```text
.arena/locks/bettor-arena.lock.json
.arena/contexts.lock.json
data/context-capsules/driver-parity.json
data/module-proof/subjects.lock.json
data/module-proof/release-receipt.json
data/mcp/exposure.json
data/origins/status.json
data/browser/status.json
```

The branch is not mergeable by project policy until the desired, lock and release module sets agree and exact-head checks pass.

## Active molecular leaves

### Documentation/PDF convergence

```text
bettor-arena#37               MERGED
skills-shared#85              MERGED
runtime-env#30                MERGED
agent-shield-monorepo#78      MERGED
        ↓
bettor-arena#38               ACTIVE convergence owner
integration/pdf-harness-convergence-v1
```

### Provider evaluation

PR [`#56`](https://github.com/ed3c/bettor-arena/pull/56), observed head:

```text
770b0c8990843e958f7c1a345c3359a2d71eeb82

provider admission evaluator     PASS
portable execution contract      PASS
provider module integration      FAIL
modular contracts                FAIL
```

The observed sync failure names a Context Capsule directory entry rather than exact tracked files. The PR must fix that path model, regenerate projections and rerun exact-head checks. Fixture PASS is not provider admission.

### Historical aggregate

PR #53 remains open, diverged and non-mergeable. It is not a merge instruction. Any unique delta must be extracted into a clean terminal leaf.

### Agent Shield acceptance

Issue #24 remains open. Historical branch `feat/agent-shield-reference` is behind `main` and has zero unique commits; it is not implementation evidence.

Full topology: [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## Git Town status

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    ABSENT
molecular delivery semantics           IMPLEMENTED
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
Human Admit is explicit
```

The complete PDF architecture remains `NOT_IMPLEMENTED` until the missing LoopX, strategy/HITL, decision-memory, worker-fleet, runtime-fabric and observability leaves have executable evidence.
