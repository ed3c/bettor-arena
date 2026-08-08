#!/bin/sh
# prove_workflow.sh — physical traversal proof of the lineage machinery.
#
# The thing that senses a moved workflow, stamps a commit with which version it
# descends from, and replays a tagged version. It had a control group and no
# receipt, so a green `workflow test` recorded that the machinery works and
# nothing recorded which bytes of it were working.
#
#   DETERMINISTIC harness — the manifest builder, the trailer/gate, the replay
#     driver, the hook that writes the stamp, and the control that plants
#     defects against all of them.
#   PROBABILISTIC read documents — none of its own; it reads the manifest and
#     the index, both machine artifacts. Stated so the absence is a property.
#
# Terminal artifact: loopctl/workflow.lock is deliberately NOT hashed. It is
# BUILT FROM the proof receipts, so hashing it in a proof makes the digest depend
# on a file that depends on the digest, and no rebuild ever settles while every
# run looks green. workflow_lock.py refuses that cycle outright; this records the
# same boundary where a reader of the receipt will see it.
#
# Usage: sh proof_workflow/prove_workflow.sh
# Exit:  0 pass · 2 a step went red · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init workflow "staged paths -> workflow.lock -> Workflow-Lineage trailer -> commit-msg gate; and <commit|tag> -> replay"

prove_harness manifest-builder loopctl/workflow_lock.py \
  "the proof receipts -> the manifest of what a traversal is made of; hashes read from the INDEX so a concurrent edit cannot move them, and a self-referential entry is refused" \
  -- python3 loopctl/workflow_lock.py --selftest
prove_harness lineage loopctl/lineage.py \
  "manifest + staged paths -> Workflow-Lineage/Version/Touched; stale lock refused; override needs a stated reason" \
  -- python3 loopctl/lineage.py --selftest
prove_harness replay loopctl/replay.sh \
  "<commit|tag> -> that ref's own CLI in a disposable worktree: tracked content verified from git, the version executed, runtime paths skipped by name (not fired here — it builds worktrees)"
prove_harness prepare-commit-msg .githooks/prepare-commit-msg \
  "staged paths -> the trailer written into the message; idempotent, and never fails the commit — the gate is what refuses"
prove_harness commit-msg-gate .githooks/commit-msg \
  "message + staged paths -> molecular contract AND lineage check; a helper that can be skipped is not a contract"
prove_harness control proof_workflow/control_workflow_lineage.sh \
  "plants a real modification into a real manifest file inside a worktree: sensed with the right kind, stale lock refused, unstamped refused, outsider silent, tag replayed"

prove_note workflow-lock-not-hashed loopctl/workflow.lock \
  "declared out of scope: the lock is BUILT FROM the proof receipts, so hashing it here would make this digest depend on a file that depends on this digest — every rebuild moves both and neither settles, while looking green throughout. Its integrity comes from being rebuildable, and workflow_lock.py refuses the cycle at source"
prove_note no-context-lane - \
  "this layer reads no prompt: its inputs are the manifest and the git index, both machine artifacts"

prove_emit
