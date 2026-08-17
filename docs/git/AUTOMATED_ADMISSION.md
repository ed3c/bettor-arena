# Automated admission

This file is the authority SSOT for automated push, merge, queue advancement,
provider activation, promotion and rollback in `ed3c/bettor-arena`.

## Standing authorization

The repository owner grants standing authorization for an Agent to complete these
operations without a per-operation confirmation prompt when every required input is
present and current. Authorization applies to one exact repository, issue, base,
head and rollback subject. It does not transfer across repositories or stale heads.

```text
candidate bytes
→ local positive/control/mutation verification
→ clean worktree and bounded cleanup receipt
→ one meaningful publication transition
→ exact-head required checks and review-thread readback
→ typed admission controller
→ push / merge / queue advance / provider activate / promote / rollback
→ remote readback and immutable receipt
```

## Required inputs

Every automated operation requires:

- runtime identity and repository ownership evidence;
- the active issue/task packet, single-writer branch lease and path lease;
- exact base, head, tree and rollback subjects;
- current positive, independent control and planted mutation evidence;
- a clean diff review and bounded artifact/cleanup receipt;
- required exact-head checks with no unresolved review thread;
- a typed controller using compare-and-swap or an equivalent expected-subject guard;
- post-operation remote/source readback and a durable receipt.

Provider activation additionally requires an allowlisted provider manifest, pinned
version and artifact digest, license/SBOM disposition, secret references rather than
secret values, explicit data scope, spend/quota ceiling, live canary, cleanup and
rollback procedure. A provider/model response cannot satisfy any of these fields.

## Controller routes

```text
commit/push/publication  github-delivery-loop publication controller
merge                    github-delivery-loop merge_gate expected-head land
queue advancement        LoopX reducer + pdf-terminal-sequence gate
provider activation      nearest module's named typed activation controller
promotion/rollback       release controller bound to release and rollback subjects
```

Generic shell strings, force push, no-op push, raw provider commands and direct
canonical-state writes are controller bypasses and fail policy.

## GitHub Actions conservation

- Keep repair commits local until the meaningful publication transition.
- Publish each changed head once; do not push merely to retrigger CI.
- Reuse successful exact-head runs and rerun only failed jobs classified as transient.
- A child-to-parent merge and a parent-to-main merge are distinct heads; each gets at
  most one required check batch. One stale run cannot prove the later subject.
- Read back the final remote head before queue advancement.

## Conflict policy

Path-disjoint changes and generated files with a single declared generator owner may
be resolved automatically. A semantic conflict needs a deterministic winner already
declared in the task packet or machine policy. Otherwise the controller records
`CONFLICT`, updates the owning issue and stops. Stopping is fail-closed automation,
not a request for an implicit human verdict.

Standing authorization automates the operation, not the creation of missing intent.
HITL decisions, source/licence rights, credential or permission changes, and any
semantic choice absent from policy remain external inputs. The controller may verify
and apply such an input; it must not invent or silently broaden it.

## Outcomes

```text
ADMITTED          exact operation completed and read back
BLOCKED_POLICY    a required policy input is absent, stale or red
CONFLICT          no deterministic semantic winner exists
FAILED            controller ran and the checked operation failed
NOT_IMPLEMENTED   the named typed controller does not exist
NOT_EXERCISED     the controller exists but has not run for this exact subject
```

Documentation gates alone never produce `ADMITTED`.

## Contract migration

This policy changes the current queue and Stack contracts to v2:

```text
human_boundary          → automation_boundary
human_owned_operations  → automation_owned_operations
human_admit             → automation_policy
```

Historical facts such as `RESOLVED_BY_HUMAN` and their original authority remain
unchanged. They describe what happened; they do not control new operations.
