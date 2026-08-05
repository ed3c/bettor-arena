# Module: unknown-discovery-composer domain lexicon and preservation ledger

This module preserves domain terms and high-value route idioms that are too detailed for the main state graph but too important to lose. Read it when a route packet uses a local term, when a previous version had a sharper phrase than the current compact catalog, or when a fresh LLM would otherwise guess what a domain word means.

## Information Disposition Rule

When refactoring this skill, classify every detail that leaves the active `SKILL.md` or gets compressed before relocating it.

| Class | What belongs here | Destination | Rule |
|---|---|---|---|
| Load-bearing procedure | State nodes, gates, actor choice, grounding, validator, human admit, failure edge | `SKILL.md` | Keep in main file. A fresh LLM must see it without loading modules. |
| Domain term | Local phrase that carries workflow behavior, such as `Blindspot Pass` or `顯式棄跑` | This module | Preserve definition, trigger, route effect, and failure edge. |
| Route example | A concrete prompt or routing idiom that helps an agent choose correctly | This module | Keep as an example, not as the only legal wording. |
| Retarget fact | Platform difference, missing antigravity mechanism, historical mapping | `modules/retarget-map.md` | Keep history out of the main workflow. |
| Stale or unavailable active route | Old wording that must not be executed as a current route, but may contain domain knowledge | `legacy-skill-2026-07-22.md` plus `retarget-map.md` or this module | Preserve the wording for audit, then mark current route status explicitly. Do not silently execute stale routes. |

Loss rule: if a detail changes which skill is selected, which actor is allowed, which validator is trusted, or where the workflow stops, it is not optional prose. Put it in `SKILL.md` or this module with an explicit route effect.

## Domain Term Ledger

| Term | Meaning | Route effect | Failure edge |
|---|---|---|---|
| `地圖 ≠ 真實疆域` | The user or model has a map of the task, but the real codebase, domain, or market may violate it. | Start at `G0 disclose_startpoint` and `G1 quadrant_inventory`; do not jump to planning. | If evidence contradicts the map, return to `G1` or route to repo/source investigation. |
| `recipe-not-engine` | The composer only inventories, routes, and surfaces. It does not execute downstream workflows or accept outcomes. | Every route packet must stop at `human_admit`. | If the response starts executing the route, stop and rewrite as SURFACE. |
| `SURFACE` | Make uncertainty, route choice, grounding, and admit visible to the human. | Route packet must expose the decision instead of hiding it in prose. | If the human cannot tell what they are admitting, return to `G2 route_packet`. |
| `LAND-DECISION` | The non-delegable human decision: which unknown matters, whether residue is acceptable, whether to merge or proceed. | Actor is `human`; model output is evidence only. | If a model verdict is treated as admit, route to `V2 route_gate`. |
| `起跑點披露` | Before classifying unknowns, state the human current understanding, familiarity, assumptions, and collaboration expectation. | Required output of `G0 disclose_startpoint`. | If omitted, the model will likely invent generic defaults; return to `G0`. |
| `盲點通行證 / Blindspot Pass` | A prompt pattern for unfamiliar code or domain areas where the user does not know what to ask. | Route UU to `zoom-out`, `repo-agent-native`, or source inspection with a blindspot-focused packet. | If blind spots are abstract and not tied to consequences, return to `G1`. |
| `主動審查訪談 / Interview Exploit` | One-question-at-a-time interview focused on answers that would change architecture. | Route KU to `grilling`, `grill-me`, `grill-with-docs`, or `loop-me`. | If the question would not change route or architecture, do not ask; keep it as residue. |
| `設計對比器 / Design Reactor` | Generate several meaningfully different design/interface directions so the human can react to tacit taste. | Route UK to `prototype` or `design-an-interface`; validator is human taste reaction. | If variants differ only cosmetically, return to route generation and demand distinct alternatives. |
| `指認參考源碼` | When the human lacks vocabulary but can point at examples, use referenced code, vendor modules, or websites as taste/contract evidence. | Route KU/UK to source inspection or prototype with `target evidence` set to the reference. | If the reference is not inspected, grounding remains `[推論]`. |
| `保真語料 intake` | Faithful transcript and extracted knowledge are different layers: transcript preserves intent; extraction contains factual claims. | Route research-to-asset cold starts to `dr-to-mvp` Phase R; route named entities and numbers to `external-verify`. | If extracted claims are used as facts without verification, mark route invalid. |
| `雙向警戒` | Training memory failing to recognize a post-cutoff entity does not prove it is false; both false-positive and false-negative confabulation are risks. | External named entities, dates, and numeric claims need primary-source verification. | If the model declares false from memory, route to `external-verify`. |
| `repo-wiki-converge gap` | Opus-grade prose repo wiki convergence from antigravity has no local equivalent unless built later. | Surface as missing capability; do not silently replace with `repo-agent-native`. | If route needs prose convergence, mark `human_required`. |
| `gemini-conversation-research gap` | Antigravity AI Studio / Gemini conversation research pipeline is not a local route. | Use `research`, `dr-research-loop`, `dr-to-mvp`, or `agy-findings` only when their contracts match. | If a Gemini conversation pipeline is required, surface missing local machinery. |
| `truth-verify-loop local status` | The skill exists, but its own contract says the local engine is not yet instantiated. | Route only as `candidate` until the setup contract has been run and selftested. | If treated as ready engine without instantiation evidence, downgrade grounding. |
| `顯式棄跑` | A planned step may be skipped only when information value is zero and the human accepts the skip. | Record `PARTIAL` or `SKIPPED`, reason, and unchanged judgment rule. | If the judgment rule is rewritten to fit partial evidence, reject. |
| `implementation-notes Deviations` | Minor non-assertion drift during implementation should be recorded with conservative choice and reason. | Route to inline discipline; it is not a new plan unless an assertion is refuted. | If drift disproves a plan assertion, route to execution-feedback instead. |
| `斷言級證偽` | Execution shows a plan assertion was false, not merely incomplete. | Route to `loop-harness-standard/modules/execution-feedback.md`. | If framed as minor drift, return to `M2 phase_transition`. |
| `HELD / REFUTED / UNOBSERVED` | Judge-verdict vocabulary for comparing plan assertions against execution evidence. | Use for post-implementation assertion review and quiz material. | If unresolved assertions are silently omitted, surface as human review residue. |
| `人理解閘 / quiz` | Merge readiness includes whether the human understands the change, not only whether tests pass. | Generate explanation plus quiz or route to `teach`; validator is human. | If quiz is generic or answerable without understanding this change, rewrite it. |
| `產物判別半 vs 人理解半` | Product quality and human understanding are separate gates. | Artifact verdicts route to `judge-loop-chooser`; code diffs route to `code-review`; understanding routes to quiz or `teach`. | If one gate is used to skip the other, surface missing gate. |

