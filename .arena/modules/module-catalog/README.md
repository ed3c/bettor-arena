# `module-catalog` module

Machine authority: [`module.json`](module.json)
Interface version: `1.2.0`

## Role

Owns `.arena/`, validates manifests and components, classifies every tracked path, resolves capabilities and emits deterministic composition locks.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `module-catalog` | core | `1.2.0` | denied | `python3 scripts/arena_lock.py` |

## Capability boundary

**Provides**

- `arena.module-catalog/v1`

**Requires**

- none

## Owned implementation roots

- `.arena/`
- `scripts/arena_index.py`
- `scripts/arena_modules.py`
- `scripts/arena_ownership.py`
- `scripts/arena_lock.py`

## Runtime and Skills

- Runtime: `git`, `python3`
- Skills: none

## Evidence

- Verify: `python3 scripts/gates/check_module_catalog.py`
- Independent control: not separately declared
- Mutation / hollow evidence: `python3 scripts/arena_lock.py --selftest`

## External boundary

Local control-plane only. Resolution and ownership checks are zero-network and must complete before any write/apply step.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
