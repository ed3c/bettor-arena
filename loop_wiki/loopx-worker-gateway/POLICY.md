# Host-neutral execution policy

1. Requests bind exact repository commit/tree, task, Skill and Context Capsule digests.
2. Adapter manifest digest must match the selected static adapter bytes.
3. Only an allowlisted executable plus `argv[]` is accepted.
4. Secret values never enter the request or receipt; secret-shaped environment names are refused and credential handles remain opaque references.
5. Each run uses a detached disposable worktree and new process group.
6. Timeout, explicit cancellation, output budget, write allowlist and cleanup are mandatory observations.
7. A local gateway may report only the attestations it physically enforces. It must fail closed when required physical isolation is unavailable.
8. `OBSERVED_SUCCESS` cannot be promoted to Gate `PASS` without an independent Gate result.
9. Static host registration, source visibility, package installation or fixture execution never creates a live canary.
10. No model, adapter or gateway action can merge, promote, Human Admit or mutate canonical LoopX state.
