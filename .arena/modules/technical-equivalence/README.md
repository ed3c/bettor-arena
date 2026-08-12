# `technical-equivalence` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.0.0`

## Role

Evaluates whether a technical claim and a candidate implementation are equivalent, preserving offline/live/judge/Human states and producing candidate-only sync bundles.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `equivalence` | micro | `1.0.0` | control-only | `sh loopctl/loopctl.sh equivalence` |

## Capability boundary

**Provides**

- `technical-equivalence.evaluate/v1`

**Requires**

- `arena.loopctl/v1`
- `arena.proof-kernel/v1`

## Owned implementation roots

- `loop_wiki/evolve-technical-equivalence-research/`

## Runtime and Skills

- Runtime: `agy`, `claude`, `python3`, POSIX `sh`; live network is broker-only
- Skills: required `external-verify`, `path-b-reduction`

## Evidence

- Verify: `python3 loop_wiki/evolve-technical-equivalence-research/selftest.py`
- Independent control: `sh proof_workflow/control_equivalence_entry.sh --json`
- Mutation / hollow evidence: `sh loop_wiki/evolve-technical-equivalence-research/selftest.sh`

## External boundary

No live or secret-bearing path is MCP-exposed. Candidate sync stops before target-side Human Admit.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
