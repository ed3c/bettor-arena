# CLAUDE.md — bettor-arena Claude Code thin projection

Read [`AGENTS.md`](AGENTS.md) first, then [`README.md`](README.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md).

`CLAUDE.md` and `AGENTS.md` are governed entry projections. The repo-local gate validates staged bytes; promotion-time cross-repository generators may update them, but pre-commit never reads a sibling checkout.

## Mandatory modular-integration read order

For module, Macro/Micro loop, Skills, runtime-env, proof, MCP, browser, origin, external bootstrap, Agent Shield, LoopX, memory or PDF-architecture work, continue through:

1. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
2. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
3. [`docs/architecture/pdf-harness-integration.matrix.json`](docs/architecture/pdf-harness-integration.matrix.json)
4. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
5. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
6. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
7. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
8. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
9. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
10. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
11. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
12. `sh loopctl/loopctl.sh contract`
13. the target module/loop passive context, nearest README, machine manifest/contract, source and current proof/control/mutation receipts.

Before claiming PDF integration, run:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
```

## Claude Code boundary

Claude Code 不得：

- bypass `loopctl` or call another module's private executable;
- relabel `loopctl` or `.arena` as the PDF's complete LoopX task-state kernel;
- treat a symlink, mutable checkout, package declaration or old SHA as release identity;
- flatten root/loop native context into an arbitrary MCP prompt;
- place credentials, browser/device sessions or host-specific secret paths in Git, bundles, MCP payloads or receipts;
- submit raw shell strings or write its own assertion/gate verdict;
- write canonical task state, waive a gate, promote a release or Human Admit;
- persist raw Thought Stream or private chain-of-thought as episodic memory;
- promote `ABSENT`, `FAIL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED` or `SKIPPED_BY_POLICY` to PASS;
- infer Git Town configuration when `.git-town.toml` and `.git-town` are absent;
- merge, close, delete branches, release-promote, production-rollback, rotate secrets or widen permissions.

A target mechanism described in Markdown or the attached PDF may still be `NOT_IMPLEMENTED`. A mechanism present in code but not run for the exact subject remains `NOT_EXERCISED`. Open a new Claude session after changing passive context before claiming it was read.
