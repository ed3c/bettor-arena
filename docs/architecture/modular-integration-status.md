# Bettor Arena Modular Integration Status

This file is the mutable implementation-status companion to [`modular-integration-requirements.md`](modular-integration-requirements.md), which remains the normative target contract.

The executable repository contracts, gates and exact-subject receipts are authoritative. This ledger explains them; it cannot turn missing or unexecuted evidence into PASS.

## Status vocabulary

| State | Meaning |
|---|---|
| `IMPLEMENTED` | The mechanism and its deterministic gate/negative control are present |
| `NOT_IMPLEMENTED` | The required mechanism is absent |
| `NOT_EXERCISED` | The mechanism exists, but the named live/provider/human path has not run for the current subject |
| `ABSENT` | A required input/tool/artifact is not present |
| `FAIL` | The mechanism ran and disagreed with the requirement |
| `PASS` | The named mechanism ran for the named subject and satisfied its contract |

These states are never normalized into one another.

## Landed deterministic control plane

### Phase 0 — Module catalog and composition

Status: **IMPLEMENTED**

- versioned module manifests and JSON Schemas;
- capability dependency resolution;
- exact component validation;
- duplicate-provider and path-overlap rejection;
- bettor-arena composition requirements;
- deterministic composition lock;
- repository-contained Agent entrypoint contract;
- fresh-clone exact-head GitHub verification.

Primary evidence:

```sh
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_lock.py resolve \
  --requirements .arena/compositions/bettor-arena.requirements.json
```

### Phase 1 — Complete tracked-path ownership

Status: **IMPLEMENTED**

Every tracked path resolves to exactly one module owner or one reviewed fallback class. Unowned, multiply owned, ambiguous fallback, stale fallback and implementation-hidden-as-evidence cases disagree independently.

Primary evidence:

```sh
python3 scripts/arena_ownership.py --selftest
python3 scripts/arena_lock.py ownership
```

The checked composition lock binds both `ownership_classes_sha256` and `ownership_sha256`.

### Phase 2 — Module-scoped proof identity and release aggregation

Status: **IMPLEMENTED**

- closure subjects are keyed by module-owned bytes and selected contracts rather than whole-repository HEAD alone;
- proof, independent control and mutation/hollow evidence remain distinct;
- unrelated module closures can remain valid when another module changes;
- dependency/proof-kernel changes invalidate transitive dependents;
- one composition release receipt aggregates exact selected subjects.

Primary evidence:

```sh
python3 scripts/arena_proof.py --selftest
python3 scripts/arena_proof.py check
```

Checked evidence:

- [`../../data/module-proof/subjects.lock.json`](../../data/module-proof/subjects.lock.json)
- [`../../data/module-proof/release-receipt.json`](../../data/module-proof/release-receipt.json)

### Phase 3 — Context Capsules and Claude/Codex carrier parity

Status: **IMPLEMENTED for deterministic materialization; live host canaries remain subject-specific**

- root/loop context manifests;
- frozen context lock;
- immutable ref resolution;
- disposable worktree materialization and cleanup;
- fixed allowlisted Claude Code and Codex CLI canaries;
- driver parity snapshot;
- missing context/tool and unrun carrier remain distinct from PASS.

Primary evidence:

```sh
python3 scripts/arena_context.py --selftest
python3 scripts/arena_context.py check
python3 scripts/arena_context.py parity
```

Live Claude/Codex availability, authentication and model execution are **`NOT_EXERCISED` unless a current carrier receipt explicitly records them**.

### Phase 4 — Default-deny stateless MCP runtime

Status: **IMPLEMENTED for the repository-supported closed carriers and external canary**

- Bun/TypeScript is the primary MCP runtime;
- tools are generated from the canonical `loopctl` surface plus explicit policy;
- exposure defaults to false;
- selected module closure only;
- typed packet / inline bundle / content-addressed carrier boundaries;
- immutable refs;
- disposable worktree/workspace cleanup;
- unknown arguments and dangerous tools fail closed;
- one external CTG consumer canary runs in CI;
- Python entrypoints remain compatibility shims, not a second policy source.

