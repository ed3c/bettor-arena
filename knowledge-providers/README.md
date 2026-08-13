# Knowledge providers

This module owns provider-neutral contracts for symbolic, semantic, graph, and project-memory projections. Serena, GrepAI, Code-Graph-RAG, and Mem0 are candidate bindings, not a mandatory pipeline and not repository authorities.

## Data flow

```text
exact repository commit/tree + typed capability request
→ provider manifest + adapter/index identity
→ read-only query or evidence-bound memory proposal
→ subject-bound candidate receipt with provenance and staleness
→ current source/manifest/test/runtime readback
→ independent gate or Human Admit outside this module
```

## Owned contracts

- [`registry.json`](registry.json) selects exactly four initial candidate manifests.
- [`providers/`](providers/) records capabilities, immutable research pins, fallbacks, effects, and authority ceilings.
- [`contracts/`](contracts/) defines provider manifest, query request, query receipt, and memory proposal shapes.
- [`architecture-decision.md`](architecture-decision.md) compares capability families without declaring an unbenchmarked winner.
- [`host-state.md`](host-state.md) defines how to measure installed, running, wired, and data-ready without persisting a false live claim.
- [`scripts/check_knowledge_providers.py`](scripts/check_knowledge_providers.py) is the deterministic validator.
- [`tests/run-all.sh`](tests/run-all.sh) runs positive, hollow, and independent mutation controls.

## Current state

All four providers are `CANDIDATE / NOT_EXERCISED`. Their source pins are research identities only. No tracked byte claims that a provider is installed, healthy, indexed, wired, or admitted. Mutable machine state must be remeasured under [`host-state.md`](host-state.md); a host may keep the resulting untracked receipt in its own local-agent stack ledger.

## Hard boundaries

- Code providers are read-only at the Bettor boundary; rename is a plan, not an edit.
- Memory write/delete operations are proposals requiring Human Admit.
- A stale or subject-mismatched index cannot emit a promoted candidate result.
- Provider output cannot mark claims tested, write LoopX state, waive a gate, promote a release, or sign Human Admit.
- Provider stores are projections and must be rebuildable from canonical artifacts.

## Verification

```sh
sh knowledge-providers/tests/run-all.sh
```

The suite uses Python standard library only. Exit `0` means the checked contract passed, `2` means a planted or real contract violation was detected, and `64` means input could not be meaningfully checked.
