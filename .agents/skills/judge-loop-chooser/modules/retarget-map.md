# Module: judge-loop-chooser — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`judge-loop-chooser`](../SKILL.md)。本檔 = port 的**命門與誠實帳本**:哪些機制一對一映到
> skill-bettor、哪些**沒有本地資產被拿掉或整支重建、為何拿掉不是簡化**。
> 命門:antigravity 版的 deliverable 型(DR 報告／COMPLETENESS 覆蓋矩陣／Path B 精煉／技術選型
> fit-to-plan)在 skill-bettor **不存在對應資產** —— 這些都是 antigravity 瀏覽器自動化執行器
> (`automate.js`/`data.js`,YouTube→AI Studio→Gemini DR)的產物型態,skill-bettor 是 living-skills
> 資產工場,可判物完全是另一套東西。**本次 port 不是逐機制映射,是保留兩條可轉移軸(grounding 三態 +
> 獨立性階梯)、整支重建 deliverable 型分類表**。

---

## 1. 為何 deliverable 型不能逐字映,只能整支重建

antigravity 原版的 4 個 deliverable 型都錨在它自己的管線資產:
- DR 報告 / 卡片盒吸收物 → 錨 `dr-research-loop` 管線產物。
- COMPLETENESS 覆蓋矩陣 → 錨 `data.js` 的 `COMPLETENESS_RUBRIC`(14 維度技術實現等價物表)。
- Path B 精煉 → 錨 antigravity 的 `PATH_B_TEMPLATE` 產物型態;本地已存在
  [`path-b-reduction`](../../path-b-reduction/SKILL.md),但它只是 claim 約分 helper,不是這種 pipeline
  deliverable。
- 技術選型 fit-to-plan → 錨 `repo-wiki-converge`/`dr-research-loop`/`gemini-conversation-research`
  三個餵軸技能。

**這四個 antigravity 產物型態在 skill-bettor 不存在**。current state 已有本地 `dr-research-loop`,
但它產的是 `proposals/*.md` 的 DR proposal 迴圈,不是 antigravity 的 DR 報告/卡片盒吸收物/
COMPLETENESS 覆蓋矩陣/Path B 精煉/技術選型 fit-to-plan 管線;本 repo 也沒有 `automate.js`/`data.js`
或 `COMPLETENESS_RUBRIC`。逐字映射 = 讓 skill 引用一堆跑不動的東西 = 死 husk(與 antigravity
自己在 port northstar 時反的 Branch B 死 husk 同一類錯誤,見 antigravity 版 retarget-map.md §1)。

**正確姿勢**:保留 antigravity 版**真正可轉移的核心**(三態 grounding、T0-T3 獨立性階梯、意圖漂移
reviewer 的骨架),把 deliverable 型分類表**整支換成 skill-bettor 自己 ARCHITECTURE.md 定義的資產**
(演化 op 的 T0 聚合結果、holdout 畢業判決、DR proposal、spawn 新家族決策、plan/debate packet、
語意證據品質 review —— 見 SKILL.md D1-D6 表)。

