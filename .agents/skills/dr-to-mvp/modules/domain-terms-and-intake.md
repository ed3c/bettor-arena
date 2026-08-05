# Module: dr-to-mvp — Domain Terms + Intake Discipline

> 屬 [`dr-to-mvp`](../SKILL.md)。本檔是冷啟動脊椎的 Domain 詞彙與被降權資訊索引。
> `SKILL.md` 保留 state graph 與會改變路由的決策語意；本檔保留 fresh LLM 需要理解但不該塞回主路由的專有名詞、intake 紀律、稀有 gotcha。

## 1. 被簡化資訊的歸宿規則

| 資訊類型 | Durable home | 何時讀 |
|---|---|---|
| 會改變下一條 edge 的決策語意 | `SKILL.md` state/node contract | 每次冷啟動必讀 |
| 可貼逐階段操作骨架 | `reference/guiding-prompt.md` | 需要產出完整 playbook 或 dispatch packet 時 |
| antigravity→skill-bettor 移植判斷、拿掉什麼 | `modules/retarget-map.md` | 懷疑某機制是否被錯刪/錯搬時 |
| Domain 詞、語料 intake、被降權 gotcha | 本檔 | fresh LLM 不懂術語、Mode B 語料、或 claim provenance 不清時 |
| owner skill 內部程序 | owner skill 真檔 | 進入該 Phase 後才讀 |

硬規則：資訊可以降權，不能無索引消失。若從 `SKILL.md` 移走一條 load-bearing 語意，必須落在 `reference/` 或 `modules/`，並從 `SKILL.md` 的 References 指到。

## 2. Domain Terms（產物首次使用需展開）

| Term | Meaning | Operational consequence |
|---|---|---|
| cold-start spine / 冷啟動脊椎 | 從研究題或 DR 語料長成全新 family runtime 的大流程。 | 只用於新 durable family/runtime，不處理既有家族日常演化。 |
| Phase R | Research → verified base。 | 產物不是 MVP；出口是 verified/adopted base + human admit。 |
| Phase G | Gap closure + prototype evidence。 | KU 讀源；UK 做實測或由 MVP seed 自身承載。 |
| Phase M | MVP seed → 八大基座小迴圈 → 畢業。 | 進 `loop_wiki/<loop>/src/`，用 dual-score 畢業。 |
| SURFACE | 停下把證據、風險、下一步交人核。 | 模型不得 auto-chain 下一 Phase。 |
| LAND-DECISION | 畢業、merge、homing 類最終人裁。 | Opus/agy findings 只是證據，不是 admit。 |
| Mode A | 有具體研究題或 URL。 | 通常跑 `dr-research-loop` proposal。 |
| Mode B | 已有 DR 語料或對話語料。 | 先分類、查既有錨、只做增量驗；不可盲跑新 DR。 |
| verified base | T0/D3/primary-source 支撐的可信基底。 | 可以餵 Phase G/M；未驗敘事不可直接當設計前提。 |
| Path B | 待驗敘事、推論、或未閉合接縫。 | 必須標 `[推論]`、`candidate` 或 `human_required`，不可平滑敘事化。 |
| Half-Bridge | 從未驗材料跳到結論，中間缺可重驗錨。 | D3 或 V0 必須擋下。 |
| D3 adopt | `judge-loop-chooser` 對 proposal 是否可採納的語意裁決。 | 對照 `origin_question` 查意圖漂移；agy 只 findings。 |
| D4 validation prototype | 只為回答一個 UK gap 而建的驗證型 prototype。 | 答完留錨，不刪、不升格 `src/`。 |
| MVP seed prototype | 已被 admit、準備長成 durable runtime 的種子。 | 可進 Phase M；不是 D4 半成品。 |
| KU / UK / UU | Known unknown / unknown known 等 gap 分類在本 skill 的操作化簡寫。 | KU 讀源可答；UK 需實測；UU 只標盲點，不假裝已關閉。 |
| dual-score | 設計分與實作分的 AND gate。 | `DESIGN-SCORE.md` 零 MISS + `verify.sh` exit 0 才能畢業。 |
| families-type homing | 把畢業 runtime 搬進 `families/<f>/shared/runtime/<mvp>/`。 | 本 repo 唯一 homing 型；搬完必在最終位置驗證。 |
| route ledger | 記錄每個 state 的 decision/evidence/actor/validator/edge 的表。 | 產物缺 route ledger = fresh LLM 需要猜，視為不合格。 |
| actor | 負責生成、修改、研究、或執行的角色。 | Codex 實作；agy 研究/複核 findings；scripts 驗 deterministic facts。 |
| validator | 負責判定 artifact 是否通過的角色或機械閘。 | Opus fresh 判語意；scripts 判 exit code；human admit phase/homing。 |
| `technical_equivalent` | 讀過且必要時跑過/比較過，證明真做同一件事。 | 可作 premise。名字像不算。 |
| `candidate` | 真實 component/source 存在，但覆蓋或等價未證。 | 只能開調查或比較 slice。 |
| `[推論]` | 沒有直接錨的推論或 LLM 判斷。 | 必須 surfaced，不得當事實。 |
| `human_required` | repo facts 無法決定的範圍、架構、產品意圖或 admit。 | 停下問人或列入 SURFACE。 |

