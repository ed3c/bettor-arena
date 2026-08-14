# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 把散落的小迴圈收斂成可組合、可證明、可發布的 modules。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 可以在不破壞既有 interface 的前提下快速迭代。

## PDF Harness Integration verdict

The attached 41-page **LLM 泛化：模型權重與 Harness** PDF is a source proposal. It proposes a complete LoopX state kernel, deterministic gates, LangGraph HITL, white/gray-box workers, episodic memory, OpenWiki/AST/LSP, worktree fleets, cloud/local runtime, observability and a Web console.

Current repository verdict:

```text
modular control-plane foundation                IMPLEMENTED
hard gates / proof / control / mutation         IMPLEMENTED
portable Skill → host-owned execution           IMPLEMENTED
Context Capsules / OpenWiki / Code Truth        IMPLEMENTED
provider-neutral query and memory contracts     IMPLEMENTED

complete LoopX task-state kernel                NOT_IMPLEMENTED
single-writer event ledger and reducer          NOT_IMPLEMENTED
Objective / Todos / Quota canonical state       NOT_IMPLEMENTED
LangGraph strategy + HITL interrupt/resume      NOT_IMPLEMENTED
evidence-bound episodic memory                  NOT_IMPLEMENTED
six-host live execution matrix                  NOT_EXERCISED
cloud/local equivalent execution                NOT_EXERCISED
Langfuse / OpenTelemetry / Harness console      NOT_IMPLEMENTED
```

The correct conclusion is:

> Bettor modularly integrates much of the PDF's supporting Harness foundation, but it does **not** yet integrate the complete PDF architecture.

Read the exact mapping, rejected source shortcuts, gaps and acceptance criteria in
[`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md).
The machine companion is
[`docs/architecture/pdf-harness-integration.matrix.json`](docs/architecture/pdf-harness-integration.matrix.json).

## Read order

1. [`AGENTS.md`](AGENTS.md) or [`CLAUDE.md`](CLAUDE.md) — mandatory cross-host entry.
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — engineering SSOT, placement contract and invariants.
3. [`CONTEXT.md`](CONTEXT.md) — current handoff and stable vocabulary.
4. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) — PDF proposal versus current repository.
5. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md) — directory owners, transitions, inputs and outputs.
6. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md) — normative target.
7. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md) — mutable implementation ledger.
8. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md) — molecular terminal/convergence topology.
9. [`.arena/README.md`](.arena/README.md), [`loopctl/README.md`](loopctl/README.md) and [`proof_workflow/README.md`](proof_workflow/README.md) — machine control, public surface and evidence semantics.

Complete navigation: [`docs/README.md`](docs/README.md).

## Directory → State Machine ownership

<!-- PDF_HARNESS_MATRIX_START -->

| Directory / route | Owner | State machine responsibility | Current state |
|---|---|---|---|
| root `*.md` | `arena-core` | `ENTRY → ROUTE → OWNER → CONTRACT → EVIDENCE` | `IMPLEMENTED` |
| `.agents/` | `agent-runtime-integration` | Skill requirements, immutable binding and host projection | `IMPLEMENTED` |
| `.skill-bindings/` | consumer binding | shared procedure → repository domain route/assertions | `IMPLEMENTED` |
| `.runtime-env/` | `environment-contracts` consumer projection | declare → resolve → materialize → offline verify → live canary | mechanism `IMPLEMENTED` |
| `.arena/modules/` | `module-catalog` | proposed → contracted → composed → proved → released | `IMPLEMENTED` |
| `.arena/compositions/` | `module-catalog` | desired modules → capability/dependency/conflict resolution | `IMPLEMENTED` |
| `.arena/locks/` | generated control plane | requirements → deterministic composition lock | mechanism `IMPLEMENTED`; exact bytes must be current |
| `.arena/contexts/` | `loop-runtime` and module owners | select → materialize → freeze → driver prepare → canary | offline `IMPLEMENTED`; live hosts vary |
| `loopctl/` | `loop-runtime` | parse → validate → dispatch public port → propagate `0/2/64` | `IMPLEMENTED` |
| `mcp/` | `mcp-adapters` | default deny → typed tool projection → disposable call → cleanup | `IMPLEMENTED` for admitted tools |
| `proof_workflow/` | `proof-kernel` | claim → physical traversal → independent control → mutation → receipt | `IMPLEMENTED` |
| `data/module-proof/` | generated evidence | module closure subjects → release aggregation | mechanism `IMPLEMENTED`; release evidence may be `NOT_EXERCISED` |
| `loop_wiki/evolve-perfect-seed-repo-factory/` | `perfect-seed-factory` | packet → build → quality/operator/validator → Human edge | `IMPLEMENTED` |
| `kb-ingest/`, `openwiki/` | `openwiki` | request → dry/full opt-in → verify → projection/receipt | `IMPLEMENTED` mechanism |
| `loop_wiki/code-truth-graph/` | `code-truth-graph` | closed packet → parse/build → graph/result artifacts | `IMPLEMENTED` |
| `docs/knowledge-providers/` | `knowledge-providers` | manifest → bounded query/proposal → source readback → Human Admit | contracts `IMPLEMENTED`; live providers vary |
| `notebooklm/` | `notebooklm` | target → resolve/auth → read/follow → scratch cleanup → receipt | mechanism `IMPLEMENTED` |
| `scripts/gates/`, `tests/` | `arena-core` / `proof-kernel` | positive → hollow/mutation → exact-tree verdict | `IMPLEMENTED` |
| `.github/workflows/` | cloud verifier | event → exact checkout → deterministic gate → status | `IMPLEMENTED` |
| `.loopx/` | proposed LoopX owner | Objective/Todos/Gates/Evidence/Quota → reducer/ledger | `NOT_IMPLEMENTED` |
| LangGraph/HITL package | proposed strategy plane | propose command → interrupt/resume → decision receipt | `NOT_IMPLEMENTED` |
| worker fleet | proposed execution plane | probe → lease → materialize → execute → collect → dispose | live matrix `NOT_EXERCISED` |
| telemetry/Web console | proposed projection plane | event → redact → project → inspect → signed Human action | `NOT_IMPLEMENTED` |

<!-- PDF_HARNESS_MATRIX_END -->

Detailed state machines and data ownership:
[`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md).

