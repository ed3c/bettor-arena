# `.arena/` — bettor-arena control plane

`.arena/` makes module boundaries, composition, context, external exposure and environment contracts **machine-readable**. It is owned by `module-catalog` and consumed by repository-contained zero-network gates.

The normative target remains [`../docs/architecture/modular-integration-requirements.md`](../docs/architecture/modular-integration-requirements.md). Current completion state is [`../docs/architecture/modular-integration-status.md`](../docs/architecture/modular-integration-status.md). The PDF proposal mapping is [`../docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](../docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md).

`.arena` is a modular composition/control plane. It is **not** the PDF's complete LoopX Objective/Todos/Gates/Evidence/Quota task-state kernel.

## Directory → State Machine map

| Path | Owner / role | State machine |
|---|---|---|
| [`modules/`](modules/) | module contracts and public capabilities | `PROPOSED → CONTRACTED → COMPOSED → PROVED → RELEASED` |
| [`schemas/`](schemas/) | machine schemas | `DRAFT → VALIDATED → VERSIONED → CONSUMED` |
| [`compositions/`](compositions/) | desired module/component/capability set | `DESIRED → RESOLVE → CONFLICT CHECK` |
| [`locks/`](locks/) | generated resolved composition | `REQUIREMENTS → MANIFEST DIGESTS → LOCK` |
| [`contexts/`](contexts/) | root/loop passive-context manifests | `SELECT → MATERIALIZE → FREEZE → DRIVER` |
| [`contexts.lock.json`](contexts.lock.json) | generated Context Capsule digests | `CONTEXT MANIFESTS → EXACT FILE DIGESTS → LOCK` |
| [`presets/`](presets/) | named composition starting points | `PRESET → PLAN → RESOLVE` |
| [`origins/`](origins/) | logical GitHub/Forgejo release contract | `DECLARE → PUBLISH → EQUIVALENCE → ADMIT` |
| [`browser/`](browser/) | Browser Contract v2 | `ACTOR → TRANSPORT → SESSION → WORKFLOW → EVIDENCE` |
| [`mcp-policy.json`](mcp-policy.json) | explicit external exposure | `DEFAULT DENY → REVIEWED ALLOW → GENERATED TOOL` |
| [`ownership-classes.json`](ownership-classes.json) | reviewed non-module path classes | `UNOWNED → CLASSIFIED → VERIFIED` |

Generated snapshots and receipts live under [`../data/`](../data/), not in this control-plane directory.

## Macro composition flow

```text
module.json + sibling README
        ↓
tracked-path ownership
        ↓
composition requirements
        ↓ deterministic resolve
composition lock
        ↓
Context Capsule lock
        ↓
module proof subjects
        ↓
release receipt
        ↓
Human Admit
```

Hard equality:

```text
requirements module IDs
== composition-lock module IDs
== release-receipt module IDs
```

A focused module test cannot proxy a stale lock.

## Relationship to the proposed LoopX kernel

Implemented here:

```text
module selection
dependency/conflict resolution
context selection
public exposure policy
proof subject aggregation
release candidate state
```

Not implemented here:

```text
Objective/Todos/Quota task state
append-only event ledger
single-writer reducer
retry/quota terminal states
LangGraph interrupt/resume
episodic-memory state
```

A future LoopX module may consume `.arena` capabilities and contexts, but it must not turn `.arena/locks` or LangGraph checkpoints into canonical task state.

## Authority and generation

- `module.json` is authoritative for ownership roots, components, capabilities, public ports, runtime tools, Skills and proof commands.
- A sibling `README.md` explains intent and navigation; it must not redefine the interface.
- Root projections are generated from canonical fragments/contracts. Modules must not maintain parallel hand-written copies.
- Checked-in locks and status snapshots must match a fresh render at the exact commit.
- Per-run artifacts do not enter mechanism digests unless a contract explicitly says they do.
- A generated file is never manually edited to make a gate green.

## Common commands

```sh
python3 scripts/arena_modules.py catalog
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_lock.py resolve \
  --requirements .arena/compositions/bettor-arena.requirements.json
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
python3 scripts/gates/check_pdf_harness_integration.py
bun scripts/gates/check_mcp_policy.ts
bun scripts/gates/check_project_bootstrap.ts
bun scripts/gates/check_environment_contracts.ts
```

## Adding or changing a module

1. Add or edit `.arena/modules/<id>/module.json`.
2. Add or update `.arena/modules/<id>/README.md`.
3. Name its state-machine owner, inputs, outputs, transitions, terminal states and Human boundary.
4. Keep tracked-path ownership single-valued.
5. Select it in the composition requirements.
6. Resolve the composition lock.
7. Regenerate Context Capsules and module proof subjects.
8. Run verify, independent control and mutation/hollow evidence.
9. Update release evidence only after all selected module subjects agree.
10. Bump `interface_version` only when an externally observable contract changes.
11. Update the directory map, PDF audit matrix and Stack index when the new module changes those claims.

## Current boundary

The repository contains executable catalog/ownership, module-scoped proof identity, Context Capsules, default-deny MCP, project bootstrap, logical-origin/browser contracts, portable Skill execution and provider-neutral knowledge contracts.

External systems can still be `NOT_EXERCISED`; a contract or status snapshot does not prove a live provider, signed-in session, cloud runtime or Human Admit. The complete LoopX kernel remains `NOT_IMPLEMENTED`.
