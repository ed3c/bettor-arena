# `parallel-agent-tech-lead` module

Machine authority: [`module.json`](module.json)

This module is the Bettor-owned consumer of the canonical fan-out procedure in `ed3c/skills-shared`. It owns repository-specific plan instances and executable assertions; it does **not** copy or fork the shared SKILL body or generic fan-out checker.

## Pinned subjects

The current consumer contract is pinned to:

```text
skills-shared main subject: 82a59bc9d253d9d77ea8bbdc493dd3689b423f52
fan-out schema blob:        e00bbb99fdb1a8888ff6fd03ce792254319e2697
context-funnel parent:      9ec507f685c9f3d0fcf97238d036a22be92fddf5
```

These are readback identities, not claims that Git Town, Forgejo, or physical Workers executed.

## State Machine

```text
exact merged base subject
→ exact compiler-truth context receipt
→ immutable acceptance/oracle lock
→ dependency + writable-path graph
→ topology derivation
   ├─ TOURNAMENT
   ├─ COOPERATIVE
   ├─ SERIAL_STACK
   └─ HYBRID
→ budget + authority validation
→ Worker packet compilation
→ PLAN_VALIDATED
→ execution lanes remain NOT_EXERCISED
```

## DAG and data flow

```text
skills-shared fan-out contract identity
        │
        ├─ context-funnel exact subject/digest
        ├─ immutable acceptance paths + hard gates
        ├─ Worker roles/dependencies/path leases
        └─ token/time/retry/process/output budgets
                         │
                         ▼
                Bettor plan compiler
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        sibling Worker  child     competitor
        packet          packet    packet(s)
              │          │          │
              └──────────┼──────────┘
                         ▼
               explicit convergence owner
```

A `SERIAL_STACK` edge is valid only when the child consumes declared unmerged contracts or paths from its parent. Path-disjoint siblings may run concurrently. Tournament competitors may intentionally overlap their target surface because only one may be admitted; competitors cannot silently exchange or cherry-pick semantic pieces.

## Public control port

```sh
python3 loop_wiki/parallel-agent-tech-lead/scripts/plan.py --help
sh loop_wiki/parallel-agent-tech-lead/tests/run-all.sh
```

## Authority ceiling

`PLAN_VALIDATED` proves only that the repository-owned fan-out plan is internally consistent and bound to an exact context subject. It does not prove that an Agent ran, Git Town restacked, Forgejo mirrored ancestry, a PR was published, a winner was admitted, a semantic conflict was resolved, or a release was promoted. Those lanes require their own receipts and remain `NOT_EXERCISED` until then.

Human/Tech-Lead ownership is retained for winner admission, semantic conflict resolution, merge/ship, release promotion, and architecture exceptions. Automatic publication, automatic semantic merge, acceptance-test mutation, required Code-Graph-RAG routing, fake stack dependencies, mutable bases, unequal tournament context, and unbounded Worker budgets are refused.

## Evidence

The module proof exercises all four topologies plus planted failures for mutable base, context drift, path collision, fake child dependency, DAG cycle, budget overflow, acceptance-oracle mutation, retired provider activation, duplicate competitor focus, premature convergence, and authority escalation. Physical parallel Agents, live Git Town synchronization, Forgejo execution, ranking uplift, token ROI, publication, and release remain outside this proof.
