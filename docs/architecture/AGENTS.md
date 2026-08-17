# Architecture documentation Agent route — Bettor Arena

This file governs `docs/architecture/`. It selects topic documents by task. It does not duplicate the contracts it routes to.

## Bootstrap

Read:

1. [`../../AGENTS.md`](../../AGENTS.md) for repository procedure.
2. [`../../README.md`](../../README.md) for repository role.
3. [`../../CONTEXT.md`](../../CONTEXT.md) for the current handoff.
4. [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) for stable placement and authority.
5. [`../INDEX.md`](../INDEX.md) for the complete route inventory.

Then read only the matching topic route.

## Conditional topic routes

| Trigger | Read |
|---|---|
| route name, hop order, route assertion | [`DOCUMENT_ROUTING.md`](DOCUMENT_ROUTING.md) |
| state, event, transition, terminal | [`STATE_MACHINES.md`](STATE_MACHINES.md) |
| shared Skill, `.agents/`, `.skill-bindings/`, module, adapter, provider port, domain boundary | [`DOMAIN_DECOUPLING.md`](DOMAIN_DECOUPLING.md) |
| target modular contract | [`modular-integration-requirements.md`](modular-integration-requirements.md) |
| current modular implementation state | [`modular-integration-status.md`](modular-integration-status.md) |
| PDF requirement comparison | [`PDF_HARNESS_INTEGRATION_AUDIT.md`](PDF_HARNESS_INTEGRATION_AUDIT.md) |
| cross-repository binding, origin or release | [`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md) |
| Git Town, branch or Stack PR | [`../git/README.md`](../git/README.md) and [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md) |
| issue/PR/eval/receipt lineage | [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md) |

Do not preload PDF, Git Town, runtime, provider, proof and domain documents for every task.

## Authority and writer rules

- The nearest README owns the local route.
- `.agents/`, `.skill-bindings/`, `.arena/`, `.runtime-env/`, proof and receipt files remain machine or consumer authorities.
- Current issue/PR/queue/provider state is read from its exact subject, not copied here.
- One branch and path lease owns one documentation change.
- Cross-repository process dependency is not Git child ancestry.
- A shared canonical method and a Bettor consumer binding may share a filename while retaining different document roles.

## Completion packet

Report:

```text
selected topic route
consumer/shared ownership affected
binding or module interface affected
State Machine or data-flow change
machine authority changed or unchanged
exact base/head
checks and remaining non-success states
```
