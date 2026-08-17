# AGENTS.md — Tech Lead + Shadow closure monitor

This directory owns the closure audit and the Local Handoff handoff description.
It does not own runtime execution, Git reconciliation, provider activation,
Human admission, PDF queue advancement, or release.

## Mandatory read order

1. repository root `AGENTS.md`
2. repository root `README.md`, `CONTEXT.md`, and `ARCHITECTURE.md`
3. `docs/INDEX.md`
4. this `README.md`
5. `closure-matrix.json`
6. `docs/traceability/local-handoff-execution-queue.json`
7. `docs/git/pdf-terminal-sequence.json`
8. `docs/integration/CROSS_REPO_INTEGRATION.md`
9. the active issue and exact GitHub base/head/checks
10. the nearest implementation README/contracts/tests/receipts

Treat a missing issue, receipt, local path, provider identity, exact subject, or
Human decision as `ABSENT`. Do not reconstruct it from chat history.

## Tech Lead procedure

1. Bind the exact repository commit/tree and rollback subject.
2. Classify every claim as source proposal, mechanism, deterministic evidence,
   live/physical evidence, Human admission, or release.
3. Map every unresolved problem to one owner issue and one State Machine.
4. Compile the task DAG.
5. Assign one writer, branch/worktree, path lease, resource lease, and
   convergence owner.
6. Require positive, independent control, and planted mutation evidence.
7. Create a Local Handoff item when the next proof needs a host or runtime not
   available in the current session.
8. Stop before semantic conflict, Human admission, release, or rollback unless a
   typed exact-subject controller owns the transition.

## Independent Shadow procedure

The Shadow uses the same immutable subject but a separate evaluation path.

The Shadow must check:

```text
requirement applicability
contradictions between docs/contracts/source/runtime
global objective versus local task PASS
evidence ceiling and false promotion
missing denominator / stale subject / wrong workspace
writer/path/resource collision
rollback and cleanup
```

The Shadow emits findings only. The Shadow must not:

```text
edit the Builder branch silently
become a second queue or state writer
turn fixture PASS into live PASS
turn deterministic convergence into Human admission
guess a semantic conflict
persist private reasoning
```

## Queue law

There is one canonical consumer queue:

```text
docs/traceability/local-handoff-execution-queue.json
```

`docs/git/local-handoff-execution-queue.json` is forbidden. A second queue is a
blocking authority conflict.

Each epoch binds one immutable subject. The current epoch contains one item:

```text
ACTIVE  ed3c/bettor-arena#172 dual-origin reconciliation
```

After reconciliation, generate a new exact-subject epoch for:

```text
#161 → #146 → #140
```

Do not mutate the old epoch to follow a moving branch.

## DAG law

Use relation types precisely:

```text
SIBLING             path-disjoint implementation
TRUE_CHILD          consumes unmerged parent bytes
CONVERGENCE         one owner of shared indexes/locks/final integration
PROCESS_DEPENDENCY  must occur earlier but is not Git ancestry
EXTERNAL_EVIDENCE   independent receipt lane with no Stack paths
HISTORICAL          preserved forensic subject, not a current writer
```

Queue order is not a reason to create a deep Git branch chain.

## Writer and path leases

Before editing, record:

```text
issue and branch
base and exact head
allowed/read-only/forbidden paths
consumed/provided artifacts
writer/worktree/resource leases
positive/control/mutation commands
cleanup and rollback
Human boundary
```

Stop when another active PR owns an overlapping path. PR #81 is historical and
must not regain the README/AGENTS/State-Machine/Stack-index writer lease.

## Completion checks

Run:

```bash
python3 scripts/gates/check_tech_lead_shadow_closure.py
python3 scripts/gates/check_tech_lead_shadow_closure.py --selftest
python3 scripts/gates/check_local_handoff_execution_queue.py
python3 scripts/gates/check_local_handoff_execution_queue.py --selftest
python3 -m unittest -q tests/test_tech_lead_shadow_closure.py
```

A green result proves the current document/queue/index subject only. Report all
remaining `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`,
`HUMAN_ADMIT_REQUIRED`, and blocked states.
