# Bettor Arena Git Town repository profile

Status vocabulary:

```text
PINNED
IMPLEMENTED
ABSENT
NOT_SELECTED
NOT_REVIEWED
NOT_EXERCISED
NOT_PERFORMED
AUTOMATION-POLICY-OWNED
```

## Repository identity

```yaml
schema: git-town-stacked-pr-worker/repo-profile/v1
repository_full_name: ed3c/bettor-arena
repository_id: 1330387399
visibility: private
default_branch: main
perennial_branches:
  - main
authoring_remote_name: forgejo
authoring_remote_url_pattern: '^http://localhost:3000/neon/bettor-arena(?:\.git)?$'
distribution_remote_name: github
distribution_remote_url_pattern: '^(?:git@github\.com:|https://github\.com/)ed3c/bettor-arena(?:\.git)?$'
current_github_main_observed: c72109e145193fdaf059944403477f01064a1c3d
current_local_forgejo_main_observed: 8d47fc1c9dfd1550c1f45504f6c11fc1f04f6a0b
current_tree_observed: 0c51ea279bd2036dce281898c2e980e8378ba1cb
current_relation: same-tree observation; tracked equivalence receipt remains NOT_EXERCISED
```

An operation using a remote outside its declared authoring/distribution role, a credential-bearing URL, mutable mirror alias or unreviewed perennial branch is `PROFILE_INVALID`.

## Canonical shared Skill

```yaml
repository: ed3c/skills-shared
commit: c5750720d960a228a0d9419f28125c09d064e3e1
blob: eb2d915bca3e8a3938625f7d33a10fae95a15769
path: skills/git-town-stacked-pr-worker/SKILL.md
reference_state: PINNED
consumer_requirements_selection: NOT_SELECTED
consumer_binding_selection: NOT_SELECTED
local_same_name_skill: ABSENT
```

The exact reference is usable for design review. Runtime use through the Bettor shared-Skill binding remains `NOT_SELECTED` until an explicit binding update and closure check land in a separate leaf.

The current Bettor binding pins `skills-shared@b3c722da1c40301b0a12e0ef99848d884bfc720b`; its same path resolves to the same blob above. This proves source-byte compatibility, not runtime selection.

## Git Town executable admission

```yaml
binary_state: ABSENT
version: ABSENT
source_repository: NOT_SELECTED
immutable_release: ABSENT
archive_sha256: ABSENT
binary_sha256: ABSENT
direct_license: NOT_REVIEWED
transitive_licenses: NOT_REVIEWED
sbom: ABSENT
legal_acceptance: NOT_PERFORMED
configuration_file: ABSENT
configuration_state: ABSENT
live_sync_state: NOT_EXERCISED
```

Do not infer installation from the Skill reference, Git Town vocabulary, branch graph or a developer’s machine.

## Synchronization policy

These are proposed safe defaults, not executed configuration:

```yaml
feature_branch_strategy: rebase-after-admission
perennial_branch_strategy: fast-forward-only
push_default: false
remote_sync_default: false
semantic_conflict_policy: stop-and-return-control
continue_skip_undo_authority: typed-controller-only
merge_ship_close_delete_authority: automated-admission-controller
automatic_branch_creation: denied-until-task-packet
automatic_branch_deletion: denied
```

## Worker and worktree policy

```yaml
primary_checkout_write: denied
linked_worktree_required: true
one_worker_one_worktree: true
one_worker_one_branch: true
one_worker_one_path_lease: true
branch_root: host-owned
worktree_root: host-owned
state_root: data/git-town
receipt_root: data/git-town/receipts
runtime_state: IMPLEMENTED_FAIL_CLOSED
receipt_state: IMPLEMENTED; live Git Town receipt NOT_EXERCISED
```

The roots above are logical contract names. No absolute host path is stored in Git.

## Task packet

Required fields:

```yaml
parent_issue: required
goal: required
non_goals: required
base_branch: required
parent_branch: required
head_branch: required
stack_class: sibling | true-child | terminal | convergence
allowed_paths: required
excluded_paths: required
dependencies: required
parallel_safe_siblings: required
required_evals: required
negative_or_mutation_controls: required
evidence_boundary: required
cleanup_contract: required
rollback_subject: required
automation_owned_operations: required
```

Missing fields produce `PACKET_INVALID`.

## Path lease policy

```yaml
lease_identity:
  - issue
  - branch
  - linked_worktree
  - allowed_paths
conflict_rule: overlapping active leases are blocked unless one is a declared true child and sequencing is explicit
generated_files_rule: one convergence owner; terminal leaves may receive bot-generated projections but do not manually edit them
duplicate_issue_rule: multiple active implementations for one issue are BLOCKED_DUPLICATE_TERMINAL
```

Observed conflict:

```text
issue #64
PR #76 feat/loopx-worker-gateway-v1
PR #77 feat/loopx-worker-gateway-terminal-v1
overlap: loop_wiki/loopx-worker-gateway/** and module/generated paths
state: RESOLVED_BY_HUMAN
resolution: PR #76 admitted; PR #77 superseded; issue #82 completed residual disposition
```

## Evaluation policy

Required zero-network governance checks:

```sh
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
python3 -m unittest -q tests/test_git_town_stack_docs.py
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_readme_coverage.py
```

Future executable admission also requires:

```text
version/checksum/license/SBOM verification
repository profile fixture
sibling sync positive case
child restack positive case
conflict stop-and-return-control case
mainline rewrite control
duplicate branch/path lease control
dirty worktree control
publication boundary control
rollback evidence
```

## Publication policy

```yaml
enabled: policy-admitted; exact runtime controller still required
github_is_publication_authority: true
exact_head_required: true
all_required_checks_required: true
billing_policy: NOT_DEFINED_FOR_GIT_TOWN
push: AUTOMATION-POLICY-OWNED
merge: AUTOMATION-POLICY-OWNED
ship: AUTOMATION-POLICY-OWNED
promotion: AUTOMATION-POLICY-OWNED
rollback: AUTOMATION-POLICY-OWNED
```

Local Git Town sync, when admitted later, does not prove GitHub publication.

## Evidence policy

```yaml
snapshot_authority: GitHub API plus repository bytes
snapshot_freshness: invalidated by branch/base/head/state/check changes
merged_to_parent_is_main: false
fixture_pass_is_live_pass: false
source_visibility_is_execution: false
generated_prose_is_receipt: false
```

## Current adoption state

```text
repository profile              IMPLEMENTED
Stack Markdown and machine queue IMPLEMENTED; active #92
Agent routing                   IMPLEMENTED
deterministic doc gate          IMPLEMENTED
typed runtime controller        IMPLEMENTED by PR #133
13 physical controls            PASS with executable-absent lane

shared Skill binding            NOT_SELECTED
Git Town binary                 ABSENT
.git-town.toml                  ABSENT
local sync                      NOT_EXERCISED
remote publication              NOT_EXERCISED
automated-admission policy      ADMITTED; exact operation NOT_EXERCISED
```

## Rollback boundary

Current documentation repair starts from:

```text
local/Forgejo subject: 8d47fc1c9dfd1550c1f45504f6c11fc1f04f6a0b
GitHub subject: c72109e145193fdaf059944403477f01064a1c3d
tree: 0c51ea279bd2036dce281898c2e980e8378ba1cb
```

Rollback is an automated-admission operation bound to exact before/after subjects.
The policy never authorizes raw reset, force-push, deletion or history rewrite.

Observed: `2026-08-15T16:50:16Z`.
