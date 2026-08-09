#!/bin/sh
set -u
PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init equivalence "hash-bound request -> research/verification/judge packets -> candidate sync bundle -> Human admit boundary"
prove_context equivalence-agents loop_wiki/evolve-technical-equivalence-research/AGENTS.md "loop ownership and authority boundaries -> agent execution"
prove_context equivalence-prompt loop_wiki/evolve-technical-equivalence-research/PROMPT.md "accepted intent -> task contract"
prove_context equivalence-routes loop_wiki/evolve-technical-equivalence-research/ROUTES.md "packet state -> legal next edges and exit meanings"
prove_context equivalence-profile loop_wiki/evolve-technical-equivalence-research/profile/technical-equivalence.md "technical viewpoint -> Gemini prompt and target mirror"
prove_context legacy-prompt-baseline loop_wiki/evolve-technical-equivalence-research/profile/legacy-baseline.md "antigravity prompt bodies -> byte-exact migration comparison"
prove_context exchange-formats loop_wiki/evolve-technical-equivalence-research/modules/exchange-formats.md "packet state -> hash-bound next state"
prove_context equivalence-architecture loop_wiki/evolve-technical-equivalence-research/modules/architecture.md "actor separation and resumability -> runtime boundaries"
prove_context equivalence-readiness loop_wiki/evolve-technical-equivalence-research/modules/production-readiness.md "offline/live/judge/Human axes -> maximum honest claim"
prove_context adapter-registry loop_wiki/evolve-technical-equivalence-research/adapter-registry.json "adapter id -> pinned source, package lock and installed dependency versions"
prove_context request-schema loop_wiki/evolve-technical-equivalence-research/schemas/equivalence-request.schema.json "request bytes -> contract"
prove_context research-request-schema loop_wiki/evolve-technical-equivalence-research/schemas/research-request.schema.json "research request bytes -> contract"
prove_context research-result-schema loop_wiki/evolve-technical-equivalence-research/schemas/research-result.schema.json "provider output -> non-empty candidate contract"
prove_context verification-schema loop_wiki/evolve-technical-equivalence-research/schemas/verification-bundle.schema.json "grounded candidates -> verification contract"
prove_context judge-packet-schema loop_wiki/evolve-technical-equivalence-research/schemas/judge-packet.schema.json "verification -> zero-context packet contract"
prove_context judge-result-schema loop_wiki/evolve-technical-equivalence-research/schemas/judge-result.schema.json "fresh judge output -> result contract"
prove_context sync-schema loop_wiki/evolve-technical-equivalence-research/schemas/sync-bundle.schema.json "judge result -> candidate sync contract"
prove_context route-schema loop_wiki/evolve-technical-equivalence-research/schemas/route-result.schema.json "stage outcome -> route contract"
prove_context adapter-receipt-schema loop_wiki/evolve-technical-equivalence-research/schemas/adapter-receipt.schema.json "live process -> receipt contract"
prove_context canary-schema loop_wiki/evolve-technical-equivalence-research/schemas/canary-observation.schema.json "live receipt -> jitter observation contract"
prove_context equivalence-tests loop_wiki/evolve-technical-equivalence-research/tests/test_cli.py "public seams -> positive and planted-negative controls"
prove_context drift-tests loop_wiki/evolve-technical-equivalence-research/tests/test_drift.py "drift policy -> boundary controls"
prove_context selftest-runner loop_wiki/evolve-technical-equivalence-research/selftest.py "offline/live controls -> aggregate receipt and honest live state"
prove_context profile-validator loop_wiki/evolve-technical-equivalence-research/profile_validator.py "profile controls -> planted omissions and swaps"
prove_context legacy-compare loop_wiki/evolve-technical-equivalence-research/legacy_compare.py "historical source -> byte and behavior comparison"
prove_harness evidence-ledger-ignore loop_wiki/evolve-technical-equivalence-research/.gitignore "per-run evidence confinement -> canonical digest stability"
prove_harness equivalence-runner loop_wiki/evolve-technical-equivalence-research/equivalence.py "request/result/evidence -> route state" \
  -- python3 loop_wiki/evolve-technical-equivalence-research/tests/test_cli.py
prove_harness equivalence-drift loop_wiki/evolve-technical-equivalence-research/drift.py "mirror/provider observations -> hard block or rolling jitter state" \
  -- python3 loop_wiki/evolve-technical-equivalence-research/tests/test_drift.py
EQUIVALENCE_RECEIPT_PATH="$PROVE_ROOT/loop_wiki/evolve-technical-equivalence-research/_runs/proof/selftest-receipt.json" \
EQUIVALENCE_FORCE_RECEIPT=1 \
prove_harness equivalence-controls loop_wiki/evolve-technical-equivalence-research/selftest.sh "profile/legacy/planted defects -> control verdict" \
  -- sh loop_wiki/evolve-technical-equivalence-research/selftest.sh
prove_note equivalence-selftest loop_wiki/evolve-technical-equivalence-research/_runs/proof/selftest-receipt.json "generated physical receipt from the harness step above; per-run evidence is deliberately outside the canonical HEAD digest"
prove_note per-run-evidence loop_wiki/evolve-technical-equivalence-research/_runs/ "raw research and execution receipts are runtime evidence, excluded from canonical digest"
prove_emit
