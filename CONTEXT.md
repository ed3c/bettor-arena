# CONTEXT.md — bettor-arena 詞彙表(glossary only,零實作細節)

- **admit**:人對狀態轉移的裁決。本 repo 有三個不可混用的子義:
  - **activation admit** — 武裝一個已落檔但未生效的閘(如 `.staged` hook 改名啟用)。
  - **ratification** — 對已發生的既成事實追認或要求補救(側門、憑證事件)。
  - **removal admit** — 不可逆刪除的放行;唯一沒有回退路徑的一種。
  G 閘全綠永遠只產生**候選**,不自動構成任何一種 admit。
- **Intent-Slice**:commit 訊息裡的意圖錨,形態 `ISSUE-<n>`(ADR 0001);n 解析到本計劃的
  issue tracker。**僅屬小迴圈**——大迴圈沒有切片可指,要求它給一個只會逼出捏造的號碼。
- **protected surface**:閘與 hook 自身的閉包(`.githooks/`、`scripts/gates/`)。改動它**不**單獨
  構成 molecular 要求;要求由**觸發角色**決定(ADR 0001 Amendment 2026-08-07):同一個 commit 同時
  碰 protected surface 與 `loop_wiki/` 才要 Intent-Slice。大迴圈維護閘面走一般 commit 紀律。
- **commit 角色**:誰觸發了這次 commit,決定它受哪套訊息契約。
  - **小迴圈** — 沙盒(`loop_wiki/`)內按切片迭代;碰 protected surface 時必帶 molecular 訊息
    (11 個必填欄位,見 `.githooks/lib/validate_molecular_message.ts` 的 `REQUIRED_FIELDS`)。
  - **大迴圈** — 編排、基礎設施與閘面維護;無切片,一般 commit 訊息。主動帶 molecular block
    時欄位完整性與順序照驗,不因不強制而不檢查。
  判定是機械的且只讀 staged paths(閘 charter 禁讀其他來源),實作＝該檔的 `requiresMolecular()`,
  四條正負對照在它的 `--selftest`。
- **receipt**:機器可驗的執行證據檔;成敗都落帳。歷史 receipt 是凍結證據,不得改寫
  (改寫證據=偽造證據);唯一顯式例外=遷移引擎 `--force-receipt`(重跑意圖必須明示聲明,
  預設碰撞拒寫)。
- **evidence allowlist**:宣告「此檔含歷史絕對路徑屬證據身份」的帳;每條都是 standing debt。
- **candidate**:全部機械閘綠、等待人 admit 的狀態;不是 merge 令。
- **wiki-update request / receipt**:工廠交付成功後確定性落於 `data/wiki-update/` 的 typed 請求
  (三欄 context 分流:fixed=官方 prompt 指針、iteration=確定性 delta、emergent=backlog 落點指針),
  與消化站處理後回鏈 request_id 的執行證據;湧現內容只落 openwiki 原生 backlog,永不進規範模組。
