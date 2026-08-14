# LoopX Harness PDF → bettor-arena modular integration

> Source under review: **《LLM 泛化：模型權重與 Harness》**, 41 pages.
>
> Source class: `REQUIREMENT_HYPOTHESIS`. The PDF is an architecture proposal and example collection. It is not evidence that a provider, model, sandbox, memory layer, UI, latency target, resource figure, or workflow is present or healthy in this repository.
>
> Audited semantic baseline: `ed3c/bettor-arena@77267aba27ad94dde85a4dbda7dacc70a3057fb0`, tree `2083db19a1bd9e50e5e9015861190cf98a041a8a`. Current PR publication base: `main@9a5549e9994a7915201862a3e76be9906a4be13c`. The five intervening commits add only probe/NOOP files and do not alter the module/runtime evidence used by this audit.

Machine-readable contract:

```text
docs/architecture/pdf-loopx-harness.integration.json
docs/architecture/pdf-loopx-harness.integration.schema.json
scripts/gates/check_pdf_loopx_harness_integration.py
```

## Exact current verdict

```text
Modular control plane                         IMPLEMENTED
Host-owned portable Skill execution           IMPLEMENTED
Default-deny stateless MCP                     IMPLEMENTED
Independent proof/control/mutation             IMPLEMENTED
Provider-neutral query/memory boundaries       IMPLEMENTED
LoopX Objective/Todos/Gates/Evidence/Quota     PARTIAL
Unified fail-fast Linter/LSP/UnitTest contract PARTIAL
Single-writer append-only state ledger         NOT_IMPLEMENTED
LangGraph interrupt/resume runtime             NOT_IMPLEMENTED
HITL evidence Web UI                           NOT_IMPLEMENTED
Evidence-bound episodic-memory distiller       PARTIAL
Grok/Pi/OpenCode/Ante current canaries          NOT_EXERCISED or ABSENT
Physical local/cloud parity                    NOT_EXERCISED
Full PDF architecture integration              NOT_EXERCISED
```

The correct conclusion is **modularly integrated in part, not physically complete**.

Current `main` is already stronger than the PDF in several governance areas:

- module ownership is explicit and machine-checked;
- the external surface is generated from `loopctl/contract.json` and defaults deny;
- portable Skill execution is host-owned, takes typed argv, runs in a disposable worktree, evaluates independent assertions, emits a subject-bound receipt, and does not write LoopX state;
- proof, independent control, mutation/hollow evidence, provider state, origin state, browser state, and release state remain separate;
- Human Admit, promotion, exception authority, and production rollback are not model tools.

The repository does **not** claim that one `.loopx/state.json`, LangGraph checkpoint, vector store, graph database, or model transcript is the single source of truth.

## Requirement matrix

