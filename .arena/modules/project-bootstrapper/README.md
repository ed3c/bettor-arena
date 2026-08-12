# `project-bootstrapper` module

Machine authority: [`module.json`](module.json)
Interface version: `1.0.0`

## Role

Plans and transactionally initializes an external project in remote-consumer or embedded-module mode, then verifies or fail-closed rolls back it.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `project-bootstrapper` | macro | `1.0.0` | denied | `bun scripts/arena_project.ts` |

## Capability boundary

**Provides**

- `arena.project-bootstrap/v1`

**Requires**

- `arena.module-catalog/v1`
- `arena.stateless-mcp/v1`

## Owned implementation roots

- `scripts/project_types.ts`
- `scripts/project_resolver.ts`
- `scripts/project_transaction.ts`
- `scripts/arena_project.ts`
- `scripts/arena_project.py`

## Runtime and Skills

- Runtime: `bun`, `git`, `python3`, POSIX `sh`
- Skills: none directly; selected modules contribute the resolved Skill closure

## Evidence

- Verify: `bun scripts/gates/check_project_bootstrap.ts`
- Independent control: `bun scripts/arena_project.ts --selftest`
- Mutation / hollow evidence: `bun scripts/arena_project.ts --selftest`

## External boundary

Local/trusted-host only. Default operation is dry-run planning. Apply, rollback and host activation are never generic MCP tools.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
