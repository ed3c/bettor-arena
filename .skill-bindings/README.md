# `.skill-bindings/` — repo-owned domain bindings

Owner: bettor-specific retargeting of portable shared procedures.

```text
shared SKILL.md procedural core
→ consumer requirements/binding
→ repo-owned domain registry/config
→ fixed public workflow/receipt
```

Bindings may name bettor modules, repositories, routes, fixtures, and receipt
locations. They must not duplicate the canonical shared Skill body or store
secrets/sessions.

The governing dependency and monotonicity rules are in [`../docs/architecture/DOMAIN_DECOUPLING.md`](../docs/architecture/DOMAIN_DECOUPLING.md). A binding may tighten constraints, narrow effects, increase evidence, or reduce authority. A binding may not weaken the shared hard gates or promote mutable/local/fixture state into release or production authority.

## Current bindings

- [`repo-agent-native/README.md`](repo-agent-native/README.md) — existing
  source-grounded Agent binding and measurement boundary.
- [`agentic-tech-lead-orchestration/README.md`](agentic-tech-lead-orchestration/README.md)
  — immutable candidate binding for contract-first DAG decomposition,
  Worktree Worker leases, deterministic code-intelligence roles, bounded
  tournament selection, and Stacked PR handoff.

Directory presence is not shared registry admission. Each binding preserves
its own candidate state, runtime evidence ceiling, and Human-owned operations.
