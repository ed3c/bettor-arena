# Decision: create-only attestations and disposable retrieval

## Status

Planned and human-aligned; implementation and backend selection remain pending.

## Attestation decision

Use create-only refs:

```text
refs/attestations/<candidate>/<axis>/<profile-sha>/<attestation-sha>
```

The last component prevents a retry from overwriting a prior result. There is
no mutable `latest` truth ref. The projector reopens all candidate/profile-bound
attestations and derives freshness and effective state.

The earlier shorter ref shape without `<attestation-sha>` is rejected because
it cannot be both append-only and retryable.

## Retrieval decision

LanceDB and SQLite FTS5 are candidates, not truth stores. Milestone 10 must run
the same corpus, queries, update workload, deletion/rebuild test, resource
measurement, and provenance checks against both. LanceDB wins only on measured
fitness and verified runtime packaging; otherwise SQLite FTS5 is the boring
fallback.

Deleting either index must leave commit, verification, progress, and admission
results byte-equivalent after projection rebuild.
