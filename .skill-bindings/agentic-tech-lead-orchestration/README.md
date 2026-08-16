# Agentic Tech Lead orchestration — Bettor binding

This directory binds the portable `agentic-tech-lead-orchestration` candidate
from `ed3c/skills-shared` to Bettor's existing modules. It does not copy the
shared `SKILL.md`, activate a provider, install Git Town, or create a second
code graph.

## Authority and source identity

```text
shared procedure candidate
  repository: ed3c/skills-shared
  branch: agent/agentic-tech-lead-controls-v1
  commit: ee7aaa55ab5b779a813f78a266569d6b53ddc7b8
  tree: 674de1eafe1def98849b316c3df7664955d38caf
  registry classification: ABSENT
  projection: ABSENT

consumer binding
  repository: ed3c/bettor-arena
  parent commit: bfabd45d4732e66961d4ba5f958d240feb15b32d
  parent tree: ae5ee587b46a98bffc8571156dbedc55fbaa44f1
  active acceptance issue: #92
```

The PDF is a `SOURCE_PROPOSAL`. Repository contracts, current source, tests,
exact runtime receipts, the active terminal queue, and Human Admit remain
above it.

## State machine

```text
ROUTE
→ LOCK_CONTRACT
→ RESOLVE_INTENT
→ EXPAND_EXACT_SUBJECT_WHEN_AVAILABLE
→ SLICE_CONTEXT
→ DECOMPOSE_DAG
→ LEASE_WORKTREES
→ EXECUTE_BOUNDED_WORKERS
→ VERIFY_AND_REPAIR
→ SELECT_OR_STACK
→ HUMAN_HANDOFF
```

Stop on an absent immutable subject, overlapping path lease, mutable
acceptance oracle, unsupported code-intelligence coverage, repeated failure,
semantic conflict, unadmitted Git Town, remote publication, merge, promotion,
or rollback request.

## Data flow

```text
Issue / PRD / source proposal
→ locked Bettor task packet
→ GrepAI candidate intent anchors
→ current-source readback
→ SCIP + SQLite exact-subject projection (NOT_IMPLEMENTED)
→ Tree-sitter structural slicing (NOT_IMPLEMENTED)
→ LoopX context assembly
→ LoopX Worker Fleet leases
→ Serena bounded execution candidate
→ proof/gate receipts
→ coherent tournament winner or dependency Stack
→ Git Town adapter only after admission
→ Human Admit
```

The current `code-truth-graph-v2` Python AST adapter is a reference evidence
adapter. It is not SCIP. The current optional vector projection is not a
LanceDB runtime. Those differences remain explicit rather than being hidden
behind a generic “integrated” claim.

## Domain module map

| Portable role | Bettor owner | Current runtime state |
|---|---|---|
| Intent anchor (`grepai`) | `.arena/modules/knowledge-providers` | `NOT_EXERCISED` |
| Deterministic graph (`SCIP + SQLite`) | `.arena/modules/code-truth-graph-v2` | `NOT_IMPLEMENTED` |
| Structural slicer (`Tree-sitter`) | `.arena/modules/code-truth-graph-v2` | `NOT_IMPLEMENTED` |
| Prompt/context assembly | `.arena/modules/loopx-context-assembly` | `NOT_EXERCISED` |
| Agent executor (`Serena`) | `.arena/modules/knowledge-providers` | `NOT_EXERCISED` |
| Vector candidate store (`LanceDB`) | `.arena/modules/loopx-notes-retrieval` | `NOT_IMPLEMENTED` |
| Parallel Worktree fleet | `.arena/modules/loopx-worker-fleet` | `NOT_EXERCISED` |
| Stacked delivery (`Git Town`) | `.arena/modules/git-town-runtime` | `ABSENT` |

`code-graph-rag` is `RETIRED_FROM_CANONICAL_ROUTE`. Its provider manifest,
provider-registry entry, evaluator participant, and evaluator provider class
must remain absent. Historical rationale lives only in explicit decision
records such as `docs/knowledge-providers/alternatives.md`; the name may also
appear in negative controls that prevent route resurrection. It cannot
participate in context assembly or impact decisions.

## Evidence boundary

The binding checker can prove exact binding bytes, module identities,
retired-provider artifact absence, path routes, automation refusals, and
planted negative controls for the branch under test.

It cannot prove:

```text
shared Skill registry admission
live GrepAI / Serena
SCIP index construction or coverage
Tree-sitter grammar/runtime
LanceDB table or embedding policy
Orca/ADE UI or model fan-out
Git Town executable/configuration
Worktree execution
Forgejo/GitHub publication
semantic conflict correctness
merge, promotion, rollback, or release
```

Those states remain `ABSENT`, `NOT_IMPLEMENTED`, or `NOT_EXERCISED` as
recorded in `binding.json`.

## Verification

```bash
python3 scripts/gates/check_agentic_tech_lead_binding.py --selftest
python3 scripts/gates/check_agentic_tech_lead_binding.py
sh tests/agentic-tech-lead-binding/run-all.sh
```

The dedicated workflow executes the same closed, offline checks at the exact
PR head. No network, provider, model, forge mutation, credential, or Git Town
operation is part of this binding gate.
