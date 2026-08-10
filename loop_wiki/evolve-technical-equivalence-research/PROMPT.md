# PROMPT.md — technical viewpoint → implementation equivalent

Given one hash-bound request, compile the canonical profile into a Gemini Deep
Research request. Preserve P1–P9/V1–V5, Path B's four stages, the single/batch gap
prompts, the six-topic cap and explicit truncation. Normalize candidates into
`candidate`, `technical_equivalent`, or `[推論]`.

Bind the generated prompt to the versioned candidate contract. Only lossless
shape normalization is automatic and must be ledgered. Missing semantic fields
do not authorize invented evidence. Only a missing `falsification_conditions`
field gets one candidate-only repair attempt; a second failure lands
`candidate_invalid` and must not restart the provider carrier.

`technical_equivalent` requires a commit-bound checkout, code-audit receipt and
real-probe receipt. Load-bearing or costly uncertainty also requires a rebuilt
alternative and side-by-side comparison. A fresh-zero-context judge may reject
but never manufacture evidence. Human admit is the only promotion edge that may
write the generated mirror.
