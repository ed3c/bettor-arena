# CONTEXT.md — bettor-arena current handoff and glossary

## Four-repository handoff

`bettor-arena` is the **Integration / Acceptance Plane**:

```text
skills-shared
  procedural Skills and method/eval contracts
        |
        v
runtime-env
  secret-free variable/module/profile/workload/policy closure
        |
        v
bettor-arena
  module composition, proof/control/mutation, Context Capsules,
  stateless MCP, project bootstrap, origin and external-release acceptance
        |
        v
agent-shield-monorepo
  domain product modules, provider adapters, and product canaries
```

The arrows are immutable contracts and bindings—not mutable checkout imports. Local Skill symlinks are development projections. Reproducible identity is an exact commit/tree/release manifest plus bindings, locks, digests, and receipts.

The common route names and assertions are in [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md). Cross-repository flow is in [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).

## Current documentation stack

Parent issue: `#35`. Independent sibling documentation issues: bettor `#36`, `skills-shared#84`, `runtime-env#29`, and `agent-shield-monorepo#77`. After all four merge, a separate bettor convergence leaf will pin exact merged PR/commit identities and run the cold-start route audit.

## Glossary

- **admit**: human decision on a state transition. Activation admit, ratification, and irreversible removal admit are distinct; green gates only create a candidate.
- **Intent-Slice**: micro-loop commit anchor `ISSUE-<n>`; Macro infrastructure work does not invent a slice.
- **protected surface**: gate/hook closure. Molecular commit requirements depend on the triggering role and staged paths.
- **commit role**: Micro loop versus Macro/infrastructure determines commit-message contract.
- **receipt**: machine-verifiable execution claim. Historical receipts are immutable except through an explicit migration/re-run mechanism.
- **evidence allowlist**: named historical evidence exceptions; each is standing debt.
- **candidate**: mechanically green, waiting for Human Admit; not a merge instruction.
- **wiki-update request / receipt**: typed request and consuming receipt between the seed factory and OpenWiki; emergent content stays backlog, not normative law.

## Evidence boundary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A route document, module declaration, symlink, package, old SHA, source proposal, or another environment cannot produce live PASS.
