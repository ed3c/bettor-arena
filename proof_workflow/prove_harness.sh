#!/bin/sh
# prove_harness.sh — physical traversal proof of the proof machinery itself.
#
# Everything else here measures a loop. This measures the instrument, because
# until it existed eleven of the seventeen files under proof_workflow/ — every
# prove_*.sh, all three files in lib/, and three of the controls — were hashed by
# nothing. Editing lib/prove.sh moved no digest and the lineage hook stayed
# silent about a change to the thing that computes every digest.
#
# Self-reference is fine here and is NOT the workflow.lock cycle. A script's own
# bytes do not change when the digest changes, so hashing this file inside this
# proof settles on the first pass. The lock is different: it is DERIVED from the
# digest, so hashing it would make each rebuild move both forever.
#
#   DETERMINISTIC harness — the recorder, the capture library, the comparator,
#     every traversal proof and every control. The two libraries with a
#     verification surface are run; the rest are hashed, because firing a proof
#     from inside a proof would write receipts about receipts.
#   PROBABILISTIC read documents — README.md, which is what an agent reads to
#     know how to interpret a red. It is covered by the macro proof as the repo's
#     passive context; naming it here too would say the same thing twice.
#
# Usage: sh proof_workflow/prove_harness.sh
# Exit:  0 pass · 2 a step went red · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init harness "proof_workflow/lib -> prove_*.sh + control_*.sh -> receipts under data/proof-workflow/"

# --- the recorder and its helpers, each run through its own selftest ---------
prove_harness recorder proof_workflow/lib/prove.sh \
  "step kinds, molecular digest, receipt collision, dirty naming; its selftest plants a self-perturbing harness and requires the digest to hold" \
  -- sh proof_workflow/lib/prove.sh --selftest
prove_harness comparator proof_workflow/lib/compare_control.py \
  "claim vs behaviour: required/optional by measurement, ledger-level coverage, declared exclusions, receipt selection by tree state" \
  -- python3 proof_workflow/lib/compare_control.py --selftest
prove_harness capture proof_workflow/lib/capture.sh \
  "physical trace of a real run: argv, cwd, exit, both streams to disk with a sha256 each (sourced, so hashed rather than fired)"
# The coverage checker, which caught its own absence the moment it became tracked:
# it is the file that asks whether the instrument is measured, and nothing was
# measuring it. Left out of the first version of this proof because it was written
# afterwards — which is exactly how the eleven-file gap happened, one file at a time.
prove_harness shebang-match proof_workflow/lib/shebang_match.py \
  "every proof/control invocation x the target's shebang -> a bash script run with sh is exit 2; a variable target is REPORTED as uncheckable rather than passed over" \
  -- python3 proof_workflow/lib/shebang_match.py --selftest
prove_harness no-bash-script-run-with-sh - \
  "the scan itself, over the live tree: it caught prove_openwiki.sh running the bash worker with sh, which had been silent until a selftest case used process substitution" \
  -- python3 proof_workflow/lib/shebang_match.py
prove_harness coverage-checker proof_workflow/lib/harness_coverage.py \
  "tracked proof_workflow files x proof receipts at this commit -> covered / declared / UNCOVERED; a control receipt is refused as a source" \
  -- python3 proof_workflow/lib/harness_coverage.py --selftest

# --- every traversal proof --------------------------------------------------
# Hashed, never fired: a proof run from inside a proof would write receipts about
# receipts, and the outer digest would then depend on when the inner one last ran.
for p in macro_loop micro_loop openwiki container policy workflow harness; do
  case "$p" in
    macro_loop|micro_loop) f="proof_workflow/prove_$p.sh" ;;
    *) f="proof_workflow/prove_$p.sh" ;;
  esac
  [ -f "$PROVE_ROOT/$f" ] || continue
  prove_harness "proof-$p" "$f" \
    "one loop's traversal -> data/proof-workflow/<loop>-<commit12>[-dirty].json (hashed, not fired)"
done

# --- every control ----------------------------------------------------------
for c in macro_entry micro_entry openwiki_entry workflow_lineage mcp_surface container_surface sandbox_policy harness_coverage; do
  f="proof_workflow/control_$c.sh"
  [ -f "$PROVE_ROOT/$f" ] || continue
  prove_harness "control-$c" "$f" \
    "one mechanism's planted defects -> a verdict the proof cannot give itself (hashed, not fired)"
done

prove_note readme-covered-by-macro proof_workflow/README.md \
  "declared out of scope HERE, not uncovered: README.md is the repo's passive context and is hashed by the macro proof. Naming it in two proofs would record the same claim twice and make a change look like two"

prove_emit
