# bettor-arena documentation

This directory is the human navigation layer. It does not replace the machine-readable contracts under `.arena/`, the public CLI contract under `loopctl/`, or executable evidence under `data/`.

## Authority order

| Layer | Authority | Purpose |
|---|---|---|
| Engineering SSOT | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Placement, invariants and repository-wide engineering rules |
| Bounded context | [`../CONTEXT.md`](../CONTEXT.md) | Stable glossary; not implementation or mutable state |
| Agent document policy | [`agents/README.md`](agents/README.md) | Domain-context, ADR, nearest-README and issue/PR routing |
| Normative target | [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) | Complete modular-integration target contract |
| Mutable status | [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) | What has actually landed and what remains unexercised |
| PDF requirement trace | [`architecture/PDF_SKILL_MCP_TRACEABILITY.md`](architecture/PDF_SKILL_MCP_TRACEABILITY.md) | SKILL.md/MCP PDF concepts mapped to Bettor contracts and evidence |
| Agent Shield PDF audit | [`integration/AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md`](integration/AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md) | runtime pin, directory/State Machine ownership, product status and Git Town Phase 3–6 Stack |
| Machine control plane | [`.arena/`](../.arena/) | Manifests, schemas, requirements, locks, policies and Context Capsules |
| Public runtime | [`loopctl/`](../loopctl/) | Stable CLI/MCP surface and wiring |
| Proof semantics | [`proof_workflow/`](../proof_workflow/) | Receipts, controls, negative controls and named exclusions |
| Generated evidence | [`data/`](../data/) | Checked-in snapshots and receipts; not hand-edited claims |

When prose and executable bytes disagree, the executable contract and its current gate/receipt win. The prose must then be corrected.

## Documentation map

- [`agents/README.md`](agents/README.md) — Agent-facing domain and issue-tracker policies adapted to Bettor's multi-hop route.
- [`agents/domain.md`](agents/domain.md) — `CONTEXT.md`/optional context-map, ADR, nearest-README and memory-conflict rules.
- [`agents/issue-tracker.md`](agents/issue-tracker.md) — GitHub/Forgejo issue/PR authority and molecular traceability.
- [`architecture/README.md`](architecture/README.md) — architecture contracts and status ledgers.
- [`architecture/PDF_SKILL_MCP_TRACEABILITY.md`](architecture/PDF_SKILL_MCP_TRACEABILITY.md) — first PDF's requirement/hypothesis → module/State Machine/evidence mapping.
- [`integration/AGENTS.md`](integration/AGENTS.md) — nearest Agent contract for cross-repository and PDF-product audits.
- [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) — four-repository data flow and authority boundary.
- [`integration/AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md`](integration/AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md) — second PDF's exact modular-integration verdict, runtime binding drift and Agent Shield Stack index.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) — issue/PR/commit/State Machine/evidence chain.
- [`adr/README.md`](adr/README.md) — admitted Architecture Decision Records.
- [`audits/README.md`](audits/README.md) — commit/branch-scoped review handoffs.
- [`plans/README.md`](plans/README.md) — dated execution plans and as-run ledgers.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skills/runtime-env/host adapters, including the `repo-agent-native` route.
- [`runtime-env-integration.md`](runtime-env-integration.md) — secret-free runtime projection and consumer verification.
- [`knowledge-providers/README.md`](knowledge-providers/README.md) — subject-bound Serena/GrepAI/Code-Graph-RAG/Mem0 capability contracts and memory proposal boundary.
- [`../.skill-bindings/repo-agent-native/README.md`](../.skill-bindings/repo-agent-native/README.md) — source-anchored repository-analysis consumer binding and provider boundaries.
- [`../.arena/modules/README.md`](../.arena/modules/README.md) — current module catalog for humans.
- [`../README.md`](../README.md) — repository entrypoint and quick verification.

## Repository-analysis route

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ applicable PDF trace/audit
→ docs/agents/domain.md
→ applicable docs/adr/
→ nearest directory README.md
→ .skill-bindings/repo-agent-native/README.md
→ docs/knowledge-providers/README.md when a semantic/symbol/graph/memory capability is used
→ projected shared Skill and matching modules
→ machine contract/source/tests/receipts
→ exact issue and PR
```

A route is optional only when its owning policy says so. Missing required context, ADR, nearest README, binding, source subject or evidence remains `ABSENT` rather than being reconstructed from memory or chat.

## Writing rules

1. Keep root `AGENTS.md` and `CLAUDE.md` as routed operating contracts; put directory-specific audit rules in the nearest `AGENTS.md`.
2. Put stable rules in the normative contract, mutable completion state in the status ledger, and run-specific facts in receipts.
3. Do not describe `NOT_EXERCISED`, `ABSENT`, `NOT_IMPLEMENTED`, `STALE_SOURCE_PIN` or source proposals as `PASS`.
4. Do not put local absolute paths, credentials, cookies, OAuth material, `.env` values, browser profiles, memory secrets, NFC material or private-key shards in documentation.
5. Every admitted module manifest needs a sibling `README.md`; `scripts/gates/check_readme_coverage.py` enforces this.
6. Per-run and digest directories inherit their parent README. Do not duplicate a README into every generated run directory.
7. A configured MCP server, provider package, Git Town branch or merged foundation contract is a declaration/implementation subject, not live product evidence.
8. Memory and code-graph outputs are candidates or hints until repository source, documents, tests or runtime receipts read them back.
9. When a consumer binding source commit/tree differs from the intended source, report `STALE_SOURCE_PIN` and require dry-run review; never auto-apply.
