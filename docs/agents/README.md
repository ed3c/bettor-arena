# Agent-facing document policy

`docs/agents/` contains small policy adapters that tell coding Agents how to consume Bettor's existing authoritative documents. It does not duplicate architecture, current state, issue data, or source truth.

## Document authority

| Path | Authority |
|---|---|
| [`domain.md`](domain.md) | root context, optional context map, ADR, nearest-README, and missing-route policy |
| [`issue-tracker.md`](issue-tracker.md) | issue/PR system-of-record, read/write, and cross-origin traceability policy |
| [`../../CONTEXT.md`](../../CONTEXT.md) | bounded Bettor glossary and stable domain terms |
| [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) | engineering placement and invariant SSOT |
| [`../architecture/`](../architecture/) | modular-integration target and mutable phase/status documents |
| [`../../.skill-bindings/repo-agent-native/`](../../.skill-bindings/repo-agent-native/) | consumer binding for source-anchored repository analysis |
| nearest directory `README.md` | local owner, interface, inputs, outputs, evidence, and change contract |
| source/manifests/tests/receipts | mechanism and execution authority |

## Mandatory route

For repository-analysis and brownfield-planning tasks:

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ docs/agents/domain.md
→ relevant docs/adr/
→ nearest directory README.md
→ repo-agent-native binding and shared procedure
→ module/public contract/source/tests/receipts
→ exact issue and PR
```

The route is progressive. Do not recursively load every document. Stop when the smallest sufficient authoritative set has been read and unresolved routes are explicit.

## Inheritance

A directory inherits the nearest README only while it introduces no new owner, public interface, state machine, context domain, source/evidence class, provider boundary, or generated/versioned-data rule. A new boundary requires a local README or a reviewed explicit redirect.

## Evidence boundary

These policy files establish routing rules only. They do not prove provider installation, index freshness, code behavior, runtime execution, issue state, origin equivalence, or merge readiness.

## Change contract

A policy change must name the route/authority problem, affected Skills and consumers, positive and missing/stale/conflicting-route controls, context-budget and privacy impact, migration/rollback subject, exact issue/PR, and Human Admit.
