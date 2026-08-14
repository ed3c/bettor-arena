# bettor-arena documentation

This directory is the human navigation layer. It does not replace machine-readable contracts under `.arena/`, the public CLI contract under `loopctl/`, or executable evidence under `data/`.

## Authority order

| Layer | Authority | Purpose |
|---|---|---|
| Engineering SSOT | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | placement, invariants and repository-wide engineering rules |
| Agent entry | [`../AGENTS.md`](../AGENTS.md) / [`../CLAUDE.md`](../CLAUDE.md) | mandatory routing and completion contract |
| Bounded context | [`../CONTEXT.md`](../CONTEXT.md) | current handoff and stable glossary |
| PDF integration audit | [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) | source proposal versus current repository |
| LoopX PDF audit | [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) | executable LoopX-specific requirement and authority mapping |
| Directory/state map | [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md) | directory owner, inputs, outputs and transitions |
| Normative target | [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) | complete modular-integration target contract |
| Mutable status | [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) | what has actually landed and what remains unexercised |
| Stack traceability | [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) | molecular siblings, children, terminal and convergence leaves |
| Machine control plane | [`.arena/`](../.arena/) | manifests, schemas, requirements, locks, policies and Context Capsules |
| Public runtime | [`loopctl/`](../loopctl/) | stable CLI/MCP surface and wiring |
| Proof semantics | [`proof_workflow/`](../proof_workflow/) | receipts, controls, negative controls and named exclusions |
| Generated evidence | [`data/`](../data/) | checked-in snapshots and receipts; not hand-edited claims |

When prose and executable bytes disagree, the executable contract and its current gate/receipt win. The prose must then be corrected.

## PDF architecture routes

The attached **LLM 泛化：模型權重與 Harness** PDF is an input proposal, not implementation evidence.

```text
PDF proposal
→ architecture/PDF_HARNESS_INTEGRATION_AUDIT.md
→ architecture/pdf-harness-integration.matrix.json
→ architecture/DIRECTORY_STATE_MACHINE_MAP.md
→ architecture/modular-integration-status.md
→ traceability/STACK_PR_INDEX.md
→ machine contracts / current receipts
```

Current conclusion:

```text
supporting modular Harness foundation   IMPLEMENTED
complete LoopX architecture             NOT_IMPLEMENTED
live six-host/provider/cloud matrix      NOT_EXERCISED
```

Validation:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
```

## Documentation map

- [`INDEX.md`](INDEX.md) — standard root, architecture, machine and traceability routes.
- [`agents/README.md`](agents/README.md) — Agent-facing domain and issue-tracker policies.
- [`agents/domain.md`](agents/domain.md) — `CONTEXT.md`, ADR, nearest-README and memory-conflict rules.
- [`agents/issue-tracker.md`](agents/issue-tracker.md) — GitHub/Forgejo authority and molecular delivery.
- [`architecture/README.md`](architecture/README.md) — architecture contracts and status ledgers.
- [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) — exact PDF-to-repository verdict.
- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — LoopX/Harness requirement and gap traceability.
- [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json) — machine-readable LoopX audit.
- [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md) — root-directory state machines and data flow.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — current Macro/Micro/module/MCP/proof/project/origin machines plus missing LoopX target.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) — source/decision/issue/PR/eval/receipt index.
- [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) — exact molecular Stack topology and stale subjects.
- [`adr/README.md`](adr/README.md) — admitted Architecture Decision Records.
- [`audits/README.md`](audits/README.md) — commit/branch-scoped review handoffs.
- [`plans/README.md`](plans/README.md) — dated execution plans and as-run ledgers.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skills/runtime-env/host adapters.
- [`runtime-env-integration.md`](runtime-env-integration.md) — secret-free runtime projection.
- [`knowledge-providers/README.md`](knowledge-providers/README.md) — Serena/GrepAI/Code-Graph-RAG/Mem0 contracts.
- [`../.skill-bindings/repo-agent-native/README.md`](../.skill-bindings/repo-agent-native/README.md) — source-anchored repository-analysis binding.
- [`../.arena/modules/README.md`](../.arena/modules/README.md) — current module catalog and state-machine ownership.
- [`../README.md`](../README.md) — repository entrypoint and quick verification.

## Repository-analysis route

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md + CONTEXT.md
→ PDF audit / modular target / current status
→ directory State Machine map
→ nearest README
→ .skill-bindings/repo-agent-native/
→ provider route when needed
→ projected shared Skill and matching modules
→ machine contract/source/tests/receipts
→ exact issue / Stack PR
```

A route is optional only when its owning policy says so. Missing required context, ADR, README, binding, source subject, receipt or Stack edge remains `ABSENT`.

## Writing rules

1. Keep `AGENTS.md` and `CLAUDE.md` routed; do not copy the whole engineering SSOT into them.
2. Put stable rules in normative contracts, mutable completion in status ledgers, and run facts in receipts.
3. Do not describe `NOT_EXERCISED`, `ABSENT`, `NOT_IMPLEMENTED` or source proposals as `PASS`.
4. Do not put absolute host paths, credentials, cookies, OAuth material, `.env` values, browser profiles, memory secrets or signed-in page bodies in documentation.
5. Every admitted module manifest needs a sibling `README.md`; `scripts/gates/check_readme_coverage.py` enforces this.
6. Per-run and digest directories inherit their parent README; do not copy a README into every generated run.
7. A configured provider or MCP server is a declaration, not installation/health/freshness/completeness evidence.
8. Memory and code-graph output remains candidate-only until repository source, documents, tests or runtime receipts read it back.
9. A PDF example, fixture or LLM-generated diagram cannot become a current state machine without code, controls and receipts.
10. Every terminal/convergence branch change updates [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md).
