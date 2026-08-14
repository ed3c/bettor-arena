# Worker Gateway contracts

| Contract | Authority |
|---|---|
| `adapter-manifest.schema.json` | Host identity, visibility ceiling, execution allowlist and zero state/Gate/Human authority |
| `worker-request.schema.json` | Exact repository/task/Skill/context/workspace subject plus typed argv and policy requirements |
| `worker-event.schema.json` | Gateway-observed process, filesystem, artifact and cleanup events only |
| `worker-receipt.schema.json` | Non-authoritative observation receipt; `OBSERVED_SUCCESS` is not Gate `PASS` |

The six host registrations are in [`../registry.json`](../registry.json) and [`../adapters/`](../adapters/). Static manifests remain `NOT_EXERCISED`; live claims require exact runtime receipts in later terminal leaves.
