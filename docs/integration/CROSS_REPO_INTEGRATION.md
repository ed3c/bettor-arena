# Cross-repository integration

## Four repository roles

| Repository | Plane | Canonical ownership |
|---|---|---|
| `skills-shared` | Instruction / Method | portable `SKILL.md`, generic references/modules, eval and prompt lineage |
| `runtime-env` | Runtime Contract | secret-free variables, modules, profiles, workloads, policies and consumer projections |
| `bettor-arena` | Integration / Acceptance | composition, ownership, Context Capsules, public ports, proof/control/mutation, external-release acceptance |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | product modules, provider adapters, provider/product state machines and domain canaries |

No arrow is a mutable sibling import. Cross-repository identity is an exact commit/tree/release manifest plus binding, digest and receipt.

## Standard release flow

```text
skills-shared immutable procedure
+ runtime-env immutable secret-free runtime contract
        ↓
Bettor requirements-filtered Skill/runtime binding
        ↓
module composition requirement
        ↓
deterministic lock + Context Capsules + proof subjects
        ↓
loopctl / default-deny MCP / bootstrap release
        ↓
Agent Shield domain/provider canaries
        ↓
Bettor external-release acceptance
        ↓
Human promotion or rollback
```

## PDF architecture allocation

The attached **LLM 泛化：模型權重與 Harness** PDF is a source proposal. Its components should be allocated without creating overlapping authorities:

| PDF component | Canonical repository owner | Current state |
|---|---|---|
| Knowledge compiler, portable Skill and prompt evolution | `skills-shared` | supporting methods exist; PDF-specific compiler release not proven here |
| Runtime variables/profiles/workloads/provider policies | `runtime-env` | secret-free contract plane implemented |
| LoopX task-state kernel, composition, public port, proof, worker gateway, HITL acceptance | `bettor-arena` | supporting control plane implemented; LoopX kernel/HITL absent |
| Product ingest, sandbox providers, code graph product view, observability UI | `agent-shield-monorepo` | product-specific mechanisms/canaries remain separately evidenced |
| Shared worker host compatibility | `skills-shared` procedure + Bettor binding/runtime | contracts implemented; live six-host matrix not exercised |
| Provider candidates | Agent Shield runtime + Bettor acceptance | Serena/GrepAI live not exercised; graph/memory runtime not implemented |

The full audit is
[`../architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](../architecture/PDF_HARNESS_INTEGRATION_AUDIT.md).

## State-machine boundaries

```text
skills-shared
  CANDIDATE PROCEDURE
  → eval / mutation / holdout
  → immutable Skill release

runtime-env
  DECLARATION
  → profile/workload resolution
  → secret-free projection
  → offline consumer verification
  → live canary

bettor-arena
  MODULE REQUIREMENTS
  → composition lock / Context Capsule
  → public execution
  → proof/control/mutation
  → external acceptance
  → Human Admit

agent-shield-monorepo
  DOMAIN REQUIREMENT
  → provider/product state machine
  → sandbox/runtime execution
  → domain receipt
  → immutable module release
```

The proposed LoopX extension belongs in Bettor, but its runtime/provider implementations may be consumed from `runtime-env` and Agent Shield:

```text
strategy graph proposes
worker/provider executes
hard gates observe
Bettor LoopX reducer commits
Human admits
```

## Exact documentation convergence

Parent: `bettor-arena#35`.

Merged independent siblings:

```text
bettor-arena#37              1f94d3d77992a1396959a15b2ada7836c07bf300
skills-shared#85             e3b327ad49c088f1962c33167ecd5ac9d28125fb
runtime-env#30               4a333ccf106ef60bc6942b922b7f5efffb3876f5
agent-shield-monorepo#78     1af04c1ef5cb68eab198987feba008c93d3ec22f
```

`bettor-arena#38` is now the convergence owner for exact route indexing, directory/state-machine mapping, PDF integration audit and cold-start status. Documentation convergence does not prove live host/provider behavior.

## Contract flow requirements

Every cross-repository binding records:

```text
source repository
commit and tree
release or manifest ID
selected components/capabilities
content digest
consumer requirement digest
runtime policy digest
known non-success states
rollback subject
Human Admit
```

Forbidden:

```text
mutable main as release identity
sibling checkout import at runtime
cross-repository symlink as production binding
secret/session/browser profile in Git or receipt
another repository's PASS copied into this subject
```

## Cloud/local separation

```text
portable plane:
  source commit/tree
  Skill/runtime/module manifests
  schemas and policies
  content-addressed artifacts
  redacted receipts

host-only plane:
  secret values
  Keychain/OAuth material
  signed-in browser/device sessions
  local sockets and absolute paths
  provider credentials
```

Local PASS does not proxy cloud PASS. A same-workload canary must pin both environments, exact artifacts, policy and cleanup.

Current state: runtime contracts exist; equivalent local/cloud execution is `NOT_EXERCISED`.

## Knowledge and memory flow

```text
source / notes / code / logs
→ skills-shared knowledge procedure
→ Bettor source-bound request / OpenWiki / Code Truth projection
→ provider candidate query
→ current source/test/runtime readback
→ evidence-bound card/decision proposal
→ Human Admit where durable state changes
```

Mem0, vector indexes, graph databases and OpenWiki are projections. Git/source/receipts/current ADR and the eventual LoopX event ledger remain higher authority.

## Stack traceability

Read [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md) before changing cross-repository branches or convergence artifacts.

No Bettor `.git-town.toml` or `.git-town` is currently tracked. The molecular sibling/child/terminal/convergence vocabulary is policy, not Git Town runtime evidence.

## Source boundary

PDF diagrams, Gemini prose and source examples do not establish:

```text
provider availability
performance or RAM footprint
security/isolation
license suitability
cloud/local equivalence
model quality
live worker compatibility
Human promotion
```

These require independent primary-source review plus exact runtime receipts.

## Validation

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
```
