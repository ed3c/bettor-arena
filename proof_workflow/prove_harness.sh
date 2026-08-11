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
  "physical trace of a real run: unique directory, argv, cwd, exit, both streams to disk with a sha256 each" \
  -- sh proof_workflow/lib/capture.sh --selftest
prove_harness ctg-control-helper proof_workflow/ctg_control.py \
  "closed packet closure + canonical projection + proof linkage for the CTG behavioral control"
prove_harness agent-runtime-control-helper proof_workflow/agent_runtime_control.py \
  "portable module-set fixture + isolated shared/runtime/Claude/Codex mutations for the independent control"
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
# A backtick inside a double-quoted prose argument is executable shell, not
# Markdown.  Two proofs used those descriptions for command names; both commands
# ran, printed an error, and the measured harness still returned zero.  Proof
# scripts have no legitimate need for legacy backtick substitution, so refuse it
# on every non-comment line instead of maintaining a list of known descriptions.
prove_harness no-executable-backticks-in-proofs - \
  "proof descriptions must be inert data: an unescaped backtick on executable lines can run a command while the measured assertion remains green" \
  -- python3 -c 'from pathlib import Path; import sys; bad=[f"{p}:{n}:{line.rstrip()}" for p in sorted(Path("proof_workflow").glob("prove_*.sh")) for n,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1) if not line.lstrip().startswith("#") and "`" in line and "\\`" not in line]; print("\n".join(bad), file=sys.stderr); sys.exit(2 if bad else 0)'
prove_harness coverage-checker proof_workflow/lib/harness_coverage.py \
  "tracked proof_workflow files x proof receipts at this commit -> covered / declared / UNCOVERED; a control receipt is refused as a source" \
  -- python3 proof_workflow/lib/harness_coverage.py --selftest
prove_harness equivalence-control-comparator proof_workflow/lib/equivalence_control.py \
  "Git-derived equivalence inventory and four independent assurance states -> control receipt" \
  -- python3 proof_workflow/lib/equivalence_control.py --selftest

# --- every traversal proof --------------------------------------------------
# Hashed, never fired: a proof run from inside a proof would write receipts about
# receipts, and the outer digest would then depend on when the inner one last ran.
for p in macro_loop micro_loop openwiki container policy workflow harness notebooklm equivalence ctg_loop agent_runtime; do
  case "$p" in
    macro_loop|micro_loop) f="proof_workflow/prove_$p.sh" ;;
    *) f="proof_workflow/prove_$p.sh" ;;
  esac
  [ -f "$PROVE_ROOT/$f" ] || continue
  prove_harness "proof-$p" "$f" \
    "one loop's traversal -> data/proof-workflow/<loop>-<commit12>[-dirty].json (hashed, not fired)"
done

# --- every control ----------------------------------------------------------
for c in macro_entry micro_entry openwiki_entry workflow_lineage mcp_surface container_surface sandbox_policy harness_coverage notebooklm_entry equivalence_entry ctg_entry agent_runtime_entry; do
  f="proof_workflow/control_$c.sh"
  [ -f "$PROVE_ROOT/$f" ] || continue
  prove_harness "control-$c" "$f" \
    "one mechanism's planted defects -> a verdict the proof cannot give itself (hashed, not fired)"
done

prove_note readme-covered-by-macro proof_workflow/README.md \
  "declared out of scope HERE, not uncovered: README.md is the repo's passive context and is hashed by the macro proof. Naming it in two proofs would record the same claim twice and make a change look like two"

prove_emit