---

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| 雙平台原生 skill(`.agents/skills/`)+ Claude 斜線命令薄轉發層(`.claude/commands/`) | **拿掉,單一 `.claude/skills/judge-loop-chooser/SKILL.md`** | skill-bettor 是 Claude-Code-only 單 host(CLAUDE.md 明文),無 Antigravity CLI/Gemini host 需要雙平台轉發 —— 與 `loop-harness-standard`/`harness-wiki` 已定案的單 host 事實一致,不是本 skill 新拿掉的維度。 |
| deliverable 型:DR 報告 / COMPLETENESS 覆蓋矩陣 / Path B 精煉 / 技術選型 fit-to-plan | **整支重建為 D1-D6**(演化 op T0 聚合 / holdout 畢業判決 / DR proposal / spawn 決策 / plan-debate packet / 語意 evidence-quality review) | 四個 antigravity 資產在 skill-bettor 都不存在(見 §1);D1-D6 錨在 skill-bettor 真實資產:`loop_wiki/_template/PROMPT.md`+`PLAN.md`、家族 `evals/`、`proposals/`、ARCHITECTURE §8 人閘④,以及本 skill 新增的低壓縮 packet/review 類型。 |
| grounding 三態 SSOT:`data.js` `COMPLETENESS_RUBRIC`(14 維度)+ `automate.js` 覆蓋矩陣格式 | **概念原樣映,活基座換成** `families/pinescript-audit/evals/runner.py` + `evals/judge.py`(program/absent/llm_judge 三種 check kind)+ `evals/cases/`+`evals/holdout/`(planted-defect fixtures)+ ARCHITECTURE.md §4 | 三態語意(已覆蓋/部分/未覆蓋 × 技術實現等價物/[推論])本來就通用;antigravity 的活基座是 prompt 模板常數,skill-bettor 的活基座是真實可執行的 eval harness —— 甚至比 antigravity 版更貼近「真的能重跑驗證」。 |
| 四層獨立性階梯(T0-T3,whose-weights) | **原樣映**,T2 具體工具換成本地 [`external-verify`](../../external-verify/SKILL.md)+[`path-b-reduction`](../../path-b-reduction/SKILL.md)+agy(Gemini)跨家族 findings | whose-weights 軸與平台無關;T2 現有「官方事實錨」「claim 約分」「跨家族 findings」三種來源,但都只給 evidence/findings,不給 admit。 |
| T2 方法之一:`path-b-reduction`(claim 約分四步驟) | **已本地落地**為 [`path-b-reduction`](../../path-b-reduction/SKILL.md) | 早期 retarget 帳曾標為未移植；current state 已有本地 skill。它補的是 claim 約分協議,非外部 fact 查證,也非 verdict。 |
| 意圖漂移 reviewer(SI1-SI8,intent=卡片盒問題/DR thesis/逐字稿源頭錨) | 保留骨架,retarget → [modules/intent-drift-review.md](intent-drift-review.md);intent 換成**兩個場景**(`PROMPT.md`+proposal/changelog 編號、或大迴圈研究題目) | Branch A 的核心,可乾淨映射(見該檔案自己的 retarget 小節)。SI5→單向流倒灌;SI6→hollow check 而非空口 [推論]。**canonical negative-space 實例(剪貼簿污染案)無對應** —— skill-bettor 尚無真實災難案例,已在該檔誠實標記,不強行造一個假案例撐場面。 |
| 5-axis 技術選型 fit-to-plan(`modules/fit-scoring-recipe.md`,餵軸=`repo-wiki-converge`/`dr-research-loop`/`gemini-conversation-research` Mode B) | **整支拿掉,不留退化版**(見 §3 判斷理由) | `repo-wiki-converge` 與 `gemini-conversation-research` 無本地基座;本地 `dr-research-loop` 存在,但不是 antigravity 技術選型 fit-to-plan 的餵源。且 skill-bettor 目前範圍沒有「該不該採用某 OSS 堆疊/repo」的決策情境。降級版會把不存在/不相容的餵源包成可用幻覺,不如誠實不留。 |
| Not For:「跑/診斷整條管線」→ `dr-research-loop` | **分流**:DR proposal 迴圈走 [`dr-research-loop`](../../dr-research-loop/SKILL.md);演化 op 沙盒走 [loop-harness-standard](../../loop-harness-standard/SKILL.md) | current state 已有本地 `dr-research-loop`;judge-loop-chooser 只選驗證標準/獨立性 tier,不驅動任一迴圈。 |
| Not For:「把報告抽成保真 markdown」→ `gemini-deep-research-extract` | **整條拿掉** | skill-bettor 沒有「DR 報告」這種資產可抽,對應的 Not-For 邊界不存在。 |
| 無 code-branch 不變量(antigravity:「別引入 judge_chooser.yaml/design-judge 沙盒」) | **保留精神,明確指向本地 `code-review`**:程式碼改動一律走 Claude Code 內建 `code-review`,本 skill 不重複造判決表 | 任務背景明文:skill-bettor「無 code/sandbox 分支,code 直接去 code-review」——這比 antigravity 版更明確地把落點釘死,不只是「不引入」,而是「有現成去處」。 |
| truth-verify 實測錨(2026-07-05/06 六 run 具體數字,agreement-gated review 兩結構洞) | **不搬數字,只搬課**(SKILL.md Gotchas + grounding module 各一句話轉述,明標「借來的教訓,非本地實測」) | skill-bettor current state 有 [`truth-verify-loop`](../../truth-verify-loop/SKILL.md) 方法 skill,但沒有 antigravity 那批 local engine/run history;那些數字不是 skill-bettor 證據 —— 與 `loop-harness-standard` retarget-map 已立的先例一致(D 編號決策帳本/commit 錨不搬)。 |

---

## 3. 為何 5-axis 技術選型分支是刻意的範圍砍除(deliberate scope cut),不是遺漏

判斷過程(誠實記錄,供未來覆核):
1. **技術選型餵軸不成立**:A/C 軸的 `repo-wiki-converge`(源碼 ground-truth wiki)與 E 軸的
   `gemini-conversation-research` Mode B(市場-gap 架構辯論)在本 repo 無本地基座。current state 的
   `dr-research-loop` 已本地落地,但產物是 skill 變現情報 proposal,不是 antigravity 技術選型
   fit-to-plan 的 D 軸餵源。
2. **skill-bettor 目前的範圍本來就不做這類決策**:它是一個 domain 固定(trading-strategy/Pine Script
   審計)的 living-skill 工場,技術堆疊本身很薄且已選定(Python stdlib + PyYAML + `claude`/`agy`
   CLI,見 `evals/runner.py` 的 import 清單),ARCHITECTURE.md 全篇找不到「評估要不要採用某 OSS
   repo/庫」的情境或待辦。
3. **退化版一樣是死 husk**:就算把 5 軸 rubric 的表格結構搬過來、拿掉餵軸連結,留下的東西仍然是
   「一張沒有東西可餵的表」——比不移植更糟,因為它看起來像可用而實際上第一次真正要用時就會卡住
   (幻覺可用性)。
