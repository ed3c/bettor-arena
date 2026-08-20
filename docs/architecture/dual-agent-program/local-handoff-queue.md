# Local Handoff Execution Queue

This queue contains work that needs a local, cloud, provider, credential, network, target, cleanup, or Human authority unavailable to a public deterministic GitHub fixture.

Every executor must rebind current exact subjects before starting. A historical SHA in `stack-index.json` is a trace input, not automatic admission.

## Admitted deterministic bases

```text
runtime-env main
baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7
tree 117901dbd77cc93993ddc388682b7ab26a00d544

bettor-arena main
74d1e75c61589dcd163c7412e1345f726781ffb4
tree 0de94032a3227ad04dde52f138041294ef9cb810

agent-shield-monorepo current main
30e12cc917503b56b002aa7351428811f20fea8e
tree 6f465f936515d81ed51c5b80595de530593f25fc
```

## Queue order

### LH-01 — Remaining deterministic Stack admission

**Owner:** `ed3c/agent-shield-monorepo` Tech Lead / Git Town controller  
**State:** `RUNTIME_AND_BETTOR_COMPLETE / AGENT_SHIELD_PENDING`

Runtime and Bettor Workflow/Effect deterministic Stacks are admitted. The remaining deterministic merge work is:

```text
Route
#162 → #166 → #167
absorb #163/#164/#165

GVisor
#174 → #177 → #178
absorb #175/#176

Shared non-promoting candidate
#180 after route/gVisor/local-sandbox inputs are current
```

Execution:

1. fetch Agent Shield current main and all open PR heads;
2. inspect changed paths, true-child dependencies, review threads and required checks;
3. restack/retarget one minimal convergence path to current main;
4. rerun exact-head contract, matrix, docs and repository gates;
5. merge only the minimal convergence path;
6. close exact-byte absorbed leaves without a second merge;
7. update #135, #144, #147 and this cross-repo index;
8. keep #95/#161/#173 open.

**Required output:** Agent Shield exact merge receipts and updated provider README/AGENTS/Stack indexes.

### LH-02 — Physical transport reconnect

**Owner:** `ed3c/runtime-env#73`  
**Parent:** `ed3c/runtime-env#58`  
**Exact deterministic base:** `baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7`

Execute a real NATS/JetStream or selected transport environment:

```text
offline durable enqueue
→ local process restart
→ reconnect
→ intentional duplicate/redelivery
→ cloud delivery
→ result return
→ second local restart
→ inbox/projection rebuild
→ cleanup/residue readback
```

Capture server/client/config identity, TLS handle references, stream/consumer state, attempts, ACK timing, stale result controls, WAL/DB/socket/process cleanup and retained durable state.

Idempotency: one logical packet and one accepted logical result; at-least-once delivery stays explicit.

Do not call hermetic adapter CI a physical reconnect PASS.

### LH-03 — Live workload identity and policy

**Owner:** `ed3c/runtime-env#83`  
**Parent:** `ed3c/runtime-env#59`  
**Exact deterministic base:** `baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7`

Use distinct local and cloud identities. Exercise enrollment/attestation, audience checks, opaque secret resolution, policy epoch drift, revocation, expiry, rotation/reissue, reconnect-time revalidation and cleanup.

Required refusal controls:

```text
wrong audience
local identity reused as cloud
stale policy
revoked identity
expired lease
raw secret leakage
transport auth used as task authorization
```

Transport mTLS is not execution authorization. Provider/package presence is not enrollment evidence.

### LH-04 — Live network and sandbox

**Owners:** `ed3c/agent-shield-monorepo#95` and `#173`  
**Depends on:** LH-01 Agent Shield admission

Run the selected Linux/gVisor environment with exact executable/image/SBOM/kernel/policy subjects. Exercise filesystem, process, capability, resource, DNS/IP and egress controls; timeout/cancel; descendant/container/workspace/socket cleanup.

Package/source presence is not isolation evidence. Local process sandbox evidence cannot proxy gVisor OCI isolation.

### LH-05 — Live API-first/browser fallback

**Owner:** `ed3c/agent-shield-monorepo#161`  
**Depends on:** LH-01 route admission and admitted network/sandbox policy

