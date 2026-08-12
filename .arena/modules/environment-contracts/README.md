# `environment-contracts` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.0.0`

## Role

Defines one logical release across GitHub/Forgejo and Browser Contract v2 across actors, surfaces, transports, sessions, workflows, routes and evidence.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `environment-contracts` | core | `1.0.0` | denied | `bun scripts/gates/check_environment_contracts.ts` |

## Capability boundary

**Provides**

- `arena.logical-release/v1`
- `arena.browser-contract/v2`

**Requires**

- `arena.module-catalog/v1`

## Owned implementation roots

- `scripts/environment_types.ts`
- `scripts/arena_origins.ts`
- `scripts/arena_origin_checkout_probe.ts`
- `scripts/arena_browser.ts`

## Runtime and Skills

- Runtime: `bun`, `git`; optional network only for explicit probes
- Skills: required `external-verify`, `gemini-conversation-research`, `dr-research-loop`

## Evidence

- Verify: `bun scripts/gates/check_environment_contracts.ts`
- Independent control: `bun scripts/gates/check_environment_contracts.ts --selftest`
- Mutation / hollow evidence: `bun scripts/gates/check_environment_contracts.ts --selftest`

## External boundary

Not MCP-exposed. Signed-in sessions and credentials remain host-only. Contract PASS does not imply live provider reachability.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