| ID | PDF pages | Requirement | Bettor owner / State Machine | Current state | Main blocker or correction |
|---|---:|---|---|---|---|
| `LX-01` | 1–2 | Agent-agnostic kernel: Objective, Todos, Gates, Evidence, Quota | `arena-core` + `loop-runtime` + `proof-kernel`; Macro/Micro/proof | `PARTIAL` | These concerns exist across typed contracts, locks, bounded loops and receipts; one append-only LoopX kernel contract is absent. |
| `LX-02` | 2–5 | Hard constraints replace model self-reporting | `agent-runtime-integration`; Skill execution | `IMPLEMENTED` | `run_portable_skill.py` accepts no raw shell and never writes state; Worker prose is evidence input, never verdict. |
| `LX-03` | 3–5 | Fail-fast Linter → LSP/type → Unit Test gates | `proof-kernel` + `arena-core`; Micro/proof | `PARTIAL` | Multiple deterministic gates exist, but no universal task-scoped multi-gate observation schema or LSP resource-pool contract exists. |
| `LX-04` | 5–7 | Quota exhaustion triggers HITL interrupt/resume | trusted Human Admit plane | `NOT_IMPLEMENTED` | No LangGraph checkpointer/`interrupt()`/resume receipt is present. A plain `force_skip` string is rejected as authority. |
| `LX-05` | 7–10 | Web UI for graph state, evidence, diff and HITL | observability projection | `NOT_IMPLEMENTED` | Evidence files exist; a LoopX/LangGraph evidence console does not. |
| `LX-06` | 10–11, 20–23, 35–39 | White-box and gray-box workers share one adapter | `agent-runtime-integration` + Context Capsule | `PARTIAL` | Claude/Codex surfaces exist; Grok Build, Pi, OpenCode and Ante require current-subject adapter/canary evidence. |
| `LX-07` | 11–16 | Monolithic micro-cell limits handoff loss | Macro/Micro + Context Capsule | `PARTIAL` | Bounded Micro loops and immutable capsules exist; a continuous-context cell and handoff-loss benchmark do not. |
| `LX-08` | 11–18 | Episodic memory carries dead ends and quirks | `knowledge-providers`; memory proposal | `PARTIAL` | Proposal-only memory is defined; distillation, retention, writeback and live cross-agent canaries are not admitted. |
| `LX-09` | 21–22, 32–33 | Single writer prevents worktree races | trusted reducer boundary | `PARTIAL` | Workers do not write state, but no canonical append-only LoopX event ledger exists. |
| `LX-10` | 18–24, 35–41 | Cloud/local separation and replaceable runtimes | `runtime-env` binding + environment contracts | `PARTIAL` | Secret-free projection exists; physical cloud/local and sandbox-provider canaries are not exercised. |
| `LX-11` | 24–33 | Worktree isolation, quotas, cleanup and GC | `loop-runtime` + Skill runner | `PARTIAL` | Disposable worktrees and cleanup controls exist; herdr/tmux orchestration, LSP pooling and system-wide GC do not. |
| `LX-12` | 31–35 | Notes/repositories compile to OpenWiki and precise retrieval | `openwiki` + seed factory + CTG | `PARTIAL` | Repository/document ingestion exists; YouTube multimodal ingest, LanceDB Notes Repo and bidirectional notes→code mapping remain incomplete. |
| `LX-13` | 31–41 | Serena/GrepAI/graph/memory are capability providers | `knowledge-providers` | `IMPLEMENTED` as contract | Results remain candidates until current source/test/receipt readback; live health is separate. |
| `LX-14` | 17–18, 33 | Prompt/Skill evolution uses evals and regression controls | `proof-kernel` + provider eval lane | `PARTIAL` | Deterministic controls exist; sealed holdout and cross-host live promotion are not complete on current `main`. |
| `LX-15` | 27–31 | CI/local simulation preserves exact-head evidence | `arena-core` + `proof-kernel` | `PARTIAL` | GitHub Actions exists; no admitted `nektos/act` parity receipt exists. |

The JSON manifest is the exact machine-readable form of this matrix. The verifier requires all 15 IDs, valid page ranges, existing module owners, existing repository paths, deterministic gate commands for `IMPLEMENTED` claims, and blockers for every non-complete state.

## Directory → State Machine → input/output/evidence

| Directory | Owner module | State Machine | Inputs | Outputs | Evidence |
|---|---|---|---|---|---|
| `.arena/modules/` | `module-catalog` | manifest → ownership/capability resolution → closure | `module.json`, dependency capabilities | module identity and closure | composition lock, proof subjects |
| `.arena/compositions/` | `module-catalog` | requirements → dependency/conflict resolution | requested modules/components, preset | selected component set | `.arena/locks/bettor-arena.lock.json` |
| `.arena/locks/` | `module-catalog` | unresolved → resolved → verified → superseded | manifests + requirements | immutable composition lock | `scripts/arena_lock.py` |
| `.arena/contexts/` | `loop-runtime` | select → verify tracked paths → materialize → freeze digest → driver receipt | root/loop manifests, immutable ref | Context Capsule lock and host projection | `.arena/contexts.lock.json`, driver parity |
| `.skill-bindings/` | `agent-runtime-integration` | select shared release → bind consumer facts → project → verify | immutable Skill release + repo binding | host-discoverable Skill closure | binding/module-set gates |
| `.agents/skills/` | `agent-runtime-integration` | discover → load → typed request → host execute → receipt | `SKILL.md`, scripts, schemas, request | candidate artifacts + execution receipt | Skill execution control |
| `.runtime-env/` | `agent-runtime-integration` | requirements → secret-free projection → offline verify → live canary pending | runtime release/profile/workload/policy | consumer projection and verdict | runtime binding gate |
| `loopctl/` | `loop-runtime` | parse → surface validate → policy authorize → dispatch → propagate exact exit | typed CLI/MCP request, immutable ref | typed result, artifact refs, exit code | contract, surface lock, MCP exposure |
| `proof_workflow/` | `proof-kernel` | proof → independent control → mutation/hollow → aggregate | module subject + public port + planted defect | proof/control/mutation receipts | module subjects and release receipt |
| `docs/knowledge-providers/` | `knowledge-providers` | declare → subject-bound query → candidate → source readback → admission pending | provider manifest/query/memory proposal | candidate receipt or memory proposal | registry + deterministic validator |
| `openwiki/` | `openwiki` | request validate → dry-run/model turn → boundary check → receipt | wiki request + source refs + context lanes | static knowledge projection | wiki-update receipts |
| `loop_wiki/code-truth-graph/` | `code-truth-graph` | materialize subject → build graph → verify → publish artifact | closed bundle or trusted manifest | graph + verification report | CTG proof/control |
| `data/` | `proof-kernel` | observe → bind subject → check → aggregate → retain/supersede | OS/artifact observations | snapshots and receipts | module proof, MCP, origin, browser records |
| `docs/` | `arena-core` | classify source → update route → check markers → link machine authority | sources/hypotheses + current contracts | Agent/human navigation | Agent-doc and README gates |

