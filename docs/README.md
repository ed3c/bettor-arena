# bettor-arena documentation

This directory is the human/Agent navigation layer. It does not replace machine-readable contracts under `.arena/`, the public CLI contract under `loopctl/`, or executable evidence under `data/`.

## Authority order

| Layer | Authority | Purpose |
|---|---|---|
| Engineering SSOT | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Placement, invariants and repository-wide rules |
| Bounded context | [`../CONTEXT.md`](../CONTEXT.md) | Stable glossary; not mutable run state |
| Agent document policy | [`agents/README.md`](agents/README.md) | Context, ADR, nearest-README and issue/PR routing |
| Normative target | [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) | Complete target contract |
| Mutable status | [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) | What landed and what remains unexercised |
| LoopX PDF audit | [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) | 41-page PDF → module/State Machine/data-flow/gap mapping |
| LoopX machine contract | [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json) | Executable integration verdict and Stack snapshot |
| Machine control plane | [`.arena/`](../.arena/) | Manifests, requirements, locks, policies and Context Capsules |
| Public runtime | [`loopctl/`](../loopctl/) | Stable CLI/MCP surface |
| Proof semantics | [`proof_workflow/`](../proof_workflow/) | Proof, control, negative control and exclusions |
| Generated evidence | [`data/`](../data/) | Subject-bound snapshots and receipts |

When prose and executable bytes disagree, the current machine contract and its gate/receipt win. Correct the prose in the same workstream.

## Documentation map

- [`INDEX.md`](INDEX.md) — standard route index.
- [`agents/README.md`](agents/README.md) — Agent-facing domain and issue-tracker policy.
- [`agents/domain.md`](agents/domain.md) — `CONTEXT.md`, ADR, nearest README and memory-conflict rules.
- [`agents/issue-tracker.md`](agents/issue-tracker.md) — GitHub/Forgejo issue/PR authority and molecular traceability.
- [`architecture/README.md`](architecture/README.md) — architecture contracts and status ledgers.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — Macro/Micro/module/MCP/proof/provider/LoopX transitions.
- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — LoopX/Harness PDF audit, corrections and terminal leaves.
- [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json) — machine-readable 15-requirement audit.
- [`architecture/pdf-loopx-harness.integration.schema.json`](architecture/pdf-loopx-harness.integration.schema.json) — audit schema.
- [`architecture/PDF_SKILL_MCP_TRACEABILITY.md`](architecture/PDF_SKILL_MCP_TRACEABILITY.md) — separate SKILL.md + MCP PDF audit.
- [`adr/README.md`](adr/README.md) — admitted Architecture Decision Records.
- [`audits/README.md`](audits/README.md) — commit/branch-scoped review handoffs.
- [`plans/README.md`](plans/README.md) — dated execution plans and as-run ledgers.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skills/runtime-env/host adapter aggregate.
- [`runtime-env-integration.md`](runtime-env-integration.md) — secret-free runtime projection and consumer verification.
- [`knowledge-providers/README.md`](knowledge-providers/README.md) — Serena/GrepAI/Code-Graph-RAG/Mem0 contracts.
- [`../.skill-bindings/repo-agent-native/README.md`](../.skill-bindings/repo-agent-native/README.md) — source-anchored repository-analysis binding.
- [`../.arena/modules/README.md`](../.arena/modules/README.md) — human module catalog.
- [`../README.md`](../README.md) — cold-start entrypoint and compact State Machine/data-flow/Stack index.

## LoopX / Harness architecture route

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md
→ docs/INDEX.md
→ docs/architecture/STATE_MACHINES.md
→ docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md
→ docs/architecture/pdf-loopx-harness.integration.json
→ target .arena/modules/<id>/README.md + module.json
→ public contract/source/tests/receipts
→ exact issue/PR/base/head/checks
```

Run:

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

A green audit means the repository documentation and current mechanisms agree with a **partial** integration verdict. It does not prove live LangGraph, worker, provider, cloud, browser, memory or production behavior.

## Repository-analysis route

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md or optional CONTEXT-MAP.md
→ docs/README.md
→ docs/agents/domain.md
→ applicable docs/adr/
→ nearest README.md
→ .skill-bindings/repo-agent-native/README.md
→ docs/knowledge-providers/README.md when a provider is used
→ projected shared Skill and selected modules
→ machine contract/source/tests/receipts
→ exact issue and PR
```

Missing required context, ADR, owner, source subject or evidence is `ABSENT`, not something to reconstruct from chat or memory.

## Writing rules

1. Keep `AGENTS.md` and `CLAUDE.md` as governed routes; point to canonical detail instead of creating parallel laws.
2. Put stable rules in normative contracts, mutable completion state in status ledgers, and run facts in receipts.
3. Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED` and `SKIPPED_BY_POLICY`.
4. Do not place absolute machine paths, credentials, cookies, OAuth material, `.env` values, browser profiles, raw chain-of-thought or signed-in page bodies in docs.
5. Every admitted module manifest needs a sibling README; `check_readme_coverage.py` enforces it.
6. Per-run/digest directories inherit parent README; do not duplicate docs into every generated directory.
7. Configured MCP/provider/Skill presence is a declaration, not health/freshness/completeness evidence.
8. Memory, vector and graph output remain candidates until current authority reads them back.
9. Update directory/State Machine/data-flow and Stack indexes whenever ownership or GitHub topology changes.
