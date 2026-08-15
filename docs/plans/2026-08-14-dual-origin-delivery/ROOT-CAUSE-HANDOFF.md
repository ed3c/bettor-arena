# Forgejo #35 root-cause and delivery handoff

This packet is the self-contained handoff for the failed dual-origin policy delivery. A fresh ChatGPT Desktop session must read this file from the local workspace and use the GitHub connector against the named private repository. Forgejo issue comments and GitHub PR comments are indexes and coordination surfaces; they are not substitutes for this evidence packet.

## Task and terminal condition

Research and resolve the lineage failure that prevented the staged dual-origin policy from being committed. Preserve truthful technical-equivalence evidence, commit without bypassing hooks, deliver through Forgejo issue #35 and its PR, then reconcile the GitHub pull-request stack one PR at a time. The terminal state requires readback from both origins and an explicit equivalence status; it is not merely a zero exit code.

## Immutable identities and current subject

| Surface | Identity |
|---|---|
| Local checkout | `<repo-root>` from `git rev-parse --show-toplevel`; its directory name is `bettor-arena` and the shared working tree remains on `main` |
| Base commit | `26dad8c1646746e1da6168257b383f171a2f0aca` |
| GitHub connector target | private repository `ed3c/bettor-arena`, repository ID `1330387399` |
| GitHub remote role | cloud distribution and GitHub Actions |
| Forgejo target | `http://localhost:3000/neon/bettor-arena` |
| Forgejo owner issue | `http://localhost:3000/neon/bettor-arena/issues/35` |
| Attempt-ledger readback | `http://localhost:3000/neon/bettor-arena/issues/35#issuecomment-543` |
| Local authoring role | Forgejo-first; GitHub-only accepted commits must sync back through Forgejo |

The exact candidate is the base commit plus the Git index, not the mutable worktree. Before acting, run `git diff --cached --name-only`, `git write-tree`, and `sha256sum`/`shasum -a 256` on this packet; compare those values with the latest owner-issue receipt. The packet does not embed its own digest or final index tree because either would be self-referential. A stale issue digest is drift, not identity.

The refreshed candidate contains these 15 staged paths (the latest owner-issue receipt binds their final index tree): `.arena/contexts.lock.json`, `.arena/contexts/macro.json`, `.arena/locks/bettor-arena.lock.json`, `.skill-bindings/forgejo-delivery-loop/README.md`, `.skill-bindings/forgejo-delivery-loop/registry.json`, `AGENTS.md`, `CLAUDE.md`, `data/context-capsules/driver-parity.json`, `data/module-proof/release-receipt.json`, `data/module-proof/subjects.lock.json`, `docs/integration/CROSS_REPO_INTEGRATION.md`, this packet, `loopctl/workflow.lock`, `loopctl/workflow_lock.py`, and `proof_workflow/prove_macro_loop.sh`.

## Three-attempt ledger with preserved gaps

Forgejo comment `#issuecomment-543` was read back from the signed-in issue page. Its exact subject was local `main` at `26dad8c1646746e1da6168257b383f171a2f0aca` plus the staged dual-origin policy changes.

The original shell transcript was not retained, so the exact argv and numeric exits below are `ABSENT` unless comment #543 stated them. This packet does not invent them after the fact.

1. **Commit attempt** — action: commit the staged policy through the normal hook; exact commit command and numeric exit: **`ABSENT`**; preserved error: pre-commit lineage rejected `AGENTS.md` because `workflow.lock` did not describe the staged bytes; raw evidence: comment #543 only, original hook stream **`ABSENT`**; hypothesis: the staged workflow bytes lacked a fresh lock; why failed: the gate correctly rejected stale lineage. No hook was bypassed and no commit was created.
2. **Re-lock attempt** — action: restore the missing HEAD post-commit terminus and rerun macro/micro/openwiki proofs; exact commands, numeric exits, and raw streams: **`ABSENT`**; preserved result: those three proofs passed, then the lock builder rejected the stale three-loop hint because the current contract declares agent-runtime and the other prove loops too; raw evidence: comment #543 only; hypothesis: repairing the terminus and those three receipts was sufficient; why failed: a duplicated loop inventory had drifted from `loopctl/contract.json`.
3. **Complete proof-set attempt** — action: run the expanded proof inventory; exact driver argv and full stream: **`ABSENT`**; preserved exits: agent-runtime/container/CTG passed, technical equivalence exited `2`; raw evidence: comment #543 plus the same-subject regenerated receipt paths below; hypothesis: equivalence red blocked commit and required live admission; why failed: that hypothesis conflated receipt completeness with PASS. The ledger said the admitted mirror `PROFILE.md` bytes and `source_profile_sha256` predated the current profile, and that live state was `NOT_EXERCISED`; it then prescribed live Gemini → audit probes → fresh judge → Human Admit. The stale offline mirror was already **`EXERCISED_FAIL` with `hard_drift`**, while only the live carrier/judge/admit lanes were `NOT_EXERCISED`.