The root [`README.md`](../../README.md) carries the compact form because it is the first cold-start route. This document carries the audit detail. Machine ownership remains in `.arena/modules/*/module.json`.

## LoopX compatibility state machine

The PDF’s five nouns are translated into existing Bettor authorities rather than copied into one mutable JSON file:

```text
OBJECTIVE_ACCEPTED
  → MODULE_REQUIREMENTS_RESOLVED            # Objective / scope
  → TYPED_TODO_DISPATCHED                   # one bounded task
  → HOST_EXECUTION_OBSERVED                 # Worker output is untrusted
  → HARD_GATES_EVALUATED                    # Gates
      ├─ PASS → EVIDENCE_SUBJECT_BOUND      # Evidence
      │          → READY_FOR_HUMAN_ADMIT
      │          → RELEASED | ROLLED_BACK
      └─ FAIL → RETRY_BUDGET_DECREMENTED    # Quota
                 ├─ RETRY_ALLOWED
                 └─ HUMAN_REVIEW_REQUIRED
```

Current implementation boundary:

- `OBJECTIVE_ACCEPTED` through deterministic evidence binding is distributed across Macro/Micro, `loopctl`, the Skill runner and proof kernel.
- `HUMAN_REVIEW_REQUIRED` exists as a governance boundary, not a LangGraph runtime.
- `RELEASED` and `ROLLED_BACK` require a subject-bound receipt and Human Admit.
- No Worker can write `READY_FOR_HUMAN_ADMIT`, `RELEASED`, or `ROLLED_BACK`.

## End-to-end data flow

```text
PDF / note / repository source                     SOURCE_PROPOSAL
        ↓ classified, never obeyed as instruction
skills-shared immutable procedure
        +
runtime-env secret-free binding/profile/workload
        ↓
.skill-bindings + .agents/.runtime-env projections
        ↓
module requirements → deterministic composition lock
        ↓
immutable Context Capsule / host projection
        ↓
loopctl public contract → default-deny MCP or trusted local port
        ↓
typed Worker request
        ↓
Claude/Codex/current or future Grok/Pi/OpenCode/Ante adapter
        ↓
candidate diff / stdout / stderr / artifacts
        ↓
host-owned assertions + proof + independent control + mutation
        ├─ failure/handoff → evidence-bound memory proposal
        └─ verified subject → composition release receipt
                                  ↓
                              Human Admit
                                  ↓
                         promotion or rollback
```

A provider result, memory, graph edge, vector hit, model statement, or UI state is never promoted directly to release authority.

## Corrections to unsafe examples

### No `shell=True`

The PDF uses command strings with `subprocess.run(..., shell=True)` on pages 3–5. Bettor requires an allowlisted executable plus `argv[]`, exact environment, bounded output, timeout/process-group cleanup, and independent assertion results.

### No direct Agent state write

The PDF correctly argues that the Agent must not control completion, but several examples still write `.loopx/state.json` from wrapper logic. Bettor’s current portable Skill runner explicitly emits a receipt and never writes LoopX state. A future LoopX reducer must be the sole writer.

### No plain `force_skip`

