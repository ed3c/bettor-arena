# Architecture — bounded repo factory

## Reduced IR

| record                                    | entropy removed           | information preserved                             |
| ----------------------------------------- | ------------------------- | ------------------------------------------------- |
| `source.json`                             | ambiguous origin          | source kind, packet/task hashes, gate             |
| `evidence.jsonl`                          | free-form corpus search   | stable ids, refs, hashes, excerpts                |
| `claims.jsonl`                            | unsupported assertions    | claim→evidence bindings and grounding             |
| `unknowns.json`                           | unspoken uncertainty      | KK/KU/UK/UU rows                                  |
| `decisions.jsonl`                         | hidden routing            | state, decision, evidence, grounding              |
| `capabilities.ts`                         | ad-hoc tool choice        | twenty named functions and DAG edges              |
| `call-plan.json`                          | implicit execution order  | exact task and dependency order                   |
| `call-results.jsonl`                      | unverifiable prose        | input/output hashes per call                      |
| `lineage.json` + manifest + build receipt | artifact origin ambiguity | packet, template, task, manifest, and file hashes |

## Boundary

The factory template is the code SSOT. Generated repos are versioned products.
Runtime call plan/results may change per task; source evidence and lineage must
not be rewritten to make a result look better.

Repo intake is bounded to 200 non-ignored files and 128 KiB excerpts per file.
Large files retain a hash and explicit `N/A-binary-or-large` excerpt reason.

## Gate order

```text
minimum lineage
  -> Prettier --check
  -> typed ESLint
  -> strict tsc --noEmit
  -> behavior/operator tests
  -> full generated-repo validation
  -> future asynchronous Code Quality + Production Use axes
  -> human admit
```

`src/run_fast_quality.ts` emits a hash-bound-input runtime receipt with the
claim boundary `preflight-only-not-code-quality-axis`. Passing it means only
that cheap deterministic defects were not found. It does not prove production
behavior, semantic intent success, or either asynchronous verification axis.