4. **結論**:不寫 `fit-scoring-recipe.md`。若 skill-bettor 未來真的要接技術選型判斷(例如評估要不要
   把某個新的 backtesting/資料源 OSS 庫引進某家族),屆時應該先移植/重建至少 A 軸(源碼真相理解)的
   本地餵軸能力,再回頭寫這個 module —— 不是現在硬造一個空殼。

---

## 4. 拿掉/重建的東西不是「簡化」,而是「資產不存在或情境不成立」

- **能一對一映的映**:三態 grounding 概念、四層獨立性階梯概念、意圖漂移 reviewer 骨架(8 探針 +
  自適應簽名 + 證據表 + 自評)、recipe-not-engine 不變量、Same-Weights 判準。
- **活基座換掉**:grounding 錨 `data.js COMPLETENESS_RUBRIC` → `evals/runner.py`+`evals/judge.py`+
  `evals/cases`;T2 工具 → 本地 `external-verify` + `path-b-reduction` + agy findings;
  意圖漂移 intent 錨 → `PROMPT.md`/proposal/研究題目。
- **整支重建**:deliverable 型分類表(D1-D6 全新,對應 skill-bettor 資產與新增 packet/review 類)。
- **誠實拿掉,不留退化殼**:5-axis 技術選型分支(§3)、雙平台轉發層、antigravity DR 報告抽取
  指向(`gemini-deep-research-extract`;本地 `dr-research-loop` 另作 DR proposal 迴圈)。
- **後續校正**:`path-b-reduction` 已本地落地;舊「未移植」缺口已關閉,但仍只是 T2 helper,不可寫成 verdict。
- **不搬歷史證成紀錄**:truth-verify 具體數字、antigravity/northstar 自己的 port 決策編號。

## 5. 判別「retarget 成立」的鐵錨(本檔撰寫時已用 `test -e` 逐一驗證)

skill-bettor 側(全部已驗證存在):
`ARCHITECTURE.md`、`CLAUDE.md`、`families/pinescript-audit/evals/{runner.py,judge.py,mock_agent.py,
no_skill_agent.sh,trigger-evals.json}`、`evals/cases/repaint-detection/{001-security-lookahead,
002-htf-confirmed-safe}/expect.yaml`、`evals/holdout/repaint-detection/003-realtime-alert/
expect.yaml`、`families/pinescript-audit/{FAMILY.yaml,changelog/2026-07-11.md,shared/snippets,
skills/repaint-detection/SKILL.md}`、根 `proposals/`、`loop_wiki/_template/{PROMPT.md,PLAN.md,
selftest.sh,verify.sh}`、`loop_wiki/engine.sh`、`.claude/skills/{loop-harness-standard,harness-wiki}/
{SKILL.md,modules/retarget-map.md}`、同批移植的 `.claude/skills/{external-verify,sdlc-plan-composer,
fold-in,html-for-decisions,loop-harness-review-handoff,unknown-discovery-composer}/`(已落地或落地中,
見各自 retarget-map)。

antigravity 源側(全部已驗證存在):`.agents/skills/judge-loop-chooser/{SKILL.md,modules/
{grounding-and-independence,intent-drift-review,fit-scoring-recipe,retarget-map}.md}`、
`.agents/skills/{path-b-reduction,external-verify,dr-research-loop,repo-wiki-converge,
gemini-conversation-research}/SKILL.md`、`data.js`(`COMPLETENESS_RUBRIC`/`PATH_B_TEMPLATE` 現址,
已模組化搬離 `automate.js`,舊 skill 文件行號引用不繼承)、`automate.js`。

若哪天有人往本 skill 塞回 DR 報告/覆蓋矩陣/Path B 精煉當 deliverable 型、重建 5-axis 技術選型分支
卻沒有本地相容餵軸能力、或把 `path-b-reduction` 寫成 verdict/admit 而非 claim 約分 helper ——
那就是把不適用/不存在的資產搬回來,擋下。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/judge-loop-chooser/`(SKILL.md +
  `modules/{grounding-and-independence,intent-drift-review,fit-scoring-recipe,retarget-map}.md`;
  其本身 port 自 `/Users/neon/northstar/.claude/skills/judge-loop-chooser/`,上上游帳本見 antigravity
  版 retarget-map.md,本檔只承 antigravity→skill-bettor 這一段,不重複複述 northstar→antigravity 那段)。
- skill-bettor 既有同構:`ARCHITECTURE.md` §4(Verify 三層)、§5(tier-dispatch)、§8(人閘清單) ——
  本 skill 的 grounding/獨立性快查表是這幾節的「逐 check/逐 claim 深度展開版」,不重複其內容,只加
  「可判標準」的紀律外殼。
- 同批移植先例(同一 rigor 要求):`.claude/skills/loop-harness-standard/modules/retarget-map.md`、
  `.claude/skills/harness-wiki/modules/retarget-map.md`(單 host 拿掉 2×2 矩陣、不搬歷史證成紀錄的
  判準,本檔沿用同一套判斷邏輯)。
