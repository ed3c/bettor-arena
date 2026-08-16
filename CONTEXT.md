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

The attached 41-page PDF is a source proposal. Current checked-tree state is:

```text
LoopX mechanism bytes                IMPLEMENTED across the terminal directories
ordered acceptance prefix            COMPLETE for orders 0–11
active terminal                      order 12 / issue #92
selected release composition         14 base modules; LoopX terminals excluded
aggregate module evidence            NOT_EXERCISED
six-host and provider live matrices  NOT_EXERCISED
Git Town executable/config           ABSENT
final convergence                    issue #68 pending
```

The previous statement that the kernel, Strategy/HITL, runtime fabric, fleet, memory and Console were not implemented is stale: their mechanisms have landed. The opposite claim—“the full PDF architecture is integrated”—is still false because merged bytes do not create ordered acceptance, composition selection, live receipts or release admission.

Read:

- [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
- [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

## Current publication and Stack convergence

Measured on 2026-08-16:

```text
local main / forgejo main  8d47fc1c9dfd1550c1f45504f6c11fc1f04f6a0b
GitHub main                 c72109e145193fdaf059944403477f01064a1c3d
shared Git tree             0c51ea279bd2036dce281898c2e980e8378ba1cb
observed relation           same-tree
tracked origin receipt      NOT_EXERCISED
active ordered terminal     #92
final convergence           #68
```

The Git-object observation cannot overwrite [`data/origins/status.json`](data/origins/status.json), whose live origin/equivalence lanes remain `NOT_EXERCISED`.

The exact `git-town-stacked-pr-worker` method pin remains `skills-shared@c5750720d960a228a0d9419f28125c09d064e3e1`, blob `eb2d915bca3e8a3938625f7d33a10fae95a15769`. Bettor's current shared binding source `b3c722da1c40301b0a12e0ef99848d884bfc720b` contains the same blob, but the Skill is `NOT_SELECTED`. PR #133 landed the typed fail-closed controller and its controls; the actual Git Town executable, `.git-town.toml`, supply-chain/legal admission and live no-push run remain absent or unexercised.

Current open GitHub issue snapshot is `#5 #24 #41 #44 #45 #61 #68 #83 #88 #91 #92 #108`. Issue closure alone is not queue completion; the complete implementation-PR/queue-state split is in the root [`README.md`](README.md).

## Glossary

- **admit**: a state transition applied by the automated-admission controller to an exact subject after policy and all required external decision inputs are present. Activation admit, ratification and irreversible removal admit are distinct; green gates only create a candidate.
- **Intent-Slice**: Micro-loop commit anchor `ISSUE-<n>`; Macro infrastructure work does not invent a slice.
- **protected surface**: gate/hook closure. Molecular commit requirements depend on the triggering role and staged paths.
- **commit role**: Micro loop versus Macro/infrastructure determines commit-message contract.
- **receipt**: machine-verifiable execution claim. Historical receipts are immutable except through an explicit migration/re-run mechanism.
- **evidence allowlist**: named historical evidence exceptions; each is standing debt.
- **candidate**: mechanically green, waiting for an exact-subject automated-admission receipt; not a merge instruction by itself.
- **wiki-update request / receipt**: typed request and consuming receipt between the seed factory and OpenWiki; emergent content stays backlog, not normative law.
- **LoopX kernel**: single-writer task-state authority over Objective, Todos, Gates, Evidence and Quota. Its mechanism is implemented; final composition and live end-to-end acceptance are not.
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
