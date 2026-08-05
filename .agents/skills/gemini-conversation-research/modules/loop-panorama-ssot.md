# Module: 閉環全景圖 + 迴圈判斷邏輯 + 原始提示詞錨（防誤改）

> 屬 [`gemini-conversation-research`](../SKILL.md)。**S0-S9 閉環**的單一真相全景——**資料流歸屬**（誰擁有哪段，別改錯地方）+ **迴圈判斷邏輯**（所有 gate/branch/throw）+ **提示詞錨點索引**（唯一真相留 canonical 檔）。
> **目的**：改任一階段（S0-S9 / Mode A·B）或任一 prompt 前，先在此對照「我要動的東西**歸屬哪裡、會不會斷閉環、會不會把 prompt 簡化壞**」。本檔是 prompt 的**索引 + 禁簡化不變量**，不是 prompt 的家。
> **sibling 全景（worked-example，指針不複製）**：[dr-research-loop/modules/loop-panorama-ssot.md](../../dr-research-loop/modules/loop-panorama-ssot.md)（YouTube→卡片盒→DR 的同紀律全景）。**不同管線、同紀律**；改 gcr 別去改它，反之亦然。

## §1 全景圖 — 資料流 + 歸屬（誰擁有哪段，別改錯地方）

```
Mode A:  URL → [S0 EXTRACT] → [S1 ANALYZE] → [S1.5 PROBE] → [S2 TRIAGE] → [S3 DEEP] → [S4 HARVEST] → [S6 FEEDBACK]
                                                                                  ↘ [S7 GAP] → [S8 MULTI-DR]⟲S2/S3 → [S9 INGEST]
Mode B:  research-context → [S-1 CONTEXT-LOAD] → [S0-ALT CONTEXT-QA] → (併入 S1…)
```

| 階段 | 擁有/產出（artifact + 路徑） | 別改錯地方 |
|------|------|------|
| **S0 EXTRACT** | 抽取的對話文本 `gemini_research/<slug>-conversation.md` | 抽取規則 SSOT 在 [conversation-pipeline.md §S0](conversation-pipeline.md)；Chrome carrier 邊界在 [browser-content-isolation.md](browser-content-isolation.md)；UI selector 真相在外部 source，不在此改 |
| **S1 ANALYZE** | 結構化維度分析（**子代理隔離**） | 隔離是內容外洩防禦（P0）；別把分析拉回主會話 |
| **S1.5 PROBE** | knowledge_gap 維度的 Gemini 追問（≤2 輪） | gate 見 §2；追問構造錨 [first-principles-probe.md](first-principles-probe.md) |
| **S2 TRIAGE** | DR prompt → `/tmp/dr-prompts/<slug>-<ts>.txt`（file-only） | 🔴 DR prompt **只寫檔**，禁 stdout/heredoc/主會話 chat；反幻覺過 [external-verify](../../external-verify/SKILL.md) |
| **S3 DEEP** | Gemini Deep Research 報告 | 狀態機 SSOT = antigravity hardened sequence；extension Chrome 用 repo-root bounded adapter 實作同 gates，CDP fallback 才用 `automate.js runDrOnce` + 外部 extractor |
| **S4 HARVEST** | **雙文件 SSOT**：`.md`（完整+bibliography）+ `.structured.txt` | 兩檔都是 SSOT；bibliography 是 external-verify 的錨；回應必給絕對路徑 |
| **S6 FEEDBACK** | 輕量 `outcome`（feedback_triangle） | 三頂點別少一個；治理路由已拿掉（[retarget-map §2](retarget-map.md)） |
| **S7 GAP** | 知識點覆蓋率比對（**子代理隔離**） | 覆蓋不足才觸 S8（§2）；隔離同 S1 |
| **S8 MULTI-DR** | 額外 DR（複用 S2/S3）→ ⟲ S2/S3 | 這是閉環 loop-back 弧，別當一次性 |
| **S9 INGEST** | 全知識點結構化落地 `<slug>.knowledge.yaml`（**檔案，非 rag-local KG**） | KG 入庫是 northstar-only；antigravity 落地 = 檔案產物 |
| **S-1 / S0-ALT（Mode B）** | research-context 載入 + 主動 Context-QA | Mode B 專屬，錨 [mode-b-contextqa.md](mode-b-contextqa.md) |

## §2 迴圈判斷邏輯（控制流 + 所有 gate/branch/throw）

