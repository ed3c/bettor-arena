# `knowledge-providers` module

Machine authority: [`module.json`](module.json)
Interface version: `1.0.0`

## Role

Defines a provider-neutral boundary for optional symbol, semantic, graph, and project-memory projections. Provider output remains a subject-bound candidate or proposal and cannot replace current source, tests, receipts, gates, or Human Admit.

## Public port

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `knowledge-providers` | provider | `1.0.0` | control-only | `python3 knowledge-providers/scripts/check_knowledge_providers.py` |

## Capability boundary

**Provides**

- `knowledge-provider.contracts/v1`
- `knowledge-provider.candidate-receipt/v1`
- `knowledge-provider.memory-proposal/v1`

**Requires**

- `arena.module-catalog/v1`
- `arena.passive-context/v1`

## Owned implementation root

- `knowledge-providers/`

## Evidence

- Verify/control: `python3 knowledge-providers/scripts/check_knowledge_providers.py check --root knowledge-providers`
- Positive, hollow, and mutation controls: `sh knowledge-providers/tests/run-all.sh`
- Host-state protocol: `knowledge-providers/host-state.md`; live results remain remeasured host receipts, not proof of this module

## External boundary

This module performs no live provider call, network access, code edit, direct memory mutation, state transition, gate verdict, release promotion, or Human Admit. Live adapters require a separately admitted runtime identity, exact index subject, canaries, cleanup evidence, and paired A/B results.

## Change discipline

`module.json` owns interface, closure, effects, and proof commands. Provider manifests own candidate capability and authority ceilings. The human README and ADR are navigation and rationale, not a second machine API.
