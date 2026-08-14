# State machines — bettor-arena

This route names the state owners and transitions represented by current repository bytes, then separates the missing LoopX state machines proposed by the attached PDF.

Machine manifests, scripts, contracts, tests and receipts remain authoritative over this Markdown.

## 1. Agent/document routing

```text
TASK RECEIVED
→ README / AGENTS / CLAUDE
→ CONTEXT + ARCHITECTURE
→ PDF AUDIT / TARGET / CURRENT STATUS
→ DIRECTORY OWNER
→ MACHINE CONTRACT
→ SOURCE / TEST / RECEIPT
→ EXACT ISSUE / STACK PR
```

Non-success:

```text
missing route / owner / subject / evidence → ABSENT
stale or conflicting prose                → FAIL until corrected
```

Owner: `arena-core`.

## 2. Macro / composition state machine

```text
MODULE PROPOSED
→ module.json + sibling README
→ TRACKED PATH OWNER ASSIGNED
→ COMPOSITION REQUIREMENT SELECTED
→ CAPABILITY / DEPENDENCY / CONFLICT RESOLVED
→ COMPOSITION LOCK
→ CONTEXT CAPSULE LOCK
→ MODULE CLOSURE SUBJECTS
→ PROOF / CONTROL / MUTATION
→ RELEASE RECEIPT
→ HUMAN ADMIT
→ MERGE / PROMOTE / ROLLBACK
```

Hard rules:

- desired, locked and released module ID sets must be equal;
- every tracked path has one owner or reviewed generated/evidence class;
- a focused feature PASS cannot proxy a stale composition lock;
- generated digests are regenerated, never hand-authored;
- Human Admit is not inferred from a green gate.

Owners: `module-catalog`, `proof-kernel`, trusted operator.

## 3. Micro / bounded task state machine

```text
TYPED PACKET / PUBLIC REQUEST
→ CONTRACT + SUBJECT VALIDATION
→ BOUNDED RUNTIME / DISPOSABLE WORKTREE
→ ARTIFACT COLLECTION
→ INDEPENDENT ASSERTION
→ NAMED EXIT
   ├─ 0  success for exact subject
   ├─ 2  checked condition failed
   └─ 64 usage / absent dependency / FATAL
→ RECEIPT
→ CALLER SELECTS NEXT EDGE
```

Micro cannot:

```text
Human Admit
merge
release-promote
production rollback
permission widening
write another module's state
```

Owners: target module public port and `loop-runtime`.

## 4. Module lifecycle

```text
PROPOSED
→ CONTRACTED
→ COMPOSED
→ VERIFIED
→ CONTROLLED
→ MUTATION-SENSITIVE
→ RELEASE-CANDIDATE
→ HUMAN-ADMITTED
→ RELEASED
→ SUPERSEDED / ROLLED BACK
```

`IMPLEMENTED` describes mechanism presence. `PASS` describes an executed exact subject. `NOT_EXERCISED` remains distinct from both.

## 5. Context Capsule state machine

```text
ROOT + LOOP NATIVE FILES
→ SELECTION MANIFEST
→ IMMUTABLE REPOSITORY REF
→ MATERIALIZATION
→ DIGEST FREEZE
→ DRIVER PREPARE
→ HOST EXECUTION
→ TYPED OUTPUT VALIDATION
→ CONTEXT / DRIVER RECEIPT
```

Current state:

```text
offline selection/materialization/digest     IMPLEMENTED
live Codex / Claude canaries                 NOT_EXERCISED
Grok / OpenCode / Pi / Ante live canaries    NOT_EXERCISED
```

A Context Capsule is input projection, not canonical task state.

## 6. Portable Skill execution state machine

```text
CANONICAL SKILL
→ IMMUTABLE CONSUMER BINDING
→ HOST PROJECTION
→ AGENT PROPOSAL
→ TYPED EXECUTABLE + ARGV REQUEST
→ DISPOSABLE DETACHED WORKTREE
→ OS PROCESS + ARTIFACT CAPTURE
→ INDEPENDENT HARD ASSERTIONS
→ SUBJECT-BOUND RECEIPT
→ CLEANUP
```

Worker/model output is evidence input, never the verdict. Raw command strings, `shell=True`, arbitrary host paths and Worker-owned PASS are rejected.

Owner: `agent-runtime-integration`.

## 7. Stateless MCP state machine

```text
CANONICAL CLI CONTRACT
→ POLICY DEFAULT DENY
→ SELECTED EXPOSED TOOL
→ IMMUTABLE RELEASE SUBJECT
→ INLINE / CONTENT-ADDRESSED CARRIER
→ DISPOSABLE WORKSPACE
→ PUBLIC PORT EXECUTION
→ TYPED RESULT
→ CLEANUP RECEIPT
```

