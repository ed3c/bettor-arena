# AGENTS.md — bettor-arena(Codex 讀取面薄入口)

工程 SSOT＝`ARCHITECTURE.md`:放置契約=§2、鐵律全文=§3。規則原文只住那裡,本檔禁複述,
只留 Codex/跨 host 專屬入口:

- 啟用:`sh bootstrap.sh`(冪等;doctor+相對 hooksPath)。
- skill 內容單份住 `.agents/skills/`(host-neutral 家;.claude/skills 全 symlink 指向它)。
- `.codex/config.toml` 僅可攜 MCP 宣告;host 段(permissions/network/sockets)人補後才可信。
- commit 前:§3 鐵律 2 的 T0 閘;落新檔前:§2 槽位對映。
