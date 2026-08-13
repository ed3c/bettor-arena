# Bettor binding for `repo-agent-native`

This directory binds the portable `repo-agent-native` procedure from `ed3c/skills-shared` to Bettor's document graph, code-intelligence providers, output locations, assertions, and evidence boundaries.

It does not contain a copy of `SKILL.md`. The projected Skill remains a symlink under `.agents/skills/repo-agent-native`; `.claude/skills/repo-agent-native` is a second pointer surface. A copied body would silently shadow the shared procedure and is a hard failure.

## Document authority

| Path | Authority |
|---|---|
| [`binding.json`](binding.json) | machine-readable Skill identity, routes, capability slots, evidence ceilings, and output contract |
| [`provider-map.md`](provider-map.md) | why each capability is assigned to its current or candidate provider |
| [`assertions.md`](assertions.md) | executable and advisory assertion classes |
| `../../AGENTS.md` | repository-wide Agent operating law |
| `../../CONTEXT.md` | bounded Bettor vocabulary |
| `../../docs/agents/domain.md` | domain-context and ADR routing policy |
| `../../.mcp.json` | Claude Code-compatible project MCP launch declarations |
| `../../.codex/config.toml` | Codex project MCP policy and tool allowlist |
| `../../scripts/gates/check_repo_agent_native_binding.py` | deterministic binding hard gate |
| shared `repo-agent-native/SKILL.md` | portable workflow and evidence law |
| current source/tests/receipts | mechanism and execution evidence |
| Human Admit | provider activation, merge, promotion, durable-memory writeback, and rollback |

## Mandatory read order

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ docs/agents/domain.md
→ relevant docs/adr/
→ nearest directory README.md
→ this README and binding.json
→ shared repo-agent-native README/SKILL.md
→ matching capability modules only
→ module manifest/public contract/source/tests/receipts
→ exact issue and PR
```

`docs/agents/domain.md` adapts the useful policy from `setup-matt-pocock-skills`: root context, optional context maps, and ADRs are explicit Agent inputs. Bettor keeps its stronger dual-entrypoint model—canonical `AGENTS.md` plus thin `CLAUDE.md`—rather than choosing only one.

## Binding state machine

```text
SHARED SKILL CANDIDATE IDENTIFIED
→ PROJECTION SHAPE VERIFIED
→ BETTOR ROUTES VERIFIED
→ CAPABILITY CONFIGS COMPARED
→ EVIDENCE CEILINGS VERIFIED
→ FALLBACKS VERIFIED
→ DETERMINISTIC MUTATIONS KILLED
→ FRESH SESSION MATERIALIZED
→ CURRENT/CANDIDATE A/B EXECUTED
→ HUMAN ADMIT
```

Failure states:

```text
SHARED_SKILL_SHADOW_COPY
SHARED_SKILL_IDENTITY_STALE
REQUIRED_ROUTE_ABSENT
PROVIDER_CONFIG_DRIFT
PROVIDER_IDENTITY_UNPINNED
PROVIDER_STATE_OVERPROMOTED
PROVIDER_FALLBACK_ABSENT
SECRET_OR_HOST_PATH_IN_BINDING
MEMORY_AUTHORITY_COLLAPSE
GRAPH_WRITE_SURFACE_EXPOSED
PHYSICAL_AB_NOT_EXERCISED
```

## Capability data flow

```text
question + repository scope
        │
        ▼
deterministic source discovery (`git`, `rg`, direct read)
        │
        ├── GrepAI semantic/call candidates
        ├── repo-context-pack bounded Python context candidates
        ├── Serena symbol/reference/diagnostic candidates
        ├── code-graph provider candidate (not configured)
        └── project-memory provider candidate (not configured)
        │
        ▼
current source / manifest / ADR / tests / runtime readback
        │
        ▼
repo-agent-native output/v2
        │
        ▼
source-reference verifier + consumer binding gate
        │
        ▼
plan/spec/refactor handoff and Human boundary
```

A provider configuration proves only that a launch surface is declared. It does not prove installation, health, index freshness, authorization, completeness, or output correctness.

## Current evidence

- `grepai`, `repo-context-pack`, and `serena` have versioned launch declarations.
- Serena is pinned in both host surfaces; GrepAI currently resolves from host `PATH`, so its executable identity remains unpinned.
- `code-graph-rag` and `mem0` are research/admission candidates and are intentionally absent from project MCP configuration.
- No physical current-versus-candidate Claude Code or Codex A/B receipt is created by this binding branch.

Use `NOT_EXERCISED` for live provider and physical A/B state until subject-bound receipts exist.

## Code and assertions

```bash
python3 scripts/gates/check_repo_agent_native_binding.py --selftest
python3 scripts/gates/check_repo_agent_native_binding.py
```

The gate checks projection shape, routes, MCP configuration, candidate absence, pins, evidence ceilings, fallbacks, and secret/path leakage. It includes planted mutations. Model self-review and Markdown checklists remain advisory.

## Change contract

A change requires:

- exact shared Skill version/commit impact;
- route and nearest-README impact;
- provider identity, tool allowlist, write/effect, retention, and cleanup impact;
- deterministic positive and mutation controls;
- A/B case impact;
- current evidence state;
- rollback subject and Human Admit.
