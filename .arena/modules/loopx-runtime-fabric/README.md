# `loopx-runtime-fabric` module

`loopx-runtime-fabric` owns leased disposable workspaces, provider-neutral execution requests and observation receipts under [`../../../loop_wiki/loopx-runtime-fabric/`](../../../loop_wiki/loopx-runtime-fabric/).

## Capabilities

```text
loopx.runtime-fabric/v1
loopx.workspace-lease/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.ledger/v1
loopx.worker-gateway/v1
arena.proof-kernel/v1
```

Terminal leaf of issue #61. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-runtime-fabric/scripts/fabric.py \
  <check|selftest|validate-request|validate-lease|admit-lease|run|gc|parity>
```

Exits `0` ok, `2` refused, `64` unusable input, `70` provider unavailable.

## Boundaries

- A runtime observes; it never decides a gate. Receipts carry `OBSERVATION_ONLY` and name the reducer as writer, and the receipt outcome vocabulary has no gate verdict in it.
- A request may only claim an enforcement level its adapter attests. `network: deny` against the local adapter is refused at admission — an unenforced restriction is worse than none, because the next person builds on it.
- The manifest's declared ceiling is compared against the adapter's own constant. A documented ceiling that has drifted is read as a guarantee.
- A lease has one owner, a real expiry and the state revision it was granted at. Two Workers on one lease, an expired lease, and a lease from a revision the task has left are all refused.
- An adapter with no receipt is `NOT_EXERCISED` in the parity matrix — never blank, never `PASS`. A row reporting dimension verdicts without a receipt is refused.
- No provider brand is an architecture invariant. `e2b-sandbox` and `firecracker-vm` are declared adapters at `NOT_EXERCISED`; admission needs exact license/spec verification and a physical canary.
- No provider activation, credential, live canary, composition selection, promotion or rollback occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-runtime-fabric/tests/run-all.sh
```

Three schemas under a digest manifest, seven manifest mutations, one positive run, eighteen contract controls, and **three physical controls** that build real workspaces and run real processes — including one where a process exits 0 while writing outside its declared paths and the receipt still classifies `POLICY_REFUSAL`.
