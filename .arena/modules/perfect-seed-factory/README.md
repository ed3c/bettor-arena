# `perfect-seed-factory` module

Machine authority: [`module.json`](module.json)
Interface version: `1.0.0`

## Role

Validates a typed packet, builds a fresh seed repository and emits a typed route result plus a wiki-update request.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `micro` | micro | `1.0.0` | allowlisted | `sh loopctl/loopctl.sh micro` |

## Capability boundary

**Provides**

- `seed-repo.build/v1`
- `wiki-update-request.produce/v1`

**Requires**

- `arena.loopctl/v1`
- `arena.proof-kernel/v1`

## Owned implementation roots

- `loop_wiki/evolve-perfect-seed-repo-factory/`

## Runtime and Skills

- Runtime: `bun`, `git`, `python3`, POSIX `sh`; local runtime profile
- Skills: required `loop-harness-standard`

## Evidence

- Verify: `sh loop_wiki/evolve-perfect-seed-repo-factory/verify.sh`
- Independent control: `sh proof_workflow/control_micro_entry.sh --json`
- Mutation / hollow evidence: `sh loop_wiki/evolve-perfect-seed-repo-factory/selftest.sh`

## External boundary

MCP may invoke only the public port with a closed carrier and fresh output path. Internal driver/prompts/iteration remain private.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
