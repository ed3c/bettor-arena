# Parallel Tech Lead ADE — consumer architecture

Status: adoption layer landed, shared contracts partially bound. No Worker has
been spawned from it.

## Decision

Bettor adopts the shared Tech Lead contracts as a *consumer* rather than
reimplementing them. The split follows the ownership line the shared repository
already draws:

```text
skills-shared owns    portable procedure, schemas, deterministic checkers
this repository owns  paths, commands, budgets, provider endpoints, receipts
```

Concretely:

```text
git-town-stacked-pr-worker   fan-out contract: TOURNAMENT | COOPERATIVE |
                             SERIAL_STACK | HYBRID, and the laws that make a
                             plan refusable before a branch exists
dual-forge-repository-loop   task-DAG compilation into Worker packets
repo-agent-native            Blindspot evidence ledger and the coverage law
                             behind an absence claim
this repository              .agentic/parallel-tech-lead/ and
                             scripts/agentic/assert_parallel_tech_lead_contract.py
```

## Why the consumer gate does not call the shared checker

This is the decision most likely to look wrong later, so it is recorded with its
reason.

The shared skills are bound through `.agents/skills` symlinks pointing outside
this repository, at a shared-skills checkout on the developer's machine. That
target exists on a developer host. It does not exist on a GitHub Actions runner,
and it is not vendored into this repository.

A consumer gate that shelled out to the shared checker would therefore be green
locally and red in CI for an environment reason rather than a defect. Gates that
fail for environment reasons get disabled, and a disabled gate is worse than no
gate because it still reads as coverage.

So the consumer gate decides only what this repository's own files can decide,
and `config.json` records the shared contract each artifact targets along with
whether that skill is actually bound. Checking a plan against the shared fan-out
checker is a separate, host-bound operation.

## What "bound" means here, and what it does not

`bound_here` in `config.json` is a statement about
`.agents/shared-skills.requirements.json` — whether this repository has declared
it consumes that skill. The checker cross-checks the claim against that file and
refuses a `bound_here: true` the requirements do not support.

It is deliberately *not* a statement about the contents of the bound checkout.
At the time of writing, `repo-agent-native` is declared and its checkout tracks
Forgejo `main`, which does not yet carry the Blindspot contract that landed on
the GitHub side. Those are two different facts and collapsing them would let a
declared binding stand in for an available contract.

`git-town-stacked-pr-worker` and `dual-forge-repository-loop` are not declared
at all yet. Adding them to the requirements file is the next step, and it is a
separate change from this one.

## Template assertions

The staged bundle this layer replaces shipped
`REPLACE_WITH_REPOSITORY_TEST_COMMAND` as its acceptance oracle. A contract
whose oracle is a placeholder passes every structural check and proves nothing,
which is what #146 means by "replace template assertions".

The acceptance command is now `sh scripts/gates/verify_modular_contracts.sh` —
the argv `.github-delivery/ci-policy.json` already names as this repository's
local verification — and the checker opens the file to confirm it exists.
`PLACEHOLDER_IN_CONTRACT` refuses the pattern returning.

## Evidence boundary

A passing contract means the plan is internally consistent against this
repository's real paths and real acceptance command. It does not mean:

```text
a Worker ran                      no Agent is spawned by this layer
Git Town synchronised             git-town is not admitted on the local host
a Forgejo ancestry exists         publication is a separate lane
multiple Agents were cheaper      nothing here measures throughput
the shared contracts were checked  they are targeted, not executed
```

## Provenance

Reconciled from the staged Parallel Tech Lead bundle under
`ed3c/skills-shared#255`, which routed six consumer-owned paths to
`ed3c/bettor-arena#146` and recorded their digests. The bundle's own copies were
written before the shared fan-out and DAG contracts existed, so this layer is
authored against the landed schemas rather than restored from those bytes.
