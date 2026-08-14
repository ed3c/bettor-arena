# Agent Shield PDF modular-integration audit

> Audit date: 2026-08-14  
> Source: `科技巨頭開源授權與AI框架v2.pdf`, pages 25–41  
> Repositories: `runtime-env`, `bettor-arena`, `agent-shield-monorepo`, `skills-shared`  
> Verdict: **CONTRACT_INTEGRATED / PRODUCT_INCOMPLETE / LIVE_ACCEPTANCE_NOT_EXERCISED**

## 1. Scope and ownership correction

The PDF's final directory target is `agent-shield-monorepo/`, including contracts, services, apps, shared packages, local/cloud runtime and repair scripts. It is not a target directory tree for `bettor-arena`.

The repository roles are:

| Plane | Repository | Authority |
|---|---|---|
| Instruction / Method | `skills-shared` | portable Skill procedure and eval contracts |
| Runtime Contract | `runtime-env` | secret-free variables, modules, profiles, workloads and carrier policies |
| Integration / Acceptance | `bettor-arena` | module closure, proof/control/mutation, Context Capsules, stateless MCP, release acceptance |
| Domain Product / Reference Consumer | `agent-shield-monorepo` | PDF product/provider modules, domain State Machines and canaries |

The correct modular integration is therefore:

```text
PDF requirement
→ repository decision and owner assignment
→ shared Skill/runtime contracts
→ Bettor immutable composition and acceptance subject
→ Agent Shield product/provider implementation
→ domain canaries
→ Bettor external-release acceptance
→ Human promotion or rollback
```

Copying the PDF's directories into Bettor would violate the plane boundary rather than prove integration.

## 2. Exact runtime projection finding

Bettor currently checks the following source into `.runtime-env/bindings/bettor-arena-local.json`:

```text
source repository: https://github.com/ed3c/runtime-env
source commit:     142e1ed278bf18f9c5c09186e28db16b623cdaee
source tree:       1bd5c97e6f5519182d151055cf5f83fccb7ff5fa
binding digest:    805a069efdad08342f79f3eee74f8f122de445f2f4e67bf46364353faa80f745
```

The runtime contract implementation baseline evaluated by this audit is:

```text
commit: 4a333ccf106ef60bc6942b922b7f5efffb3876f5
 tree:  68cda3d0ce7f1df26475a5d7322968194e794046
```

Later `runtime-env/main` commits may update audit documentation without changing contract semantics. The checked Bettor binding is still older than the evaluated contract baseline, so its audit state is `STALE_SOURCE_PIN` until one of these decisions is recorded:

```text
ACCEPT_EXISTING_PIN with rationale and verifier
or
DRY_RUN_SYNC → REVIEW → APPLY_EXPLICIT → STAGED_VERIFY
```

No Agent may silently run `--apply` because upstream `main` advanced.

## 3. Directory → State Machine ownership in Bettor

| Bettor path | State Machine / role | Input | Output / evidence | Does not own |
|---|---|---|---|---|
| [`.agents/`](../../.agents/README.md) | Skill requirement/binding closure | desired Skill names and immutable sources | resolved bindings/module-set | product code or secrets |
| [`.runtime-env/`](../../.runtime-env/README.md) | runtime consumer projection | requirements + pinned runtime source | binding/workload/policies/example | runtime provider implementation |
| [`.arena/modules/`](../../.arena/modules/README.md) | `PROPOSED → ADMITTED → VERIFIED → RELEASED` | module manifest and public seam | module identity, capability and owner | sibling private implementation |
| [`.arena/compositions/`](../../.arena/compositions/README.md) | Macro requirement selection | desired modules and components | composition requirements | proof or promotion by itself |
| [`.arena/locks/`](../../.arena/locks/README.md) | immutable closure result | resolved requirements | deterministic composition lock | mutable branch identity |
| [`.arena/contexts/`](../../.arena/contexts/README.md) | Context Capsule | selected module/loop and host projection | bounded passive context | credentials or arbitrary prompt flattening |
| [`loopctl/`](../../loopctl/README.md) | public CLI / stateless MCP seam | typed command/request | typed result, exit and artifact refs | private flags or generic shell |
| [`proof_workflow/`](../../proof_workflow/README.md) | proof/control/mutation | exact immutable subject | falsifiable receipt matrix | Human Admit |
| [`data/module-proof/`](../../data/module-proof/README.md) | module subject and release evidence | proof/control outputs | checked subject-bound receipt | hand-written success claims |
| [`data/mcp/`](../../data/mcp/README.md) | MCP exposure snapshot | canonical contract + policy | exposure digest | provider health |
| [`data/origins/`](../../data/origins/README.md) | GitHub/Forgejo observation | exact origin subject | origin receipt/equivalence candidate | logical equivalence by prose |
| [`data/browser/`](../../data/browser/README.md) | browser transport/provider observation | exact browser subject | status/receipt | signed-in session portability |
| [`scripts/`](../../scripts/README.md) | deterministic reducers and gates | admitted files/arguments | checked transitions | provider/product authority |
| [`docs/`](../README.md) | routing and explanation | repository decisions and exact evidence | human/Agent navigation | machine status or receipt authority |

