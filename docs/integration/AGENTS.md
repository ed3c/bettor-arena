# AGENTS.md — Bettor cross-repository integration audit

This file governs `docs/integration/`. Root [`../../AGENTS.md`](../../AGENTS.md) remains repository-wide authority.

## Mandatory read order

For `runtime-env`, Agent Shield, PDF architecture, cross-repository data flow or molecular Stack work:

1. [`../../README.md`](../../README.md)
2. [`../../AGENTS.md`](../../AGENTS.md)
3. [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md)
4. [`../INDEX.md`](../INDEX.md)
5. [`../architecture/STATE_MACHINES.md`](../architecture/STATE_MACHINES.md)
6. [`CROSS_REPO_INTEGRATION.md`](CROSS_REPO_INTEGRATION.md)
7. [`AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md`](AGENT_SHIELD_PDF_MODULAR_INTEGRATION_AUDIT.md)
8. [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md)
9. `.runtime-env/requirements.json`, the generated binding/workload/policies and their source commit/tree.
10. Agent Shield's exact status ledger, Stack plan, issue, PR base/head and immutable implementation subject.

## Evidence rules

- The PDF is a `SOURCE_PROPOSAL`, not repository truth.
- Its target monorepo is Agent Shield. Do not copy domain product directories into Bettor to claim integration.
- Keep Runtime Contract, Integration / Acceptance and Domain Product transitions separate.
- A checked binding is evaluated against an explicitly named intended source commit/tree. Upstream branch movement does not authorize automatic sync.
- `STALE_SOURCE_PIN` means review is required. It does not by itself prove the pinned binding invalid.
- A provider-neutral contract can be PASS while every native provider remains `NOT_IMPLEMENTED` or `NOT_EXERCISED`.
- Package presence, permissive direct licensing, source prose, issue creation, branch creation, Git Town sync or merged foundation code cannot produce product or production PASS.
- Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY` and `STALE_SOURCE_PIN` as distinct states.
- Secrets, browser/device profiles, OAuth sessions, NFC material, TSS shards, private keys, `.env` values and host paths never enter the audit.
- Absolute-security and zero-legal-risk claims are forbidden.

## Git Town / Stack rules

`bettor-arena` has no repository-owned `.git-town.toml`. Agent Shield owns the domain-product Git Town configuration and Phase 3–6 Stack.

```text
foundation
→ path-disjoint sibling leaves
→ true child only when unmerged bytes are consumed
→ terminal leaf evidence
→ phase convergence
→ reference-consumer convergence
→ Human Admit
```

Every audit must name:

```text
issue
branch
base branch and base commit
head commit/tree
sibling / true-child / terminal / convergence class
owned paths and exclusions
positive and disagreement controls
current evidence state
remaining gaps
rollback subject
```

GitHub base/head/merge metadata is publication truth. A Git Town command exit is branch-movement evidence only.

## Completion contract

Do not claim end-to-end modular integration until one immutable subject proves:

```text
fresh or explicitly accepted runtime pin
compatible Skill/runtime/module closure
Bettor proof + independent control + mutation/hollow
Agent Shield local/cloud provider canaries
product/mobile canaries
security/hardware/settlement canaries
Bettor reference-consumer parity
Claude and Codex carrier canaries
GitHub and Forgejo equivalence
cleanup/residue
aggregate release receipt
Human Admit
rollback subject
```

Missing evidence remains named, not averaged into a percentage or compressed into PASS.