Forbidden:

```text
generic shell-over-MCP
server-host path from caller
secret/cookie/profile payload
live owner checkout mutation
implicit connection state
Human Admit tool
```

Owner: `loop-runtime` and `mcp-adapters`.

## 8. Proof state machine

```text
CLAIM
→ MODULE SUBJECT / CLOSURE
→ PHYSICAL PROOF TRAVERSAL
→ INDEPENDENT CONTROL EXECUTION
→ HOLLOW / MUTATION
→ RECEIPTS
→ RELEASE AGGREGATION
```

A proof receipt is not a live provider canary. The release aggregate remains `NOT_EXERCISED` until required evidence is present for its exact subject.

Owner: `proof-kernel`.

## 9. Project bootstrap state machine

```text
PRESET / DESIRED CAPABILITIES
→ PLAN
→ RESOLVE MODULES / SKILLS / RUNTIME
→ RENDER TEMP TREE
→ VERIFY TEMP TREE
→ CONFLICT + DRIFT CHECK
→ APPLY
→ APPLY RECEIPT
→ VERIFY TARGET
→ ROLLBACK IF TARGET BYTES UNCHANGED
```

Owner: `project-bootstrapper`.

## 10. OpenWiki state machine

```text
WIKI-UPDATE REQUEST
→ CONTRACT CHECK
→ FIXED / ITERATION / EMERGENT CONTEXT LANES
→ DRY RUN BY DEFAULT
→ FULL MODEL TURN ONLY WITH EXPLICIT OPT-IN
→ PATH BOUNDARY CHECK
→ VERIFIER
→ RECEIPT
→ TRACKED OPENWIKI PROJECTION
```

`openwiki/` is a rebuildable projection. It does not become source authority over code, tests or receipts.

Owner: `openwiki`.

## 11. Code Truth Graph state machine

```text
CLOSED SOURCE PACKET
→ PINNED TOOL PROFILE
→ STATIC PARSE / SYMBOL / EDGE BUILD
→ CONTENT-ADDRESSED SNAPSHOT
→ GRAPH / RESULT ARTIFACT
→ VERIFICATION
→ RECEIPT
```

Graph edges remain bounded by parser/language/path coverage and source provenance. They do not prove runtime behavior.

Owner: `code-truth-graph`.

## 12. Knowledge-provider state machine

```text
PROVIDER MANIFEST
→ EXACT SUBJECT + BOUNDED CAPABILITY REQUEST
→ PINNED ADAPTER / INDEX IDENTITY
→ READ-ONLY QUERY OR MEMORY PROPOSAL
→ SUBJECT / QUERY / FRESHNESS RECEIPT
→ CURRENT SOURCE / MANIFEST / TEST / RUNTIME READBACK
→ CANDIDATE RECOMMENDATION
→ HUMAN ADMIT
```

Current state:

```text
Serena contract                 IMPLEMENTED
GrepAI contract                 IMPLEMENTED
Code-Graph-RAG contract         IMPLEMENTED
Mem0 proposal contract          IMPLEMENTED

Serena live canary              NOT_EXERCISED
GrepAI live canary              NOT_EXERCISED
Code-Graph-RAG runtime          NOT_IMPLEMENTED
Mem0 runtime/writeback          NOT_IMPLEMENTED
```

Owner: `knowledge-providers`.

## 13. Origin and browser state machines

### Logical origin

```text
SOURCE COMMIT / TREE
→ FORGEJO OR GITHUB PUBLICATION
→ RELEASE MANIFEST
→ ORIGIN STATUS
→ EQUIVALENCE RECEIPT
→ HUMAN PROMOTION
```

Mutable `main` is not equivalence evidence.

### Browser

```text
ACTOR + SURFACE
→ TRANSPORT
→ SESSION REFERENCE
→ WORKFLOW
→ EVIDENCE
→ CLEANUP
→ HUMAN ADMIT
```

Signed-in profiles and sessions remain host-only.

Owner: `environment-contracts`.

## 14. External release acceptance

```text
EXTERNAL REPOSITORY RELEASE
→ EXACT COMMIT / MANIFEST / DIGEST
→ SELECTED MODULES + CAPABILITIES
→ OFFLINE CLOSURE VALIDATION
→ OPTIONAL LIVE REACHABILITY / INITIALIZATION
→ CONSUMER RECEIPT
→ HUMAN ADMIT
```

Current Agent Shield reference-consumer acceptance issue is `bettor-arena#24`; no unique implementation delta exists on its historical feature branch.

## 15. Molecular delivery state machine

