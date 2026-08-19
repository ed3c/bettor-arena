# Inception A5 — bounded discovery and admission

Status: **FIRST PUBLIC IMPLEMENTATION CANDIDATE**  
Upstream profile issue: `ed3c/enterprise_agent_system#17`  
Owner issue: `ed3c/bettor-arena#192`

This leaf implements a strict public candidate contract for source identity, terms-before-bytes review, one-SPI mapping, restricted-context isolation and benchmark-denominator honesty. It does not download restricted third-party bytes, establish clean-room independence, run a real external benchmark, make legal/commercial conclusions, Human-admit a candidate, activate a provider, merge, release or rollback.

## Implementation subjects

```text
candidate_contract.py
test_candidate_contract.py
```

The candidate contract requires:

```text
exact repository + 40-hex commit + 40-hex tree
content digest + terms digest
terms_captured_before_candidate_bytes = true
rights_state = REVIEW_REQUIRED | BLOCKED | UNKNOWN
exactly one target SPI
raw_source_bytes_allowed = false
artifact_mode = DERIVED_INTERFACE_ONLY
self_claim_clean_room = false
Human admission subject = null during automated candidate stage
```

The benchmark lane remains separate. `NOT_EXERCISED` must have no fabricated outcomes. Once executed, every recorded outcome must be one of:

```text
PASS
FAILED
TIMEOUT
OOM
BLOCKED
REJECTED
DEFERRED
INCONCLUSIVE
```

The validator refuses mutable source identities, missing terms digests, rights review after candidate bytes, restricted bytes in the synthesis surface, multiple SPIs, clean-room self-claims, fabricated benchmark outcomes, automated `ADMITTED`, commercial-safety claims or promotion.

## State Machine

```text
SOURCE_PROPOSAL_CAPTURED
→ RIGHTS_AND_FOUR_TIER_TERMS_REVIEWED
→ INTERFACE_FIT_MAPPED
→ RESTRICTED_CONTEXT_BOUND
→ ISOLATED_CANDIDATE_PREPARED
→ MATCHED_BENCHMARK_EXECUTED
→ INDEPENDENT_SHADOW_REVIEWED
→ HUMAN_ADMITTED | REJECTED | BLOCKED | DEFERRED
```

The current public implementation covers the deterministic contract through `ISOLATED_CANDIDATE_PREPARED`; matched benchmark, independent Shadow over an external candidate and Human disposition remain unexercised.

## Existing canonical mechanisms reused

| Existing path | Reusable responsibility | Boundary |
|---|---|---|
| `loop_wiki/loopx-source-ingest/` | rights-before-bytes and source manifests | no semantic/legal conclusion |
| `loop_wiki/loopx-benchmark/` | complete trial denominator | no automatic promotion |
| `loop_wiki/loopx-skill-evolution/` | baseline/mutation/holdout/replication | candidate only until Human Admit |
| `docs/git/AUTOMATED_ADMISSION.md` | exact-subject guarded operations | missing intent/policy fails closed |
| `proof_workflow/` | deterministic proof/control/mutation semantics | no legal clearance |

## Writer lease

```text
loop_wiki/inception-discovery-admission/**
.arena/modules/inception-discovery-admission/**
data/inception-discovery-admission/**
.github/workflows/inception-a5-discovery-admission.yml
```

Shared registries, composition locks, release manifests, ordered terminal queues and aggregate indexes remain read-only.

## Next transition

`RUN_MATCHED_PUBLIC_FIXTURE_BENCHMARK_AND_INDEPENDENT_SHADOW`

The next atom may execute a matched benchmark only on public/reversible fixture subjects with exact workload/environment digests and a complete failure denominator.

## Evidence ceiling

```text
candidate contract          DETERMINISTIC_CANDIDATE
mutation controls           DETERMINISTIC_CANDIDATE
external source ingestion   NOT_PERFORMED
matched benchmark           NOT_EXERCISED
independent Shadow          NOT_EXERCISED
Human admission             HUMAN_ADMIT_REQUIRED
merge / release / rollback  NOT_PERFORMED
```

Machine authority: [`preflight.json`](preflight.json).
