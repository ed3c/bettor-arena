# Capability Workspace Control Plane v1

Status: **deterministic consumer contract and route-admission implementation** for `ed3c/bettor-arena#197`.

This module consumes an exact KAW `RouteProposalPacket` through a Bettor-owned admission envelope and returns only an acknowledgement compatible with KAW W4. It does not run a Worker, decide a Gate, mutate LoopX state, or claim domain/user outcomes.

## Data flow

```text
KAW RouteRequest
→ W4 exact subject/data/evidence admission
→ RouteProposalPacket
→ Bettor capability-workspace envelope
→ exact KAW commit/tree/blob binding
→ destination/capability/public-subject admission
→ semantic fingerprint + durable-host ledger port
→ ACKNOWLEDGED | DENIED
→ KAW RouteProposalReceipt echo
```

The initial implementation uses a JSON-file ledger for CLI and an injected mapping for tests. A deployment may replace storage, but it may not weaken semantic-conflict rejection.

## State machine

```text
RECEIVED
→ CONTRACT_VALIDATED
→ EXACT_BINDING_VALIDATED
→ PUBLIC_SUBJECTS_ADMITTED
→ REQUEST_ID_CLAIMED
   ├─ same fingerprint → IDEMPOTENT_REPLAY
   ├─ different fingerprint → DENIED
   └─ new fingerprint → ACKNOWLEDGED
```

Every acknowledgement has:

```text
execution.state = NOT_EXERCISED
workerReceiptReference = null
gateReceiptReference = null
loopxStateWritten = false
maximumClaim = ROUTE_PROPOSAL_ADMISSION_ONLY
```

## Exact binding

`contracts/upstream-binding.json` pins:

- KAW W4 commit/tree;
- `FederationRouter.kt` Git blob;
- W0 `WorkspaceContracts.kt` Git blob;
- `orchestrate.work` → `ORCHESTRATE_WORK` → `ORCHESTRATOR/bettor-arena`;
- Bettor baseline commit/tree;
- existing Worker Gateway manifest and Worker receipt schema Git blobs.

The dedicated checker reads the local Bettor blobs and, in hosted CI, reads back the exact public KAW commit/tree/blobs.

## Evidence ceiling

A PASS proves:

```text
exact cross-repository contract binding
strict public route admission
semantic fingerprint/idempotency behavior
bounded KAW acknowledgement projection
no execution/Gate/LoopX/domain authority widening
```

It does not prove:

```text
live Bettor deployment
real Worker/provider execution
Gate success
LoopX reducer commit
private-subject transport
user or paid outcome
merge or release
```

## Validation

```sh
python3 loop_wiki/capability-workspace-control-plane/scripts/check_capability_workspace.py --remote
python3 -m unittest discover \
  -s loop_wiki/capability-workspace-control-plane/tests \
  -p 'test_*.py' -v
```

A future KAW adapter may call this consumer through an admitted carrier. The carrier itself remains a separate atom and cannot promote this deterministic contract receipt into `LIVE_BETTOR_HANDOFF`.
