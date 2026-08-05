# Intent and know-how

## Original intent

Evolve the existing bounded factory so a DR, GCR, readable repo, or physical
`grill-me` record produces a standalone Git repo that contains:

- a resettable, hash-bound perfect-seed ontology and initial-seed boundary;
- runnable code and three repo-local skills for reasoning, perception, and
  terminal implementation;
- exact twenty-call local reasoning over entropy-reducing data structures;
- traceable Work-Items, terminal slices, candidate commits, asynchronous
  attestations, Forgejo projections, progress, drift, and repair prompts;
- physical oracles proving intended behavior rather than file presence or agent
  self-report.

“Perfect” remains an optimization target. It is never an automatic status.

## Shared-understanding decisions

The human explicitly accepted the following design constraints during the
planning interview. This file is the first physical serialization of that
conversation; the raw application transcript is not a repo artifact, so these
rows are human-confirmed reconstruction, not byte-range transcript evidence.

1. A commit claims closure only for one terminal slice; repo-level graph checks
   global invariants.
2. Architecture perception has three artifacts: intended graph, observed graph,
   and conformance/difference projection.
3. Plan definition is normative; progress is derived from Git, receipts,
   attestations, and readbacks.
4. One local Work-Item is one terminal slice and one candidate molecular commit;
   a Forgejo issue is a recoverable projection.
5. A commit message is a concise, repo-relative RAG index card; full evidence is
   in a hash-bound manifest.
6. Fixed, automatic, and emergent prompt contexts are distinct, hash-bound
   prompt-cache roles. Automatic prompts are derived from current physical
   projection, not confused with fixed text.
7. Same slice + expected HEAD + leased paths + unchanged exit criteria may
   generate a bounded repair prompt. Scope, dependency, plan, architecture, or
   invariant expansion requires a new repair proposal and human admission.
8. CQ-0 runs synchronously before a candidate commit: minimum lineage,
   changed-path format/lint, affected TypeScript project closure, strict type
   checking, dependency boundary, then focused behavior. Unprovable closure
   falls back to full repo.
9. Expensive CQ-1, Production Use, and architecture conformance may run
   asynchronously against the immutable candidate. Merge, release, and
   admission remain blocked until current passing attestations exist.
10. Attestation refs are append-only and profile/candidate bound. Forgejo is not
    their truth store.
11. The generated repo contains exactly three product skills:
    `seed-repo-operator`, `repo-neural-perception`, and
    `repo-terminal-operator`. Forgejo operation remains an external adapter.
12. The canonical skill templates live under the factory template and are
    materialized into generated repos. The generated repo has no runtime
    dependency on the mother repo.
13. Forgejo outage does not block local CQ-0 or candidate commit. It blocks
    merge, release, and admission until projection/readback closes.
14. Every exit criterion pre-binds a mechanical, behavioral, semantic,
    external, or human oracle and a non-literal falsifier.
15. Scope is this factory plus only necessary generic extraction from the mother
    repo. It is not a refactor of the plan-truth mother loop.
16. `perfect-seed-repo@1.1.0` remains supported. V2 is
    `perfect-seed-repo@2.0.0` with an explicit migration receipt and no silent
    semantic upgrade.
17. LanceDB is not pre-admitted. A real local LanceDB-versus-SQLite-FTS5 spike
    decides. The RAG index is always rebuildable projection and never a gate.

## Brownfield

Yes. The current factory already materializes and validates v1.1 repos and has
an uncommitted CQ-preflight overlay. The mother repo already has lineage,
verification projection, terminal operator, and Forgejo primitives. Those
primitives are candidates for extraction, not runtime dependencies or presumed
equivalents.

## Premise disproof

- **Existing v1.1 already solves it:** false. It has only the reasoning skill,
  no Work-Item, graphs, full CQ/PU lifecycle, Forgejo, attestation refs, repair
  projection, seed-boundary reset, or RAG projection.
- **Mother repo profiles can simply be copied:** false. The central contracts
  are plan-truth-specific, require absolute-path-heavy commit messages, and the
  generated repo would cease to be standalone.
- **A mutable event log should own all progress:** rejected. It makes ontology
  reconstruction depend on replay and creates a second plan truth source.
- **A declarative registry alone is enough:** incomplete. Execution still needs
  an immutable, portable capability packet and a one-attempt lease envelope.
- **CQ/PU must block every commit:** rejected as too slow. CQ-0 blocks candidate
  commit; expensive axes block promotion.

## Selected interface synthesis

Use declarative registries for ontology and intent definitions, an immutable
capability packet plus lease-bound terminal envelope for a portable execution
closure, and append-only attestations for observations. Event/CAS state machines
may exist inside asynchronous workers for leases, cancellation, and races; they
must not become plan or ontology SSOT.

The v2 repo must have a deterministic Git genesis because HEAD/tree, leases,
candidate commits, stale detection, and attestation refs are otherwise
undefined. Fresh-clone reconstruction is an exit criterion, not an assumption.

## Non-goals

- Claiming universal or omniscient “complete neural perception”. The legal
  claim is complete coverage of a declared observation closure plus explicit
  blind spots.
- Copying private DR/GCR text into Git. Opaque source refs and hashes are legal.
- Auto-admission by an LLM, test runner, Forgejo issue, or RAG retrieval score.
- Replacing all central plan-truth code or retrofitting its historical commits.

## Open questions

None changes the planned architecture. The implementation spike still decides
the RAG backend; that is an intentional measured milestone, not unresolved
intent.