- **S1.5 PROBE gate**：`knowledge_gap == 0` → **跳過 PROBE**；partial 維度先 Gemini 展開（**max 2 輪**），仍不足才標 `research_gap` 送 S2。追問比 DR 便宜兩個數量級——能在同對話追到就別開 DR。
- **S2 TRIAGE branch**：**只把 research-gap 送 DR**，合併為最少查詢。非 gap 維度不進 DR。
- **S3 DEEP 完成判據（關鍵 gate，曾有假陽性）**：**非** `verifyStarted`（秒級 Start 鈕消失 = 假陽性）。真完成 = 字數 ≥3000 ∧ 0 計劃殘留（`开始研究`/`修改方案`/`只需要几分钟`，認簡繁）∧ `deep-research-source-lists`。投 DR 後 ~8min metadata-only 探針看 `hasPanel` 判卡 plan vs 健康（§5.7）。
- **S3 prompt 形態 gate**：DR prompt 須**單一聚焦段落 ≤~1200 字**；長/多問 → soft-decline 或 `start_button_not_found`。**多問拆 S8**，勿塞一個長 prompt。
- **S7 → S8 loop-back**：覆蓋率不足 → S8 生額外 DR（⟲ S2/S3）→ S9 全落地。閉環迭代弧，**收斂上限 3 輪**。
- **throw 鐵律（絕不把垃圾餵下游）**：抽取/分析/DR 漂移 → **fail-loud 可診斷，不靜默吞**。DR 若卡 plan（`hasPanel:false`）別當報告抽走（會得 871 字垃圾）；分析漂移報不硬吞。
- **browser carrier AUP gate**：主會話只可收 `main_context_projection=metadata_only ∧ raw_content_returned=false ∧ receipt≤4096 chars`；snapshot 可在 bounded adapter runtime 內做 locator grounding，但 snapshot/正文 evaluate/screenshot 一律不得回主會話。

## §3 提示詞錨點索引（唯一真相留 canonical 檔，禁簡化）

> 格式：**錨**（canonical `file §section`）· **角色** · **禁簡化**（砍它會壞什麼）。改 prompt → 改錨指的原檔，回本表更新描述，**不複製內文**。

| Prompt | 錨（canonical） | 角色 | 禁簡化 |
|--------|------|------|--------|
| S1 分析 prompt | [conversation-pipeline.md §S1](conversation-pipeline.md) | 維度解構 + Q&A 邏輯 + 資訊密度標記（子代理隔離） | 砍「資訊密度標記（充分/部分/淺）」→ S1.5/S2 失去 gap 判據 |
| S1.5 追問 prompt | [conversation-pipeline.md §S1.5](conversation-pipeline.md) + [first-principles-probe.md](first-principles-probe.md) | 批量合併 knowledge_gap 維度、同對話追問、鑽到鐵錨 | 砍批量合併 → 多輪零散追問撞 2 輪上限；砍鑽入 → 放水 |
| **S2 DR-prompt 構造** | [conversation-pipeline.md §S2](conversation-pipeline.md) + [external-verify](../../external-verify/SKILL.md) | 背景+方向+輸出要求；過反幻覺 + ≤1200 字單段 | 🔴 砍 **G3「源碼=SSOT」/ G5「禁盲搜、錨 bibliography」** → DR 幻覺入庫；砍 ≤1200 字 → `start_button_not_found` |
| Mode B 啟動 + S0-ALT | [mode-b-contextqa.md](mode-b-contextqa.md) | 主動 Context-QA + 資料主權過濾 | 砍資料主權 → 越界洩漏私有脈絡給外部 Gemini |
| S7 gap-analyze prompt | [conversation-pipeline.md §S7](conversation-pipeline.md) | 知識點覆蓋率比對（子代理隔離） | 砍覆蓋率量化 → S8 loop-back 失去觸發判據 |
| S8 multi-DR prompt | [conversation-pipeline.md §S8](conversation-pipeline.md)（複用 S2） | 對每組 gaps 構造額外 DR | 同 S2（複用，勿各自漂） |
| **DR 抽取 / 完成偵測 prompt·邏輯** | 外部 `gemini-deep-research-extract` + `automate.js` | HTML→turndown 保真 / `[cite:N]` / 完成判據 | 逐字 SSOT 在外部 skill + 引擎，**別在 gcr 留簡化副本** |

## §4 可移植方法論（沿用 antigravity 既有紀律）

1. **確定性脊椎優先，LLM 只做模糊增益**：S0 抽取 / S1·S7·S9 子代理走確定性骨架，prompt 是骨架不是即興。
2. **漂移即 fail-loud（不靜默吞）**：S0 抽取 / Gemini UI drift 漂移要報不要硬吞（§2 throw 鐵律）。
3. **durable 更正勝過手改源**：prompt 缺陷改 **canonical 檔**（§3 錨指的）一處，禁在各 stage 散補（散補 = 雙源漂移）。
4. **技術等價物判斷（grounding-verified）**：DR 落地 claim 須 grounding（external-verify + [judge-loop-chooser](../../judge-loop-chooser/SKILL.md) 三態 grounding，**非字面主義**）。
5. **隔離 + 防禦縱深**：內容 file-based 不進主 context + DR prompt `/tmp` file-only + S1/S7/S9 子代理隔離 = 多層防外洩（antigravity 架構天生，非 hook；[retarget-map §4](retarget-map.md)）。

