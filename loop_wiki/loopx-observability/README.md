# `loopx-observability`

Redacted, rebuildable projection of LoopX execution evidence, and a console
surface that can prepare Human decisions without being able to make them.

Machine authority: [`../../.arena/modules/loopx-observability/module.json`](../../.arena/modules/loopx-observability/module.json)
Interface version: `1.0.0`

## Projection law

```text
LoopX ledger + artifact references
→ deterministic redaction under a versioned policy
→ OpenTelemetry-shaped envelopes
→ trace store / event stream / Web projection
→ Human action proposal
→ signed decision request
→ LoopX validation and ledger commit
```

Delete the projection entirely, rebuild it from the ledger under the same policy
version, and the envelope bytes are identical. That property is what makes a
trace store safe to lose — and what makes a trace store that disagrees with the
ledger a detectable fault rather than a second opinion.

## Public control port

```sh
python3 loop_wiki/loopx-observability/scripts/observability.py \
  <check|selftest|project|rebuild|admit-request|validate-policy|validate-request>
```

Exits are `0` admitted, `2` refused, `64` unusable input. The split between 2
and 64 is load-bearing: a missing ledger file and a ledger that violates the
projection law are different answers, and a caller that cannot tell them apart
will read a broken pipe as a verdict.

The module is `control-only` and is not exposed through MCP.

## Redaction is deterministic and self-reporting

Two properties, both checkable:

- **deterministic** — the same events under the same policy produce byte-identical envelopes. Correlation ids are *derived* from subject and event rather than generated, because a random id would make two rebuilds of one ledger differ and destroy the only thing this module promises.
- **self-reporting** — every envelope records the policy version and the exact field paths removed.

A projection that silently omits is worse than one that visibly redacts: the
reader of a redacted field knows to go ask; the reader of a missing one does not
know there was anything to ask about.

The policy has a floor. A policy may drop *more* than `redaction_floor_keys`;
one that drops fewer is refused, so a later policy version cannot quietly widen
what escapes. Policy arrays must be sorted — two equivalent policies that digest
differently would break rebuild equality.

## The console has no authority

A console may show state, inspect bounded evidence, and prepare a
`RETRY_AFTER_FIX` / `UPDATE_CONTRACT` / `CANCEL` / `SCOPED_EXCEPTION` request.
Every request binds three things the operator was actually looking at: the state
revision, the ledger head, and the digest of the projection displayed. That
binding is what makes a stale page **detectable** rather than merely unlucky —
an operator acting on a five-minute-old view is not proposing what they think
they are proposing, and the request says so.

Fields that would turn a request into a command (`force`, `mark_pass`,
`gate_verdict`, `promote`, `rollback`, `state_write`, …) are rejected by name at
any depth, as are keys carrying secret material or private reasoning.

`commit` is deliberately **not** on that list. It reads as a verb, but in this
repository it is overwhelmingly a noun — `subject.commit` is a git sha on every
packet in the system, and banning the word rejected the module's own positive
fixture. A name-based ban has to be read as names, not as vocabulary.

## Backends are adapters, not participants

Langfuse, an OTLP collector and local JSONL are listed as adapters over the
envelope shape. No SDK is imported and no backend is named in the projection
path. `backend_admission_state` is `NOT_EXERCISED` and the contract checker
refuses any other value — the line that keeps *"Langfuse is reachable"* from
being read as *"the task passed"*.

Backend absence cannot stop LoopX correctness, and the suite demonstrates rather
than asserts it: nothing in the projection path touches a backend at all.

## Evidence

```sh
sh loop_wiki/loopx-observability/tests/run-all.sh
```

Three schemas under a digest manifest, six manifest mutations, one positive
pipeline run, nineteen controls, and a subprocess control that projects the same
ledger twice **in two separate processes** and compares the bytes — determinism
asserted inside one interpreter would survive a dependency on hash seeding.

Each control was checked to fail for its own reason:

```sh
python3 loop_wiki/loopx-observability/scripts/probe_controls.py
```

That check earned its place here. The policy-version control was originally
reported as *"the trace store disagrees with the ledger"* — true, but the wrong
diagnosis for someone who had simply changed policy, and it meant the version
check itself was never reached. The order now establishes policy version before
equality is asked, because rebuild equality is only defined within one version.

## Molecular boundary

Terminal leaf of issue #61, on Contract v1 (#62), the ledger and reducer (#63)
and Strategy + HITL (#65).

Contract validation and deterministic fixture projection are `IMPLEMENTED`. A
live trace store, a real console, signed operator authentication and production
UI activation remain `NOT_IMPLEMENTED` or `NOT_EXERCISED` until separate exact
receipts exist. Merge remains a Human decision.
