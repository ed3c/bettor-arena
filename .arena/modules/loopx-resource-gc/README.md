# `loopx-resource-gc` module

`loopx-resource-gc` owns retention and garbage collection under [`../../../loop_wiki/loopx-resource-gc/`](../../../loop_wiki/loopx-resource-gc/).

## Capabilities

```text
loopx.resource-gc/v1
loopx.retention-policy/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.ledger/v1
loopx.runtime-fabric/v1
loopx.worker-fleet/v1
arena.proof-kernel/v1
```

Stage 6 of the PDF terminal queue, answering issue #97. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-resource-gc/scripts/resourcegc.py \
  <check|selftest|plan|run|verify-receipt>
```

Exit `0` ok, `2` refused, `64` unusable input, `70` resource exhausted. The fourth code exists because a full disk is not a task that failed and not a gate that disagreed.

## State Machine

```text
RESOURCE_INVENTORY_CAPTURED
→ OWNERSHIP_LEASE_RETENTION_CLASSIFIED
→ LIVE_PROTECTED_BLOCKED_EXPIRED_DERIVED
→ REBUILD_PROBE
→ DRY_RUN_GC_PLAN
→ SAFETY_SUBJECT_REACHABILITY_GATES
→ HUMAN_ADMIT_FOR_DESTRUCTIVE_CLASSES
→ CLEANUP_EXECUTED
→ RESIDUE_VERIFIED
→ TOMBSTONE_RECEIPT_APPENDED
```

The rebuild probe runs **before** the plan. Proving a projection rebuildable after removing it is a recovery attempt, not a probe — by then there is no original to compare against.

## Boundaries

- A mutable projection is deletable only when a rebuild beside the original produced byte-identical output. `DIVERGENT` — the rebuild works and does not reproduce this content — keeps the resource.
- Immutable evidence (ledger segments, Human decisions, release receipts, WAL) and blocked conflict evidence cannot be admitted for deletion at all.
- Leased and dirty resources are live. A resource with no last-used time is protected, not expired: an unknown age is not an old age.
- Selection is subtractive — everything starts protected and earns its way out, so a resource nobody wrote a rule for is kept rather than selected.
- `authorized_by` must be `HUMAN`. An agent or provider cannot admit a destructive class.
- Residue is verified across path, process, port and mount, because they fail independently.
- Every removal leaves a tombstone; a removal without one erases the record that the resource existed.
- No canonical state write, gate verdict, merge, promotion or production policy change occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-resource-gc/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, eleven positive properties, thirteen planted controls, and four physical controls that build real trees and run real rebuilds — including a demonstration that deleting a `DIVERGENT` projection loses the original content, measured rather than argued.
