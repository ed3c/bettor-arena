# `apps/harness-console`

The Harness Console's **view model** layer. Answers #99 together with
[`../../services/hitl-api/`](../../services/hitl-api/) and
[`../../packages/harness-console-contracts/`](../../packages/harness-console-contracts/).

## `render_state: NOT_IMPLEMENTED`

There is no HTML here, no websocket, no browser and no server. What is here is the
data a renderer would render, and the reason that split is written down rather than
implied: a mechanism described in Markdown may still be `NOT_IMPLEMENTED`, and a
directory called `apps/` invites the assumption that something runs in it.

A rendering layer would need a live console to be exercised against, and production
console activation is Human Admit. Shipping an unexercised one and calling the issue
answered would promote `NOT_IMPLEMENTED` to PASS.

What **is** exercised is everything the renderer would depend on: the projection is
rebuildable from canonical events, every view is bounded and says when it truncated,
the exception state is counted separately from completion, and no view can express a
gate verdict.

## The eight views

```text
thread_task_graph         task topology, and COMPLETED_WITH_EXCEPTION on its own line
gate_evidence_inspector   verdicts as the ledger recorded them; may_write_verdict: false
diagnostics_panel         LSP/linter/test output, bounded
git_diff_viewer           diffs, capped per entry (4 KiB) as well as per list
quota_retry_panel         retries and token budget
provenance_panel          memory and code-truth provenance
hitl_dialog               the closed action set and the bindings a request will carry
receipt_links             stack/host/runtime receipts, as references not copies
```

Every list view carries `shown`, `total`, `truncated` and `limit` — always, including
when nothing was dropped. A field that only appears when it is interesting is a field
nobody looks for, and a truncated list that does not say so is just a shorter list.

## Boundaries

- The view layer reads a projection and nothing else. It performs no I/O, holds no
  cache, and has no path to the ledger.
- `hitl_dialog.draftable` is false on an `INCOMPLETE` projection. A dialog that opens
  over a gap drafts a decision about history it did not show.
- Redaction runs over the whole structure and the output is re-scanned. The console
  renders whatever an agent produced, and this is the last point before a screen.

## Evidence

```sh
sh tests/harness-console/run-all.sh
```
