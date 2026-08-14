# `loopx-worker-gateway` module

Machine authority: [`module.json`](module.json)

## Role

Owns the host-neutral Worker request/event/receipt contract and the trusted
fixture process adapter for Codex CLI, Claude Code, Grok Build, OpenCode, Pi and
Ante.

## State machine

```text
REQUEST_VALIDATED
→ HOST_RESOLVED
→ POLICY_CHECKED
→ WORKSPACE_LEASED
→ PROCESS_STARTED
→ OBSERVATIONS_CAPTURED
→ PROCESS_EXITED
→ CLEANUP_VERIFIED
→ WORKER_RECEIPT
```

## Capability boundary

Provides:

- `loopx.worker-gateway/v1`

Requires:

- `loopx.contracts/v1`
- `arena.proof-kernel/v1`

The module is catalogued but not selected in the shared composition. Its
production host registry remains `NOT_EXERCISED`; fixture execution does not
upgrade live host state.

## Evidence

```sh
sh loop_wiki/loopx-worker-gateway/tests/run-all.sh
```

## Forbidden authority

The Gateway and every host adapter must not write LoopX state, Gate verdicts,
Human decisions, promotion, rollback, credentials, or provider health claims.
