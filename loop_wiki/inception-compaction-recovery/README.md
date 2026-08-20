# Inception A1 — durable compaction and recovery

Status: **PUBLIC CRASH-MATRIX VERIFICATION CANDIDATE**  
Upstream profile issue: `ed3c/enterprise_agent_system#5`  
Owner issue: `ed3c/bettor-arena#191`

This leaf binds the Agent Thinking Inception source proposal to Bettor's existing
LoopX state, ledger, HITL, context-assembly and resource-GC mechanisms. It now
proves a narrow file-backed checkpoint contract plus abrupt-process crash behavior
at prepare, recovery-probe and activation commit boundaries in public CI. It does
**not** implement a second LoopX ledger, summarize live model context, exercise a
provider tokenizer, or claim production/multi-host durability, merge, release or
rollback.

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
  named fault-hook durability boundaries

test_checkpoint_contract.py
  file-backed close/reopen persistence
  ordered assistant/tool/result transaction control
  exact revision/CAS control
  recovery-PASS-before-activation control
  idempotency and checkpoint-id collision control
  invalid digest and in-memory durability refusals

test_crash_matrix.py
  child-process os._exit fault injection
  prepare_before_commit / prepare_after_commit
  recovery_before_commit / recovery_after_commit
  activate_before_commit / activate_after_commit
  fresh-process readback and WAL/SHM residue checks
```

The SQLite fixture uses WAL plus `synchronous=FULL` and retains prior checkpoint
rows. Fault hooks exist only as a deterministic public-test seam. Production
storage remains under the existing LoopX persistence owner.

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

The implemented public candidate covers the middle persistence boundary:
`SAFE_TOOL_BOUNDARY_REACHED → SNAPSHOT_PREPARED → RECOVERY_PROBED → activation`.
A complete assistant/tool/result transaction is atomic. A prepared checkpoint
cannot become active until the recovery probe is `PASS`.

## Crash matrix

```text
PREPARE transaction
  crash before commit → row absent after fresh-process reopen
  crash after commit  → row present, active revision unchanged

RECOVERY probe
  crash before commit → recovery_state remains NOT_EXERCISED
  crash after commit  → recovery_state = PASS, still not active

ACTIVATION
  crash before commit → active revision unchanged
  crash after commit  → exact new revision/checkpoint visible after reopen
```

Each child exits abruptly with a dedicated non-zero code rather than raising a
normal Python exception. A separate parent process reopens the SQLite file and
checks durable visibility. Terminal readback also checks that `-wal` and `-shm`
residue is absent after all connections close.

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
prepare commit boundary ← crash matrix → fresh-process readback
        ↓
recovery probe boundary ← crash matrix → fresh-process readback
        ↓
activation boundary     ← crash matrix → fresh-process readback
        ↓
context reconstruction remains a separate next-stage canary
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

## Current deterministic evidence ceiling

```text
file-backed checkpoint contract  DETERMINISTIC_PASS candidate
SQLite close/reopen readback      DETERMINISTIC_PASS candidate
six abrupt crash boundaries       PUBLIC_VERIFICATION_CANDIDATE
WAL/SHM terminal residue check    PUBLIC_VERIFICATION_CANDIDATE
live context reconstruction       NOT_EXERCISED
provider tokenizer/context limit  NOT_EXERCISED
multi-host/production recovery    NOT_EXERCISED
Human admission                   NOT_PERFORMED
merge / release / rollback        NOT_PERFORMED
```

Machine state is maintained in [`preflight.json`](preflight.json).

## Next transition

`RUN_PUBLIC_CONTEXT_RECONSTRUCTION_FIXTURE_AND_SHADOW_READBACK`

A green crash matrix does not prove summary fidelity or live context recovery. The
next atom must reconstruct one bounded public fixture from a committed checkpoint,
preserve evidence anchors/unresolved work, and read it back independently before
any live model/provider claim is considered.
