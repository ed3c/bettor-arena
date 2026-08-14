# Molecular Stack PR index

## Authority and freshness

This index records the molecular delivery topology observed while auditing
`ed3c/bettor-arena` against the attached Harness architecture PDF.

GitHub issue/PR metadata remains the current authority for open/closed/head/check
state. This Markdown records the relationship and the last observed immutable
subjects; it must be updated when a branch head, base or terminal decision
changes.

Audit baseline:

```text
bettor-arena main: d291523856988cfa54316dba967fea8470194b72
tree:              71d7b874dfd181e15d6b614cd6d3bf7fb47d8c43
convergence issue: bettor-arena#38
convergence branch: integration/pdf-harness-convergence-v1
```

## Git Town status

```text
.git-town.toml                         ABSENT
.git-town                              ABSENT
selected git-town-stacked-pr-worker    ABSENT
repository molecular-delivery policy   IMPLEMENTED
```

No repository-level Git Town configuration is currently tracked, and
`.agents/shared-skills.requirements.json` does not select a
`git-town-stacked-pr-worker` Skill. Therefore this index does **not** claim that
Git Town CLI is configured or that any branch relation was created by Git Town.

The repository still uses the molecular terms defined in
[`../agents/issue-tracker.md`](../agents/issue-tracker.md):

```text
sibling      independent path-disjoint slice
true child   consumes unmerged parent bytes
terminal     one reviewable behavior plus eval/evidence
convergence  shared indexes, generated locks and final acceptance
```

## Four-repository documentation convergence

