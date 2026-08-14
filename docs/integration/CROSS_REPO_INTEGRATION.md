# Four-repository modular integration — bettor acceptance view

## Ownership planes

| Repository | Plane | Owns | Must not own |
|---|---|---|---|
| `skills-shared` | Instruction / Method | portable procedural Skills, generic contracts, Skill eval/evolution truth | product/provider state, consumer branches/secrets |
| `runtime-env` | Runtime Contract | secret-free variables/modules/profiles/workloads/policies and consumer bindings | secret values, generic shell, product semantics |
| `bettor-arena` | Integration / Acceptance | module composition, proof/control/mutation, Context Capsules, stateless MCP, bootstrap, origins, external-release acceptance | domain product implementation, hidden live checkout dependencies |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | product modules, provider adapters, product state machines, exact domain canaries | canonical shared Skill bodies or generic runtime catalog |

## Contract data flow

```text
skills-shared immutable Skill release
        |
        +--> .agents requirements/binding
        |
runtime-env requirements → secret-free binding/workload/policy
        |                         |
        +------------+------------+
                     v
bettor .arena module/composition locks
+ module proof subjects
+ Context Capsules
+ CLI/MCP/bootstrap release
                     |
                     v
Agent Shield remote-consumer or embedded-module initialization
                     |
                     v
Claude/Codex/origin/browser/provider/product canary receipts
                     |
                     v
bettor external-release acceptance
                     |
                     v
Human promotion or rollback
```

## Channel separation

```text
Skill symlink / editable checkout = local development channel
immutable commit/tree/release + binding/lock = reproducible channel
loopctl / stateless MCP = public consumption channel
```

No mutable sibling checkout, secret file, browser profile, device session, or owner temp state becomes a release dependency. Forgejo authoring and GitHub distribution equivalence require exact receipts.

<a id="private-github-local-forgejo-delivery-loop"></a>

## Private GitHub → local Forgejo delivery loop

This is the canonical state machine for a new private repository that must be available to the ChatGPT/Codex GitHub integration and GitHub Actions while local implementation remains Forgejo-first. GitHub is the cloud distribution and Actions origin; Forgejo is the local authoring origin. Neither mutable `main` branch is release identity.

```text
private GitHub bootstrap + ChatGPT/Codex repository authorization
→ exact baseline mirrored to Forgejo
→ Forgejo issue → isolated worktree → tests/review → Forgejo PR
→ standing owner admit → automatic Forgejo merge → local main fast-forward
→ GitHub publication PR → exact-head Actions
→ bounded GitHub issue/PR reconciliation
→ accepted GitHub-only changes sync back by Forgejo issue/PR
→ exact commit/tree/release-manifest equivalence receipt
```

### 1. Bootstrap the two origins

