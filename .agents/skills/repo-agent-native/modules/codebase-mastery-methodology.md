# 方法論：「codebase 完全掌握」可複用配方(Codebase Mastery Recipe)

> 屬 [`repo-agent-native`](../SKILL.md)。Layer B know-why。**這是 antigravity
> `repo-agent-native/modules/codebase-mastery-methodology.md` 的 skill-bettor retarget**——這是
> northstar→antigravity→skill-bettor 鏈的第三環，antigravity 版本身已是 northstar 版的 retarget(見
> antigravity 版自己的 `retarget-map.md`，本檔不重複那一段)。配方(4 步＋8 probe＋evaluator-first＋RIP
> 封頂)**一對一映**，是全平台無關的推理紀律；**唯一的實質降級是 Step 3**(見下)，因為餵軸技能
> `gemini-conversation-research` 在 skill-bettor 不存在(本批次明確不移植)。配套提示詞 →
> [`specs-as-code-prompt.md`](specs-as-code-prompt.md)。**2026-07-23 更新**：
> skill-bettor 已新增 `.claude/skills/repo-wiki-converge/` 作為 antigravity `.agents/skills/repo-wiki-converge`
> 的本地 port；它提供 L1 openwiki 收斂入口，但不提供 antigravity `kb-ingest`/KG ingestion。
> 本層仍是 L2 source-grounded 不變量與隱含設計合約機制，兩者互補，不互相取代。

> **適用對象**：要對一個**可讀的** target(repo、家族、共享 harness 引擎)建立「完全掌握」型規格。
> **核心命題**：對可讀 target，**SOURCE 是 SSOT，人工研究只是補外部缺口的支流**；把外部研究當主幹去
> 「研究」一個能直接讀的 codebase＝**漏斗倒置**(funnel inversion)，既貴又會吞掉 README／brief 行銷語
> 當事實。

---

## 0. 為什麼「研究優先」是漏斗倒置(the funnel inversion)

功能漏斗鐵律：**最便宜、最確定的 Tier 起**。對一個能讀的 target：

| Tier | 工具(skill-bettor 實base) | 對「掌握一個可讀 target」的角色 | 成本／確定性 |
|------|--------------------------|------------------------------|--------------|
| **Tier 0** | Glob／ripgrep／Read 源碼 | **SSOT**——每條事實附 `file:line`，可逐字複驗 | 0 token、最高確定性 |
| Tier 1 | `grepai_search`／`grepai_trace_*`(需 target 已建索引，見 `../SKILL.md` Evidence Level 段) | 在已讀源碼上做符號／語義／call-graph 導航 | 低、高(索引未建時不可用，退回 Tier 0) |
| Tier 3 | 人工單次研究(內建 `research` skill)，**非**迭代多 DR | **只補真外部缺口**(生態譜系、上游契約、跨 repo 對比)；skill-bettor 無自動化收斂機制(見 §3 降級說明) | 中、one-shot 品質，非收斂品質 |

**倒置的代價**：
- README／brief 只給**宣稱層**——真正的 gotcha(host-side 行為、平台條件 no-op、確定性 vs agent-judged
  邊界)只能從源碼＋changelog 浮現，**永不在 README**。
- 研究優先會把「合理但錯誤的推測」寫進規格；只有回源碼逐 `file:line` 驗才會**推翻**它(最高價值點)。
- 把確定性編排器誤讀成 agentic 自評迴圈：外部研究看不出「gate 是 exit-code 還是 LLM judge」，源碼一眼
  定生死(如 `evals/runner.py --compare` 是確定性 G1-G3，`llm_judge` checks 才是 heuristic，兩者混為一談
  是常見誤讀)。

> **判據(何時可反過來用外部研究當主幹)**：target **不可讀**時——閉源、只有 SDK、runtime-only 黑盒行為、
> 或要的是「這東西在生態裡的位置／上游 wire protocol」而非「它自己怎麼寫」。此時 SOURCE Tier 0 無料可吃，
> 研究才升主幹(並仍須過 `external-verify`)。**可讀 target 用研究當主幹＝反模式。**

