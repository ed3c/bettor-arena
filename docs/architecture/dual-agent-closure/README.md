# Dual-Agent source-problem closure monitor

This directory binds the uploaded five-page **`双 Agent 架构：云端本地协同`** source to current repository ownership, State Machines, dependency/process DAGs, molecular implementation issues, evidence ceilings, and final release authority.

It is a **documentation and audit projection**. It does not execute a local Agent, cloud Agent, message transport, durable workflow, sandbox, API, browser, external effect, Human decision, release, or rollback.

The parent monitor is [`../tech-lead-shadow-monitor/`](../tech-lead-shadow-monitor/). Read its [`AGENTS.md`](../tech-lead-shadow-monitor/AGENTS.md) and [`README.md`](../tech-lead-shadow-monitor/README.md) first. This route specializes that monitor for source `DA-SRC-001`; it does not create a second Local Handoff queue or a second task-state authority.

## Current closure verdict

```text
source problem denominator                  BOUND
cross-repository authority map              BOUND
unfinished work represented by Issues       BOUND
portable Dual-Agent method                  NOT_IMPLEMENTED / issue open
exact offload packet/receipt contracts       NOT_IMPLEMENTED / issue open
durable offline/reconnect transport          NOT_IMPLEMENTED / issue open
workload identity/policy/secret binding      NOT_IMPLEMENTED / issue open
durable offload workflow                     NOT_IMPLEMENTED / issue open
idempotent external-effect admission         NOT_IMPLEMENTED / issue open
API-first + browser-fallback adapter          NOT_IMPLEMENTED / issue open
gVisor cloud isolation adapter/live canary   NOT_IMPLEMENTED / issue open
physical local → cloud → local user canary   NOT_EXERCISED
independent end-to-end evidence closure       NOT_IMPLEMENTED / issue open
explicit licenses for four mandatory repos   HUMAN_ADMIT_REQUIRED
content-addressed selected release            NOT_RELEASED
production operation and rollback             NOT_EXERCISED
```

The correct conclusion is:

> The repositories contain strong LoopX, module, proof, Runtime Fabric, provider-boundary, Skill-governance, and evidence mechanisms. The uploaded Dual-Agent problem is **not closed** because no one exact release subject has yet proven offline local submission, reconnect, cloud execution, structured result return, restart reconstruction, duplicate-effect refusal, user-visible success, explicit commercial/open-source license closure, Human admission, and rollback.

An issue being open means the gap is owned. It does not mean the mechanism is implemented. An implementation merged to `main` means bytes are reachable. It does not mean the physical or user problem is closed.

## Source problem denominator

Source ID: `DA-SRC-001`.

