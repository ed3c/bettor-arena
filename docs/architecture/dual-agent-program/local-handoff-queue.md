# Local Handoff Execution Queue

This queue contains only work that needs a local, cloud, provider, credential, network, target, cleanup, or Human authority unavailable to a public deterministic GitHub fixture.

Every executor must rebind current exact subjects before starting. A historical SHA in `stack-index.json` is a trace input, not automatic admission.

## Queue order

### LH-01 — Current-main deterministic Stack admission

**Owner:** repository-local Tech Lead / Git Town controller  
**Repositories:** `runtime-env`, `bettor-arena`, `agent-shield-monorepo`

For each minimal convergence path in `merge-review.md`:

1. fetch current main and all open PR heads;
2. inspect changed paths, true-child dependencies, review threads and required checks;
3. restack/retarget one minimal convergence path;
4. regenerate repository-owned projections rather than selecting generated files manually;
5. rerun exact-head repository gates;
6. merge only the convergence path;
7. close absorbed leaves as superseded;
8. update parent Issues with merge commit, rollback subject and remaining live states.

**Required output:** exact merge receipts and updated repository README/AGENTS/Stack indexes.

### LH-02 — Physical transport reconnect

**Owner:** `ed3c/runtime-env#73`  
**Depends on:** admitted runtime contract/transport candidate

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

Do not call hermetic adapter CI a physical reconnect PASS.

### LH-03 — Live workload identity and policy

**Owner:** `ed3c/runtime-env#83`  
**Depends on:** admitted identity contract/local/cloud/policy candidates

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

### LH-04 — Live network and sandbox

**Owners:** `ed3c/agent-shield-monorepo#95` and `#173`

Run the selected Linux/gVisor environment with exact executable/image/SBOM/kernel/policy subjects. Exercise filesystem, process, capability, resource, DNS/IP and egress controls; timeout/cancel; descendant/container/workspace/socket cleanup.

Package/source presence is not isolation evidence. Local process sandbox evidence cannot proxy gVisor OCI isolation.

### LH-05 — Live API-first/browser fallback

**Owner:** `ed3c/agent-shield-monorepo#161`

Select a safe public/non-production target with terms and egress review. Run:

```text
admitted typed API positive route
or typed API refusal/absence
→ bounded browser fallback only when policy permits
→ exact observation/artifact/readback
→ cleanup
```

Do not use a personal signed-in session. Keep API and browser evidence separate.

### LH-06 — Reversible effect/readback

**Owner:** `ed3c/bettor-arena#223`

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

### LH-07 — Physical local→cloud→local canary

**Owner:** `ed3c/bettor-arena#186`

Compose LH-02 through LH-06 around one useful monitoring job:

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
→ HUMAN_REVIEW
```

Required denominator includes duplicate packet, cloud retry/restart, stale source/policy/runtime/result, timeout/cancel, failed/skipped attempts and cleanup failures.

### LH-08 — Independent real-bundle verification

**Owner:** `ed3c/truth-verify-loop#22`

Ingest the complete LH-07 bundle. Independently:

- re-fetch/read back source and artifacts;
- verify delivery/workflow/restart lineage;
- verify effect/idempotency/readback/compensation lineage;
- verify provider/route/user/cleanup lane separation;
- preserve every retry, duplicate, timeout, cancellation and failure;
- run the merged deterministic technical matrix;
- invoke the existing semantic plane only with admissible semantic evidence.

Technical consistency alone remains `UNVERIFIABLE`.

### LH-09 — Human Admit, release and rollback

**Owner:** Human/trusted release authority; convergence issue `ed3c/bettor-arena#68`

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