```text
SOURCE / INCIDENT
→ ARCHITECTURE DECISION
→ PARENT ISSUE
→ MOLECULAR TERMINAL ISSUE
→ BRANCH / PR / EXACT HEAD
→ POSITIVE + HOLLOW/MUTATION
→ GENERATED LOCKS / INDEXES
→ CONVERGENCE LEAF
→ HUMAN ADMIT
```

Relations:

```text
sibling      independent bytes
true child   consumes unmerged parent
terminal     one behavior + eval/evidence
convergence  shared lock/index/final acceptance
```

No `.git-town.toml` or `.git-town` is currently tracked. These are delivery semantics, not proof of active Git Town configuration.

Owner: issue/PR policy and trusted operator.

## 16. Missing PDF LoopX state kernel

The PDF proposes:

```text
INIT
→ OBJECTIVE LOCKED
→ TODO READY
→ DISPATCHED
→ RUNNING
→ VERIFYING
   ├─ GATES PASSED
   │    → MEMORY PROPOSED
   │    → READY FOR HUMAN ADMIT / NEXT TODO
   ├─ RETRYABLE FAILURE
   │    → RETRY SCHEDULED
   ├─ QUOTA EXCEEDED
   │    → HITL WAIT
   ├─ CAPABILITY MISMATCH
   │    → HANDOFF REQUIRED
   ├─ BLOCKED
   └─ FAILED TERMINAL
```

Required components:

```text
Objective / Todo / Gate / Evidence / Quota schemas
append-only event ledger
single-writer lease
deterministic reducer
derived snapshot projector
replay and corruption controls
quota and retry accounting
terminal-state contract
```

Current state: `NOT_IMPLEMENTED`.

`loopctl` dispatch and module receipts are enabling mechanisms, not this state machine.

## 17. Missing strategy graph and HITL state machine

```text
CURRENT LOOPX SNAPSHOT
→ STRATEGY GRAPH SELECTS NEXT COMMAND
→ LOOPX VALIDATES CAPABILITY / QUOTA / DEPENDENCIES
→ COMMAND DISPATCH
→ RESULT EVENT
→ REDUCER
→ CONTINUE OR INTERRUPT
→ HUMAN DECISION RECEIPT
→ RESUME / ABORT / EXCEPTION
```

Rules:

- graph checkpoint is a projection, not canonical truth;
- strategy node cannot write task state;
- `force_skip` is replaced by a scoped exception receipt;
- resume must re-run required hard gates.

Current state: `NOT_IMPLEMENTED`.

## 18. Missing decision-memory state machine

```text
OBSERVATION / DEAD END / QUIRK / DECISION
→ EVIDENCE REFERENCES
→ SCOPE + VALIDITY + PRIVACY
→ CONFLICT / SUPERSESSION
→ CAPSULE PROPOSAL
→ HUMAN OR POLICY ADMIT
→ IMMUTABLE CAPSULE
→ OPTIONAL REBUILDABLE INDEX
→ EXPIRY / DELETE / EXPORT RECEIPT
```

Never store private chain-of-thought. Store externalized rationale, observations, alternatives, evidence refs and falsifiers.

Current state: `NOT_IMPLEMENTED`.

## 19. Missing worker-fleet state machine

```text
CAPABILITY REQUEST
→ WORKER PROBE
→ VERSION / ADAPTER PIN
→ WORKSPACE LEASE
→ CONTEXT MATERIALIZATION
→ EXECUTE
→ STREAM NORMALIZED EVENTS
→ COLLECT ARTIFACTS
→ CANCEL / TIMEOUT / KILL GROUP
→ DISPOSE + RESIDUE RECEIPT
```

Workers:

```text
Grok Build
OpenCode
Pi
Codex CLI
Claude Code
Ante
```

Current state: compatibility contracts exist; live matrix `NOT_EXERCISED`.

## 20. Missing observability and Harness console state machine

```text
CANONICAL EVENT / ARTIFACT REF
→ REDACTION
→ TRACE / METRIC PROJECTION
→ EVIDENCE INSPECTOR
→ HUMAN DECISION FORM
→ SIGNED DECISION RECEIPT
→ LOOPX REDUCER
```

A UI button never writes state directly.

Current state: `NOT_IMPLEMENTED`.

## 21. Cross-machine invariants

```text
README explains; manifest/contracts decide
strategy proposes; LoopX commits
worker executes; gates decide
memory suggests; current authority wins
provider returns candidates; readback verifies
checkpoint/cache/index/UI are projections
Human admits merge/promotion/exception/rollback
```

Validation:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_context.py check
python3 scripts/arena_proof.py check
```
