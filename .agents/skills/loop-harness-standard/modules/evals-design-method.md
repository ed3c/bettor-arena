# Module: evals-design-method — evals 一次性 pre-registered 行為驗證設計法

> 屬 [`loop-harness-standard`](../SKILL.md)。**定位重申(逐字語意不可弱化)**:family `evals/` ＝**一次性
> pre-registered 設計,非每輪 LLM 判官**。迴圈完成率保證永遠是 T0 硬驗證器(`verify.sh` exit-code)×
> iterate-until-pass×stop-loss,evals **不參與**此判定。它是**周期性/一次性行為品質稽核**(規避機械覆蓋率
> 說謊——0-頁面過關/空測試 PASS/runs-pass-while-components-fail),設計一次、隨後被 T0 或人週期性重跑,
> **不是每輪迭代 turn 都請一次 LLM 判官**(那正是本法否決的反模式:撞訓誡衰減/Goodhart)。
>
> **本地 worked instance**:`families/pinescript-audit/evals/`(cases/holdout/candidates/runner.py/
> baselines/)——本法在 skill-bettor 已有的實作,詳情見該家族目錄,本檔不重抄。
>
> **進階實例指針(未移植,僅供參考)**:antigravity 的 `truth-verify-loop` skill 是這套方法論的
> 全套重量級實作——多 tier worker 交叉驗證、sealed mutation ledger、盲性拓撲(orchestrator/判官皆不可
> 讀播錯真值)、G1-G5 質量閘,背後是一個 12MB/620 檔案的真實量測引擎(`antigravity/truth-verify/`)。
> **本次未移植**:單搬 skill 檔案會變成指向不存在引擎的空指標,真要搬等於要搬整個引擎(規模與
> skill-bettor 現有需求不成比例),而且其歷史 run 記錄是 antigravity 自己的實驗軌跡,對 skill-bettor
> 無意義。若 skill-bettor 未來真的需要「多 tier 交叉驗證 + sealed ledger」這種重量級量測迴圈(例如
> 要對某 family 的判準做大規模盲性驗證),屆時可參考 `/Users/neon/antigravity/.agents/skills/
> truth-verify-loop/`(SKILL.md + `modules/measurement-methodology.md`)當設計參照,重新按 skill-bettor
> 自己的規模建置,而非移植其引擎。

## 設計法三段

### 1. 維度×槓桿矩陣
對每個家族 skill 的輸出面(功能驅動槓桿),列其對應品質維度(正確性/完整性/格式忠實度/邊界覆蓋),輸出
「維度 × 槓桿 → 預期行為斷言」表。維度內容按該家族 domain 重新定義,不照搬其他家族的維度。

### 2. runnable/rubric 兩類切分
- **runnable**(機械可判,exit code 零 LLM)＋**rubric**(語義軸,設計期＋畢業一次性判官)。
- **positive-control selftest(anti-placebo)**:每個 runnable checker 必對 good/hollow fixtures 區分
  (**good=PASS ∧ hollow=FAIL** 才算 checker 活),placebo checker 過不了 selftest → 修 checker 或降級為
  rubric,不放水。

### 3. planted-defect fixtures 設計法
- `cases/`(乾淨基準輸入 + 已知缺陷變體,可按密度分級)
- `holdout/`(畢業段專用,演化迭代期間禁碰)
- `candidates/`(新案例候選,人 admit 後才升 holdout/public)
- ledger(`mutation_id`/`criterion`/`expected_verdict`,對照器不可讀寫)

額外可仿「機制級微妙播錯撰寫者」角色(非機械替換,而是因果倒置/條件偷換一類難檢錯誤)——一份「高推理
模型單次設計 sealed 播錯集」的合約模板。subtle 集正是 runnable 抓不到、必須畢業一次性判官才抓的。

## 覆蓋率不失真度量
產出指標＝**planted-defect 檢出率**(sealed 播錯集抓到幾條 ＝ (runnable 抓到 mechanical + 判官抓到
subtle) / ledger 總數),**非行/函式覆蓋率**。此度量本身可機械判(比對 sealed ledger vs 實測),不需 LLM
二次判斷「測試是否真測到」。

## 4. 語意鑑別坐實法(多 tier 無 skill 對照+判官矩陣;2026-07-11 fold-in,首個 worked instance)

新案例過了 trap-ness(機械)與可解性(有 skill 真跑)兩閘,仍未回答「無 skill 的強模型是不是**語意上**
真的會錯」——機械分差可能全是格式分。坐實法:
1. **多 tier 無 skill fan-out**:同案例 × N 個裸模型(建議含釘死的 eval tier + 上下各一 tier +
   跨家族),單 run、**保留報告**;各 arm 由機械層 subagent(Haiku)並行執行。
2. **Opus fresh 判官矩陣**:逐份報告對照 ground truth 裁「結論方向/機制歸因/修法品質」,findings-only,
   逐字引文可抽查。判官永不 Haiku、永不 agy。
3. **判讀規則**:(a) 機械分齊平但語意分歧 → 案例鑑別的是語意,判官層不可簡化(2026-07-11 實證:
   5 arm 機械分完全齊平,004 語意上 2/5 淪陷);(b) **CLEAN 陷阱(誤報型)是主要鑑別器**——真 bug
   案例方向題太容易,鑑別力在修法品質層,該層要靠 `--judge-cmd` 讓 fix-quality check 進分母;
   (c) 跨家族分數齊平=案例未編碼單一模型 prompt 技巧(雙 harness 交叉驗證的廉價實作)。
4. **操作紅線**:對照 arm 與複核 arm 一律唯讀 dispatch(agy accept-edits 實測會改壞 fixture 副本)。

worked instance(工具+15 份報告+矩陣):`families/pinescript-audit/evals/candidates/_validation/
2026-07-11-semantic-control/`(tools/ 內腳本參數化 FAMILY,可重用;第二個家族用到時再升共用層,
demand-pull 不預先抽象)。

### 產品化
`semantic_pass_rate`＝判官矩陣中「有 skill」報告被判為語意正確的比例。量測時機＝**案例輪替畢業段**
(非每輪機械迭代,判官不進機械內迴圈,承下文 tier 邊界重申)。結果寫回 `FAMILY.yaml` 的
`metrics.semantic_pass_rate` 與 `evals/baselines/` 快照。它是機械 `success_rate` 的**正交第二軌**:
兩軌同升才算真成長,機械分單獨走高是 Goodhart 警訊。

## tier 邊界重申
- **設計**(維度×槓桿定義＋播錯集植入內容)＝**Opus/Fable 5**(一次性,高推理捕捉巧妙缺陷)。
- **執行**(跑 fixture、比對 sealed ledger、輸出檢出率)＝**機械腳本,零 LLM**(runner.py/純 shell)。
- **畢業一次性判官**(semantic rubric)＝**家族層隔離**:Claude-author → fresh zero-context Claude
  subagent(禁 fork),findings-only、admit 永遠人。
- 兩者不可混淆成「evals 每次都要 Opus/Fable5 當判官跑一輪」。

---

*本檔＝evals 設計方法論(裁決類,Opus/Fable 設計);antigravity 原版附帶的 pilot 逐輪判官 finding 史
(R7/R8/M15-M20 案例、engine-driven slice 記錄)是它自己的證成軌跡,不搬——skill-bettor 的等價軌跡
累積在各家族 `changelog/`,見 [retarget-map.md](retarget-map.md)。*