1. Create the GitHub repository as private. Add the root `AGENTS.md`, least-privilege Actions workflows, branch protection, and required checks before treating it as a runtime. Workflow actions are pinned to immutable revisions; secrets remain in GitHub's secret boundary and never enter repository files, prompts, logs, or receipts.
2. In ChatGPT/Codex, install or enable the GitHub integration, grant it access to this exact private repository, and configure Codex cloud/code review only after repository-owner authorization. Connected repository access does not imply permission to mutate branches or read Actions logs. Codex review setup and private-repository access remain human-owned ([official GitHub integration guide](https://learn.chatgpt.com/docs/third-party/github)).
3. Clone or attach the local checkout with explicit remotes named `github` and `forgejo`; avoid an ambiguous `origin`. Create the local Forgejo repository as the authoring origin and mirror the exact initial commit/tree from GitHub. Record both immutable repository identities, roles, commits, trees, and release-manifest digests in the origin contract; keep Forgejo and GitHub delivery evidence in their host-specific registries/receipts rather than inserting GitHub addresses into the Forgejo-only registry.
4. Verify the local main checkout stays on `main`. Work branches live only in standard Git worktrees or ChatGPT desktop managed Worktrees. The CLI may enter an existing standard worktree with `codex -C <path>`; it does not create a desktop-managed Worktree.

### 2. Forgejo-first implementation

1. The implementation queue is the registered Forgejo PRD/milestone and its open slice issues. One issue owns one acceptance boundary and one idempotency marker.
2. For each admitted issue, create an isolated worktree at the start, implement in small testable commits, run the issue's verification and negative control, self-review the diff, and open a Forgejo PR whose body contains `Closes #N`.
3. The repository owner has supplied standing Human Admit for this declared loop. After required current-head receipts are complete, commit gates and review are green, and any contract-declared checked-red evidence is explicitly reported, commit and push normally, merge the PR to `forgejo/main` without another confirmation prompt, then fast-forward the local main checkout. A worktree result, green model response, or local test alone still cannot authorize merge.
4. New findings become a new Forgejo issue under the same milestone. Do not expand the active PR or silently rewrite the original acceptance criteria.

### 3. Three-strike root-cause escalation

"Three failures" means three materially different attempts against the same failure signature or acceptance criterion. Each attempt records the exact subject, command/action, exit/error, evidence location, current hypothesis, and why it failed. A retry with no changed hypothesis or external state does not consume a new attempt because it contributes no new evidence.

After attempt three:

1. Stop modifying the implementation. Open or reuse the idempotent owner issue first: Forgejo for local authoring/code failures; GitHub for a GitHub Actions or GitHub-distribution-only failure. If a GitHub failure requires local code work, create one linked Forgejo implementation issue and keep the GitHub item as the distribution/CI record rather than duplicating acceptance truth.
2. Create a repo-contained root-cause handoff, not a short issue comment. It contains exact local/GitHub/Forgejo repository identities, commit/tree/index subject, the complete three-attempt ledger, raw log/receipt paths and key excerpts, governing invariants, curated source entrypoints, reproduction commands, suspected abstraction error, counterevidence, GitHub PR/commit history anchors, checkable acceptance criteria, output artifacts, and delivery/stop conditions. Exclude secrets and signed-in session material. Put the handoff path plus digest on the owner issue so the issue is an index rather than a lossy copy.
3. Start a fresh ChatGPT desktop chat from that packet. The prompt explicitly says `Use the GitHub connector`, names the exact private `owner/repo`, requests repository/history/PR research, and identifies which GitHub PRs must receive the resulting solution. Current Codex CLI supports `codex app <repo>` to launch the desktop workspace; the canonical `codex://threads/new?prompt=...&path=...` deep link can prefill a new chat but does not submit it ([official CLI command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-app), [official desktop deep links](https://learn.chatgpt.com/docs/reference/commands#deep-links)). The operator must press Send/Return when the App requires it. Do not claim connector-backed research started until the submitted chat reads back the named repository; if UI automation is unavailable or disallowed, record that manual send as the remaining human-interface step instead of treating prefill as delivery. A deep link is navigation only; connector access plus the repo-contained packet provide the data plane. Context isolation is not independent verification.
4. Search current source/tests/logs first and use the GitHub connector against the named repository for private issue/PR/commit context. For unstable external claims, invoke `external-verify` and pull official primary material. For a cross-family independent replay, resolve the current `agy models` inventory and select a high-reasoning model; its output is findings-only. Codex CLI or Claude Code may take a distinct named code/search role, but "Codex or Claude or agy" is not a route. Every dispatch names its visible inputs, semantic role, output artifact, and stop condition.
5. Distinguish an executable failure from an evidence verdict. A proof exit `2` records a checked red result and may still be required input to a lineage lock; exit `64` is the fail-closed contract/tool absence. When refreshing all contract-declared proof receipts, collect every `0` or `2` verdict and continue so the lock sees the complete evidence set; stop on `64`. Never turn a red receipt green merely to unblock a commit.
6. Once root cause is evidenced, start a new desktop Worktree chat for implementation, or have an authorized orchestration step create a standard Git worktree and enter it with `codex -C`. The shared main tree never changes branch. Return to the Forgejo issue/PR path in §2.

### 4. Publish and reconcile GitHub

After the admitted Forgejo changes are on local `main`:

1. Publish the exact local-main subject to a GitHub distribution branch and open/update a GitHub PR. Do not push directly to protected GitHub `main`, and do not silently fall back to a mutable remote branch when an immutable subject is missing.
2. Inspect GitHub Actions with `gh` at the exact PR head. The connected GitHub app owns structured repository/issue/PR context; it does not replace `gh` for Actions logs. A CI failure follows `gh-fix-ci`: record the failing check and root cause, bind the fix to an admitted issue, implement under the standing owner authorization, run focused local verification, push the repaired head, and require current-head checks. No per-fix confirmation is required.
3. Snapshot the currently open GitHub issues and PRs into a bounded queue. Process WIP=1 because every merged PR moves the base. Before fixing a conflict, classify the PR as already integrated, superseded, duplicate, actionable, or blocked; close/supersede instead of manufacturing a conflict-resolution commit when its change already landed.
4. For an actionable PR, use a dedicated worktree at its exact head. Prefer merging the current GitHub base into the PR branch so the update is non-destructive; the standing authorization does not include rebase/force-push. Resolve conflicts, run the full applicable checks, commit and push normally when branch permission exists, then merge automatically when required current-head checks and review are green. A fork PR without write permission produces a patch or replacement PR, never an authority workaround.
5. Re-evaluate the remaining queue after every merge. New issues discovered during this pass enter the next queue snapshot; "fix all" is a converging bounded loop, not an unbounded batch mutation.

### 5. Close the loop

If GitHub reconciliation adds any commit not already in Forgejo, GitHub is temporarily ahead and the loop is still open. Open a Forgejo sync-back issue, materialize the exact GitHub subject in a dedicated worktree, run the same proof/control/mutation gates, and automatically commit, push, and merge it through a Forgejo PR under the standing owner admit. Then fast-forward local `main` and regenerate the logical-origin receipts.

### Standing automation authorization

Within the registered repository, milestone, and bounded issue/PR queue, the agent is pre-authorized to create the worktree/branch, edit, test, commit, push, open or update PRs, repair actionable conflicts, merge green PRs, close their bound issues, and perform the required Forgejo↔GitHub sync-back. These normal delivery steps must not pause for another owner confirmation. Process WIP=1 and read back every external mutation before advancing.

The authorization fails closed when required checks remain red, the third materially different repair attempt fails, write permission is absent, branch protection rejects the operation, a conflict has ambiguous product semantics, the only path requires force-push or destructive history/data changes, or secrets/permissions/promotion scope would change. Record the exact blocker on the owner issue; never relabel it as merged or complete.

The terminal condition is not "all commands returned zero." It is:

- admitted Forgejo and GitHub issues/PRs have terminal readback;
- current required GitHub Actions pass at the exact merged subjects;
- local `main`, `forgejo/main`, and `github/main` satisfy an accepted exact-commit, same-tree, or same-release-manifest mode;
- delivery, origin, and equivalence receipts bind that same subject;
- remaining blocked, deferred, or policy-skipped items are explicit rather than counted as done.

## Skill procedural/domain separation

Shared `SKILL.md` contains generalized workflow/method/laws. Shared `references/` contains reusable contracts. Shared `modules/` contains domain examples loaded on demand. Bettor repo-owned bindings select and retarget the procedure without copying the canonical core.

## Source boundary

The attached architecture PDF proposes E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, licensing, cost, performance, and recovery. Those are research inputs. Admission requires independent verification, implementation, evals, canaries, receipts, and Human Admit.
