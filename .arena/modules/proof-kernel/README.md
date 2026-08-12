# `proof-kernel` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.3.0`

## Role

Computes module-closure proof identities and aggregates traversal, independent control, mutation/hollow evidence, named exclusions and release receipts.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `harness` | core | `1.0.0` | control-only | `sh proof_workflow/prove_harness.sh` |
| `module-proof` | core | `1.0.0` | control-only | `python3 scripts/arena_proof.py` |

## Capability boundary

**Provides**

- `arena.proof-kernel/v1`

**Requires**

- `arena.module-catalog/v1`
- `arena.loopctl/v1`

## Owned implementation roots

- `proof_workflow/`
- `tests/`
- `scripts/arena_proof.py`

## Runtime and Skills

- Runtime: `git`, `python3`, POSIX `sh`
- Skills: none

## Evidence

- Verify: `python3 scripts/arena_proof.py check`
- Independent control: `python3 scripts/arena_proof.py check`
- Mutation / hollow evidence: `python3 scripts/arena_proof.py --selftest`

## External boundary

Not a generic external tool. A proof receipt cannot proxy its independent control; `NOT_EXERCISED` cannot aggregate to PASS.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
