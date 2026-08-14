# Additional receipts

This directory is reserved for admitted versioned receipts that do not belong to a more specific evidence namespace.

Every receipt must state its schema, subject, observed provenance, status and named exclusions. A producer must fail closed on ambiguous or stale subjects. Per-run private payloads belong in ignored runtime storage, not here.

`skill-measurement-universal-v2-dev.json` is a consumer acceptance receipt for
the shared measurement **protocol closure**. Its PASS is limited to catalog and
conformance controls; it explicitly preserves repo-agent-native physical v2 as
`NOT_EXERCISED` and the older 144-cell behavior result as `FAIL`.
