# `mcp-adapters` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.0.0`

## Role

Contains higher-level MCP adapters, read-only context-pack machinery and transactional production migration layered above the immutable loop runtime.

## Public ports

No loop-level public port is declared by this module. Consumers reach bounded resident adapters through the stable `loopctl`/MCP layer where explicitly admitted.

## Capability boundary

**Provides**

- `arena.mcp-adapters/v1`

**Requires**

- `arena.stateless-mcp/v1`

## Owned implementation roots

- `mcp/`

## Runtime and Skills

- Runtime: `python3`
- Skills: none

## Evidence

- Verify: No aggregate module-level verify is declared; use the resident adapter tests and `mcp/README.md`.
- Independent control: not declared
- Mutation / hollow evidence: not declared

## External boundary

The module itself is not MCP-exposed. Individual adapters remain bounded by their own contracts and human approval.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