| Problem ID | Source locator | Source-derived problem | Repository interpretation | Current evidence stage | Owning issues |
|---|---|---|---|---|---|
| `DA-P01` | PDF page 1, source lines 5–17 | An always-on cloud Agent continues long-running monitoring and automation while the local computer is off | Requires a durable cloud execution lane, exact provider/runtime identity, isolation, limits, cleanup, restart and current-provider evidence | `OWNER_AND_CONTRACT_BOUND`; selected live subject `NOT_EXERCISED` | Bettor #66/#183/#184/#186; Agent Shield #3/#40/#95/#147 |
| `DA-P02` | PDF page 1, source lines 12–17 and table | A local Agent owns local code, files, private data and direct device access | Requires a local sovereign runtime, `LOCAL_ONLY` policy, host-owned credentials/sessions, physical host/device evidence and a controlled bridge | mechanisms exist in parts; end-to-end selected lane `NOT_EXERCISED` | runtime-env #57/#58/#59; Bettor #161/#183/#186; Agent Shield device/live issues |
| `DA-P03` | PDF page 2, source lines 53–73 | Long work is offloaded from local to cloud and structured results return after reconnect | Requires durable local outbox/inbox, at-least-once transport, workflow history, idempotency, stale-result refusal, artifact return and restart reconstruction | `OWNER_AND_CONTRACT_BOUND`; mechanism `NOT_IMPLEMENTED` | skills-shared #359; runtime-env #57/#58/#59; Bettor #183/#184/#185/#186 |
| `DA-P04` | PDF page 3, source lines 85–107 | A structured API should replace fragile UI automation when a suitable API exists | Requires exact provider/schema/auth/terms admission, closed endpoint/method surface, error semantics, data policy and effect readback | `OWNER_AND_CONTRACT_BOUND`; adapter `NOT_IMPLEMENTED` | Agent Shield #144; Bettor #185/#186 |
| `DA-P05` | PDF pages 2–3, source lines 57–60 and 85–107 | Browser automation remains necessary where APIs are absent, but is more fragile | Requires exact browser/tool/profile identity, policy-gated fallback, structured DOM/accessibility/network assertions, bounded artifacts and cleanup | `OWNER_AND_CONTRACT_BOUND`; adapter/live route `NOT_IMPLEMENTED` or `NOT_EXERCISED` | Agent Shield #139/#144; Bettor #186 |
| `DA-P06` | PDF pages 4–5, source lines 115–156 | Local and cloud Agents share organizational memory and collaborate asynchronously | Shared docs/memory may provide context and collaboration, but workflow state, effects, Gates, Human decisions and release remain separate authorities | several memory/projection mechanisms `IMPLEMENTED`; selected end-to-end authority closure `ABSENT` | Bettor #63/#67/#103/#105/#183/#186; final #68 |
| `DA-P07` | PDF page 2, source lines 56–73 | Users should not pay a large DevOps/configuration/recovery tax | Requires one reproducible install/admit/run/reconnect/inspect/recover/rollback path and a user-outcome canary; architecture prose cannot prove usability | no selected user-outcome receipt | Bettor #186; final #68; FDE deployment profiles |
| `DA-P08` | Derived commercial requirement attached to the user request | Mandatory repositories and dependencies must have explicit commercially usable rights and release notices | Requires owner-selected exact license bytes, notices, contributor provenance, transitive dependency/source review and content-addressed release | four mandatory repositories `HUMAN_ADMIT_REQUIRED`; release `NOT_RELEASED` | skills-shared #360; Bettor #182; Agent Shield #143; FDE #97; final #68 |

### Unsupported source claims

The source also contains statements about hardware configuration, API catalog size/popularity, speed, token cost, automation reliability, unified graphs, CRDT implementation, permission management, and very high success rates. These statements are not current repository facts. They may become research questions or provider admissions only after an exact current source, implementation subject, measurement contract, controls, and receipt are bound.

## Closure ladder

Every row in the denominator follows this independent ladder:

```text
SOURCE_PROPOSAL
→ OWNER_AND_CONTRACT_BOUND
→ MECHANISM_IMPLEMENTED
→ DETERMINISTICLY_VERIFIED
→ LIVE_OR_PHYSICAL_EXECUTED
→ USER_OUTCOME_VERIFIED
→ HUMAN_ADMITTED
→ RELEASED
→ OPERATED_WITH_ROLLBACK
```

Examples of illegal promotion:

```text
issue created                  ≠ mechanism implemented
schema valid                   ≠ transport/provider live
transport ack                  ≠ task result
workflow completed             ≠ Gate PASS
Gate PASS                      ≠ external effect committed
artifact digest listed         ≠ artifact bytes read back
backend result                 ≠ local/user result reconstructed
provider canary                ≠ production availability
license candidate              ≠ owner/legal admission
all terminal PRs merged        ≠ selected release
release manifest rendered      ≠ production rollout
```

## Cross-repository directory → State Machine → DAG → data flow

