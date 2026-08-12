# Four-repository routing traceability index

## Trace chain

```text
source / incident
→ repository decision
→ parent issue
→ molecular issue
→ sibling or true-child PR
→ eval / negative control
→ immutable subject
→ receipt / current evidence state
→ Human Admit
```

## Documentation stack

| Repository | Issue | Branch | Stack class | State |
|---|---|---|---|---|
| `bettor-arena` parent | #35 | n/a | parent contract | open |
| `bettor-arena` binding | #36 | `docs/document-routing-v1` | independent sibling | implementation branch |
| `skills-shared` method | #84 | `docs/document-routing-v1` | independent sibling | implementation branch |
| `runtime-env` binding | #29 | `docs/document-routing-v1` | independent sibling | implementation branch |
| `agent-shield-monorepo` binding | #77 | `docs/document-routing-v1` | independent terminal sibling | implementation branch |
| final exact index/cold-start audit | future bettor issue/PR | future branch | convergence leaf | `NOT_IMPLEMENTED` until siblings merge |

These branches are independent because each changes only its repository's documentation and consumes merged bytes. They are not a false serial stack. The final convergence leaf alone updates exact merged PR/commit references and runs the cross-repository cold-start route audit.

## Method lineage

- `knowledge-continuity`: no hidden background, knowledge outsourcing, or unexplained two-hop-to-evidence chain.
- `forgejo-delivery-loop`: local authoring, deterministic routing/outbox/recovery, receipt separation.
- `github-delivery-loop`: GitHub publication/Actions/merge state separation.
- `git-town-stacked-pr-worker`: sibling versus true-child, terminal leaf, convergence leaf, worktree/lease, no-push sync, Human boundaries.

## Current machine authorities

- `.agents/shared-skills.requirements.json`, `.agents/bindings/`, `.agents/module-set.json`
- `.runtime-env/requirements.json`, bindings, workloads, policies
- `.arena/modules/`, compositions, locks, contexts, origins, browser and MCP policies
- `loopctl/contract.json` and Bun/TypeScript MCP runtime
- `proof_workflow/` and `data/` receipts

Documentation completion does not imply cross-repository route-checker execution, GitHub/Forgejo equivalence, live Claude/Codex/browser/provider canaries, Agent Shield acceptance, or Human promotion.
