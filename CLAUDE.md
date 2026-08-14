# CLAUDE.md — bettor-arena Claude Code thin projection

Read [`AGENTS.md`](AGENTS.md) first, then [`README.md`](README.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md).

`CLAUDE.md` and `AGENTS.md` are governed entry projections. Repo-local gates validate repository bytes without reading mutable sibling checkouts.

## Mandatory modular-integration read order

For module, Macro/Micro, Skill, runtime-env, proof, MCP, provider, LoopX, memory, Git Town or branch-Stack work, continue through:

1. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
2. [`docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md)
3. [`docs/architecture/pdf-harness-integration.matrix.json`](docs/architecture/pdf-harness-integration.matrix.json)
4. [`docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md)
5. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
6. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
7. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
8. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
9. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)
10. [`docs/git/README.md`](docs/git/README.md)
11. [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
12. [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
13. [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md)
14. [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md)
15. [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json)
16. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
17. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
18. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
19. `sh loopctl/loopctl.sh contract`
20. the target module README, manifest, source, tests, receipts and current GitHub base/head/checks

Canonical Git Town procedure reference:

```text
ed3c/skills-shared@c5750720d960a228a0d9419f28125c09d064e3e1
skills/git-town-stacked-pr-worker/SKILL.md
blob eb2d915bca3e8a3938625f7d33a10fae95a15769
```

Bettor owns the repository profile and Stack index only. The shared Skill is currently `NOT_SELECTED` in the consumer binding, `.git-town.toml` is `ABSENT`, and live Git Town sync is `NOT_EXERCISED`.

Before claiming PDF or Git Stack integration, run:

```sh
python3 scripts/gates/check_pdf_harness_integration.py
python3 scripts/gates/check_pdf_harness_integration.py --selftest
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
python3 scripts/gates/check_git_town_stack_docs.py
python3 scripts/gates/check_git_town_stack_docs.py --selftest
```

## Claude Code boundary

Claude Code 不得：

- bypass `loopctl` or call another module's private executable;
- relabel `.arena` or `loopctl` as the complete LoopX kernel;
- submit raw shell strings or write its own Gate/assertion verdict;
- write canonical task state, Quota, Human decision, promotion or rollback;
- persist raw Thought Stream or private chain-of-thought;
- infer hidden gray-box tool calls;
- infer Git Town installation from the shared Skill reference;
- create `.git-town.toml` before executable/version/checksum/license/SBOM/legal admission;
- resolve semantic conflicts or execute Git Town continue/skip/undo;
- push, merge, ship, close, delete or retarget branches;
- change remotes, credential helpers or permissions;
- describe `MERGED_TO_PARENT` as `MERGED_TO_MAIN`;
- treat duplicate active writers as parallel-safe;
- promote `ABSENT`, `FAIL`, `NOT_IMPLEMENTED`, `NOT_EXERCISED` or `SKIPPED_BY_POLICY` to PASS;
- perform Human Admit.

Current Stack conflict:

```text
PR #76 and PR #77 both implement issue #64 and overlap loop_wiki/loopx-worker-gateway/**
→ BLOCKED_DUPLICATE_TERMINAL
→ Human decision required
```

A mechanism described in Markdown may remain `NOT_IMPLEMENTED`. A mechanism present in code but not executed for the exact subject remains `NOT_EXERCISED`. GitHub metadata is fresher than the checked-in Stack snapshot. Open a new Claude session after changing passive context before claiming it was read.