Parent: [`bettor-arena#35`](https://github.com/ed3c/bettor-arena/issues/35)

| Role | Repository leaf | Relation | State | Exact merged identity |
|---|---|---|---|---|
| Integration / Acceptance | [`bettor-arena#37`](https://github.com/ed3c/bettor-arena/pull/37) | independent sibling | `MERGED` | `1f94d3d77992a1396959a15b2ada7836c07bf300` |
| Instruction / Method | [`skills-shared#85`](https://github.com/ed3c/skills-shared/pull/85) | independent sibling | `MERGED` | `e3b327ad49c088f1962c33167ecd5ac9d28125fb` |
| Runtime Contract | [`runtime-env#30`](https://github.com/ed3c/runtime-env/pull/30) | independent sibling | `MERGED` | `4a333ccf106ef60bc6942b922b7f5efffb3876f5` |
| Domain Product / Reference Consumer | [`agent-shield-monorepo#78`](https://github.com/ed3c/agent-shield-monorepo/pull/78) | independent sibling | `MERGED` | `1af04c1ef5cb68eab198987feba008c93d3ec22f` |
| Exact route/PDF audit | [`bettor-arena#38`](https://github.com/ed3c/bettor-arena/issues/38) | convergence owner | `ACTIVE` | branch `integration/pdf-harness-convergence-v1`; PR pending in the first documentation commit |

All four blockers named by #38 are merged. The convergence leaf may now pin
their exact merge commits, compare route/state-machine vocabulary, and record
remaining cold-start/live gaps. It must not infer a live Claude/Codex read from
the documentation changes themselves.

## Modular platform implementation spine

These are historical vertical slices landed on `main`. They are shown as a
causal implementation spine, not as proof of active Git Town configuration.

```text
#4  module catalog + composition contract
 ↓
#8  complete tracked-path ownership
 ↓
#10 module-closure proof subjects
 ↓
#12 Context Capsules and fixed Claude/Codex preparation
 ↓
#15 default-deny stateless MCP contract
 ↓
#21 Bun/TypeScript stateless MCP implementation
 ↓
#22 transactional external-project bootstrap
 ↓
#23 GitHub/Forgejo logical origin + Browser Contract v2
 ↓
#29 README and current-status convergence
```

| PR | Terminal behavior | Main state |
|---|---|---|
| [`bettor-arena#4`](https://github.com/ed3c/bettor-arena/pull/4) | module manifest, composition requirement and deterministic lock | `MERGED` |
| [`bettor-arena#8`](https://github.com/ed3c/bettor-arena/pull/8) | exactly one owner or reviewed class per tracked path | `MERGED` |
| [`bettor-arena#10`](https://github.com/ed3c/bettor-arena/pull/10) | module-local/transitive proof identity | `MERGED` |
| [`bettor-arena#12`](https://github.com/ed3c/bettor-arena/pull/12) | immutable Context Capsules and offline driver parity | `MERGED` |
| [`bettor-arena#15`](https://github.com/ed3c/bettor-arena/pull/15) | default-deny MCP policy and disposable closure | `MERGED` |
| [`bettor-arena#21`](https://github.com/ed3c/bettor-arena/pull/21) | typed Bun stateless MCP runtime | `MERGED` |
| [`bettor-arena#22`](https://github.com/ed3c/bettor-arena/pull/22) | project plan/apply/verify/rollback | `MERGED` |
| [`bettor-arena#23`](https://github.com/ed3c/bettor-arena/pull/23) | logical origins and browser contract | `MERGED` |
| [`bettor-arena#29`](https://github.com/ed3c/bettor-arena/pull/29) | nearest README coverage and mutable status correction | `MERGED` |

## Skill, host execution and provider spine

```text
#40 / #43  shared repo-agent procedure → Bettor consumer binding
      ↓
#47 / #48  portable SKILL.md and six-host compatibility contract
      ↓
#49 / #50  host-owned typed-argv execution and assertion receipts
      ↓
#51        provider-neutral query/memory proposal contracts
      ↓
#46 / #56  paired fixture-only provider admission evaluator
```

| Issue / PR | Relation | State | Current authority |
|---|---|---|---|
| [`bettor-arena#40`](https://github.com/ed3c/bettor-arena/issues/40) / [`#43`](https://github.com/ed3c/bettor-arena/pull/43) | terminal consumer-binding leaf | `MERGED` | `.skill-bindings/repo-agent-native/` |
| [`bettor-arena#47`](https://github.com/ed3c/bettor-arena/issues/47) / [`#48`](https://github.com/ed3c/bettor-arena/pull/48) | terminal portable-Skill leaf | `MERGED` | `.agents/skills/harness-wiki/` |
| [`bettor-arena#49`](https://github.com/ed3c/bettor-arena/issues/49) / [`#50`](https://github.com/ed3c/bettor-arena/pull/50) | true child of the portable contract | `MERGED` | typed runner + `loopctl` port |
| [`bettor-arena#51`](https://github.com/ed3c/bettor-arena/pull/51) | provider-contract terminal leaf on `main` | `MERGED` | `docs/knowledge-providers/` and module manifest |
| [`bettor-arena#46`](https://github.com/ed3c/bettor-arena/issues/46) / [`#56`](https://github.com/ed3c/bettor-arena/pull/56) | active provider-eval terminal leaf | `OPEN` | observed head `770b0c8990843e958f7c1a345c3359a2d71eeb82` |

### Active PR #56 exact observed state

```text
base: main @ d291523856988cfa54316dba967fea8470194b72
head: integration/provider-admission-packets-v1
head SHA: 770b0c8990843e958f7c1a345c3359a2d71eeb82
GitHub mergeable metadata: true

Knowledge provider admission evals: PASS
harness-wiki portable execution:   PASS
Knowledge provider contracts:      FAIL
Modular contracts:                 FAIL
```

The failing modular path is load-bearing. The observed sync run could generate a
new composition lock, then stopped because a Context Capsule listed
`docs/knowledge-providers/evals/cases` as a directory rather than tracked file
bytes. The PR must replace directory entries with exact files or a supported
manifest expansion, regenerate all projections, and pass exact-head checks.
Fixture evaluator PASS cannot proxy the modular failure.

## Non-authoritative or stale branch subjects

| PR / branch | State | Why it must not be merged as-is |
|---|---|---|
| [`bettor-arena#52`](https://github.com/ed3c/bettor-arena/pull/52) | merged to a non-`main` feature base | alternate provider slice; not current `main` release identity |
| [`bettor-arena#53`](https://github.com/ed3c/bettor-arena/pull/53) | `OPEN`, diverged, non-mergeable | historical aggregate branch; extract any unique delta into new terminal leaves instead of merging the aggregate |
| [`bettor-arena#55`](https://github.com/ed3c/bettor-arena/pull/55) | closed without merge | publication subject and generated-head identity were invalid |
| `feat/agent-shield-reference` | behind `main`, zero unique commits | not an implementation of issue #24 |

Do not delete historical branches merely because this index marks them
non-authoritative. Close, supersede or delete remains a Human decision.

## Open terminal leaves required by the PDF target

| Owner issue | Terminal leaf | Current state |
|---|---|---|
| [`bettor-arena#24`](https://github.com/ed3c/bettor-arena/issues/24) | immutable Agent Shield reference-consumer acceptance | `OPEN`; implementation branch has no unique delta |
| LoopX contracts | Objective/Todo/Gate/Evidence/Quota + command/event/snapshot schemas | `ABSENT` issue/PR |
| LoopX ledger | single writer, hash chain, replay and split-brain controls | `ABSENT` issue/PR |
| Worker gateway | Grok/OpenCode/Pi/Codex/Claude/Ante adapter contract and canaries | `ABSENT` issue/PR |
| Strategy/HITL | graph command port, interrupt/resume/exception receipts | `ABSENT` issue/PR |
| Decision memory | evidence-bound capsule, expiry, conflict, deletion and admit | `ABSENT` issue/PR |
| Runtime fabric | worktree/container/provider isolation and local/cloud canary | `ABSENT` issue/PR |
| Observability/UI | redacted event projection and signed HITL console | `ABSENT` issue/PR |

Each row should become a separate terminal issue/PR unless a current issue
already owns the exact behavior. Shared lock/index regeneration and final
acceptance belong only to one convergence leaf.

## Required receipt chain

```text
source proposal or incident
→ architecture decision
→ parent issue
→ molecular terminal issue
→ branch / PR / exact head
→ positive + hollow/mutation controls
→ immutable implementation subject
→ runtime/provider/host receipt where applicable
→ convergence index
→ Human Admit
```

Missing links remain `ABSENT`. Similar names, mutable branch heads, old green
runs, package installation, generated prose or another environment's receipt do
not fill the chain.
