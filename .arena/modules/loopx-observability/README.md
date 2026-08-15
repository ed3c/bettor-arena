# `loopx-observability` module

`loopx-observability` owns the redacted evidence projection and the Human-in-the-loop console boundary under [`../../../loop_wiki/loopx-observability/`](../../../loop_wiki/loopx-observability/).

## Capabilities

```text
loopx.observability-projection/v1
loopx.hitl-console/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.ledger/v1
loopx.hitl/v1
arena.proof-kernel/v1
```

Terminal leaf of issue #61, on Contract v1 (#62), the ledger and reducer (#63) and Strategy + HITL (#65). Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-observability/scripts/observability.py \
  <check|selftest|project|rebuild|admit-request|validate-policy|validate-request>
```

## State Machine

```text
ledger events + versioned redaction policy
→ deterministic redaction with recorded removed paths
→ OpenTelemetry-shaped envelopes (derived trace/span ids)
→ stored projection
→ delete and rebuild → byte-identical envelopes
→ console prepares a signed request bound to revision, ledger head and shown projection
→ FORWARDED_TO_REDUCER
```

## Boundaries

- The projection has no authority. Every envelope and every projection states `PROJECTION_ONLY`, and every proposal names `LOOPX_LEDGER_REDUCER` as the writer.
- Rebuild equality is only defined within one policy version, and that is checked before equality is asked — otherwise a policy change reports as a trace-store disagreement.
- The redaction policy has a floor: a policy may drop more, never fewer, so a later version cannot quietly widen what escapes. Policy arrays must be sorted, or two equivalent policies would digest differently.
- A console request binds the state revision, ledger head and the digest of the projection displayed. A stale page is detected rather than honoured.
- Backends are adapters. No SDK is imported, no backend is named in the projection path, and `backend_admission_state` may not claim anything but `NOT_EXERCISED` — provider availability is not task evidence.
- No canonical state write, gate verdict, permission widening, secret rotation, merge, promotion or rollback occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-observability/tests/run-all.sh
```

Three schemas under a digest manifest, six manifest mutations, one positive pipeline run, nineteen controls, and a subprocess control that projects the same ledger in two separate processes and compares bytes — determinism asserted inside one interpreter would survive a dependency on hash seeding.