## Route Idioms To Preserve

### Blindspot Pass
Use when the user is entering an unfamiliar code area or domain.

```text
I am working on adding or changing [target], but I do not know the relevant [modules/domain] well. Do a blindspot pass: list the unknown unknowns that could change the plan, cite the repo or source evidence you inspected, and help me produce a better next prompt.
```

Packet requirements:
- quadrant: usually UU;
- actor: `main-session`, `codex`, `zoom-out`, or `repo-agent-native` depending on code depth;
- validator: source references or human admit for scope;
- failure edge: return to `G1` if the pass only lists generic risks.

### Interview Exploit
Use when ambiguity is known, but only some answers would matter.

```text
Interview me one question at a time about anything ambiguous. Prioritize questions where my answer would change architecture, route choice, actor, validator, or human admit.
```

Packet requirements:
- quadrant: KU;
- actor: `leaf-skill:grilling`, `leaf-skill:grill-me`, `leaf-skill:grill-with-docs`, or `leaf-skill:loop-me`;
- validator: the answer changes or confirms a route packet field;
- failure edge: stop asking if the question would not affect a route.

### Design Reactor
Use when the human cannot state taste but can react to alternatives.

```text
Create several materially different design directions for [target] so I can react. Each direction must reveal a different product assumption, not just a different visual skin.
```

Packet requirements:
- quadrant: UK;
- actor: `leaf-skill:prototype` or `leaf-skill:design-an-interface`;
- validator: human selects or rejects assumptions exposed by the variants;
- failure edge: regenerate variants if differences are superficial.

## Lost-Term Recovery Procedure

When a fresh LLM encounters a term in old notes, plans, or changelogs that is not defined in `SKILL.md`:
1. Search this module first.
2. If missing, search `legacy-skill-2026-07-22.md`, sibling modules, and `retarget-map.md` before inventing a meaning.
3. If the term changes a route, actor, validator, or admit point, add it to this module before relying on it.
4. If the term is only historical and has no current route effect, preserve it in `legacy-skill-2026-07-22.md` or `retarget-map.md` and keep it out of the active packet.
5. If the term points to unavailable machinery, mark the route `human_required` or `[推論]`; do not silently substitute a nearby local skill.
