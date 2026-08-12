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

## Documentation sibling set

| Plane | Issue | PR | Stack class | State |
|---|---|---|---|---|
| Parent integration contract | `#35` | n/a | parent | open |
| Integration / Acceptance | `#36` | `#37` | independent sibling | Draft |
| Instruction / Method | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | Draft |
| Runtime Contract | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | Draft |
| Domain Product / Reference Consumer | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | Draft |
| Exact merged index + cold-start audit | `#38` | future | convergence leaf | blocked by four PRs |

The four documentation PRs are siblings because each edits only its own repository and consumes merged inputs. They do not form a false serial Stack. Issue #38 is the only convergence owner; its branch must not be created until all four PRs merge.

Exact open-PR heads are read from GitHub PR metadata. Issue #38 will record immutable merged commits and trees.

## Method lineage

- `knowledge-continuity`: every hop leaves a local summary; no hidden background or unexplained index-to-index outsourcing.
- `forgejo-delivery-loop`: local authoring, deterministic routing/outbox/recovery, and receipt separation.
- `github-delivery-loop`: GitHub publication, Actions, and merge-state separation.
- `git-town-stacked-pr-worker`: sibling, true-child, terminal leaf, convergence leaf, worktree/lease, no-push sync, and Human boundaries.

## Machine authorities

- `.agents/shared-skills.requirements.json`, `.agents/bindings/`, `.agents/module-set.json`
- `.runtime-env/requirements.json`, bindings, workloads, and policies
- `.arena/modules/`, compositions, locks, contexts, origins, browser, and MCP policies
- `loopctl/contract.json` and the Bun/TypeScript MCP runtime
- `proof_workflow/` and `data/` receipts
- Agent Shield module release/status/receipts in its own repository

## Evidence boundary

Documentation completion does not imply route-checker execution, fresh Claude/Codex cold-start, GitHub/Forgejo equivalence, live browser/provider canaries, Agent Shield acceptance, external-release promotion, or production readiness.
