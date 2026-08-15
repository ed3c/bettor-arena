# `packages/harness-console-contracts`

Vocabulary and schemas shared by [`../../apps/harness-console/`](../../apps/harness-console/)
and [`../../services/hitl-api/`](../../services/hitl-api/). Answers #99.

## What is here

```text
hc_vocab.py     UI states, the eight views, task states, the authority boundary, redaction
hc_contract.py  manifest identity, schema digests, vocabulary drift, 18 mutations
contracts/      three schemas under a digest manifest
```

## The authority boundary is a list

`CONSOLE_MAY` is closed and `CONSOLE_MAY_NOT` is enumerated:

```text
may       REQUEST_RETRY  REQUEST_CONTRACT_UPDATE  REQUEST_CANCEL  REQUEST_SCOPED_EXCEPTION

may not   MUTATE_TASK_STATE   WRITE_LEDGER_EVENT   MARK_GATE_PASS   UNSCOPED_FORCE_SKIP
          HIDE_COMPLETED_WITH_EXCEPTION           WIDEN_TOOLS_PERMISSIONS_OR_SECRETS
          MERGE   PROMOTE_RELEASE   ROLLBACK_PRODUCTION
          PERSIST_RAW_PAGE_BODY_OR_PRIVATE_REASONING
```

A list rather than a principle, because a principle gets weakened one adjective at a
time and a list has to be edited in front of a reviewer.

`COMPLETED_WITH_EXCEPTION` is a task state of its own for the same reason: it is the
same colour as `COMPLETED` in every dashboard ever built.

## States

```text
render_state        NOT_IMPLEMENTED  no HTML, no websocket, no browser
live_console_state  NOT_EXERCISED    production console activation is Human Admit
```

Neither may be promoted to PASS.