---

## 1. 配方四步(the four-step recipe)

### Step 1 — SOURCE＝SSOT 漏斗：先讀源碼，確認 canonical target
1. **確認 canonical target**：家族內部改動直接對齊 `families/<family>/`；外部 repo 對齊其
   `package.json`/`pyproject.toml`/README 連結，別對 fork／鏡像／過時 tag 讀。記下版本錨(如
   `FAMILY.yaml` 的 `version` 欄、外部 repo 的 `package.json` version)。
2. **本地家族不需要 clone**(已在 disk)；外部 target clone 到中性工作區(全歷史，never `--depth 1`)，
   所有後續 `file:line` 都指這裡。
3. **Tier 0 起**：`FAMILY.yaml`(interface/metrics 性質)→`SKILL.md`(路由器承諾)→`shared/conventions.md`
   (顯性契約)→子技能 `skills/<sub>/SKILL.md`→`evals/`。第三方 target 要跑 `grepai` 前先對 target 目錄
   建索引(見 `../SKILL.md` Evidence Level 段的 Gotcha)。**禁跳層**到語義檢索之前先把骨架讀出來。
4. **每條進規格的事實必附 `source_ref`(path＋line)**。不能附 line 的(外部生態、上游假定)標**⚠ 需人工
   二次確認**——誠實邊界，非失敗。

### Step 2 — 通用 IMPLICIT-DESIGN PROBE checklist(把靜態 catalog 變成真掌握)
> 配方的**靈魂**。naive 三檔模板(architecture／data-flow／security 問 SQLi/XSS/N+1)只抓 API 表面＋
> 漏洞清單，**系統性漏掉隱含設計決策**。下面 8 條 probe 是**通用**的，對任何 codebase 都把「長得像讀過」
> 逼成「真的掌握合約」。

| # | Probe | 問句(對源碼提問＋回證偽) |
|---|-------|------------------------------|
| 1 | **Seam(接縫)** | 哪些是可抽換的擴展點？(如新增一個家族要不要碰 `loop_wiki/engine.sh`？新增一個 check kind 要不要碰 `judge.py` core？) |
| 2 | **Determinism boundary(確定性邊界)** | 每個 gate／判定是 exit-code／字串掃描(確定性)還是 LLM-judge／heuristic？畫出確定性 vs agent-judged 的線(如 `runner.py --compare` 的 G1-G3 vs `llm_judge` checks)。 |
| 3 | **Platform conditional(平台條件碼)** | grep target 是否有依 driver(`claude`/`agy`)、model tier 分叉的行為？某個 no-op 是 bug 還是「正確地什麼都不做」(如 quota 耗盡的 silent no-op)？ |
| 4 | **Bounded loop(有界迴圈)** | 迴圈上限／終止信號／timeout 的**預設值**是什麼？(如 `engine.sh` 的 `no-progress=2`/`exhausted=$MAX_ITERS`)引擎內建還是呼叫端組合？ |
| 5 | **Trust boundary(信任邊界)** | 哪些輸入不可信？(如 `proposals/` 未驗證內容禁被家族引用)信任邊界劃在哪？哪個開關會讓邊界塌陷？ |
| 6 | **Ergonomics(人因／DX 合約)** | 有沒有「方便但危險」的語法糖？(如把 `PROMPT.md` 全文餵給 driver 當祈使任務，已知反模式)它同時是 DX 合約也是攻擊面/反模式嗎？ |
| 7 | **Typed errors(型別化錯誤)** | 錯誤是 typed 還是裸 throw？(如 `verify.sh` 的 exit 0/2/64 是否真的區分清楚，還是都塞同一個 exit code) |
| 8 | **Framework idiom(框架慣用法)** | 整個 target 建在哪個框架慣用法上？load-bearing 還是裝飾？用硬數據釘住(如 grep 某 idiom 排家族剛好 N 個)。 |