## Current implemented data flow

```text
skills-shared immutable Skill release ──┐
                                        ├─→ .agents/ + .skill-bindings/
runtime-env secret-free release ────────┘              │
                                                       ▼
                                            .arena composition requirements
                                                       │
                                                       ▼
                                      lock + Context Capsules + proof subjects
                                                       │
                            ┌──────────────────────────┼────────────────────────┐
                            ▼                          ▼                        ▼
                     loopctl public port       default-deny MCP       host Context projection
                            │                          │                        │
                            └──────────────────────────┼────────────────────────┘
                                                       ▼
                                      bounded module / disposable Skill runner
                                                       │
                                              artifacts + OS exits
                                                       │
                                                       ▼
                                        proof + control + mutation/hollow
                                                       │
                                                       ▼
                                           subject-bound receipt
                                                       │
                                                       ▼
                                             Human Admit / release
```

## Missing LoopX control flow

The PDF's core task-state loop is not represented by the current `loopctl` name:

```text
Objective + Todos + Gates + Evidence + Quota
        ↓
append-only single-writer event ledger
        ↓
strategy graph proposes a typed command
        ↓
worker executes in an isolated workspace
        ↓
hard gates observe artifacts
        ↓
LoopX reducer alone commits the transition
        ↓
memory proposal / retry / HITL / complete
```

Required authority law:

```text
strategy proposes
worker executes
gates observe
LoopX commits
Human admits
```

## Current module catalog

| Module ID | Responsibility |
|---|---|
| `agent-runtime-integration` | Skill/runtime bindings, portable host-owned execution and adapter verdicts |
| `arena-core` | root entrypoints, bootstrap, placement and repository gates |
| `code-truth-graph` | source-bound Code Truth Graph builder |
| `environment-contracts` | runtime projection, logical origins and Browser Contract |
| `knowledge-providers` | bounded provider query and proposal-only memory contracts |
| `loop-runtime` | `loopctl`, Context Capsules and stateless MCP runtime |
| `mcp-adapters` | higher-level MCP adapters |
| `module-catalog` | manifests, ownership, composition and locks |
| `notebooklm` | authenticated bounded harvest loop |
| `openwiki` | typed OpenWiki update and projection |
| `perfect-seed-factory` | typed seed-repository Micro loop |
| `project-bootstrapper` | external-project plan/apply/verify/rollback |
| `proof-kernel` | closure subjects, controls, mutations and release aggregation |
| `technical-equivalence` | claim-to-implementation equivalence loop |

