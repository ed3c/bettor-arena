# Host-state measurement protocol

Provider readiness is four independent states. Never collapse them into “installed” or infer a later state from an earlier one.

| State | Question | Minimum evidence |
|---|---|---|
| `installed` | Is an exact executable or adapter identity present? | executable path plus exact version or immutable digest |
| `running` | Do all required local services answer their own health probes now? | timestamped per-service result; partial stacks stay partial |
| `wired` | Can the selected Claude/Codex carrier reach the admitted adapter under current host policy? | carrier-specific tool discovery and a bounded canary receipt |
| `data-ready` | Is an index or memory namespace built for the exact repository commit/tree and current schema? | subject commit/tree, index digest, staleness verdict, cleanup scope |

## Measurement rules

1. Re-run probes in the current host/session. A previous dashboard or document is not current evidence.
2. Record provider, executable/adapter identity, repository commit/tree, index digest, timestamp, named state, exit code, and sanitized output digest.
3. Keep secrets and raw credentials out of tracked files and receipts.
4. Treat unreachable, blocked, absent, stale, and not-exercised as different results.
5. Never promote `installed` to `running`, `running` to `wired`, or `wired` to `data-ready` by inference.
6. Feed live results through a subject-bound query receipt; do not edit tracked provider manifests to mirror mutable host state.

The tracked provider registry deliberately remains `CANDIDATE / NOT_EXERCISED`. Admission requires an immutable adapter identity, live canaries, cleanup/staleness evidence, paired A/B results, and Human Admit.
