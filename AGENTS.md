# AGENTS.md — bettor-arena(Codex 讀取面薄入口)

工程 SSOT＝`ARCHITECTURE.md`:放置契約=§2、鐵律全文=§3。規則原文只住那裡,本檔禁複述,
只留 Codex/跨 host 專屬入口:

- 啟用:`sh bootstrap.sh`(冪等;doctor+相對 hooksPath)。
- skill 內容單份住 `.agents/skills/`(host-neutral 家;.claude/skills 全 symlink 指向它)。
- `.codex/config.toml` 僅可攜 MCP 宣告;host 段(permissions/network/sockets)人補後才可信。
- commit 前:§3 鐵律 2 的 T0 閘;落新檔前:§2 槽位對映。

---

## 工程法則的實證歸屬 (Rule → Evidence Routing)

全局 `~/.claude/CLAUDE.md` 的工程法則不直接指向迴圈目錄——法則層綁死在某個 repo 的
目錄結構上，迴圈改名即斷。**本節是那一跳的落點**：法則指到這裡，這裡指到擁有實證的 Harness。

骨架、各節硬性要求與零網路註冊檢查 → `ix-agy/.agents/modules/agents-md-template.md`

| 法則主題 | 實證 Harness |
|---|---|
| §4 觀測：綠燈值多少看抵達；兩種獨立抵達才 settled | `loop_wiki/evolve-perfect-seed-repo-factory/modules/eight-base-laws.md` 抵達分層表——訊號：想把 verify 綠讀成 seed 可升級；動作：查表，PROD 抵達（Production Use axis）未接即停在人閘；為何：SANDBOX 綠只證合成輸入，判準本身擋升級。 |
| §4 觀測：量測工具該紅的時候真的會紅 | 同檔 B3 段——訊號：只有正控綠就想信儀器；動作：跑 `selftest.sh` hollow 負控＋`portability.sh` 雙負控（planted-defect 真跑）；為何：工具的綠也是單一抵達的宣稱。 |
| §3 閘門：缺席≠否、狀態碼傳到底 | 同檔 B2 段——訊號：多段執行想彙報單一結果；動作：照 `trigger.sh` 分記四段 exit、早段非零→後段 `not_run`；為何：缺席偽裝成 fail／pass 都會扭曲路由。 |
| §2 構形：模組不向上依賴根目錄；搬一次真跑才算解耦 | 同檔 B5 段——訊號：想把「在原地會跑」讀成「這個模組搬得走」；動作：跑 `portability.sh`（`git archive HEAD:<prefix>` 抽出、`bun install --frozen-lockfile`、跑抽出樹自己的 `verify.sh`，含「裝之前必須先紅」負控），並查該檔尾註標記的未蓋控制面；為何：上層 `node_modules`／上層設定／寫死深度這類向上解析在原地永遠綠，只有離開根才爆。 |
| §7 邊界：共享 working tree 的暫存區是公共狀態 | 同檔 §7 段——訊號：多 session 同樹且自己的 commit 剛被閘門拒絕；動作：先把自己的檔 `git restore --staged`，排查完把 stage 與 commit 綁在同一條命令；為何：失敗的 commit 不回滾 `git add`，留在暫存區的檔會被別人的 commit 掃走（2026-08-08 實證 8628397）。 |
| §6 落帳：推翻是時間線＋note 必填 | 同檔 B8 段——訊號：一列軌跡被後來證偽；動作：append note 記「當初為什麼會信」，禁改寫；為何：防重蹈的是誤信原因，不是結論。 |

<!-- 自動偵測到的 Harness（1 個），已逐個確認：loop_wiki/evolve-perfect-seed-repo-factory 擁有上列法則實證。 -->