## 4. Cross-repository State Machines

### Runtime binding

```text
REQUIREMENTS_RECEIVED
→ SOURCE_COMMIT_AND_TREE_IDENTIFIED
→ CLOSURE_RESOLVED
→ DRY_RUN_PLAN
→ APPLY_EXPLICIT
→ PROJECTION_WRITTEN
→ STAGED_OFFLINE_VERIFY
→ CONSUMER_CANARY
→ HUMAN PROMOTION / ROLLBACK
```

### Bettor Macro / acceptance

```text
MODULE REQUIREMENTS
→ DEPENDENCY/CONFLICT RESOLUTION
→ SKILL/RUNTIME/HOST PROJECTIONS
→ PROOF MATRIX
→ HUMAN ADMIT
→ COMPOSITION LOCK
→ IMMUTABLE RELEASE
→ EXTERNAL CONSUMER ACCEPTANCE
→ PROMOTION OR ROLLBACK
```

### Agent Shield product/provider

```text
FOUNDATION CONTRACT
→ TERMINAL PROVIDER/PRODUCT LEAVES
→ PUBLIC-SEAM POSITIVE + DISAGREEMENT CONTROLS
→ PHASE CONVERGENCE
→ BETTOR REFERENCE-CONSUMER BINDING
→ CLI/MCP + CARRIER + ORIGIN CANARIES
→ REFERENCE COMPOSITION RELEASE
```

These are separate evidence transitions:

```text
runtime declaration ≠ fresh Bettor projection
fresh projection ≠ Bettor proof PASS
Bettor proof PASS ≠ Agent Shield provider canary
provider canary ≠ product convergence
product convergence ≠ Human production promotion
```

## 5. PDF capability status matrix

| PDF capability | Canonical implementation owner | Current exact evidence | State |
|---|---|---|---|
| Runtime request/provider/receipt contract | Agent Shield issue #38 | PR #79 merged at `7d28a8cada03726b2b8966d9a229500f285d1b2b` | `IMPLEMENTED` for provider-neutral SPI only |
| Disposable local runtime baseline | Agent Shield status ledger | `runtime-local-disposable: PASS` | `PASS` for exact baseline subject |
| Apple Container | issue #39 | `runtime-apple-container: NOT_EXERCISED` | `NOT_EXERCISED` |
| E2B / Firecracker | issue #40 | `runtime-e2b: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| OpenShell / tmux | issues #41–#42 | `runtime-openshell-tmux: NOT_EXERCISED` | `NOT_EXERCISED` |
| Hybrid immutable exchange / repair | issue #43 | no promoted provider receipt | `NOT_IMPLEMENTED_OR_NOT_EXERCISED` |
| Expo mobile | issue #48 | `product-expo: NOT_EXERCISED` | `NOT_EXERCISED` |
| In-App action bridge | issue #49, true child of #48 | no admitted product receipt | `NOT_IMPLEMENTED_OR_NOT_EXERCISED` |
| Maestro / WDA / scrcpy | issues #50–#52 | `product-maestro-wda-scrcpy: NOT_EXERCISED` | `NOT_EXERCISED` |
| OPA / durable workflow / OpenBao / verified ledger | issues #55–#58 | umbrella status `security-native-providers: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| Secure Enclave / NFC / MPC-TSS | issues #59–#61 | umbrella status `security-native-providers: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| smart account / testnet settlement | issues #62–#63 | umbrella status `security-native-providers: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| PDF ingest | Agent Shield document-ingest module | `document-ingest-pdf: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| Bettor reference consumer | Agent Shield Phase 6 | `bettor-consumer: NOT_EXERCISED` | `NOT_EXERCISED` |
| Claude / Codex live carrier | Phase 6 + environment | both status entries `NOT_EXERCISED` | `NOT_EXERCISED` |
| Forgejo / GitHub equivalence | Phase 6 | no same-subject equivalence receipt | `NOT_EXERCISED` |
| signed-in browser | environment + adapter | `signed-in-browser: NOT_EXERCISED` | `NOT_EXERCISED` |
| product-complete release | issue #75 | no aggregate release subject | `ABSENT` |

The PDF's prose claim that all MVPs are already fully integrated cannot override this matrix.

## 6. Git Town molecular implementation Stack

`bettor-arena` has no repository-owned `.git-town.toml`. The canonical Git Town policy and product Stack live in `agent-shield-monorepo`.

### Phase 3 — Runtime fabric

```text
main
└─ #38 runtime SPI foundation                   MERGED / PR #79
   ├─ #39 Apple Container                       terminal provider leaf
   ├─ #40 E2B runtime                           terminal provider leaf
   ├─ #41 OpenShell policy                      terminal provider leaf
   ├─ #42 tmux / PTY                            terminal provider leaf
   └─ #43 hybrid exchange / repair              terminal provider leaf
main after #38–#43
└─ #44 runtime convergence                      convergence leaf
```

### Phase 4 — Product and mobile