| Repository / directory | State Machine owner | Input | Output / next owner | Process-DAG dependencies | Evidence ceiling now |
|---|---|---|---|---|---|
| `ed3c/skills-shared/skills/agentic-tech-lead-orchestration/` or the exact owner selected by #359 | portable Dual-Agent method | source problem, exact task subject, data/effect class, authority and budget | provider-neutral procedure, laws, packet requirements, stop conditions → runtime-env/consumers | existing #249/#332/#358; new #359 | portable contract only; `NOT_IMPLEMENTED` |
| `ed3c/skills-shared` release/legal surfaces | licensing and Skill-release governance | owner rights decision, source/dependency inventory | exact license/notices and admitted Skill release → consumers | #360 plus existing release gates | `HUMAN_ADMIT_REQUIRED` |
| `ed3c/runtime-env/contracts/dual-agent/` proposed by #57 | offload contract plane | portable method + exact source/runtime/policy subjects | `OffloadJob`, capability, effect, artifact and receipt schemas → transport/Bettor/Agent Shield | skills-shared #359 | `NOT_IMPLEMENTED` |
| `ed3c/runtime-env` proposed transport surfaces | host transport and durable local projection | validated offload packet, exact NATS/SQLite/runtime profile | outbox/inbox, attempt/ack/result metadata receipts → Bettor workflow/reconciliation | runtime-env #57 and existing #45 | issue #58; `NOT_IMPLEMENTED`, physical canary `NOT_EXERCISED` |
| `ed3c/runtime-env` proposed identity/policy surfaces | runtime admission binding | workload/tenant/audience, policy epoch, capability and opaque secret refs | identity/policy/lease metadata receipt → transport/provider/workflow | runtime-env #57; may consume #58 for live bridge | issue #59; `NOT_IMPLEMENTED` |
| `bettor-arena/loop_wiki/dual-agent-offload-workflow/` proposed | durable workflow adapter and LoopX reducer integration | validated job, delivery events, provider/activity receipts, Human signals | canonical workflow events and task proposals → Gates/reducer/effect ledger | runtime-env #57–#59; existing LoopX #62–#67 | issue #184; `NOT_IMPLEMENTED` |
| `bettor-arena/loop_wiki/dual-agent-effect-ledger/` proposed | external-effect admission | exact effect intent, policy/Human receipt, target precondition, provider observation | reserved/refused/unknown/committed/compensated effect receipt → workflow/user result | #184 and LoopX ledger #63 | issue #185; `NOT_IMPLEMENTED` |
| `ed3c/agent-shield-monorepo/services/runtime-fabric/` | runtime-provider SPI and adapters | closed runtime request, exact image/provider/policy/workload | execution/artifact/cleanup receipt → Bettor Gates/workflow | existing #38 foundation; provider leaves #39–#43/#147; convergence #44 | deterministic mechanisms vary; selected Dual-Agent live lane `NOT_EXERCISED` |
| `ed3c/agent-shield-monorepo/services/research-orchestrator/` proposed API/browser adapters | integration route and observation | typed action, exact API/schema/auth or browser bundle/session policy | structured observation, target readback and cleanup receipt → effect/Gate owners | #144; provider runtime; Bettor #185 | `NOT_IMPLEMENTED` |
| `ed3c/truth-verify-loop` proposed Dual-Agent verifier | independent evidence closure | complete content-bound local/cloud/workflow/effect/artifact/user bundle | `SUPPORTED | REFUTED | CONFLICTED | STALE | UNVERIFIABLE` → Shadow/Human | all exercised lanes; #22 | `NOT_IMPLEMENTED` for this bundle shape |
| `ed3c/fde-agent-platform` | Role Pack / Tenant Overlay composition | admitted domain-neutral capabilities and private tenant policy/mapping | governed tenant specification → deployment/runtime consumers | generic runtime release; license #97 | platform planning exists; Dual-Agent production overlay `NOT_EXERCISED` |
| `bettor-arena/docs/architecture/tech-lead-shadow-monitor/` | parent closure monitor | exact GitHub/local state, source problems, issues, PRs, receipts | canonical audit and Local Handoff route | issue #173 / PR #176 | parent PR `DRAFT`; not merged |
| `bettor-arena/docs/architecture/dual-agent-closure/` | this source-specific projection | parent monitor + PDF problem denominator + current issue graph | specialized directory/DAG/data-flow/Stack index | true child of PR #176; issue #187 | documentation candidate only |
| `bettor-arena/.arena/compositions/`, locks and `data/module-proof/` | final composition/release owner | admitted exact terminal subjects and explicit exclusions | content-addressed release/rollback dossier | final #68 after ordered prerequisites | `BLOCKED_BY_PREDECESSORS`, `NOT_RELEASED` |

## State Machine composition

No component may skip the following logical sequence:

```text
LOCAL INTENT
→ DATA / EFFECT / AUTHORITY CLASSIFICATION
→ EXACT OFFLOAD PACKET
→ RUNTIME / POLICY / IDENTITY BINDING
→ DURABLE LOCAL OUTBOX COMMIT
→ AT-LEAST-ONCE DELIVERY
→ DURABLE WORKFLOW ADMISSION
→ LEASED ISOLATED EXECUTION
→ API-FIRST ROUTE OR POLICY-GATED BROWSER FALLBACK
→ STRUCTURED OBSERVATION + CONTENT-ADDRESSED ARTIFACTS
→ HOST-OWNED GATES + SOURCE/TARGET READBACK
→ IDEMPOTENT EFFECT ADMISSION WHEN APPLICABLE
→ RESULT RECEIPT
→ DURABLE LOCAL INBOX COMMIT
→ RESTART / RECONNECT PROJECTION REBUILD
→ USER RESULT VERIFICATION
→ INDEPENDENT SHADOW / TRUTH VERIFICATION
→ HUMAN ADMIT
→ CONTENT-ADDRESSED RELEASE OR ROLLBACK
```

### Failure and blocked-state composition

At minimum preserve:

```text
ABSENT_RUNTIME
STALE_BINDING
LOCAL_ONLY_REFUSED
IDENTITY_REFUSED
POLICY_REFUSED
TRANSPORT_UNAVAILABLE
DISCONNECTED
DUPLICATE_DELIVERY
ACK_TIMED_OUT
DEADLINE_EXPIRED
CANCELLED
ACTIVITY_FAILED
RESULT_STALE
RESULT_MISMATCH
ARTIFACT_MISSING
GATE_FAILED
EFFECT_DUPLICATE_REFUSED
EFFECT_RESULT_UNKNOWN
COMPENSATING
COMPENSATION_FAILED
FAILED_CLEANUP
UNKNOWN_RESIDUE
USER_RESULT_UNVERIFIED
CONTESTED
HUMAN_ADMIT_REQUIRED
NOT_RELEASED
```

A catch-all `FAILED` or `COMPLETED` projection must not erase these facts.

## Process / evidence DAG

```text
DA-SRC-001 uploaded source
        ↓
skills-shared#359 portable method
        ↓
runtime-env#57 exact offload/receipt contracts
        ├───────────────┬─────────────────┐
        ↓               ↓                 ↓
runtime-env#58     runtime-env#59    licensing siblings
transport/restart  identity/policy   #360 #182 #143 #97
        └───────┬───────┘                 │
                ↓                         │
bettor-arena#184 durable workflow         │
                ├───────────────┐         │
                ↓               ↓         │
bettor-arena#185 effect ledger  existing LoopX/Gates
                └───────┬───────┘
                        ↓
Agent Shield Phase-3 foundation #38
        ├─ existing #39 Apple Container
        ├─ existing #40 E2B / Firecracker-backed provider route
        ├─ existing #41 OpenShell policy
        ├─ existing #42 tmux / PTY
        ├─ existing #43 hybrid exchange
        ├─ new #144 API-first / Playwright fallback
        └─ new #147 gVisor OCI isolation
                        ↓
Agent Shield #44 provider convergence + applicable #95 live egress
                        ↓
bettor-arena#186 physical offline/reconnect monitoring canary
                        ├─ independent Shadow
                        └─ truth-verify-loop#22
                                ↓
bettor-arena#187 documentation/trace convergence
                                ↓
bettor-arena#68 final composition, release and rollback
```

The process DAG is not a Git branch graph. Cross-repository prerequisites never create Git ancestry.

## End-to-end data flow

```text
Local sovereign host
  local UI / CLI / Agent
        ↓
  exact source + data/effect classification
        ↓
  runtime-env OffloadJob + capability/policy/identity bindings
        ↓
  SQLite outbox transaction
        ↓
  local NATS leaf / transport adapter
        ║  disconnect is retained, not task failure
        ║  at-least-once delivery + idempotency key
        ↓
Cloud transport / durable workflow
  cloud NATS hub / adapter
        ↓
  durable workflow history + LoopX event proposal
        ↓
  leased Agent Shield runtime provider
        ↓
  API adapter ────────────────┐
        │ unavailable/policy  │
        └→ Playwright fallback│
                              ↓
  structured observation + target/source readback
        ↓
  content-addressed artifacts + cleanup receipt
        ↓
  Bettor Gates
        ├─ fail / stale / cancel / retry / compensate / HITL
        └─ pass candidate
                ↓
  effect ledger when an external write is requested
        ↓
  execution/result/effect receipt bundle
        ↓
Local transport / inbox
  result delivery attempts
        ↓
  SQLite inbox transaction
        ↓
  process restart + deterministic projection rebuild
        ↓
  user-visible result verification
        ↓
Independent verification
  truth-verify-loop + Shadow Architect
        ↓
Human Admit → #68 release / rollback
```

