# Module: S9 後下游落地驗證方法論（DR 落地驗證 → 架構設計迭代 → gap 收斂 → prototype）

> 屬 [`gemini-conversation-research`](../SKILL.md)。**S9 之後**的下游閉環：一份 DR 抽取存檔（S4）≠ 可信、≠ 可落地。本模組是把「DR 報告 → 可行度/真實度裁決 → 架構設計 → 落地驗證」定序成可複用程序的 **know-why + how-to**。
> **性質**：methodology/routing fold，**無 automate.js 錨**；反-husk 錨＝下方所有指針都指真檔案（漂移時以那些 skill 現存目錄為準）。
> **鐵律**：全程 **recipe-not-engine**——每段路由 SURFACE 給人 admit，不 auto-chain（同 [unknown-discovery-composer](../../unknown-discovery-composer/SKILL.md) 不變量）。**確定性錨 > LLM 說詞**（見 §1）。
> **可移植**：本方法論對**任何**已採收的 DR 成立（不限 gcr 對話源）；dr-research-loop 影片管線的 DR 同樣適用——此處是 owner，跨管線引用只指針。

---

## 為何需要這一層（S4 harvest 不是終點）

S1-S9 把對話萃取、缺口送 DR、報告存檔。但 **DR 報告是「平滑敘事」，不是鐵錨**（Path B 紀律）：報告的 load-bearing claim 常掛在行銷來源、具名實體可能 post-cutoff 杜撰、中心論點可能與真實實作矛盾。把 DR 當事實直接用 = 幻覺入庫。這一層把 DR 的每條可行度/真實度 claim 約分到**確定性鐵錨**，再據以設計、再據以落地驗證。

## 四段定序程序（每段 SURFACE-gated，人 admit 才續）

> **LIVE ✓（cc-20260711）**：完整 D1→D2 端到端首次真跑——Gemini DR「Maestro 本地 iOS 真機測試」（S0 抽取 16.6K/130 引用/32 來源）→ D1 多模型分工（Opus 編排+判官／Sonnet repo 成熟度／Haiku iOS 事實層 8/8／主 session 親跑 GitHub API+Go proxy+release assets 確定性錨）→ 真實度計分卡（`devicelab-dev` 存在 ✅ 但「100% drop-in」**CONTRADICTED**、3.6x iOS **UNVERIFIED**）→ D2 合成分層架構+等價物矩陣 → 落成 checker-backed skill `ios-realdevice-automation`（**跨 repo** 落 `/Users/neon/ix-agy/.agents/skills/`，`tests/run-all.sh` ALL GREEN）。反-husk 錨＝skill 與研究產物皆真檔案在真路徑（`gemini_research/gcr/b6d196f0f7fb2c7d-SYNTHESIS.md`）。**最高價值揭露＝深研參考實作反證 DR 主張**（官方文檔自列 iOS 真機不支援命令 `setPermissions`/`openNotifications`，正撞落地測試需求）。

### D1 — DR 落地驗證（可行度 / 真實度）
把 DR 的 load-bearing claim 逐條裁決。**多模型分工**（實測有效的分派）：
- **主 session（Opus）= 編排 + 判官**：分派、裁決 CRITICAL claim、彙整。判官永不外包（同 repo-wiki-converge 不變量 1）。
- **子代理分層**：Sonnet（工具/實體存在性+成熟度，fetch repo/docs）、Haiku（well-known 事實層）、agy Gemini Pro/Flash（獨立第二意見，尤其 post-cutoff 實體——Gemini 較新知識）。⚠ **agy 從 Claude Code 非互動 session 內不可靠**（實測 cc-20260711：accept-edits 需 TTY／PTY 包裹不完成寫檔／`--print` 對實質 prompt silent-no-op 且無視 `--model`，5 模式全敗）→ 此時**跳過 agy**，由下方確定性錨補位（機械錨對 post-cutoff 存在性比任何 LLM 第二意見更強，agy 缺席無損正確性）。
- **反幻覺走 [external-verify](../../external-verify/SKILL.md)**：錨 DR 自身 bibliography + primary source，三態 VERIFIED/UNVERIFIED/FETCH-FAILED；存在性 VERIFIED ≠ perf/framing 也對（分開判）。
- **🔴 確定性錨 > LLM grounding**：實體存在性/成熟度**別信任何 LLM 說詞**（實測：agy Flash「7 個全存在」過度討好，6 真 1 張冠李戴）——用**機械閘**硬證。錨工具箱（依實體型別）：repo/tool → **GitHub API**（`repos/<org>/<name>` 的 stargazers/pushed_at/created_at/forks，一次判存在+活躍+成熟度）+ **套件 registry proxy**（如 Go `proxy.golang.org/<mod>/@latest` 判 `go install` 是否真可解析）+ **release assets**（二進位檔名+`.sha256` 驗「單一二進位」宣稱）；一般網站 → HTTP HEAD 狀態碼 + repo `<title>` 內容比對。cutoff-bound 子代理對 post-cutoff 真實體會 false-positive「疑杜撰」→ verify-before-exclude，只永久排除機械雙證的假（**實測 ×2**：gcr S9 的 6 具名實體 6/6 真；cc-20260711 Maestro DR 的 `devicelab-dev` 406★/`Goja` 6990★ 被 S1 子代理疑「vaporware/捏造」、GitHub API 全推翻）。
- **系統性虛標檢查**：查 cite 過載（半數 claim 掛同一來源？該來源真含那些數字嗎？）——證據等級虛標比單條誇大更該扣分。

