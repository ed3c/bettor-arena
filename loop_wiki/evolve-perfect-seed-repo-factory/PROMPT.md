# Target contract — perfect-seed repo factory

## Task

Accept one admitted physical source packet of kind `dr`, `gcr`, `repo`, or
`grill-me`. Materialize a standalone repo whose local operator skill executes
exactly twenty dependency-valid reasoning functions for an explicit task.

## Success criteria

- All four source kinds pass the same public build seam.
- Invalid kinds, missing/mismatched sources, and existing outputs fail loudly.
- Generated repo contains a repo-local operator skill, reduced IR, artifact
  manifest, lineage, runnable code, and tests.
- Generated operator writes exactly twenty unique calls and twenty hash-bound
  results in dependency order.
- Final call surfaces `human_required`.
- Schema replay, baseline governance, template lifecycle, trend recording,
  behavior eval, positive control, and hollow control are executable.
- Factory verification and the physical trigger run minimum lineage, read-only
  formatting, typed lint, and strict TypeScript before behavior/operator work.
- The fast receipt remains `preflight-only-not-code-quality-axis`; it cannot
  promote asynchronous Code Quality or Production Use from `pending`.
- `sh verify.sh` and `sh selftest.sh` exit 0.

## Guard metric

Physical behavior at the two public seams: packet→repo and task→20-call trace.
File presence alone is insufficient; generated code and hollow controls run.

## Stop-loss

Three materially different attempts per failing problem. Then record the error,
question the abstraction, choose a smaller route, and surface the blocker.
