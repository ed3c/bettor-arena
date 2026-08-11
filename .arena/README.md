# `.arena/` — bettor-arena module control plane

This directory is the first executable slice of
`docs/architecture/modular-integration-requirements.md`.

## Implemented in Phase 0

- versioned module manifests under `modules/*/module.json`;
- composition requirements and a deterministic checked-in lock;
- capability dependency resolution;
- exact component validation;
- overlapping ownership-root rejection;
- zero-network positive and negative controls;
- a repository-contained Agent entrypoint contract.

Run:

```bash
python3 scripts/arena_modules.py catalog
python3 scripts/arena_modules.py check
python3 scripts/arena_modules.py resolve \
  --requirements .arena/compositions/bettor-arena.requirements.json
```

The commit gate uses:

```bash
python3 scripts/gates/check_module_catalog.py
python3 scripts/gates/check_agent_docs.py
```

## Honest boundary

Phase 0 does **not** claim that module-scoped proof v2, Context Capsules,
project initialization, GitHub/Forgejo multi-origin promotion, browser contract
v2, or automatic consumer rollout exists. Those remain `NOT_IMPLEMENTED`.

The ownership gate currently proves that declared roots do not overlap. It does
not yet prove that every tracked file belongs to a module; repository-wide
coverage is a later vertical slice.
