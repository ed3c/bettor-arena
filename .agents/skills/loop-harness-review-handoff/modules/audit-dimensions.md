# Module: 八大基座已知審計維度 checklist(＋逼未知)

> 屬 [`loop-harness-review-handoff`](../SKILL.md) skill。SKILL.md 6 步程序的第 ③ 步引用本檔。
> **用法**:交接時把下列**已知維度**逐項放進 reviewer 的審計任務,再帶 §逼未知 的 completeness-critic 提問。維度可複用、可依 session-adjustment([handoff-know-why §4](handoff-know-why.md))刪去已答項。
> 每維度指向的設計 SSOT 只**指針**(漂移時以真檔為準):[`harness-spec.md`](../../loop-harness-standard/modules/harness-spec.md)、[`evals-design-method.md`](../../loop-harness-standard/modules/evals-design-method.md)、`ARCHITECTURE.md`、pilot `families/pinescript-audit/`、引擎 `loop_wiki/engine.sh`。
> **與 antigravity 原版的差異(誠實記)**:原版八項裡有兩項對 skill-bettor 不適用,已**移除,不佯裝存在**——見下方「④/⑤ 已移除」。移除理由承 [`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md) 第 1 行、[`harness-wiki/modules/retarget-map.md`](../../harness-wiki/modules/retarget-map.md) 第 2 行——不是本檔重新做的判斷,是同一個架構事實(skill-bettor 恆單 host,無 root `AGENTS.md`)的第三次引用。

## 已知審計維度(known dimensions;逐項掃)

### ① scripts/ vs tests/ 設計目的與最佳結構
skill-bettor 現存**兩種**scripts↔fixtures 配對形態,結構不同:
- **op 沙盒側**(`loop_demo/claude_agy`,本地唯一 canonical 範例):`scripts/<checker>` ↔ `tests/<checker>/fixtures/{good,hollow}/target.*`,1:1,**無 wrapper**——`evals.json` 的 `verify_topology.scripts_tests_pairing` 欄位已載明 wrapper 層(每 checker 一份 `tests/<checker>/verify.sh`)已在移植前的來源狀態就被砍掉,改用 naming-convention glob 探勘直呼 `scripts/<checker>`。
- **family 側**(`families/pinescript-audit`):`skills/repaint-detection/scripts/scan_repaint.py`(production checker 本體)+ `evals/{cases,holdout}/repaint-detection/<case>/{task.md,expect.yaml,fixtures/}`,由 `evals/judge.py` 的三型 check(`program`/`absent`/`llm_judge`)評分——不是 op 沙盒側的 good/hollow 二元 fixture 形。family 側**目前沒有 checker 級 selftest**(只有 agent 級 `evals/mock_agent.py` 正控,驗證的是整條 runner 管線,不是單一 checker 的 good/hollow 區分力)。
- **問**:兩種配對形態不同是否該統一?family 側要不要也建 per-checker 的 good/hollow selftest(仿 op 沙盒側)?`evals.json`/`expect.yaml` 該不該吸收其中一層?**要求 reviewer 給結構建議**。
- 錨:`loop_demo/claude_agy/{scripts/,tests/,evals.json}`、`families/pinescript-audit/{skills/repaint-detection/scripts/,evals/{cases,holdout}/,evals/judge.py}`、[`loop-harness-standard` 基座卡「6 獨立 verifier」](../../loop-harness-standard/SKILL.md)。

### ② 執行效率度量＋instrument
- **具體度量**:收斂輪數 iterations-to-converge／每次收斂 token 成本／wall-clock／planted-defect 檢出率／cache 命中率／driver 失敗率／**Goodhart 逃逸率**(＝機械綠但畢業判官 HOLD 的比例)。**問**:哪些是虛榮指標、哪些真反映效率?
- **現正存在、已知、未修的活案例**(這是本地唯一一個「效率度量已知失真」的真實案例,適合直接拿來當本維度的具體審計對象):`families/pinescript-audit/changelog/2026-07-11.md`「已知問題1:token 口徑失真」記錄 `runner.py` 的 `parse_agent_output` 把跨迭代 `cache_read` 累加,懲罰「多思考幾輪」而非「skill 膨脹」;`ARCHITECTURE.md` §7 鐵律 6 已把「改量測 max-over-iterations」定為修復方向但**尚未實作**。**要求 reviewer 給具體修法**(該從 `runner.py` 哪個函式改、驗證方式)。
- **instrument 現況(誠實記)**:引擎 `loop_wiki/engine.sh` 設計了 `_engine-run/trajectory.log` 軌跡機制,但**本地任何沙盒都還沒真跑產生過這個目錄**(`loop_demo/claude_agy` 的 `RETARGET-NOTE.md` 已明記 dry-run 一節是 antigravity 移植前的舊測試,未在本地重跑)——這件事本身也是一個「已設計未證」的缺口,值得逼未知時提出。
- 錨:`families/pinescript-audit/changelog/2026-07-11.md`、`families/pinescript-audit/evals/runner.py`、`ARCHITECTURE.md` §7 鐵律 6、`loop_wiki/engine.sh`、`loop_demo/RETARGET-NOTE.md`。

### ③ passive-context 的 domain/路由/規則混雜是否稀釋注意力＋最優切分
- 沙盒 `CLAUDE.md`(`loop_wiki/_template/CLAUDE.md`,≤300 行)目前把 domain 知識＋路由指針＋standing rules 混在一起。**問**:這種混雜是否稀釋注意力、傷完成率(對照 [`harness-spec.md` §2❷](../../loop-harness-standard/modules/harness-spec.md) 記的 **91.6%→71.3%** 上下文腐化)?
- **最優切分建議**:domain 知識→family `skills/`、路由/成功判準→`PROMPT.md`、少量鐵律→passive-context。**要求論證 + 含它對 cache 不變量([`harness-spec.md` §5](../../loop-harness-standard/modules/harness-spec.md))的影響**(切分若動搖 prefix 字元級穩定＝cache miss)。
- **新增子問(skill-bettor 自己的角度,非復活已刪的 antigravity 維度)**:skill-bettor 實際有**三層**被動上下文/路由文件——root `CLAUDE.md`(≤300 行)／op 沙盒 `CLAUDE.md`(≤300 行)／family 路由器 `SKILL.md`(`ARCHITECTURE.md` §2「家族內部契約」規定「只放地圖不放知識」)。**問**:三層職責邊界是否清楚?有沒有重疊或該合併的情況?
- 錨:`CLAUDE.md`(root)、`loop_wiki/_template/CLAUDE.md`、`families/pinescript-audit/SKILL.md`、`ARCHITECTURE.md` §2。

### ④ 已移除 — AGENTS.md／CLAUDE.md 差異
skill-bettor 恆為 Claude Code 單 host,**沒有 root `AGENTS.md`**——`ARCHITECTURE.md` §2 目錄圖明寫「⚠️ 暫不建 root AGENTS.md——『dual-runnable 才雙檔』」,§11「為何不」重申。這項審計維度在 antigravity 問的是「雙份常駐上下文檔案是否最優」,skill-bettor 沒有第二份可比較,問題本身不成立,不是簡化掉一個困難問題。
錨:`ARCHITECTURE.md` §2／§11、[`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md) 第 1 行。

