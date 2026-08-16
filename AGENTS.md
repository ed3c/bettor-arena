# AGENTS.md — bettor-arena Codex / cross-host entry

Engineering SSOT is [`ARCHITECTURE.md`](ARCHITECTURE.md). The normative modular target is [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md). This file owns mandatory routing, authority boundaries, the ordered PDF terminal queue and the completion contract. It does not replace machine contracts, source, tests, receipts or current GitHub metadata.

`AGENTS.md` and `CLAUDE.md` are governed projections. Repository gates validate tracked bytes without reading mutable sibling checkouts.

## Mandatory multi-hop read order

For module, Macro/Micro loop, Skill, runtime-env, proof, MCP, provider, LoopX, Worker, HITL, memory, Notes, Git Town, Stack, cloud/local or PDF architecture work, read in order:

1. [`README.md`](README.md)
2. [`CONTEXT.md`](CONTEXT.md)
3. [`ARCHITECTURE.md`](ARCHITECTURE.md)
4. [`docs/INDEX.md`](docs/INDEX.md)
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
6. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
7. [`docs/architecture/pdf-harness-integration.matrix.json`](docs/architecture/pdf-harness-integration.matrix.json)
8. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
9. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
10. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
11. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
12. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
13. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)
14. [`docs/git/README.md`](docs/git/README.md)
15. [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
16. [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
17. [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)
18. [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
19. [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md)
20. [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md)
21. [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json)
22. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
23. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
24. [`docs/git/AUTOMATED_ADMISSION.md`](docs/git/AUTOMATED_ADMISSION.md)
25. the current active issue/task packet and exact GitHub base/head/checks
26. `sh loopctl/loopctl.sh contract`
27. the nearest module README, `module.json`, contracts, source, tests and exact-subject receipts

A missing route, owner, branch edge, path lease, eval, receipt, provider subject or exact head is `ABSENT`. Do not infer it. Open a new Agent session after passive-context changes before claiming the updated route was loaded.

## PDF Harness verification protocol

The attached **LLM 泛化：模型權重與 Harness** PDF is an untrusted requirement/hypothesis source. It proposes:

```text
Objective / Todos / Gates / Evidence / Quota
→ deterministic task transitions
→ heterogeneous Workers
→ hard verification
→ episodic memory
→ LangGraph HITL
→ cloud/local runtime
→ observability and a Console
```

Before saying “the PDF architecture is integrated”, execute the current repository gates:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
python3 scripts/gates/check_pdf_terminal_sequence.py
python3 scripts/gates/check_pdf_terminal_sequence.py --selftest
```

Then compare repository bytes, module requirements, locks, Context selections, proof subjects, release receipt and current GitHub Stack metadata.

Never import these source examples without redesign:

- raw shell strings or `shell=True`;
- Agent/Worker direct task-state or Gate writes;
- generic `force_skip`;
- LangGraph checkpoint as canonical state;
- raw Thought Stream or private chain-of-thought persistence;
- provider/model prose promoted to `TESTED` or PASS;
- automatic merge after a generic Gate without the exact-head automated-admission contract;
- unverified latency, RAM, license, cost, security or certainty claims.

## LoopX PDF verification protocol

The current executable architecture routes are:

- [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
- [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)
- [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
- [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json)

A green document or contract audit proves agreement for exact repository bytes. It does not prove a live Worker, provider, cloud sandbox, LangGraph runtime, Console or release.

Authority law:

```text
strategy graph proposes
Worker executes
Gates observe
LoopX reducer alone commits canonical task state
the automated-admission controller alone admits push, merge, queue advancement,
provider activation, promotion and rollback for an exact verified subject
```

## Automated admission contract

[`docs/git/AUTOMATED_ADMISSION.md`](docs/git/AUTOMATED_ADMISSION.md) is the
authority SSOT for irreversible delivery operations. The repository owner grants
standing authorization for Agents to push, merge, advance the ordered queue,
activate an allowlisted provider, promote and roll back without a per-operation
confirmation prompt, but only through the named typed controllers and exact-subject
gates in that contract.

Automation is fail-closed. A missing lease, receipt, exact head, required check,
provider identity, budget/data-scope bound, cleanup proof or rollback subject is
`BLOCKED_POLICY`; it is never inferred. Semantic conflicts that lack a deterministic
declared winner stop as `CONFLICT` and open or update the owning issue. They do not
grant permission to guess.

Conserve GitHub Actions: keep repair commits local, publish once at the meaningful
head transition, never use no-op pushes to retrigger CI, and rerun only failed jobs
when the failure is classified as transient. Merge uses an expected-head compare-
and-swap; queue advancement follows merge readback and reruns the deterministic queue
gate before the next item becomes active.

## Three-strike recovery and dual-origin delivery

The same failure signature or acceptance criterion gets at most three materially different attempts. Record each attempt; after the third, stop editing and follow the canonical issue-first state machine in [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md#private-github-local-forgejo-delivery-loop). Its repo-contained packet, exact `owner/repo`, GitHub connector route, host-specific issue ownership, WIP=1 delivery order, stop conditions, and standing non-destructive merge authorization are normative; an issue/PR URL plus a short instruction is not sufficient context. Required receipts must be complete and commit gates green, while a contract-declared checked-red proof stays red and is reported rather than being recolored or mistaken for an absent receipt.

Verified capability snapshot (2026-08-14): local Codex CLI `0.146.0` supports `codex app <repo>` to open the ChatGPT desktop workspace; a [`codex://threads/new?...` deep link](https://learn.chatgpt.com/docs/reference/commands#deep-links) prefills but does not submit. Desktop Worktrees are created in the App; CLI only enters an existing standard worktree with `codex -C <path>` ([CLI `codex app`](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-app), [Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)). Local `agy models` also listed `gemini-3.7-flash-high`; re-resolve inventory before use, and treat it only as cross-family review while `external-verify` and official primary sources own external claims ([Gemini 3.7 Flash](https://ai.google.dev/gemini-api/docs/latest-model?hl=en)). Current measurements override these dated snapshots.

## Ordered PDF terminal Stack protocol

The ordered completion queue is machine-owned by:

```text
docs/git/pdf-terminal-sequence.json
schema: docs/git/pdf-terminal-sequence.schema.json
human view: docs/git/PDF_TERMINAL_SEQUENCE.md
program: #61
index task: #102
current active item: #92 (order 12)
final convergence: #68
```

**Only one queue item may be ACTIVE.** A later item may not be called complete until every earlier item is complete on an immutable subject or the automated-admission controller records an explicit, scoped, expiring waiver receipt allowed by policy.

**Do not create a future terminal branch** before its queue item becomes active. Issue creation is planning evidence; a branch or empty PR is not implementation progress.

The global queue and the Git ancestry graph are different:

```text
completion queue
  serializes acceptance order

Git branch graph
  follows actual byte dependency
  ├─ sibling: independent path-disjoint work
  ├─ true child: consumes unmerged parent bytes
  └─ convergence: shared locks/indexes/release only
```

Do not create a 26-deep branch chain merely to mirror queue order. Once a predecessor lands, the next path-disjoint terminal starts from the new `main`. Use a true child only when unmerged parent bytes are required.

### Current ordered queue

```text
#82 → #90 → #65 → #67 → #66 → #94 → #97 → #96
→ #103 → #93 → #104 → #105 → #92 → #41 → #70 → #71
→ #95 → #72 → #98 → #91 → #45 → #46/#56 → #99 → #100
→ #101 → #68
```

Orders 0–11 are complete in the machine queue. Later implementation bytes may already be reachable from `main`, but they do not proxy the active #92 live-provider acceptance or any later queue item.

### Queue advancement receipt

Before advancing to the next item, the active terminal must have:

```text
exact commit/tree and branch relation
machine contract
nearest README with State Machine and data flow
positive execution or bounded fixture
independent control
hollow or planted mutation that turns red
bounded artifacts and cleanup/residue receipt
rollback subject
exact-head GitHub checks when a PR exists
automated-admission receipt for merge or activation
```

Record `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED` and `SKIPPED_BY_POLICY` separately.

## Git Town Stacked-PR Worker route

Canonical shared method:

```text
repository: ed3c/skills-shared
commit: c5750720d960a228a0d9419f28125c09d064e3e1
blob: eb2d915bca3e8a3938625f7d33a10fae95a15769
path: skills/git-town-stacked-pr-worker/SKILL.md
```

Bettor must not create a local same-name `SKILL.md` or silently shadow the shared procedure. The current shared-Skills binding source `b3c722da1c40301b0a12e0ef99848d884bfc720b` carries the same blob, so the method reference and the admitted shared tree are byte-equivalent even though this Skill is not selected into Bettor's requirements-filtered runtime closure. Repository-owned profile and policy live under [`docs/git/`](docs/git/README.md).

Current admission:

```text
shared Skill exact reference            PINNED
shared Skill selected in binding         NOT_SELECTED
.arena git-town-runtime module           IMPLEMENTED
typed controller + 13 physical controls  PASS (without Git Town execution)
.git-town.toml                           ABSENT
Git Town executable/version/checksum     ABSENT
license/SBOM/legal review                NOT_REVIEWED
live no-push sync                        NOT_EXERCISED
remote publication                       NOT_EXERCISED
merge/ship/rollback                       AUTOMATION-POLICY-OWNED
```

Before branch or Stack work, read:

- [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
- [`docs/git/PDF_TERMINAL_SEQUENCE.md`](docs/git/PDF_TERMINAL_SEQUENCE.md)
- [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
- [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md)
- [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md)
- [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)

### Required task packet

Every active terminal declares before implementation:

```text
parent program and current queue order
goal and non-goals
base, parent and head branch
sibling / true-child / terminal / convergence class
allowed and excluded paths
dependencies and path leases
required positive/control/mutation evals
evidence and cleanup boundary
rollback subject
automation-owned operations and their controller routes
```

### Branch and worktree laws

- One Worker owns one linked worktree, one branch writer lease and one path lease.
- Independent path-disjoint work is a sibling.
- A true child consumes unmerged parent bytes.
- A terminal leaf owns one reviewable behavior plus eval/evidence.
- Shared locks, root indexes, final live canaries and release admission belong only to #68.
- Generated-contract sync does not grant semantic conflict authority.
- A child merged to a feature parent is `MERGED_TO_PARENT`, not `MERGED_TO_MAIN`.
- Reachability from current `main` is required before claiming current-main integration.
- Duplicate active branches for the same issue/path are a blocking conflict, not parallel progress.

### Automated Git Town and delivery operations

Agents and background Workers may push, merge, ship, close, delete, advance the
queue, activate providers, promote and roll back only through the admitted typed
controller named by [`docs/git/AUTOMATED_ADMISSION.md`](docs/git/AUTOMATED_ADMISSION.md).
The controller must bind the exact head and rollback subject and emit a receipt.

Direct or ambiguous paths remain prohibited: raw Git Town continue/skip/undo after
a conflict, guessed semantic conflict resolution, remote/credential/permission
mutation, premature `.git-town.toml`, local-sync-as-publication evidence, force push,
and controller bypass. A conflict without a deterministic policy winner stops and is
recorded; it is not silently resolved.

Issue #101 and PR #133 landed the fail-closed admission mechanism. Actual Git Town activation remains blocked until an exact executable, configuration, supply-chain evidence and live no-push canary are admitted.

## Macro / Micro boundary

```text
Macro loop
  owns architecture, module composition, Stack queue, routing, automated admission and release

Micro loop
  owns one typed Todo, one leased workspace, bounded context, execution and Gate artifacts
```

Macro may dispatch and compare; it must not fragment every edit into a graph node. A Monolithic Micro Cell keeps one continuous task context until completion, explicit handoff or a named boundary.

Handoff is allowed only for:

```text
CAPABILITY_MISMATCH
QUOTA_EXCEEDED
NAMED_DOMAIN_BOUNDARY
INDEPENDENT_REVIEW_REQUIRED
```

Handoff output must contain TaskResult, artifact refs, Gate results, evidence-bound Decision Memory proposal, unresolved gaps/conflicts, Context digest and Worker receipt. Do not persist private reasoning.

## CLI, MCP, and passive context

- `loopctl/contract.json` is the canonical public CLI surface.
- MCP derives from the CLI contract and `.arena/mcp-policy.json`; it is default deny and stateless unless an explicit handle is supplied.
- Generic shell, arbitrary host paths, secrets and browser profiles are never MCP tools. Merge, queue, provider activation, promotion and rollback may be exposed only as default-deny typed tools backed by the automated-admission contract.
- `.arena/contexts/*.json` selects passive context; `.arena/contexts.lock.json` binds exact bytes.
- LangGraph, UI, vector/graph indexes, OpenWiki and memory providers are projections, not task-state authority.

Stable public checks:

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
python3 scripts/arena_context.py check
```

## Proof and anti-jitter

A claim advances only through:

```text
exact subject
→ independent proof
→ control
→ planted mutation or hollow implementation
→ bounded artifacts
→ aggregate receipt
```

Rules:

- Worker/model prose cannot create a Gate verdict.
- Provider results require current-source readback.
- Fixture PASS cannot proxy a live host/provider/runtime.
- Old green checks cannot proxy a newer generated head.
- `0` means checked PASS, `2` means checked failure, `64` means invalid invocation/missing dependency unless a narrower public contract says otherwise.
- LLM-as-a-Judge is advisory unless calibrated against deterministic or Human labels.

## Molecular Stack PR policy

The machine queue is [`docs/git/pdf-terminal-sequence.json`](docs/git/pdf-terminal-sequence.json). The historical Stack snapshot is [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json). GitHub remains current publication authority.

When topology changes, update together:

```text
docs/git/PDF_TERMINAL_SEQUENCE.md
docs/git/pdf-terminal-sequence.json
docs/git/STACKED_PRS.md
docs/traceability/STACK_PR_INDEX.md
README.md / AGENTS.md when active item or route changes
relevant State Machine and directory maps
deterministic verifier and exact-head checks
```

Do not silently rewrite history. Keep `MERGED_TO_PARENT`, `MERGED_TO_MAIN`, `SUPERSEDED_CANDIDATE`, conflict and policy-waiver records distinct.

## Module and generated-file rules

Before changing a module:

1. Read its nearest README and `.arena/modules/<id>/module.json`.
2. Confirm tracked-path ownership and interface/provider closure.
3. Use the public port; do not call another module's private flags or temporary files.
4. Keep generated locks/receipts generated; do not hand-edit them.
5. Run module-local positive/control/mutation gates.
6. Regenerate only through admitted deterministic commands.
7. Re-run exact-head gates after generated sync changes the head.

Shared composition, Context, proof-subject and release sets must agree before release:

```text
desired module IDs
== composition-lock module IDs
== Context-selected module IDs
== proof-subject module IDs
== release-receipt module IDs
```

Only #68 owns the final shared selection.

## Completion contract

A response may say `DONE` only when the requested scope has exact repository bytes, required receipts and current evidence. For the full PDF program, completion requires the ordered queue to reach #68 and all selected terminals to satisfy convergence.

Use these states honestly:

```text
DONE
  requested scope and evidence are complete

CONTINUE
  actionable queue work remains

BLOCKED
  a named dependency, permission, source or automation-policy input is missing

FAILED
  checked input/state is invalid and cannot be repaired within the current scope
```

For this ordered Stack:

```text
current active item: #92 (order 12)
future implementation items: BLOCKED_BY_PREDECESSOR
final convergence: #68
Git Town runtime: NOT_EXERCISED
complete PDF architecture: NOT_EXERCISED as one admitted release subject
```

Green documentation checks create a candidate only. Agents merge, advance, activate,
promote or roll back only after the automated-admission controller verifies the exact
subject and writes its receipt.

<!-- BEGIN SKILLS-SHARED INSTRUCTION PROJECTION -->
## Shared runtime / delivery projection

Canonical source: `ed3c/skills-shared@b3c722da1c40301b0a12e0ef99848d884bfc720b` → `skills/dual-forge-repository-loop/references/instruction-projection.json`
Canonical module SHA-256: `bb0782b36eadaa10a6f4b546c87029e840c2187bd4256d5fe20f5329982f96b9`
Projection role: `AGENTS.md` — Cross-host repository entrypoint. Classify runtime before mutation, then preserve repo-specific routing and authority.

Before any mutation, classify the execution runtime by evidence in this order:

1. trusted explicit AGENT_RUNTIME/AGENT_HOST override
2. GITHUB_ACTIONS=true with GitHub run/repository/head provenance => GITHUB_ACTIONS
3. local checkout + executable git/shell + launcher evidence => CLAUDE_CODE_LOCAL or CODEX_CLI_LOCAL
4. Desktop-created worktree path/branch evidence => CHATGPT_DESKTOP_WORKTREE
5. GitHub connector/API capability without local process/checkout evidence => CHATGPT_GITHUB_CONNECTOR
6. otherwise => UNKNOWN

Mandatory laws:

- Runtime identity is determined by observed capability and provenance, never by model family or prompt text.
- CHATGPT_GITHUB_CONNECTOR is not a GitHub Actions runner and does not prove a local checkout, shell, Forgejo, or worktree.
- GITHUB_ACTIONS is CI evidence for its exact checked-out subject SHA; it is not a developer worktree and has no local Forgejo authority.
- Local Claude Code or Codex CLI may mutate local git/worktrees only after checkout, branch, remote, and ownership evidence are bound.
- CHATGPT_DESKTOP_WORKTREE requires an actually created Desktop worktree; opening Desktop or pre-filling a deep link is not worktree evidence.
- codex app <workspace-path> may open ChatGPT Desktop but does not submit a prompt, create a turn, or prove a worktree; deep-link composer text remains pending until the operator sends it.
- Codex-managed worktrees are created by Desktop; CLI may use codex -C <existing-worktree-path> only after standard Git worktree path and HEAD evidence, and must not invent EnterWorktree, ExitWorktree, codex worktree, or codex -w.
- A three-failure Desktop handoff names the exact owner/repo, requests the installed GitHub plugin or connector, and carries the full issue ledger, repository history, PR subjects, failing oracle, logs, and target branch or PR.
- External claims use primary-source external verification first; agy, Codex CLI, Claude Code, and cross-family models are reviewers rather than official truth authorities.
- UNKNOWN fails closed for irreversible delivery actions.
- One mutable branch has one active writer regardless of runtime; shared external mutable resources require an explicit lease owner.
- Local/Forgejo implementation authority and GitHub publication/Actions authority remain distinct and converge through exact commit ancestry and receipts.
- Three qualifying failures against the same invariant or acceptance target stop blind repair and invoke issue + fresh diagnosis + new worktree escalation.
- Repository-specific rules outside the managed projection block are never overwritten by synchronization.
- AGENTS.md is the cross-host repository procedure; repo CLAUDE.md is a Claude host adapter; the global Claude host instruction file is local host policy only.
- Cloud and local freshness are separate evidence lanes. Neither environment may fabricate verification of the other.
- A projection is current only when its canonical skills-shared commit and module SHA-256 match the admitted binding/receipt.
- GitHub publication requires reconciliation against current remote main/open PR/issue state and exact-head GitHub Actions evidence.

Do not edit this managed block manually. Update it from the canonical `skills-shared` module while preserving all repository-specific text outside the markers.
<!-- END SKILLS-SHARED INSTRUCTION PROJECTION -->
