# `lsp-pool` module

`lsp-pool` owns the bounded worktree-aware language-server pool under [`../../../loop_wiki/lsp-pool/`](../../../loop_wiki/lsp-pool/).

## Capabilities

```text
loopx.lsp-pool/v1
loopx.code-intelligence-evidence/v1
```

Required capabilities:

```text
loopx.code-truth-graph/v2
loopx.runtime-fabric/v1
loopx.worker-fleet/v1
arena.proof-kernel/v1
```

Stage 7 of the PDF terminal queue, answering issue #96. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/lsp-pool/scripts/lsppool.py <check|selftest|query|to-graph>
```

## State Machine

```text
LSP_CAPABILITY_REQUESTED
→ SERVER_VERSION_CONFIG_PINNED
→ WORKSPACE_SUBJECT_LEASE_PINNED
→ POOL_SLOT_SELECTED_OR_CREATED
→ INITIALIZATION_INDEX_FRESHNESS_VERIFIED
→ QUERY_EXECUTED
→ SOURCE_READBACK_COVERAGE_RECEIPT
→ MEMORY_CPU_QUEUE_ACCOUNTED
→ WORKSPACE_INVALIDATED_OR_REUSED
→ SHUTDOWN_RESIDUE_CHECK
```

Freshness is verified before the query. A stale slot answering first and being marked stale afterwards has already returned the wrong answer.

## Boundaries

- `CLEAN`, `UNKNOWN` and `SERVER_FAILED` are three different answers that all produce an empty findings list, and they are never collapsed. Findings arriving with a non-evidence state are discarded and the discard is stated in the reason.
- A slot is keyed on server id, version, config digest **and** workspace subject. A single-root server is not shared across workspaces; a multi-root one may not cross repositories; a slot whose commit or tree moved is stale.
- Eviction never touches a slot with an active request. A full pool of busy slots queues, and a queued query is `NOT_EXERCISED`.
- Eviction order is `(indexed_at, slot_id)` so the same pool evicts the same slot every run.
- The CLI fallback declares a capability ceiling and refuses project-wide queries rather than answering them with an empty list — an empty reference list reads as "this symbol is unused".
- The Code Truth Graph is handed provenance and `EVIDENCE_INPUT_NOT_GATE_VERDICT`, never bare diagnostics; non-evidence states are not admitted at all.
- `canary_state` is `NOT_EXERCISED`: no real language server has been run, and a deterministic fixture is not a live host.
- No canonical state write, gate verdict, merge, promotion or server activation occurs in this leaf.

## Evidence

```sh
sh loop_wiki/lsp-pool/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, ten positive properties, twelve planted controls, and four physical controls driving a real server subprocess that can actually crash, actually hang, and actually answer for the wrong workspace. Control 1 is a pair — a clean file and a crashed server, both returning zero findings, landing in different states — because without the pair the collapse this module guards against is never demonstrated.
