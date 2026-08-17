# Bettor Arena documentation index

## Root routes

- [`../README.md`](../README.md) — project role, PDF-integration verdict, directory/state map and public entrypoints.
- [`../AGENTS.md`](../AGENTS.md) — mandatory Agent procedure, PDF verification and completion contract.
- [`../CLAUDE.md`](../CLAUDE.md) — Claude Code thin projection.
- [`../CONTEXT.md`](../CONTEXT.md) — current four-repository/PDF handoff and glossary.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — stable placement and engineering invariants.

## Current Tech Lead + Shadow closure route

Read this route before using a historical Stack snapshot or claiming that a
PDF/article issue is closed:

- [`architecture/tech-lead-shadow-monitor/AGENTS.md`](architecture/tech-lead-shadow-monitor/AGENTS.md) — mandatory Tech Lead/Shadow procedure, writer leases and stop conditions.
- [`architecture/tech-lead-shadow-monitor/README.md`](architecture/tech-lead-shadow-monitor/README.md) — current directory → State Machine map, DAG, data flow, molecular PR index, closure status and Local Handoff queue.
- [`architecture/tech-lead-shadow-monitor/closure-matrix.json`](architecture/tech-lead-shadow-monitor/closure-matrix.json) — machine-readable real-problem denominator and evidence ceilings.
- [`traceability/local-handoff-execution-queue.json`](traceability/local-handoff-execution-queue.json) — the one canonical local/runtime continuation queue.

`traceability/STACK_PR_INDEX.md` retains historical narrative and can lag current
GitHub metadata. The closure monitor identifies the current subject; GitHub
issue/PR metadata remains current external authority.

## Dual-Agent source-problem closure route

This route specializes the parent Tech Lead + Shadow monitor for the uploaded
`双 Agent 架构：云端本地协同` source. The PDF remains `SOURCE_PROPOSAL`; this
route records owners and missing evidence rather than promoting its claims:

- [`architecture/dual-agent-closure/AGENTS.md`](architecture/dual-agent-closure/AGENTS.md) — mandatory source classification, Tech Lead packet, authority, writer-lease, Shadow-review and stop laws.
- [`architecture/dual-agent-closure/README.md`](architecture/dual-agent-closure/README.md) — source-problem denominator, current closure verdict, cross-repository directory → State Machine → DAG → data-flow map, issue matrix and Molecular Stack PR index.
- [`architecture/dual-agent-closure/closure-matrix.json`](architecture/dual-agent-closure/closure-matrix.json) — machine-readable problem, repository-plane, issue, process-edge, evidence-stage and forbidden-promotion matrix.

Issue [`#187`](https://github.com/ed3c/bettor-arena/issues/187) owns this route.
Its branch is a **true documentation child** of the unmerged Tech Lead/Shadow
parent PR because it consumes that parent's route and closure vocabulary. The
process DAG recorded here is not Git ancestry: cross-repository prerequisites
remain issue/evidence edges, while Git Town children require actual unmerged-byte
dependency.

The route preserves these distinct states:

```text
source problem bound
!= mechanism implemented
!= deterministic PASS
!= physical local/cloud execution
!= user-outcome verification
!= Human Admit
!= licensed release
!= production operation and rollback
```

## Standard multi-hop routes

- [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) — route names and assertions.
- [`architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](architecture/PDF_HARNESS_INTEGRATION_AUDIT.md) — source proposal versus current Bettor mechanisms.
- [`architecture/pdf-harness-integration.matrix.json`](architecture/pdf-harness-integration.matrix.json) — machine-readable component states and evidence paths.
- [`architecture/DIRECTORY_STATE_MACHINE_MAP.md`](architecture/DIRECTORY_STATE_MACHINE_MAP.md) — directory owners, inputs, outputs, transitions and data flow.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — current State Machines and missing LoopX target.
- [`architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md`](architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md) — LoopX-specific requirement, authority and gap audit.
- [`architecture/pdf-loopx-harness.integration.json`](architecture/pdf-loopx-harness.integration.json) — executable LoopX audit contract.
- [`git/README.md`](git/README.md) — repository-owned Git Town adoption and Stack policy.
- [`git/REPO_PROFILE.md`](git/REPO_PROFILE.md) — observed repository shape the Stack policy is bound to.
- [`git/STACKED_PRS.md`](git/STACKED_PRS.md) — historical construction, retarget and land rules.
- [`git/WORKER_PROTOCOL.md`](git/WORKER_PROTOCOL.md) — what a Worker session may and may not do to a Stack.
- [`git/GIT_TOWN_ADMISSION.md`](git/GIT_TOWN_ADMISSION.md) — admission state of the Git Town binary itself.
- [`git/AUTOMATED_ADMISSION.md`](git/AUTOMATED_ADMISSION.md) — exact-subject authority for automated delivery, queue, provider and release operations.
- [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) — four-repository ownership and release flow.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) — source/decision/issue/PR/eval/receipt history.
- [`traceability/STACK_PR_INDEX.md`](traceability/STACK_PR_INDEX.md) — historical molecular topology narrative.

## Canonical modular contracts

- [`architecture/modular-integration-requirements.md`](architecture/modular-integration-requirements.md) — complete target contract.
- [`architecture/modular-integration-status.md`](architecture/modular-integration-status.md) — current implemented/unexercised status.
- [`agent-runtime-integration.md`](agent-runtime-integration.md) — Skill/runtime/host adapter aggregate.
- [`runtime-env-integration.md`](runtime-env-integration.md) — runtime projection and consumer verification.

## Machine and local-owner routes

- [`.arena/`](../.arena/README.md) — module/composition/context/origin/browser control plane.
- [`.agents/`](../.agents/README.md) — Skill requirements, bindings, module set and local projections.
- [`.runtime-env/`](../.runtime-env/README.md) — secret-free runtime consumer projection.
- [`.skill-bindings/`](../.skill-bindings/README.md) — repo-owned domain bindings for shared procedures.
- [`loopctl/`](../loopctl/README.md) — canonical CLI and stateless MCP runtime.
- [`proof_workflow/`](../proof_workflow/README.md) — proof/control/mutation semantics.
- [`data/`](../data/README.md) — generated snapshots and receipts.

## Validation

```sh
python3 scripts/gates/check_tech_lead_shadow_closure.py
python3 scripts/gates/check_tech_lead_shadow_closure.py --selftest
python3 scripts/gates/check_local_handoff_execution_queue.py
python3 scripts/gates/check_local_handoff_execution_queue.py --selftest
python3 -m json.tool docs/architecture/dual-agent-closure/closure-matrix.json >/dev/null
```

The nearest README routes to machine authority. Prose never overrides manifests,
contracts, scripts, tests, receipts, Git history, local runtime observations, or
Human admission.
