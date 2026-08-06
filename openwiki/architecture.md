---
type: Architecture
title: Repo SSOT and governance model
description: How ARCHITECTURE.md works as the single engineering SSOT, what the placement contract and iron laws demand, and which mechanism enforces each rule.
tags: [governance, ssot, placement-contract]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: ca72a92
covers: [ssot-derivation, placement-contract, iron-laws, admit-vocabulary]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Repo SSOT and governance model

bettor-arena is the new home of four subtrees migrated out of the `ts-skill-bettor` repo (src: ARCHITECTURE.md:3). Its design facts live in exactly one place — `ARCHITECTURE.md` — and every other root document is a deliberately thin derivation of it.

## Document topology

| File | Role | Evidence |
|---|---|---|
| `ARCHITECTURE.md` | Engineering SSOT: falsifiable modularity definition (§1), placement contract (§2), iron laws (§3) | its own header: "設計事實單一權威源＝本檔" (src: ARCHITECTURE.md:3-4) |
| `AGENTS.md` | Codex-facing thin entry; explicitly forbidden from restating rules ("本檔禁複述") | (src: AGENTS.md:3-4) |
| `CLAUDE.md` | Claude-tier thin entry; same non-restatement rule, plus the freeze note "迭代期間 root 被動上下文凍結" | (src: CLAUDE.md:3, CLAUDE.md:8) |
| `CONTEXT.md` | Glossary only, zero implementation detail | (src: CONTEXT.md:1) |
| `docs/adr/0001-molecular-slice-vocabulary.md` | The one accepted ADR: Intent-Slice vocabulary | (src: docs/adr/0001-molecular-slice-vocabulary.md:3) |

PRD and slice ledger intentionally do NOT live in this repo: they sit in the source repo's issue tracker, issues #2–#13 (src: ARCHITECTURE.md:4-5). Commit messages anchor back to that tracker via `Intent-Slice: ISSUE-<n>` — see [the molecular message contract](host-loop/molecular-messages.md).

## §1 — falsifiable modularity

Modularity is defined as a conjunction, not a vibe: zero inbound code references ∧ own verify ∧ own selftest ∧ green relocation in an isolated environment (src: ARCHITECTURE.md:9). Two corollaries stated in the same section:

- "Perfect" is never a state name; only versioned, counterexample-carrying, evolvable states exist (src: ARCHITECTURE.md:10). The factory encodes this literally — its legal machine states are candidate / validated / failed / human-required (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:36-37).
- Every green must first have had its corresponding red demonstrated (src: ARCHITECTURE.md:10). This is enforced culturally in every selftest in the repo (see [structure gates](gates/structure-gates.md) and [testing](testing.md)) and physically in relocation proofs such as `kb-ingest/port/test_relocation.sh` and the factory's `portability.sh`.

## §2 — placement contract

Every tracked root-level item must map to a slot in the §2 fenced tree (src: ARCHITECTURE.md:12-43). No slot = amend the map first, then land the file; each amendment rides a human-admitted commit (src: ARCHITECTURE.md:12).

The contract is mechanized, not aspirational: `scripts/gates/check_placement.py` parses the first fenced block under the `## §2` heading with `ENTRY_RE = ^[├└]──\s+(\S+)` (src: scripts/gates/check_placement.py:26), diffs those slots against the actual root-level items of `git ls-files` (src: scripts/gates/check_placement.py:45-52), and fails exit 2 on any undeclared root item. A declared slot with no files yet is legal — planned slots land in later slices (src: scripts/gates/check_placement.py:9-10). The gate rides the pre-commit hook (src: .githooks/pre-commit:70).

The `openwiki/` directory this wiki lives in is itself a §2 slot: a regenerable projection produced by the `repo-wiki-converge` skill, updated via the official update mode, tracked in git. `data/wiki-update/` is a sibling slot added for ISSUE-23: the runtime landing site for the factory delivery terminus's typed wiki-update requests and the digestion station's receipts (src: ARCHITECTURE.md:38-40) — see [data ledgers](data-ledgers.md) and [kb-ingest official port](kb-ingest/official-port.md).

## §3 — iron laws, each with its enforcement mechanism

The SSOT lists seven laws (src: ARCHITECTURE.md:45-59). What makes them laws rather than prose is that each has a mechanical teeth:

