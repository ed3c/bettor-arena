# Logical origin status

[`status.json`](status.json) is generated from `.arena/origins/release.json`.

It records deterministic contract state for the configured GitHub/Forgejo origins and keeps unreachable, mismatched and not-exercised states distinct. A live origin equivalence claim requires an immutable commit/tree/release-manifest probe receipt.
