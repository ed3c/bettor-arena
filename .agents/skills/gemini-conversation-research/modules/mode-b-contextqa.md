# Module: Mode B — Context-QA 主動研究（S-1 + S0-ALT）

> 屬 [`gemini-conversation-research`](../SKILL.md) §Mode B。**不抽取已有對話**，而是**主動開新 Gemini 對話**逐輪 Q&A、再併回 S1 分析。
> 追問怎麼構造 → [first-principles-probe.md](first-principles-probe.md)；主線 S1-S9 → [conversation-pipeline.md](conversation-pipeline.md)。
> **retarget 註**：northstar 的 signal-scanner / openclaw dispatch 上游**拿掉**（antigravity 無此基座）；觸發源 = 使用者直接給主題 + 上下文。資料主權的 northstar 內部名 regex 表**拿掉**，保留泛化紀律（見 §資料主權）。

---

## S-1: CONTEXT-LOAD — 讀取研究上下文

**前置**: Mode B 觸發（無 URL，使用者給主題 + 上下文）。
**步驟**:
1. 從當前對話 / 使用者輸入萃取 `context_extraction: {research_topic, key_questions[], background, private_context[]}`。
2. 構造 Q&A 計劃：`qa_plan.{topic, questions[].{q, intent, expected_density}}`。
   - `intent ∈ {explore, validate, compare, quantify}`；`expected_density ∈ {data, framework, case_study}`。

**Checkpoint**: `qa_plan.questions >= 3`。
**硬數據**: `s_neg1_context: {mode: user_input, research_topic, questions_planned, context_chars}`

---

## S0-ALT: CONTEXT-QA — 主動 Gemini Q&A 研究

**前置**: S-1 完成，qa_plan 已構造。
**核心**: 主動開新 Gemini 對話逐輪提問；每輪後 Claude 評估回應密度動態調整下一輪。

**步驟**:
1. 取得已登入瀏覽器頁面（同 S0：research profile 或 CDP `:9333` fallback）→ 新對話。
2. **Round 1 主題定錨**（1 大問題建立上下文，含背景、公開術語）→ 送出 → 快捷模式 ~10s → 抽最後一條回應。
3. Claude 評估 Round 1：密度（sufficient/partial/shallow）+ 識別追問方向。
4. **Round 2-4 深入追問**（基於回應動態構造）：追問構造走 [first-principles-probe.md](first-principles-probe.md)（引用-鑽入 + 反向自陳 + first-principles 約分，**鑽到鐵錨而非泛泛「要數據/案例/比較」**）。
5. 每輪累積密度評分、識別 research_gaps。
6. **收斂判定**：全部 sufficient 或 4 輪用完 → 結束。剩餘 gaps 送 S2 DR。
7. 合併整段對話文本 → 寫檔 `gemini_research/<topic>-qa-session.md`；記 `conversation_url`。

**Q&A 上限**: 4 輪（R1 定錨 + R2-4 追問）。
**Checkpoint**: `rounds_completed >= 2` AND `total_response_chars > 3000`。
**硬數據**: `s0_alt_qa: {mode: context_qa, rounds_completed, rounds_max:4, total_response_chars, density_per_round{}, research_gaps_remaining, conversation_url, local_path}`

**完成後**: 併回主管線 → [conversation-pipeline.md §S1](conversation-pipeline.md)（用 Q&A 全文作分析輸入）。

---

## 資料主權（P0，每輪 prompt 構造前）

**紀律**：送給外部 Gemini 的 Q&A prompt **只含公開可得的概念與術語**，**不洩漏私有專案脈絡**——
- 不含私有專案 / repo / 客戶的專有名詞、內部代號、內部路徑。
- 不含商業敏感的識別碼（channel ID、token、私有 URL）。
- 需要用到私有脈絡描述架構時，**泛化成公開術語**（例：某內部代號 → 其通用架構描述）。

> retarget 註：northstar 版有硬編碼 `BLOCKED_PATTERNS` regex 表（DDR-NNN / Bug Scar / local_stack / openclaw / ixsecurity 等**northstar 內部名**）+ 確定性 `sovereignty_check()`。那些名字在 antigravity 不存在，**regex 表拿掉**。若本 repo 累積出需要固定過濾的私有詞，可在此 module 補一張 antigravity 自己的 pattern 表（demand-pull，別預先造空表）。**紀律不變**：越界洩漏私有脈絡 = BLOCK 修正後重試。

**Checkpoint**: 每輪 prompt 過人審 / pattern 表（若有）確認無私有脈絡洩漏。

---

## Mode B 啟動意圖（自然語言，非 northstar 治理術語）

- **主題驅動**：「用 Gemini 研究〈主題〉。上下文：〈背景〉。需要分析〈方向 1〉〈方向 2〉的權衡。」
- **帶主權約束**：「用 Gemini 研究〈主題〉。不可提及具體專案名 / 內部代號 / 識別碼，只用公開術語描述架構。」

> retarget 註：northstar `activation-prompts.md` 的 GCR-0..5 含「已授權 stealth surface / autoMode.environment / INV-HUMAN-GATE」等 northstar engine-locus 術語——**拿掉**。antigravity 的閘就是「人跑瀏覽器 / 人開 CDP」，用平白話說即可。
