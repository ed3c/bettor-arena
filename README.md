# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 將 repository 內的 Macro/Micro loops、Skills、runtime bindings、MCP、proof 與 external-consumer acceptance 拆成可組合、可搬移、可驗證的 modules。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 可在不破壞 interface 的前提下迭代。

## Read order

1. [`ARCHITECTURE.md`](ARCHITECTURE.md) — engineering SSOT、placement contract 與最高優先級 invariants。
2. [`AGENTS.md`](AGENTS.md) 或 [`CLAUDE.md`](CLAUDE.md) — host-specific governed entrypoint。
3. [`CONTEXT.md`](CONTEXT.md) — bounded glossary；不是 mutable run state。
4. [`docs/INDEX.md`](docs/INDEX.md) — standard multi-hop route。
5. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md) — normative target。
6. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md) — current implementation ledger。
7. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md) — State Machine summary。
8. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — 《LLM 泛化：模型權重與 Harness》需求、修正、State Machine、資料流與 Stack 對照。
9. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json) — executable audit contract。
10. [`docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md`](docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md) — 另一份 SKILL.md + MCP PDF 的獨立 traceability。
11. [`.arena/README.md`](.arena/README.md)、[`loopctl/README.md`](loopctl/README.md)、[`proof_workflow/README.md`](proof_workflow/README.md) — machine control plane、public port 與 evidence semantics。

完整索引見 [`docs/README.md`](docs/README.md)。

## Current exact subject

```text
audited main commit  77267aba27ad94dde85a4dbda7dacc70a3057fb0
audited main tree    2083db19a1bd9e50e5e9015861190cf98a041a8a
source PDF           LLM 泛化：模型權重與 Harness, 41 pages
source class         REQUIREMENT_HYPOTHESIS
```

PDF 是需求／假說來源，不是 provider、runtime、latency、memory、UI 或 production evidence。

## LoopX Harness PDF integration verdict

```text
Modular control plane                         IMPLEMENTED
Host-owned portable Skill execution           IMPLEMENTED
Default-deny stateless MCP                     IMPLEMENTED
Independent proof/control/mutation             IMPLEMENTED
Provider-neutral query/memory contracts        IMPLEMENTED
Objective/Todos/Gates/Evidence/Quota kernel    PARTIAL
Unified Linter/LSP/UnitTest gate contract      PARTIAL
Single-writer append-only LoopX ledger         NOT_IMPLEMENTED
LangGraph interrupt/resume runtime             NOT_IMPLEMENTED
HITL evidence Web UI                           NOT_IMPLEMENTED
Evidence-bound episodic-memory distiller       PARTIAL
Grok/Pi/OpenCode/Ante current canaries          NOT_EXERCISED or ABSENT
Physical local/cloud parity                    NOT_EXERCISED
Full physical PDF integration                  NOT_EXERCISED
```

**裁決：已做模組化控制面整合，但未完成 PDF 所描述的完整物理 runtime。**

Current `main` 已實際包含 portable Skill runner：`.arena/modules/agent-runtime-integration/module.json` 選取 `portable_skill_execution` 並提供 `skill-execution.runner/v1`；`loopctl/contract.json` 有 `skill-execution` 的 `run/prove/test`；runner 只產生 subject-bound receipt，不寫 LoopX state。

