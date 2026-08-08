#!/bin/sh
# prove_ctg_loop.sh — deterministic traversal of the CTG runtime contract.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

F=loop_wiki/code-truth-graph
prove_init ctg "loopctl ctg run -> closed packet -> verified snapshot/profile -> graph + route-result"

prove_harness input-schema "$F/schemas/ctg-input.schema.json" \
  "external packet -> closed semantic envelope (hashed; json readability is exercised by the public contract test)"
prove_harness result-schema "$F/schemas/ctg-route-result.schema.json" \
  "runtime stages and artifact digests -> closed route-result envelope (hashed; json readability is exercised by the public contract test)"
prove_harness runtime-ref "$F/src/code_truth_graph/__init__.py" \
  "immutable runtime identity -> expected_runner comparison"
prove_harness runtime "$F/src/code_truth_graph/cli.py" \
  "packet bundle -> digest verification -> graph/result materialization"
prove_harness entry "$F/run.sh" \
  "stdin EOF + sandbox-local Python path -> one-shot runtime (hashed, not fired because the contract test fires the public CLI)"
prove_harness public-contract tests/test_ctg_cli.sh \
  "good/unknown/duplicate/unsafe/stale packets -> exact 0/64/2 exits and durable outputs" \
  -- sh tests/test_ctg_cli.sh

prove_note per-run-output-not-hashed \
  "CTG output is caller-selected and content-addressed; the public contract test verifies its graph/result digests in a disposable directory, so a previous run cannot stand in for this traversal"
prove_note control-owned-by-harness proof_workflow/control_ctg_entry.sh \
  "the behavioral control is part of the proof instrument and is hashed by prove_harness.sh, never fired from its traversal proof"

prove_emit
