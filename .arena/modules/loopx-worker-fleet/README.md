# `loopx-worker-fleet` module

`loopx-worker-fleet` owns multi-Worker scheduling, worktree leases and orphan recovery under [`../../../loop_wiki/loopx-worker-fleet/`](../../../loop_wiki/loopx-worker-fleet/).

## Capabilities

```text
loopx.worker-fleet/v1
loopx.worktree-lease/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.ledger/v1
loopx.worker-gateway/v1
loopx.runtime-fabric/v1
arena.proof-kernel/v1
```

Stage 5 of the PDF terminal queue, answering issue #94. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-worker-fleet/scripts/fleet.py \
  <check|selftest|cycle|gc|verify-receipt>
```

## State Machine

```text
TASK_PACKET_ADMITTED
→ DEPENDENCIES_READY
→ BRANCH_WORKTREE_PATH_LEASED
→ RESOURCE_SLOT_RESERVED
→ WORKER_DISPATCHED
→ HEARTBEAT_CANCELLATION_MONITORED
→ ARTIFACTS_GATES_COLLECTED
→ HANDOFF_OR_TERMINAL_RECEIPT
→ CLEANUP
→ LEASE_RELEASED
→ GC_ORPHAN_RECOVERY
```

Leases are admitted before resource slots are reserved: a slot held for a task whose lease then collides makes the fleet read as full while idle.

## Boundaries

- Branch, worktree and path are one lease, because they fail together. Path overlap is compared by path component — `loop_wiki/ab` is a sibling of `loop_wiki/a`, not a child.
- No worktree may sit inside the owner's live checkout.
- Heartbeat staleness and lease expiry are separate findings: a silent Worker inside its window has crashed, an expired one may just be slow, and recovering them the same way kills slow work.
- tmux has no verdict vocabulary at all; a session is a terminal that is still open and survives the process failing. Herdr stays `NOT_EXERCISED` without an exact binary digest, config digest and canary receipt, and even when admitted its `gate_evidence` is `NONE`.
- Orphan recovery keeps leased, dirty and unreadable workspaces, removes nothing by default, refuses to let a human admit past a keep reason, and re-checks the disk immediately before acting.
- A receipt whose task ended while descendants are still running is refused.
- No fleet component writes canonical task state, a gate verdict, a merge, a promotion or a rollback.

## Evidence

```sh
sh loop_wiki/loopx-worker-fleet/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, nine positive properties, nineteen planted controls, and five physical controls on real processes and real directories — including a workspace made genuinely unreadable with `chmod`, and a process group killed with its descendants verified against the OS rather than against the parent's exit status.
