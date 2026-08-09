# Technical-equivalence research profile

This is the host-neutral canonical profile. The historical source peer owns
`data.js` (`COMPLETENESS_RUBRIC`, `PATH_B_REFINE_TEMPLATE`) plus the
single/batch gap queries in `automate.js`.
Card-box v6.6 and browser/login mechanics are explicitly outside this profile.

## 完整度量規（固定 14 維度；每維度都必須有「可追溯的技術實現等價物」）

生產環境維度：

- P1 部署拓撲（架構／服務邊界／單機 vs 分散式）
- P2 規模（QPS／並發／資料量／Token 吞吐）
- P3 延遲與 SLO（p50/p99／可用性）
- P4 故障模式與回滾（失敗點／重試／熔斷／降級）
- P5 成本與運算開銷（$/單位、硬體、FinOps）
- P6 工具鏈與框架（runtime／orchestration／SDK）
- P7 資料流與儲存（pipeline／DB／快取／向量庫）
- P8 安全與權限邊界（authn/z、沙盒、密鑰、合規）
- P9 可觀測性（監控／日誌／追蹤／eval）

技術觀點維度：

- V1 核心主張與底層機制（how it works）
- V2 前提假設與適用邊界
- V3 反例／失敗模式／Pre-mortem
- V4 與競品／替代方案對比
- V5 實證／數據佐證（primary source）

## Path B 四階段

1. 敘事脈絡理解：重述核心技術觀點、主張與生產環境落地方式。
2. 量規覆蓋稽核與缺口：逐維度輸出覆蓋狀態、實作等價物、來源／`[推論]`；比較逐字稿→卡片盒→DR 的語意損失，缺口編成可直接研究的題目。
3. Path B：只有卡到底層數學原理時，依物理鐵錨→人為槓桿→微觀總代價→約分消去；否則明示「無需動用 Path B」。
4. 已充足整理：彙整已覆蓋且有可追溯實作等價物的維度，與缺口對照。

## Grounding contract

- `candidate`：repo、README、license 或來源存在，但尚未完成讀碼與真實 probe。
- `technical_equivalent`：已審計實際代碼並真跑；load-bearing、等價性不確定或判錯有代價時，另有重建替代版與並列量測。
- `[推論]`：沒有公開可驗實作；清楚標示推理鏈與可證偽條件。
- 每個 repo 必須帶可點 URL、精確 commit、SPDX、程式碼錨與 probe receipt。名稱相似不構成等價證據。

## 單題 Gap Deep Research（精確保留的必要句）

基於「已知相關資訊」（原始材料 + 前一輪深度研究報告），針對下列**單一主題**做一輪深度研究、建立完整知識體系：補齊已知資訊未涵蓋的深度、機制、實作細節與外部佐證，勿重複已知內容。

**技術實現等價物（必做）**：找出實現此主題的**開源可商用庫**（套件名 + repo 連結 + 授權條款）；若無公開實現等價物，則推論等價的生產環境配置並標為 `[推論]`。目標：此維度有「可追溯的技術實現」。

## 整批 Gap fallback（精確保留的必要句）

針對缺口清單做聚焦深度研究補齊，勿重複已知。**每一缺口都要給技術實現等價物**：優先開源可商用庫（套件名 + repo + 授權）；若無公開實現等價物，推論生產環境配置並標 `[推論]`。最多六題；超出部分必須記錄為 truncated，不得靜默遺失。

## Output contract

輸出 claim／P-V 維度／候選等價物矩陣、來源 URL、repo URL、SPDX、code anchors、probe/rebuild 狀態、gap topics、截斷帳與 semantic-loss ledger。來源不足時降級，不得補寫不存在的證據。

報告末尾必須附 fenced `json` block，根物件為
`technical_equivalence_candidates`。公開候選須帶 candidate_id、claim、
repo_url、精確 commit、SPDX、source_urls、code_anchors、三個 rebuild-trigger
布林值與 inference:false；研究階段的 code_audit/probe 必須明示
`not_exercised`，不得假造本機 receipt。沒有公開實作時仍須輸出至少一個
inference:true 候選及可證偽條件，空陣列是 declared verification failure。
