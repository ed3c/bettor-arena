# Module: unknown-discovery-composer semantic loss ledger

This ledger verifies the stricter preservation requirement for the 2026-07-22 rewrite: no domain knowledge from the previous `SKILL.md` may disappear. If content leaves the active state graph, it must remain discoverable in a module and the active `SKILL.md` must link to that module.

Authoritative preservation modules:
- `legacy-skill-2026-07-22.md`: verbatim copy of the previous `SKILL.md`; this is the complete no-delete archive.
- `domain-lexicon.md`: normalized domain terms, route idioms, and failure edges extracted from the legacy text.
- `retarget-map.md`: lineage, platform retargeting, unavailable machinery, and historical status changes.

## Status Labels

| Label | Meaning |
|---|---|
| `ACTIVE_IN_SKILL` | The meaning is still part of the live execution workflow in `../SKILL.md`. |
| `PRESERVED_IN_MODULE` | The meaning is not inline in the active workflow, but is normalized in `domain-lexicon.md`, this ledger, or `retarget-map.md`. |
| `LEGACY_ARCHIVED` | The exact old wording is preserved verbatim in `legacy-skill-2026-07-22.md`. |
| `CANONICAL_OWNER_WITH_LEGACY_COPY` | The active owner is another skill, but the old composer wording is still preserved in the legacy archive and this ledger records the owner. |
| `STALE_ACTIVE_ROUTE_PRESERVED` | The old wording named a route/status that is no longer true as an active route; it is preserved as history, and the current status is stated. |

There is intentionally no `deleted` or `retired` success label. Moving information out of the active path is allowed only when the information is still preserved in one of the modules above.

## Coverage Verdict

The old `SKILL.md` has full preservation coverage:
- active procedure and gates are in `../SKILL.md`;
- specialized route idioms and domain vocabulary are in `domain-lexicon.md`;
- exact original wording is in `legacy-skill-2026-07-22.md`;
- platform and lineage facts are in `retarget-map.md`;
- downstream internals point to owner skills while the legacy wording remains archived.

## Semantic Unit Coverage

