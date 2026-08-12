# `.arena/` — bettor-arena control plane

`.arena/` makes module boundaries, composition, context, external exposure and environment contracts machine-readable. It is owned by the `module-catalog` module and is consumed by repository-contained zero-network gates.

The normative target remains [`../docs/architecture/modular-integration-requirements.md`](../docs/architecture/modular-integration-requirements.md). Current completion state is recorded in [`../docs/architecture/modular-integration-status.md`](../docs/architecture/modular-integration-status.md).

## Directory map

| Path | Role |
|---|---|
| [`modules/`](modules/) | One versioned `module.json` plus a sibling human guide per admitted module |
| [`schemas/`](schemas/) | JSON Schemas for manifests, requirements, locks and receipts |
| [`compositions/`](compositions/) | Desired module/component/capability sets |
| [`locks/`](locks/) | Deterministically resolved composition locks |
| [`contexts/`](contexts/) | Root/loop passive-context manifests |
| [`contexts.lock.json`](contexts.lock.json) | Frozen Context Capsule digests |
| [`presets/`](presets/) | Named consumer/embedded/owner composition starting points |
| [`origins/`](origins/) | One logical release across GitHub/Forgejo origins |
| [`browser/`](browser/) | Browser Contract v2 actors, transports, sessions, routes and evidence |
| [`mcp-policy.json`](mcp-policy.json) | Explicit MCP exposure policy; absence means denied |
| [`ownership-classes.json`](ownership-classes.json) | Reviewed fallback classes for non-module tracked paths |

Generated snapshots and receipts live under [`../data/`](../data/), not in this control-plane directory.

## Authority and generation

```text
module.json + composition requirements
        ↓ deterministic resolve
composition lock
        ↓
Context / Skill / runtime / host projections
        ↓
module proof subjects + release receipt
        ↓
immutable CLI/MCP release
```

- `module.json` is authoritative for ownership roots, components, capabilities, public ports, runtime tools, Skills and proof commands.
- A sibling `README.md` explains intent and navigation; it must not redefine the interface.
- Root projections are generated from canonical fragments/contracts. Modules must not maintain parallel hand-written copies.
- Checked-in locks and status snapshots must match a fresh render at the exact commit.
- Per-run artifacts do not enter mechanism digests unless a contract explicitly says they do.

## Common commands

```sh
python3 scripts/arena_modules.py catalog
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_lock.py resolve \
  --requirements .arena/compositions/bettor-arena.requirements.json
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
bun scripts/gates/check_mcp_policy.ts
bun scripts/gates/check_project_bootstrap.ts
bun scripts/gates/check_environment_contracts.ts
```

## Adding or changing a module

1. Add or edit `.arena/modules/<id>/module.json`.
2. Add or update `.arena/modules/<id>/README.md`.
3. Keep tracked-path ownership single-valued.
4. Resolve the composition lock.
5. Regenerate Context Capsules and module proof subjects.
6. Run verify, control and mutation/hollow evidence.
7. Update release evidence only after all selected module subjects agree.
8. Bump `interface_version` only when an externally observable contract changes.

## Current boundary

The repository contains executable catalog/ownership, module-scoped proof identity, Context Capsule, default-deny MCP, project bootstrap, logical-origin and browser contracts. External systems can still be `NOT_EXERCISED`; a contract or status snapshot does not prove a live provider, signed-in session, cloud runtime or Human Admit occurred.