Primary evidence:

```sh
bun test loopctl/mcp_core.test.ts
bun loopctl/mcp_tools.ts --selftest
bun loopctl/mcp_runtime.ts --selftest
bun scripts/gates/check_mcp_policy.ts
sh tests/test_ctg_mcp_carrier.sh
```

Generic shell-over-MCP, mutable `main`, server-host absolute paths and secret-bearing payloads are not admitted.

### Phase 5 — Transactional project bootstrapper

Status: **IMPLEMENTED**

- consumer and embedded planning;
- deterministic dependency/module/Skill/runtime resolution;
- dry-run plan by default;
- render into a temporary tree;
- verify before apply;
- managed projection and orphan/conflict checks;
- append-only apply receipt;
- fail-closed rollback when target bytes drift after apply.

Primary evidence:

```sh
bun scripts/arena_project.ts --selftest
bun scripts/gates/check_project_bootstrap.ts
```

Project MCP approval, repository trust, permission widening, network policy and secret-bearing providers remain human-owned.

### Phase 6A — Logical origins and Browser Contract v2

Status: **IMPLEMENTED as deterministic contracts**

- one logical release across GitHub/Forgejo origin declarations;
- exact-commit/tree/release-manifest equivalence model;
- Browser Contract v2 actor/surface/transport/session/workflow/route/evidence separation;
- zero-network negative controls;
- exact GitHub PR-head checkout probe in CI;
- checked origin and browser status snapshots.

Primary evidence:

```sh
bun scripts/gates/check_environment_contracts.ts --selftest
bun scripts/gates/check_environment_contracts.ts
bun scripts/arena_origins.ts status
bun scripts/arena_browser.ts status
```

Current external boundary:

- live Forgejo reachability/equivalence: **`NOT_EXERCISED` unless a current immutable probe receipt exists**;
- signed-in browser providers and cloud browser brokers: **`NOT_EXERCISED`**;
- local signed-in profile/cookie transfer to cloud: **forbidden**, not a missing feature;
- browser contract PASS does not imply a provider session ran.

## Active delivery

- Parent modular-integration PRD: issue **#5**.
- Documentation convergence and cold-start README gate: issue **#27**.
- Immutable Agent Shield reference-consumer acceptance: issue **#24**.

## Remaining target work

### Reference consumer

Status: **NOT_IMPLEMENTED / active in issue #24**

The repository has not yet completed acceptance of the pinned `agent-shield-monorepo` module release as the first external reference consumer. Private-source reachability, selected capability validation and consumer initialization must remain separate evidence.

### Current live/provider admits

Status: **NOT_EXERCISED unless current receipts are supplied**

- current-subject live Claude Code carrier;
- current-subject live Codex CLI carrier;
- authenticated NotebookLM business run;
- signed-in browser routes;
- Forgejo/GitHub live environment equivalence;
- cloud MicroVM/container provider;
- Human Admit and production promotion/rollback.

### Cloud MicroVM provider

Status: **NOT_IMPLEMENTED and not promoted to an invariant**

E2B/Firecracker, Daytona and similar runtimes are research/provider candidates. Startup latency, license, isolation, networking, dependency image and billing claims require independent verification plus a provider runtime canary before a module manifest or release may rely on them.

## Documentation convergence verification

```sh
python3 scripts/gates/check_readme_coverage.py --selftest
python3 scripts/gates/check_readme_coverage.py
```

The gate requires a root/docs/control-plane navigation surface and one sibling README for every admitted module manifest. It does not require a README in every per-run or digest directory.

## Exact-head release verification

The GitHub workflow renders and compares:

- composition lock;
- Context Capsule lock and driver parity;
- module proof subjects and release receipt;
- MCP exposure snapshot;
- logical-origin status;
- browser status.

A green deterministic workflow proves only those named contracts for the checked commit. It does not proxy external provider or human evidence.
