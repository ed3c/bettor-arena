# Bettor Arena traceability index

## Purpose

Trace every significant architecture or delivery claim through:

```text
source / incident
→ decision / target
→ current status
→ parent issue
→ molecular terminal PR
→ eval and negative control
→ immutable implementation subject
→ runtime/consumer receipt
→ convergence index
→ Human Admit
```

A missing edge remains explicit. This index routes to machine authority; it is not a second receipt registry.

## PDF Harness trace

| Layer | Route |
|---|---|
| source proposal | attached 41-page **LLM 泛化：模型權重與 Harness** PDF; repository copy `ABSENT` |
| human audit | [`../architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](../architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) |
| machine matrix | [`../architecture/pdf-harness-integration.matrix.json`](../architecture/pdf-harness-integration.matrix.json) |
| directory/state ownership | [`../architecture/DIRECTORY_STATE_MACHINE_MAP.md`](../architecture/DIRECTORY_STATE_MACHINE_MAP.md) |
| normative modular target | [`../architecture/modular-integration-requirements.md`](../architecture/modular-integration-requirements.md) |
| mutable status | [`../architecture/modular-integration-status.md`](../architecture/modular-integration-status.md) |
| state machines | [`../architecture/STATE_MACHINES.md`](../architecture/STATE_MACHINES.md) |
| molecular delivery | [`STACK_PR_INDEX.md`](STACK_PR_INDEX.md) |
| executable audit | [`../../scripts/gates/check_pdf_harness_integration.py`](../../scripts/gates/check_pdf_harness_integration.py) |
| convergence owner | [`bettor-arena#38`](https://github.com/ed3c/bettor-arena/issues/38) |

Current conclusion:

```text
supporting modular Harness foundation   IMPLEMENTED
complete PDF/LoopX architecture         NOT_IMPLEMENTED
```

## Four-repository documentation subjects

| Repository | PR | Merge commit | Relation |
|---|---|---|---|
| `bettor-arena` | [`#37`](https://github.com/ed3c/bettor-arena/pull/37) | `1f94d3d77992a1396959a15b2ada7836c07bf300` | independent sibling |
| `skills-shared` | [`#85`](https://github.com/ed3c/skills-shared/pull/85) | `e3b327ad49c088f1962c33167ecd5ac9d28125fb` | independent sibling |
| `runtime-env` | [`#30`](https://github.com/ed3c/runtime-env/pull/30) | `4a333ccf106ef60bc6942b922b7f5efffb3876f5` | independent sibling |
| `agent-shield-monorepo` | [`#78`](https://github.com/ed3c/agent-shield-monorepo/pull/78) | `1af04c1ef5cb68eab198987feba008c93d3ec22f` | independent sibling |
| `bettor-arena` | [`#38`](https://github.com/ed3c/bettor-arena/issues/38) | branch `integration/pdf-harness-convergence-v1` | convergence owner |

The four blockers for #38 are merged. Fresh Claude/Codex cold-start and cross-environment checks remain separate from the documentation bytes.

## Machine authority routes

| Subject | Machine authority | Human route |
|---|---|---|
| placement | [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) | root README |
| module contract | [`.arena/modules/*/module.json`](../../.arena/modules/) | [module catalog README](../../.arena/modules/README.md) |
| composition desired state | [`.arena/compositions/`](../../.arena/compositions/) | [`.arena/README.md`](../../.arena/README.md) |
| resolved composition | [`.arena/locks/bettor-arena.lock.json`](../../.arena/locks/bettor-arena.lock.json) | modular status |
| context selection | [`.arena/contexts/`](../../.arena/contexts/) | directory state map |
| public CLI | [`../../loopctl/contract.json`](../../loopctl/contract.json) | [`loopctl/README.md`](../../loopctl/README.md) |
| proof semantics | [`../../proof_workflow/`](../../proof_workflow/) | proof README |
| release aggregate | [`../../data/module-proof/release-receipt.json`](../../data/module-proof/release-receipt.json) | modular status |
| provider contracts | [`../knowledge-providers/`](../knowledge-providers/) | provider README |
| Skill execution | `harness-wiki` schemas/runner | agent runtime docs |
| molecular topology | GitHub metadata | [`STACK_PR_INDEX.md`](STACK_PR_INDEX.md) |

## Modular implementation trace

```text
module catalog #4
→ ownership #8
→ proof subjects #10
→ Context Capsules #12
→ stateless MCP #15/#21
→ project bootstrap #22
→ origins/browser #23
→ README/status convergence #29
```

Exact PR relations and states: [`STACK_PR_INDEX.md`](STACK_PR_INDEX.md).

## Skill/runtime/provider trace

```text
repo-agent consumer binding #43
→ portable Skill contract #48
→ host-owned runner #50
→ provider contracts #51
→ fixture-only paired evaluator #56
```

Current provider state:

```text
Serena live                  NOT_EXERCISED
GrepAI live                  NOT_EXERCISED
Code-Graph-RAG runtime       NOT_IMPLEMENTED
Mem0 runtime/writeback       NOT_IMPLEMENTED
provider winner              NOT_EXERCISED
```

Universal measurement protocol trace:

```text
skills-shared@3d3c179d773e251ad1ae49c9453e428784219f00
→ Forgejo feature branch feat/repo-agent-native-v2-ab (not canonical release)
→ measurement closure 306e01a0b5741a18579956917359233484b7b1410d039133cf8ce51425b9cbc6
→ five archetypes / 23 catalogued Skills / 20 of 20 protocol mutations killed
→ data/receipts/skill-measurement-universal-v2-dev.json
→ repo-agent-native legacy behavior FAIL
→ repo-agent-native physical v2 NOT_EXERCISED
→ Human Admit remains required
```

PR #56 has a focused evaluator PASS but observed modular-contract failures. It cannot be promoted until exact lock/context/proof projections are current.

## Stale and absent subjects

| Subject | State | Trace rule |
|---|---|---|
| PR #53 | open, diverged, non-mergeable | extract unique delta; do not merge aggregate |
| PR #52 | merged to non-main feature base | not `main` release identity |
| PR #55 | closed unmerged | not implementation evidence |
| issue #24 | open | Agent Shield acceptance remains pending |
| `feat/agent-shield-reference` | behind main, zero unique commits | not issue #24 implementation |
| `.loopx/` | `ABSENT` | complete LoopX kernel not implemented |
| LangGraph/HITL package | `ABSENT` | strategy/interrupt state machine not implemented |
| Git Town config | `ABSENT` | molecular terms do not prove CLI configuration |
| observability/UI package | `ABSENT` | no Langfuse/OTel/HITL console authority |

## Git Town and molecular topology

Observed repository configuration:

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
git-town-stacked-pr-worker selected    ABSENT
```

Use [`../agents/issue-tracker.md`](../agents/issue-tracker.md) for sibling/true-child/terminal/convergence semantics. Current exact branch/PR graph lives in [`STACK_PR_INDEX.md`](STACK_PR_INDEX.md).

## Evidence rules

- `IMPLEMENTED` means mechanism bytes and contracts exist.
- `PASS` means an executed exact subject passed the named gate.
- `NOT_EXERCISED` means the mechanism or declaration exists but the exact run does not.
- `ABSENT` means the required artifact/route/provider is unavailable.
- `NOT_IMPLEMENTED` means the target mechanism is not present.
- `FAIL` is preserved even when another focused check passes.
- fixture evidence proves evaluator behavior only.
- old green checks do not move with a changed head.
- Markdown links and source diagrams are navigation/evidence inputs, not runtime receipts.

## Required update events

Update this index and [`STACK_PR_INDEX.md`](STACK_PR_INDEX.md) when:

```text
a documentation sibling merges
a terminal/convergence PR opens, rebases, changes head or closes
a generated lock/release set changes
a PDF matrix component changes state
a live host/provider/cloud canary lands
issue #24 gains an implementation subject
Git Town configuration or selected Skill appears
Human Admit promotes or rolls back
```
