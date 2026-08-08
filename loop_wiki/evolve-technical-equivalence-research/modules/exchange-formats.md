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
judge, and sync filenames include their immediate upstream digest prefix, so
the immutable artifacts coexist rather than overwrite each other.
