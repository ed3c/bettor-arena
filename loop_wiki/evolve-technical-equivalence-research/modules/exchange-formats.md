# Exchange formats

Every packet is immutable and hash-bound to its immediate predecessor. The five
external packet families are request, research request/result, verification
bundle, judge packet/result and sync bundle. Schemas live in `schemas/`.

`fixed_context`, `iteration_context`, and `emergent_context` remain separate.
The sync bundle contains only allowlisted generated files, their exact bytes,
the expected target HEAD and upstream digests. Raw Gemini output and run receipts
stay in `_runs/`; they are not promoted into the skill mirror.

Multiple research results for one request are legal (for example, raw Gemini
candidate output followed by independently enriched evidence). Verification,
judge, sync, and route-result filenames include a binding digest prefix, so the
immutable artifacts coexist rather than overwrite each other.

Research request v1.1 carries a versioned candidate-contract digest. Live
research result v1.1 and adapter receipt v1.2 repeat that digest so cached
transport evidence cannot answer for a different candidate schema. Verification
bundle v1.1 records lossless normalization, the bounded repair ledger and every
candidate-level validation error.

Adapter receipt v1.2 retains the execution identities introduced in v1.1. The
execution-policy digest identifies which external write-path exports may be
redirected plus the local persistent-session runner and transport. The
execution-mirror digest identifies the copied/transformed modules, redirect
targets and verified dependency directory used by that attempt. These are
runtime receipts only; neither grants semantic authority or Human admit.