```text
main
└─ #45 product contracts
   ├─ #46 dashboard GenUI
   ├─ #47 terminal projection
   ├─ #48 Expo mobile
   │  └─ #49 In-App action bridge               true child
   ├─ #50 Maestro MCP
   ├─ #51 WDA iOS projection
   └─ #52 scrcpy Android projection
main after #45–#52
└─ #53 product convergence
```

### Phase 5 — Security, hardware and settlement

```text
main
└─ #54 security contracts
   ├─ #55 OPA policy
   ├─ #56 durable workflow
   ├─ #57 OpenBao broker
   ├─ #58 verified ledger
   ├─ #59 Secure Enclave
   ├─ #60 CoreNFC challenge
   ├─ #61 MPC-TSS provider
   └─ #62 smart-account contracts
      └─ #63 testnet submission                 true child
main after #54–#63
└─ #64 security convergence
```

### Phase 6 — Bettor reference consumer

```text
main
└─ #65 consumer contracts
   └─ #66 immutable module closure
      ├─ #67 Skill binding
      └─ #68 runtime binding
serialized selected closure
└─ #69 CLI / MCP parity
   ├─ #70 Claude canary
   ├─ #71 Codex canary
   ├─ #72 GitHub origin
   └─ #73 Forgejo origin
main after #72 + #73
└─ #74 origin equivalence
main after #65–#74
└─ #75 reference composition release
```

Rules:

- sibling leaves own path-disjoint providers/products from one admitted parent;
- a true child consumes unmerged parent bytes;
- a terminal leaf owns one reviewable implementation and its evidence;
- a convergence leaf alone owns shared registries, status, release manifests and aggregate promotion;
- Git Town exit `0` proves branch movement only;
- GitHub base/head/merge metadata, exact commits, exact-head checks and Human review remain publication authority.

## 7. Documentation convergence status

The four route-binding PRs are merged:

```text
runtime-env #30             4a333ccf106ef60bc6942b922b7f5efffb3876f5
skills-shared #85           e3b327ad49c088f1962c33167ecd5ac9d28125fb
agent-shield-monorepo #78   1af04c1ef5cb68eab198987feba008c93d3ec22f
bettor-arena #37            1f94d3d77992a1396959a15b2ada7836c07bf300
```

Bettor issue #38 is therefore no longer blocked by those four PRs. Its fresh Claude/Codex cold-start and exact-route audit remain `NOT_EXERCISED` until physically run.

This audit PR is a true documentation child of Bettor PR #57 because it consumes #57's unmerged root README/AGENTS directory-State-Machine mapping and extends the same files for a second PDF architecture. It must be rebased or retargeted after #57 merges.

## 8. Required next transitions

### Runtime projection

1. Run `runtime-env sync` dry-run against an exact runtime source.
2. Compare module/profile/workload/policy closure and generated files.
3. Record `ACCEPT_EXISTING_PIN` or approve `--apply`.
4. Run Bettor staged offline verification without sibling dependency.
5. Update source commit/tree/digests and rollback subject.

### Product implementation

1. Complete Phase 3 provider leaves and #44 convergence.
2. Complete Phase 4 product/mobile leaves and #53 convergence.
3. Complete Phase 5 security/settlement leaves and #64 convergence.
4. Complete Phase 6 immutable Skill/runtime binding, parity, carrier and origin canaries.
5. Promote only through #75 with aggregate evidence, Human Admit and rollback.

### Cold-start and route verification

1. Open fresh Claude Code and Codex CLI sessions from each repository root.
2. Verify an Agent reaches owner, machine contract, current status, Stack leaf and evidence subject without chat history.
3. Record disagreements rather than silently reconciling them.
4. Verify no Markdown duplicates machine authority.

## 9. Security and source-claim boundary

The PDF says in one section that absolute security does not exist, but elsewhere assigns unsupported percentages and “100% immune” labels. Bettor and Agent Shield must instead record:

```text
threat model
→ preventive/detective controls
→ disagreement and mutation tests
→ exact canary subject
→ cleanup/residue
→ residual risk
→ Human decision
```

Permissive direct licensing does not prove transitive licensing, service terms, security, product fitness or zero legal risk. Timestamp-based `newest`/`prefer-cloud`/`prefer-beta` code repair is not admitted as source authority; Git ancestry, immutable bases, one-writer leases, content-bound patches and review remain required.

## 10. Final verdict

```text
Skill/runtime contract connection:          PRESENT
Bettor module/acceptance mechanisms:        PRESENT
Bettor runtime projection freshness:        STALE_SOURCE_PIN
Agent Shield runtime SPI foundation:        PRESENT
PDF native runtime providers:               INCOMPLETE
PDF product/mobile modules:                 INCOMPLETE
PDF security/settlement modules:            INCOMPLETE
Bettor reference-consumer acceptance:       NOT_EXERCISED
Claude/Codex/origin/provider live evidence: NOT_EXERCISED or ABSENT
Product-complete release:                   ABSENT
```

**Bettor is modularly integrated with the runtime and acceptance architecture, but the PDF's end-to-end product architecture is not yet integrated.**