# ARCHITECTURE.md — bettor-arena 工程 SSOT

> 遷移自 ts-skill-bettor 的四子樹新家。設計事實單一權威源＝本檔;host 被動上下文檔
> (CLAUDE.md/AGENTS.md)是本檔的 tier 派生,禁複述。PRD 與切片帳在來源 repo 的
> issue tracker(#2–#13)。

## §1 可證偽的模組化定義

模組化 ＝ 零入向代碼引用 ∧ 自有 verify ∧ 自有 selftest ∧ 隔離環境 relocation 綠。
「完美」不作狀態名;只有版本化、帶反例、可演進。每個綠都必須先有對應的紅被造出來過。

## §2 放置契約(root 層槽位;無槽位=先改本圖再落檔,隨 commit 人 admit)

```
bettor-arena/
├── AGENTS.md          # 跨 host 工程原則(Codex 官方讀取面;內容 SSOT 指針)
├── CLAUDE.md          # Claude-tier 薄派生(tight 入口,禁複述)
├── ARCHITECTURE.md    # 本檔=工程 SSOT+放置契約權威源
├── bootstrap.sh       # 冪等啟用:相對 hooksPath+環境 doctor(exit 64=FATAL)
├── .githooks/         # 大迴圈 git hooks(唯一跨 host 閘層;S7/S8 落 pre-commit/commit-msg)
├── .claude/           # Claude Code host 配置(版控 settings;skills 全 symlink → .agents/skills)
├── .codex/            # Codex host 配置(僅可攜 MCP 宣告;host 段人補)
├── .agents/
│   └── skills/        # skill 內容 SSOT(host-neutral 單份;S5 落地)
├── kb-ingest/         # repo-wiki 模組(openwiki/=上游逐字;port/=本地執行層;S4 落地)
├── loop_wiki/
│   └── evolve-perfect-seed-repo-factory/   # 工廠沙盒(自足 TS;trigger.sh 入口;S3 落地)
├── mcp/               # MCP adapter 層(context-pack+production 引擎;S10 落地)
├── scripts/
│   ├── gates/         # repo 級防禦腳本(零 LLM):check_root_coupling.py+allowlist 帳
│   └── migrate/       # 遷移引擎 v2(migrate_seed.py;dry-run 預設/--apply/--stats/--selftest;S2 落地)
├── tests/             # repo 級測試(打 gate CLI exit code 接縫)
├── data/              # 機器帳與 receipt 落點(遷移 stats/煙測 receipt)
│   └── migration/     # manifest.json(v2;repo-relative 唯一)+apply receipt(last-migration-report.json,執行期生)
└── docs/              # 計劃/交接文件(非模組知識)
```

## §3 鐵律(承 PRD 全部裁決,只列最高頻)

1. 大迴圈 gate 掛 host(git hooks/Claude settings;Codex 不依賴實驗 hooks),小迴圈 gate
   全是 CLI+exit code+receipt;縫合面只有 exit code 與 receipt,單向依賴 host→artifact。
2. tracked 檔禁絕對家目錄路徑;歷史證據入 allowlist 帳,不改寫。T0 閘=
   `python3 scripts/gates/check_root_coupling.py`。
3. root 被動上下文極薄且迭代期凍結(cache 前綴正確性條件);沙盒以自身目錄為 host 目錄,
   授權基座一律 CLI 旗標;真隔離走樹外實體化,禁依賴巢狀 git root。
4. commit 閘只讀訊息+本 repo staged 清單;任何常設閘禁讀 sibling checkout(解析走顯式
   --peer 審計,無參數 NOT_RUN)。
5. 快速品質閘(format/lint/型別)為架構級硬閘:pre-commit 掃 staged(<5s)+沙盒 verify T0
   同一定義;快閘綠不冒充 CQ/PU 軸綠;人 admit 永遠是終端邊。
