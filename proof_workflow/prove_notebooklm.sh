#!/bin/sh
# prove_notebooklm.sh — physical traversal proof of the NotebookLM harvest loop.
#
# The path this records: the skill an agent reads to drive the loop, the module
# that says which notebook is harvested and why, the CLI surface that is the
# only way in, and the one script that does the work — fired through its own
# selftest, which is hermetic and touches no network.
#
#   DETERMINISTIC harness — notebooklm/workflow.py, run via `--selftest`. That
#     selftest is what makes this proof worth anything: it drives every named
#     absence (absent binary 64 vs unauthenticated 2, the `Matched:` JSON
#     impurity, an empty link set under --follow, and the scratch notebook being
#     deleted even when the follow fails) against a fake CLI on PATH.
#   PROBABILISTIC read documents — SKILL.md and the business module. They are
#     what the agent side actually reads before pressing anything, so an absent
#     one is FATAL: a prompt that is not there cannot be the one that ran.
#
# Terminal artifact: NONE, and that is a property rather than a gap. Every run
# writes data/notebooklm/<utc>/, whose path and bytes are new each time; hashing it
# would make this digest track "where the last run went" instead of "what the
# mechanism is". It is declared out of scope by name below, and what stands in
# for it is a FIELD assertion inside the selftest — the same repair the micro
# loop's iteration lane got.
#
# Usage: sh proof_workflow/prove_notebooklm.sh
# Exit:  0 pass · 2 a step went red · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init notebooklm "loopctl notebooklm run -> notebooklm/workflow.py -> notebook by title -> one Google Doc/Sheet -> the docs.google link inside it -> data/notebooklm/<utc>/"

prove_context skill .agents/skills/notebooklm-workflow/SKILL.md \
  "repo -> the agent driving this loop: which button, and how to read each exit code"
prove_context module .agents/skills/notebooklm-workflow/modules/ai-monetization-doc-harvest.md \
  "the first business module -> which notebook is harvested, the pick rule, and the measured baseline"

prove_harness entry notebooklm/workflow.py \
  "notebook title -> full UUID -> one ready Google Doc/Sheet -> its fulltext -> the docs.google links inside it -> (opt-in) that document opened via a scratch notebook that is deleted from finally. Its selftest drives every named absence against a fake CLI on PATH, with no network" \
  -- python3 notebooklm/workflow.py --selftest
prove_harness drive-fetch notebooklm/drive_fetch.py \
  "a docs.google file id -> sources.add_drive over the SIGNED-IN session -> that document's indexed text as JSON. Hashed, not fired: it runs under the CLI's own interpreter and every run of it writes to the account. It exists because the CLI's URL ingestion is anonymous — measured, every document linked from the harvested sheet answers HTTP 401 to an anonymous fetch while a nonexistent id answers 404, and the CLI returned FAILED_PRECONDITION for all of them"
prove_harness registry notebooklm/registry.json \
  "the interaction data: account profile, pinned notebook ids, named harvest targets. Hashed rather than run — it is data. A pin here is cross-checked against the live account at run time, never trusted as a shortcut, and the control asserts offline that every target names a notebook this file also declares"
prove_harness surface loopctl/loopctl.sh \
  "the only way in: flags not on the contract are refused rather than forwarded (hashed, not fired — loopctl --selftest is the macro loop's step)"

prove_note per-run-output-not-hashed data/notebooklm/ \
  'declared out of scope: every run writes a new <utc> directory, so hashing it would make this digest move on every run and track where the last run went rather than what the mechanism is. It is also other people Google document text, which does not belong in a committed receipt. What covers it instead is the field assertion in the selftest (schema_version, hop2.state, extracted.count) plus the sha256 the run itself records in module.json'
prove_note control-owned-by-harness proof_workflow/control_notebooklm_entry.sh \
  'declared here, hashed by the harness proof. Ownership rule: every file under proof_workflow/ belongs to prove_harness.sh, because those files ARE the instrument. Hashing a control in two proofs records one claim twice and makes a single edit look like two moved digests'
prove_note contract-owned-by-macro loopctl/contract.json \
  'declared out of scope HERE, not uncovered: the contract is one surface for every loop and is hashed by the macro proof. Naming it in each loop proof would record the same claim once per loop'

prove_emit