The issue ordered a stop after attempt three. No commit, push, PR, or merge occurred; the staged patch was retained for this issue-bound session. The missing historical argv/streams remain `ABSENT` in the final report; current reruns prove the repaired mechanism but cannot retroactively manufacture the old transcript.

## Why the prior handoff failed

The prior Desktop deep link carried only a task sentence and the Forgejo URL. That forced the new session to reconstruct repository identity, hidden local evidence, GitHub history, proof semantics, and delivery responsibility from memory. It also stated the wrong prerequisite: “make equivalence green before commit.”

Repository evidence says the opposite:

- `proof_workflow/README.md` states that `workflow lock` requires each receipt to exist but does not require a green verdict; the commit gate requires a fresh lock.
- `loopctl/workflow_lock.py` derives all required proof names from `loopctl/contract.json` and reads receipt steps without rejecting a receipt whose proof verdict is red.
- `proof_workflow/control_workflow_lineage.sh` intentionally runs every contract-declared proof without aborting the loop on exit `2`, then builds the lock.
- GitHub commit `24510a4633effe38e02b70f564d7ea1b5729c43b` records that equivalence stayed red while three commits landed. Commits `f45a8b79fb2dbd63ac1076d72e312792c862086a` and `539adfa4e589e654e327405869e973e0297dc5c7` preserve the same boundary.
- GitHub PR #26 records that the live Gemini/Judge/Human-admit path remained separately blocked while ordinary repository repairs and regenerated lineage locks were delivered.

Two executable defects were then evidenced:

- The repair driver used `|| exit $?`. Technical equivalence returned the expected checked-red exit `2`, so the driver aborted before producing the remaining proof receipts and `workflow.lock`. This was misreported as “equivalence blocks commit.”
- `loopctl/workflow_lock.py::commit_bytes()` accepted non-empty stdout from a failed `git rev-parse :path`. Git echoes the unresolved `:path` token while returning non-zero; the following failed `cat-file` produced empty stdout, which was hashed as `e3b0c442…` and mislabeled `hash_source=index`. Non-empty runtime artifacts such as `.grepai/index.gob` and `data/receipts/post-commit-26dad8c1646746e1da6168257b383f171a2f0aca.json` therefore received false same-index evidence. The repair must check both Git return codes and keep a selftest negative control for an untracked, non-empty artifact.

Raw evidence anchors and key excerpts:

- `data/proof-workflow/equivalence-26dad8c16467-dirty.json`: `status=failed`; `equivalence-controls` ran `selftest.sh` and exited `2`; commit=`26dad8c…`, tree=`6448187…`.
- `loop_wiki/evolve-technical-equivalence-research/_runs/selftest/receipt.json`: `offline_surface=EXERCISED_FAIL`, `live_carrier=NOT_EXERCISED`, `fresh_semantic_judge=NOT_EXERCISED_REQUIRES_TWO_BLINDED_BATCHES`, `human_admit=NOT_EXERCISED_REQUIRES_EXTERNAL_HUMAN`; `hard_drift.failures` names `mirror PROFILE.md bytes mismatch` and `mirror manifest source_profile_sha256 mismatch`.
- `proof_workflow/README.md`: “`workflow lock` only requires receipt existence, not green; the commit gate requires a fresh lock.”
- `proof_workflow/control_workflow_lineage.sh`: the relock control derives prove loops from `loopctl/contract.json` and runs the full loop before building the lock.

## Evidence-preserving repair

Use the contract as the loop inventory. For each declared proof:

1. exit `0`: record PASS and continue;
2. exit `2`: record the checked red verdict and continue;
3. exit `64` or any undeclared exit: stop because the proof contract or environment is absent/broken.

