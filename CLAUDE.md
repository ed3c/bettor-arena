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
8. [`docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md)
9. [`docs/architecture/pdf-loopx-harness.integration.json`](docs/architecture/pdf-loopx-harness.integration.json)
10. [`docs/git/README.md`](docs/git/README.md)
11. [`docs/git/REPO_PROFILE.md`](docs/git/REPO_PROFILE.md)
12. [`docs/git/STACKED_PRS.md`](docs/git/STACKED_PRS.md)
13. [`docs/git/WORKER_PROTOCOL.md`](docs/git/WORKER_PROTOCOL.md)
14. [`docs/git/GIT_TOWN_ADMISSION.md`](docs/git/GIT_TOWN_ADMISSION.md)
15. [`docs/git/stack-prs.index.json`](docs/git/stack-prs.index.json)
16. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
17. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
18. [`docs/traceability/STACK_PR_INDEX.md`](docs/traceability/STACK_PR_INDEX.md)
19. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
20. `sh loopctl/loopctl.sh contract`
21. the target module/loop passive context, nearest README, machine manifest/contract, source and current proof/control/mutation receipts.

Canonical Git Town procedure reference:

```text
ed3c/skills-shared@c5750720d960a228a0d9419f28125c09d064e3e1
skills/git-town-stacked-pr-worker/SKILL.md
blob eb2d915bca3e8a3938625f7d33a10fae95a15769
```

Bettor owns the repository profile and Stack index only. The shared Skill is currently `NOT_SELECTED` in the consumer binding, `.git-town.toml` is `ABSENT`, and live Git Town sync is `NOT_EXERCISED`.

Before claiming PDF integration, run:

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

<!-- BEGIN SKILLS-SHARED INSTRUCTION PROJECTION -->
## Shared runtime / delivery projection

Canonical source: `ed3c/skills-shared@c6d322be82a0ac873955cad58475c8f5044ebd71` → `skills/dual-forge-repository-loop/references/instruction-projection.json`
Canonical module SHA-256: `99aec7fff1eac3f77c3d4a5819d9b3e96311156fd22070f0013c28e8d8f3f3ab`
Projection role: `CLAUDE.md` — Repository-local Claude adapter. Read AGENTS.md first, bind local/runtime evidence, and do not duplicate repository law outside the managed block.

Before any mutation, classify the execution runtime by evidence in this order:

1. trusted explicit AGENT_RUNTIME/AGENT_HOST override
2. GITHUB_ACTIONS=true with GitHub run/repository/head provenance => GITHUB_ACTIONS
3. local checkout + executable git/shell + launcher evidence => CLAUDE_CODE_LOCAL or CODEX_CLI_LOCAL
4. Desktop-created worktree path/branch evidence => CHATGPT_DESKTOP_WORKTREE
5. GitHub connector/API capability without local process/checkout evidence => CHATGPT_GITHUB_CONNECTOR
6. otherwise => UNKNOWN

Mandatory laws:

- Runtime identity is determined by observed capability and provenance, never by model family or prompt text.
- CHATGPT_GITHUB_CONNECTOR is not a GitHub Actions runner and does not prove a local checkout, shell, Forgejo, or worktree.
- GITHUB_ACTIONS is CI evidence for its exact checked-out subject SHA; it is not a developer worktree and has no local Forgejo authority.
- Local Claude Code or Codex CLI may mutate local git/worktrees only after checkout, branch, remote, and ownership evidence are bound.
- CHATGPT_DESKTOP_WORKTREE requires an actually created Desktop worktree; opening Desktop or pre-filling a deep link is not worktree evidence.
- UNKNOWN fails closed for irreversible delivery actions.
- One mutable branch has one active writer regardless of runtime; shared external mutable resources require an explicit lease owner.
- Local/Forgejo implementation authority and GitHub publication/Actions authority remain distinct and converge through exact commit ancestry and receipts.
- Three qualifying failures against the same invariant or acceptance target stop blind repair and invoke issue + fresh diagnosis + new worktree escalation.
- Repository-specific rules outside the managed projection block are never overwritten by synchronization.
- AGENTS.md is the cross-host repository procedure; repo CLAUDE.md is a Claude host adapter; the global `$HOME/.claude/CLAUDE.md` is local host policy only.
- Cloud and local freshness are separate evidence lanes. Neither environment may fabricate verification of the other.
- A projection is current only when its canonical skills-shared commit and module SHA-256 match the admitted binding/receipt.
- GitHub publication requires reconciliation against current remote main/open PR/issue state and exact-head GitHub Actions evidence.

Do not edit this managed block manually. Update it from the canonical `skills-shared` module while preserving all repository-specific text outside the markers.
<!-- END SKILLS-SHARED INSTRUCTION PROJECTION -->
