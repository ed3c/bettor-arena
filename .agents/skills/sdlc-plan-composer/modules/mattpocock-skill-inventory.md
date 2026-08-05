# Module: mattpocock 全局 atomic skill 盤點(24 個;2026-07-17 逐檔實讀)

> 屬 [`sdlc-plan-composer`](../SKILL.md)。**只映射不重抄**——每 skill 一行:SDLC 落點/任務性質/
> 葉節點(自帶子代理分治,S4 委派即讓其自分治)/人在場(人機對話型,禁入全自動管線)。
> 盤點方法+tier 全景=`docs/plans/2026-07-17-agent-native-sdlc-panorama/`(歷史記錄)。
> 內容以 `~/.claude/skills/<name>/SKILL.md` 磁碟檔為準,本表漂移時以磁碟贏。

| skill | SDLC 落點 | 性質 | 葉 | 人在場 |
|---|---|---|---|---|
| grilling / grill-me / grill-with-docs | S1 | 人機對話(逐題等反饋,共識前禁執行) | - | **是** |
| domain-modeling | S1+維護 | 對話+作者(CONTEXT.md/ADR inline 更新) | - | **是** |
| loop-me | S1(workflow spec) | 對話(grilling 變體) | - | **是** |
| to-prd | S2 | 作者(不訪談,只綜合已知) | - | - |
| to-issues | S2 | 作者+對話(tracer-bullet 切片;quiz 段) | - | quiz 段是 |
| wayfinder | S1+S2 跨 session | 編排(票據狀態機,一 session 一票) | - | - |
| design-an-interface | S3 | 編排+作者(3+ 平行子代理產異構方案) | **葉** | 選型是 |
| codebase-design | S3 | 純參考(深模組詞彙庫) | - | - |
| prototype | S3 | 作者(throwaway,用完即刪) | - | - |
| tdd | S5+執行 | 機械(紅綠)+作者(重構屬 code-review) | - | - |
| implement | S5+執行 | 編排(序列 tdd→code-review) | - | - |
| diagnose(=diagnosing-bugs 近重複,取一) | S5+執行 | 研究+機械(Phase 1 tight/red-capable 迴圈) | - | - |
| code-review | S5+維護 | 編排+判官(Standards/Spec 雙軸並列不合併) | **葉** | - |
| handoff / claude-handoff(同構對,取一) | 執行/維護 | 作者(後者另 spawn 背景 agent) | - | - |
| improve-codebase-architecture | 維護 | 編排(Explore)+判官(deletion test)+對話 | **葉** | 選項後是 |
| research | 全階段支援 | 研究(單一背景 agent,只信 primary source) | - | - |
| triage | S1 入口 | 編排+判官(issue/PR 同一狀態機) | - | 視需要 |
| write-a-skill | meta | 對話+作者 | - | 是 |
| writing-great-skills | 跨階段參考 | 純參考 | - | - |
| zoom-out | 執行(定向) | 對話(單句抽象層上移) | - | 是 |
