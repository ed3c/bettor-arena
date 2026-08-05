# Module: Guided Conversation Observation — buttons, auto-prompts, and semantic-loss control

> 屬 [`gemini-conversation-research`](../SKILL.md)。本模組補上 Gemini 對話中「非固定複製按鈕」的引導按鈕觀察與順序觸發程序。這些按鈕可能是「是」、延伸方向、比較方向、追問方向；它們不是固定 UI chrome，而是 Gemini 根據上下文產生的 conversation continuation affordance。

## Purpose

把 Gemini 引導對話從「一次抽取文本」提升成 stateful workflow：

```text
G0 Source Intake
  -> G1 Match Conversation State
  -> G2 Observe Candidate Buttons
  -> G3 Select Next Branch
  -> G4 Trigger In Context Order
  -> G5 Capture Auto Prompt And Answer
  -> G6 Normalize Missing Context And Domain Terms
  -> G7 Verify Semantic Truth
  -> G8 Emit Golden Trace / Behavior Eval
```

**不可壓成單一 prompt**。匹配、生成、驗證必須是不同 state graph 節點；每個節點只改自己的 state delta。

## State Contract

```yaml
guided_conversation_state:
  source_url: "https://gemini.google.com/app/<id>"
  conversation_id: "<id>"
  source_turn_index: 0
  observed_events:
    - event_id: "E001"
      event_type: "assistant_response|suggestion_button|auto_prompt|auto_answer|user_prompt"
      text: "<verbatim-or-normalized-label>"
      dom_role: "conversation_turn|contextual_suggestion_button|generated_prompt|generated_answer"
      order_index: 1
  pending_buttons:
    - label: "是"
      button_kind: "continue_yes|explore_direction|compare_direction|probe_gap|unknown"
      parent_event_id: "E001"
      context_before: "<short context packet, not full transcript>"
  chosen_branch:
    button_label: "是"
    reason: "continues current semantic thread before lateral exploration"
  missing_context:
    simplified_information: []
    lost_information: []
    missing_domain_terms: []
  prompt_context:
    fixed_prompt: "<stable role + state graph contract>"
    iteration_auto_prompt: "<generated from observed_events + pending_buttons>"
    emergent_prompt: "<new prompt created from unexpected button/term/gap>"
  verification:
    judge_loop: "judge-loop-chooser"
    judges: ["codex", "agy", "opus-or-human"]
    verdict: "pass|candidate|human_required|fail"
```

## Conditional Edges

| edge | condition | next |
|---|---|---|
| `G1.has_contextual_buttons` | non-copy buttons appear after assistant response | `G2 Observe Candidate Buttons` |
| `G1.no_contextual_buttons` | no contextual suggestion button | `G6 Normalize Missing Context And Domain Terms` |
| `G2.button_is_yes_continue` | label is `是` or equivalent continue confirmation | `G4 Trigger In Context Order` |
| `G2.button_is_lateral_direction` | button opens a different exploration direction | queue branch, keep current order |
| `G2.button_is_probe_gap` | button asks to build evals, guardrails, missing-term definitions, or implementation proof | `G4 Trigger In Context Order` with a repair-first auto prompt |
| `G5.answer_adds_domain_term` | auto answer introduces new specialized term | `G6 Normalize Missing Context And Domain Terms` |
| `G6.context_loss_detected` | simplified/lost info or missing term exists | `G3 Select Next Branch` with repair prompt |
| `G7.truth_uncertain` | semantic truth not grounded | external-verify / judge-loop-chooser / human |
| `G7.pass` | all required branches captured or explicitly deferred | `G8 Emit Golden Trace / Behavior Eval` |

## Button Handling Rules

- Treat contextual suggestion buttons as conversation events, not UI decoration.
- Preserve button order exactly as observed.
- Trigger contextual buttons in context order before inventing new prompts.
- If multiple buttons compete, classify them first: continue-current-thread, lateral-exploration, compare/contrast, probe-gap, unknown.
- For `是`, default to continue-current-thread unless surrounding text proves it is consent for a different branch.
- Do not trigger fixed copy/share/retry UI buttons; only contextual exploration buttons belong to this workflow.

## Browser Carrier AUP Contract

G2/G4/G5 不能靠 `domSnapshot` 或 conversation `textContent/innerText` 把 Gemini 頁面送回主會話。使用 [browser-content-isolation.md](browser-content-isolation.md) 的固定程序：

