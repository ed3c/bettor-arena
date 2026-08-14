# `loopx-source-ingest` module

`loopx-source-ingest` owns the source boundary under [`../../../loop_wiki/loopx-source-ingest/`](../../../loop_wiki/loopx-source-ingest/).

## Capabilities

```text
loopx.source-ingest/v1
loopx.evidence-manifest/v1
```

Required capabilities:

```text
loopx.contracts/v1
arena.proof-kernel/v1
```

Stage 10 of the PDF terminal queue, answering issue #104. It precedes the knowledge compiler (#70), which consumes the manifest this module emits. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-source-ingest/scripts/ingest.py \
  <check|selftest|ingest|verify-manifest>
```

## State Machine

```text
SOURCE_DECLARED
→ ACCESS_RIGHTS_DESTINATION_AUTHORIZED
→ RAW_ARTIFACT_CAPTURED_OR_BLOCKED
→ CONTENT_DIGESTED
→ TYPE_DEPENDENCY_KEY_CLASSIFIED
→ LOCATORS_EXTRACTED
→ TRANSCRIPT_FRAME_CODE_NORMALIZED
→ EVIDENCE_MANIFEST_EMITTED
→ NOTES_REPO_COMMIT_TREE_PINNED
→ QUALITY_INJECTION_GAP_GATES
→ READY_FOR_KNOWLEDGE_COMPILATION
```

Rights are checked before bytes are read. A capture that reads first has already made the copy the check is deciding about.

## Boundaries

- A locator is `READ_FROM_ARTIFACT` or it is not evidence. `ESTIMATED` and `ASSUMED` exist in the vocabulary so a pipeline can say it guessed, and neither is admissible — an estimated timestamp has the same format and the same plausible value as a real one.
- A transcript with no cues yields no timestamps. A PDF extract missing page 2 yields two pages and reports the third missing, never an observed empty one.
- Two speakers in one recording are one source. Independent support is counted by dependency key.
- A repost of identical bytes is one piece of evidence: identity is the artifact digest plus the position inside it, not the URL.
- Every declared source that produced no bytes appears as a schedulable gap with its own reason — `BLOCKED_BY_RIGHTS`, `BLOCKED_BY_ACCESS`, `ABSENT` or `GAP`. Silence is indistinguishable from having looked and found nothing.
- Credential-bearing query parameters are refused at declaration, because a URL becomes a locator and a locator is copied into every note.
- Source text is quarantined data with `is_data: true` and no authority. Injection-shaped passages are recorded as findings, not errors — a security note quoting an attack is a legitimate document — and the policy fields are compared before and after ingest.
- OCR text needs its artifact digest and a bounding box, or nobody else can check it.
- The manifest is an inventory. It decides nothing about what any of the evidence means.

## Evidence

```sh
sh loop_wiki/loopx-source-ingest/tests/run-all.sh
```

Two schemas under a digest manifest, eight manifest mutations, ten positive properties, eleven planted controls, and five physical controls that write real artifacts and read them back — checking that every cue timestamp is a substring of the file it came from, that an untimed transcript yields nothing, and that ingesting a transcript containing a real injection string changed no declaration.
