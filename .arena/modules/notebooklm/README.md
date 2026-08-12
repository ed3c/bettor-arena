# `notebooklm` module

Machine authority: [`module.json`](module.json)
Interface version: `1.0.0`

## Role

Runs the host-owned NotebookLM harvest workflow, including authenticated Drive-by-reference follow, while keeping source notebooks read-only.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `notebooklm` | micro | `1.0.0` | control-only | `sh loopctl/loopctl.sh notebooklm` |

## Capability boundary

**Provides**

- `notebooklm.harvest/v1`

**Requires**

- `arena.loopctl/v1`
- `arena.proof-kernel/v1`

## Owned implementation roots

- `notebooklm/`

## Runtime and Skills

- Runtime: `notebooklm` CLI + `python3`; host authentication required for live paths
- Skills: repo-owned `notebooklm-workflow`

## Evidence

- Verify: `python3 notebooklm/workflow.py --selftest`
- Independent control: `sh proof_workflow/control_notebooklm_entry.sh --json`
- Mutation / hollow evidence: `sh proof_workflow/control_notebooklm_entry.sh --json`

## External boundary

Authenticated run is not MCP-exposed by default. Binary absence, unauthenticated and unauthorized are distinct exits.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
