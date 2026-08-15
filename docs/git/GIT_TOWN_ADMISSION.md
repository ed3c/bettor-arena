# Git Town executable and configuration admission

## Decision

Git Town is **not currently admitted** as a Bettor runtime dependency.

```text
shared procedure reference     PINNED
repository adoption docs       IMPLEMENTED
typed controller               IMPLEMENTED by PR #133
physical fail-closed controls  PASS (13 real-repository controls)
binary                         ABSENT
version/checksum               ABSENT
license/SBOM/legal             NOT_REVIEWED
.git-town.toml                 ABSENT
local sync                     NOT_EXERCISED
remote publication             NOT_EXERCISED
```

The repository uses molecular Stack semantics, a typed controller and GitHub metadata without claiming a live Git Town installation. Controller PASS proves policy enforcement around the absent-executable lane; it does not prove `git town` behavior.

## Why admission is separate

The shared Skill fixes the method boundary, but executable use also changes:

```text
branch ancestry
rebase behavior
conflict state
worktree lifecycle
remote publication risk
rollback surface
```

That requires its own terminal leaf, controls and Human review.

## Admission State Machine

```text
SOURCE SELECTED
→ IMMUTABLE RELEASE PINNED
→ ARCHIVE/BINARY DIGEST VERIFIED
→ DIRECT LICENSE REVIEWED
→ TRANSITIVE LICENSES + SBOM REVIEWED
→ LEGAL ACCEPTED
→ ISOLATED VERSION PROBE
→ REPO PROFILE FIXTURE
→ SIBLING SYNC CANARY
→ TRUE-CHILD RESTACK CANARY
→ CONFLICT STOP CANARY
→ NO-PUSH CANARY
→ CONFIG CANDIDATE
→ HUMAN ADMIT
→ ENABLED
```

Any failure stops the process. No automatic fallback to an unpinned package or mutable latest release.

## Required supply-chain receipt

A future receipt must contain:

```yaml
schema: bettor-arena/git-town-admission/v1
source_repository: exact URL
release_tag: immutable tag
release_commit: 40-hex commit
archive_sha256: 64-hex digest
binary_sha256: 64-hex digest
version_output_sha256: 64-hex digest
direct_license:
  identifier: reviewed SPDX identifier
  file_sha256: 64-hex digest
transitive_licenses:
  status: reviewed
sbom:
  format: SPDX or CycloneDX
  sha256: 64-hex digest
legal_decision:
  authority: Human
  state: accepted | rejected
execution:
  environment: disposable
  exit_code: integer
cleanup:
  state: PASS
```

No executable-admission receipt exists today.

## Configuration admission

`.git-town.toml` must not be added until executable admission passes.

A future configuration candidate must encode:

```text
main as the perennial branch
feature branch sync strategy
no automatic push
no automatic ship
no automatic branch deletion
conflict stop-and-return-control
repo-owned branch naming
worktree/receipt paths as logical references
```

The configuration must have:

```text
positive fixture
unknown-field rejection
mainline rewrite control
dirty worktree control
duplicate branch control
conflict control
no-push control
rollback subject
```

## Live canary matrix

| Canary | Required observation | Current state |
|---|---|---|
| version | exact binary and version digest | `NOT_EXERCISED` |
| sibling sync | two path-disjoint branches | `NOT_EXERCISED` |
| child restack | child consumes parent bytes | `NOT_EXERCISED` |
| conflict | stop without semantic resolution | `NOT_EXERCISED` |
| dirty worktree | refusal without mutation | `NOT_EXERCISED` |
| no push | no remote ref change | `NOT_EXERCISED` |
| cleanup | no orphan worktree/process | `NOT_EXERCISED` |
| rollback | exact subject restoration | `NOT_EXERCISED` |

Repository-controller verification is separate:

```sh
sh tests/git-town/run-all.sh
```

It passes contract/selftest checks and 13 physical controls while the public port returns the stable executable-absent result.

## Publication separation

Even after local admission:

```text
git town sync PASS
  does not create
GitHub publication PASS
  does not create
merge / release promotion
```

GitHub exact-head checks and Human Admit remain separate.

## Current repository profile

Read [`REPO_PROFILE.md`](REPO_PROFILE.md). The profile intentionally declares:

```text
binary_state: ABSENT
configuration_state: ABSENT
push_default: false
merge/ship: HUMAN-OWNED
```

## Unblock criteria

Git Town may move from executable `ABSENT` to runtime candidate only after:

1. exact executable source/release/digests are named;
2. license/SBOM/legal review is attached;
3. wrapper uses typed executable + `argv[]`, never shell strings;
4. isolated positive/control/mutation tests pass;
5. conflict returns control without mutation;
6. remote refs are proven unchanged;
7. cleanup and rollback receipts exist;
8. repository profile and Stack index are updated;
9. exact-head GitHub checks pass;
10. Human Admit records the activation decision.

## Remaining non-goals of the current mechanism

- install Git Town;
- select a package manager;
- create `.git-town.toml`;
- execute sync;
- create or remove worktrees;
- change remotes;
- push, merge, ship, close or delete;
- resolve conflicts;
- promote or rollback.

Issue #101 / PR #133 implemented the admission controller, not the admitted third-party executable.

Observed: `2026-08-15T16:50:16Z`.
