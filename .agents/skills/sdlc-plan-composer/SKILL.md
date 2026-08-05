---
name: sdlc-plan-composer
description: |
  Stateful SDLC plan composer for multi-stage planning work in skill-bettor. Use when a task must be planned before execution and the plan needs explicit routing through intent alignment, brownfield invariant extraction, vertical slicing, interface design, execution actor selection, and validation contracts. This skill is a recipe-not-engine workflow，it writes decision-complete plan artifacts, route ledgers, and handoff contracts; it does not implement code, auto-run delegated skills, or invent replacement logic for existing atomic skills. It routes to repo-agent-native, unknown-discovery-composer, to-prd, to-issues, design-an-interface, code-review, judge-loop-chooser, autoresearch-composer, tdd, diagnose, handoff, Codex, agy, Opus fresh judges, and mechanical scripts according to explicit semantic gates.
---
# sdlc-plan-composer
## Role
Plan a multi-stage task as a **stateful workflow**, not as a single large prompt.
The output is a plan package under `docs/plans/<date>-<topic>/` that another agent can execute without guessing:
- route decisions are recorded in `route-ledger.md`;
- user intent and why are recorded in `00-intent-and-knowhow.md`;
- domain terms are recorded in `CONTEXT.md`;
- each vertical slice is recorded as `NN-<slice>.md`;
- validation and actor choices are explicit, grounded, and not left as `Opus or Codex or agy`;
- plan prose carries enough context for a fresh LLM to execute without guessing.
This skill follows the truth discipline of `judge-loop-chooser`: every load-bearing decision must say what is being judged, which evidence grounds it, who is allowed to judge it, and whether the result is `technical_equivalent`, `candidate`, `[推論]`, or `human_required`.
## Not For
- Do not use this skill to implement code. Execution goes to `implement`, `tdd`, `diagnose`, Codex, or the relevant harness after the plan exists.
- Do not use this skill for a vague starting point. If success criteria, scope, or target are still foggy, route to `unknown-discovery-composer`.
- Do not use this skill for a clear single-stage request. Route to `to-prd + implement`.
- Do not use this skill to judge a deliverable directly. Route validation strategy to `judge-loop-chooser` or code changes to `code-review`.
- Do not rewrite delegated atomic skills inline. This composer routes and records contracts; it does not duplicate the logic of `repo-agent-native`, `design-an-interface`, `autoresearch-composer`, or `judge-loop-chooser`.
## Invariants
1. **Stateful, not one-shot**: Always proceed through Match -> Generate -> Validate nodes. A plan that jumps straight to final prose is incomplete.
2. **Route before write**: Before writing slice content, record why the workflow is using this skill, which capabilities already exist, whether the work is brownfield, and which actor or validator is responsible.
3. **No name-based equivalence**: A skill or family is `technical_equivalent` only after reading its real contract and showing how it satisfies the requested behavior. Names, descriptions, memory, and superficial similarity are at most `candidate` or `[推論]`.
4. **Load-bearing uncertainty requires comparison**: If a reused component is load-bearing and equivalence is uncertain, add a rebuild or compare slice, or stop for human decision. Do not hide the uncertainty inside implementation text.
5. **Brownfield truth first**: Brownfield plans must extract invariants before premise disproof, intent alignment, slicing, or interface decisions rely on existing system facts.
6. **LLM verdict is evidence, not admit**: Opus, Codex, agy, and llm_judge can produce evidence or findings. Final LAND-DECISION stays human.
7. **Actors have semantic roles**: Mechanical scripts judge deterministic facts; Opus fresh judges semantic verdicts; Codex implements and reproduces; agy researches and cross-checks facts. Do not list them as interchangeable alternatives.
8. **Semantic truth survives output**: Skill text and generated plans must be understandable by a fresh LLM without conversation context. Expand compressed labels into goal, evidence, actor reason, validator, admit point, and failure edge.
9. **Three attempts then stop**: If a node fails three times, record what failed, question the abstraction, and switch approach rather than retrying the same shape.
## STOP - You Are Rationalizing
| Thought | Reality |
|---|---|
| The user asked for a plan, so I can just write the plan. | No. First classify the request and record the route. |
| This sounds like an existing skill, so I will reuse it. | Not enough. Read the actual skill or family contract or mark it `candidate` or `[推論]`. |
| Brownfield is obvious from memory. | Not enough. Run `repo-agent-native` or record a source-linked fallback inventory. |
| S1 is conversational, so I can infer intent. | If a missing answer would change architecture, ask the user or record `human_required`. |
| S3 can be one sensible interface. | No. Interface changes require at least two distinct designs via `design-an-interface` or an explicit fallback comparison. |
| Opus, Codex, and agy can all handle it. | Wrong abstraction. Choose by semantic role and record why. |
| The judge passed it, so the plan is done. | A judge result is evidence. The plan must still expose grounding and human admit points. |
## State Graph
```mermaid
flowchart TD
  M0["M0 classify_request"] -->|foggy; cannot plan| X0["handoff: unknown-discovery-composer"]
  M0 -->|single-stage; clear; low-risk| X1["handoff: to-prd + implement"]
  M0 -->|multi-stage or high-risk SDLC planning| M1["M1 capability_match"]
  M1 -->|true equivalent exists| X2["delegate_existing_skill_or_stop"]
  M1 -->|load-bearing equivalence uncertain| M1B["M1B rebuild_compare_plan"]
  M1 -->|composition needed| M2["M2 brownfield_match"]
  M1B --> M2
  M2 -->|brownfield| Gm1["G-1 invariant_extraction"]
  M2 -->|greenfield| G0["G0 premise_disproof"]
  Gm1 --> Vm1["V-1 invariant_gate"]
  Vm1 -->|fail; retry <=3 or fallback| Gm1
  Vm1 -->|pass| G0
  G0 --> V0["V0 premise_gate"]
  V0 -->|falsified| X3["wontfix_or_out_of_scope"]
  V0 -->|pass| G1["G1 intent_alignment"]
  G1 --> V1["V1 intent_gate"]
  V1 -->|human answer changes architecture| H1["ask_user_input"]
  H1 --> G1
  V1 -->|pass| G2["G2 vertical_slice_decomposition"]
  G2 --> V2["V2 slice_gate"]
  V2 -->|horizontal or unverifiable| G2
  V2 -->|pass| M3["M3 interface_decision_match"]
  M3 -->|public boundary changes| G3["G3 design_interface"]
  M3 -->|boundary unchanged| M4["M4 execution_actor_match"]
  G3 --> V3["V3 design_gate"]
  V3 -->|insufficient alternatives| G3
  V3 -->|pass| M4
  M4 --> G4["G4 dispatch_plan"]
  G4 --> V4["V4 dispatch_gate"]
  V4 -->|actor or backend unclear| M4
  V4 -->|pass| M5["M5 validation_strategy_match"]
  M5 -->|code artifact| X4["handoff: code-review"]
  M5 -->|judgeable deliverable| G5A["G5A judge_loop_contract"]
  M5 -->|metric iteration| G5B["G5B autoresearch_contract"]
  M5 -->|ordinary implementation| G5C["G5C tdd_diagnose_handoff_contract"]
  G5A --> V5["V5 final_plan_gate"]
  G5B --> V5
  G5C --> V5
```
## Grounding Labels
Use these labels in `route-ledger.md`, slice validation contracts, and final gates.
| Label | Meaning | Allowed use |
|---|---|---|
| `technical_equivalent` | The existing component was read and, where relevant, run or compared. It actually performs the needed job. | Can be used as a plan premise or delegation target. |
| `candidate` | A real component, fixture, rubric, or source exists, but coverage or equivalence has not been proven. | Can justify an investigation or comparison slice, not a final premise. |
| `[推論]` | No direct source or fixture proves the claim. This is an inference, LLM judgment, or pattern guess. | Must be surfaced as risk, assumption, or human question. |
| `human_required` | The choice changes architecture, scope, admit, or product intent and cannot be decided from repo facts. | Must be asked or listed as unresolved. |
## Route Ledger Contract
Every plan package must include `route-ledger.md`. This ledger is the workflow truth surface: it lets a future LLM understand why the plan took each edge without reading the full conversation.
Use this table shape:
```md
| state | decision | evidence | grounding | chosen edge | unresolved |
|---|---|---|---|---|---|
| M0 classify_request | multi-stage SDLC | touches families/... and requires pre-planning | candidate | M1 | none |
```
Rules:
- Every Match node must write one row.
- Every Generate node that relies on a premise must cite the evidence row or source file.
- Every Validate node must record pass or fail and the reason.
- Do not write `appropriate`, `as needed`, `consider`, or `Opus or Codex or agy` as an unresolved instruction. Either decide, ask, or mark `human_required`.
- Do not compress context into labels like `semantic truth`, `judge it`, or `validate later`; write what is judged, with which evidence, by whom, and what failure means.
## Node Contracts
### M0 classify_request
Purpose: Prevent foggy requests from becoming fake plans, and prevent simple work from being taxed by a six-stage workflow.
Inputs:
- User request.
- Mentioned paths, systems, families, harnesses, or deliverables.
- Whether the user asked to plan before implementation.
Decision Rule:
- If success criteria, scope, target, or constraints are too unclear to make a plan, route to `unknown-discovery-composer`.
- If the task is single-stage, clear, and low risk, route to `to-prd + implement`.
- If the task is multi-stage, high-risk, brownfield, cross-family, harness-level, or explicitly plan-first, continue to M1.
Semantic Grounding:
- `technical_equivalent`: only when a concrete alternative workflow fully covers the request.
- `candidate`: when the request appears likely to fit SDLC planning but still needs capability matching.
- `human_required`: when scope choice itself changes the architecture or work boundary.
Output:
- Add `M0 classify_request` row to `route-ledger.md`.
Validation Gate:
- The row must explain why the other two exits were not chosen.
Failure Edge:
- If classification depends on missing intent, ask the user or route to `unknown-discovery-composer`.
### M1 capability_match
Purpose: Prevent duplicate skills and prevent name-based false equivalence.
Inputs:
- `~/.claude/skills/*/SKILL.md`
- `.claude/skills/*/SKILL.md`
- `families/*/SKILL.md`
- Similar implementations mentioned by the task.
- `modules/mattpocock-skill-inventory.md` only as a candidate index, not as proof.
Decision Rule:
- Mark `technical_equivalent` only after reading the real target contract and explaining how it satisfies the needed behavior.
- Mark `candidate` when a real target exists but equivalence is not proven.
- Mark `[推論]` when the match is from names, summaries, memory, or an LLM guess.
- If a `technical_equivalent` target fully handles the request, delegate or stop rather than composing a new plan.
- If composition is needed, continue to M2.
- If load-bearing equivalence is uncertain, go to M1B.
Semantic Grounding:
- A source path is mandatory for every claimed capability.
- If the target is load-bearing and comparison is cheap enough to plan, prefer a compare slice over confident reuse.
Output:
- Add a capability matrix to `route-ledger.md`:
```md
| candidate | source | needed behavior | grounding | decision |
|---|---|---|---|---|
```
Validation Gate:
- No row may claim equivalence without a source reference and explanation.
Failure Edge:
- If all matches are `[推論]`, write a rebuild or compare slice, or ask for human choice before relying on them.
### M1B rebuild_compare_plan
Purpose: Convert maybe-already-exists into a measurable comparison instead of letting the model reuse by convenience.
Inputs:
- Candidate component from M1.
- Desired behavior.
- Available fixture, eval, smoke test, or manual rubric.
Decision Rule:
- Add a comparison slice when the component is load-bearing, equivalence is uncertain, and a wrong choice would waste or corrupt later work.
- The slice must define same input, same output expectation, same evaluator, and acceptance rule for both existing and rebuilt variants.
- If no meaningful comparison can be constructed, mark `human_required`.
Output:
- A `NN-compare-<capability>.md` vertical slice.
- A `route-ledger.md` row linking the comparison to M1.
Validation Gate:
- The comparison must be capable of proving non-equivalence, not just confirming the preferred option.
Failure Edge:
- If the comparison cannot be made concrete, return to M1 or ask the user whether to accept the risk.
### M2 brownfield_match
Purpose: Decide whether the plan depends on existing system truth.
Decision Rule:
- Brownfield if the plan touches existing `families/<family>/skills`, `families/<family>/shared`, `families/<family>/evals`, `loop_wiki/engine.sh`, `loop_wiki/_template`, harness skills, shared schemas, or multi-family contracts.
- Greenfield if the work is a wholly new family from template, a new independent skill with no existing contract dependency, or pure documentation.
Output:
- Add `brownfield: yes/no + reason` to `00-intent-and-knowhow.md`.
- Add M2 row to `route-ledger.md`.
Validation Gate:
- Brownfield must enter G-1.
- Greenfield must record why S-1 is N/A.
Failure Edge:
- If unsure and the touched path exists, treat as brownfield.
### G-1 invariant_extraction
Purpose: Extract repo truth before using existing contracts as premises.
Inputs:
- Target path.
- Plan directory.
- `.claude/skills/repo-agent-native/SKILL.md`.
Decision Rule:
- Prefer delegating `repo-agent-native`.
- Use fallback only if the skill is unavailable, the target is unsuitable, or the necessary index or path support is unavailable.
- Fallback must read actual source files and record path-backed assumptions. It is weaker than delegated extraction and must say so.
Fallback Inventory:
1. Read target family `SKILL.md`.
2. Read `FAMILY.yaml` for interface and metric contracts.
3. Read `shared/conventions.md` and `shared/glossary.md` if present.
4. Inspect eval fixture names and metadata without reverse-engineering holdout answers.
5. If harness-level, inspect `loop_wiki/engine.sh` or relevant template or harness skill contracts.
Output:
- Delegated path: `invariants/<slug>/<page>.md`.
- Fallback path: `00-intent-and-knowhow.md` section `Assumed Invariants`.
Validation Gate:
- Every load-bearing invariant has a source reference.
- `unverified` facts are not used as reliable premises in G0, G1, G2, or G3.
Failure Edge:
- Retry extraction up to three times. Then stop and record why S-1 cannot be trusted.
### V-1 invariant_gate
Purpose: Check that brownfield truth is usable before the SDLC stages consume it.
Pass Conditions:
- Brownfield reason is recorded.
- Delegated invariant page exists and is non-empty, or fallback assumptions are source-linked.
- SURFACE fields such as `a_ratio`, `unverified_count`, or fallback confidence are visible when available.
Failure Edge:
- Return to G-1 for missing sources.
- Stop if the plan would rely on unverified facts as hard premises.
### G0 premise_disproof
Purpose: Try to prove the request should not exist before planning how to build it.
Inputs:
- User intent.
- Capability matrix from M1.
- Brownfield invariants from G-1 when applicable.
- Existing decisions under `docs/decisions/` or plan-local decision notes.
Decision Rule:
List at least three falsifiable reasons the demand may be false or unnecessary:
- Existing skill or family already solves it.
- Existing decision record rejected the same direction.
- Brownfield invariant shows the change would violate a contract.
- The requested plan is too broad, too speculative, or lacks a real verification surface.
Output:
- `00-intent-and-knowhow.md` section `Premise Disproof`.
Validation Gate:
- If any disproof succeeds, stop and write a `wontfix` or out-of-scope rationale.
- If none succeeds, record why and proceed to G1.
Failure Edge:
- If disproof depends on missing source truth, return to M1 or G-1.
### G1 intent_alignment
Purpose: Fix the human goal, language, and why before slicing work.
Inputs:
- User request and follow-up answers.
- Brownfield invariants.
- Existing glossary or conventions.
- `grill-with-docs`, `grill-me`, or `domain-modeling` when intent is ambiguous.
Decision Rule:
- If a missing answer would change architecture, ask the user.
- If the user is unavailable, write an explicit reconstruction and open questions. Do not pretend the grill is complete.
- Use `CONTEXT.md` for canonical terms and `00-intent-and-knowhow.md` for original intent, know-how, and why.
Output:
- `CONTEXT.md`.
- `00-intent-and-knowhow.md` sections for intent, why, assumptions, and open questions.
Validation Gate:
- Every canonical term is sourced from user language, repo source, or marked assumption.
- Every architecture-changing open question is in `route-ledger.md` as `human_required`.
Failure Edge:
- Ask the user or route back through `unknown-discovery-composer` if the task is not yet plannable.
### G2 vertical_slice_decomposition
Purpose: Produce executable slices that carry value and verification through the stack.
Inputs:
- Intent artifacts.
- Capability matrix.
- Brownfield invariants.
- `to-prd` and `to-issues` as generation aids.
Decision Rule:
- Each slice must include goal, why now, patch boundary, dispatch plan placeholder, validation contract placeholder, known risks, human decisions, and completion evidence.
- A vertical slice must connect the relevant data, logic, interface, and test or eval surface. Equivalent non-code slices must still have an artifact and validation surface.
- Brownfield slices must account for affected fixtures, harness behavior, or shared contracts.
Output:
- `01-<slice>.md ... NN-<slice>.md`.
Validation Gate:
- No horizontal-only slices.
- No slice without a validation surface.
- No hidden dependency on an unresolved human decision.
Failure Edge:
- Return to G2 until slices are vertical and verifiable.
### M3 interface_decision_match
Purpose: Decide whether interface design is load-bearing.
Decision Rule:
- Go to G3 when the plan changes public API, schema, CLI, skill contract, family interface, evaluator contract, or handoff artifact shape.
- Skip G3 only when the plan changes internal implementation without altering a boundary. Record which boundary is unchanged.
Output:
- `route-ledger.md` row `M3 interface_decision_match`.
Validation Gate:
- Skipping G3 requires explicit evidence that the public boundary is unchanged.
Failure Edge:
- If unsure, go to G3.
### G3 design_interface
Purpose: Prevent the model from choosing the first plausible interface without comparison.
Inputs:
- Slices that change boundaries.
- Existing interface contracts.
- `design-an-interface`.
Decision Rule:
- Delegate to `design-an-interface` when available.
- Require at least two meaningfully different abstractions, not two phrasings of the same design.
- Write a decision record only if all sparse-decision conditions are true: hard to reverse, surprising without context, and based on a real tradeoff.
Output:
- `docs/decisions/<slug>.md` when the sparse conditions pass.
- Otherwise a design rationale inside the affected slice.
Validation Gate:
- Single-option design fails.
- Tradeoff-free decision records fail.
- Interface changes that contradict `FAMILY.yaml` or existing contracts fail unless explicitly planned as breaking changes with human admit.
Failure Edge:
- Return to G3 for more alternatives or ask the user if the tradeoff is product or architecture-level.
### M4 execution_actor_match
Purpose: Choose the actor by semantic job, not model brand or convenience.
Inputs:
- Slice list.
- Validation needs.
- `modules/multi-model-dispatch.md` when actor selection is non-trivial.
- `modules/codex-integration.md` only after choosing Codex.
- `ARCHITECTURE.md` tier-dispatch facts when needed.
Decision Rule:
- **Mechanical script**: Use deterministic shell, test, runner, or checker when it can answer the question. This is cheaper and more independent than LLM judgment.
- **Opus fresh zero-context**: Use for verdicts, semantic judging, design challenge, and evidence review. If Opus is unavailable, queue the verdict. Do not silently downgrade to Haiku or agy.
- **Codex**: Use for implementation, repair, reproduction, TDD driving, second implementation, and code-running engineering work. Codex self-report is not completion evidence. Verify file changes and run checks from the main session.
- **agy**: Use for external research, cross-model fact findings, DR proposal generation, and broad truth checks. agy produces findings, not verdicts.
- **Main session**: Owns the state graph, route ledger, user questions, integration of slice plans, and all LAND-DECISION handoffs.
- **Leaf skills**: `design-an-interface`, `code-review`, and `improve-codebase-architecture` already own their internal subagent structure. Do not wrap them in another layer of subagent dispatch.
Output:
- `Dispatch Plan` section in every `NN-<slice>.md`.
- M4 row in `route-ledger.md`.
Validation Gate:
- No unresolved `Opus or Codex or agy` phrasing.
- Every external CLI or tool dependency has a tracer or availability check planned before use.
- Every Codex task has completion evidence based on files, tests, or logs, not status text.
- Every agy finding has a consumer that knows it is not a verdict.
Failure Edge:
- Return to M4 if role, independence, or evidence semantics are unclear.
- Ask the user only when the actor choice changes cost, latency, or human review burden materially.
### G4 dispatch_plan
Purpose: Write a concrete dispatch plan for each slice.
Output Shape:
```md
## Dispatch Plan
- actor: mechanical-script | main-session | opus-fresh-judge | codex | agy | leaf-skill:<name>
- reason: <semantic reason this actor owns the work>
- input packet: <files/artifacts/prompts the actor receives>
- output packet: <artifact expected back>
- completion evidence: <file/test/log/verdict matrix>
- fallback: <what happens if the actor/tool is unavailable>
```
Validation Gate:
- The output packet must be checkable by M5.
- Dispatch prompts written ad hoc during execution must be saved under `dispatches/<role>-<slug>.md` before use.
Failure Edge:
- Return to M4 if actor ownership or completion evidence is not concrete.
### M5 validation_strategy_match
Purpose: Select validation standards instead of inventing judge logic inside the plan.
Inputs:
- Slice deliverables.
- Dispatch plans.
- `judge-loop-chooser` for judgeable non-code deliverables.
- `autoresearch-composer` for metric iteration loops.
- `code-review` for code changes.
Decision Rule:
- Code artifact -> `code-review`.
- Evolution op T0 aggregate, holdout graduation, DR proposal, or spawn new family or skill decision -> `judge-loop-chooser`.
- Bounded metric-driven `modify -> verify -> keep/discard` task -> `autoresearch-composer`.
- Ordinary implementation -> `tdd`, `diagnose`, and `handoff` contracts.
Semantic Grounding:
- A validation method with true fixture plus good or hollow selftest can be `technical_equivalent`.
- A real rubric or fixture without proven coverage is `candidate`.
- LLM-only judgment, bespoke pattern checks, or unanchored claims are `[推論]`.
- `[推論]` may be evidence for a human gate, never an automatic completion criterion.
Output:
- `Validation Contract` section in every `NN-<slice>.md`.
- M5 row in `route-ledger.md`.
Validation Gate:
- Every slice names its validator and grounding state.
- Every human admit point is explicit.
Failure Edge:
- Return to M5 or route to `judge-loop-chooser` if the validation tier itself is unclear.
### G5A judge_loop_contract
Purpose: Route judgeable non-code deliverables to the existing validation router.
Decision Rule:
- Do not inline the D1-D4 decision tree from `judge-loop-chooser`.
- State which deliverable type appears to apply, what evidence packet will be sent, and where the human admit happens.
Output:
```md
## Validation Contract
- validator: judge-loop-chooser
- deliverable kind: <D1/D2/D3/D4 or candidate>
- evidence packet: <files and summaries>
- grounding before judge: technical_equivalent | candidate | [推論]
- human admit: required
```
Validation Gate:
- The contract must not treat judge PASS or FAIL as auto-accept.
### G5B autoresearch_contract
Purpose: Route bounded metric iteration to `autoresearch-composer` without duplicating its full contract.
Decision Rule:
- Use only when the slice has a measurable metric, direction, guard, iteration bound, and keep or discard semantics.
- Otherwise return to ordinary implementation or intent clarification.
Output:
```md
## Validation Contract
- validator: autoresearch-composer
- route reason: metric-driven bounded iteration
- required fields to obtain: Goal, Scope, Metric, Direction, Verify, Guard, Iterations
- human admit: required before accepting iteration result
```
Validation Gate:
- No vague optimize slice may pass without a metric and guard.
### G5C tdd_diagnose_handoff_contract
Purpose: Give ordinary implementation slices executable acceptance criteria.
Decision Rule:
- Use `tdd` for planned feature or fix work where tests can be written first.
- Use `diagnose` for hard, flaky, intermittent, or poorly reproduced bugs.
- Use `handoff` or `claude-handoff` when context transfer is part of execution.
Output:
```md
## Validation Contract
- validator: tdd | diagnose | handoff | combination
- acceptance commands: <tests/checks>
- failure mode: <what failure proves>
- completion evidence: <logs/files/diff/verdict>
```
Validation Gate:
- There must be at least one concrete acceptance command or a stated reason why validation is human-only.
### V5 final_plan_gate
Purpose: Ensure the final plan is executable by a fresh LLM without hidden conversation context.
Pass Conditions:
- `route-ledger.md` has rows for M0, M1, M2, G-1 and V-1 when brownfield, G0 and V0, G1 and V1, G2 and V2, M3, M4 plus G4 plus V4, and M5.
- Every `NN-<slice>.md` has `Goal`, `Why now`, `Patch boundary`, `Dispatch Plan`, `Validation Contract`, `Known risks`, `Human decisions`, and `Completion evidence`.
- Every delegated skill exists or has an explicit fallback.
- Every `candidate`, `[推論]`, and `human_required` item is visible and not silently converted into a premise.
- No execution instruction depends on `as appropriate`, `consider`, `if needed`, or undecided `Opus or Codex or agy` language.
- A fresh LLM can read the plan package without the original conversation and recover the goal, source evidence, actor choice, validator, human admit point, and stop condition.
Failure Edge:
- Return to the failing node. After three failed repair attempts, stop and write a failure ledger with tried steps, errors, and a simpler alternative path.
## Public Artifacts
```text
docs/plans/<date>-<topic>/
├── route-ledger.md              # Required: workflow decisions and grounding
├── 00-intent-and-knowhow.md     # Required: original intent, why, S0, assumptions
├── CONTEXT.md                   # Required when terminology matters
├── invariants/<slug>/<page>.md  # Brownfield delegated extraction, when applicable
├── dispatches/<role>-<slug>.md  # Required for ad-hoc prompts used during execution planning
├── 01-<slice>.md
├── 02-<slice>.md
├── docs/decisions/<slug>.md     # Only when sparse decision conditions pass
├── implementation-notes.md      # Execution phase ledger
├── implement/                   # Execution diff mirror, historical evidence not SSOT
└── fold-in/                     # Fold-in diff mirror, historical evidence not SSOT
```
Slice file shape:
```md
# <slice title>
## Goal
## Why now
## Patch boundary
## Dispatch Plan
## Validation Contract
## Known risks
## Human decisions
## Completion evidence
```
## Module Routing
Read modules only when their edge is active:
- `modules/mattpocock-skill-inventory.md`: read during M1 if matching against global Matt Pocock skills.
- `modules/multi-model-dispatch.md`: read during M4 when actor selection involves Opus, Codex, agy, fallback, or independence tiers.
- `modules/codex-integration.md`: read only after M4 chooses Codex for a slice.
- `modules/retarget-map.md`: read when auditing why a mechanism was ported, removed, or downgraded. Do not use it as the main workflow.
Historical lineage and backend gotchas are important, but they must not interrupt the state graph. The main SKILL.md is the workflow SSOT; modules are edge-local evidence.
## Test Scenarios
Use these as dry-run checks after editing or applying this skill:
1. **Foggy request**: A user says make this better without target or success criteria. Expected route: M0 -> `unknown-discovery-composer`. No SDLC plan should be generated.
2. **Clear single-stage request**: A user asks for one narrow code change with obvious validation. Expected route: M0 -> `to-prd + implement`. No S-1..S5 tax.
3. **Brownfield family change**: A user asks to modify `families/<family>/skills/<sub>`. Expected route: M2 -> G-1 `repo-agent-native`; later stages cite invariants.
4. **Possible existing equivalent**: A user asks for functionality that may already exist. Expected route: M1 marks real evidence; load-bearing uncertainty creates M1B compare slice.
5. **Semantic judge needed**: A slice produces a DR proposal or holdout verdict. Expected route: M5 -> `judge-loop-chooser`; judge output is evidence, not auto-admit.
6. **Implementation actor needed**: A slice requires code writing and tests. Expected route: M4 chooses Codex or TDD by role; completion evidence is files, tests, or logs, not self-report.
7. **External facts needed**: A slice depends on post-cutoff or external truth. Expected route: agy or external verification as findings; final verdict remains human or judge-loop as appropriate.
## Experience Accumulation
After using this skill, fold new failure modes back into the smallest owning surface:
- workflow routing failure -> this SKILL.md;
- actor selection failure -> `modules/multi-model-dispatch.md`;
- Codex-specific completion or session issue -> `modules/codex-integration.md`;
- port or history discrepancy -> `modules/retarget-map.md`;
- global skill matching drift -> `modules/mattpocock-skill-inventory.md`.
Do not add more historical prose to the main state graph unless it directly changes a node, edge, or validation gate.