### Data that may not cross the portable boundary

```text
secret values
Keychain/KMS/OpenBao raw material
browser cookies and personal profiles
signed-in page bodies unless explicitly admitted and redacted
private device sessions
machine-local absolute paths
private chain of thought
mutable sibling checkouts
unbounded logs or source bodies
Human decisions without a signed/content-bound receipt
```

## Molecular implementation and Stack PR index

The following table records intended implementation atoms. It does **not** claim that a branch or PR exists unless an exact PR is named.

| Issue | Molecular atoms | Intended Git topology | Current Git/implementation state | Convergence owner |
|---|---|---|---|---|
| skills-shared #359 | `DA-M-C → DA-M-K → DA-M-E → DA-M-D` | contract-first true children only where later atoms consume unmerged schemas; independent docs may wait for admitted implementation | issue open; no implementation PR indexed here | final method/registry leaf under #359 and existing #332/#358 |
| skills-shared #360 | license decision, exact bytes, notices, SBOM/release gate | independent Human/legal sibling; no child relation to method bytes | issue open; `HUMAN_ADMIT_REQUIRED` | repository owner |
| runtime-env #57 | `DA-RC-C → DA-RC-K → DA-RC-E → DA-RC-D` | contract foundation then real children; shared contract/index only one owner | issue open; `NOT_IMPLEMENTED` | #57 docs/contract convergence |
| runtime-env #58 | `DA-TR-C`, sibling `DA-TR-L`/`DA-TR-N`, physical `DA-TR-E`, `DA-TR-D` | local and NATS leaves may be siblings after stable contract; physical canary consumes admitted bytes; shared docs/status in convergence | issue open; `NOT_IMPLEMENTED` / `NOT_EXERCISED` | #58 convergence, cross-repo final #186 |
| runtime-env #59 | `DA-ID-C`, sibling local/cloud/policy leaves, live controls, docs convergence | provider/runtime bindings are siblings after shared identity contract | issue open; `NOT_IMPLEMENTED` | #59 convergence |
| Bettor #184 | `DA-WF-C → DA-WF-K`, retry/HITL/compensation siblings, eval and docs convergence | children only when consuming unmerged workflow contract; shared module bytes one owner | issue open; `NOT_IMPLEMENTED` | #184 module convergence; release #68 |
| Bettor #185 | `DA-EF-C → DA-EF-K`, policy/provider/compensation siblings, eval/docs convergence | may start after admitted #184 contract; true child only for unmerged-byte use | issue open; `NOT_IMPLEMENTED` | #185 module convergence; release #68 |
| Agent Shield #144 | `DA-INT-C`, API/browser/policy/eval siblings, `DA-INT-D` | API and browser leaves are siblings after one route contract; registry/status is convergence-only | issue open; short issue contract recorded; `NOT_IMPLEMENTED` | Phase-3/provider convergence #44 plus #144 docs convergence |
| Agent Shield #147 | gVisor contract, deterministic adapter, live isolation/cleanup canary, docs/status convergence | sibling provider leaf under runtime SPI #38; does not become child of E2B | issue open; `NOT_IMPLEMENTED` | Phase-3 convergence #44 |
| Agent Shield #143 | license decision/notices/SBOM | independent Human/legal sibling | issue open; `HUMAN_ADMIT_REQUIRED` | repository owner |
| Bettor #186 | target freeze plus local/cloud/effect/Shadow sibling evidence lanes and one receipt convergence | process fan-out; Git siblings only where paths/resources are disjoint; no fake Stack | issue open; physical run `NOT_EXERCISED` | #186 evidence convergence; release #68 |
| truth-verify-loop #22 | contract plus delivery/effect/artifact/user sibling verifiers, mutations and docs convergence | verifier lanes may be siblings after shared bundle schema | issue open; `NOT_IMPLEMENTED` | #22 convergence |
| FDE #97 | license decision/notices/SBOM | independent Human/legal sibling | issue open; `HUMAN_ADMIT_REQUIRED` | repository owner |
| Bettor #187 / this branch | source-specialized `AGENTS.md`, README, JSON matrix and docs index | **true child of PR #176** because parent monitor bytes are consumed | branch `docs/187-dual-agent-closure`; draft child PR is the intended publication | issue #187 |
| Bettor #68 | terminal selection, locks, complete canaries, release, promotion/rollback | convergence from exact admitted main after every selected prerequisite; not stacked on one unmerged sibling | `BLOCKED_BY_PREDECESSORS`, `NOT_RELEASED` | #68 only |

