# Module: fold-in — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`fold-in`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到 skill-bettor、哪些因為
> 架構前提不同被拿掉/拆分,為何不是簡化。northstar → antigravity 那一手是**第三手參照**,本檔不重抄,
> 只在 §5 引註 lineage。

---

## 1. 為何多數內容不能逐字複製——antigravity 原版的 durable home 是單一集中檔案,skill-bettor 沒有

antigravity 原版 `fold-in-know-why.md` 的核心敘事建立在一個前提上:**經驗的 durable home 只有一個
地方**——root `AGENTS.md`「Resolved」帳本。它的 Layer A/B、discrimination gate、boundary-aware 三段,
全都預設「吸收 = 寫進 SKILL.md/Gotchas + 寫進那一個 AGENTS.md」。

skill-bettor **沒有 root `AGENTS.md`**(`ARCHITECTURE.md` §11 明文:dual-runnable 才建雙檔,Gemini
host 未實際開啟本 repo 前建 = 死配置),也**不該**造一個同構的集中帳本頂替它——不是因為偷懶,是因為
skill-bettor 的教訓範疇天生四維(單一家族內容 / 單一家族過程 / 跨家族引擎 / 跨迴圈拓撲 / repo 政策),
硬塞一個檔案會製造「找教訓要線性掃全檔」的新問題。逐字複製「antigravity 的 durable home = AGENTS.md」
這句話會誤導出「skill-bettor 該新建一個等價集中檔案」的錯誤修法——本移植因此**不搬檔案位置這件事本身**,
只搬「教訓要畢業到 durable home、要有顯式禁回退句式」這條方法論,由此重新設計出四路 taxonomy
(設計理由見 [modules/fold-in-know-why.md](fold-in-know-why.md) §3)。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| durable home = root `AGENTS.md`「Resolved」帳本(單一集中式,所有範疇共用一個檔案) | **拆成四路**:單一家族行為/eval 教訓 → `families/<family>/changelog/`;該家族子技能領域知識 → 子技能 `SKILL.md`+`references/`;跨家族 harness 工程教訓 → [`loop-harness-standard`](../../loop-harness-standard/SKILL.md) 自己的 Gotchas/modules;迴圈拓撲事實 → [`harness-wiki`](../../harness-wiki/SKILL.md) 組件卡;repo 級決策 → `ARCHITECTURE.md` §10/§11 | skill-bettor 沒有 root `AGENTS.md`(§1);更根本的是結構前提不同——antigravity 是單一大迴圈套多 stage-skill,skill-bettor 是多家族×多迴圈的資產工場,教訓範疇本來就分四維。這不是簡化,是**教訓的真實歸屬本來就不是一維的**。 |
| actuator = `antigravity-skill-authoring`(判該不該新建,Google Antigravity `.agents/skills/` 格式規範) | actuator = Claude Code 內建 `write-a-skill`(`~/.claude/skills/write-a-skill/`,user-global,非本 repo 內路徑) | **平台真的不同**,不只是換名:antigravity-skill-authoring 是 Google Antigravity CLI skill 格式(其 SKILL.md 明文牆開與 Claude 格式的差異)的裁決者;skill-bettor 是 Claude-Code-only,理應用 Claude Code 自己內建的 skill 撰寫規範。判「新建 vs fold」的**理由**(anti-inflation/grounding,見 fold-in-know-why.md §1)跨平台通用,但「新 skill 怎麼寫」的 frontmatter 慣例不同,兩者不可混用——所以 SKILL.md 正文裡凡是解釋「為何判新建/fold」的段落維持平台無關措辭,只有這一個委派指針換掉。 |
| owner 候選源 = `antigravity-harness-wiki` 組件卡(現況 10+ 列迴圈) | owner 候選源 = `harness-wiki` 組件卡(現況 2 列:演化 op 迴圈/DR proposal 迴圈) | 同一條「讀全景圖當活系統邊界,別憑硬數字」紀律原樣映——這條方法論與迴圈數量無關。skill-bettor 的全景圖現在誠實地薄,是`harness-wiki` 自己 SKILL.md 已明文的現況,不是本 skill 移植時的降級。 |
| 確定性鐵錨 = `automate.js`(單一檔案,整條 DR 管線的執行邏輯都在這裡) | 確定性鐵錨依範疇分兩類 load-bearing 檔案:家族範疇 → 該家族 `evals/runner.py`(或 `judge.py`/掃描腳本);跨家族範疇 → `loop_wiki/engine.sh`(或 `loop_wiki/_template/` 慣例) | antigravity 只有一個「確定性邏輯 SSOT」;skill-bettor 沒有單一等價物——確定性邏輯依 family 分散(每家族自己的 `evals/`),依 harness 引擎則集中在 `engine.sh`。discrimination gate 因此多一步:先問「這是哪個範疇的教訓」才知道查哪個檔案,不像 antigravity 永遠查同一處。 |
| 禁回退鐵錨句式「`<症狀>(根因+live 實測)→ 已解:<修法>。禁回退用 <舊法>。`」,全部記在 `AGENTS.md` | **句式原樣映**,但落點依範疇分散四路(見上);跨家族 harness 範疇沒有獨立 ledger,Gotchas 行本身就是錨句(無「事實面」與「錨句」的物理分離) | 句式本身(症狀→已解→禁回退用)是純方法論,完全可搬;搬不過去的只有「記在哪」。 |
| `antigravity-harness-wiki` 組件卡逐條(`repo-wiki-converge`/`dr-research-loop`/`ds-workflow-loop`/……10+ 條) | 不重複列——`harness-wiki` 已有自己的 `modules/retarget-map.md` 記過一次同一件事(同批移植) | fold-in 只需要**指向** harness-wiki,不需要在自己的 retarget-map 裡再維護一份組件卡副本——維護两份 = 雙圖漂移,正是 fold-in 自己第 6 條不變量要防的事,連在自己的移植帳本裡都不能犯。 |
| Layer A/B(SKILL.md 事實 + `modules/` know-why,「A」的物理位置單一) | Layer A/B 分層邏輯完全相同,但「A」的物理位置依範疇擴散到 changelog 條目/子技能 SKILL.md/Gotchas 行/組件卡列/`ARCHITECTURE.md` §10 條目 | antigravity 的 durable home 集中一個檔案,Layer A 自然就是那個檔案的一行;skill-bettor 因為 durable home 分四路,Layer A 的「物理位置」也跟著分散——但「A=事實不寫 why,B=modules/為何」这条分层规则本身不变,原样映。 |
| 跨迴圈 fold 回同步 `antigravity-harness-wiki`(不變量 6) | 跨迴圈 fold 回同步 `harness-wiki`(不變量 6) | **原樣映**——這條與 durable-home 拆分或 host 數量都無關,是純粹「地圖需要跟着真實系統同步」的方法論。 |
| 「動到大小迴圈八大基座」核對 `loop-harness-standard` 的 **N×M host×driver 全景圖**＋設計規範差異表 | 核對 `loop-harness-standard` 的**八大基座組件卡**＋防退化鐵律(N×M 矩陣已被該 skill 自己的 `modules/retarget-map.md` 整個拿掉) | skill-bettor 恆單 host,`loop-harness-standard` 移植時已記錄「2×2 host×driver 矩陣…**拿掉,降為單軸 driver 選型**」。fold-in 引用它時必須跟著拿掉那個維度,不能自己留一句指向已不存在維度的引用——這是「retarget 要順著已完成的移植鏈走,不能自己开一个分岔」的具體例子。 |
| Not For:「跑管線／診斷管線失敗」→ `dr-research-loop` | Not For:「建/驅動一條新演化 op 沙盒、選 driver、分層 verify」→ [`loop-harness-standard`](../../loop-harness-standard/SKILL.md) | **誠實標注不完全對應**:skill-bettor 沒有 `dr-research-loop` 或 `automate.js` 那種「單一固定管線」的等價物(background 已確認)。loop-harness-standard 是「建/驅動任何一條迴圈的工程規範」,性質上更接近方法論而非「跑一條管線」——選它是因為它是現存最貼近的落點,不是因為兩者職能真的 1:1。 |
| Not For:「查證外部 claim」→ `external-verify` | Not For:「查證外部 claim」→ [`external-verify`](../../external-verify/SKILL.md) | **原樣映,名稱不變**——external-verify 與本次同批移植,寫本檔時已在磁碟落地(`.claude/skills/external-verify/SKILL.md` 已存在),非死指針。 |

