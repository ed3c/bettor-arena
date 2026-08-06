---
type: Plan
title: Perfect-seed v2 execution plan (pointer and structure)
description: Structure and truth-layer discipline of plans/perfect-seed-v2/ — the canonical machine-readable plan for evolving the factory template from 1.1.0 to a standalone 2.0.0; a plan, not implementation evidence.
tags: [factory, plan, v2]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [v2-plan, truth-layers, ontology-placement]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Perfect-seed v2 execution plan (pointer and structure)

`loop_wiki/evolve-perfect-seed-repo-factory/plans/perfect-seed-v2/` is "the canonical, machine-readable execution plan for evolving the bounded factory from `perfect-seed-repo@1.1.0` to a standalone `perfect-seed-repo@2.0.0`. It is a plan, not implementation evidence. Creating this directory does not advance any milestone" (src: loop_wiki/evolve-perfect-seed-repo-factory/plans/perfect-seed-v2/README.md:3-6). This wiki page is a pointer-and-structure map; the plan directory is its own SSOT — "Do not mirror mutable plan definitions elsewhere" (src: README.md:10). The current [factory](overview.md) implements v1 (`perfect-seed-repo@1.1.0`, src: loop_wiki/evolve-perfect-seed-repo-factory/templates/template-metadata.json:3).

## Location decision

The plan deliberately lives factory-local instead of the generic `docs/plans/<date>-<topic>/` convention, following the human-approved factory-local boundary (src: README.md:8-10) — consistent with iron law 3's "sandboxes use their own directory as host dir" (src: ARCHITECTURE.md:47-48).

## Truth layers

Four layers, strictly ordered (src: README.md:12-21):

1. **Normative definitions** — `plan-registry.json` (twelve-milestone DAG, Work-Item definitions, exit criteria bound to oracle ids, policies; "never mutable progress"), `intended-architecture.json` (declared eight-base/dataflow topology and ownership), `oracle-registry.json` (pre-bound mechanical/behavioral/semantic/external/human oracles), each with a v1 schema under `schemas/`.
2. **Physical facts** — git commits, content-addressed receipts, append-only attestation refs (`refs/attestations/<candidate>/<axis>/<profile-sha>/<attestation-sha>`, axis ∈ cq/pu/architecture, final hash component so a retry cannot overwrite an earlier observation; src: README.md:96-104), Forgejo readbacks.
3. **Disposable projections** — `_engine-run/progress-projection.<head>.json`, automatic prompts, Forgejo issues, the RAG index.
4. **Human admission** — "Only a human admission artifact may derive `admitted`" (src: README.md:21).

No status is hand-edited into the plan registry; legal derived states are `pending`, `in_progress`, `implemented`, `verified`, `admitted`, `repair_required` (src: README.md:23-25).

## Ontology placement

v2 must materialize the reusable ontology under `templates/repo/.perfect-seed/` (schemas/, registries/, prompt-templates/, `seed-manifest.json`) and copy it into each generated repo; reset/extraction commands must reopen `seed-manifest.json` and classify every path as `ontology_owned`, `template_owned`, `materialized_input`, `runtime_generated`, or `user_domain_owned` — "never guess from filenames or erase user-owned files" (src: README.md:28-46).

## Directory responsibilities

From the plan's own table (src: README.md:49-63): `00-intent-and-knowhow.md` human intent + premise attacks; `CONTEXT.md` canonical language for fresh agents; `route-ledger.md` stateful SDLC route decisions; the three registries + `schemas/`; `invariants/` source-anchored brownfield facts (`factory-v1-and-central-primitives.md`); `docs/decisions/` sparse hard-to-reverse interface decisions (`attestation-and-rag.md`, `interface-boundary.md`); `01-*.md`…`12-*.md` thirteen executable vertical slices (00 through 12); `fixtures/` planned positive AND adversarial fixture contracts (good / hollow / scope-drift / stale) — "not passing evidence"; `dispatches/` exact planning/design packets (three design-interface dispatches); `validation/` planning-turn structural receipts that "validate the plan package, not the v2 product" (`plan-validation-receipt.json`); `implementation-notes.md` append-only execution ledger.

## Commit-card and dataflow contract

The planned commit card carries seven stable fields — `Work-Item`, `Slice`, `Intent`, `Scope`, `Prompts`, `Oracles`, `Evidence` — with prompts bound "by repo-relative ref plus hash" and volatile pending/pass state kept out of the message (src: README.md:91-94). The plan's dataflow diagram runs source intake → ontology/registries → deterministic Git genesis → 20-call reasoning → CQ-0 + focused oracle → candidate molecular commit → append-only attestations → derived progress → human admit (src: README.md:65-89) — an evolution of the same admit-terminal shape the v1 [workflow](overview.md) already enforces.