Select a safe public/non-production target with terms and egress review. Run:

```text
admitted typed API positive route
or typed API refusal/absence
→ bounded browser fallback only when policy permits
→ exact observation/artifact/readback
→ cleanup
```

Do not use a personal signed-in session. Keep API and browser evidence separate.

### LH-06 — Live durable-workflow engine

**Owner:** `ed3c/bettor-arena#184`  
**Exact deterministic base:** `74d1e75c61589dcd163c7412e1345f726781ffb4`  
**Packet:** `LH-WF-001`

Use an authorized disposable Temporal or equivalent durable-workflow environment. Pin exact workflow code/tree, namespace/queue, Worker build, runtime contract set, policy and provider subjects.

Required execution:

```text
submit exact job
→ restart Worker during retry
→ restart during timer
→ restart during WAITING_FOR_HUMAN
→ scoped Human approval/refusal
→ cancellation/deadline propagation
→ stale source/runtime/policy refusal
→ write routed only through Effect Plane
→ cleanup/residue readback
```

Retain every workflow/activity/attempt event and byte-identical replay digest. Fresh-process fixture replay is not live engine failover.

### LH-07 — Reversible effect/readback

**Owner:** `ed3c/bettor-arena#223`  
**Parent:** `ed3c/bettor-arena#185`  
**Exact deterministic base:** `74d1e75c61589dcd163c7412e1345f726781ffb4`

Execute one safe reversible write with:

```text
exact effect identity
+ idempotency reservation
+ policy/Human/precondition admission
+ real provider attempt
+ intentional duplicate/redelivery
+ exact target readback
+ at most one accepted commit
+ linked compensation when admitted
+ cleanup/residue inventory
```

`RESULT_UNKNOWN` must trigger reconciliation; it cannot become committed by timeout inference.

### LH-08 — Physical local→cloud→local canary and independent verification

**Execution owner:** `ed3c/bettor-arena#186`  
**Verification owner:** `ed3c/truth-verify-loop#22`

Compose LH-02 through LH-07 around one useful, public/test-safe monitoring job:

```text
LOCAL_REQUESTED
→ OUTBOX_COMMITTED_OFFLINE
→ LOCAL_RESTART
→ TRANSPORT_RECONNECT
→ CLOUD_WORKFLOW
→ IDENTITY/POLICY_REVALIDATION
→ SANDBOX_READY
→ API_ROUTE | BROWSER_FALLBACK
→ RESULT_AND_ARTIFACT
→ LOCAL_INBOX
→ SECOND_LOCAL_RESTART
→ USER_RESULT_VERIFIED
→ OPTIONAL_EFFECT_DISPOSITION
→ CLEANUP_VERIFIED
→ INDEPENDENT_VERIFICATION
→ HUMAN_REVIEW
```

Required denominator includes duplicate packet, cloud retry/restart, stale source/policy/runtime/result, timeout/cancel, failed/skipped attempts and cleanup failures.

Truth Verify Loop must independently:

- re-fetch/read back source and artifacts;
- verify delivery/workflow/restart lineage;
- verify effect/idempotency/readback/compensation lineage;
- verify provider/route/user/cleanup lane separation;
- preserve every retry, duplicate, timeout, cancellation and failure;
- run the merged deterministic technical matrix;
- invoke the existing semantic plane only with admissible semantic evidence.

Technical consistency alone remains `UNVERIFIABLE`.

### LH-09 — Human Admit, release and rollback

**Owner:** Human/trusted release authority  
**Convergence issue:** `ed3c/bettor-arena#68`

Review target terms, egress, data classification, credentials, provider cost, physical receipts, independent closure, residual risks, SBOM/license notices, rollback subject and cleanup. Record an explicit decision:

```text
ADMIT
REFUSE
DEFER
ROLLBACK
```

No Agent, fixture, CI, README or mergeable PR may perform this transition.

## Completion packet for every queue item

```text
repository / issue / PR
exact base / head / tree / rollback
runtime / provider / policy / schema / image subjects
commands or workflow identity
typed state-transition history
positive and planted disagreement results
all failed / timed-out / skipped attempts
artifact and readback digests
cleanup and residue inventory
evidence ceiling
remaining NOT_EXERCISED lanes
Human decision when required
```
