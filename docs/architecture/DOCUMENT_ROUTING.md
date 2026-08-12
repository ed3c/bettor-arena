# Document routing — bettor-arena binding

Bettor Arena is the reference implementation of the shared multi-hop document route:

```text
README / AGENTS / CLAUDE
→ CONTEXT + ARCHITECTURE
→ docs/INDEX
→ nearest directory README
→ machine manifest/contract/script/verifier
→ current status/receipt/traceability
```

## Standard routes

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

## Assertions

- `DR-01`: root routes exist and agree on repository role.
- `DR-02`: relative links resolve.
- `DR-03`: every governed directory has a nearest README or named inheritance.
- `DR-04`: README names owner, purpose, inputs, outputs, state machine, evidence, allowed/forbidden changes.
- `DR-05`: Markdown is not a second CLI/API/schema/manifest/receipt/verifier authority.
- `DR-06`: no credential, browser/device session, secret value, or specific host checkout is portable state.
- `DR-07`: evidence states remain distinct.
- `DR-08`: target architecture and current status are separate.
- `DR-09`: shared `SKILL.md` is procedural; `modules/` contains on-demand domain instances.
- `DR-10`: all four repositories agree on roles and immutable binding/release flow.
- `DR-11`: if Git Town is admitted, sibling/true-child/terminal/convergence/Human boundaries are explicit.
- `DR-12`: source proposals do not become implementation or live evidence without verification and receipts.

Each route leaves an in-place summary before linking away, following the `knowledge-continuity` rule. The normal path from nearest README to machine authority and evidence should take no more than two intentional hops.
