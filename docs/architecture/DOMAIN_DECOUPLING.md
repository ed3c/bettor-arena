# Domain Decoupling Contract — Bettor consumer binding

Document ID: `DOMAIN-DECOUPLING-V1`  
Document Role: `CONSUMER_BINDING`  
Repository Plane: `INTEGRATION_ACCEPTANCE`  
Canonical method: resolved by `.agents/bindings/*.json`; never by mutable `main` or a sibling checkout  
Current-state authority: repository `CONTEXT.md`, machine bindings, queues, receipts, and exact GitHub/Forgejo/local subjects

This document maps the shared procedural-core/domain-port contract onto Bettor Arena's existing directories. It does not duplicate canonical shared Skill bodies or replace machine manifests.

## 1. Scope

Load this document for work that changes:

```text
shared Skill requirements or exact bindings
.skill-bindings domain retargeting
.arena module boundaries or public capabilities
.runtime-env profiles or provider-routing ports
proof/evidence requirements
cross-module dependency direction
consumer authority or effect boundaries
```

Do not load it for an unrelated source edit whose nearest README and machine contract are sufficient.

## 2. Related routes

| Topic | Route |
|---|---|
| route names and hop rules | [`DOCUMENT_ROUTING.md`](DOCUMENT_ROUTING.md) |
| states and transitions | [`STATE_MACHINES.md`](STATE_MACHINES.md) |
| target modular architecture | [`modular-integration-requirements.md`](modular-integration-requirements.md) |
| current modular status | [`modular-integration-status.md`](modular-integration-status.md) |
| repository-plane and release flow | [`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md) |
| source/issue/PR/eval/receipt lineage | [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md) |
| complete documentation map | [`../INDEX.md`](../INDEX.md) |

## 3. Ownership map

| Bettor path | Domain-decoupling role | Machine or local authority |
|---|---|---|
| [`.agents/`](../../.agents/README.md) | desired shared capabilities, exact bindings, module-set aggregation, host projections | `shared-skills.requirements.json`, `bindings/*.json`, `module-set.json` |
| [`.skill-bindings/`](../../.skill-bindings/README.md) | Bettor-owned domain retargeting and evidence ceilings | each binding's machine contract and exact source identity |
| [`.arena/`](../../.arena/README.md) | module manifests, composition, context, public capability ownership | module/composition manifests and `loopctl` contracts |
| [`.runtime-env/`](../../.runtime-env/README.md) | secret-free runtime/profile projection | binding/profile/policy files and runtime receipts |
| [`proof_workflow/`](../../proof_workflow/README.md) | proof, independent control and mutation semantics | proof specs, checkers and receipts |
| [`data/`](../../data/README.md) | generated snapshots and execution receipts | content digests and producing verifier |
| `docs/architecture/` | stable architecture and dependency laws | this document plus machine routes |
| `docs/integration/` | cross-repository binding/release flow | exact release/binding contracts |
| `docs/traceability/` | human navigation to exact lineage | issues, PRs, workflows and receipts remain authority |

## 4. Procedural core and consumer specialization

```text
skills-shared portable SKILL.md
→ Bettor requirement
→ immutable shared binding
→ Bettor domain module/adapter
→ Bettor runtime selection
→ Bettor proof/control/mutation
→ Bettor-owned receipt
```

The shared core defines method, proof obligations, stop conditions and domain ports. Bettor supplies repository facts, terminology, module selection, runtime policy, privacy policy, acceptance policy and stronger constraints.

Bettor must not copy a shared `SKILL.md` and edit it as a second canonical body.

## 5. Exact binding law

A shared dependency is usable only when the consumer machine state resolves:

```text
source repository
commit and tree or immutable artifact digest
selected Skill path/content digest
consumer requirement digest
consumer binding digest
runtime/profile selection when required
rollback subject
```

The following are development conveniences or observations, not release identity:

```text
mutable main/latest
local symlink
sibling checkout path
provider installed/healthy
README statement
old successful SHA
```

## 6. Domain ports in Bettor

Bettor ports include:

| Port | Consumer owner | Typical evidence |
|---|---|---|
| `repository-context` | nearest bounded-context README/manifest | exact repository/path/subject |
| `terminology-profile` | domain binding or termbase owner | admitted entry and Human receipt when required |
| `provider-routing` | `.runtime-env/` plus consumer policy | exact profile and execution receipt |
| `acceptance-policy` | `.arena/`, proof and admission controller | checker result on exact subject |
| `privacy-policy` | domain binding/runtime policy | classification, lane and approval receipt |
| `delivery-policy` | `docs/git/` and typed controller | exact head, required checks and operation receipt |

A port can remain `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, or `SKIPPED_BY_POLICY`. A prose fallback cannot convert those states to `PASS`.

## 7. Constraint monotonicity

```text
BettorConstraints       ⊇ SharedCoreConstraints
BettorRequiredEvidence  ⊇ SharedRequiredEvidence
BettorAllowedEffects    ⊆ SharedAllowedEffects
BettorAuthority         ⊆ SharedMaximumAuthority
```

Bettor may:

```text
add or tighten domain invariants
narrow filesystem/network/provider effects
add negative controls and evidence lanes
require a Human or trusted-operator receipt
select an admitted provider/runtime profile
define Bettor terminology and module ownership
```

Bettor must not:

```text
weaken a shared hard gate
delete a shared negative control
treat fixture PASS as live/production PASS
treat provider health as privacy or correctness admission
expand merge/release/rollback authority
use a mutable branch as an immutable binding
```

## 8. State Machine

```text
CLASSIFY_BETTOR_TASK
→ LOAD_NEAREST_README
→ LOAD_DOMAIN_DECOUPLING_WHEN_TRIGGERED
→ RESOLVE_SHARED_REQUIREMENTS
→ RESOLVE_EXACT_BINDING
→ SELECT_BETTOR_MODULES
→ VALIDATE_MONOTONICITY_AND_EFFECTS
→ EXECUTE_PUBLIC_PORT
→ RUN_BETTOR_PROOF_AND_CONTROLS
→ EMIT_BETTOR_RECEIPT
→ CLASSIFY_FINDING
    ├── BETTOR_SPECIFIC → KEEP_LOCAL
    └── GENERIC_METHOD  → PROPOSE_UPSTREAM
```

Stop states:

```text
BLOCKED_MISSING_BINDING
BLOCKED_AMBIGUOUS_MODULE
BLOCKED_POLICY
BLOCKED_STALE_SUBJECT
HUMAN_ADMIT_REQUIRED
FAIL
```

## 9. Data flow

```text
user task / issue / source proposal
→ root Agent route
→ docs/INDEX topic selection
→ nearest module README
→ exact shared binding
→ shared procedure
→ Bettor domain adapter/module
→ runtime/public port
→ deterministic + semantic + Human lanes as required
→ consumer receipt
→ completion or handoff
```

Current queue, PR, provider and runtime state stays in existing machine routes. This document remains stable when one task or branch changes.

## 10. Module interaction boundary

One module may consume another module only through:

```text
public capability
typed packet
artifact reference
named exit
receipt reference
```

Forbidden:

```text
relative import of another module's private script
reading another module's run-temp directory
calling another module's private flag
sharing a mutable provider session as state authority
```

## 11. Generic-learning upstream protocol

```text
Bettor finding
→ verify against Bettor source/tests/runtime
→ classify domain-specific or reusable
→ domain-specific: retain in Bettor module and tests
→ reusable: open shared-method proposal with controls
→ shared admission creates a new immutable subject
→ Bettor explicitly updates requirements/binding
```

No automatic writeback from a Bettor run into shared core is permitted.

## 12. Documentation and context boundary

```text
AGENTS.md
  conditional routing, stop conditions, completion packet

ARCHITECTURE.md
  global stable placement and authority

DOMAIN_DECOUPLING.md
  stable core/port/module/adapter laws

CONTEXT.md
  mutable current handoff and selected subjects

nearest README.md
  local owner, State Machine, DAG, data flow, evidence ceiling

machine contract / receipt
  exact executable authority
```

A bounded-context `CONTEXT.md` is added only when that directory has distinct mutable context. It is not copied into Skill directories.

## 13. Evidence boundary

This document proves only that the consumer ownership and route are declared. It does not prove:

```text
the shared binding is currently fresh
a provider or model ran
a private endpoint is approved
a production termbase exists
a Git Town operation ran
a PR merged
a release or rollback occurred
```

Read the exact machine subject and receipt before making those claims.
