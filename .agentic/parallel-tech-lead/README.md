# Parallel Tech Lead adoption layer

This is Bettor's consumer side of the shared Tech Lead contracts. It answers one
question the shared body deliberately does not: *what are this repository's real
paths, real acceptance command, and real budgets*.

```bash
python3 scripts/agentic/assert_parallel_tech_lead_contract.py check
python3 scripts/agentic/assert_parallel_tech_lead_contract.py selftest
```

## Why the checker is self-contained

The shared contracts live in `skills-shared` and reach this repository through
`.agents/skills` symlinks into a developer host's checkout. A GitHub Actions
runner has no such checkout. A consumer gate that executed the shared checker
would pass locally and fail in CI for an environment reason, and an environment
failure is the kind that gets a gate switched off.

So this layer asserts what can be decided from this repository's own files, and
`config.json` records which shared contract each artifact targets. Conformance
against the shared checker is a separate, host-bound check — not a claim made
here.

## What it refuses

| Code | Refused shape |
|---|---|
| `PLACEHOLDER_IN_CONTRACT` | `REPLACE_WITH_*` anywhere in the layer |
| `ACCEPTANCE_COMMAND_NOT_REAL` | an acceptance command naming a file this repository does not have |
| `SHARED_CONTRACT_UNBOUND_BUT_CLAIMED` | `bound_here: true` for a skill absent from `.agents/shared-skills.requirements.json` |
| `BASE_NOT_IN_REPOSITORY` | a plan base that is not a commit here, or a base declared mutable |
| `LEASE_OVERLAP` | concurrent Workers writing the same path |
| `ACCEPTANCE_PATH_WRITABLE` | a Worker leasing the gate it is scored against |
| `CONVERGENCE_MISSING_INPUT` | a convergence owner that does not depend on what it converges |
| `HUMAN_OPERATION_DROPPED` | automatic winner admission or semantic merge |

The first two are why this exists. #146 asked for template assertions to be
replaced because the staged bundle shipped
`REPLACE_WITH_REPOSITORY_TEST_COMMAND`: a contract whose oracle is a placeholder
passes every check and proves nothing. The acceptance command here is
`sh scripts/gates/verify_modular_contracts.sh`, the argv
`.github-delivery/ci-policy.json` already names, and the checker opens the file
to confirm it exists.

## Current binding state

```text
repo-agent-native            listed in shared-skills.requirements.json
git-town-stacked-pr-worker   NOT listed -- add it before checking a plan against
                             the shared fan-out checker
dual-forge-repository-loop   NOT listed -- same, for the task-DAG compiler
```

The bound `repo-agent-native` checkout tracks Forgejo `main` and does not yet
carry the Blindspot contract from `ed3c/skills-shared#248`. `bound_here` in
`config.json` records the requirements-file state, not the checkout's contents,
and the checker refuses a `bound_here: true` that the requirements file does not
support.

## The example plan

`plan.example.json` is `COOPERATIVE`: two gates that do not read each other's
files, plus the index that lists them. It is the smallest shape in this
repository that is genuinely path-disjoint and still needs a convergence owner.

It is not a `TOURNAMENT` because "does this gate hold" has one right answer, and
several differentiated implementations of one right answer measure sampling
noise. Tournaments are for questions with more than one defensible shape.

## What this layer does not do

It creates no branch, worktree or Agent, spawns nothing, and merges nothing.
A `PARALLEL TECH LEAD CONTRACT PASS` says the plan is internally consistent
against this repository's real paths. It says nothing about execution.
