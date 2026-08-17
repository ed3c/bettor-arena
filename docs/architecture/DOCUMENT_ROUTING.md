# Document routing — bettor-arena binding

Bettor Arena is the Integration / Acceptance reference for the shared multi-hop route:

```text
README / AGENTS / CLAUDE
→ CONTEXT + ARCHITECTURE
→ docs/INDEX topic selection
→ conditional architecture AGENTS
→ nearest directory README
→ machine manifest/contract/script/verifier
→ current receipt + molecular Stack index
```

## Standard routes

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/AGENTS.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/DOMAIN_DECOUPLING.md
docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md
docs/architecture/pdf-harness-integration.matrix.json
docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
docs/traceability/STACK_PR_INDEX.md
<governed-directory>/README.md
```

## Route profiles

### Normal module/task work

```text
root entry
→ docs/INDEX
→ nearest README
→ module manifest/public contract
→ source/tests/receipts
→ exact issue/PR
```

### Domain, Skill, binding or adapter work

```text
root entry
→ docs/architecture/AGENTS.md
→ DOMAIN_DECOUPLING.md
→ .agents or .skill-bindings nearest README
→ exact requirement/binding/module contract
→ consumer proof and receipt
```

### PDF Harness verification

```text
root entry
→ PDF_HARNESS_INTEGRATION_AUDIT.md
→ pdf-harness-integration.matrix.json
→ DIRECTORY_STATE_MACHINE_MAP.md
→ modular-integration-status.md
→ machine contracts/receipts
→ STACK_PR_INDEX.md
```

### Branch, PR or generated-lock work

```text
root entry
→ docs/agents/issue-tracker.md
→ STACK_PR_INDEX.md
→ current GitHub issue/PR metadata
→ generated lock/context/proof subjects
→ exact-head checks
```

## Assertions

- `DR-01`: root routes exist and agree on repository role.
- `DR-02`: relative links resolve.
- `DR-03`: every governed directory has a nearest README or named inheritance.
- `DR-04`: README names owner, purpose, inputs, outputs, state machine, evidence, allowed/forbidden changes.
- `DR-05`: Markdown is not a second CLI/API/schema/manifest/receipt/verifier authority.
- `DR-06`: no credential, browser/device session, secret value or specific host checkout is portable state.
- `DR-07`: evidence states remain distinct.
- `DR-08`: source proposal, target architecture and current status are separate.
- `DR-09`: shared `SKILL.md` is procedural; `modules/` contains on-demand domain instances.
- `DR-10`: all four repositories agree on roles and immutable binding/release flow.
- `DR-11`: Git Town configuration must be observed; molecular terms alone do not prove it is active.
- `DR-12`: source proposals do not become implementation or live evidence without verification and receipts.
- `DR-13`: the PDF audit distinguishes the existing modular foundation from the missing LoopX kernel.
- `DR-14`: irreversible delivery, queue, provider and release operations route through `docs/git/AUTOMATED_ADMISSION.md`; prose or a generic Gate cannot authorize them.
- `DR-15`: desired, locked and released module sets agree before integration is called coherent.
- `DR-16`: every active/stale molecular leaf is indexed with relation, state and automation boundary.
- `DR-20`: this modular consumer provides `docs/architecture/DOMAIN_DECOUPLING.md`.
- `DR-21`: architecture `AGENTS.md` loads the domain contract conditionally and does not repeat it.
- `DR-22`: consumer bindings use immutable identities and do not copy canonical shared Skill bodies.
- `DR-23`: consumer specialization only tightens constraints, narrows effects, increases evidence, or reduces authority.
- `DR-24`: mutable issue/PR/provider/runtime state remains in current machine routes, not in the stable shared contract.

Each route leaves an in-place summary before linking away, following the `knowledge-continuity` rule. The normal path from nearest README to machine authority and evidence should take no more than two intentional hops.

## Validation

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
```
