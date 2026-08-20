# Inception A5 — bounded discovery and admission verification

Status: **PUBLIC MATCHED-FIXTURE BENCHMARK CANDIDATE**
Upstream profile issue: `ed3c/enterprise_agent_system#17`
Owner issue: `ed3c/bettor-arena#192`

This leaf keeps source identity, terms-before-bytes review, one-SPI mapping and restricted-context isolation, then executes a matched public fixture benchmark. It does not download restricted third-party bytes, establish clean-room independence, benchmark a real external project/model, make legal/commercial conclusions, Human-admit a candidate, activate a provider, merge, release or rollback.

## Implementation subjects

```text
candidate_contract.py
test_candidate_contract.py
benchmark_fixture.py
test_benchmark_fixture.py
```

## Candidate contract

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

## Matched benchmark contract

The P4 fixture has two distinct arms:

```text
protocol-oracle/v1
candidate-contract/v1
```

Both consume the same sealed subject:

```text
workload_digest
environment_digest
case set
repetitions
```

The benchmark intentionally executes the entire categorical denominator on every repetition:

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

`TIMEOUT` and `OOM` are planted bounded fixture failures; they test denominator retention, not real infrastructure capacity. The candidate arm must match the sealed protocol oracle trial-for-trial. Environment/repetition drift, omitted trials, duplicate trial keys, or an unknown outcome fail closed.

The only allowed comparison disposition is:

```text
MATCHED_FIXTURE_NO_SUPERIORITY_CLAIM
```

No latency/cost/quality superiority is inferred from this deterministic fixture.

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

The current public lane covers a sealed fixture through `MATCHED_BENCHMARK_EXECUTED`. External-candidate benchmarking and Human admission remain separate.

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

`BIND_EXTERNAL_PUBLIC_CANDIDATE_TERMS_AND_RUN_MATCHED_BENCHMARK`

An external public candidate must first bind immutable source/terms and an admissible restricted-context route. This fixture cannot proxy that lane.

## Evidence ceiling

```text
candidate contract             DETERMINISTIC_PASS candidate
matched sealed fixture         TARGETED_PUBLIC_CANARY
failure denominator retention  TARGETED_PUBLIC_CANARY
external source ingestion      NOT_PERFORMED
external candidate benchmark   NOT_EXERCISED
external independent Shadow    NOT_EXERCISED
Human admission                HUMAN_ADMIT_REQUIRED
merge / release / rollback     NOT_PERFORMED
```

Machine authority: [`preflight.json`](preflight.json).