### D2 — 架構設計合成 + 迭代
把 D1 的**已驗證事實**合成成架構設計（非把 DR 原文當設計）。SYNTHESIS 產物型態：① 真實度計分卡（逐 claim + 證據等級 marketing<vendor<primary）；② 技術等價物矩陣（願景概念→真實 repo，帶存在性+成熟度**+ license 欄**）；③ 分層架構 + 最脆弱三處 + 格式/工具選型矩陣；④ 願景分層（現在可落地 vs 需未來基礎設施）。設計原則從查證反推（例：把「精準」責任從 LLM 移到確定性中介層）。
- **🔴 若下游要商用+不強制開源**：等價物矩陣每元素過**授權/專利合規軸**（code 授權 + **model card 分開查** + codec 專利 + 科技巨頭 permissive 選）→ [external-verify/license-patent-compliance.md](../../external-verify/modules/license-patent-compliance.md)。開源≠可商用零義務；code MIT ≠ model MIT（實測 pyannote model=CC-BY-4.0 gated）；剪輯決定/中介文件工具不 encode→編碼專利在下游 render。

### D3 — 可行度 gap 收斂（地圖≠疆域）
用 [unknown-discovery-composer](../../unknown-discovery-composer/SKILL.md) 四象限（KK/KU/UK/UU）盤點「設計本身的可行度」未知，路由：
- **KU（可讀源收斂）→ [repo-wiki-converge](../../repo-wiki-converge/SKILL.md)（L1 理解 wiki）→ [repo-agent-native](../../repo-agent-native/SKILL.md)（L2 source-anchored 不變量）**。深研真實**參考實作**常**反證 DR 中心論點**（實測：最大真實 AI 剪輯 agent 繞過 DR 主張的交換格式路、直接 render）——這是最高價值的 gap 揭露。階梯 SSOT → [`kb-ingest/mastery-ladder.md`](../../../../kb-ingest/mastery-ladder.md)。
- **UK（做出來才知）→ prototype（見 D4）**；**UU → 盲點 pass**。
- 產物判準 tier → [judge-loop-chooser](../../judge-loop-chooser/SKILL.md)。

