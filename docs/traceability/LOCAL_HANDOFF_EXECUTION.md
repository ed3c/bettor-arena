# Local Handoff Execution Queue — Bettor consumer epoch 1

Canonical procedure remains in `ed3c/skills-shared`; this repository stores only the consumer queue instance and thin admission bridge.

## Frozen subjects

```text
skills-shared  dbcfdb4df76609822893aeb595e5f8ada8483435
bettor commit  542a935064e06f358d7d890df5d86364bbc20f46
bettor tree    78a6b573f094f1df7f3537ace551768f70210e51
rollback       1d08d76ccf890b8f1bc706041adec12eb7fb781d
runtime-env    77dca3584a4adb1c463c815bdb5ab603eae32b23
profile        bettor-arena-tech-lead-local
active item    ed3c/bettor-arena#161
```

## Prepare the local execution worktree

Keep the checkout containing this queue as the controller checkout. Create a separate clean execution worktree at the frozen Bettor subject:

```bash
BETTOR_CONTROLLER=/absolute/path/to/current/bettor-arena
BETTOR_EXEC=/absolute/path/to/local-state/bettor-542a9350
SKILLS_SHARED=/absolute/path/to/skills-shared
RUNTIME_ENV=/absolute/path/to/runtime-env

# skills-shared must be clean and exactly at dbcfdb4d...
# runtime-env must be clean and exactly at 77dca358...

git -C "$BETTOR_CONTROLLER" worktree add --detach "$BETTOR_EXEC" \
  542a935064e06f358d7d890df5d86364bbc20f46

python3 "$BETTOR_CONTROLLER/scripts/gates/prepare_local_handoff.py" \
  --skills-shared-root "$SKILLS_SHARED" \
  --consumer-root "$BETTOR_EXEC" \
  --receipt /absolute/host-private/issue-161-handoff-admission.json
```

The preparation receipt may say `READY_FOR_ACTIVE_ITEM_EXECUTION`; it does **not** prove #161 execution.

## Execute the ACTIVE item

First run the fixed selftest from the frozen execution subject:

```bash
cd "$BETTOR_EXEC"
python3 scripts/gates/issue_161_host_rebind.py --selftest
```

Then materialize the local-only runtime path and execute the admitted mutation:

```bash
python3 scripts/gates/issue_161_host_rebind.py \
  --runtime-env-root "$RUNTIME_ENV" \
  --mode apply \
  --receipt /absolute/host-private/issue-161-rebind.json
```

The #161 receipt must validate as PASS/`READY_FOR_LOCAL_CANARY`. Dry-run success, GitHub CI, issue UI state, or tool presence cannot substitute for this receipt.

## Epoch boundary

`runtime-env sync --apply` changes consumer binding bytes. Local Handoff Queue v1 binds one immutable `subject.commit` across one queue instance, so **do not advance #146 inside this queue epoch**.

After #161 PASS:

1. inspect the exact changed binding and all required assertions;
2. freeze the resulting consumer bytes into a new exact commit/tree through the repository's Human-owned convergence path;
3. compile a new Local Handoff Execution Queue epoch whose ACTIVE item is #146;
4. bind #231/#234/#256 live requirements to that new subject;
5. only then run real multi-Worker, GrepAI/SCIP/Tree-sitter/Serena/SQLite, Git Town and Forgejo lanes.

No step here grants merge, force-push, issue-close, queue-advance, provider activation, semantic-conflict resolution, promotion or destructive rollback authority.

## Cleanup

If the #161 epoch is abandoned before Human convergence, remove the execution worktree only after preserving required host-private receipts:

```bash
git -C "$BETTOR_CONTROLLER" worktree remove --force "$BETTOR_EXEC"
git -C "$BETTOR_CONTROLLER" worktree prune
```
