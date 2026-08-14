# CLAUDE.md — bettor-arena Claude Code thin projection

Read [`AGENTS.md`](AGENTS.md) first, then [`README.md`](README.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md).

`CLAUDE.md` and `AGENTS.md` are governed entry projections. The repo-local gate validates staged bytes; promotion-time cross-repository generators may update them, but pre-commit never reads a sibling checkout.

## Mandatory modular-integration read order

For module, Macro/Micro loop, Skills, runtime-env, proof, MCP, browser, origin, external bootstrap, or Agent Shield work, continue through:

1. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
2. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
3. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
4. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
5. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
6. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
7. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
8. `sh loopctl/loopctl.sh contract`
9. the target module/loop passive context, nearest README, machine manifest/contract, and latest proof/control/mutation receipts.

## Claude Code boundary

Claude Code 不得：

- bypass `loopctl` or call another module's private executable;
- treat a symlink, mutable checkout, package declaration, or old SHA as release identity;
- flatten root/loop native context into an arbitrary MCP prompt;
- place credentials, browser/device sessions, or host-specific secret paths in Git, bundles, MCP payloads, or receipts;
- promote `ABSENT`, `FAIL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, or `SKIPPED_BY_POLICY` to PASS;
- invent Human Admit, or merge without the issue-bound standing owner authorization and exact-head gates defined by [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md); release promotion, production rollback, secret rotation, and permission widening remain human-only.

A target mechanism described in Markdown may still be `NOT_IMPLEMENTED`. A mechanism present in code but not run for the exact subject remains `NOT_EXERCISED`. Open a new Claude session after changing passive context before claiming it was read.
