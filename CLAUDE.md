# CLAUDE.md — bettor-arena（Claude Code 薄派生）

工程 SSOT＝`ARCHITECTURE.md`：放置契約＝§2、鐵律全文＝§3。規則原文只住 canonical 文件，
本檔只保留 Claude Code 專屬入口與強制讀取順序，禁止複述另一份模組化規格。

`CLAUDE.md`／`AGENTS.md` 是 governed projections；修改時必須同步其 `skills-shared` canonical generator/source。
本機 agent-docs gate 缺席時只能回報 `NOT_CHECKED`，不得把 SKIP 說成 checked-clean。

- 啟用：`sh bootstrap.sh`；專案 MCP（`.mcp.json`）與 hook（`.claude/settings.json`）啟用＝人 admit。
- commit 前：走 `ARCHITECTURE.md` §3 的 T0 閘；落新檔前：先查 §2 槽位與 module owner。
- 迭代期間 root passive context 凍結；改本檔後必須開新 Claude Code session 才能驗證。

## Mandatory modular-integration read order

任何涉及 module、大小迴圈、Skills、runtime-env、proof、MCP、browser route、GitHub/Forgejo origin、
外部 project bootstrap 或 Agent Shield integration 的工作，動手前依序讀取：

1. `ARCHITECTURE.md` §1–§3；
2. `docs/architecture/modular-integration-requirements.md`；
3. `docs/agent-runtime-integration.md`；
4. `sh loopctl/loopctl.sh contract`；
5. 目標 module/loop 宣告的 passive context，例如 `AGENTS.md`、`CLAUDE.md`、`PROMPT.md`、`ROUTES.md`、`PLAN.md` 與法則層；缺席必須具名，不得臆造；
6. 最新 proof/control receipt 與 named exclusions。

`docs/architecture/modular-integration-requirements.md` 是 target contract，不是完成宣告。不存在的 `.arena/`
manifest、module-scoped proof v2、project initializer、browser contract v2 等必須回報 `NOT_IMPLEMENTED`；
未跑的 live/provider path 必須回報 `NOT_EXERCISED`。

Claude Code 不得：

- 繞過 `loopctl` 直呼另一 module 的 private entrypoint；
- 以 symlink 當 reproducible execution/release；
- 把 root 與 loop 八大基座壓平成一段任意 MCP prompt；
- 自行 Human Admit、promotion、production rollback、secret rotation 或 permission widening；
- 把 ABSENT、FAIL、NOT_EXERCISED 讀成 PASS。

完成報告欄位與大小迴圈、Context Capsule、stateless MCP、proof/control、Skills/runtime、origins、browser
及 external project 初始化的完整契約，統一讀 `AGENTS.md` 與
`docs/architecture/modular-integration-requirements.md`。
