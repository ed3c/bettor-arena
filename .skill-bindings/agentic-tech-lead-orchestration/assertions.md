# Agentic Tech Lead binding assertions

The checker owns these hard controls:

- `ATL-BIND-001` — exact shared candidate repository, branch, commit, tree,
  evidence state, absent registry classification, absent projection, and no
  copied `SKILL.md`.
- `ATL-BIND-002` — exact Bettor parent commit/tree and active issue `#92`.
- `ATL-BIND-003` — one role per provider/module mapping with current module ID
  and interface version read back from `.arena/modules/**/module.json`.
- `ATL-BIND-004` — GrepAI is an intent anchor; semantic/vector results remain
  candidates until source readback.
- `ATL-BIND-005` — SCIP + SQLite is the deterministic target, but the existing
  Python AST adapter is not mislabeled as SCIP.
- `ATL-BIND-006` — Tree-sitter owns structural slicing only; current runtime
  remains `NOT_IMPLEMENTED`.
- `ATL-BIND-007` — active `code-graph-rag` and double-graph execution are
  forbidden; its historical manifest is `REJECTED`/`ABSENT` and digest-bound.
- `ATL-BIND-008` — Stack/Tournament limits are three Workers and three
  materially different repairs per stable failure signature.
- `ATL-BIND-009` — one writer per path, path-disjoint parallelism, true-child
  dependency, and immutable acceptance oracles remain locked.
- `ATL-BIND-010` — auto-restack, publication, semantic conflict resolution,
  merge, provider-state writes, and Worker-state writes remain false.
- `ATL-BIND-011` — provider activation, semantic-conflict admission,
  publication, merge, promotion, and rollback remain Human-owned.
- `ATL-BIND-012` — binding routes, dedicated suite/workflow, no secrets,
  no user-specific absolute paths, no `.git-town.toml`, and no unadmitted
  skill projection.

A PASS proves only these deterministic controls for the exact repository
bytes. It does not promote any runtime state.
