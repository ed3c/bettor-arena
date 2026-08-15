# LoopX LSP Pool v1

A bounded, provider-neutral language-server pool for multi-worktree execution.
Reduces repeated indexing cost while proving that every diagnostic belongs to the
exact workspace subject it claims. Stage 7 of the terminal queue, on the Runtime
Fabric (#66), the Worker Fleet (#94) and Code Truth Graph v2 (#69). Answers #96.

## Public port

```sh
python3 loop_wiki/lsp-pool/scripts/lsppool.py <check|selftest|query|to-graph>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` the input is unusable.

There is no subcommand that starts a real language server. Admitting one is a
canary with its own exact binary and config digest, and it is Human Admit — the
contract manifest pins `canary_state` to `NOT_EXERCISED` until then.

## The three answers that all look like zero errors

```text
CLEAN          the server looked and found nothing
UNKNOWN        nobody looked -- unsupported language, unindexed path
SERVER_FAILED  the server crashed, hung, or never initialised
```

A crashed server returns no diagnostics. So does a clean file. So does a file in
a language the server does not handle. Reporting all three as "zero errors" means
a broken index and a genuinely clean tree produce identical evidence, and
whoever reads it downstream cannot tell which one they have.

`answer_for` asks about the server's own health **first**, because that is the
case most easily mistaken for the others. And a finding list that arrives with a
non-evidence state is discarded *out loud*: the reason says how many were thrown
away, so a reader can tell "0 findings" from "findings we could not trust".

Only `CLEAN` and `FINDINGS` are handed to the Code Truth Graph, and they are
handed over with provenance and `EVIDENCE_INPUT_NOT_GATE_VERDICT` attached. A
language server reads source; its output is input to a graph, not a verdict.

## A slot is keyed on the subject, not just the server

Sharing one warm process across five worktrees is exactly what a pool is for, and
it is exactly how a symbol from another worktree comes back looking
authoritative. So a slot matches only when server id, version, config digest
**and** workspace subject all agree:

- a single-root server holding one workspace is not offered to another;
- a multi-root server may share, but not across repositories — it would resolve
  a name to whichever definition it saw first;
- a slot whose workspace commit or tree moved is **stale**, not old. The index
  describes bytes that are no longer there, and reusing it answers about the
  previous commit with no marking of any kind.

Freshness is verified before the query. A stale slot answering first and being
marked stale afterwards has already returned the wrong answer.

## Eviction never kills an active request

A full pool with an idle slot evicts the oldest index — deterministically, by
`(indexed_at, slot_id)`, because a pool that evicts by dict order evicts
differently on every run and no test of it means anything.

A full pool where **every** slot is busy queues instead. Evicting there turns a
capacity problem into a wrong answer for someone who is still waiting. A queued
query is `NOT_EXERCISED`, which is not the same as finding nothing.

## The fallback has a ceiling, and refuses above it

```text
DIAGNOSTICS  SINGLE_FILE_SYNTAX_ONLY
SYMBOLS      SINGLE_FILE_ONLY
REFERENCES   REFUSED_PROJECT_WIDE
DEFINITION   REFUSED_PROJECT_WIDE
```

A `REFERENCES` query answered by a single-file parser returns an empty list, and
an empty reference list reads as *"this symbol is unused"* — which is the reading
someone acts on by deleting it. The fallback refuses rather than answering badly,
and it runs only when admitted with every ceiling acknowledged.

## Evidence

```sh
sh loop_wiki/lsp-pool/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, ten positive
properties, twelve planted controls, and a physical control group.

`tests/fake_server.py` is a **real subprocess**, not a mock: it can actually
crash, actually hang, and actually answer for the wrong workspace, and none of
those three can be demonstrated by a function that returns a dict.

The physical group runs it five ways and prints where each lands:

```json
{"clean-file": "CLEAN", "crashed-server": "SERVER_FAILED",
 "hung-server": "SERVER_FAILED", "wrong-tree": "REFUSED",
 "beta-workspace": "FINDINGS"}
```

Control 1 is a **pair** on purpose — a clean file and a crashed server, both
returning zero findings, landing in different states. Without the pair, every
other check is about one of them in isolation and the collapse this module
guards against is never actually demonstrated.

`scripts/probe_controls.py` prints all six behaviours side by side and exits 2 if
any of them collapsed into `CLEAN`.

## Boundaries

- Every result carries provenance: server id, version, config digest, workspace
  id, repository, root, commit, tree, index time and freshness. A diagnostic
  without provenance is a claim about "the code", and there are five worktrees.
- A result whose provenance names a different tree than the request is refused
  before it becomes a well-formed result.
- `UNKNOWN`, `SERVER_FAILED` and `NOT_EXERCISED` never bear evidence, and the
  manifest refuses to move them into the evidence-bearing set.
- No canonical state write, gate verdict, merge, promotion or server activation
  occurs in this leaf.