### D4 — prototype 端到端驗證（推導 → 實測）
UK/可行度 gap 中「非讀碼可答、要做出來才知」者，跑 **驗證型 prototype** 把 claim 從「推導」升「實測」。程序：
- **一鍵建工作區**：`bash kb-ingest/setup-prototype.sh <plan_name> <repo_name> [pip_pkgs...]` → `prototype/<plan>/<repo>/`（gitignored，對稱 `/repo/`；venv 直接 call interpreter、relocatable）。
- **紀律**（[prototype](../../../../.claude/skills/prototype) 全局 skill）：最小 scope（只答一個 UK,skip polish）、標記 PROTOTYPE、一命令跑、每步 surface state、**混入該擋的壞 case** 實測防護真起作用（實測：驗證中介層真攔 out<in / 超範圍 / 媒體不存在）。
- **實測揭露 nuance**：claim 從概念變硬矩陣（實測：EDL 對多軌非 silently-lossy 而是 loud raise；格式選擇 load-bearing）。
- **誠實留白**：明寫「本 prototype **未**證什麼」（真 app import？LLM 步是否模擬？邊緣 case 留 G5）。
- **封存 ANSWER**：`NOTES.md` 記問題+裁決，absorb 回 SYNTHESIS；artifact **留存作驗證錨**（gitignored＋獨立 git，venv 不入庫）——不是拋棄式，是驗證過的技術實作等價物，刪了「已實測關閉」就失去可重驗鐵錨（2026-07-20 修正，know-why → dr-to-mvp `reference/guiding-prompt.md` §0）。**永不升格 src/**。

## DR→skill 落地程序（D2 已驗架構 → checker-backed skill 的可複用步驟序列）

> D2 產出的是「架構設計」，本節是把它**落成一個有守門測試的 skill** 的步驟序列（actuate 委派 [skill-authoring](../../skill-authoring/SKILL.md)，**非在此重造 skill 規範**）。錨＝cc-20260711 真跑產物 `ios-realdevice-automation`（絕對路徑 `/Users/neon/ix-agy/.agents/skills/ios-realdevice-automation/`，`tests/run-all.sh` 全綠）。

1. **S0 EXTRACT**：DR/對話 URL → 保真 md（metadata-only 進主 context，原文走檔案隔離）。
2. **S1 ANALYZE（子代理）**：抽 `named_entities`（每個具名 repo/工具/版本＝機械查證清單）/ `feasibility_claims` / `tech_equivalents` / `implied_architecture`。
3. **D1 VERIFY**：多模型分工 + 確定性錨 → 真實度計分卡（存在性/成熟度/perf **分開判**；tier 分發權威見 [loop-harness-standard §9❻](../../loop-harness-standard/modules/harness-spec.md)，此處不重抄）。
4. **D2 SYNTHESIZE**：計分卡 + 技術等價物矩陣 + 分層架構（verified-substrate-first）+ 最脆弱三處 + 選型矩陣；設計原則＝**把精準責任從 vendor 敘事移到確定性中介層**。
5. **LAND（actuate → skill-authoring）**：canonical skill 落地——
   - `SKILL.md`（分層架構 + 不變量 + 選型）+ `modules/<name>-know-why.md`（計分卡 + 根因 + 查證血統）。
   - `scripts/<checker>`：**把 D1 的 CONTRADICTED/UNVERIFIED 發現編碼成機械閘**（每條 load-bearing 不變量一個 checker，例：「iOS 不支援命令須標記」「vendor 二進位釘版+sha256」）+ boundary/preflight（唯讀盤點/就緒閘）。
   - `tests/<checker>/fixtures/{good,hollow}` + `evals.json`（覆蓋率＝planted-defect 檢出率，非行覆蓋）。
   - **T0 閘**：`bash tests/run-all.sh` 全綠＝No-Prose-Husk 達標；否則是散文 husk，退回。
6. **【預留】八大基座接入（SURFACE 人 admit，非 auto-chain）**：DR→skill 產物**預設是 standalone skill**。若要當**自癒小迴圈**跑，依 [loop-harness-standard](../../loop-harness-standard/SKILL.md) 八大基座組件卡 + [harness-spec.md §6 skill→小迴圈 recipe](../../loop-harness-standard/modules/harness-spec.md)（8-列映射：SKILL 規則→被動上下文、scripts→checker、tests→fixtures、run.sh 調度、driver 選型、verify 三層）轉沙盒化——**指針不重抄八大基座規範**（防設計飄移，[fold-in](../../fold-in/SKILL.md) 不變量 6）。⚠ 本輪 `ios-realdevice-automation` 的結構（SKILL+modules+scripts↔tests good/hollow+evals）**已與 §6 recipe 同構＝沙盒-ready**；升格與否＝人 admit。**空間預留給後續**：DR→skill 產物自動接八大基座的完整程序（driver 綁定/被動上下文 sizing/verify 三層接線）待首次真跑「skill→小迴圈」再 fold-back 填實，此前只留指針不臆造。
7. **D3/D4**（見上四段程序）：pilot + prototype 把 UK gap 從推導升實測。

## 反模式（實測血淚）
- ❌ 把 DR 報告當事實直接設計/入庫（= 幻覺入庫；DR＝待驗敘事非鐵錨）。
- ❌ 信 LLM（含 Gemini grounding）對實體存在性的說詞（過度討好會 confabulate 看似合理的 repo URL）——用 HTTP 硬證。
- ❌ 深研參考實作時預設它「印證」DR（常是**反證**——真實作繞過 DR 主張的路，這才是最有價值的發現）。
- ❌ 把 prototype 半成品當交付碼／MVP 種子（answer 畢業到 NOTES.md/SYNTHESIS；artifact 留錨**不升格**——留錨≠升格身分，見 dr-to-mvp §0.2）。
- ❌ auto-chain D1→D4（recipe-not-engine；每段人 admit）。
