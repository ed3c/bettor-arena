# State ledger — perfect-seed repo factory

STATUS: candidate

## Verifier topology

- T0: `verify.sh` runs factory behavior tests, stats, template lifecycle, schema
  replay, materialization, generated operator tests, and repo validation. It
  now starts with a physical minimum-lineage/format/lint/typecheck receipt.
- Anti-placebo: `selftest.sh` proves a generated repo passes and the same repo
  with its operator skill removed fails.
- Relocatability: `portability.sh` extracts `HEAD:<this loop>` with `git archive`
  into a directory outside the repository, installs from the committed lockfile,
  and requires its own T0 to pass there. It carries two negative controls: the
  archive must not ship `node_modules` and must fail `verify.sh` before install
  (otherwise the green is not bought by the clean install), and removing one
  `verify.sh` required file must return exit `2` (otherwise the instrument is not
  demonstrably capable of going red). It refuses to run against a dirty subtree,
  because `git archive` reads HEAD and a green result would then describe a
  commit nobody is looking at.
  Deliberately outside `verify.sh`: `verify.sh` is the per-iteration hot path and
  this pays for a real `bun install`. `verify.sh` asserts only that the file
  exists; execution is an explicit human/CI act, and the receipt lands in
  `_engine-run/portability-receipt.json`.
  Claim boundary: relocatability of HEAD, not of the working tree.
- Semantic superiority over the existing plan-truth mother loop remains
  `candidate` and requires human review.

## Iteration trajectory

| iter | actor        | result | evidence                                                                                                                                                                                                                          |
| ---- | ------------ | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | main-session | RED    | public CLI tests failed because `src/cli.ts` did not exist                                                                                                                                                                        |
| 1    | main-session | GREEN  | four source kinds materialized; six tests and 153 assertions passed                                                                                                                                                               |
| 2    | main-session | RED    | manifest escape test stopped at the earlier missing-call-plan gate; fixture had not run the operator                                                                                                                              |
| 3    | main-session | GREEN  | eight tests/159 assertions; generated repo two tests/37 assertions; unsafe output and manifest escape rejected; hollow mutation, physical trigger, and governed gates passed                                                      |
| 4    | main-session | RED    | generated-repo fast gate exposed 11 format drifts, then two strict lint defects; factory lint/typecheck exposed 14 additional static defects                                                                                      |
| 5    | main-session | GREEN  | 13 factory tests/189 assertions and two generated-repo tests/37 assertions pass; minimum-lineage and real Prettier/typed ESLint/strict-tsc gates pass; format/lint/type hollow controls fail at their own stages                  |
| 6    | main-session | RED    | seven new source_refs tests failed: validate accepted refless packets, resolve-refs was an unknown command, lineage carried no refs                                                                                               |
| 7    | main-session | GREEN  | 20 tests/225 assertions; refless/malformed refs fail validate at exit 1; resolve-refs without --peer is NOT_RUN exit 2; refs flow packet→IR→lineage with refs_grounded; migrated legacy packets carry the marked unknown sentinel |

## Remaining human gates

- Decide whether the bounded seed complements or replaces any part of the
  existing plan-truth mother loop.
- Decide whether a future carrier may turn the twenty local calls into external
  LLM/MCP calls; this implementation does not authorize that boundary.
- Implement hash-bound asynchronous Code Quality and Production Use request,
  receipt, stale projection, retry, and promotion gates; fast quality remains
  preflight-only until then.
- Admit template lifecycle from `validated` to `seed` only with current evidence.
