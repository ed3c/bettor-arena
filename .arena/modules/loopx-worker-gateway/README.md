# `loopx-worker-gateway` module

Machine authority: [`module.json`](module.json)
Interface version: `1.0.0`

## Role

Owns the host-neutral Worker request/event/receipt contract, six-host descriptor registry, disposable fixture execution path, epistemic trace ceilings, cleanup controls and status separation for Codex CLI, Claude Code, Grok Build, OpenCode, Pi and Ante.

## Public control port

```sh
python3 loop_wiki/loopx-worker-gateway/scripts/gateway.py
```

The module is `control-only` and is not exposed through MCP in this terminal leaf.

## Capability boundary

**Provides**

```text
loopx.worker-gateway/v1
```

**Requires**

```text
loopx.contracts/v1
skill-execution.runner/v1
arena.proof-kernel/v1
```

## State Machine

```text
typed request
→ exact subject/Skill/context validation
→ adapter identity and epistemic ceiling
→ disposable workspace
→ process-group execution
→ normalized events/artifacts
→ path and cleanup checks
→ Worker receipt
→ independent Gates
```

The gateway stops at a Worker receipt. It cannot create a Gate PASS or canonical LoopX state transition.

## Current live state

```text
Codex CLI    NOT_EXERCISED
Claude Code  NOT_EXERCISED
Grok Build   NOT_EXERCISED
OpenCode     NOT_EXERCISED
Pi           NOT_EXERCISED
Ante         NOT_IMPLEMENTED
```

Fixture execution proves only the gateway mechanism.

## Evidence

```sh
sh loop_wiki/loopx-worker-gateway/tests/run-all.sh
```

Controls cover fake PASS, adapter/host mismatch, subject/Skill/context drift, path traversal, secret-shaped payload, fabricated gray-box internals, authority escalation, cleanup failure, a real fixture subprocess and disposable-worktree cleanup.

## Molecular boundary

This is a sibling of `loopx-ledger`: both depend on LoopX Contract v1, but neither consumes the other's implementation. Composition selection, public `loopctl`/MCP exposure, live host canaries, runtime-fabric attestation and release promotion remain separate leaves.

Merge remains a Human decision.
