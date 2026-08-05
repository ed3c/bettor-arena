# decision-report.prompt — 決策面生成提示詞（schema v1）

> 屬 [`html-for-decisions`](../SKILL.md)。本檔＝交給執行 LLM（主 session／subagent／headless）的
> **生成契約**：讓不同家族/op 依同一 schema 物理邊界產出同構的 HTML 決策面。骨架與不變量收斂、
> 內容忠於各自的 md SSOT。
> 設計註記：本任務目標是**形式收斂**，故以真實範例（antigravity 歷史案例，見
> [reference/antigravity-example-decision-dashboard.html](../reference/antigravity-example-decision-dashboard.html)）
> 當 schema 物理邊界是刻意選擇——約束「形」、不約束「內容」。

---

## 提示詞本體（以下整段交給執行 LLM；`{{...}}`＝調用者代入）

你要為一個家族/演化 op 產出**單檔自包含 HTML 決策面**，給人在 LAND-DECISION 節點（見
`ARCHITECTURE.md` §8 人閘清單）做裁決用。

**輸入**：
- md SSOT 所在目錄：`{{SOURCE_DIR}}`（依人閘類型而定：家族 `evals/results`＋`baselines`、沙盒
  `PLAN.md`、`evals/candidates`↔`evals/holdout`、家族 `changelog/`……判定表、人閘、張力都在裡面）
- 快照日期：`{{SNAPSHOT_DATE}}`（YYYY-MM-DD；**不得**自行取系統時間）
- 輸出路徑：`{{OUTPUT_PATH}}`
- 骨架範例：`.claude/skills/html-for-decisions/reference/antigravity-example-decision-dashboard.html`
  （antigravity 歷史案例，只取其 `<style>` 與 DOM 骨架，內容一字不留——banner 已標明非
  skill-bettor 案例）

**角色鐵律（違反即產物無效）**：
1. 你是**投影者不是判定者**：只萃取 md SSOT 已有的判定/裁決/張力，**禁發明、禁改寫結論、禁把
   預判寫成定案**。每個狀態 chip 的依據必須能在 md 裡指到出處。
2. **骨架複用、資料全換**：從骨架範例取 `<style>` 全段與各 section 的 DOM 結構；範例中
   antigravity 自己的判定資料**一字不留**。
3. **自包含**：零外部請求（無 CDN/遠端字型/圖片）；CJK 用系統字型堆疊（骨架已含，勿改）。
4. 頁面必含（checker 機械驗）：`<title>`（≤20 字家族/op 代號式標題）、「**本頁為投影非 SSOT**」
   宣告、`快照 {{SNAPSHOT_DATE}}`、quiz 閘（見 S9）。

**Schema v1 —— section 物理邊界（順序固定；「必」缺料時顯式寫「無/N-A＋原因」，禁靜默省略）**：

| # | section | 必/選 | 欄位（每項的槽） |
|---|---|---|---|
| S0 | masthead | 必 | eyebrow（媒介階＋決策標的名，例如家族名/op 名）、h1（≤18 字）、一段
  thesis（含「本頁為投影非 SSOT」語）、meta 行（快照日期＋家族或 op 狀態＋契約一句） |
| S1 | KPI tiles | 必 | 3–6 塊 `{數字, 標籤, tone: ok/warn/risk/中性}`；數字必須可由 md 數出來 |
| S2 | 已知↔未知四象限 | 必 | KK/KU/UK/UU 各 ≥1 條或顯式 N/A；UU 中的**命門**加粗 |
| S3 | 張力/盲點表 | 必 | 列＝`{張力, 對撞雙方, 預判裁決, 狀態chip}`；狀態只允許：待終審/待人裁/
  已入驗收欄/已裁 |
| S4 | 判定分佈 | 必 | 每本帳一條堆疊 bar（順序固定：採納→借形→待裁→僅記錄→husk）＋
  `<details>` 載荷最重 8–12 條表 `{ID, 項, chip, 注入點}` |
| S5 | LAND-DECISION 佇列 | 必 | 每卡＝`{標題, 狀態chip, 一句說明, src 出處（檔名＋節）}`；已裁的
  卡左邊條轉綠並附裁決記錄出處 |
| S6 | 邊界/風險卡 | 選 | 邊界內/外雙欄＋風險表 `{風險, 錯誤形態, 護欄}` |
| S7 | 落地程度 | 選 | 狀態階梯 bar＋逐項列表 `{名, 能力一句, 狀態chip}`；外部資料（其他家族/
  跨 repo）必標「唯讀投影＋快照日期＋會漂」 |
| S8 | 媒介矩陣 | 選 | 三受眾×落點表 |
| S9 | quiz 閘 | 必 | 5 題 radio 單選＋判卷按鈕＋`全對才 admit` 判準；題目對準**載荷最重的判
  定**（完成率來源/命門/裁決方向這類），禁形式題；答案鍵寫在 inline JS |
| S10 | footer | 必 | 源指針（`{{SOURCE_DIR}}`）＋「本頁為投影非 SSOT」重申 |

**狀態色 tokens（已過 CVD 驗證，禁換色禁重排堆疊順序）**：
採納 `#1A7A4A` → 借形 `#1D6FA8` → 待裁 `#B45309` → 僅記錄 `#7A5CB8` → husk `#B3382C`。
（分段相鄰序＝CVD 命門：紫緊鄰藍會 FAIL，此順序實測 PASS。chip 一律帶文字標籤，不靠色單獨編碼。）

**程序**：
1. 讀 `{{SOURCE_DIR}}` 對應的 md SSOT（見上方輸入說明依節點類型定位），把資料萃取進上表的槽（先
   列槽清單再寫 HTML，缺料的槽標 N/A＋原因）。
2. 複用骨架，逐 section 填入；S4 的 bar 寬度用 `flex:<count>`。
3. 寫出 `{{OUTPUT_PATH}}`（單檔）。
4. 自驗：`python3 .claude/skills/html-for-decisions/scripts/check_decision_html.py
   {{OUTPUT_PATH}}`——exit 0 才算完成；exit 2 按 FAIL 項修復重跑，**禁降級宣稱完成**。
5. 回報：一句話（產出路徑＋checker 結果＋哪些槽 N/A）。**不要**在回報裡複述頁面內容。

---

## 調用備註（不進執行 LLM 的 prompt）
- driver tier：本 prompt 為 Stage-2 形（規則＋槽位＋範例錨）——因目標是**形式收斂**，Sonnet 級
  執行即可（skill-bettor tier-dispatch 對應「演化 author」層，見 `ARCHITECTURE.md` §5）；Opus
  執行時同樣守槽位，不因能力高就自由發揮版式。
- 更新（vN 重生）：同一 prompt、同一 `{{OUTPUT_PATH}}` 覆蓋，`{{SNAPSHOT_DATE}}` 換新＋meta 行標
  vN 與變更觸發事件（人閘裁決/判定表變動）。
- schema 演化：改槽位＝改本檔（schema 版本遞增）＋同步 checker 可機械驗的子集；骨架範例僅在
  schema 變更後由真實案例替換——skill-bettor 一旦有自己的第一份真實 worked instance，應考慮以其
  替換 antigravity 的骨架範例，禁憑空造模板。
