# LoopX Worker Fleet v1

A provider-neutral multi-Worker fleet controller for AFK execution. Preserves
one Worker / one branch / one worktree / one path lease, keeps canonical task
state in LoopX, and treats tmux and Herdr as adapters that observe rather than
decide. Stage 5 of the terminal queue, on the Worker Gateway (#64), the Ledger
(#63) and the Runtime Fabric (#66). Answers #94.

## Public port

```sh
python3 loop_wiki/loopx-worker-fleet/scripts/fleet.py \
  <check|selftest|cycle|gc|verify-receipt>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` the input is unusable.

There is no subcommand that writes canonical task state, merges, ships, promotes
or rolls back — a fleet controller with a button for those is one that will
eventually press it.

## Three ideas

### Path overlap is a component comparison, not a string prefix

```text
"loop_wiki/a"    vs "loop_wiki/a"     nested   -> collision
"loop_wiki/ab"   vs "loop_wiki/a"     siblings -> no collision
"loop_wiki/a/b"  vs "loop_wiki/a"     nested   -> collision
```

`startswith` says `loop_wiki/ab` is inside `loop_wiki/a`. It is not. A fleet that
gets this wrong refuses lease pairs that were never in conflict, and the fix
someone reaches for is to loosen the check.

Branch, worktree and path are leased **together**, because they fail together:
two Workers on one branch produce commits nobody ordered, two on one worktree
produce a tree neither wrote alone. Split into separate ledgers, a Worker could
hold three of the four and look admitted.

### An adapter has no vocabulary for a verdict

`TMUX_STATES` is `SESSION_PRESENT / SESSION_ABSENT / SESSION_UNKNOWN`. There is
no value it can carry that a reader could mistake for a task verdict — because a
session is a terminal that is still open. It survives the process that was
running in it, and it survives that process failing.

`herdr_admission` reports `NOT_EXERCISED` unless given an exact binary digest,
config digest and canary receipt. Even when admitted, `gate_evidence` stays
`NONE`: the exit code describes the adapter's own run, not the workload's gates.

### Orphan recovery deletes nothing by default

```text
KEEP_ACTIVE_LEASE   someone is using it
KEEP_DIRTY          the work exists nowhere else
KEEP_UNREADABLE     absence of evidence
```

`KEEP_UNREADABLE` is the one that gets left out. A scan error on one directory is
easy to skip past, and skipping past it classifies that directory as having no
reason to keep it — so a GC that treats "cannot tell" as "safe to delete" deletes
exactly what it cannot see.

A default plan marks nothing removable. A human admits a specific workspace by
path, and admitting one that is leased, dirty or unreadable is **refused** rather
than honoured: releasing the lease or committing the work comes first, or the
check is decorative. `execute` re-checks each workspace immediately before
acting, because an inventory taken five minutes ago describes a tree that may
have gained a Worker since.

## Also enforced

- a `heartbeat_interval_s` not shorter than the lease — a Worker that cannot miss
  a beat before expiry is detected by nothing;
- stale heartbeat and expiry are **separate** findings: a silent Worker inside
  its window has crashed, an expired one may just be slow, and recovering them
  the same way kills slow work;
- two missed intervals before declaring staleness, because one missed beat is as
  likely to be a slow tick and killing on it makes the fleet flap;
- a worktree inside the owner's live checkout;
- dependency cycles, reported *as the cycle* rather than as its existence;
- a task requesting more than the fleet has — it would wait forever looking
  merely unlucky;
- backpressure that defers **with a reason** rather than dropping;
- a receipt whose task ended while descendants are still running.

## Evidence

```sh
sh loop_wiki/loopx-worker-fleet/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, nine positive
properties, nineteen planted controls, and a **physical** control group.

The physical group answers the two failures a fixture cannot:

1. a clean leaseless workspace is proposed, never auto-removed;
2. a dirty workspace is kept — and is still on disk after `apply`;
3. a leased workspace is kept — and is still on disk after `apply`;
4. an **unreadable** workspace is kept, made genuinely unreadable with `chmod`
   so the branch is reached by the filesystem rather than by a flag;
5. a killed process group takes its descendants with it, verified by asking the
   OS about the child pid — not by trusting the parent's exit status, which is
   exactly what a fleet would otherwise record.

**Verified by deliberately breaking it.** Making `_dirty` return `False` instead
of `None` on an unreadable directory:

```
fleet control RED: an unreadable workspace classified PROPOSED_REQUIRES_HUMAN,
not KEEP_UNREADABLE; a GC that treats 'cannot tell' as 'safe to delete' deletes
exactly what it cannot see
exit=2
```

If the suite runs as root the `chmod` cannot make anything unreadable, and
control 4 exits `64` saying so rather than passing on a check it could not
perform.

## Boundaries

- Every receipt carries `gate_authority: GATES_ONLY_NOT_THIS_FLEET`,
  `canonical_writer: LOOPX_LEDGER_REDUCER` and `authority: OBSERVATION_ONLY`.
- Adapter observations are kept on the receipt and validated through a module
  with no verdict vocabulary; `task_evidence` and `gate_evidence` are `NONE`.
- A `COMPLETED` receipt with no gate results and a live tmux session is refused.
- Scheduling is deterministic — ordering is `(priority desc, order, task_id)` and
  nothing else, so the same queue yields the same plan and a collision control
  can tell "wrong" from "different".
- No canonical state write, gate verdict, merge, promotion, permission widening,
  secret access or rollback occurs in this leaf.