**probe 為何系統性贏**：8 條共同根因＝**隱含設計決策／宣稱 vs 實測落差／跨情境條件分支／確定性邊界**。
這些**不在任何漏洞清單，也不在任何 API 表面**，只能由「對設計意圖提問＋回源碼證偽」觸及。關鍵手法：
**把 brief／README／FAMILY.yaml 假設當待證命題，回源碼逐 `file:line` 證偽**(推翻假設即最高回報)。

### Step 3 — 真外部缺口的處理(降級版，非迭代多 DR)
> **這是本檔相對 antigravity 版唯一的實質降級**。antigravity 版靠 `gemini-conversation-research`
> 迭代多 DR 收斂真外部缺口(S7 gap→S8 multi-DR→回 S7 重算 coverage，收斂上限 3 輪)。**skill-bettor 沒有
> 這個工具**(本批次明確不移植：零 domain fit，會是死 catalog)。

Step 1+2 跑完後，剩下的⚠待確認項若是**外部**的(生態譜系、上游契約、跨 repo 對比)：
1. **不嘗試自動化多輪收斂**——沒有工具鏈可以迭代 gap→research→回填→重算 coverage。
2. **標記即完成**：在輸出頁的「External Gaps(未填)」小節逐條記 `⚠ 需人工二次確認`＋為什麼無法從源碼
   解決(是上游契約、是生態位置、還是需要 runtime 觀測)。
3. **需要進一步研究時，人工決定是否單次調用內建 `research` skill**(mattpocock 全局)——這是**一次性
   查找**，不是迭代收斂迴圈，找到的東西一樣要標來源，不能當已驗證事實直接寫回規格(仍須過
   `external-verify` 若涉 post-cutoff claim)。**能力不對等，明確記為降級**：`gemini-conversation-research`
   的 S7/S8 gap-fill 迴圈有「覆蓋率重算」「adversarial frontier pass」這類收斂機制；單次 `research`
   沒有，跑一次就結束，覆蓋率好壞全靠那一次研究品質。此降級沿用 `unknown-discovery-composer`
   retarget-map 已立的同一先例(該檔第 30 行：「DR 研究批次改走 `agy` 直發／`research`，是換了機制而非
   簡化同一機制」)。
4. **守住紅線不變**：對可讀 target，若 Step 1+2 已把已知需求覆滿就**不該**為了「完整」去研究外部缺口
   (＝supply-push catalog 墳場)。只為一個具名的外部缺口研究，demand-pull。

### Step 4 — EVALUATOR-FIRST 驗證：對 answer-key 計分＋迭代提示詞
> **driver 前先有 evaluator**。先有「對不對」的硬尺，才知道提示詞要不要再 harden。
1. **建 answer-key**：用**既有吸收**(家族 `SKILL.md`/`FAMILY.yaml` 承諾的介面、先前 plan 產出的不變量
   頁)、本地 `repo-wiki-converge` 產出的 openwiki，或一份 held-out fact set 當答案鑰匙。openwiki 只能
   當 SCOPE seed / answer-key candidate；load-bearing fact 仍須本 skill 回源碼複驗。
2. **逐條判 `yes/partial/no`**，證據**必須來自規格本身**(`file:line`)——防自洽幻覺。
3. **load-bearing 條目回源碼複驗**(規格說對≠自洽，要對源碼逐字核)。
4. **算 coverage_pct**＋標 MISSES＋beyond-key surfaced。
5. **迭代提示詞**：哪條 answer-key 被漏 → 對映到 Step 2 哪條 probe 不夠硬 → 補進 file spec → 重跑。
   **fresh-context 稽核**(非作者跑 evaluator，避免自我背書——同家族 author×judge 必 fresh subagent，
   沿用 `loop-harness-standard` 已立的驗證器/執行者隔離不變量)。
