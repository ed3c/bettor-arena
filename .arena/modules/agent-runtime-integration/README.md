# `agent-runtime-integration` module

Machine authority: [`module.json`](module.json)
Interface version: `1.2.0`

## Role

Resolves the selected `skills-shared` and `runtime-env` closure, binds it to bettor-arena, reports host-adapter readiness without storing secret values, and owns the host-only portable Skill execution/assertion port.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `agent-runtime` | aggregate | `1.0.0` | control-only | `sh loopctl/loopctl.sh agent-runtime` |
| `skill-execution` | execution-port | `1.0.0` | host-only | `sh loopctl/loopctl.sh skill-execution` |

## Capability boundary

**Provides**

- `agent-runtime.aggregate/v1`
- `skill-execution.runner/v1`

**Requires**

- `arena.module-catalog/v1`
- `arena.loopctl/v1`
- `arena.proof-kernel/v1`

## Owned implementation roots

- `.agents/`
- `.runtime-env/`
- `scripts/agent_runtime.py`
- `scripts/check_agent_runtime_module.py`
- `scripts/runtime-env/`
- `docs/agent-runtime-integration.md`
- `docs/runtime-env-integration.md`

`proof_workflow/` remains owned by `proof-kernel`; its traversal/control scripts bind evidence to this module without transferring ownership.

## Runtime and Skills

- Runtime: `claude`, `codex`, `git`, `python3`, `sh`; profile `bettor-arena-runtime-local`
- Skills: required upstream `shared-skills-infra`; repo-owned `harness-wiki`

## Evidence

- Verify/selftest: `python3 scripts/check_agent_runtime_module.py`
- Independent aggregate control/mutation: `sh proof_workflow/control_agent_runtime_module.sh --json`
- Portable execution proof: `sh loopctl/loopctl.sh skill-execution prove`
- Portable public-port control: `sh loopctl/loopctl.sh skill-execution test`

## External boundary

Not MCP-exposed. A local process receipt cannot proxy a physical sandbox, live host, live provider or Human Admit. `network=deny` and `network=allowlisted` fail closed until an admitted sandbox adapter can enforce and attest them.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Public input/output, named exits, required flags, effects or artifact contracts require an interface bump.