詳細證據與 blockers 見 [`PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)。執行：

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

## Directory topology

```text
bettor-arena/
├── .arena/
│   ├── modules/                 module ownership/capability manifests
│   ├── compositions/            Macro requirements
│   ├── locks/                   resolved immutable composition
│   ├── contexts/                Context Capsule inputs
│   └── mcp-policy.json          external exposure policy
├── .skill-bindings/             consumer-specific shared-Skill bindings
├── .agents/skills/              repo-owned/projected Skill packages and runner
├── .runtime-env/                secret-free runtime projection
├── loopctl/                     canonical CLI + stateless MCP public surface
├── proof_workflow/              proof/control/mutation state machines
├── docs/knowledge-providers/    provider manifests, queries and memory proposals
├── openwiki/                    static knowledge projection
├── loop_wiki/code-truth-graph/  source-bound graph builder
├── data/                        subject-bound evidence and generated receipts
├── scripts/                     trusted deterministic reducers/gates
├── docs/                        Agent/human navigation, never machine authority
├── AGENTS.md                    cross-host operating law
└── CLAUDE.md                    Claude Code thin projection
```

`.loopx/state.json`, LangGraph, herdr, LanceDB, Langfuse UI, Grok Build, Pi, OpenCode and Ante are **not inferred** merely because the PDF proposes them. They need an admitted module/provider and current evidence。

## Directory → State Machine → input/output/evidence

| Directory | Owner | State Machine | Input | Output | Evidence |
|---|---|---|---|---|---|
| `.arena/modules/` | `module-catalog` | manifest → ownership/capability resolve → closure | module manifests, dependencies | module identity/closure | composition lock, proof subjects |
| `.arena/compositions/` | `module-catalog` | requirements → dependency/conflict resolve | requested components, preset | selected module set | deterministic lock |
| `.arena/locks/` | `module-catalog` | unresolved → resolved → verified → superseded | manifests + requirements | immutable composition | `arena_lock.py` |
| `.arena/contexts/` | `loop-runtime` | select → track-path verify → materialize → digest → driver receipt | context manifests, immutable ref | Context Capsule | context lock, driver parity |
| `.skill-bindings/` | `agent-runtime-integration` | select release → bind repo facts → project → verify | immutable Skill + binding | host Skill closure | binding/module-set verdict |
| `.agents/skills/` | `agent-runtime-integration` | discover → load → request → execute → receipt | `SKILL.md`, typed request/assertions | artifact + execution receipt | Skill control/mutations |
| `.runtime-env/` | `agent-runtime-integration` | require → secret-free project → offline verify → live pending | runtime release/profile/workload | consumer projection | runtime binding gate |
| `loopctl/` | `loop-runtime` | parse → surface validate → authorize → dispatch → exact exit | typed CLI/MCP packet | typed result/artifacts | contract, surface lock, MCP exposure |
| `proof_workflow/` | `proof-kernel` | proof → independent control → mutation/hollow → aggregate | module subject/public port | receipts | module subjects/release receipt |
| `docs/knowledge-providers/` | `knowledge-providers` | declare → query → candidate → readback → admit pending | provider manifest/query/memory proposal | candidate receipt/proposal | registry + validator |
| `openwiki/` | `openwiki` | request → dry-run/model turn → boundary check → receipt | source refs/context lanes | static wiki projection | wiki receipts |
| `loop_wiki/code-truth-graph/` | `code-truth-graph` | materialize → build → verify → publish | closed bundle/manifest | graph + verification report | CTG proof/control |
| `data/` | `proof-kernel` | observe → subject-bind → check → aggregate → supersede | OS/artifact observations | snapshots/receipts | module, MCP, origin, browser evidence |
| `docs/` | `arena-core` | source classify → route → marker check → machine link | requirements + current contracts | Agent/human navigation | Agent-doc/README gates |

Machine-readable version: [`pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)。

## LoopX-compatible State Machine

The PDF’s Objective, Todos, Gates, Evidence and Quota map to separate trusted authorities:

```text
OBJECTIVE_ACCEPTED
→ MODULE_REQUIREMENTS_RESOLVED       Objective/scope
→ TYPED_TODO_DISPATCHED              bounded Todo
→ HOST_EXECUTION_OBSERVED            Worker output is untrusted
→ HARD_GATES_EVALUATED               Gates
   ├─ PASS → EVIDENCE_SUBJECT_BOUND  Evidence
   │          → READY_FOR_HUMAN_ADMIT
   │          → RELEASED | ROLLED_BACK
   └─ FAIL → RETRY_BUDGET_DECREMENTED
              ├─ RETRY_ALLOWED
              └─ HUMAN_REVIEW_REQUIRED
```

