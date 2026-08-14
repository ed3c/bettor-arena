# Assertion contract

## Hard assertions

A hard assertion is deterministic, identifies its subject, returns a meaningful non-zero status on failure, and has a planted negative control.

The binding gate checks:

```text
shared Skill projection is a Git symlink, not a copied body
required document routes exist
optional routes remain explicitly optional
binding candidate identity is immutable-looking
configured MCP servers agree across Claude/Codex surfaces
NOT_CONFIGURED providers remain absent from both surfaces
Serena's configured commit agrees with the binding
non-PASS provider states name a fallback
provider evidence ceilings are explicit
binding/docs contain no secret-shaped value or machine-local path
core evidence vocabulary and Human boundaries remain present
```

Run:

```bash
python3 scripts/gates/check_repo_agent_native_binding.py --selftest
python3 scripts/gates/check_repo_agent_native_binding.py
```

The selftest must make each planted mutation turn red:

```text
projection replaced by copied directory
required route removed
unadmitted graph provider silently added
provider fallback removed
secret-shaped or machine-local value injected
```

## Source/output assertions

The shared Skill's `verify_repo_agent_native_output.py` owns output hard gates:

- confirmed claims use `A` or `A-` and include source references;
- negative invariants declare search boundaries;
- unavailable providers name fallbacks;
- current authority wins memory conflicts;
- confirmed graph edges have source readback;
- unresolved states remain explicit.

## Runtime assertions

Provider health, index freshness, compiler/LSP diagnostics, graph coverage, memory retrieval, Claude/Codex outputs, and consumer behavior require current execution receipts. Configuration presence is not runtime `PASS`.

## Advisory assertions

Markdown checklists and model self-review may check clarity, usefulness, naming, or completeness. They cannot create a hard-gate outcome unless calibrated against independent positive and negative fixtures.

## Failure policy

- never append `|| true` to an assertion;
- never retry stochastic output until it happens to pass;
- never infer `PASS` from skipped/no-runner execution;
- preserve exit code, stderr, exact commit, command, and artifact digest;
- stop before merge/promotion when a hard assertion fails or required evidence is absent.