| Legacy semantic unit | Status | Preservation location | Active-route treatment |
|---|---|---|---|
| Trigger: task starts in fog, user does not know what to ask, taste unstated, too vague to plan, post-implementation understanding gate | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md`; `legacy-skill-2026-07-22.md` | Active invocation preserved. |
| `地圖 ≠ 真實疆域` framing | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; `legacy-skill-2026-07-22.md` | Used as term meaning, not repeated in main title. |
| KK/KU/UK/UU quadrant model | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` G1 and packet; legacy archive | Active gate preserved. |
| Three phases: pre/during/post implementation | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` graph and route packet `phase`; legacy archive | Recast as conditional state edges. |
| `recipe-not-engine`, SURFACE, no auto-chain | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md`; `domain-lexicon.md`; legacy archive | Strengthened as invariant and packet rule. |
| Human admit after every route segment | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` H1 and packet field; legacy archive | Active human gate preserved. |
| Disk existence check for target skills | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/M1B; legacy archive | Active validation preserved. |
| STOP table: no full auto-chain, no fake quadrant filling, no SDLC tax for simple work, code goes to code-review, quiz must be meaningful | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md` invariants/gates/Gotchas; `domain-lexicon.md`; legacy archive | Converted from warning table to validation gates. |
| Starting point disclosure and specificity balance | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md` G0; `domain-lexicon.md`; legacy archive | Active node preserved. |
| Blindspot Pass prompt | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Available when a UU route needs the idiom. |
| `teach` for new domain learning | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/catalog; legacy archive | Active route preserved. |
| `research` vs `external-verify` split | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/catalog; legacy archive | Active route preserved. |
| `gemini-conversation-research` unavailable local machinery | `STALE_ACTIVE_ROUTE_PRESERVED` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; `retarget-map.md`; legacy archive | Not executable as local route; surfaced as gap. |
| Faithful transcript plus extraction intake | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/catalog; `domain-lexicon.md`; legacy archive | Active route through `dr-to-mvp` Phase R plus `external-verify`. |
| Double warning: training memory not recognizing post-cutoff entity does not prove false | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Used to force primary-source verification. |
| `wayfinder` for session-scale fog | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/catalog; legacy archive | Active route preserved. |
| `grilling` replacement for unavailable `superpowers:brainstorming` | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md`; `retarget-map.md`; legacy archive | Active route is `grilling`; superpowers history preserved. |
| `grill-with-docs` local output convention: no numbered ADR/DDR system, use prose/changelog | `CANONICAL_OWNER_WITH_LEGACY_COPY` | legacy archive; downstream owner/context | Active composer may cite when the route packet needs this output shape. |
| Interview Exploit prompt | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Available when KU interview routing needs the idiom. |
| Reference-source pointing when vocabulary is missing | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Preserved as `指認參考源碼`. |
| Design Reactor prompt | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Available when UK taste routing needs alternatives. |
| `prototype` / `design-an-interface` for taste uncertainty | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/catalog; legacy archive | Active route preserved. |
| `improve-codebase-architecture` route | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M1/catalog; legacy archive | Active route preserved. |
| `repo-agent-native` for repo truth and no-KG detail | `ACTIVE_IN_SKILL` + `CANONICAL_OWNER_WITH_LEGACY_COPY` | `../SKILL.md`; legacy archive; `repo-agent-native` owner | Active route preserved; owner owns internals. |
| `repo-wiki-converge` unavailable local machinery | `STALE_ACTIVE_ROUTE_PRESERVED` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; `retarget-map.md`; legacy archive | Not executable as local route; surfaced as gap. |
| Claim truth verification vs token-efficiency measurement split | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md`; `domain-lexicon.md`; legacy archive | Current status refined: `truth-verify-loop` skill exists but local engine is not instantiated. |
| U1 exit gate to `sdlc-plan-composer` or `to-prd + implement` | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M0/H1/catalog; legacy archive | Active exit preserved. |
| Plan shape requirements: mutable decisions first, unknown-response clause | `CANONICAL_OWNER_WITH_LEGACY_COPY` | legacy archive; `sdlc-plan-composer` owner | Composer may surface as context; owner owns plan-shape contract. |
| `implementation-notes.md` Deviations for minor drift | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md` M2; `domain-lexicon.md`; legacy archive | Active drift distinction preserved. |
| Assertion-level refutation to execution-feedback | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md` M2; `domain-lexicon.md`; legacy archive | Active route preserved. |
| Pivot when UK was really UU | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` invariant/graph/M2; legacy archive | Active pivot preserved. |
| Explicit skip when information value is zero | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Preserved as `顯式棄跑`; active route can invoke it by term. |
| `diagnose` / `diagnosing-bugs` for hard bugs | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md` M2/catalog; legacy archive | Active route preserved. |
| `handoff` / `claude-handoff` plus missing fidelity-handoff caveat | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md`; `retarget-map.md`; legacy archive | Active route preserved; historical caveat preserved. |
| U3 proposal/explanation to `to-prd`, prose to `writing-shape` / `edit-article` | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | this ledger; legacy archive | Not in compact catalog; still preserved and recoverable when route packet identifies prose shaping. |
| U3 quiz and `teach` learning-record shape | `ACTIVE_IN_SKILL` + `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `../SKILL.md`; `domain-lexicon.md`; legacy archive | Active understanding route preserved. |
| `HELD / REFUTED / UNOBSERVED` assertion review | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Preserved for post-implementation assertion review. |
| `qa` for conversational leftover issue reporting | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | this ledger; legacy archive | Preserved and recoverable; active packet can route to `qa` when issue filing is the unknown. |
| Artifact verdict to `judge-loop-chooser`; code to `code-review` | `ACTIVE_IN_SKILL` + `LEGACY_ARCHIVED` | `../SKILL.md`; legacy archive | Active split preserved. |
| Human understanding half vs artifact judgment half | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `domain-lexicon.md`; legacy archive | Preserved as domain term. |
| Downstream boundaries for `sdlc-plan-composer`, `to-prd+implement`, `judge-loop-chooser`, `code-review` | `ACTIVE_IN_SKILL` + `CANONICAL_OWNER_WITH_LEGACY_COPY` | `../SKILL.md`; legacy archive; owner skills | Active boundary preserved without duplicating owner internals. |
| Lineage from antigravity and no skill-conformance-hub governance | `PRESERVED_IN_MODULE` + `LEGACY_ARCHIVED` | `retarget-map.md`; legacy archive | Preserved as lineage, not active route logic. |

## Out Of Active Catalog But Preserved

These items are intentionally not in the compact active route catalog, but they are not deleted. They remain preserved in the legacy archive and are listed here for recovery.

| Preserved item | How to recover into active route packet |
|---|---|
| Prose shaping after proposal or explanation | Use `to-prd`, `writing-shape`, or `edit-article` when the route packet identifies prose shaping as the next unknown. |
| Conversational leftover issue filing | Use `qa` when post-implementation residue is issue reporting rather than understanding, code review, or artifact verdict. |
| Antigravity-specific deliverable examples such as DR report / Path-B / COMPLETENESS matrix | Keep as lineage examples unless the local `judge-loop-chooser` owner establishes a corresponding skill-bettor deliverable. |
| Exact old U0-U3 linear graph | Use only as historical shape; current execution uses the state graph in `../SKILL.md`. |
| Long frontmatter retarget story | Use `retarget-map.md` and the legacy archive for history; frontmatter stays invocation-focused. |
