# CONTEXT.md — bettor-arena 詞彙表(glossary only,零實作細節)

- **admit**:人對狀態轉移的裁決。本 repo 有三個不可混用的子義:
  - **activation admit** — 武裝一個已落檔但未生效的閘(如 `.staged` hook 改名啟用)。
  - **ratification** — 對已發生的既成事實追認或要求補救(側門、憑證事件)。
  - **removal admit** — 不可逆刪除的放行;唯一沒有回退路徑的一種。
  G 閘全綠永遠只產生**候選**,不自動構成任何一種 admit。
- **Intent-Slice**:commit 訊息裡的意圖錨,形態 `ISSUE-<n>`(ADR 0001);n 解析到本計劃的
  issue tracker。
- **protected surface**:改動即要求 molecular 訊息的路徑集(閘與 hook 自身的閉包)。
- **receipt**:機器可驗的執行證據檔;成敗都落帳。歷史 receipt 是凍結證據,不得改寫
  (改寫證據=偽造證據);唯一顯式例外=遷移引擎 `--force-receipt`(重跑意圖必須明示聲明,
  預設碰撞拒寫)。
- **evidence allowlist**:宣告「此檔含歷史絕對路徑屬證據身份」的帳;每條都是 standing debt。
- **candidate**:全部機械閘綠、等待人 admit 的狀態;不是 merge 令。
