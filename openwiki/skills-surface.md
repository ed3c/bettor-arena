---
type: Reference
title: Skills surface — single home, host pointers
description: The .agents/skills host-neutral content SSOT, the .claude/skills symlink surface, the module-owned exception, and how the pointer contract is enforced and was migrated.
tags: [skills, ssot, pointers]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [skills-single-home, host-pointers]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Skills surface — single home, host pointers

Since S5 (commit ae3a2db), skill CONTENT exists exactly once, host-neutral, under `.agents/skills/`; `.claude/skills/` holds only symlinks that resolve into `.agents/skills/` or a module-owned skill home (src: scripts/gates/check_skill_pointers.py:4-8; ARCHITECTURE.md:24, 27-28). The contract is enforced by [check_skill_pointers](gates/structure-gates.md) on every commit.

## The twenty content homes

`.agents/skills/` currently holds twenty skills, mirrored one-to-one by `.claude/skills/` symlinks: autoresearch-composer, dr-research-loop, dr-to-mvp, external-verify, fold-in, forgejo-loop-ops, gemini-conversation-research, harness-wiki, html-for-decisions, judge-loop-chooser, loop-harness-review-handoff, loop-harness-standard, path-b-reduction, product-ops, repo-agent-native, repo-wiki-converge, sdlc-plan-composer, skill-authoring, truth-verify-loop, unknown-discovery-composer. Their internal methodology is each skill's own SSOT and outside this wiki's scope (the wiki documents the surface and contract, per the documented scope brief in the init run).

## The module-owned exception

`repo-wiki-converge` is special: its content home is `kb-ingest/skill/` (the module owns its skill; the SKILL.md documents `$MODULE` = the directory above it, src: kb-ingest/skill/SKILL.md:23-28), and BOTH `.agents/skills/repo-wiki-converge` and `.claude/skills/repo-wiki-converge` are symlinks into it. The gate's `ALLOWED_TARGET_RELS` names `kb-ingest/skill` explicitly (src: scripts/gates/check_skill_pointers.py:33), §2 admits module-owned symlinks since commit 6f06881, and the kb-ingest module gate's `host-skill-links` profile asserts the same fact from the module's side (src: kb-ingest/host-profile.json:17, 25).

## How the contract is enforced

Three invariants, checked against tracked and untracked-visible files: host entries are symlinks resolving inside an allowed home (no real files, no escapes); no `.agents/skills/` symlink resolves back into `.claude/` (content never lives behind a host entry); and no two real SKILL.md files repo-wide share a skill-directory name — a residual copy would re-create the dual-home drift S5 removed (src: scripts/gates/check_skill_pointers.py:8-19). Full mechanics: [structure gates](gates/structure-gates.md).

## Migration relationship

The skills subtree was the `agents-skills` component of the [migration manifest](migration/engine.md); its port-lineage `retarget-map.md` ledgers and historical-evidence modules were copied VERBATIM under the evidence allowlist (reasons `port-lineage-ledger` / `historical-evidence-foreign-root-anchor`) and declared into `scripts/gates/root_coupling_allowlist.txt` rather than rewritten (src: data/migration/manifest.json evidence_allowlist; scripts/migrate/migrate_seed.py:13-16). The applied receipt is `data/migration/report-f3776cb-agents-skills.json` ([data ledgers](data-ledgers.md)).

## Sandbox-local skills

The factory sandbox and its generated repos carry their OWN `.agents/` trees (`seed-factory-router` agent, `perfect-seed-domain` skill, and each product's `seed-repo-operator`) — deliberately outside the host skills surface, because the sandbox is its own host (iron law 3, src: ARCHITECTURE.md:47-48). See [factory overview](factory/overview.md) and [generated repo](factory/generated-repo.md).
