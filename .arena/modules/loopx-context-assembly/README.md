# `loopx-context-assembly` module

`loopx-context-assembly` owns the Prompt IR and its host projections under [`../../../loop_wiki/loopx-context-assembly/`](../../../loop_wiki/loopx-context-assembly/).

## Capabilities

```text
loopx.context-assembly/v1
loopx.prompt-ir/v1
```

Required capabilities:

```text
loopx.notes-retrieval/v1
loopx.contracts/v1
arena.proof-kernel/v1
```

Stage 12 of the PDF terminal queue, answering issue #95. Consumes the retrieval surface from #105 and feeds the host runtimes. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-context-assembly/scripts/contextasm.py \
  <check|selftest|assemble|emit|verify>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` unusable input — an empty projection directory is `64`, because "nothing to compare" and "they disagree" are different answers that would otherwise render identically as a non-zero exit.

There is no subcommand that renders a single host in isolation. A host rendered alone cannot disagree with anything.

## Boundaries

- **One IR, six projections.** `ante`, `claude`, `codex`, `grok-build`, `opencode`, `pi`. Provider-specific formatting is presentation: every projection carries `authority: PRESENTATION_ONLY` and changes no evidence and no permission.
- **The normative law is delimited and compared.** Six hand-maintained prompts diverge in exactly the paragraph that must not differ, and the divergence is found by an agent doing on one host what another forbids. `law_matrix` digests the delimited region of every projection; more than one digest is red.
- **A host that was never projected is absent, not agreeing.** Five agreeing projections and one missing is refused, because that is the state a hand-maintained prompt drifts in.
- **The cacheable prefix refuses to contain anything that varies.** `render_prefix` scans its own rendered output for timestamps, epochs, UUIDs, `run_id`, `session_id`, `nonce`. Nothing errors when a volatile value reaches a prompt cache; the only symptom is the bill.
- **Tool order is canonicalised, and the order digest covers order and schemas together.** A reorder changes the prefix bytes and so the cache key, and is invisible in review without a digest that moves with it.
- **An evidence anchor is never dropped to fit a budget.** A claim whose anchor was trimmed still reads as cited, and the citation is what a reader checks. When the anchors alone exceed the budget the assembler refuses rather than choosing which evidence to lose; every trim says what it dropped.
- **A cache hit rate is scoped to one host, one model, one provider.** Cache behaviour is a property of a tokenizer, a serving stack and a billing policy. `universal_claim` is never true, and reading a receipt as evidence about another environment is refused.
- `live_host_state` is `NOT_EXERCISED`: the six projections are rendered and compared here, not sent to six real agent runtimes.

## Evidence

```sh
sh loop_wiki/loopx-context-assembly/tests/run-all.sh
```

Three schemas under a digest manifest, fourteen manifest mutations, fifteen positive properties, nineteen planted controls, and eight physical controls that write the six projections to real files, edit the law in one of them on disk, and check the from-disk comparison turns red — then restore the file and check it turns green again, so the red is attributable to the edit rather than to the reader being broken. Two of the eight render the prefix in separate interpreters under different `PYTHONHASHSEED` values and opposite caller-supplied tool order, because a prefix that is stable inside one process is not thereby stable across the process that caches it.
