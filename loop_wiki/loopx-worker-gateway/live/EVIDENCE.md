# Issue-91 live lane evidence

Extends the frozen leaf's `../EVIDENCE.md` ladder. That leaf stops at
`FIXTURE_ONLY`; this lane can reach `CARRIER_EXERCISED` on its own and
`GATEWAY_LIVE` only from a receipt produced by a real host launch.

```text
CONTRACT_ONLY      descriptor and schema bytes validate
FIXTURE_ONLY       the frozen synthetic Worker proves the gateway controls
CARRIER_EXERCISED  this lane's own carrier + verification ran end to end against
                   the exact subject, with the stub in place of the host
GATEWAY_LIVE       the host binary was launched by this carrier inside a detached
                   worktree of the exact subject and produced a receipt with
                   executed=true, a real exit code and cleanup PASS
```

`CARRIER_EXERCISED` never implies `GATEWAY_LIVE`: the stub lane deliberately
carries `host_id=fixture-host`, which the published request and adapter
contracts reject, so no dry-run byte can be replayed as a host result.

`GATEWAY_LIVE` is still not a live-matrix PASS. It is one observation of one
process. Promoting Claude Code in `../LIVE_MATRIX.md` needs independent Gates
and Human admission, neither of which this lane may write.

## Lane state

Fill each row from a receipt path. A row with no receipt path stays `PENDING`;
documentation, an installed binary, a green selftest or another host's result
never fills one.

| Claim | State | Receipt / observation |
|---|---|---|
| lane contracts validate against the frozen schemas | `PENDING` | |
| planted controls each go RED | `PENDING` | `--selftest` output |
| whole chain green with the stub carrier | `PENDING` | `receipts/dry-run/<utc>/receipt.json` |
| `claude` launched once against the exact subject | `PENDING` | `receipts/live/turn-1/receipt.json` |
| leased worktree removed and pruned | `PENDING` | receipt `cleanup` + `lane.json.cleanup_observation` |
| Claude Code live-matrix row | `NOT_EXERCISED` | out of this lane's authority |
| independent Gate verdict | `NOT_PERFORMED` | out of this lane's authority |
| Human Admit / merge / promotion | `NOT_PERFORMED` | out of this lane's authority |

## What the live receipt is grounded by

```text
subject.repository/commit/tree     git rev-parse of the checkout the gateway leased from
adapter.descriptor_digest          adapters/claude-code.json, recomputed by the frozen validator
adapter.binary_identity            the descriptor binary; the stub lane is stamped "fixture-adapter"
trace.events_digest/event_count    the bytes of events.jsonl, re-read and re-digested after the run
process.exit_code                  the carrier's own exit status, cross-checked against PROCESS_EXIT
cleanup                            worktree remove, then prune, then an assertion that no lease survives
```

The frozen receipt validator never re-reads the event stream, so a fabricated
`trace.events_digest` survives it. The `fabricated-event-digest` control exists
because of that gap and fails if the cross-check is ever removed.

## Still opaque after a live turn

```text
whether the host read AGENTS.md/CLAUDE.md from the worktree
which tools, models or providers the host used internally
host-side network behaviour; no isolation is attested
whether another host would behave equivalently
```
