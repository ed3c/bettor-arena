# Host Skill compatibility and document-route contract

Owner: [`harness-wiki`](../SKILL.md). This module defines how one canonical Skill body is projected into Codex CLI, Claude Code, Grok Build, OpenCode, Pi, and Ante without creating six divergent procedures.

## One portable package, several host projections

The portable intersection is the Agent Skills package:

```text
<skill-id>/
├── SKILL.md                 # required: YAML frontmatter + Markdown procedure
├── scripts/                 # optional executable helpers
├── references/              # optional on-demand knowledge
├── assets/                  # optional templates/static data
└── agents/openai.yaml       # optional Codex/OpenAI interface metadata
```

Canonical portable frontmatter:

```yaml
---
name: lower-kebab-case
# State what it does and when it should trigger.
description: >-
  ...
license: Apache-2.0                  # optional
compatibility: Requires git ...     # optional
metadata:                            # optional string-to-string map
  owner: ed3c
  version: "1"
---
```

`name` and `description` are the only safe fields that every target should be expected to understand. `license`, `compatibility`, and `metadata` are portable optional fields. `allowed-tools` exists in the open Agent Skills specification but is experimental and does not replace host policy. Host-only fields belong in a generated projection or sidecar when their semantics affect security or invocation.

## Research subjects and evidence state

- Grok Build reference subject: `xai-org/grok-build@e5fd4816d43260c15ba785f103990c1ed6cea230`. The repository is Apache-2.0 and source-visible, but this refactor has not executed its headless/ACP worker or verified a loaded Skill digest; state remains `NOT_EXERCISED`.
- Ante remains an experimental compatibility target. Its public protocol/docs can define an adapter, but its core Harness must not be labeled white-box unless the exact runtime source becomes publicly inspectable.

## Host matrix

| Host | Project Skill discovery | Repository instruction route | Host extensions | Executable carrier | Bettor classification |
|---|---|---|---|---|---|
| Codex CLI | `.agents/skills/**/SKILL.md`; `.codex/skills/**/SKILL.md` | `AGENTS.override.md` then `AGENTS.md`, accumulated from root to working directory | `agents/openai.yaml`; Codex reads `name` and `description` from `SKILL.md` | Codex tools/sandbox or a typed external runner | source-visible host; model remains provider-controlled |
| Claude Code | `.claude/skills/<id>/SKILL.md`; nested package Skills on demand | `CLAUDE.md` and explicit `@path` imports; repository may retain canonical `AGENTS.md` with thin Claude projection | invocation/subagent/tool fields, dynamic `!command`, legacy `.claude/commands/*.md` | Claude tools/hooks/SDK, still subject to independent gates | gray-box worker with strong host controls |
| Grok Build | `.grok/skills`, `.grok/commands`, compatibility roots including `.agents/skills` | recognized project-rule files include `AGENTS.md` and `CLAUDE.md` variants, loaded root to working directory | `when-to-use`, invocation/tool/model fields, `grok inspect --json` | source-visible Rust CLI/headless/ACP worker | white-box reference Harness; provider/model still separate |
| OpenCode | `.opencode/skills`, `.agents/skills`, `.claude/skills`, project and global | `AGENTS.md`; explicit `opencode.json(c)` instruction sources may add routes | v1 recognizes only standard portable fields; v2 adds path IDs, flat Markdown and catalogs | native skill tool plus permission-controlled Agent tools | open-source host; source of truth remains external gates |
| Pi | `.pi/skills`, `.agents/skills`, global equivalents, packages and `--skill` | project instruction files plus configured context; do not assume another host's imports | lenient Agent Skills parsing; TypeScript extensions add tools/events/commands | built-in tools, RPC/SDK, or extensions; Pi itself has no built-in OS permission boundary | white-box reference host; sandbox externally |
| Ante | `.ante/skills`, `.agents/skills`, `.claude/skills` and user equivalents | project `AGENTS.md`, with documented Claude fallback behavior | Ante-specific invocation metadata; unsupported fields may be ignored | JSONL/headless/SDK protocol where available | experimental gray-box; core Harness is not fully public |

## Bettor canonical path policy

```text
skills-shared/skills/<id>/SKILL.md     canonical portable procedure
             │
             ├── immutable requirements-filtered bundle
             └── local development projection
                         │
                         ▼
bettor-arena/.agents/skills/<id>       universal project Skill surface
                         │
             ┌───────────┼──────────────┬──────────────┬──────────────┐
             ▼           ▼              ▼              ▼              ▼
      .claude/skills   Codex native   Grok compatibility OpenCode compat Pi/Ante compat
      pointer          `.agents`      `.agents`         `.agents`      `.agents`
```

Do not copy a shared `SKILL.md` into each host directory. A copy becomes a shadow authority and can drift. A symlink is only a local-development projection; releases must materialize an immutable, digest-bound bundle.

## Document names and their real jobs

| Document | Job | Not its job |
|---|---|---|
| `AGENTS.md` | Canonical repository operating law and multi-hop route for Agent-compatible hosts | procedural Skill body or mutable run state |
| `CLAUDE.md` | Thin Claude Code projection/import surface | second architecture SSOT |
| `CONTEXT.md` | Stable bounded vocabulary; in Bettor the root file stays glossary-only | provider health, implementation detail, todo ledger, memory dump |
| `CONTEXT-MAP.md` | Optional pointer map when multiple real bounded contexts exist | required boilerplate or flattened giant prompt |
| `docs/agents/domain.md` | Policy for locating context files, ADRs and nearest READMEs | duplicate glossary or code mechanism |
| `docs/adr/**` | Durable decisions with status and supersession | current implementation proof |
| nearest `README.md` | Local owner, boundary, inputs, outputs and change contract | global law |
| `SKILL.md` | On-demand procedure and resource router | permission, execution truth, or state authority |
| machine manifest/schema | Exact interface and validation contract | human explanation |
| execution receipt | What ran against which immutable subject | general capability claim |

The useful part of `setup-matt-pocock-skills` is the explicit context/ADR/issue-tracker route and the rule not to create parallel root instruction files. Bettor keeps its stronger `AGENTS.md` canonical entrypoint plus thin `CLAUDE.md`; it should not replace that with a Claude-only root.

## Host-extension rule

A canonical Skill may declare only portable semantics. Generate host projections for semantics that are not equivalent:

```text
portable intent
+ host capability descriptor
+ repository permission policy
→ generated host projection
→ projection digest
→ discovery/invocation receipt
```

Examples:

- Claude `disable-model-invocation` is not a Codex hard control. Codex needs its own `agents/openai.yaml` invocation policy.
- Claude `allowed-tools` or Grok/Pi equivalents are model-facing hints unless the host enforces them.
- OpenCode permission rules live in OpenCode configuration and should not be inferred from unknown frontmatter fields.
- Pi extensions can register executable tools; a Skill alone cannot.
- Ante fields must not be treated as portable unless the current Ante version documents them.

## Admission gate

A host is `SUPPORTED` only when all are recorded:

1. exact host version or immutable source identity;
2. Skill discovery path and loaded Skill digest;
3. instruction-route digest;
4. tool/permission/sandbox identity;
5. one positive invocation and one wrong/missing/disabled Skill control;
6. typed execution and assertion receipt when code is run;
7. cleanup/residue status;
8. Human Admit where required.

Installation, a path on disk, or a successful `skills/list` is not an execution PASS.
