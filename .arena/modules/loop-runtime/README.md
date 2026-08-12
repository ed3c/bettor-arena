# `loop-runtime` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.5.0`

## Role

Provides the stable `loopctl` surface, immutable Context Capsules, fixed Claude/Codex canaries and the primary Bun/TypeScript default-deny stateless MCP runtime.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `loopctl` | core | `2.9.0` | allowlisted | `sh loopctl/loopctl.sh` |
| `context-capsule` | core | `1.0.0` | control-only | `python3 scripts/arena_context.py` |
| `mcp-policy` | core | `1.2.0` | control-only | `bun scripts/gates/check_mcp_policy.ts` |

## Capability boundary

**Provides**

- `arena.loopctl/v1`
- `arena.stateless-mcp/v1`
- `arena.context-carrier/v1`

**Requires**

- `arena.module-catalog/v1`
- `arena.passive-context/v1`

## Owned implementation roots

- `loopctl/`
- `scripts/arena_context.py`

## Runtime and Skills

- Runtime: `bun`, `git`, `python3`, POSIX `sh`, plus allowlisted `claude`/`codex` host adapters
- Skills: required `shared-skills-infra`

## Evidence

- Verify: `bun scripts/gates/check_mcp_policy.ts`
- Independent control: `sh tests/test_ctg_mcp_carrier.sh`
- Mutation / hollow evidence: `bun test loopctl/mcp_core.test.ts`

## External boundary

Only explicitly allowlisted tools are exposed. Every call pins an immutable subject and uses selected closure + disposable workspace. Secrets are broker-only.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
