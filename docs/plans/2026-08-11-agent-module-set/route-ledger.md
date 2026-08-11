# Route ledger — agent module set

| 輸入 | 路由 | 原因 | 狀態 |
|---|---|---|---|
| 共用 skill 一處更新、多 repo 消費 | `skills-shared` canonical → consumer binding → local symlink / immutable bundle | 內容單份；transport 不冒充 SSOT | portable complete; adapter drift |
| runtime 設定跨 repo 組合 | `runtime-env` catalog → requirements → resolved binding/projections | consumer 只帶 secret-free closure，不帶 sibling path 或值 | portable complete |
| Claude Code 與 Codex CLI 無斷點操作 | bettor `agent-runtime` aggregate gate | host 可發現、投影可驗、workload 可達、live canary 分態 | interface complete; live not exercised |
| 收據與對照組 | `proof_workflow/` | 正控證 traversed bytes；負控證儀器會紅 | control green; same-HEAD proof pending commit |
| 發布 | GitHub PRIVATE remote only | draft PR for Agent audit; no merge | blocked: gh auth invalid |

Grounding：既有碼與本機驗證為 `repo-evidence`；尚未真跑的 Claude/Codex model turn 為
`NOT_EXERCISED`，不能由離線檢查代理成 PASS。