## 3. 拿掉的東西不是「簡化」,而是「結構前提不同」或「無對應基座」

- **能一對一映的映**:Layer A/B 分層邏輯、禁回退錨句式、owner 候選讀全景圖(不憑硬數字)的紀律、
  跨迴圈 fold 回同步全景圖(不變量 6)、technical-equivalent 判斷通則(fold-in-know-why.md §6)。
- **架構前提不同、真拆分**:集中式 `AGENTS.md` Resolved → 四路 taxonomy;單一 `automate.js` 鐵錨 →
  依範疇兩類檔案——skill-bettor 多家族×多迴圈的事實,不是能力縮水。
- **平台真不同、真換掉**:actuator(`antigravity-skill-authoring` → 內建 `write-a-skill`)——連格式
  規範本身都不同,不是換名。
- **不完全對應、誠實標注**:`dr-research-loop` 的 Not-For 位置换成 `loop-harness-standard`,但職能
  只是「最貼近」不是「同構」——見上表最後一列。

## 4. 判別「retarget 成立」的鐵錨(逐條 `test -e` 已驗證,見下)

以下路徑在寫作本檔時已用 `test -e` / `grep` 現場驗證存在,而非憑記憶假設:

- `harness-wiki` 組件卡與其 `modules/retarget-map.md` ——磁碟已驗證。
- `loop-harness-standard` 的 `SKILL.md`(含 `## Gotchas` 標題行)、`modules/harness-spec.md`、
  `modules/evals-design-method.md` ——磁碟已驗證。