## 3. Mode B 語料 Intake 紀律

Mode B 語料常同時含「逐字保真原文」與「知識萃取稿」。兩層不得混用：

| Layer | Meaning | Allowed use | Forbidden use |
|---|---|---|---|
| S0 逐字稿 | 原始對話、逐字轉錄、未清洗材料。 | 意圖考古：重建 `origin_question`、檢查記憶改寫、找意圖漂移辯論素材。 | 不可直接當計劃前提或事實錨。 |
| S1 萃取/整合稿 | 從 S0 或多來源整理出的知識層。 | 可作候選 claim 清單。 | load-bearing 數字、實體、趨勢未經 external-verify 前不可入基底。 |

Post-cutoff 實體要雙向警戒：
- 訓練記憶想不起來，不代表它是假。
- 語料裡講得很像真，也不代表它是真。
- 判 confabulation 前先走 `external-verify`；查得真值覆蓋語料原值。
- 標 still-unverified 的實體一律當未證，不餵 Phase M 設計分。

大檔處理：先關鍵詞 triage；命中冷啟動題目、具名實體、數字、授權、平台政策、技術等價物，才萃取成 S1。不要為了「完整消化」把整批語料壓進 plan。

## 4. 產物中的 Domain 詞處理規則

任何 `dr-to-mvp` 產出的 plan/report/dispatch packet：
1. 首次使用本檔 term 時，用「term：一句操作定義」展開。
2. 若用了本檔沒有的 Domain 詞，必須新增 `Glossary delta` 表：`term | intended meaning | source | grounding | unresolved`。
3. 若該詞會改變路由或 admit，不能只進 glossary；同時在 route ledger 標 `human_required` 或補 evidence。
4. 不允許只寫縮寫：`D3`、`D4`、`KU`、`UK`、`Path B`、`Half-Bridge` 首次出現都要帶語義。
5. Domain 詞不可被翻成一般詞後失去判準，例如把 `SURFACE` 寫成「回報一下」就是語意遺失。

## 5. 已復原的上一版高風險資訊

這些資訊不該塞回 `SKILL.md` 主路由，但不能丟：
- S0/S1 保真語料分工與 post-cutoff 雙向警戒。
- D4 artifact 留錨不刪、不升格的理由：刪掉會讓「UK 已關閉」失去可重驗鐵錨。
- Mode B 先查既有同主題錨，再做增量驗。
- families-type homing 的最終位置驗證與 `__file__` 相對路徑要求。
- antigravity 2×2 host matrix、remote/reference-impl homing 是架構前提不適用，不是能力縮水。