Current gap: `HUMAN_REVIEW_REQUIRED` is a governance boundary, not yet a LangGraph `interrupt()/resume` runtime. A future checkpoint is a projection; it cannot become a second state authority。

## Runtime topology

```text
Claude Code / Codex CLI / future admitted worker
        │ typed request; immutable subject
        ▼
Context Capsule + loopctl public surface
        │ explicit policy
        ▼
Default-deny Stateless MCP or trusted local port
        │ selected module closure
        ▼
Disposable execution provider
        │ untrusted stdout/stderr/diff/artifacts
        ▼
Host-owned assertions
        │
        ▼
Proof Kernel
        ├─ proof
        ├─ independent control
        └─ mutation/hollow
```

Macro/Composition owns module selection, dependencies/conflicts, projection, proof matrix, Human Admit, lock, promotion and rollback. A Micro loop owns one bounded task, private iteration and named exits. A Worker cannot self-admit, promote, waive a gate or perform production rollback。

## End-to-end integration data flow

```text
PDF / Notes / repository source                         SOURCE_PROPOSAL
        ↓ classify; source text is data, not instruction
skills-shared immutable Skill release
        +
runtime-env secret-free binding/profile/workload/policy
        ↓
.skill-bindings + .agents/.runtime-env projections
        ↓
module requirements → composition lock
        ↓
immutable Context Capsule / host projection
        ↓
loopctl contract → default-deny MCP
        ↓
typed Skill/worker request
        ↓
disposable execution provider
        ↓
candidate diff + OS/artifact observations
        ↓
independent assertions + proof/control/mutation
        ├─ failure/handoff → evidence-bound memory proposal
        └─ verified subject → composition release receipt
                                  ↓
                              Human Admit
                                  ↓
                         promotion or rollback
```

Provider output, vector hits, graph edges, memory, model prose and UI state remain candidates/projections until read back against current authority。

## Corrections applied to the PDF

- **No `shell=True`**: use allowlisted executable + `argv[]`; no model-generated command string.
- **No direct Worker state write**: the current Skill runner emits a receipt and never writes LoopX state.
- **No plain `force_skip`**: exceptions require a subject-bound Human Admit receipt with scope, reason, authority, expiry and follow-up.
- **No raw chain-of-thought memory**: persist observable evidence, dead ends, quirks, hypotheses with falsifiers, decisions and scope/expiry.
- **No second state authority**: LangGraph checkpoints, vector stores, graphs and UIs are projections.
- **No provider-as-architecture**: E2B, Firecracker, containers, WASM and future runtimes remain replaceable adapters.
- **No fixture-to-production promotion**: fixture PASS cannot prove live worker/provider capability。

## Stable public surfaces