1. **Macro-loop gates hang on the host; micro-loop gates are CLI + exit code + receipt; the only seam is exit codes and receipts** (src: ARCHITECTURE.md:47-48). Mechanism: git hooks + `.claude/settings.json` on the host side ([git hooks](host-loop/git-hooks.md), [Claude host](host-loop/claude-host.md)); the factory's `trigger.sh` records four stage exit codes into a route-result JSON on the artifact side ([build pipeline](factory/build-pipeline.md)).
2. **Tracked files must not embed absolute home-root paths; historical evidence goes in an allowlist ledger, never rewritten** (src: ARCHITECTURE.md:49-50). Mechanism: `scripts/gates/check_root_coupling.py` with `root_coupling_allowlist.txt` ([structure gates](gates/structure-gates.md)); the migration engine copies allowlisted evidence verbatim because "rewriting evidence is forging evidence" (src: scripts/migrate/migrate_seed.py:14-16).
3. **Root passive context is ultra-thin and frozen during iteration; sandboxes use their own directory as host dir; real isolation materializes outside the tree** (src: ARCHITECTURE.md:51-52). Mechanism: the factory sandbox carries its own AGENTS.md/CLAUDE.md and its `portability.sh` extracts `HEAD:` via `git archive` to a directory outside the repository (src: loop_wiki/evolve-perfect-seed-repo-factory/PLAN.md:12-15).
4. **Commit gates read only the message + this repo's staged list; standing gates never read sibling checkouts; ref resolution requires an explicit `--peer` audit and is NOT_RUN without it** (src: ARCHITECTURE.md:53-54). Mechanism: the molecular validator's charter forbids sibling reads (src: .githooks/lib/validate_molecular_message.ts:5-11); the factory's `resolve-refs` prints `NOT_RUN` and exits 2 without `--peer` (src: loop_wiki/evolve-perfect-seed-repo-factory/src/cli.ts:42-47).
5. **Fast quality (format/lint/type) is an architecture-level hard gate: pre-commit scans staged (<5s) and the sandbox verify uses the same T0 definition; a fast green never impersonates the CQ/PU axes; human admit is always the terminal edge** (src: ARCHITECTURE.md:55-56). Mechanism: `scripts/gates/fast_quality.sh` is the single check definition with two mounts (src: scripts/gates/fast_quality.sh:2-12), and its receipt hard-codes `claim_boundary: "preflight-only-not-code-quality-axis"` (src: scripts/gates/fast_quality.sh:161).
6. **Missing tools go FATAL (exit 64), distinct from check failure (exit 2); absence must never read as green** (src: ARCHITECTURE.md:57-58). Mechanism: every gate and hook in the repo uses the 0/2/64 triple — e.g. `bootstrap.sh` (src: bootstrap.sh:8-9), `commit-msg` (src: .githooks/commit-msg:6), `fast_quality.sh` (src: scripts/gates/fast_quality.sh:39).
7. **Duplicate components must not be judged equivalent by name; equivalence = read the code + actually run it; load-bearing cases get rebuilt and measured side by side** (src: ARCHITECTURE.md:59). Worked example: the molecular gate was deliberately REBUILT from the source repo's validator rather than reused, with the stripped rules ledgered in its header (src: .githooks/lib/validate_molecular_message.ts:12-33) and the gap measured by `tests/tools/replay_corpus_parity.py`.

## Glossary: the three senses of "admit"

`CONTEXT.md` pins vocabulary the rest of the repo uses without redefining (src: CONTEXT.md:3-16):

- **activation admit** — arming a landed-but-inactive gate (e.g. renaming a `.staged` hook live).
- **ratification** — after-the-fact human judgment of an already-occurred event (side doors, credential events).
- **removal admit** — authorizing an irreversible deletion; the only kind with no rollback path.

G-gates all-green always yields only a **candidate**, never any kind of admit (src: CONTEXT.md:8, CONTEXT.md:16). Other pinned terms: **Intent-Slice** (`ISSUE-<n>`, ADR 0001), **protected surface** (paths whose change requires a molecular message — the closure of gates and hooks themselves), **receipt** (machine-verifiable execution evidence, frozen once written, single explicit exception `--force-receipt`), **evidence allowlist** (each entry is standing debt), **candidate**, **wiki-update request / receipt** (the typed `data/wiki-update/` artifact the factory delivery terminus writes on successful delivery, and the digestion station's execution evidence back-linking its `request_id`; three context lanes — fixed prompt pointers, a deterministic iteration delta, and a pointer to the openwiki-native backlog — with emergent content forbidden from landing anywhere but that backlog, src: CONTEXT.md:16-18).

## ADR 0001 — Intent-Slice vocabulary

Decision (2026-08-06, human-adjudicated): the only legal Intent-Slice form is `ISSUE-<n>`, where n resolves to the ts-skill-bettor Forgejo tracker (PRD #2, slices #3–#13, residual debt #14–#20 and onward) (src: docs/adr/0001-molecular-slice-vocabulary.md:13-15). Rejected alternatives: inheriting the source repo's three prefixes (would re-embed the topology the rebuild just stripped) and inventing a new numbering scheme (the tracker is already the intent-chain SSOT; a second numbering is dual-map drift) (src: docs/adr/0001-molecular-slice-vocabulary.md:16-21). Consequence explicitly recorded: the historical corpus-parity receipt was measured under the OLD vocabulary and is frozen evidence; replaying the same corpus under the new vocabulary gives a different verdict distribution, which is expected evolution, not a defect (src: docs/adr/0001-molecular-slice-vocabulary.md:25-27).

## Where to go next

- Entry point and task routing: [quickstart](quickstart.md)
- The hook chain that enforces commits: [git hooks](host-loop/git-hooks.md)
- The gates the hooks call: [fast quality](gates/fast-quality.md), [structure gates](gates/structure-gates.md)
- How the subtrees got here: [migration history](migration/history.md)