## §5 DR 吞吐 + 引擎復用（防誤改命門）

> 一整段 DR 自動化血淚（northstar 實證 cc-20260629/0630，在 antigravity 原地更成立——引擎就在本 repo）。改 S3 DR 或想「加速/並行 DR」前先讀。

1. **一個 Gemini 帳號可並發 DR——但要等「脫鉤」才投下一個**。帳號 DR 槽**只在 ~2-3min 初始化期被佔**；研究一脫鉤到 server 端（出現「可以離開頁面/研究已開始」）槽就釋放。**太早投（init 期內）會搶槽餓死前者**；**等 ~210s 過脫鉤再投則兩個都完整**。∴ 一帳號 N 個 DR 可重疊（research 期並發），不需 N 帳號。
2. **DR 瀏覽器 3 段生命週期**：submit（~48s 開瀏覽器）→ **research（~10min 在 Google 伺服器，無本地瀏覽器）** → extract（再開）。「研究期沒看到瀏覽器」是正常，非失敗。
3. **`verifyStarted`（秒級：Start 鈕消失/immersive panel）是『會跑完』的假陽性**。真完成判據 = 字數 ≥3000 ∧ 0 計劃殘留 ∧ `deep-research-source-lists`。盲 sleep + 事後抽取分不出「卡 plan」與「真報告」。
4. **🔴 reliability 命門 = 復用 `automate.js runDrOnce`，不在 gcr 重造**。northstar `submit-dr-prompt.ts` 是 automate.js DR flow 的**滯後複製**（缺 monitor-to-complete + `MAX_DR_ATTEMPTS` retry）→ 間歇卡（實證 0/N）；同 prompt 經 `automate.js`（硬化引擎）**一次跑完 22.8K 字**。**別往 gcr 加 monitor+retry（= 重造）**。改 DR selector 時 current working selectors 在 `automate.js`（source-contrast，AUP 擋 live-probe），dr-research-loop `execution-playbook.md §8` 是失敗模式表。
5. **bridge / 帳號序列約束**：`automate.js` DR 走 :9333 + 那一個帳號 → **不可與 dr-research-loop 影片管線同時跑**（一帳號序列）。跑前 `pgrep -fl automate.js` = 無。turndown ESM：`import` 走 `.cjs.js` build。
6. **runner timeout floor**：DR 一次跑的 timeout **必須 ≥ 引擎報告 poll（30min=1800s）+ extract buffer（≥2100）**。低於此會砍掉**健康的長 DR**（安全/市場綜述真會 >25min）。
7. **verify-started 探針（item 3 操作化）**：投 DR 後 **~8min**（避開引擎 ≤5min 計劃等待）跑 **metadata-only 探針**（puppeteer connect :9333 讀 immersive panel），判別子 = **`hasPanel`**（`deep-research-immersive-panel` 在 = 已啟動）：`true` → 健康讓它跑；`false ∧ planRemnant:true`（卡 plan）→ Start inert → **早砍重跑**。探針只回 `{len, hasPanel, planRemnant}`（body 不進主 context）。**第 2 次仍 inert = 停手改路由**，別 thrash。
8. **DR 報告萃取走並行子代理**：N 份 DR 報告（各 ~20K）**每份一子代理並行**讀 + 萃取，**只回蒸餾結論（findings/錨/grounding-state），raw body 永不進主 context**。external-verify 在子代理內就地做（錨報告 bibliography URL，§3），回 `VERIFIED/UNVERIFIED/FETCH-FAILED` per claim。
9. **CDP fallback（research profile `auth_required` 且拒新登入）**：連使用者**既有、常駐、已登入**的 `:9333` Chrome（`puppeteer-core.connect({browserURL:'http://127.0.0.1:9333'})`，用 antigravity 已裝的 `node_modules/puppeteer-core`）。目標對話 URL 已是該瀏覽器一個開啟分頁 → 零導航、零登入直接讀。**判「兩對話誰較新」的硬錨**：Gemini 側欄 `conversations-list` 倒序（index 0 = 最新），點開 toggle 後 `document.querySelectorAll('a[href*="<id>"]')` 判在場 + 序位。**適用邊界**：只在「使用者已有常駐已登入 CDP 瀏覽器 + 目標對話已開分頁」才是省事路徑；否則走 primary。