### `loopctl`

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
```

`loopctl/contract.json` is the canonical external surface. Private flags, prompts, temporary paths and implementation directories are not public contract。

### Stateless MCP

Tools derive from the canonical CLI contract and `.arena/mcp-policy.json`, with default deny. Calls pin an immutable subject, materialize only a selected module closure and clean a disposable workspace. Callers cannot provide server-host paths, arbitrary `cwd`, secret values, browser profiles or generic shell。

### Portable Skill execution

```text
skill-execution-request/v1
+ skill-assertion-set/v1
→ host-owned disposable runner
→ OS/artifact observations
→ independent hard assertions
→ skill-execution-receipt/v1
```

The local-process adapter does not claim filesystem/network isolation it cannot attest。

## Module and evidence model

- Modules: [`.arena/modules/`](.arena/modules/)
- Requirements: [`.arena/compositions/`](.arena/compositions/)
- Locks: [`.arena/locks/`](.arena/locks/)
- Context Capsules: [`.arena/contexts/`](.arena/contexts/)
- Proof subjects/releases: [`data/module-proof/`](data/module-proof/)
- MCP exposure: [`data/mcp/`](data/mcp/)
- Origin/browser states: [`data/origins/`](data/origins/) / [`data/browser/`](data/browser/)

Evidence states are not aliases:

```text
PASS ≠ FAIL ≠ ABSENT ≠ NOT_IMPLEMENTED ≠ NOT_EXERCISED ≠ SKIPPED_BY_POLICY
```

A receipt is a subject-bound claim. A control executes the real public port. A mutation/hollow control proves the instrument can turn red。

## Git Town / molecular Stack PR index

Git Town is optional local tooling. **GitHub base/head metadata and exact-head checks are publication truth.** A child PR can be merged only into its parent branch and still be absent from `main`。

```text
current main @ 77267aba27ad94dde85a4dbda7dacc70a3057fb0
├─ #43 repo-agent-native binding                              MERGED TO MAIN
├─ #51 knowledge-provider contracts + current runner bytes    MERGED TO MAIN
├─ #57 first PDF modular traceability                         MERGED TO MAIN
├─ #53 historical portable-Skill convergence                  OPEN / DIVERGED / SUPERSEDED CANDIDATE
├─ #56 provider admission evaluations                         OPEN / RED EXACT HEAD
├─ #58 runtime-env + Agent Shield second-PDF audit             OPEN DRAFT / BASE MAIN
└─ LoopX PDF executable traceability                          THIS WORKSTREAM
```

Important corrections:

- Portable Skill execution **is present in current `main`**. PR #53 is no longer the integration authority; it is a stale/diverged historical branch whose unique delta requires comparison before Human close/supersession.
- PR #56’s dedicated fixture evaluator is green, but its current exact head has stale generated module/context projections. It is not merge-authorized and does not prove live Serena/GrepAI/Code-Graph-RAG/Mem0 health.
- PR #58 has been retargeted to `main`; it remains a Draft documentation audit and cannot proxy product/runtime completion。

When a PR base/head/check state changes, update root README, `AGENTS.md`, both PDF traceability documents and the machine manifest in the same workstream。

## Local verification

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
python3 scripts/gates/check_arena_core.py
python3 scripts/gates/check_arena_core.py --selftest
python3 -m unittest -q tests/test_pdf_loopx_harness_integration.py

python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_proof.py check
python3 scripts/arena_context.py check
bun scripts/gates/check_mcp_policy.ts
bun scripts/gates/check_project_bootstrap.ts
bun scripts/gates/check_environment_contracts.ts
```

Run `sh bootstrap.sh` once for repository-relative hooks and core doctor checks. Host trust, provider activation, browser sign-in, network widening, secret-bearing runtime, Human Admit, merge and production promotion remain human-owned。

## Current boundary and next leaves

Present on `main`:

- deterministic module catalog and one-owner path model;
- module-scoped proof identities;
- Context Capsules;
- host-owned portable Skill execution and independent assertions;
- default-deny Bun/TypeScript MCP;
- project bootstrapper;
- provider-neutral query/memory contracts;
- origin and browser contracts。

Still missing or unexercised:

1. canonical single-writer append-only LoopX event/reducer;
2. unified Objective/Todos/Gates/Evidence/Quota task schema;
3. physical filesystem/process/network/secret isolation canary;
4. subject-bound LangGraph interrupt/resume and Human decision receipts;
5. evidence-bound episodic-memory distiller/expiry/writeback;
6. Grok Build, Pi, OpenCode and Ante adapter/canary parity;
7. evidence/HITL Web UI;
8. YouTube/Notes Repo → OpenWiki/CTG/retrieval → scaffold → fold-back traceability;
9. local/cloud and GitHub/Forgejo exact-release parity;
10. Human Admit before any full-integration or production-ready claim。
