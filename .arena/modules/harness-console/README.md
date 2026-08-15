# `harness-console` module

`harness-console` owns [`../../../apps/harness-console/`](../../../apps/harness-console/), [`../../../services/hitl-api/`](../../../services/hitl-api/) and [`../../../packages/harness-console-contracts/`](../../../packages/harness-console-contracts/).

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
python3 services/hitl-api/hitlapi.py \
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

## Path lease

The three trees live where #99 leased them:

```text
apps/harness-console                  the view model layer
services/hitl-api                     the request path
packages/harness-console-contracts    the shared vocabulary and schemas
tests/harness-console                 the suite
```

`apps/`, `services/` and `packages/` are declared in [`ARCHITECTURE.md`](../../../ARCHITECTURE.md) §2,
which is this repository's placement authority. They landed under `loop_wiki/` first, because
declaring a root slot requires editing that file and editing it trips the lineage gate — the
proof workflow has to be re-stamped and re-locked across all twelve loops before the bytes may
change. That was done rather than worked around.