### Current documentation Stack

```text
main
└─ PR #176  docs/173-tech-lead-shadow-closure
   Tech Lead + independent Shadow monitor and canonical Local Handoff route
   └─ docs/187-dual-agent-closure
      source-specific problem denominator, directory DAG, data flow and issue index
```

The child must remain based on the parent until the parent is admitted. After PR #176 merges, rebase/retarget the child onto exact `main`, re-run route/JSON/link controls, and update the PR evidence to the new exact head.

### Git Town rules

```text
path-disjoint work from one admitted base   → sibling branches
unmerged public contract consumed directly → true child
shared registry/status/index/release        → one convergence branch
process prerequisite in another repository → no Git ancestry
provider popularity or worker count         → no topology authority
```

Git Town manages admitted branch ancestry and bounded synchronization. It does not decide whether a source problem, implementation, test, provider, effect, user outcome, Human decision, license, release, or rollback is correct.

## Issue closure matrix

| Owner | Issue | Exact gap owned | Current stage | Required next transition |
|---|---:|---|---|---|
| skills-shared | #359 | portable local/cloud offload, authority, idempotency and evidence laws | `OWNER_AND_CONTRACT_BOUND` | implement exact portable contract and deterministic controls |
| skills-shared | #360 | explicit commercial/open-source license and notices | `HUMAN_ADMIT_REQUIRED` | owner/legal license decision, then exact bytes and release gate |
| runtime-env | #57 | exact offload/capability/effect/artifact/receipt schemas | `OWNER_AND_CONTRACT_BOUND` | implement schemas and cross-schema validator |
| runtime-env | #58 | SQLite outbox/inbox plus NATS/JetStream disconnect/reconnect | `OWNER_AND_CONTRACT_BOUND` | implement deterministic transport, then physical host canary |
| runtime-env | #59 | workload identity, audience, policy epoch and opaque secret handles | `OWNER_AND_CONTRACT_BOUND` | implement bindings and exact live enrollment/revocation cases |
| Bettor | #182 | explicit repository license and release notices | `HUMAN_ADMIT_REQUIRED` | owner/legal decision and exact release artifacts |
| Bettor | #183 | overall end-to-end source problem | `OWNER_AND_CONTRACT_BOUND` | maintain full denominator while child lanes implement and execute |
| Bettor | #184 | durable workflow/replay/retry/HITL/cancel/compensation | `OWNER_AND_CONTRACT_BOUND` | implement exact workflow adapter and deterministic replay controls |
| Bettor | #185 | idempotent observable external effects | `OWNER_AND_CONTRACT_BOUND` | implement effect ledger, readback and unknown/reconciliation semantics |
| Bettor | #186 | physical offline/reconnect monitoring user outcome | `NOT_EXERCISED` | satisfy prerequisites and run exact physical matrix |
| Bettor | #187 | source-specific docs/DAG/Stack traceability | `IMPLEMENTATION_IN_PROGRESS` | publish draft child PR, validate and preserve evidence ceiling |
| Agent Shield | #143 | explicit repository license and notices | `HUMAN_ADMIT_REQUIRED` | owner/legal decision and exact artifacts |
| Agent Shield | #144 | API-first integration and bounded browser fallback | `OWNER_AND_CONTRACT_BOUND` | expand exact route contract, implement adapter leaves and live receipts |
| Agent Shield | #147 | gVisor OCI runtime adapter and isolation canary | `OWNER_AND_CONTRACT_BOUND` | implement adapter, isolation controls and physical canary |
| truth-verify-loop | #22 | independent end-to-end receipt and user-result verification | `OWNER_AND_CONTRACT_BOUND` | implement bundle contract and planted false-closure controls |
| FDE | #97 | explicit Role Pack/Tenant Overlay license boundary | `HUMAN_ADMIT_REQUIRED` | owner/legal decision and exact release artifacts |
| Bettor | #68 | selected final composition, release and rollback | `BLOCKED_BY_PREDECESSORS` | wait for selected exact terminal subjects and Human/policy scope decision |

