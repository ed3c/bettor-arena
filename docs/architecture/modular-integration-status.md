# Bettor Arena Modular Integration Status

This file is the mutable implementation-status companion to
`modular-integration-requirements.md`, which remains the normative target
contract. When the target document's historical current-state section differs
from this file, this file is authoritative for what has actually landed.

## Phase 0 — executable module catalog

Status: **IMPLEMENTED on `main` by PR #4, merge commit
`5ff5e374fa1113451796c3136d0d4d86449e9c11`. Evidence is the
repository-contained gates and exact-head GitHub workflow, not this sentence.**

Implemented:

- `.arena/schemas/` for module, composition requirements, and composition lock;
- eleven current module manifests;
- bettor-arena owner composition requirements;
- deterministic composition lock with per-manifest SHA-256;
- capability dependency resolution;
- requested/required component validation;
- duplicate capability-provider rejection;
- overlapping ownership-root rejection;
- `catalog`, `check`, and `resolve` commands in `scripts/arena_modules.py`;
- positive and negative controls;
- repository-contained `AGENTS.md` / `CLAUDE.md` contract;
- staged-tree pre-commit checks with no sibling checkout;
- GitHub fresh-clone workflow for the Phase 0 gates.

Current limitation:

- ownership validation covers declared roots and rejects overlap; it does not yet
  prove that every tracked file has a module owner;
- manifests describe current proof/control entrypoints, but receipts remain the
  existing repo-commit-scoped v1 form;
- no public `loopctl module` surface has been added, so the Arena surface version
  has not changed.

## Active delivery

- Parent PRD: issue #5.
- Current slice: issue #6, full tracked-path ownership coverage.

## Remaining target phases

- **NOT_IMPLEMENTED:** full tracked-path ownership coverage (issue #6);
- **NOT_IMPLEMENTED:** module-scoped proof v2 and transitive receipt invalidation;
- **NOT_IMPLEMENTED:** Context Capsule and Claude/Codex driver parity;
- **NOT_IMPLEMENTED:** stateless MCP default-deny generation from module policy;
- **NOT_IMPLEMENTED:** project plan/apply/verify/rollback initializer;
- **NOT_IMPLEMENTED:** GitHub/Forgejo logical-release promotion and equivalence;
- **NOT_IMPLEMENTED:** browser contract v2 and cloud signed-in browser broker;
- **NOT_IMPLEMENTED:** requirements-filtered external module bundles;
- **NOT_EXERCISED:** current-HEAD live Claude/Codex and browser provider canaries.

## Verification commands

```bash
python3 scripts/gates/check_agent_docs.py --selftest
python3 scripts/gates/check_agent_docs.py
python3 scripts/gates/check_module_catalog.py --selftest
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_modules.py catalog
```

A green Phase 0 gate proves catalog and lock integrity only. It must not be
reported as completion of the later phases.
