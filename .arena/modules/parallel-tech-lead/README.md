# parallel-tech-lead

Consumer adoption layer for the shared Tech Lead contracts.

```text
.agentic/parallel-tech-lead/   config, example plan, layer README
scripts/agentic/               the gate
```

The shared body owns the portable contract; this module owns what only this
repository can state: real paths, a real acceptance command, real budgets, and
which shared contract each artifact targets.

```bash
python3 scripts/agentic/assert_parallel_tech_lead_contract.py check
python3 scripts/agentic/assert_parallel_tech_lead_contract.py selftest
```

`selftest` plants ten defects and requires each to be refused by its own code.
Two of them are why the module exists: `PLACEHOLDER_IN_CONTRACT` and
`ACCEPTANCE_COMMAND_NOT_REAL`. The bundle this layer replaces shipped
`REPLACE_WITH_REPOSITORY_TEST_COMMAND` as its oracle, and a contract whose
oracle is a placeholder passes every structural check while proving nothing.

## Why the gate does not call the shared checker

The shared skills are reached through `.agents/skills` symlinks into a
developer-host checkout. No Actions runner has that path and it is not vendored
here, so a gate that shelled out to the shared checker would pass locally and
fail in CI for an environment reason. Gates that fail for environment reasons
get switched off, and a switched-off gate still reads as coverage.

Checking a plan against the shared fan-out checker is a separate, host-bound
operation, and `config.json` records which contract each artifact targets so
that operation knows what to run.

## Binding state

`bound_here` in `config.json` is a claim about
`.agents/shared-skills.requirements.json` — whether this repository declares it
consumes that skill — and the gate refuses a claim that file does not support.
It is deliberately not a claim about the bound checkout's contents:
`repo-agent-native` is declared while its checkout tracks Forgejo `main`, which
does not yet carry the Blindspot contract from the GitHub side. Two facts, kept
apart.

`git-town-stacked-pr-worker` and `dual-forge-repository-loop` are not declared
yet. Declaring them is a separate change from this module.

## Evidence boundary

`PARALLEL TECH LEAD CONTRACT PASS` means the plan is internally consistent
against this repository's real paths and acceptance command. No Agent is
spawned, no branch or worktree is created, no shared checker is executed, and
nothing here measures whether parallel Workers were faster or cheaper than one.

Provenance: `ed3c/skills-shared#255` routed these paths here and named
`ed3c/bettor-arena#146` as owner. It recorded digests and no content, and the
bundle predates the shared contracts, so this layer is authored against the
landed schemas rather than restored.
