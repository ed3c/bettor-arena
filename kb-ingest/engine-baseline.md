# Engine baseline — Fable-judge × agy-author 每認證產物成本帳本（**已退役引擎，保留為實測證據**）

> **2026-08-04 狀態**：本表量測的引擎（agy Gemini 作者 × Fable/Opus 判官 × claim contract × T0
> pre-verifier）已隨 L1 回歸 langchain-ai/openwiki 官方程序而退役，**不再新增行**。保留的理由是下方
> §三假設實測判定 是「錨定成本擠壓覆蓋廣度」這個結論的唯一證據，且記錄了 Flash 捏造具體值
> （100k files／50k lines／errno 13）這個失效模式——官方三閘抓不到這一類，人 admit 時要自己獵。
> 退役帳本 → `.agents/skills/repo-wiki-converge/modules/official-port-map.md` §4。

> 目標函數＝**Fable(判官) token / 每認證產物**，質量閘（≥90 protocol）**不可簡化**＝verdicts intact。
> 這張表是「架構優化引擎」立案 gate 的 baseline 計量基座（gate 條件見
> `.agents/skills/antigravity-harness-wiki/modules/token-efficiency-anchors.md` §4）。
> 每個 L1 run 收斂後 additive 加一行；judge verify batches＝判官該 run 手打的驗證指令批數（自報）。
> preverify 欄自 2026-07-04 起由 `agy-pass.sh` 自動記進 converge.log（verify-claims.sh 摘要行）。
> **量測法紀律**：機制變更後的假設檢定只認**同 repo 同 pin A/B 行**（唯一變因＝該機制）；混入 repo 變因的
> real-run 行只累積趨勢、不判假設。run 算不算「新機制下」以**機制 commit 時間 vs run 時間**判——
> 2026-07-04 早上四個 DS round-1（09:52-10:35）即舊合約產物（合約 22:52 才上線），不可當 H1 數據。

| date | repo@pin | rounds(c+r) | round-1 score | final | author secs | judge verify batches | judge-injected errors | preverify | notes |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07-04 | superpowers@v6.1.1 | 1+3 | 68 | 93 | 389 | ~15（手工;pre-verifier 後建,N/A） | 2（.agents 誤判;generated_at 違反合約） | N/A | 新頁＝捏造溫床（round-2 8/8 缺陷全在新頁）;claim-contract＋pre-verifier 於本 run 後上線 |
| 2026-07-05 | superpowers@v6.1.1（A/B 重跑,同 pin 同模型,唯一變因＝claim contract＋T0 pre-verifier） | 1+3（其中 refine-03＝零判官 T0 bounce） | 72 | 92 | 546 | 13（r1=3,r3=6,r4=4;bounce=0） | 0 | r1 FAIL(3 why-untagged)→r2 FAIL(5 quotes)→r3 PASS→r4 PASS | 13 批獵殺**零捏造**、行號抽查 11/11 精準;round-1 覆蓋反縮（3 頁 vs 6）——錨定成本擠壓廣度;作者 +40% 耗時;量測產物不 ingest（repo/superpowers-rerun/,AB-NOTE.md） |

## 三假設實測判定（2026-07-05 A/B run;Path B：數字如實記,不護航）
1. claim contract → round-1 ≥80：**FAIL**（72 vs 68,僅 +4）。機制发现：合約消滅捏造但錨定成本擠壓 round-1 覆蓋（3 頁 vs 6 頁）——分數瓶頸從「髒」換成「窄」,淨提升小。
2. pre-verifier → 判官批次 −60%：**FAIL**（13 vs ~15,僅 −13%）。機制发现：pre-verifier 確實吃掉全部機械層（4 輪 ×38 anchors/31 quotes 機器檢,判官零機械批次）,但判官批次的大頭本來就是覆蓋/機制忠實度/≥90 protocol（4 批）,不隨機械檢查消失。假設把「機械工作量」誤標定為「批次數主成分」。
3. 輪數 ≤1+2：**FAIL**（1+3 打平;其中一輪是零判官 bounce,判官出場 3 次 vs baseline 4 次）。
**真收益（非假設所測但實測到的）**：捏造率 baseline（create 腦補 why＋round-2 8/8 新頁缺陷＋2 判官注入錯）→ 0；bounce 接線實測有效（refine 讀 preverify 報告,5 引文一輪修清）;判官注入錯誤 2→0（gap-list lint 生效）。質量閘從「靠判官獵」左移到「機器擋」的方向正確,但**降本主張在判官批次維度不成立**——下輪優化該瞄的是「錨定成本 vs 覆蓋廣度」的作者側 trade-off（如:create 先廣後錨、或 page-budget 下限）,不是再壓判官。
