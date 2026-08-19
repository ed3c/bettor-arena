# Inception A1 — durable compaction and recovery

Status: **FIRST PUBLIC IMPLEMENTATION CANDIDATE**  
Upstream profile issue: `ed3c/enterprise_agent_system#5`  
Owner issue: `ed3c/bettor-arena#191`

This leaf binds the Agent Thinking Inception source proposal to Bettor's existing
LoopX state, ledger, HITL, context-assembly and resource-GC mechanisms. The first
implementation candidate proves a narrow file-backed checkpoint contract and
recovery/activation semantics in public CI. It does **not** implement a second
LoopX ledger, summarize live model context, exercise a provider tokenizer, or
claim production durability, merge, release or rollback.

## Exact lineage

```text
repository        ed3c/bettor-arena
base commit       6bf8f7966c02b49294e22b329a6fce68fa50a815
base tree         05bc4982db6ea8a1609e4b5cc374a3db6a125da2
branch            agent/inception-a1-compaction-recovery
controller commit 6e0a916fd06dd8635d77c9a8c4d1b475185ea13e
controller tree   c3851a6953d456d0342a9776eed28561c1af0ca1
packet digest     sha256:e20049d29ce3ddca00a6aa74802e042a562ca3ee7336f86e91cc945102ee9540
packet bundle     sha256:dc4473b3195a738e55eb49c43661b6e1f4ea7f95c66749454776f2003b18ebc3
source digest     sha256:a6f1245ff865cae24838ed8ec4828330be684f3c03b29b9064ade8bfac94d8da
```

## Source-proposal boundary

The source proposes a token-watermark watchdog that summarizes older history,
writes a state snapshot to VFS and reconstructs the active context. These remain
requirements to test. Fixed `75%`/`80%` values, character-count token estimates,
summary losslessness and an in-memory dictionary receive no production evidence
credit.

## Existing canonical mechanisms reused

| Existing path | Reusable responsibility | Boundary |
|---|---|---|
| `loop_wiki/loopx-kernel/` | typed task/Gate/Quota authority | contracts do not execute transitions |
| `loop_wiki/loopx-ledger/` | append-only state, CAS, replay and torn-tail recovery | POSIX single-host ceiling |
| `loop_wiki/loopx-strategy-hitl/` | projection-only checkpoint and scoped Human resume | no Worker or ledger append authority |
| `loop_wiki/loopx-context-assembly/` | bounded Prompt IR and evidence-anchor preservation | live host state remains separate |
| `loop_wiki/loopx-resource-gc/` | retention, rebuild proof and residue inventory | destructive actions remain admitted separately |

No second generic ledger, reducer, queue, workflow engine or state writer may be
introduced in this leaf.

## Implementation subjects

```text
checkpoint_contract.py
  SafeToolTransaction
  CheckpointCandidate
  SqliteCheckpointFixture

test_checkpoint_contract.py
  file-backed close/reopen persistence
  ordered assistant/tool/result transaction control
  exact revision/CAS control
  recovery-PASS-before-activation control
  idempotency and checkpoint-id collision control
  invalid digest and in-memory durability refusals
```

The SQLite fixture uses WAL plus `synchronous=FULL` and retains prior checkpoint
rows. It is deterministic public evidence only; production storage remains under
the existing LoopX persistence owner.

## State Machine

```text
BUDGET_OBSERVED
→ SOFT_CHECKPOINT_REQUESTED
→ SAFE_TOOL_BOUNDARY_REACHED
→ SNAPSHOT_PREPARED
→ SNAPSHOT_VALIDATED
→ SNAPSHOT_COMMITTED
→ CONTEXT_RECONSTRUCTED
→ RECOVERY_PROBED
→ RESUMED | ROLLED_BACK | HUMAN_ESCALATED
```

The implemented candidate currently covers the middle persistence boundary:
`SAFE_TOOL_BOUNDARY_REACHED → SNAPSHOT_PREPARED → RECOVERY_PROBED → activation`.
A complete assistant/tool/result transaction is atomic. A prepared checkpoint
cannot become active until the recovery probe is `PASS`.

## Data flow

```text
exact task revision
+ complete ordered tool transaction
+ state/artifact/unresolved-work/lease/pending-effect digests
        ↓
validate CheckpointCandidate
        ↓
BEGIN IMMEDIATE + expected-revision CAS
        ↓
file-backed checkpoint row retained
        ↓
recovery probe
        ├─ PASS → exact single activation
        └─ FAIL / absent → no activation
        ↓
close / reopen readback proves persisted candidate and active revision
```

## Writer and resource lease

```text
loop_wiki/inception-compaction-recovery/**
.arena/modules/inception-compaction-recovery/**
data/inception-compaction-recovery/**
.github/workflows/inception-a1-compaction-recovery.yml
```

Read-only dependencies include all existing LoopX modules, root/shared indexes,
composition locks, release manifests, ordered terminal queues and source bytes.

Resource leases:

```text
local-storage-namespace:inception-compaction
sqlite-database:inception-compaction-fixture
filesystem-fixture:inception-compaction-crash-matrix
```

## Current deterministic evidence

The exact implementation workflow runs the contract tests, Python compilation,
changed-path lease checks and patch hygiene. Machine state is maintained in
[`preflight.json`](preflight.json).

## Next transition

`RUN_SQLITE_FAULT_MATRIX_AND_SHADOW_READBACK`

The next atom must add crash-before/crash-after fault injection around persistence
transitions and an independent readback receipt before any live context-compaction
or production durability claim is considered.

## Evidence ceiling

```text
file-backed contract candidate  DETERMINISTIC_PASS
SQLite close/reopen readback    DETERMINISTIC_PASS
full crash fault matrix         NOT_EXERCISED
live context reconstruction     NOT_EXERCISED
provider tokenizer budget       NOT_EXERCISED
production recovery             NOT_EXERCISED
Human admission                 NOT_PERFORMED
release / rollback              NOT_PERFORMED
```