After all receipts exist for the exact staged subject, build and stage `loopctl/workflow.lock`, obtain the required lineage trailer, and commit normally. Do not run live Gemini merely to recolor evidence, and do not use `--no-verify` or a lineage override for this ordinary documentation change.

The stale admitted mirror remains a real `EXERCISED_FAIL/hard_drift` item. The live Gemini carrier, fresh semantic judge, and Human Admit remain separate `NOT_EXERCISED` items. Making those live lanes green would transmit declared research input to Google and requires its own explicit data-scope authorization, audit probes, fresh judge result, and Human Admit. ChatGPT/GitHub research can diagnose these states but cannot impersonate the Gemini canary.

## Curated research entrypoints

Read in this order:

1. `proof_workflow/README.md`, especially the boundary explaining why a red receipt does not block a commit.
2. `loopctl/workflow_lock.py`, especially `_loops`, `_receipt`, and `build`.
3. `proof_workflow/control_workflow_lineage.sh`, especially the relock control.
4. `loopctl/contract.json` for the current proof inventory and exit domains.
5. `proof_workflow/prove_equivalence.sh` and `loop_wiki/evolve-technical-equivalence-research/selftest.sh` for the live verdict.
6. `AGENTS.md` and `docs/integration/CROSS_REPO_INTEGRATION.md` for the staged policy.
7. Through the GitHub connector on `ed3c/bettor-arena`: PR #26; commits `24510a4`, `f45a8b7`, `539adfa`; then the current open PR stack.

Read-only grounding commands:

```text
git status --short
git diff --cached --check
sh loopctl/loopctl.sh contract
rg -n "紅燈本來|workflow lock|receipt" proof_workflow/README.md loopctl/workflow_lock.py
gh pr list --repo ed3c/bettor-arena --state open --json number,title,headRefName,baseRefName,mergeable,mergeStateStatus
```

## Desktop and GitHub connector prompt

Use the GitHub connector with private repository `ed3c/bettor-arena` (repository ID `1330387399`). Read this entire packet and the curated local files before proposing a fix. Research GitHub PR #26 and commits `24510a4`, `f45a8b7`, and `539adfa`; verify whether a red technical-equivalence receipt is evidence input or a commit blocker. Inspect the staged diff and current proof contract. Produce anchored findings first, then implement the evidence-preserving relock algorithm without bypassing hooks. Deliver the policy through Forgejo #35, publish it to an explicit GitHub PR, and reconcile the existing GitHub stack WIP=1. Every claim must cite a local path/line, exit code, or GitHub PR/commit. Do not send private repository content to Gemini or another provider unless a separate authorization names the exact data and destination.

Desktop status at packet refresh: the deep link populated this prompt but did **not** submit it, and no connector readback from that new chat exists. The operator must press Send/Return. If the Desktop UI remains outside the allowed automation surface, record `BLOCKED_MANUAL_SEND`; never relabel prefill as a submitted research session. The current Codex session independently verified connector read access to private repository `ed3c/bettor-arena`, but that is not a receipt for the unsent Desktop chat.

## Delivery responsibilities

1. Update the Forgejo issue with this packet’s path and SHA-256.
2. Keep the `workflow_lock.py --selftest` negative control green, then generate the complete same-subject proof set while preserving all `0`/`2` verdicts; stop on `64`.
3. Rebuild and stage `loopctl/workflow.lock`; verify every `hash_source=index|head` digest against a successfully resolved Git object, and regenerate any governed context/proof projections affected by new documentation.
4. Run repository gates, self-review the staged diff, and commit with the generated workflow lineage trailer.
5. Push a Forgejo branch, open a PR with `Closes #35`, read back checks, and merge only when the repository gates allow it.
6. Publish the admitted exact subject to GitHub. Re-snapshot the open PR graph after every merge; repair conflicts in dedicated worktrees and preserve stacked base order.
7. If GitHub gains commits absent from Forgejo, open a Forgejo sync-back issue/PR before declaring origin equivalence.

## Stop conditions and required output

Stop and record a blocker on Forgejo #35 for exit `64`, absent write authority, branch-protection rejection, ambiguous semantic conflict, destructive-history requirement, or a third materially different failure. The final report must distinguish proof receipt presence from proof PASS; name all remaining `FAIL`, `NOT_EXERCISED`, and origin drift; list every created commit/PR/merge receipt; and state the next stack edge if the queue is not empty.
