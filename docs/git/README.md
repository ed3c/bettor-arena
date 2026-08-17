# Git Town Stacked-PR governance

## Role

This directory is the **repository-owned adoption and queue layer** for canonical shared delivery/orchestration methods.

```text
shared Skills
  = reusable Git Town / stacked-PR / Agentic Tech Lead procedures and eval contracts

docs/git/
  = Bettor repository profile, ordered queue, task/path-lease policy,
    Local Handoff Execution Queue, historical Stack snapshots and runtime admission state

Git Town
  = optional admitted local branch hierarchy and no-push synchronization engine

GitHub
  = publication/base/head/check authority

LoopX
  = canonical task-state authority

Human / typed admission
  = semantic conflict, terminal admission, promotion and rollback boundary
```

Bettor does not copy shared `SKILL.md` bodies. Consumer-specific queue instances stay here.

## Local Handoff authority

The portable handoff procedure is admitted from:

```text
repository: ed3c/skills-shared
commit:     dbcfdb4df76609822893aeb595e5f8ada8483435
path:       skills/agentic-tech-lead-orchestration/SKILL.md
schema:     skills/agentic-tech-lead-orchestration/references/local-handoff-queue.schema.json
validator:  skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py
```

The current consumer instance is [`local-handoff-execution-queue.json`](local-handoff-execution-queue.json). It freezes an immutable Bettor subject so the local executor does **not** chase mutable `main` while executing the handoff.

## Directory map

| File | Owner | Purpose | Authority |
|---|---|---|---|
| [`README.md`](README.md) | repository Git governance | route, State Machine and data flow | navigation |
| [`REPO_PROFILE.md`](REPO_PROFILE.md) | repository owner | branches, remotes, policies, receipts and automation boundaries | repository policy |
| [`PDF_TERMINAL_SEQUENCE.md`](PDF_TERMINAL_SEQUENCE.md) | #61/#102 queue owner | full ordered PDF completion queue and directory/data-flow map | human queue view |
| [`pdf-terminal-sequence.schema.json`](pdf-terminal-sequence.schema.json) | queue contract owner | closed shape for orders 0–25 | machine contract |
| [`pdf-terminal-sequence.json`](pdf-terminal-sequence.json) | queue owner | active item, prerequisites, paths, branches, acceptance and automation bounds | current reviewed queue |
| [`local-handoff-execution-queue.json`](local-handoff-execution-queue.json) | local handoff owner | zero-context #161 → #146 → #140 continuation contract | local execution queue |
| [`STACKED_PRS.md`](STACKED_PRS.md) | Stack topology owner | dependency-driven branch graph and expected branches | human topology view |
| [`WORKER_PROTOCOL.md`](WORKER_PROTOCOL.md) | task/lease owner | one Worker/worktree/branch/path lease | execution contract |
| [`GIT_TOWN_ADMISSION.md`](GIT_TOWN_ADMISSION.md) | trusted operator | executable/config/license/SBOM/legal/live gates | mutable admission ledger |
| [`stack-prs.index.schema.json`](stack-prs.index.schema.json) | historical snapshot contract | machine shape for observed PR graph | machine contract |
| [`stack-prs.index.json`](stack-prs.index.json) | generated/reviewed historical snapshot | observed GitHub graph and lineage | snapshot only |

Full historical human index: [`../traceability/STACK_PR_INDEX.md`](../traceability/STACK_PR_INDEX.md).

## State Machine

### Ordered completion

```text
PDF GAP INVENTORY
→ EXISTING ISSUE/PR SUBJECTS RESOLVED
→ MISSING TERMINALS CREATED
→ STRICT GLOBAL COMPLETION ORDER DECLARED
→ ONE ACTIVE TERMINAL
→ TASK PACKET + PATH LEASE
→ IMPLEMENT / CONTROL / MUTATION / CLEANUP
→ EXACT-HEAD PUBLICATION CANDIDATE
→ TERMINAL ADMISSION
→ QUEUE ADVANCE
→ FINAL CONVERGENCE #68
```

Current stopping point:

```text
program                        #61
queue index task               #102
completed prefix               orders 0–12
active order                   13
active terminal                #140 / HUMAN_ADMIT_REQUIRED
local handoff active item      #161 / runtime rebind + scheduler canary
local handoff successor        #146 / physical Tech Lead golden run
terminal handoff successor     #140 / Human admission + typed queue transition
final convergence              #68
```

