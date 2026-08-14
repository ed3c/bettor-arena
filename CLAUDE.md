# CLAUDE.md — bettor-arena Claude Code thin projection

Read [`AGENTS.md`](AGENTS.md) first, then [`README.md`](README.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md).

`CLAUDE.md` and `AGENTS.md` are governed entry projections. Repository-local gates validate their bytes; promotion-time cross-repository generators may update them, but pre-commit never reads a sibling checkout.

## Mandatory modular-integration read order

For module, Macro/Micro loop, Skills, runtime-env, proof, MCP, browser, origin, external bootstrap, Agent Shield, LoopX/Harness, monolithic-worker, episodic-memory or PDF work, continue through:

1. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
2. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
3. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
4. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
5. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
6. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)
7. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
8. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
9. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
10. `sh loopctl/loopctl.sh contract`
11. the target module/loop Context Capsule, nearest README, machine manifest/contract, source, tests and latest proof/control/mutation receipts.

For the separate SKILL.md + MCP PDF, also read [`docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md`](docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md).

## Claude Code boundary

Claude Code 不得：

- bypass `loopctl` or call another module’s private executable;
- treat a symlink, mutable checkout, package declaration, old SHA, PDF prose or fixture as release/live identity;
- execute model-generated raw shell, use `shell=True`, or invent OS/test evidence;
- write LoopX completion, quota, gate, Human Admit, promotion or rollback state;
- persist raw chain-of-thought as episodic memory;
- accept a plain `force_skip` action as exception authority;
- treat LangGraph checkpoint, UI, vector index, code graph or memory store as canonical state;
- flatten root/loop native context into an arbitrary MCP prompt;
- place credentials, browser/device sessions or secret host paths in Git, bundles, MCP payloads or receipts;
- promote `ABSENT`, `FAIL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED` or `SKIPPED_BY_POLICY` to PASS;
- perform Human Admit, merge, release promotion, production rollback, secret rotation or permission widening.

A target in Markdown may remain `NOT_IMPLEMENTED`. A mechanism present in code but not run for the exact subject remains `NOT_EXERCISED`. Open a new Claude session after changing passive context before claiming it was read.

For LoopX/PDF architecture changes run:

```sh
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```