The PDF’s HITL example accepts `force_skip` as a string. Bettor requires an exception/Human Admit receipt with exact subject, scope, reason, signer/authority, expiry, follow-up and rollback impact. A UI button cannot create authority by itself.

### No raw chain-of-thought persistence

The PDF proposes carrying the last Thought Stream between workers. Bettor does not persist private model reasoning. A handoff may persist only externally observable, evidence-bound material:

```text
observation
dead end + failure artifact
codebase quirk + source/readback
working hypothesis + falsifier
decision + rejected alternatives
open question
scope and expiry
```

### LangGraph is a projection, not a second state authority

A future LangGraph checkpoint may pause/resume orchestration, but it cannot compete with the trusted reducer, evidence ledger, release receipt or Human Admit.

### A cloud sandbox is a provider

E2B, Firecracker, OpenShell, Daytona, containers, WASM or another runtime may implement an execution-provider interface. None is required for the architecture to remain valid, and none is `PASS` before a current canary.

## Git Town / molecular Stack traceability

Git Town is optional local tooling. GitHub base/head metadata and exact-head checks are publication truth.

```text
current publication base main @ 9a5549e9994a7915201862a3e76be9906a4be13c
├─ #43 repo-agent-native binding                              MERGED TO MAIN
├─ #51 knowledge-provider contracts + current runner bytes    MERGED TO MAIN
├─ #57 first PDF modular traceability                         MERGED TO MAIN
├─ #53 historical portable-Skill convergence                  OPEN / DIVERGED / SUPERSEDED CANDIDATE
├─ #56 provider admission evaluations                         OPEN / RED EXACT HEAD
├─ #58 runtime-env + Agent Shield second-PDF audit             OPEN DRAFT / BASE MAIN
└─ #60 LoopX PDF executable traceability                      OPEN / MERGEABLE / HUMAN REVIEW
```

The portable Skill mechanism is present on current `main`: the module manifest selects `portable_skill_execution`, provides `skill-execution.runner/v1`, and the public contract contains `skill-execution` run/prove/test commands. PR #53 is therefore not the current integration authority. It is a stale/diverged historical convergence branch whose remaining unique delta must be compared before a Human closes or supersedes it.

PR #56’s dedicated fixture evaluator is green, but its current exact head has stale generated modular projections. It is not merge-authorized, and fixture PASS does not prove live Serena, GrepAI, Code-Graph-RAG or Mem0 capability.

PR #58 remains a Draft documentation audit. PR #60 is the current executable LoopX traceability leaf; exact-head checks must be rerun after every metadata or Context Capsule update. Human Admit owns merge, promotion and rollback.

Whenever a base/head or check state changes, update:

```text
README.md
AGENTS.md
this document
pdf-loopx-harness.integration.json
```

## Verification

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
python3 scripts/gates/check_arena_core.py
python3 scripts/gates/check_arena_core.py --selftest
python3 -m unittest -q tests/test_pdf_loopx_harness_integration.py
```

The verifier is zero-network. It checks:

- all 15 PDF requirement IDs and page ranges;
- allowed implementation states;
- current module IDs and repository paths;
- typed deterministic gate commands;
- blockers for every non-complete claim;
- directory/State Machine/input/output/evidence coverage;
- acyclic forward data flow with one explicit memory feedback edge;
- Stack snapshot invariants;
- root README/AGENTS/State Machine markers;
- current portable runner, `skill-execution.runner/v1`, stateless MCP and proof control/mutation mechanisms;
- positive plus planted negative controls.

It does not turn documentation consistency into a live-provider or production PASS.

## Remaining terminal leaves

1. Define a canonical single-writer append-only LoopX event/reducer contract.
2. Define task-scoped Objective/Todos/Gates/Evidence/Quota schemas and named transitions.
3. Add a physical execution-provider canary for filesystem, process, network, secret and cleanup isolation.
4. Add subject-bound LangGraph interrupt/resume and Human decision receipts without creating a second authority.
5. Add evidence-bound episodic-memory distillation, expiry, conflict and writeback controls.
6. Exercise Claude/Codex and each admitted white/gray worker on the same immutable cases.
7. Implement an evidence/HITL UI as a read projection.
8. Complete Notes Repo → OpenWiki/CTG/retrieval → scaffold → fold-back traceability.
9. Repair or supersede #53 and refresh #56’s generated projections.
10. Require Human Admit before any full-integration or production-ready claim.