- `families/pinescript-audit/changelog/2026-07-11.md`、`families/pinescript-audit/SKILL.md`、
  `families/pinescript-audit/skills/repaint-detection/{SKILL.md,references/security-function-patterns.md}`
  ——磁碟已驗證,四路 taxonomy 裡「家族範疇」與「子技能範疇」两条路的具體格式依據就是這些真檔案。
- `loop_wiki/engine.sh`、`loop_wiki/_template/`、`loop_demo/claude_agy` ——磁碟已驗證。
- `ARCHITECTURE.md` §10(行 152,「## 10. 遷移步驟」)與 §11(行 169,「## 11. 為何不」)——`grep`
  已驗證確切標題與行號,非憑印象引用。
- root `AGENTS.md` ——`test -e` 已驗證**確實不存在**於 skill-bettor(與 antigravity 的
  `/Users/neon/antigravity/AGENTS.md` 對照,後者確實存在且含 6 處「禁回退用」)。
- Claude Code 內建 `write-a-skill` ——`/Users/neon/.claude/skills/write-a-skill/SKILL.md` 已驗證
  存在(user-global,非本 repo 內)。
- 同批移植手足 skill:寫作本檔時 `unknown-discovery-composer`／`sdlc-plan-composer`／
  `judge-loop-chooser`／`html-for-decisions`／`external-verify` 均已在磁碟落地;僅
  `loop-harness-review-handoff` 尚未落地(本檔未引用它,故不構成死指針風險)。

若哪天有人想把 skill-bettor 的四路 durable home 收斂回單一集中檔案(例如真的建了 root `AGENTS.md`),
那不是「一鍵改名」——要重新評估四路 taxonomy 的分艙理由(§1)是否仍成立,而不是機械地把四個位置的
內容搬進一個新檔案。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/fold-in/`(SKILL.md +
  `modules/fold-in-know-why.md`)。
- northstar 源(第三手,不重抄本檔):antigravity `modules/fold-in-know-why.md` §5 的
  northstar→antigravity 映射表,原始出處 `/Users/neon/northstar/.claude/commands/fold-in.md`。
  本檔只在此引註為 upstream lineage,完整映射細節留在 antigravity 的檔案裡,不三手複製。
- skill-bettor 既有同構:`ARCHITECTURE.md`(§10/§11)、`loop-harness-standard`/`harness-wiki`
  (同批移植,retarget-map 已各自記過一次,本檔不重複)、`families/pinescript-audit/changelog/`
  (四路 taxonomy 的第一個實例依據)。
