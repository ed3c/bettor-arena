# ROUTES.md

`equivalence-request → research-request → research-result → verification-bundle
→ judge-packet/result → sync-bundle → external Human admit → target-side apply`.

Legal route states: `research_required`, `research_pending`, `candidate_ready`,
`verification_failed`, `judge_required`, `sync_bundle_ready`, `human_required`,
`admitted`, `no_drift`, `not_exercised`, `live_revalidation_required`.

`candidate_ready` is deliberate: Gemini cannot self-author code-audit/probe
receipts. Supply a new, digest-keyed enriched research result after the
independent audit/probe/rebuild step; only then can `judge_required` be reached.

Exit 0 means a valid route state, including pending/human-required. Exit 2 means
a declared check failed. Exit 64 means malformed contracts or absent required
tools. A provider's non-zero exit is recorded verbatim in its adapter receipt.

Assurance axes are not route aliases. Offline surface, live carrier, fresh
semantic judge calibration, and external Human admit are recorded separately;
an unexercised later edge never inherits an earlier green.
