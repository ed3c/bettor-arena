# AGENTS.md — bettor-arena Codex / cross-host entry

Engineering SSOT is [`ARCHITECTURE.md`](ARCHITECTURE.md); the complete modular target is [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md). This file owns mandatory routing, non-negotiable boundaries, and the completion report. Do not copy the full specification into passive root context.

`AGENTS.md` and `CLAUDE.md` are governed projections. Repo-local staged gates validate them without reading sibling checkouts. Cross-repository generators are promotion-time tools only.

## Mandatory multi-hop read order

For module, Macro/Micro loop, Skills, runtime-env, proof, MCP, Claude/Codex adapter, browser, GitHub/Forgejo origin, external bootstrap, or Agent Shield work, read in order:

1. [`README.md`](README.md)
2. [`CONTEXT.md`](CONTEXT.md)
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) §1–§3
4. [`docs/INDEX.md`](docs/INDEX.md)
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md)
6. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md)
7. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md)
8. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md)
9. [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md)
10. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md)
11. [`docs/agent-runtime-integration.md`](docs/agent-runtime-integration.md)
12. `sh loopctl/loopctl.sh contract`
13. the target module/loop nearest README, passive context (`AGENTS.md`, `CLAUDE.md`, `PROMPT.md`, `ROUTES.md`, `PLAN.md`, law layer), machine manifest/contract, and current receipts.

A missing route, owner, module, issue, parent, eval, or evidence subject is `ABSENT`; do not infer it. Open a new Agent session after changing passive context before claiming it was read.

The target contract is not a completion declaration. Only exact current files and subject-bound receipts establish `IMPLEMENTED` or `PASS`; a mechanism that exists but has not run remains `NOT_EXERCISED`.

## Bettor Arena role

```text
Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper
```

The minimum modularity test remains: no inbound private-code dependency, module-owned verify and selftest, real relocation/isolation, and a hollow/mutation control that can turn each green result red.

## Shared document-route interface

Bettor Arena implements the same route names consumed by `skills-shared`, `runtime-env`, and `agent-shield-monorepo`:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

A README explains ownership and routing; it never replaces manifests, schemas, CLI contracts, scripts, verifiers, receipts, or Git history. Each hop leaves a local summary before linking away.

## Macro / Micro boundary

| | Macro / Composition loop | Micro / Task loop |
|---|---|---|
| Owns | module selection, dependency/conflict resolution, projection, proof matrix, Human Admit, lock, promotion/rollback | typed task, bounded iteration, module-local state, typed result, named exits, module proof/control |
| Reads | manifests, composition locks, public capabilities, receipts | its own passive context, source, private executable |
| Uses another module | capability and `loopctl` public port | typed packet → public port → artifact/receipt ref |
| Must not | learn private flags, prompt fragments, per-run temp | source/import another module internals or read another `_engine-run/` |

The only seam is the public interface, typed packet, artifact reference, exit code, and receipt. Human Admit, promotion, and production rollback belong to the Macro/trusted operator plane.

## Internal / external consumption

```text
Symlink = local development channel
Bundle + lock = reproducible execution channel
CLI / MCP = public consumption channel
```

- Inside one module, its public adapter may call executables in its own closure.
- Same-repo cross-module use goes through a stable library API or `loopctl`.
- External repositories default to immutable bettor release + stateless MCP; embedded bundles are for offline/custom ownership.
- Symlinks may project shared Skill/passive instructions locally; they must not carry cross-repo executables, venvs, `node_modules`, runtime checkouts, browser profiles, cookies, credentials, or cloud dependencies.

## CLI, MCP, and passive context

1. `loopctl` is the canonical CLI; MCP tools are generated from the CLI contract.
2. Commands default hidden unless `external_policy.exposed=true`.
3. Every MCP call pins an immutable release and uses a disposable worktree/bundle, never the owner live checkout.
4. Callers cannot provide server-host paths, arbitrary `cwd`, private flags, secrets, or browser profiles.
5. Accept only typed packets, inline bundles, or content-addressed artifact references; verify cleanup.
6. Macro work is packetized (`plan → resolve → verify → status`), not one long stateful call.
7. Live-repo apply, Human Admit, promotion, production rollback, secret rotation, and permission widening are never model tools.

MCP wraps **context materialization**, not arbitrary prompt execution:

