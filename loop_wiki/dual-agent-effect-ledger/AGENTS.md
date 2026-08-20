# Dual-Agent Effect Ledger — Agent Contract

This directory is a deterministic Effect Plane candidate. Read this file only after `README.md`.

## Required read order

```text
README.md
→ AGENTS.md
→ stack-index.json
→ effect_contract.py
→ effect_reducer.py
→ effect_policy_gate.py
→ effect_provider_adapter.py
→ effect_compensation.py
→ effect-matrix-preflight.json
→ test_effect_matrix.py
```

## Authorities

```text
canonical task writer   loopx-ledger
canonical effect writer dual-agent-effect-ledger
workflow authority      proposal / EFFECT_ADMISSION_REQUEST only
provider authority      observation only
browser/API authority   route-scoped observation only
PR #196 substrate       reference only / writer NONE
Shadow                  read-only evaluation / no promotion authority
Human                    credential/provider/live-effect admission
release                  #68 only
```

No Worker, model, provider, browser/API adapter, transport ACK, workflow state, provider-native idempotency result, fixture, or documentation may self-promote task/effect/live/release state.

## Exact current deterministic subjects

```text
DA-EF-C / PR #216
  f9b64994979042fc3726c524944a61da4f9cb8b5
  tree e0f0ff4bf0b55627b420ace027043c3b7fee5d1d

DA-EF-K / PR #224
  6b99815d2b3fb76436c05641b32d1e7be1a36ec4
  tree ac7dba91541dfb8c1bcbc1d4f9bc7d2726735eac

DA-EF-P / PR #225
  ba9ebfe5f4efa01d040ec3b51f93b32045899b23
  tree a128ea330647d9a3c83f7852eb7174bcdbbd6511

DA-EF-A / PR #226
  ee7b99080e71c834c979ba56fb2d9a3f6c7c27db
  tree 67ed1df8a447e1e4ac958a819203ecf5d4ce8020

DA-EF-COMP / PR #227
  50f0e5ca7a9a2860d7429f00f3a7b3189910ba08
  tree 40ae3458df32137fdb1b05e42e7985f5607b5715

DA-EF-E / PR #228
  5ba49cc935c059a8fd96e78773c3df9a2ab9be4c
  tree 6eb20d4289d7296be7348c70aa8618e2d8a9aecc
```

These are candidate subjects, not merge/release authority. Rebind before acting if any head moves.

## State-machine ownership

```text
effect_contract.py
  identity + state vocabulary + transition law

 effect_reducer.py
  ordered history + reservation + attempt denominator + readback-gated commit

 effect_policy_gate.py
  policy + Human approval + precondition admission

 effect_provider_adapter.py
  provider-attempt/result/readback observation contract

 effect_compensation.py
  linked compensation-effect identity and lineage

 test_effect_matrix.py
  deterministic denominator / disagreement controls
```

No file in this directory may become a second LoopX task writer. Provider/readback and compensation adapters must emit observations/proposals and return to `dual-agent-effect-ledger` for canonical effect decisions.

## Process DAG vs Git DAG

Process dependency:

```text
runtime-env PR #69
→ workflow PR #202
→ PR #216
→ PR #224
→ PR #225
→ PR #226 + PR #227
→ PR #228
→ #222 docs
→ #223 live
→ #186 physical E2E
→ truth-verify-loop #22
→ #68 release
```

Git ancestry follows byte dependency only:

```text
PR #216
└─ PR #224
   └─ PR #225
      ├─ PR #226
      ├─ PR #227
      └─ PR #228 (base #225; exact sibling blobs materialized)
           └─ #222 docs child
```

Cross-repository dependencies are exact commit/tree/schema/digest edges and MUST NOT be represented as fake Git parents.

## Effect laws

```text
RESULT_UNKNOWN != EFFECT_COMMITTED
provider SUCCESS != EFFECT_COMMITTED
transport ACK != EFFECT_COMMITTED
workflow COMPLETED != EFFECT_COMMITTED
provider-native idempotency != canonical effect authority
fixture readback != live readback
compensation != history rewrite
```

One logical effect may have multiple attempts but at most one accepted commit. Every attempt stays in the denominator. A timeout/connection-loss remains unresolved until exact target readback/reconciliation. Compensation is a new linked effect with its own identity, admission, attempt and readback.

## Path ownership

Implementation leaves own only their declared files. Shared directory routing/docs/status is owned by #222 after implementation/evidence leaves stabilize. Root repository composition, generated locks, release receipts and promotion remain #68 authority.

For #222, writable shared paths are limited to:

```text
loop_wiki/dual-agent-effect-ledger/README.md
loop_wiki/dual-agent-effect-ledger/AGENTS.md
loop_wiki/dual-agent-effect-ledger/stack-index.json
loop_wiki/dual-agent-effect-ledger/test_effect_docs.py
.github/workflows/dual-agent-effect-docs.yml
```

Do not edit root README/AGENTS, release locks, module composition, provider credentials, or production configuration in this leaf.

## Forbidden substitutions

Never substitute:

```text
workflow state     for effect state
provider result    for target readback
provider idempotency for canonical reservation
fixture evidence   for live evidence
browser evidence   for API evidence
transport auth     for effect authorization
Human fixture      for live Human admission
task PASS          for effect commit
effect commit      for user outcome
CI PASS             for merge/release
skipped workflow    for PASS
```

## Current evidence ceiling

```text
COMPLETE_DETERMINISTIC_EFFECT_MATRIX_ONLY
```

Deterministic closure includes contract, reducer, policy/Human/precondition semantics, provider/readback boundary, compensation lineage and the 16-case matrix. It excludes real credentials, provider I/O, live target readback, live Human/policy decisions, physical transport/identity, user outcome, merge, release and rollback.

## Live stop condition — #223

Do not enter #223 from GitHub fixture/CI alone. Stop with `HUMAN_TRUSTED_AUTHORITY_REQUIRED` unless all of the following are explicitly admitted:

```text
safe reversible non-production target
provider enrollment
opaque credential-handle resolution authority
exact provider/resource/action
policy and Human approval scope
readback mechanism
safe duplicate/redelivery plan
optional compensation plan
cleanup/residue observation
```

No production customer data or irreversible action is allowed as the first live canary.

## Zero-context handoff

A fresh Agent continuing this subtree must:

1. re-fetch PR #216/#224/#225/#226/#227/#228 exact heads and mergeability;
2. run/read the exact-head Effect matrix CI, not stale run IDs;
3. verify `stack-index.json` matches those exact subjects;
4. verify PR #196 remains `REFERENCE_SUBSTRATE_ONLY` and writer `NONE`;
5. preserve the 16-case deterministic denominator;
6. preserve `NOT_EXERCISED` for every live/provider/user/release lane;
7. use #223 only after trusted/Human live admission;
8. route final composition, merge/release/rollback authority through #68.

If an exact subject, authority, denominator or path lease drifts, stop and rebind before writing.
