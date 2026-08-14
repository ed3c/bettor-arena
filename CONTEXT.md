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

The arrows are immutable contracts and bindings—not mutable checkout imports. Local Skill symlinks are development projections. Reproducible identity is an exact commit/tree/release manifest plus bindings, locks, digests and receipts.

The common route names and assertions are in [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md). Cross-repository flow is in [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).

## Current PDF Harness handoff

The attached 41-page PDF is a source proposal. The current audit concludes:

```text
modular Harness foundation       IMPLEMENTED
complete LoopX state kernel      NOT_IMPLEMENTED
six-host live matrix             NOT_EXERCISED
provider live matrix             NOT_EXERCISED / NOT_IMPLEMENTED
cloud/local equivalent run       NOT_EXERCISED
observability and HITL console   NOT_IMPLEMENTED
```

Do not infer a LoopX kernel from the names `loopctl` or `loop-runtime`. The missing canonical pieces are Objective/Todos/Quota task state, a single-writer event ledger, reducer, LangGraph command/HITL port, evidence-bound episodic memory, worker canaries and runtime/observability receipts.

Read:

- [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
- [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

## Current documentation convergence

Parent issue: `bettor-arena#35`.

Merged independent siblings:

```text
bettor-arena#37              1f94d3d77992a1396959a15b2ada7836c07bf300
skills-shared#85             e3b327ad49c088f1962c33167ecd5ac9d28125fb
runtime-env#30               4a333ccf106ef60bc6942b922b7f5efffb3876f5
agent-shield-monorepo#78     1af04c1ef5cb68eab198987feba008c93d3ec22f
```

`bettor-arena#38` now owns the convergence leaf. Branch:
`integration/pdf-harness-convergence-v1`.

Git Town repository configuration is `ABSENT`; molecular sibling/child/terminal/convergence semantics are policy vocabulary, not proof that Git Town CLI is active.

## Current implementation leaves

```text
#43  repo-agent-native consumer binding          MERGED
#48  portable Skill + six-host contract          MERGED
#50  host-owned typed-argv Skill runner          MERGED
#51  provider-neutral query/memory contracts     MERGED
#56  paired fixture-only provider evaluator      OPEN; mixed checks
#53  historical diverged aggregate               OPEN; non-authoritative
#24  immutable Agent Shield reference consumer   OPEN
```

Current issue/PR metadata remains authoritative. Read the Stack index before changing a branch or generated lock.

## Glossary

- **admit**: Human decision on a state transition. Activation admit, ratification and irreversible removal admit are distinct; green gates only create a candidate.
- **Intent-Slice**: Micro-loop commit anchor `ISSUE-<n>`; Macro infrastructure work does not invent a slice.
- **protected surface**: gate/hook closure. Molecular commit requirements depend on the triggering role and staged paths.
- **commit role**: Micro loop versus Macro/infrastructure determines commit-message contract.
- **receipt**: machine-verifiable execution claim. Historical receipts are immutable except through an explicit migration/re-run mechanism.
- **evidence allowlist**: named historical evidence exceptions; each is standing debt.
- **candidate**: mechanically green, waiting for Human Admit; not a merge instruction.
- **wiki-update request / receipt**: typed request and consuming receipt between the seed factory and OpenWiki; emergent content stays backlog, not normative law.
- **LoopX kernel**: proposed single-writer task-state authority over Objective, Todos, Gates, Evidence and Quota. It is currently `NOT_IMPLEMENTED`.
- **strategy graph**: proposes typed commands; it never commits canonical state.
- **Worker**: executes in a leased workspace and submits artifacts/events; it cannot decide gate or state.
- **decision-memory capsule**: externalized, evidence-bound observation/dead-end/decision package. It is not private chain-of-thought.
- **terminal leaf**: one reviewable behavior plus its eval/evidence.
- **convergence leaf**: shared locks, indexes and final acceptance after terminal leaves settle.

## Evidence boundary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A route document, PDF diagram, module declaration, symlink, package, old SHA, source proposal, fixture or another environment cannot produce live PASS.
