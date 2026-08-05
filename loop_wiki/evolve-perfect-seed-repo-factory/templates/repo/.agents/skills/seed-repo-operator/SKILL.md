---
name: seed-repo-operator
description: |
  Operates a generated perfect-seed candidate from local evidence through an exact twenty-call dependency graph. Use when a task must be reasoned from this repo's source, claims, unknowns, decisions, and lineage without hidden chat state or external calls.
---

# seed-repo-operator

## Role

Turn one explicit task into exactly twenty local function calls. The skill uses
the repo's reduced IR to lower ambiguity; it does not claim semantic perfection,
external research, or independent model consensus.

## Workflow

1. Match：read `data/source.json`; reject a task that contradicts the admitted source kind.
2. Generate：run `bun run scripts/plan.ts --task "<task>"`.
3. Validate：run `bun run quality:fast` before `bun test`; inspect
   `data/call-plan.json` and `data/call-results.jsonl`.
4. Record：keep task hash, source hash, dependencies, and result hashes intact.
5. Observe：compare new results with prior task traces before replacing them.
6. Admit：surface the next action to the human; never auto-admit the seed or a repo mutation.

## Data structures

- `evidence.jsonl`：append-only physical observations.
- `claims.jsonl`：claims bound to evidence ids.
- `unknowns.json`：KK/KU/UK/UU inventory.
- `decisions.jsonl`：grounding and human-gate ledger.
- `call-plan.json`：twenty-call DAG.
- `call-results.jsonl`：hash-bound outputs.
- `artifact-manifest.json` and `lineage.json`：materialization provenance.

## Failure edges

- Missing or malformed local data → stop; do not infer it from chat.
- Missing dependency, duplicate call, or non-20 count → stop and repair the operator.
- External truth needed → emit `human_required` and route to an authorized research workflow.
- Repo mutation requested → produce a bounded implementation slice; require tests and human admit.

## Boundary

These are twenty deterministic repo-local reasoning functions, not twenty MCP,
browser, network, LLM, or independent judge calls.
