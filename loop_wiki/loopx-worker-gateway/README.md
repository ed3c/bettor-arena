# LoopX Worker Gateway v1 — six-host protocol and evidence boundary

Status: **contract and fixture-execution candidate for issue #64**. This leaf defines one subject-bound protocol for Codex CLI, Claude Code, Grok Build, OpenCode, Pi, and Ante. It does not claim that any of the six real hosts has been physically executed by this branch.

The source architecture routes heterogeneous Workers beneath a deterministic LoopX control plane. The gateway keeps that separation while correcting unsafe shortcuts:

```text
LoopX typed dispatch proposal
+ exact repository/task/Skill/context subject
+ trusted workspace lease
+ resource/network/environment policy
        ↓
host adapter
        ↓
externally observable event stream
+ stdout/stderr/diff/artifacts
        ↓
Worker receipt
        ↓
independent Gates
        ↓
LoopX reducer
```

The Worker receipt is not a Gate result and cannot mutate canonical task state.

## Directory

```text
loop_wiki/loopx-worker-gateway/
├── README.md
├── contracts/
│   ├── manifest.json
│   ├── adapter-descriptor.schema.json
│   ├── worker-request.schema.json
│   ├── worker-event.schema.json
│   └── worker-receipt.schema.json
├── adapters/
│   ├── registry.json
│   ├── codex-cli.json
│   ├── claude-code.json
│   ├── grok-build.json
│   ├── opencode.json
│   ├── pi.json
│   ├── ante.json
│   └── unimplemented.py
├── scripts/
│   ├── gateway_common.py
│   ├── gateway_contract.py
│   ├── gateway_runtime.py
│   ├── gateway.py
│   ├── fake_worker.py
│   ├── check_gateway.py
│   └── control_gateway.py
└── tests/
    ├── run-all.sh
    └── fixtures/
        ├── good/
        └── hollow/
```

Machine module authority: [`.arena/modules/loopx-worker-gateway/module.json`](../../.arena/modules/loopx-worker-gateway/module.json).

## Host matrix

| Host | Classification | Descriptor state | Trace ceiling |
|---|---|---:|---|
| Codex CLI | source-visible host, provider-controlled model | `NOT_EXERCISED` | `PROCESS_ONLY` |
| Claude Code | gray-box | `NOT_EXERCISED` | `PROCESS_ONLY` |
| Grok Build | white-box reference at reviewed source pin | `NOT_EXERCISED` | `SOURCE_VERIFIED_INTERNAL` ceiling, not observed evidence |
| OpenCode | white-box reference | `NOT_EXERCISED` | `TOOL_OBSERVED` |
| Pi | white-box reference | `NOT_EXERCISED` | `TOOL_OBSERVED` |
| Ante | experimental gray-box | `NOT_IMPLEMENTED` | `PROCESS_ONLY` |

A descriptor is a contract, not a live receipt. The registry is required to preserve `live_matrix_state: NOT_EXERCISED`.

## Authority ceiling

A Worker may:

- read its immutable Context Capsule and Skill;
- edit only leased writable paths;
- emit normalized observations;
- return stdout, stderr, diff and artifacts;
- exit, time out or be cancelled.

A Worker may not:

- write LoopX state or the append-only ledger;
- submit a Gate verdict;
- perform Human Admit;
- promote or roll back a release;
- write durable memory;
- claim hidden gray-box tool calls or reasoning;
- retain credentials, workspaces or descendants after cleanup.

## White/gray-box semantics

```text
PROCESS_ONLY
  OS process, streams, exit and filesystem effects only

TOOL_OBSERVED
  externally emitted structured tool events, without inferring hidden steps

SOURCE_VERIFIED_INTERNAL
  internal event only when exact source/runtime identity and event instrumentation are both pinned
```

A host classification sets an upper bound. A receipt may report less complete evidence. Missing internal telemetry is `UNKNOWN`, never synthesized.

## Trusted local execution path

```sh
python3 loop_wiki/loopx-worker-gateway/scripts/gateway.py run \
  --request request.json \
  --adapter adapter.json \
  --repo /trusted/host/repository \
  --output /trusted/host/artifacts/run-001 \
  --receipt-id run-001
```

`--repo` is a trusted operator argument and is not part of the untrusted Worker request or MCP surface. The gateway checks the exact commit/tree, Skill digest, context files, prompt artifact, path policy, process group and cleanup.

The current local adapter cannot attest `DENY` or `ALLOWLISTED` network policies. Such requests return `SKIPPED_BY_POLICY`; a physical runtime-fabric adapter is required.

## Fixture execution

The test-only fixture adapter proves the gateway mechanism in a disposable Git worktree:

```text
exact subject
→ detached worktree
→ bounded fixture Worker
→ normalized three-event stream
→ allowed-path check
→ stdout/stderr/diff artifacts
→ cleanup
→ PASS receipt
```

This does not prove any of the six real hosts.

## Validation

```sh
sh loop_wiki/loopx-worker-gateway/tests/run-all.sh
```

Expected evidence includes:

- four fail-closed schemas and content hashes;
- six exact descriptors and a `NOT_EXERCISED` live matrix;
- positive contract fixture;
- non-exercised receipt;
- planted subject, host, path, secret, trace, cleanup and authority mutations;
- one actual fixture subprocess in a disposable worktree;
- production Codex descriptor remaining `NOT_EXERCISED`;
- `0 / 2 / 64` behavior and cleanup.

## Molecular boundary

This terminal leaf is a sibling of the ledger leaf: both depend on LoopX Contract v1, but the Worker Gateway does not need the ledger implementation to define or test its observation protocol. Final composition selection, real host canaries, runtime-fabric attestation, public `loopctl`/MCP projection and release admission remain separate leaves.

Merge remains a Human decision.