### ⑤ 已移除 — N×M(host×driver)覆蓋
skill-bettor 不存在雙 host 翻面(不會有「開這個 repo 的 CLI 換家族」的情境),driver 只在小迴圈側單軸二選一(`claude -p`／`agy`)——[`harness-spec.md` §3](../../loop-harness-standard/modules/harness-spec.md) 已明寫此差異。**提醒**:`ARCHITECTURE.md` §6「N×M 政策」仍殘留「格 3/4(Gemini host)僅設計未證」的措辭,那是**假設性占位**(只有真的要接 Antigravity CLI host 才會啟用),不是本 repo 現存的雙 host 事實——reviewer 讀到 §6 別誤讀成「skill-bettor 其實有 N×M 矩陣需要審」。
錨:`ARCHITECTURE.md` §6、[`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md) 第 1 行、[`harness-wiki/modules/retarget-map.md`](../../harness-wiki/modules/retarget-map.md) 第 2 行。

### ⑥ 效益疊加 vs 冗餘
對每個主要實作(八大基座本身、`engine.sh` 的 iterate/stop-loss/snapshot/trajectory、`_template` 骨架、family `evals/runner.py` G1-G5 閘、holdout 一次性、fresh-subagent 判官隔離(鐵律 2)、cache 五不變量(`harness-spec.md` §5)、tier-dispatch(`ARCHITECTURE.md` §5)、prune 保護(G5)、token 口徑鐵律(§7-6)、祈使任務綁 target 鐵律(§7-7)):具體效益是**疊加(compound)還是重疊/冗餘**?**依價值排序 + 點名可砍的儀式性/冗餘/過度工程**(反膨脹,別客氣)。
worked instance(本地實測疊加效益的唯一真實錨):`families/pinescript-audit/FAMILY.yaml` history ＋ `changelog/2026-07-11.md`(有 skill 1.000 vs 無 skill 0.5834,+41.7pp)。
錨:`ARCHITECTURE.md` §3-§7、`families/pinescript-audit/{FAMILY.yaml,changelog/2026-07-11.md}`。

### ⑦ Goodhart 逃逸＋fold-back 閉環
skill-bettor 沒有 antigravity 那種帶案例代號(R7/R8)的具體踩坑史,但**已經有一個活生生的早期訊號**:`families/pinescript-audit/changelog/2026-07-11.md` 記錄「本次 Δ 主要量測的是介面契約遵循 + 輸出穩定性,不是『找不找得到 bug』」,以及「已知問題 5:案例對強模型太簡單,新案例應往『語意級陷阱』走」。**問**:這是不是一個 Goodhart 早期警訊(機械/格式層對強模型幾乎滿分,但實際 bug-finding 能力未必被量到)?fold-back 閉環(finding→收緊 checker 或案例)在 skill-bettor 目前只有「人在 changelog 記已知問題」這種粗放形式,**尚無**像 antigravity 那種「finding→立即寫新 runnable checker」的機械化 fold-back 循環——這本身是不是一個缺口?機械層永遠關不完 Goodhart → semantic 判官(畢業段)是否永遠必要 backstop?
錨:`families/pinescript-audit/changelog/2026-07-11.md`、[`evals-design-method.md`](../../loop-harness-standard/modules/evals-design-method.md)(Goodhart 提及段)、[`loop-harness-standard` Verify 三層](../../loop-harness-standard/SKILL.md)(semantic 判官 backstop 行)。

### ⑧ 驗證器設計/隔離/tier 經濟學
**問**:驗證器隔離(跨家族天然 vs 同家族 fresh subagent 禁 fork,[`loop-harness-standard` 鐵律 2](../../loop-harness-standard/SKILL.md))是否落地正確?判官經濟學(Opus 做機械＝浪費、低 tier 裁決抓不到 Goodhart)tier 分派(`ARCHITECTURE.md` §5)是否最優?畢業一次性 semantic 判官 vs 機械閘的分工是否清?
**已知落差(逼未知的具體素材)**:`ARCHITECTURE.md` §5 規定 eval agent「Sonnet(釘死在評測指令裡)」,但 `families/pinescript-audit/changelog/2026-07-11.md`「已知問題 2」記錄本次評測實際用的是預設 `claude-fable-5`,**尚未真的釘死**——這是一個「規範已寫但實作未追上」的活缺口。
錨:`ARCHITECTURE.md` §5、`families/pinescript-audit/changelog/2026-07-11.md`、[`loop-harness-standard` 鐵律 2](../../loop-harness-standard/SKILL.md)。

### ⑨ 可選交叉工具:ponytail-audit / ponytail-debt(2026-07-17 新增;互補非取代)
- 全庫過度工程盤點(`/ponytail-audit`,一次性 findings 報告)與 `ponytail:` 註解債帳(`/ponytail-debt`,機械 grep)可作 ⑥「效益疊加 vs 冗餘」的獨立第二視角——反膨脹方向同 ⑥,工具家族不同(插件層 persona 系),findings-only 不改動。
- 錨:`~/.claude/plugins/cache/ponytail/ponytail/4.8.4/skills/{ponytail-audit,ponytail-debt}/SKILL.md`(插件層,隨版本更新;掛載決策=`docs/plans/2026-07-17-agent-native-sdlc-panorama/03-slice-ponytail-mounting.md`)。

## 逼未知(completeness-critic;每次交接必帶)

已知維度掃完只是 floor,不是 ceiling。交接提示詞必令 reviewer 額外回答:

1. **哪個維度沒被審?** ——上列六項之外,還有哪個基座/決策/資料流沒進任何維度的視野。
2. **哪個 claim 沒被驗?** ——建置者宣稱成立、但無確定性錨、reviewer 也未 read-only ground 的 claim,逐條標出。
3. **哪個基座沒 pilot?** ——僅設計未跑過真實例的基座/決策(如 `loop_wiki/engine.sh` 的 `_engine-run/trajectory.log` 機制、family 畢業段/holdout 判官)。
4. **`ARCHITECTURE.md` §10 遷移步驟(D1-D5)裡,哪一項最可能被誤認為已完成?**(warm-up 範例,本次移植時已發現一起:§10 checklist 的 D1「`git init` + 首 commit」顯示**未勾選**,但本地 `git log` 實測已有 3 個 commit——這是一個「文件滯後於實況」的具體漂移案例,reviewer 應比照這個模式找出其他項。)
5. **哪條不變量可能已悄悄漂移?** ——設計 SSOT 宣稱的不變量,對照真檔(`loop_demo/claude_agy`／`families/pinescript-audit`／`loop_wiki/engine.sh`)是否還成立,或已在某次改動中被打破而未同步。

> **紀律**:逼未知的回答同樣受 anchored-claims 約束——「我覺得可能還有 X 沒審」若不能落到具體維度/檔案,標為未錨推測,不算 finding([handoff-know-why §3](handoff-know-why.md))。