The local handoff is a continuation **inside** active order 13. It does not create a second PDF terminal and cannot advance order 13 by itself.

### Zero-context local handoff

```text
IMMUTABLE HANDOFF SUBJECT FROZEN
→ #161 HOST REBIND CONTRACT SELFTEST
→ RESOLVE CLEAN LOCAL runtime-env ROOT
→ REBIND exact runtime-env/profile/workload
→ SCHEDULER / PROCESS-WORKTREE CANARY
→ #161 EXIT RECEIPT PASS
→ #146 PHYSICAL TECH LEAD GOLDEN RUN
→ LIVE PROVIDER / SOURCE / WORKTREE / SQLITE / FORGE RECEIPTS
→ #146 EXIT RECEIPT PASS
→ #140 HUMAN TERMINAL ADMISSION
→ TYPED PDF QUEUE ADVANCEMENT
```

Current frozen handoff subject:

```text
bettor-arena commit  542a935064e06f358d7d890df5d86364bbc20f46
bettor-arena tree    78a6b573f094f1df7f3537ace551768f70210e51
runtime-env          77dca3584a4adb1c463c815bdb5ab603eae32b23
profile              bettor-arena-tech-lead-local
#161 state           BLOCKED_STALE_BINDING
consumer canary      NOT_EXERCISED
```

A local executor starts from the single `ACTIVE` item in `local-handoff-execution-queue.json`. Any `unresolved_operations` must first be resolved from their named canonical source into a concrete argv/cwd/timeout contract. Fake command names are forbidden.

### Git Town runtime

```text
SHARED_METHOD_PINNED
→ REPO_PROFILE_VALIDATED
→ EXECUTABLE / LICENSE / SBOM / CONFIG ADMISSION
→ ISOLATED STACK FIXTURE
→ DRY-RUN NO-PUSH
→ LIVE LOCAL NO-PUSH
→ REPOSITORY EVALS
→ GITHUB PUBLICATION GATE
→ HUMAN / POLICY ADMISSION
→ MERGE / SHIP / ROLLBACK
```

Current runtime state:

```text
SHARED_METHOD_PINNED       PASS
REPO_PROFILE_VALIDATED     IMPLEMENTED
ORDERED_QUEUE_INDEXED      IMPLEMENTED; #140/order 13 ACTIVE
PHYSICAL_CONTROLS          PASS where separately observed
GIT_TOWN_EXECUTABLE        ABSENT for the admitted Darwin lane
GIT_TOWN_CONFIG            ABSENT
LOCAL_NO_PUSH_SYNC         NOT_EXERCISED
PUBLICATION                NOT_EXERCISED for the physical handoff result
HUMAN_ADMIT                REQUIRED for Darwin artifact / semantic decisions
```

## Local handoff command surface

Repository-owned deterministic entrypoints already known:

```sh
python3 scripts/gates/issue_161_host_rebind.py --selftest
python3 scripts/gates/check_issue_161_runtime_admission.py --selftest
python3 scripts/gates/check_issue_161_runtime_admission.py
python3 scripts/gates/check_local_handoff_execution_queue.py --selftest
python3 scripts/gates/check_local_handoff_execution_queue.py

sh loop_wiki/parallel-agent-tech-lead/tests/run-all.sh
sh loop_wiki/code-truth-graph-v2/tests/run-all.sh
sh tests/agentic-tech-lead-binding/run-all.sh
python3 scripts/gates/check_issue_140_convergence.py
```

The actual host rebind apply requires a clean local checkout of the pinned runtime-env subject and an explicit `--runtime-env-root`; the handoff queue leaves only that machine-local root resolution unresolved. Scheduler/process-worktree canary, physical Tech Lead run, and Human terminal admission remain separately resolved operations until their concrete contracts are materialized from the named authorities.

## Evidence states

Keep these distinct:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
ACTIVE
BLOCKED_BY_PREDECESSOR
FINAL_CONVERGENCE
```

No static fixture, synthetic runtime, provider hit, issue UI state, Git Town success, or Forgejo success may proxy a different live/evidence lane.

## Authority boundary

Automation must not infer or perform merge, force-push, issue close, PDF queue advance, provider activation, promotion, rollback, permission change, or semantic-conflict resolution from handoff success. Human/policy-owned transitions require their own typed admission receipt.
