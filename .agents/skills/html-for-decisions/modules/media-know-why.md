# Module: html-for-decisions — know-why ＋ retarget 脈絡

> 屬 [`html-for-decisions`](../SKILL.md)。SKILL.md 有確定性程序＋不變量；本檔＝為何這樣、lineage、
> viz-sync/solo-pipeline 一路 retarget 到 skill-bettor 的脈絡。

## 1. 三受眾媒介矩陣（為何 HTML 只給決策節點）

| 受眾 | 媒介 | 資訊特徵 | skill-bettor 落點 |
|---|---|---|---|
| 代理自身 | Markdown for itself | 帳本/迭代軌跡/implementation-notes | 沙盒 `PLAN.md`（STATUS+迭代軌跡）、`anti/` 失敗軌跡 |
| 人類協作者 | Markdown for you | 表格/代碼塊，快速掃描 | 家族 `README.md`、`changelog/`、`shared/conventions.md` |
| 關鍵決策節點 | **HTML for decisions** | 富交互＋quiz，高決策密度 | 決策儀表板、畢業 quiz、`ARCHITECTURE.md` §8 人閘佇列的視覺化 |

**HTML 稅**：HTML 產出/維護成本高於 Markdown 一個量級。只有「等人裁」的節點，決策密度才值回這個
稅——過程報告用 HTML＝把稅付在沒有決策的地方。這是判準不是偏好：頁面目的是「裁」→ HTML；是
「讀」→ Markdown。

> 這張三受眾矩陣的命名（代理自身/人類協作者/關鍵決策節點）源自 antigravity 自己的卡片盒系統編號
> （其 SKILL.md 稱之為「06 §A C03/C04 卡」）。skill-bettor 沒有這套卡目——本檔只承接**概念**（三
> 受眾、決策密度判準），不承接編號引用，避免指向一個 skill-bettor 查無此卡的死指針。

## 2. 為何 md＝源、HTML＝投影（Markdown-as-Code 自反）

markdown 檔是系統源代碼、其餘皆生成物——這個形套用到決策面：判定/裁決的 SSOT 永遠在對應的 md
檔（依 `ARCHITECTURE.md` §8 節點類型而定：沙盒 `PLAN.md`、家族 `changelog/`、`evals/baselines`
等），HTML 是事件式重生的投影。反向（在 HTML 側改判定）＝製造會漂的第二真相——與本地
[harness-wiki](../../harness-wiki/SKILL.md)「只指針不抄」防的是同一種雙圖漂移。頁面自帶「非
SSOT」宣告＋快照日期＝投影的誠實標記。

**dogfood 錨——誠實標記為 antigravity 自己的歷史，非 skill-bettor 的**：antigravity 側曾有一輪
真實 dogfood（2026-07-09，`loop-harness-panorama` 儀表板 v0 產出 → 人裁 5 項 → 裁決先回填計劃 md
→ 再改 HTML 佇列狀態為 v0.1），驗證了「先改 md 源、再重生 HTML 投影」這條順序可以真的走一輪不出
錯。**skill-bettor 目前沒有這一輪的自己版本**——本 skill 移植過來的是「這個機制曾被驗證過」的信
心，不是「skill-bettor 已經驗證過」的事實。skill-bettor 自己第一次真用本 skill 走完一輪人裁回填,
才是本地的吸收成立錨。

## 3. quiz 閘為何綁在決策面上

quiz 測「人」的理解就緒度——merge/admit 前全對才過，強制人腦留在知識環內。放進決策面而非獨立文
件，是因為兩者服務同一個節點：裁決需要理解，理解閘與裁決佇列同頁＝一次交互完成。題庫對準載荷最
重的判定（完成率來源、驗證器隔離命門、判官分頻這類），形式題＝假閘。

## 4. retarget 已經走過兩手——本檔不重複第一手

這個機制的設計曾經歷**兩次 retarget**：第一手是 antigravity 自己從 northstar 借
`viz-sync`/`solo-pipeline` 的機制、拿掉 live-draw-mcp daemon、拿掉 lavish-axi long-poll 標註、
保留「approve 永遠人」「agent 親寫 HTML 無轉換器」——這份逐機制映射表記在 antigravity 自己的
`html-for-decisions/modules/media-know-why.md` §4,是 antigravity 自己的歷史決策記錄，**不在本
檔重複**（重複＝與本地 [harness-wiki](../../harness-wiki/SKILL.md) 已立的先例衝突：northstar 對
比記錄屬上游自己的沿革，不隨每一手移植複製一次）。

