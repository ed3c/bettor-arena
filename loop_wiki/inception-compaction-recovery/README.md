# Inception A1 — durable compaction and recovery preflight

Status: **OWNER IMPLEMENTATION PREPARATION ONLY**  
Upstream profile issue: `ed3c/enterprise_agent_system#5`  
Owner issue: `ed3c/bettor-arena#191`

This leaf binds the Agent Thinking Inception source proposal to Bettor's existing
LoopX state, ledger, HITL, context-assembly and resource-GC mechanisms. It does
not yet implement or execute a new compactor, VFS, provider tokenizer, durable
checkpoint activation, production recovery, merge, release or rollback.

## Exact preparation subject

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
writes a state snapshot to VFS and reconstructs the active context. These are
requirements to test, not current repository facts. Fixed `75%`/`80%` values,
summary losslessness and an in-memory VFS receive no production evidence credit.

## Existing canonical mechanisms to adapt

| Existing path | Reusable responsibility | Boundary |
|---|---|---|
| `loop_wiki/loopx-kernel/` | typed task/Gate/Quota authority | contracts do not execute transitions |
| `loop_wiki/loopx-ledger/` | append-only state, CAS, replay and torn-tail recovery | POSIX single-host ceiling |
| `loop_wiki/loopx-strategy-hitl/` | projection-only checkpoint and scoped Human resume | no Worker or ledger append authority |
| `loop_wiki/loopx-context-assembly/` | bounded Prompt IR and evidence-anchor preservation | live host state remains separate |
| `loop_wiki/loopx-resource-gc/` | retention, rebuild proof and residue inventory | destructive actions remain admitted separately |

No second generic ledger, reducer, queue, workflow engine or state writer may be
introduced in this leaf.

## Target State Machine

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

A complete assistant/tool/result transaction is atomic. `SNAPSHOT_COMMITTED`
may not replace the previous active checkpoint until independent reconstruction
and recovery probes pass.

## Data flow

```text
provider/model/tokenizer budget receipt
+ exact task revision
+ complete transaction boundary
+ unresolved work / leases / pending effects / artifacts
        ↓
prepare content-addressed snapshot candidate
        ↓
validate manifest, digests and version transition
        ↓
atomically activate new checkpoint while retaining rollback subject
        ↓
reconstruct bounded context and run recovery probe
        ├─ PASS → resume
        └─ FAIL → rollback or Human escalation
```

## Provisional writer and resource lease

Writable only after exact-head revalidation:

```text
loop_wiki/inception-compaction-recovery/**
.arena/modules/inception-compaction-recovery/**
data/inception-compaction-recovery/**
.github/workflows/inception-a1-compaction-recovery.yml
```

Read-only dependencies include all existing LoopX modules, root/shared indexes,
composition locks, release manifests, ordered terminal queues and source bytes.

Resource lease candidates:

```text
local-storage-namespace:inception-compaction
sqlite-database:inception-compaction-fixture
filesystem-fixture:inception-compaction-crash-matrix
```

## First implementation commit admission

The next commit must first add a strict contract and a failing or hollow control
for one bounded transition. It must bind an actual SQLite, PostgreSQL or
filesystem fault-injection subject and prove that an in-memory dictionary cannot
satisfy durable recovery.

Required controls include transaction split/reorder, stale revision, concurrent
activators, crash before/after every persistence transition, corrupt artifact,
missing digest, recovery failure, premature deletion, secret leakage and dirty
residue.

## Evidence ceiling

```text
OWNER_PREPARATION_READY
implementation code       NOT_STARTED
local fault execution     NOT_EXERCISED
provider tokenizer budget NOT_EXERCISED
production recovery       NOT_EXERCISED
Human admission           NOT_PERFORMED
release / rollback        NOT_PERFORMED
```

The machine-readable authority for this preparation stage is
[`preflight.json`](preflight.json).
