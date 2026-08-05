# AGENTS.md — bettor-arena 跨 host 工程原則

設計事實 SSOT＝`ARCHITECTURE.md`(放置契約 §2、鐵律 §3);本檔是 Codex 讀取面的薄入口,
禁複述。skill 內容單份住 `.agents/skills/`(host-neutral 家)。

所有 host/agent 遵守:
- 修改前先對映 `ARCHITECTURE.md` §2 槽位;無槽位先改圖。
- 每個綠先證明會紅(selftest/負控);工具缺席走 FATAL,與檢查失敗分流。
- 重複組件禁字面推論等價:判等價=讀碼+真跑;load-bearing 且判錯有代價=重建並列量測。
- commit 前跑 `python3 scripts/gates/check_root_coupling.py`;tracked 檔禁絕對家目錄路徑。