第二手（antigravity → skill-bettor，本次移植）的結論可以直接推：skill-bettor 比 antigravity 更
沒有這些基座（同樣無 live-draw-mcp、同樣無 lavish-axi），所以第一手「拿掉」的結論原樣成立、無需
重新論證。真正屬於**這一手**的移植決策（哪些機制映到 skill-bettor 哪裡、卡片盒編號怎麼處理、兩份
reference HTML 各自留不留）記在 [modules/retarget-map.md](retarget-map.md)，不在本檔重複。

## 5. 與「計劃 slice」分工——skill-bettor 沒有對應概念，誠實記錄

antigravity 原版此處分工說明引用它自己的計劃 slice 檔（`docs/plans/2026-07-09-loop-harness-
panorama/10-media-and-boundary.md`）,是「plan-scoped 判定 vs durable 操作規則」的分工示範。
skill-bettor **沒有** `docs/plans/` 這種計劃/slice 目錄慣例（見 `ARCHITECTURE.md`，遷移步驟走的
是 `families/`＋`loop_wiki/evolve-<family>-<op>/`，不是計劃 slice 制）。本 skill 仍然是媒介操作
規則的 durable home；plan-scoped 的判定（某次具體 merge admit 裁了什麼）落在對應沙盒的 `PLAN.md`
或家族 `changelog/`，两者不是同一種文件家族，不需要互相指針複誦。等 skill-bettor 有了自己第一個
真實跑完的 LAND-DECISION HTML worked instance,那份紀錄該指回本檔,而不是本檔預先虛構一個尚不存
在的分工範例。

## 6. 觀測面家譜與機器帳 pattern(2026-07-11 fold-in;首個 worked instance 同日誕生)

觀測面從一型長成三型,層級對應受眾:
| 型 | 腳本 | 源 | 受眾 |
|---|---|---|---|
| session 層 | context_trace.py | session JSONL | 工程師(token 經濟/D7 oracle) |
| 家族層 | family_metrics_board.py | FAMILY.yaml+baselines+results+registry | operator(資產健康) |
| 產品層 | product_board.py | product/state.json+FAMILY.yaml | 產品管理(階段/經濟/規則) |

三型共同紀律(=觀測面的定義,缺一即漂向決策面):零 LLM 確定性渲染、無 quiz 機件、非 SSOT 宣告、
`--as-of` 外部傳入禁系統時間、`--selftest` 合成正控。

**機器帳 pattern**(product_board 首用):板子要投影「規格」(決策規則/心跳/方案)時,不解析散文 md
——把規格的機器可讀形收進 `state.json`(SSOT 仍是 PRODUCT.md,state.json=數值與規則的投影層),
板子只讀 JSON。理由:md 解析脆(改寫散文=板子壞),雙檔分工=散文給人、JSON 給板,兩者同步由
publish 紀律保證(改 PRODUCT.md 規則必同步 state.json,commit 同批)。

**禁投影假數的 why**:產品唯一賣點=「eval 曲線不可造假」;後台若為版面美觀補假訂閱數,
等於在自己家裡先破了這條——null→「未上線(N/A)」不是 UI 缺陷,是證據鏈紀律在投影端的延伸。

**決策面 vN 事件式重生首例**(v1→v2,觸發=心跳敘事人核):實證了「人裁→先回寫 md(PRODUCT.md)
→再重生 HTML」的順序可運轉;重生成本≈編輯 3 個 section+checker 一次,遠低於重寫,
支持「事件式非定期」的更新策略(SKILL.md 程序 7)。

## Sources / Lineage
- antigravity 源：`.agents/skills/html-for-decisions/SKILL.md` + `modules/media-know-why.md`
  （2026-07-11 唯讀快照；活 repo 會漂，引用時回讀）。
- antigravity 的第一手 retarget（northstar `viz-sync`/`solo-pipeline` → antigravity）：見
  antigravity 自己的 `modules/media-know-why.md` §4，**本檔不重複該表**，只承接其結論。
- dogfood：antigravity `reference/loop-panorama-decisions.html`（v0.1）＋人裁回填記錄——**
  antigravity 自己的歷史**，skill-bettor 保留骨架研讀副本見
  [reference/antigravity-example-decision-dashboard.html](../reference/antigravity-example-decision-dashboard.html)。
- 本次移植帳本：[modules/retarget-map.md](retarget-map.md)。
