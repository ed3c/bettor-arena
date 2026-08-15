# `services/hitl-api`

The request path for the Harness Console. Answers #99 together with
[`../../apps/harness-console/`](../../apps/harness-console/) and
[`../../packages/harness-console-contracts/`](../../packages/harness-console-contracts/).

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
