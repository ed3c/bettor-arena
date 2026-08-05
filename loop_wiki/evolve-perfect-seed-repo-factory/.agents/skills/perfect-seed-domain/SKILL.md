---
name: perfect-seed-domain
description: |
  Interprets perfect-seed repo-factory packets, reduced IR, twenty-call traces, and human-admit boundaries. Use inside evolve-perfect-seed-repo-factory when routing or checking one physical source packet.
---

# perfect-seed-domain

## Procedure

1. Match exactly one source kind from the typed packet.
2. Preserve source, evidence, claims, unknowns, decisions, calls, and lineage as separate records.
3. Validate exact twenty-call count and dependency order mechanically.
4. Label deterministic observations `technical_equivalent`, unjudged design `candidate`, inference `[推論]`, and admission `human_required`.
5. Return one named failure edge; never use “retry as needed”.

## Boundary

This skill owns local vocabulary only. It does not own macro orchestration,
external truth, generated-repo mutation, or seed admission.
