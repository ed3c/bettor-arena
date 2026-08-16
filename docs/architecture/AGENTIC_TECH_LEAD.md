# Agentic Tech Lead Architecture

The repository orchestrator is a compiler and scheduler of bounded Worker contracts, not a single-thread supervisor that continuously tells one Agent what to do.

```text
product goal
→ exact repository subject + architecture constraints
→ contract dependency DAG
→ path leases + branch topology
→ blindspot queries + evals + mutation controls
→ shared Tech Lead compiler
→ Worker packets
→ consumer runtime may allocate isolated Workers
→ Git Town synchronization
→ convergence after admitted dependencies
→ Human semantic conflict resolution / merge / promotion
```

## Tech Lead responsibilities

- turn the goal into explicit architecture constraints with owner tasks and verification;
- identify provided/consumed contracts before choosing branch order;
- use path-disjoint sibling branches for independent work;
- use a child branch only when it consumes an explicit unmerged parent contract;
- allocate aggregate indexes/registries/migrations to a convergence owner;
- require one blindspot query, source read-back route, eval, and negative/mutation control per task;
- cap concurrency by dependency, path lease, shared mutable resource, and budget;
- re-plan through a new immutable plan digest rather than silently widening a Worker packet.

## Worker boundary

A Worker receives one exact subject, goal/non-goals, branch parent/head, allowed/excluded paths, dependencies, contracts, assigned constraints, blindspot queries, evals, negative controls, cleanup, rollback subject, and Human-owned operations. It cannot change the architecture, widen paths, self-admit provider output, merge, publish, or resolve semantic conflicts unattended.

## Provider roles

- grepai: fuzzy Intent Anchor and bounded runtime MCP exploration.
- SCIP: emitted declarations/references/implementations for a pinned indexed subject and indexer.
- Tree-sitter: AST skeleton, edit boundary, and parse/error coverage.
- Serena: symbol-aware Agent executor after scope is narrowed.
- SQLite: authoritative normalized evidence/admission ledger.
- LanceDB: optional rebuildable similarity projection.
- source read-back/tests: admission gates.

## Adapter boundary

`scripts/agentic_tech_lead.py` only validates the consumer binding and invokes projected shared deterministic contracts. It does not create Git branches/worktrees, spawn Agents, invoke providers, contact Forgejo, merge, or publish. A later runtime adapter must emit separate receipts for those effects.
