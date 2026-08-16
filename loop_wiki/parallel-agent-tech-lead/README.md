# Parallel Agent Tech Lead — Bettor consumer plan

The generic fan-out law remains in `ed3c/skills-shared`. Bettor stores only the immutable upstream contract identity, repository-specific plan instances, a consumer validator/compiler, and execution-state receipts. No shared `SKILL.md` or generic fan-out checker is copied here.

Current upstream identity:

```text
repository   ed3c/skills-shared
commit       82a59bc9d253d9d77ea8bbdc493dd3689b423f52
schema       skills/git-town-stacked-pr-worker/references/FAN_OUT_CONTRACT.schema.json
schema blob  e00bbb99fdb1a8888ff6fd03ce792254319e2697
```

## State Machine

```text
EXACT UPSTREAM CONTRACT PINNED
→ BETTOR BASE COMMIT/TREE LOCKED
→ CONTEXT DIGEST + CONTEXT-FUNNEL RECEIPT BOUND
→ REAL DEPENDENCY/PATH GRAPH CLASSIFIED
→ TOURNAMENT | COOPERATIVE | SERIAL_STACK | HYBRID
→ BUDGETS / IMMUTABLE ACCEPTANCE ORACLES LOCKED
→ WORKER BRANCH/PATH/RESOURCE PACKETS COMPILED
→ HARD CONTROLS
→ PLAN PASS
→ execution remains NOT_EXERCISED until physical receipts exist
```

Mode selection follows the dependency graph rather than Agent count:

- `TOURNAMENT`: two or more incompatible competitors share one immutable base/context and may overlap only with other competitors on the competed surface.
- `COOPERATIVE`: independent siblings have disjoint writable paths and no unmerged-byte dependency.
- `SERIAL_STACK`: at least one child consumes explicit unmerged parent contracts/paths; stacking without consumed bytes is refused.
- `HYBRID`: a bounded tournament coexists with independent sibling or true dependency work under one convergence owner.

## Architecture invariants

Every plan locks one immutable base commit/tree, one context digest, one compiler-truth funnel receipt, immutable acceptance paths, at least two independent oracles, worker budgets, and Human-owned semantic operations before a Worker packet is emitted.

The consumer compiler rejects mutable bases, unequal context, concurrent path collisions, fake child edges, acceptance-test mutation, worker budget overflow, retired Code-Graph-RAG as a required provider, duplicate competitor strategies, premature/ambiguous convergence, topology/mode mismatch, DAG cycles, and automation authority escalation.

## Data flow

```text
skills-shared fan-out law (immutable identity)
        ↓
#138 exact-subject context-funnel receipt
        ↓
repository task/dependency/path facts
        ↓
plan.py validate
        ↓
plan.py compile
        ↓
content-addressed Worker packets
        ↓
Worker Fleet / worktrees / Git Town / Forgejo
        ↓
physical receipts (separate lane)
```

The compiler itself never creates a branch/worktree, launches an Agent, invokes Git Town, writes Forgejo/GitHub state, publishes, merges, promotes, rolls back, or resolves a semantic conflict.

## Executable contract

```sh
python3 loop_wiki/parallel-agent-tech-lead/scripts/plan.py validate plan.json
python3 loop_wiki/parallel-agent-tech-lead/scripts/plan.py compile plan.json --output receipt.json
sh loop_wiki/parallel-agent-tech-lead/tests/run-all.sh
```

The test suite exercises all four admitted topology classes and planted architecture violations. Its context-funnel evidence is explicitly synthetic fixture evidence; it proves the planner/checker mechanism only. Physical parallel Agents, live Git Town synchronization, Forgejo ancestry, model-quality uplift, token ROI, publication, merge, and release remain `NOT_EXERCISED` until exact receipts exist.

## Authority ceiling

```text
Tech Lead        task decomposition + architecture invariants + leases + topology
Worker           leased implementation only
Gates            observe/assert only
LoopX reducer    canonical task state writer
Human/policy     semantic conflict, winner admission, merge/ship, promotion, rollback
```