## Tech Lead review of previously completed mechanisms

The following mechanisms are useful prerequisites, not Dual-Agent problem closure:

| Existing mechanism | What it supports | What it does not prove |
|---|---|---|
| LoopX contract, ledger and reducer | single-writer task-state law and replayable event model | offline transport, provider execution, effect correctness, user result or release |
| Runtime Fabric and Worker Fleet | provider-neutral leases, workspaces, Workers and cleanup contracts | one selected local/cloud provider is live and equivalent |
| Decision Memory, Notes and Context Assembly | rebuildable context and bounded retrieval/projection | canonical workflow/effect state or source truth |
| Proof Kernel and controls | falsifiable claims, negative controls and subject-bound receipts | physical provider/user outcome without exact live evidence |
| stateless MCP gateway | default-deny typed public tool surface | local host reachability, provider availability or arbitrary action authority |
| Git Town controls | branch topology, leases and bounded no-push synchronization | implementation correctness, semantic conflict resolution, merge or release |
| Agent Shield runtime SPI/providers | typed provider boundaries and deterministic provider fixtures | live isolation, network, performance, cost or cleanup on the selected environment |
| truth-verify-loop current harness | source capture, semantic review and evidence closures | the new cross-repo Dual-Agent bundle shape until #22 lands |
| parent Shadow monitor PR #176 | honest closure vocabulary and Local Handoff routing | any Dual-Agent implementation or live evidence |

## Independent Shadow Architect monitor

For each change, the Shadow reviewer compares:

```text
DA-SRC-001 problem denominator
vs portable method
vs exact runtime contracts
vs current source and Git subjects
vs transport/workflow/provider/effect attempts
vs artifact and target readback
vs user-visible result
vs licensing/Human/release state
```

Mandatory disagreement checks:

- missing problem ID or silent scope narrowing;
- source proposal promoted to implementation/live/user truth;
- transport/task/workflow/Gate/effect/user/release lane substitution;
- local/cloud, API/browser, provider/provider, carrier/carrier or origin/origin substitution;
- stale or mutable source/runtime/policy/tool/image/target identity;
- dropped duplicate, failed, cancelled, blocked or superseded attempts;
- artifact listed without byte readback;
- effect committed without target readback or explicit unknown state;
- cleanup/residue or rollback unknown;
- license/terms absent for a mandatory release subject;
- multiple aggregate writers or fake Git ancestry;
- Human Admit inferred from machine eligibility.

A disagreement yields `CONTESTED`, `UNKNOWN`, `REPLAN_REQUIRED`, `BLOCKED_*`, or a narrower explicit scope. The Shadow does not silently edit semantic conflicts or recolor evidence.

## Local Handoff

This child does not mutate the canonical Local Handoff queue. The current queue under [`../../traceability/local-handoff-execution-queue.json`](../../traceability/local-handoff-execution-queue.json) remains parent-owned.

The Dual-Agent follow-up is an issue/process DAG, not permission to bypass the active Local Handoff epoch. Before any physical implementation:

1. reconcile and admit the parent/current local/GitHub/Forgejo subject required by the parent monitor;
2. select the currently executable issue whose prerequisites are exact and available;
3. create only that terminal branch/worktree and its leases;
4. leave unavailable provider, credential, device, browser, network, license and Human lanes explicitly blocked;
5. return exact receipts and residue state to the owning issue and parent monitor.

## Validation for this documentation slice

This branch must at least satisfy:

```text
all four leased files exist
README and AGENTS relative links resolve
closure-matrix.json parses as JSON
problem IDs and issue references are unique
all selected issues have a current evidence stage and next transition
no implementation/status/queue/lock/release/generated path changes
parent PR ancestry remains intact
source claims remain SOURCE_PROPOSAL
```

Repository-wide generated locks and proof receipts are parent/convergence-owned. This child does not regenerate them merely because documentation bytes changed.

## Completion boundary

This directory is complete only as a **candidate documentation route** when its exact child PR head passes link/JSON/route review and the parent/child relation is current. It cannot close #183, #184, #185, #186, any runtime/provider/license issue, or #68.

The Dual-Agent architecture remains open until one exact selected release reaches the user outcome, independent verification, Human admission, release and rollback stages without lane substitution.