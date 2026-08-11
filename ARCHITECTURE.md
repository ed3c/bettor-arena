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
├── .github/           # GitHub cloud verification；只跑零網路、可由 fresh clone 重現的契約閘
├── .claude/           # Claude Code host 配置(版控 settings;skills 全 symlink,指向 .agents/skills 或模組自有 skill,如 kb-ingest/skill;
│                      #   commands/=slash 轉發層,零邏輯,程序 SSOT 在對應 skill)
├── .codex/            # Codex host 配置(僅可攜 MCP 宣告;host 段人補)
├── .runtime-env/      # runtime-env 單向產生的消費端投影(binding/example/workload/policies;
│                      #   Agent 操作與完成契約→docs/runtime-env-integration.md):
│                      #   只帶名稱、安全預設與 source commit/tree receipt，禁放憑證值與 .env;
│                      #   維護時顯式 sync，consumer verifier 的輸入只准本 repo projection，禁讀 source catalog
├── .agents/
│   ├── skills/        # skill 內容 SSOT(host-neutral 單份;S5 落地)
│   ├── shared-skills.requirements.json # consumer desired shared/repo-owned names與雙 carrier surface
│   ├── bindings/      # skills-shared resolver 產的 commit/tree/requirements/registry/per-skill digest closure
│   └── module-set.json # skills-shared + runtime-env + Claude/Codex adapter 的唯一聚合介面
├── .arena/            # 模組控制面：schemas、module manifests、composition requirements/locks、presets；
│                      #   Phase 0 只宣告與驗證，不冒充 module-scoped proof v2 或 project initializer 已完成
├── .skill-bindings/   # 共用 skill 的本 repo 綁定層(一 skill 一目錄,必有 binding.md 四欄:
│                      #   skill/upstream/retargeted_at/body_commit)。判準:原封搬到別的 repo 還為真嗎?
│                      #   不為真就落此槽——registry、worked instance 指針、環境路徑、移植帳本。
│                      #   目錄不存在=未 retarget,是缺席不是缺陷
├── .runtime-env/      # runtime-env 的 consumer 投影(非密鑰儲存):bindings/ 固定來源 commit/tree+profile closure;
│                      #   examples/ 是可重算 dotenv；workloads/ 固定入口/收據/對照組；policies/ 分離 Claude/Codex 原生設定。
│                      #   pre-commit 驗 staged manifest 全閉包，禁連網/讀 sibling/自動同步；README.md 記顯式 sync/check 路徑
├── kb-ingest/         # repo-wiki 模組(openwiki/=上游逐字;port/=本地執行層;S4 落地)
├── notebooklm/        # NotebookLM 業務迴圈模組(README.md=法則層+抖動迴圈+已抓到的缺陷,開這個目錄的
│                      #   agent 先讀它;workflow.py=唯一入口,drive_fetch.py=認證過的 Drive 路徑,
│                      #   registry.json=互動資料(notebook pin/harvest target;憑證只留指針,絕不落值),
│                      #   自有 `--selftest` 零網路)。
│                      #   兩跳:hop1 從具名 notebook 取一個 Google Doc/Sheet 的 fulltext,
│                      #   hop2(`--follow` opt-in)拿 hop1 抽出的 docs.google 文件 URL 真去存取——
│                      #   走**丟棄式 scratch notebook**,來源 notebook 永不被寫。
│                      #   外部組件=notebooklm CLI(github_projects/notebooklm-py);binary 缺席=64,
│                      #   present-but-NOT-authenticated=2,兩者不得互相冒充。
│                      #   `--json` 純度是量出來的契約:partial ID 會讓 CLI 在 JSON 前多印一行
│                      #   `Matched: ...`,所以每個 id 先解析成完整 UUID 再呼叫,且解析後仍斷言純度
├── loop_wiki/
│   ├── evolve-perfect-seed-repo-factory/   # 工廠沙盒(自足 TS;trigger.sh 入口;S3 落地)
│   ├── evolve-technical-equivalence-research/ # 技術觀點→落地等價物小迴圈(profile+五類 packet+Gemini adapter;
│   │                  #   只產 candidate sync bundle，skill-bettor target-side Human admit 才可套用)
│   └── code-truth-graph/ # 通用 CTG runtime 沙盒；closed packet、content-addressed snapshot、
│                         # pinned tool profile、0/2/64 與 graph/result artifacts；不持有 ix domain/raw evidence
├── mcp/               # MCP adapter 層(context-pack+production 引擎;S10 落地)
├── openwiki/          # repo-wiki-converge 生成的 as-built wiki(可再生投影,git 追蹤;更新走官方 update 模式,index.md 由 finalize 生成禁手寫)
├── loopctl/           # contract 宣告迴圈對外的唯一 CLI 表面(外界只准碰這裡;繞過它去學各入口的私有旗標,
│                      #   下一步就是為了遷就呼叫端去改入口本身——這支存在就是擋這種抖動)。
│                      #   contract.json=宣告面(loop×mode×必填/選填旗標/寫出什麼;`contract` 子命令
│                      #   連 sha256 一起印,表面變動因此是可見事件);loopctl.sh=接線;兩者由
│                      #   selftest.sh 雙向綁死,任一邊多出命令即紅。exit code 原樣透傳不重映射。
│                      #   危險路徑一律 opt-in 旗標(`openwiki run --full` 才燒 model turn 並改 openwiki/)
├── proof_workflow/    # contract 宣告迴圈的物理遍歷證明(含 agent-runtime proof/control；一迴圈一支 .sh;lib/prove.sh=共用記錄器,
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
│   ├── arena_modules.py # Phase 0 module catalog CLI：catalog/check/resolve，產 deterministic composition lock
│   ├── agent_runtime.py # module-set 深介面：offline/adapter/strict 三層判決與雙 carrier live receipt
│   ├── gates/         # repo 級零網路閘：root coupling/placement/skills/credentials/runtime/delivery，
│   │                  #   加上 agent entrypoint contract 與 module catalog/lock；常設閘禁讀 sibling checkout
│   ├── delivery_status.py # 交付活狀態顯式審計(打網路,禁進 hook;--selftest 零網路驗渲染)
│   └── migrate/       # 遷移引擎 v2(migrate_seed.py;dry-run 預設/--apply/--stats/--selftest;S2 落地)
├── tests/             # repo 級測試(打 gate CLI exit code 接縫;tools/=量測再現腳本,如 corpus parity)
├── data/              # 機器帳與 receipt 落點(遷移 stats/煙測 receipt)
│   ├── proof-workflow/ # proof_workflow/ 的遍歷收據(schema
│   │                  #   bettor-arena-proof-workflow-receipt@1.0.0;檔名 <loop>-<commit12>[-dirty].json,
│   │                  #   同名重跑 FATAL 64,PROVE_FORCE_RECEIPT=1 顯式覆寫;-dirty=雜訊樹,
│   │                  #   hash 的位元組不在該 commit 裡,宣稱範圍隨檔名寫死)
│   ├── notebooklm/    # notebooklm 迴圈的每趟業務收據(runtime 生成物,gitignore;schema
│   │                  #   bettor-arena-notebooklm-module@1.0.0)。內容是他人 Google 文件的抽取物,
│   │                  #   位元組不進版控也不進任何 proof digest——每趟都變的東西進 digest,
│   │                  #   追蹤的就變成「上次跑在哪」而不是「機制是什麼」。收據只記 sha256 與計數
│   ├── ingest/        # loopctl `micro run --source` 的抽取產物(runtime 生成物,gitignore):
│   │                  #   packet.json + extracted.txt + provenance.json(原檔路徑/sha256、抽取器 argv
│   │                  #   與版本、抽出後 sha256)。抽取記錄在案才不會讓衍生物頂著原檔的名字
│   ├── wiki-update/   # 工廠交付終點的 wiki-update 請求+消化站 receipt(runtime 生成物,gitignore;
│   │                  # schema bettor-arena-wiki-update-request@1.0.0,producer=工廠 trigger.sh,
│   │                  # consumer=kb-ingest/port/wiki_update_worker.sh;湧現內容不落此處,只落 openwiki backlog)
│   └── migration/     # manifest.json(v2;repo-relative 唯一)+apply receipt(per-run report-<commit>-<組件集>.json append-only,同名重跑 exit 64/--force-receipt 顯式覆寫;S3/S4 的 apply 早於 per-run 機制,其 receipt 僅存 git history 的 last-migration-report.json 版本;last-migration-report.json=最新拷貝,執行期生)
└── docs/              # 計劃/交接文件(非模組知識);agent-runtime-integration.md=目前可執行跨 repo closure；
                       #   architecture/modular-integration-requirements.md=下一階段低壓縮 target contract；
                       #   audits/=具名 commit/branch 的審計交接包;adr/=架構決策記錄(0001=slice 詞彙);
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
8. `.arena/` 是 manifest-first 控制面；Phase 0 的綠只證 catalog/requirements/lock 自洽與 ownership
   不重疊，不得代理 module-scoped proof v2、Context Capsule、project initializer 或 multi-origin promotion。