6. **收斂判據**：answer-key 全 `yes`＋規格在 beyond-key 處有 surface＋每條 load-bearing 回源碼複驗屬實。
   **收斂由人接受**(人 LAND-DECISION，禁自動接受規格)。

### Step 4.5 — RIP 封頂：behavioral／runtime claim 只能真跑定案
> **evaluator-first 對_靜態_事實(結構／設計合約／型別)有效；對 _runtime 行為_(某 op 是否真的收斂、
> 某 check 是否真的區分 good/hollow、perf 數字)不夠**——**源碼讀＋窄 probe 都會 over-reach**。

繼承教訓(上游 lineage 的通用案例，非 skill-bettor 本地事故)：源碼讀證明 prior 歸因錯 → 窄 probe 據此
推「某功能在某情境下可行」並寫入規格 → 但完整端到端真跑才證明實際上 reproduced-broken → 推翻先前結論。
這說明**任何 behavioral 結論都必須真跑過才能定案，不能只靠讀+窄測就下筆**。

**鐵律**：任何 behavioral／perf claim 進規格前，跑一次**完整 RIP**(真跑該操作的端到端路徑，不是窄
probe)定案——skill-bettor 的載具就是家族自己的 `evals/runner.py`／`selftest.sh`／`loop_wiki/engine.sh`。
**Evidence A 僅當 runtime 真跑過該完整路徑；源碼推論／窄 probe 最高 B**(且必標「未 RIP」)。

---

## 2. 一句話精華
對**可讀** target，**SOURCE 漏斗(Tier 0 源碼＝SSOT)＋通用 implicit-design probe(8 條)**就能重發現
README-level 吸收的全部 answer-key 並超越它；**真外部缺口標記即止**(skill-bettor 無迭代多 DR 收斂
機制，需要時人工單次 `research`，明確降級非等價)，**evaluator-first 對 answer-key 計分並回頭硬化提示
詞**，**behavioral claim 完整 RIP 定案**(家族自己的 `evals/runner.py`/`selftest.sh` 當載具)。

---

## 與「廣度理解」的邊界
antigravity 原版這裡講的是「與 `repo-wiki-converge` 的邊界」：那邊是 Gemini-author×Opus-judge judge-loop
產廣度理解 wiki，這邊是 8-probe＋evaluator-first 產隱含設計合約規格，兩者不競爭。

**skill-bettor 現在有本地 `repo-wiki-converge` port，但能力邊界比 antigravity 原版窄**：
本地 port 生成 repo openwiki 並用 deterministic gate 驗證使用入口/lifecycle/state graph/code-call wiring；
它產的是 OKF 散文 wiki 並進 RepoDoc lane，**不產 `source_ref` 級不變量**。它可餵 S0 SCOPE 與 answer-key candidate，不能直接
升級成 Evidence A。Evidence A 仍需本 skill 的 source-grounded extraction / RIP。

---

## Sources / Lineage
- antigravity 源：`/Users/neon/antigravity/.agents/skills/repo-agent-native/modules/
  codebase-mastery-methodology.md`(其自身標記為 northstar 版的 retarget，sandcastle worked-example
  是 northstar 專屬產物，antigravity/skill-bettor 均無)。
- 活基座：`grepai`(需索引，見 `../SKILL.md`)、`external-verify`(本地同批移植)、內建 `research`(單次
  查找，降級替代 `gemini-conversation-research`)、`repo/agent-skills-repo/tests/`(本 mirror 可驗的 RIP
  載具)、`loop_wiki/engine.sh`(RIP 載具的另一本地 worked instance)。`families/pinescript-audit/evals/`
  只屬源 repo lineage，本 mirror 當前不存在。
- **明確拿掉，非簡化**：`gemini-conversation-research` 迭代多 DR 收斂機制(見 §3)；
  antigravity `repo-wiki-converge` 的 `kb-ingest`/KG ingestion 執行器；sandcastle worked-example
  (北極星專屬，antigravity 自己也沒有)。
