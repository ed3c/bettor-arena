# Module proof evidence

- [`subjects.lock.json`](subjects.lock.json) binds each selected module to its closure digest, dependency interface digests and declared proof surface.
- [`release-receipt.json`](release-receipt.json) aggregates the exact selected module subjects for one composition release.

Regenerate with:

```sh
python3 scripts/arena_proof.py subjects
python3 scripts/arena_proof.py release
python3 scripts/arena_proof.py check
```

Changing module A should leave unrelated module B's closure subject unchanged. A dependency, proof-kernel or selected contract change must invalidate transitive dependents. The aggregate release is valid only when all required evidence belongs to the same resolved subject.