The desired, locked and released module sets must be identical. A selected module missing from the lock or release receipt is a hard integration failure.

## Stable public surfaces

### `loopctl`

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
```

`loopctl/contract.json` is the canonical external surface; `loopctl.sh` is wiring. Private flags, prompt fragments, implementation paths and temporary files are not external contract.

### Stateless MCP

MCP tools are generated from the canonical CLI contract and `.arena/mcp-policy.json`, with default deny. Each call pins an immutable subject, materializes only the selected closure, uses a disposable workspace and verifies cleanup. No generic shell, server-host absolute path, arbitrary `cwd`, secret or browser profile is accepted.

### Project bootstrapper

```sh
bun scripts/arena_project.ts --help
bun scripts/gates/check_project_bootstrap.ts
```

Initialization follows `plan → resolve → render temp tree → verify → apply → receipt`. Rollback refuses target bytes changed after apply.

## Molecular Stack PR index

Repository-level Git Town configuration is currently absent:

```text
.git-town.toml                       ABSENT
.git-town                            ABSENT
git-town-stacked-pr-worker selected  ABSENT
```

Molecular sibling/child/terminal/convergence semantics are still enforced by
[`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md). The full current topology is
[`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md).

Quick view:

```text
four documentation siblings (#37, skills-shared#85, runtime-env#30, shield#78)
        ↓ all merged
bettor-arena#38 convergence leaf
        ├─ pin exact merged routes
        ├─ audit PDF mapping
        ├─ regenerate lock/context/proof projections
        └─ keep live host/provider checks separate

repo-agent binding #43
→ portable Skill contract #48
→ host-owned execution #50
→ provider contracts #51
→ paired provider evaluator #56 (open; mixed exact-head checks)
```

PR #53 is a diverged historical aggregate and is not a merge instruction. Issue #24 remains the open immutable Agent Shield reference-consumer leaf.

## Evidence model

- Module manifests: [`.arena/modules/`](.arena/modules/)
- Composition requirements: [`.arena/compositions/`](.arena/compositions/)
- Deterministic lock: [`.arena/locks/`](.arena/locks/)
- Context Capsules: [`.arena/contexts/`](.arena/contexts/)
- Module proof subjects: [`data/module-proof/`](data/module-proof/)
- MCP exposure: [`data/mcp/`](data/mcp/)
- Origin/browser status: [`data/origins/`](data/origins/) / [`data/browser/`](data/browser/)

Evidence states are not aliases:

```text
PASS ≠ FAIL ≠ ABSENT ≠ NOT_IMPLEMENTED ≠ NOT_EXERCISED
```

A receipt is a claim. A control must execute the public port. A mutation or hollow control must prove that a load-bearing guard can turn red.

## Local verification

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py --selftest
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_proof.py check
python3 scripts/arena_context.py check
bun scripts/gates/check_mcp_policy.ts
bun scripts/gates/check_project_bootstrap.ts
bun scripts/gates/check_environment_contracts.ts
```

Run `sh bootstrap.sh` once to install repository-relative hooks and perform core doctor checks. Host trust, MCP approval, network widening, browser sign-in and secret-bearing providers remain Human-owned activation.

## Current boundary

The deterministic module catalog, ownership model, module-scoped proof identity, Context Capsules, default-deny MCP runtime, transactional project bootstrap, logical-origin/browser contracts, portable Skill execution, OpenWiki, Code Truth Graph and provider-neutral contracts are present.

Live subscriptions, signed-in sessions, provider indexes, cloud MicroVMs, local/cloud parity, LoopX task-state authority, LangGraph HITL, episodic-memory writeback, observability and Web UI remain `NOT_EXERCISED` or `NOT_IMPLEMENTED` unless an exact current receipt says otherwise.
