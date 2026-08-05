# Decision: registry definitions + capability packet + terminal envelope

## Status

Planned and human-aligned; implementation not admitted.

## Context

V2 needs resettable ontology, portable terminal execution, derived progress,
asynchronous evidence, and standalone operation. A single mutable registry
cannot safely carry execution state, while a pure event-sourced core makes a
slice unintelligible without replay.

## Alternatives compared

### A. Append-only event core

Expose `appendEvent()` and `project()` and retain all execution history in a Git
ref chain. This gives excellent sequencing and retry auditability but makes
ordinary Work-Item understanding depend on replay. It remains appropriate
inside async lease/cancel/race machinery.

### B. Registry-first compiler

Compile declarative plan, architecture, oracle, and skill registries with Git
and receipts. This cleanly separates ontology from runs and supports seed reset,
but by itself lacks a portable per-slice authorization closure.

### C. Capability packet and terminal envelope

Give each slice an immutable packet and each attempt a leased envelope. This is
portable and easy to verify in a clean clone, but without registries it repeats
global definitions and can obscure repo-wide invariants.

## Decision

Synthesize B + C. Registries are ontology/intent SSOT. The capability packet is
the immutable terminal closure. The envelope is one execution grant. Physical
attestations are append-only observations. Event/CAS mechanics remain private to
the async worker lifecycle.

Public deep operations should converge on `reason`, `perceive`, and `execute`,
not dozens of registry getters or writable status methods.

## Consequences

- A change to intent, oracles, architecture requirements, base snapshot, or
  scope creates a new capability packet.
- Lease expiry alone creates a new envelope for the same packet.
- No public `setStatus`, `markPassed`, or `markStale` operation exists.
- Slice closure never substitutes for repo-level architecture conformance.
