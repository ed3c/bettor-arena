# Four-repository modular integration — bettor acceptance view

## Ownership planes

| Repository | Plane | Owns | Must not own |
|---|---|---|---|
| `skills-shared` | Instruction / Method | portable procedural Skills, generic contracts, Skill eval/evolution truth | product/provider state, consumer branches/secrets |
| `runtime-env` | Runtime Contract | secret-free variables/modules/profiles/workloads/policies and consumer bindings | secret values, generic shell, product semantics |
| `bettor-arena` | Integration / Acceptance | module composition, proof/control/mutation, Context Capsules, stateless MCP, bootstrap, origins, external-release acceptance | domain product implementation, hidden live checkout dependencies |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | product modules, provider adapters, product state machines, exact domain canaries | canonical shared Skill bodies or generic runtime catalog |

## Contract data flow

```text
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
Agent Shield remote-consumer or embedded-module initialization
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

## Channel separation

```text
Skill symlink / editable checkout = local development channel
immutable commit/tree/release + binding/lock = reproducible channel
loopctl / stateless MCP = public consumption channel
```

No mutable sibling checkout, secret file, browser profile, device session, or owner temp state becomes a release dependency. Forgejo authoring and GitHub distribution equivalence require exact receipts.

## Skill procedural/domain separation

Shared `SKILL.md` contains generalized workflow/method/laws. Shared `references/` contains reusable contracts. Shared `modules/` contains domain examples loaded on demand. Bettor repo-owned bindings select and retarget the procedure without copying the canonical core.

## Source boundary

The attached architecture PDF proposes E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, licensing, cost, performance, and recovery. Those are research inputs. Admission requires independent verification, implementation, evals, canaries, receipts, and Human Admit.
