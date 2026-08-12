# `arena-core` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.1.0`

## Role

Owns the repository engineering SSOT, native Agent entrypoints, bootstrap, hooks and root-level deterministic gates.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `macro` | macro | `2.8.0` | denied | `sh loopctl/loopctl.sh macro` |

## Capability boundary

**Provides**

- `arena.passive-context/v1`
- `arena.host-gates/v1`

**Requires**

- `arena.module-catalog/v1`

## Owned implementation roots

- `AGENTS.md`
- `CLAUDE.md`
- `CONTEXT.md`
- `ARCHITECTURE.md`
- `bootstrap.sh`
- `.githooks/`
- `.github/`
- `scripts/gates/`
- `docs/architecture/`

## Runtime and Skills

- Runtime: `git`, POSIX `sh`, `python3`
- Skills: none

## Evidence

- Verify: `python3 scripts/gates/check_agent_docs.py`
- Independent control: `sh proof_workflow/control_macro_entry.sh --json`
- Mutation / hollow evidence: `python3 scripts/gates/check_agent_docs.py --selftest`

## External boundary

Macro governance is local/trusted-host only. It is never exposed as a generic MCP operation.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
