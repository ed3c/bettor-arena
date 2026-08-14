# Git Town runtime admission v1

Answers issue #101. Follows governance #80 / PR #81. This is the **runtime admission
leaf** for the canonical shared `git-town-stacked-pr-worker` method; it does not copy
the shared Skill.

## Current state on this machine

```text
executable_state   EXECUTABLE_ABSENT
live_sync_state    NOT_EXERCISED
```

`git-town` is not installed here. That is a **state**, not a failure and not a pass:
nothing ran, so nothing about Git Town's behaviour follows. The port exits `70` for
it — the provider is unavailable — because "the provider is not here" and "the
admission disagreed" are different answers that both read as non-zero.

**So nothing in this module claims anything about Git Town.** What it does claim is
checkable without it: the guard rails around whatever runs, and the admission gate in
front of it.

## The non-negotiable command shape

```text
git town sync --stack --non-interactive --no-auto-resolve --no-push
```

Dry run precedes live, and the dry-run argv is that shape plus `--dry-run` — checked
as a property, not written twice.

The caller selects an admitted **mode** by name; it never supplies argv. That is the
whole difference between admitting a tool and admitting a shell: a caller that can
pass argv can pass `--continue`, and `--continue` resolves a semantic conflict on the
agent's own judgement.

```text
version              git town --version
config               git town config
sync_dry_run         the shape above, plus --dry-run
sync_local_no_push   the shape above
```

Forbidden in every mode, enumerated rather than described:

```text
--continue  --skip  --undo  --abort  --force  --force-with-lease
--push      --auto-resolve  --ship  --merge  --no-verify
```

Each is a decision a human owns, and each has a plausible reason to be added at 2am.

## The admission ladder

```text
EXECUTABLE_ABSENT               unlocks nothing; a human review cannot promote it
EXECUTABLE_PRESENT_NOT_ADMITTED presence is not admission
ADMITTED_DRY_RUN_ONLY           pinned and profiled, no human has reviewed the live lane
ADMITTED_LOCAL_NO_PUSH          reviewed; still no mode that reaches the network
```

An admission names a specific binary — version, checksum of the bytes, provenance URL,
licence, SBOM reference — **or it is refused**. Anything less names a *tool*, and a
tool is not a thing that ran. A version of `latest` is refused by name: the bytes
behind it can be replaced without the string moving.

The repository profile is a **closed set** rather than a validated shape. A validated
shape admits `rebase-and-force-push` on the grounds that it is a string. It is also
path-neutral: a config naming someone's home directory works exactly once, and the
second machine's failure looks like a Git Town problem.

## The invariants, and why each one exists

Taken before and after, around whatever ran:

| rule | why |
|---|---|
| `REMOTE_REF_MOVED` | `--no-push` is a flag on a program; this is a fact about the remote. Read from the remote repository, **not** the local remote-tracking cache — the cache does not move when somebody else pushes, and does move when nobody pushed at all. |
| `PROTECTED_REF_MOVED` | main and perennial branches point where they pointed. |
| `TREE_LEFT_DIRTY` | clean before, clean after. |
| `RESIDUE_LEFT` | `.orig` / `.rej` / `.BACKUP.*` on disk. `git status` can report a clean tree with these present — a half-finished merge that looks finished. |
| `OPERATION_IN_FLIGHT` | `rebase-merge`, `MERGE_HEAD` and friends. Present afterwards means the operation stopped in the middle, which is exactly the state a `--continue` would be offered for. |
| `SILENT_CONFLICT_MARKERS` | markers in a committed file with a clean status. The dangerous case is the one where the operation *finished* and the markers look like code. |
| `OUT_OF_LEASE_DIFF` | nothing outside the lease changed. |

The rollback subject is pinned by **reachability**, not by branch equality. A branch
moving forward is what a sync does and the rollback is still available; drift is the
recorded commit becoming unreachable — what a reset or a force-push does, and after
which the rollback restores something nobody chose.

## Authority

```text
Git Town      local branch hierarchy, bounded local synchronization
GitHub gate   exact-head publication decision
LoopX         canonical task state
Human         semantic conflicts, remote publication, merge or ship,
              release promotion, production rollback, config activation
```

A table rather than a paragraph: the interesting question is always "who decided
this", and a paragraph answers it differently depending on who is reading.

## Publication

One operation, and a human performs it. `publication_decision` returns whether a
request **may be made**, never whether one was made — `performed` is always false
coming out of it, because there is no code there that publishes.

The local receipt head and the GitHub check head must be the **same commit**. Two
different heads are two facts about a different commit each, and the sentence that
combines them ("local is green and CI is green") is true of neither.

Four receipt kinds stay separate: `LOCAL_SYNC`, `LOCAL_VERIFICATION`, `PUBLICATION`,
`HUMAN_ADMIT`. Folded into one, "the sync ran" and "a human admitted it" become the
same record, and only one of them is a decision.

**Tool exit zero is not repository PASS.** A tool exiting zero says the tool finished;
whether the repository is in an acceptable state is a different question.

## Evidence

```sh
sh tests/git-town/run-all.sh
```

Thirteen physical controls on **real repositories with a real bare remote** — a real
push, a push from a second clone that moves the remote while this repository's cache
stays put, a real protected-ref move, a real out-of-lease edit, conflict markers
committed with a clean `git status`, a real `.orig` on disk, a genuinely conflicting
rebase stopped mid-flight, and a reset that puts the rollback target out of reach.
Every dirty case is followed by the clean one again, so a red is attributable to what
was planted rather than to the checker having broken.

There is no `.git-town.toml` in this repository. Config activation is Human Admit, and
writing the file is the activation.
