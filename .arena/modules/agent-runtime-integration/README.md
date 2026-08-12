# `agent-runtime-integration` module

Machine authority: [`module.json`](module.json)
Interface version: `1.1.0`

## Role

Resolves the selected `skills-shared` and `runtime-env` closure, binds it to bettor-arena, and reports Claude Code/Codex CLI adapter readiness without storing secret values.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `agent-runtime` | aggregate | `1.0.0` | control-only | `sh loopctl/loopctl.sh agent-runtime` |

## Capability boundary

**Provides**

- `agent-runtime.aggregate/v1`

**Requires**

- `arena.module-catalog/v1`
- `arena.loopctl/v1`
- `arena.proof-kernel/v1`

## Owned implementation roots

- `.agents/`
- `.runtime-env/`
- `scripts/agent_runtime.py`
- `scripts/runtime-env/`
- `docs/agent-runtime-integration.md`
- `docs/runtime-env-integration.md`

## Runtime and Skills

- Runtime: `claude`, `codex`, `python3`; profile `bettor-arena-runtime-local`
- Skills: required `shared-skills-infra`

## Evidence

- Verify: `python3 scripts/agent_runtime.py check --offline`
- Independent control: `sh proof_workflow/control_agent_runtime_entry.sh --json`
- Mutation / hollow evidence: `sh proof_workflow/control_agent_runtime_entry.sh --json`

## External boundary

Not MCP-exposed. Live host adapters need human-owned credentials/subscriptions; offline PASS cannot proxy a live run.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
