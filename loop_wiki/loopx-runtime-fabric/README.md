# `loopx-runtime-fabric`

Provider-neutral execution fabric: leased disposable workspaces, an enforcement
ceiling that is declared rather than implied, and a parity harness that says
`NOT_EXERCISED` out loud.

Machine authority: [`../../.arena/modules/loopx-runtime-fabric/module.json`](../../.arena/modules/loopx-runtime-fabric/module.json)
Interface version: `1.0.0`

## Runtime state machine

```text
RUNTIME_REQUESTED
→ PROVIDER_CAPABILITY_PROBED
→ POLICY_COMPATIBILITY_CHECKED
→ LEASE_GRANTED
→ IMMUTABLE_SUBJECT_MATERIALIZED
→ DEPENDENCIES_PREPARED
→ WORKER_EXECUTED
→ ARTIFACTS_COLLECTED
→ GATES_EXECUTED
→ CLEANUP_VERIFIED
→ RECEIPT_EMITTED
→ LEASE_RELEASED
```

## Public control port

```sh
python3 loop_wiki/loopx-runtime-fabric/scripts/fabric.py \
  <check|selftest|validate-request|validate-lease|admit-lease|run|gc|parity>
```

Exits are `0` ok, `2` refused, `64` unusable input — and `70` provider
unavailable. That fourth code is the one this module needs and the others did
not: a sandbox that will not start has told you nothing about the task, and
folding it into `2` records a verdict about code that never ran.

## The enforcement ceiling is stated, not implied

The local adapter's ceiling, copied onto every receipt it emits:

```text
filesystem    DECLARED_NOT_KERNEL_ENFORCED
network       UNENFORCED
process_group ENFORCED
timeout       ENFORCED
output_bytes  ENFORCED
memory_bytes  NOT_OBSERVED
disk_bytes    NOT_OBSERVED
```

A local subprocess shares the host filesystem and network. The workspace is a
fresh temporary directory that is deleted afterwards — disposable, not isolated.

So a request may not *claim* `network: deny` against this adapter. The validator
refuses the claim at admission:

> `request.network.requested='deny'` but the adapter attests `'UNENFORCED'`; a restriction nothing enforces is a fabricated safety property, and someone will rely on it

That last clause is the reason. An unenforced restriction is worse than no
restriction, because the next person builds on it.

The contract checker also compares the manifest's declared ceiling against the
adapter's own constant. A documented ceiling that has drifted from the
implementation is read as a guarantee.

## Physical controls

`#66` asks for *at least one isolation control that physically turns red*. A
fixture asserting that a rule exists cannot answer that, so
`scripts/control_fabric.py` builds real source trees and runs real subprocesses:

| control | what actually happens |
|---|---|
| **escape** | a process writes `src/sneaked.txt`, outside every declared writable path, then **exits 0**. The residue scan finds it and the receipt classifies `POLICY_REFUSAL` — residue outranks a zero exit code, because the exit code cannot see the violation |
| **timeout** | a sleeping process is killed with its process group and the workspace is still removed; classified `TASK_FAILURE`, not a policy violation |
| **clean** | a well-behaved run leaves no residue and removes its workspace |

The clean run is not decoration. Without it, a residue scanner that returned a
constant non-empty list would pass the escape control and prove nothing.

## Parity says NOT_EXERCISED out loud

Eight dimensions are compared field by field — a single overall verdict would let
one matching exit code hide four disagreements. Timing and resource observations
are deliberately excluded: they are environment-specific, and a matrix requiring
them to match would be permanently red or quietly rounded until meaningless.

An adapter with no receipt is `NOT_EXERCISED`, never `PASS` and never blank.
A matrix that renders absent adapters as blank invites the reading that they
agreed, and the validator refuses a row that reports dimension verdicts without
a receipt behind it.

`e2b-sandbox` and `firecracker-vm` are declared and `NOT_EXERCISED`. No provider
brand is an architecture invariant here; each is an adapter that would need exact
license/spec verification and a physical canary before admission.

## Evidence

```sh
sh loop_wiki/loopx-runtime-fabric/tests/run-all.sh
```

Three schemas under a digest manifest, seven manifest mutations, one positive
run, eighteen contract controls, and three physical controls that execute.

Each contract control was checked to fail for its own reason:

```sh
python3 loop_wiki/loopx-runtime-fabric/scripts/probe_controls.py
```

## Molecular boundary

Terminal leaf of #61, on Contract v1 (#62), the ledger and reducer (#63) and the
Worker Gateway (#64).

The local adapter is `EXERCISED_FIXTURE_ONLY`. No cloud sandbox has been
started, no provider credential exists in this repository, and no live canary
has run. Merge and provider activation remain Human Admit.
