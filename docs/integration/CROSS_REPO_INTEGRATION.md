# Four-repository modular integration — bettor acceptance view

## Ownership planes

| Repository | Plane | Owns | Must not own |
|---|---|---|---|
| `skills-shared` | Instruction / Method | portable procedural Skills, generic contracts, Skill eval/evolution truth | product/provider state, consumer branches/secrets |
| `runtime-env` | Runtime Contract | secret-free variables/modules/profiles/workloads/policies and consumer bindings | secret values, generic shell, product semantics |
| `bettor-arena` | Integration / Acceptance | module composition, proof/control/mutation, Context Capsules, stateless MCP, bootstrap, origins, external-release acceptance | domain product implementation, hidden live checkout dependencies |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | product modules, provider adapters, product State Machines, exact domain canaries | canonical shared Skill bodies or generic runtime catalog |

## Contract data flow

```text
PDF / product requirement
        |
        +--> SOURCE_PROPOSAL classification and plane owner
        |
skills-shared immutable Skill release
        |
        +--> .agents requirements/binding
        |
runtime-env requirements → secret-free binding/workload/policy
        |                         |
        +------------+------------+
                     v
bettor .arena module/composition locks
+ module proof subjects
+ Context Capsules
+ CLI/MCP/bootstrap release
                     |
                     v
Agent Shield provider/product implementation
+ remote-consumer or embedded-module initialization
                     |
                     v
Claude/Codex/origin/browser/provider/product canary receipts
                     |
                     v
bettor external-release acceptance
                     |
                     v
Human promotion or rollback
```

## Freshness and evidence separation

```text
runtime declaration
  ≠ fresh Bettor projection
  ≠ Bettor proof PASS
  ≠ Agent Shield provider canary
  ≠ product convergence
  ≠ production promotion
```

The checked Bettor runtime binding currently pins `runtime-env` commit `142e1ed278bf18f9c5c09186e28db16b623cdaee`, tree `1bd5c97e6f5519182d151055cf5f83fccb7ff5fa`. The implementation baseline evaluated by the PDF audit is `4a333ccf106ef60bc6942b922b7f5efffb3876f5`, tree `68cda3d0ce7f1df26475a5d7322968194e794046`. The relation is `STALE_SOURCE_PIN` until an explicit accept-pin or reviewed sync decision is recorded.

## Channel separation

```text
Skill symlink / editable checkout = local development channel
immutable commit/tree/release + binding/lock = reproducible channel
loopctl / stateless MCP = public consumption channel
```

No mutable sibling checkout, secret file, browser profile, device session or owner temp state becomes a release dependency. Forgejo authoring and GitHub distribution equivalence require exact receipts.

## Skill procedural/domain separation

Shared `SKILL.md` contains generalized workflow/method/laws. Shared `references/` contains reusable contracts. Shared `modules/` contains domain examples loaded on demand. Bettor repo-owned bindings select and retarget the procedure without copying the canonical core.

## PDF architecture boundary

The architecture in `科技巨頭開源授權與AI框架v2.pdf` proposes the Agent Shield domain-product tree: local/cloud runtime, mobile, hardware, wallet, security, ledger, workflow and settlement. Bettor must not absorb those private implementations. It integrates them only through immutable module/runtime/Skill contracts and subject-bound acceptance.

Current high-level state:

```text
Runtime Contract plane:                 implemented
Bettor Integration / Acceptance plane: implemented for named deterministic contracts
Bettor runtime binding freshness:       STALE_SOURCE_PIN
Agent Shield provider-neutral SPI:      implemented
native provider/product/security:       incomplete or not exercised
reference-consumer live acceptance:     not exercised
product-complete release:               absent
```

Read [`AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md`](AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md) for the directory/State Machine matrix, exact status and Agent Shield Git Town Phase 3–6 Stack. Read [`AGENTS.md`](AGENTS.md) before changing this integration route.

## Git Town boundary

`bettor-arena` has no repository-owned `.git-town.toml`. The domain-product Stack belongs to Agent Shield. Git Town synchronizes branch ancestry only; exact GitHub base/head, current checks, receipts, convergence ownership and Human review remain authoritative.