# Frozen antigravity technical-equivalence prompt baseline

This file preserves the load-bearing legacy prompt bodies byte-for-byte between
the marker lines. It is comparison evidence, not the host-neutral execution
profile. `legacy_compare.py` extracts the corresponding JavaScript template
literals from an explicit source peer and compares the bodies.

<!-- COMPLETENESS_RUBRIC:START -->
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
<!-- COMPLETENESS_RUBRIC:END -->

<!-- PATH_B_REFINE_TEMPLATE:START -->
# Path B 精煉（量規驅動四階段）— 脈絡 → 量規覆蓋稽核+缺口 → 必要時 Path B → 整理已充足

你會收到：①**影片逐字稿**（YouTube 字幕軌，影片實際講了什麼的源頭鐵錨）②**卡片盒原文**（AI Studio 對影片的結構化整理）③該原文的**深度研究報告（DR）**④DR 的**公式**。
**核心目標：對下列固定量規逐維度稽核，且每個維度（無論已覆蓋或未覆蓋）都要給出「可追溯的技術實現等價物」——
優先開源可商用庫（附套件名／repo／授權）；若該維度無公開實現等價物，明確標為 [推論]，並指出可從 AI Engineer
頻道（youtube.com/@aiDotEngineer）哪些其他演講推論其生產環境配置。** 分四階段，不要一上來就套 Path B。

${COMPLETENESS_RUBRIC}

## 階段一：敘事脈絡理解
讀懂 DR 的核心技術觀點與生產環境使用方式，重述主線脈絡與關鍵主張（誰、做什麼、在什麼生產環境怎麼落地）。

## 階段二：量規覆蓋稽核 + 缺口（不套 Path B）
逐一對照上面 14 個量規維度，判定每維度：覆蓋狀態（已覆蓋／部分／未覆蓋，依原文+DR）＋技術實現等價物（實現該維度的開源可商用庫；找不到標 [推論]+可推論來源）。產出：
- **(2a) 覆蓋矩陣（表格）**：維度 | 覆蓋狀態 | 技術實現等價物（開源可商用庫，附 repo） | 來源／[推論]。
- **(2b) 三層損失比對 + 缺口研究題目（編號條列 1. 2. …，可直接當 DR 題目）**：先做三層比對找損失——
  - **逐字稿 → 卡片盒原文**：影片逐字稿講了、但卡片盒原文壓掉/漏掉的（AI Studio 壓縮損失）。
  - **卡片盒原文 → DR**：原文有、但 DR 漏掉/弱化的（DR 損失）。
  凡「未覆蓋」「覆蓋但無可追溯實現等價物」「上述任一層損失」的 → 各成一題。**每題都明確要求：找出實現它的開源可商用庫等價物；若無，對 @aiDotEngineer 其他影片深研以推論生產環境**。

## 階段三：Path B（僅限「需要底層數學原理」的條目）
只有真卡到「底層數學原理」、非拆到守恆量不可時才動。**鐵律**：不用同一套方法論／同一條約分路徑硬套每一條（會**扭曲 Path B 真相**），每條自推專屬鐵錨／槓桿／代價／約分；用不到就明說「無需動用 Path B」。
四步驟：物理鐵錨 → 人為槓桿 → 微觀總代價 → 約分消去 → 該條語意真相。反認知卸載：寫出底層移動了什麼資料／改了什麼約束／付了什麼物理代價。

## 階段四：語意已充足部分的整理
把「已覆蓋且有可追溯實現等價物」的維度**系統化彙整**（核心知識 + 對應開源庫），與階段二缺口對照。

## 輸出
A. 脈絡重述。
B. 量規覆蓋矩陣（每維度 + 技術實現等價物 + 來源/[推論]）＋ 缺口研究題目（編號、可直接當 DR、每題要求實現等價物）。
C. Path B（若有；否則「無需動用 Path B」）。
D. 已充足維度整理（知識 + 開源實現等價物）。
E. 蒸餾可重用提示詞（定位底層原理、反認知卸載，供調整 LLM 語意風格）。
F. **覆蓋率**：有可追溯技術實現等價物的維度數 / 14（[推論] 者另計，如「9/14 有開源庫 + 3/14 [推論]」）。

語氣：冷峻、精準。禁止結尾廢話與跟進選項。
<!-- PATH_B_REFINE_TEMPLATE:END -->

<!-- SINGLE_GAP_QUERY:START -->
基於以下「已知相關資訊」（卡片盒原文 + 前一輪深度研究報告），針對下列**單一主題**做一輪深度研究、建立完整知識體系：補齊已知資訊未涵蓋的深度、機制、實作細節與外部佐證，勿重複已知內容。\n\n**技術實現等價物（必做）**：找出實現此主題的**開源可商用庫**（套件名 + repo 連結 + 授權條款）；若無公開實現等價物，則對 AI Engineer 頻道（youtube.com/@aiDotEngineer）其他演講做深度研究，推論等價的生產環境配置並標為 [推論]。目標：此維度有「可追溯的技術實現」。\n\n## 研究主題\n${topic}\n\n## 已知資訊一：卡片盒原文\n${articleText}\n\n## 已知資訊二：前一輪深度研究報告\n${reportMd}
<!-- SINGLE_GAP_QUERY:END -->

<!-- BATCH_GAP_QUERY:START -->
基於以下「已知相關資訊」（卡片盒原文 + 前一輪深度研究報告），針對下列缺口清單做聚焦深度研究補齊，勿重複已知。\n\n**每一缺口都要給技術實現等價物**：優先**開源可商用庫**（套件名 + repo + 授權）；若無公開實現等價物，對 AI Engineer 頻道（youtube.com/@aiDotEngineer）其他演講深研以推論生產環境配置並標 [推論]。目標：每個維度都有「可追溯的技術實現」。\n\n## 缺口清單\n${gapText}\n\n## 卡片盒原文\n${articleText}\n\n## 前一輪深度研究報告\n${reportMd}
<!-- BATCH_GAP_QUERY:END -->

## Frozen legacy extractor behaviour

`GAP_TOPICS_INPUT` and `GAP_TOPICS_OUTPUT` are one observed input/output pair of
the legacy `parseGapTopics`, captured by executing the JavaScript itself — not
by writing down what the Python rebuild returns. That distinction is the whole
value of the block: a baseline generated from the rebuild would compare the
rebuild against itself and stay green through any drift.

The output is deliberately lossy. The legacy extractor takes the `1.` and
`題目三：` forms and drops the full-width `2）` one, so this pair also pins a
known legacy quirk rather than an idealised behaviour.

<!-- GAP_TOPICS_PROVENANCE:START -->
repo: antigravity
commit: f3f1da95ee8228e03d8f0713d5f479725a30555d
data.js: sha256:ce177bb4752fb2ea2a14e9a406c118fac2e9caac6aed57725052a1344abfb94a
automate.js: sha256:331ea353d5d2f0c437ac1b70f3e08f5fbb96c7e7c35dc049c638c0899ec10917
captured_by: node --input-type=module -e 'import {parseGapTopics} from data.js'
<!-- GAP_TOPICS_PROVENANCE:END -->

<!-- GAP_TOPICS_INPUT:START -->
前言
研究題目清單
1. Durable packet state implementation
2）Retry and rollback production mechanism
題目三：Observability evidence and eval pipeline
<!-- GAP_TOPICS_INPUT:END -->

<!-- GAP_TOPICS_OUTPUT:START -->
["Durable packet state implementation","Observability evidence and eval pipeline"]
<!-- GAP_TOPICS_OUTPUT:END -->
