# Bettor Agentic Engineering adapters

This directory is the consumer-owned adapter surface for `human-led-agentic-engineering`. The shared method remains provider-neutral; Bettor owns concrete runtime bindings and exact evidence.

## Directory topology

```text
adapters/agentic-engineering/
├── AGENTS.md
├── README.md
├── intent/           IntentLedgerPort implementations
├── review/           ReviewProviderPort implementations
├── observability/    SessionObservabilityPort implementations
├── workspace/        WorkspacePort implementations
└── session/          SessionCarrierPort implementations
```

Provider leaves should be created only when an issue/task contract admits them. Empty/provider-placeholder directories are not implementation evidence.

## Adapter State Machine

```text
PORT_REQUIRED
→ PROVIDER_CANDIDATES_CLASSIFIED
→ LICENSE_BOUNDARY_ASSERTED
→ CAPABILITY_TRIGGER_BOUND
→ PROVIDER_SELECTED
→ ADAPTER_IMPLEMENTED
→ POSITIVE_CONTROL_VERIFIED
→ NEGATIVE_CONTROL_VERIFIED
→ EXACT_SUBJECT_RECEIPT_BOUND
→ CONSUMER_ADMITTED
```

Installation does not imply `PROVIDER_SELECTED`. A provider-specific PASS does not imply `CONSUMER_ADMITTED`.

## Adapter DAG

```text
shared port contract
  ↓
Bettor immutable binding
  ├─ intent provider leaf
  ├─ review provider leaf
  ├─ observability provider leaf
  ├─ workspace provider leaf
  └─ session carrier leaf
       ↓
consumer convergence owner
       ↓
Bettor proof/control/mutation gates
```

Path-disjoint provider leaves are siblings. A child edge is valid only when the child consumes named unmerged bytes/contracts from its parent.

## Data flow

```text
capability trigger
→ rights/license policy
→ provider identity/version
→ adapter invocation
→ provider-native result
→ normalized Bettor evidence
→ independent/native verification where required
→ exact-subject receipt
→ Shadow reconciliation
→ consumer admission or blocked state
```

## Default policy

```text
IntentLedgerPort
  GitHub Issues           primary
  Kata                    optional / MIT

ReviewProviderPort
  Bettor native gates     primary correctness lane
  roborev                 optional evidence / MIT

SessionObservabilityPort
  Bettor native metrics   primary
  AgentsView              optional read-only evidence / MIT

WorkspacePort
  Git Town                primary
  kwt                     optional / Apache-2.0
  Kenn Forge              optional external boundary / Elastic-2.0

SessionCarrierPort
  existing local/remote carriers
  Ghosthub                optional external boundary / AGPL-3.0
```

Restricted provider source is not copied into this Apache-2.0 consumer core by default.

## Current Stack

```text
#189 B1 consumer binding        ACTIVE METHOD/CONTRACT SLICE
#234 shared live delivery       PROCESS_DEPENDENCY / OPEN
#393 review-provider contract   PROCESS_DEPENDENCY / OPEN
#394 intent/observability       PROCESS_DEPENDENCY / OPEN

future path-disjoint adapters   SIBLINGS
final shared-index update       one CONVERGENCE owner
```
