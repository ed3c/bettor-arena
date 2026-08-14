# `harness-console` module

`harness-console` owns [`../../../loop_wiki/harness-console/app/`](../../../loop_wiki/harness-console/app/), [`../../../loop_wiki/harness-console/service/`](../../../loop_wiki/harness-console/service/) and [`../../../loop_wiki/harness-console/contracts/`](../../../loop_wiki/harness-console/contracts/).

## Capabilities

```text
loopx.harness-console/v1
loopx.hitl-request/v1
```

Required capabilities:

```text
loopx.contracts/v1
arena.proof-kernel/v1
```

Stage 18 of the PDF terminal queue, answering issue #99. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

`render_state: NOT_IMPLEMENTED` and `live_console_state: NOT_EXERCISED`: there is no HTML, no websocket and no browser here, and production console activation is Human Admit. Neither may be promoted to PASS.

## Public control port

```sh
python3 loop_wiki/harness-console/service/hitlapi.py \
  <check|selftest|project|views|draft|sign|submit>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` unusable input — an absent
projection, an absent events file and an unset signer key are all `64`, because an
unconfigured operator and a decision that disagreed are different answers and both
are non-zero.

There is no subcommand that mutates task state, writes a ledger event, marks a gate
PASS, merges, promotes or rolls back. Asking for one is unusable input.

## The signer key

Read from `HITL_SIGNER_KEY`, never a flag — a flag lands in a shell history, a process
list and a CI log, and all three outlive the request. The key is Human-held, is never
stored in this repository, and never enters a request or a receipt. Only the key **id**
travels.

Signing is `HMAC-SHA256` and is named as such: it authenticates that the holder of the
signer key produced the request, and nothing more.

## Boundaries

- **The projection is a pure function of the events.** Delete it and it comes back
  byte for byte. A UI database that has drifted from the ledger renders confidently
  and wrongly, and the screen looks the same either way.
- **A gap is `INCOMPLETE` and names the missing sequences.** A graph drawn from events
  1, 2, 4 and one drawn from 1, 2, 3, 4 are the same picture; the difference is
  whatever happened in 3.
- **A request binds both the ledger head and the state revision.** The head can move
  without the revision and the revision cannot move without the head, so both are
  checked. A stale request looks exactly like a fresh one.
- **A duplicate is one decision, not two.** The request id is keyed on content; a
  nonce would have made two identical decisions into two requests, and one Human
  clicking twice is not two decisions.
- **Acceptance mutates nothing.** `mutated: false`, `gate_verdict_written: false`,
  `requires_gate_revalidation: true`. LoopX has taken delivery of a question.
- **A scoped exception carries a subject, a gate and an expiry.** Without all three it
  is an unscoped force-skip with a better name, and one that never expires is permanent
  with nothing about it saying so.

## Evidence

```sh
sh tests/harness-console/run-all.sh
```

## A deliberate departure from #99's path lease

#99 leases `apps/harness-console/**`, `services/hitl-api/**` and
`packages/harness-console-contracts/**`. Those are three new root-level slots, and
`ARCHITECTURE.md` §2 is the placement authority for this repository: a new slot has to
be declared there first. Editing that file trips the lineage gate, which requires the
proof workflow to be re-stamped -- and the openwiki lane's re-stamp needs a real model
run, which is a Human-owned operation.

The queue records the PDF as `SOURCE_PROPOSAL_ONLY`. So the trees live under the
existing `loop_wiki/` slot with the same three-way split preserved:

```text
apps/harness-console            ->  loop_wiki/harness-console/app
services/hitl-api               ->  loop_wiki/harness-console/service
packages/harness-console-contracts -> loop_wiki/harness-console/contracts
tests/harness-console           ->  unchanged (tests/ already has a slot)
```

Nothing about the split is lost; only the root changed. Declaring the three slots is a
separate change with a Human-admitted re-stamp attached to it.
