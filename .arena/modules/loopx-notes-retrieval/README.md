# `loopx-notes-retrieval` module

`loopx-notes-retrieval` owns the macro/micro knowledge split under [`../../../loop_wiki/loopx-notes-retrieval/`](../../../loop_wiki/loopx-notes-retrieval/).

## Capabilities

```text
loopx.notes-retrieval/v1
loopx.openwiki-projection/v1
```

Required capabilities:

```text
loopx.source-ingest/v1
loopx.contracts/v1
arena.proof-kernel/v1
```

Stage 11 of the PDF terminal queue, answering issue #105. Consumes the evidence manifest from #104 and precedes Notes→Scaffold (#70). Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-notes-retrieval/scripts/notesretrieval.py \
  <check|selftest|build|query>
```

Exit `0` ok, `2` refused, `64` unusable input, `70` the vector provider is absent — nothing was asked, so nothing about the notes follows.

## Boundaries

- Four things a retrieval can mean by "nothing": `MISS`, `NOT_INDEXED`, `PROVIDER_ABSENT` and a `HIT` that found something else. **None of them prove absence**, and every result carries `absence_proof: NONE`.
- A hit is a `RETRIEVAL_CANDIDATE` with provenance. It is not a fact and not a gate verdict; the final authority is current source and evidence.
- Every hit is read back against the source it cites. A chunk whose text is no longer in that file is `DRIFTED`, not a hit — the citation would otherwise look perfect.
- An index subject is the commit, the tree, the source-manifest digest **and** the compiler policy. Subject drift and policy drift are reported separately: one says the notes moved, the other says the way we read them did, and the second returns confident nonsense rather than nothing.
- Generated OpenWiki pages carry a derived marker **in their content**, so a page copied into a notes file keeps it after losing its filename. Citing one back as evidence is refused.
- The macro read needs no provider. A missing vector store costs the micro queries and nothing else.
- Uncovered evidence is `UNKNOWN`, never absent.
- `live_provider_state` is `NOT_EXERCISED`: LanceDB or any other store is an adapter choice after exact version and license admission.

## Evidence

```sh
sh loop_wiki/loopx-notes-retrieval/tests/run-all.sh
```

Three schemas under a digest manifest, nine manifest mutations, ten positive properties, twelve planted controls, and five physical controls that write an index to a file, edit the notes on disk, and check the stale index refuses rather than answering — then restore the source and check the query works again, so the refusal is attributable to the drift rather than to the readback.