```text
immutable release
→ materialize root + loop native context
→ freeze digest
→ cwd = loop root
→ allowlisted claude -p / codex exec
→ typed output validation
→ context + driver receipt
```

Root context owns global laws; loop context owns `PROMPT.md`, `ROUTES.md`, `PLAN.md`, and the eight-base mapping. Do not flatten both layers into one ad-hoc MCP prompt and delete the native files.

## Proof and anti-jitter

Each module needs independent arrival paths:

- `proof`: traversed context/harness/artifact claim;
- `control`: execute the real public port and observe paths/exits;
- `mutation` or hollow: a load-bearing guard must turn red when broken;
- `consumer-canary`: external Claude/Codex calls the released adapter;
- `release-receipt`: aggregate evidence for one composition subject.

`ABSENT`, `FAIL`, `NOT_EXERCISED`, hashed-not-run, and `PASS` never proxy one another. Exit codes propagate unchanged. Module proof identity is closure-scoped: changing A invalidates A and transitive dependents, not unrelated B merely because repository HEAD moved.

## Conflict, Skills, runtime, origins, browser

- Every tracked path has exactly one module owner or an explicit generated/evidence classification.
- Root projections are deterministically generated from module fragments; modules do not maintain parallel root copies.
- Modules exchange typed packets/artifacts/receipts; entrypoints receive exact environment allowlists.
- Skill closure is requirements-filtered for selected modules. Shared/repo-owned name collision or incompatible bytes is RED.
- `SKILL.md` contains generalized procedure/method/laws; shared `references/` contains generic contracts; shared `modules/` contains domain examples loaded on demand. Consumer-specific facts live in `.skill-bindings/` and nearest READMEs.
- `runtime-env` synchronizes secret-free projections. Consumer gates are offline, sibling-independent, and never auto-sync.
- Forgejo may be local authoring and GitHub cloud distribution for one logical release; equivalence requires exact commit, tree, or release-manifest evidence. Never fall back to mutable `main`.
- Claude Code, Codex CLI, and agy are actors; Playwright, stealth-browser, and Antigravity CDP are transports/adapters. Signed-in profiles/sessions never file-sync local→cloud.
- `gemini-conversation-research` body is file-only; `dr-research-loop` browser lane is optional untrusted Stage 1; `external-verify` prefers raw primary evidence and records browser downgrade.

Agent Shield product implementation belongs in `agent-shield-monorepo`; bettor consumes selected immutable modules. PDF/document ingest is an independent module. E2B/Firecracker, startup latency, cost, license, isolation, provider capability, mobile, wallet, and security claims are source inputs until independently verified and exercised.

## Four-repository integration

```text
skills-shared immutable procedural Skill release
+ runtime-env secret-free binding/workload/policy
→ bettor module/Skill/runtime composition and proof subject
→ immutable loopctl/MCP/bootstrap release
→ Agent Shield provider/product canaries
→ bettor external-release acceptance
→ Human promotion or rollback
```

Read [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Mutable sibling checkouts and local symlinks are never release identity.

## Evidence vocabulary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Source prose, diagrams, package presence, old SHAs, skipped/no-runner jobs, another provider, or another environment cannot create live PASS.

## Completion contract

Before stopping, report:

```text
changed module IDs / interface versions / closure digests
changed document routes and directory owners
affected transitive dependents
changed public CLI / MCP surface
path ownership conflicts
proof / control / mutation-hollow results
Claude / Codex adapter results
GitHub / Forgejo origin and equivalence status
browser / provider / external-consumer canary status
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
rollback subject
Human Admit and next merge order
```

Missing an applicable item forbids a claim that modular integration is complete.

## Rule → evidence routing

Detailed requirements and current/target gaps live in the modular requirements/status documents. Eight-base worked evidence lives in `loop_wiki/evolve-perfect-seed-repo-factory/modules/eight-base-laws.md`.

| Law | Evidence Harness |
|---|---|
| Green value depends on arrival; two independent arrivals settle | eight-base arrival table; sandbox green cannot proxy production/Human Admit |
| An instrument must turn red | B3 `selftest.sh` hollow + `portability.sh` negative control |
| Absence is not denial; status propagates | B2 per-step exits; unexecuted state is `not_run` |
| A module does not depend upward; relocation proves separation | B5 extraction, isolated install, verify, and negative control |