1. `captureGeminiGuidanceProjectionFromBrowserTab` 只從最新 model response 內、明確 suggestion container 的可見文字按鈕投影候選；generic chip/source/citation container、歷史回合、全頁 ordinal、固定 toolbar 或 ownership 不明都不是候選。label + bounded `context_before` 寫入 `gemini_research/gcr/<id>-guidance-<round>.json`，主會話只收 receipt。
2. 隔離子代理讀 projection，只回 `candidate_index`、`button_kind`、`reason`；不回 label/context 原文。
3. 優先使用 `runGeminiGuidedConversationBrowserEdge` 組合 capture → Bun decision → optional click；它預設 dry-run。只有 `click_ready` 才能顯式允許 click，且底層必須綁 capture receipt 的 exact projection SHA-256，再於點前 fail-loud 重驗 latest model turn ownership、suggestion container、label 與 bounded parent context SHA-256。
4. `submit_ready` 只能由 `submitGeminiEmergentPromptFromDecisionFile` 從 exact decision bytes 送出；`allowSubmit` 預設 false。相同 prompt 已是最後 user turn 時必須冪等，不可重送；此時必須有完全匹配的 `response_pending` receipt 才能恢復原始 model baseline。
5. `inspectGeminiConversationMetadataFromBrowserTab` 只輪詢同一 selector policy 的 turn counts、last-response char count 與 streaming flag；連續兩次穩定且 model turn 相對持久化 baseline 已前進，才用完整 extractor 寫檔並回 `analysis_required`，再交隔離子代理做 G5/G6。user/model count 不可互相比較。

任何 safe adapter 失敗都不得退回 snapshot；應記 `browser_content_boundary_failure` 並停止該 edge。

## Semantic-Loss Repair

被簡化的資訊、遺失資訊、遺失 Domain 專有名詞要變成 state，不是藏在 prompt 裡：

```yaml
semantic_loss_ledger:
  simplified_information:
    - original_signal: "<what was compressed>"
      current_short_form: "<compressed phrase>"
      risk: "LLM may pick wrong route"
      repair_action: "ask Gemini to restate exact assumption before continuing"
  lost_information:
    - missing_source_span: "<turn/button/event id>"
      impact: "breaks branch ordering"
      repair_action: "return to previous event or mark human_required"
  missing_domain_terms:
    - term: "<unknown term>"
      first_seen_event: "E012"
      inferred_meaning: "<candidate meaning>"
      grounding_status: "candidate|verified|human_required"
      repair_action: "ask definition in-context before using term in downstream prompt"
```

## Prompt Slots

- `fixed_prompt`: stable state graph contract, no task-specific compression.
- `iteration_auto_prompt`: generated from current `observed_events`, `pending_buttons`, `missing_context`, and previous verdict.
- `emergent_prompt`: only for unexpected button labels, new domain terms, or semantic conflicts.

All prompt slots must be serialized into the golden trace. If a slot is empty, write a reason such as `N/A-no-unexpected-button`; do not omit it.

## Golden Dataset Requirement

Every production run should be reducible to a golden case:

```yaml
case_id: "gcr-guided-047d548-001"
source_url: "https://gemini.google.com/app/047d548af8f8e34c"
expected_event_order: ["assistant_response", "suggestion_button", "auto_prompt", "auto_answer"]
expected_state_nodes: ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
expected_conditional_edges: ["G1.has_contextual_buttons", "G5.answer_adds_domain_term"]
required_prompt_slots: ["fixed_prompt", "iteration_auto_prompt", "emergent_prompt"]
truth_policy: "judge-loop-chooser with codex/agy/opus-or-human"
```

The small-loop template and eval live under `loop_wiki/evolve-unknown-discovery-plan-truth/templates/gemini-conversation-research/`.

## Physical Trace Artifacts

The production seed is not only the case list. A valid guided-conversation run must be serializable as:

- `golden/guided-conversation-cases.json`: expected behavior cases and button policies.
- `golden/guided-conversation-traces.json`: physical event order, graph transitions, prompt slots, semantic-loss ledger, and terminal artifacts.
- `schemas/guided-conversation-trace.schema.json`: required field names, status values, and the rule that `external_engine_required` traces must not claim live browser execution.

## Executable File Handoff

`scripts/run_guided_conversation.py` 是 source-oracle，Bun target runtime 是
`loop_wiki/evolve-unknown-discovery-plan-truth/adapters/typescript/runtime/loop_wiki/evolve-unknown-discovery-plan-truth/scripts/run_guided_conversation.ts`。
兩者只接 file input/output，stdout 只回 bounded metadata receipt；候選欄位直接沿用 browser adapter
`gcr-guidance-projection@0.2.0` 的 `candidate_index`、`label_sha256`、
`context_before_sha256`、`disabled`，禁止另造相似但接不上的欄位。

一次執行只處理一條 edge：未捕獲回答時輸出 `click_guidance_candidate` 或
`submit_emergent_prompt`；把 captured auto prompt/answer 寫回 input 後再執行，且
`truth_verification.verdict=pass`，才可輸出 G0-G8 trace。candidate 停在
`external_verify`，human-required/fail 停在 `human_review`。空 candidate array 不是 unknown
button，必須走 `G1.no_contextual_buttons -> G6`；三個 semantic-loss arrays 可全空，此時走
`G6.no_context_loss`，不得捏造 repair event。queued branch 必須逐項保存實際 deferred reason；
unknown hint 必須附 `button_kind_hint_reason` 與 `isolated_hint` provenance。
最多三輪；未知按鈕不得猜著點，達上限輸出 `human_required`。輸入/輸出 schema 見
`templates/gemini-conversation-research/schemas/guided-conversation-run-*.schema.json`。

If a Gemini URL has not been extracted by the external browser/CDP engine, set `source_status=external_engine_required`, `evidence_grade=template_seed`, and `live_execution_claimed=false`. Do not convert a URL-only seed into a verified trace by narrative inference.
