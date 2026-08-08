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
├── CONTEXT.md         # 詞彙表(glossary only;admit 三義/Intent-Slice/receipt 等 canonical terms)
├── ARCHITECTURE.md    # 本檔=工程 SSOT+放置契約權威源
├── bootstrap.sh       # 冪等啟用:相對 hooksPath+環境 doctor(exit 64=FATAL)
├── delivery.json      # 本線交付收據(物理證據:四層位址+synced_at_commit);SSOT 對映在
│                      #   .agents/skills/forgejo-delivery-loop/registry.json,T0 閘=check_delivery_receipt.py
├── .gitignore         # 版控忽略帳(__pycache__/、*.pyc 等生成物)
├── .mcp.json          # Claude Code 專案 MCP 宣告(啟用=人 admit;S10 落地)
├── .githooks/         # 大迴圈 git hooks(唯一跨 host 閘層;S7/S8 落 pre-commit/commit-msg)
├── .claude/           # Claude Code host 配置(版控 settings;skills 全 symlink,指向 .agents/skills 或模組自有 skill,如 kb-ingest/skill;
│                      #   commands/=slash 轉發層,零邏輯,程序 SSOT 在對應 skill)
├── .codex/            # Codex host 配置(僅可攜 MCP 宣告;host 段人補)
├── .agents/
│   └── skills/        # skill 內容 SSOT(host-neutral 單份;S5 落地)
├── .skill-bindings/   # 共用 skill 的本 repo 綁定層(一 skill 一目錄,必有 binding.md 四欄:
│                      #   skill/upstream/retargeted_at/body_commit)。判準:原封搬到別的 repo 還為真嗎?
│                      #   不為真就落此槽——registry、worked instance 指針、環境路徑、移植帳本。
│                      #   目錄不存在=未 retarget,是缺席不是缺陷
├── kb-ingest/         # repo-wiki 模組(openwiki/=上游逐字;port/=本地執行層;S4 落地)
├── loop_wiki/
│   └── evolve-perfect-seed-repo-factory/   # 工廠沙盒(自足 TS;trigger.sh 入口;S3 落地)
├── mcp/               # MCP adapter 層(context-pack+production 引擎;S10 落地)
├── openwiki/          # repo-wiki-converge 生成的 as-built wiki(可再生投影,git 追蹤;更新走官方 update 模式,index.md 由 finalize 生成禁手寫)
├── proof_workflow/    # 三條迴圈的物理遍歷證明(一迴圈一支 .sh;lib/prove.sh=共用記錄器,
│                      #   `--selftest` 是它自己的負控)。每支從啟動點走到末端產物,分記兩種步驟:
│                      #   harness=確定性腳本(真跑並記 exit;會改帳的入口只 hash 記 hashed-not-run,
│                      #   永不讀成綠)、context=概率性那一側真正讀的文檔(只 hash 不執行,缺席即 FATAL)、
│                      #   artifact=末端產物(tracked 者判 HEAD 位元組,免得同一趟的 harness 移動自己的證據;
│                      #   tracked 但本地被刪=獨立紅)、note=刻意不 hash 者連理由一起入帳,禁無聲截斷。
│                      #   收據落 data/proof-workflow/,帶 commit+tree+全路徑 sha256 折成的 proof_digest。
│                      #   control_macro_entry.sh=大迴圈啟動點的**對照組**:真跑 bootstrap.sh,把每條
│                      #   執行的 argv/exit/stdout/stderr 落 proof_workflow/data/<run_id>/(gitignore,
│                      #   因 gate 輸出含本機絕對 repo root;收據帶每個 stream 的 sha256 把它釘回 commit)。
│                      #   路徑是必要還是可選由**實驗**判定——丟棄式 worktree 拿掉該路徑再跑,看 exit 變不變,
│                      #   不讀 fatal/warn 字面;未分類即 FATAL。比對面是三支證明收據的聯集,不只 macro
├── scripts/
│   ├── gates/         # repo 級防禦腳本(零 LLM):check_root_coupling.py+check_placement.py(§2 機械化)+check_skill_pointers.py(skills 單份+host 指針閘;S5)+check_credential_hygiene.py(憑證材料不入 tracked 檔;#17 事故根因)+check_delivery_receipt.py(交付收據;forgejo-delivery-loop 的 T0,零網路;#27)+_gate_common.py(三閘共用 repo_root/fixture 樣板)+allowlist 帳
│   ├── delivery_status.py # 交付活狀態顯式審計(打網路,禁進 hook;--selftest 零網路驗渲染)
│   └── migrate/       # 遷移引擎 v2(migrate_seed.py;dry-run 預設/--apply/--stats/--selftest;S2 落地)
├── tests/             # repo 級測試(打 gate CLI exit code 接縫;tools/=量測再現腳本,如 corpus parity)
├── data/              # 機器帳與 receipt 落點(遷移 stats/煙測 receipt)
│   ├── proof-workflow/ # proof_workflow/ 的遍歷收據(schema
│   │                  #   bettor-arena-proof-workflow-receipt@1.0.0;檔名 <loop>-<commit12>[-dirty].json,
│   │                  #   同名重跑 FATAL 64,PROVE_FORCE_RECEIPT=1 顯式覆寫;-dirty=雜訊樹,
│   │                  #   hash 的位元組不在該 commit 裡,宣稱範圍隨檔名寫死)
│   ├── wiki-update/   # 工廠交付終點的 wiki-update 請求+消化站 receipt(runtime 生成物,gitignore;
│   │                  # schema bettor-arena-wiki-update-request@1.0.0,producer=工廠 trigger.sh,
│   │                  # consumer=kb-ingest/port/wiki_update_worker.sh;湧現內容不落此處,只落 openwiki backlog)
│   └── migration/     # manifest.json(v2;repo-relative 唯一)+apply receipt(per-run report-<commit>-<組件集>.json append-only,同名重跑 exit 64/--force-receipt 顯式覆寫;S3/S4 的 apply 早於 per-run 機制,其 receipt 僅存 git history 的 last-migration-report.json 版本;last-migration-report.json=最新拷貝,執行期生)
└── docs/              # 計劃/交接文件(非模組知識);adr/=架構決策記錄(0001=slice 詞彙);
                       #   plans/<date>-<topic>/as-run.md=該線執行帳(已完成/未完成/已跑/未跑),
                       #   forgejo-delivery-loop 三 SSOT 之一,與 openwiki(as-built)分工
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
6. 工具缺席走 FATAL(exit 64),與檢查失敗(exit 2)分流;缺席永不可讀成綠(§1:每個綠
   先有對應的紅)。
7. 重複組件禁字面推論等價:判等價=讀碼+真跑;load-bearing 且判錯有代價=重建並列量測。
