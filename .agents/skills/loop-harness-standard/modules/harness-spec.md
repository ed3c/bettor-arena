# Module: loop-harness-standard — 技術規格與設計決策 know-why

> 屬 [`loop-harness-standard`](../SKILL.md)。SKILL.md＝基座組件卡＋不變量;本檔＝**目錄結構圖＋設計
> 決策 know-why**——只留跨專案可轉移的方法論,antigravity 原版的歷史證成細節(具體 commit、具體案例
> 編號)不搬,見 [retarget-map.md](retarget-map.md)。

---

## §1 演化 op 沙盒目錄結構圖

```text
loop_wiki/evolve-<family>-<op>/       # 一沙盒一 op(spawn/refine/prune/spawn-cases)
├── run.sh                            # 1  調度入口 + driver switch(claude | agy;單發 dispatch)
├── PROMPT.md                         # 7  目標規範合約(Success Criteria = verify.sh 綠 + G 閘)
├── PLAN.md                           # 8  狀態帳本(STATUS + Verifier 歸屬 + 迭代軌跡)
├── CLAUDE.md                         # 1  被動上下文(≤300 行;claude -p 從沙盒 CWD 起載入)
├── AGENTS.md                         #   【選用】非 Claude driver 入口;同構時可 symlink,有 driver-specific
│                                      #    邊界時用薄 wrapper 指回 CLAUDE.md/PROMPT.md/ROUTES.md
├── ROUTES.md                         # 4+5 macro/small-loop route contract:agents,skills,validator,packet
├── modules/exchange-formats.md        #   【選用】跨 loop 交換 wire protocol(多 packet kind 時必備)
├── modules/production-readiness.md     #   【production seed】baseline/schema/template/behavior/scaffold/trend/security gates
├── baselines/                         #   【production seed】固定 count baseline,只經 governance packet 更新
├── packets/                           #   【選用/production seed】inbox/outbox 物理 exchange packets
│   ├── inbox/
│   └── outbox/
├── .agents/                          #   【選用】sandbox-local mirror endpoints,非 host config
│   ├── agents/                       #    小迴圈 domain/task actors
│   └── skills/                       #    小迴圈 domain/task skills
├── verify.sh                         #    T0 聚合:呼叫 `scripts/runner.py --family <f> --compare`,真 exit code
│                                      #    (0=全綠/2=FAIL/64=用法錯);非綠附 `PROGRESS:` 行供 engine 判斷
├── selftest.sh                       #    positive-control(good=PASS ∧ hollow=FAIL 才算判分器活)
├── scripts/                          #   【op 專屬 checker】如 spawn-cases 的 validate_candidates.py
├── anti/                             #    失敗模式沉澱(stop-loss 後的教訓)
├── logs/                             #    沙盒本地 log
└── _engine-run/                      #    engine.sh 落的迭代軌跡與快照
```

### §1.5 大迴圈側全結構(engine 層;2026-07-11 落地)

```text
loop_wiki/
├── engine.sh                         # 大迴圈機械引擎:iter-0 基線→conform_only 快路徑→dispatch
│                                     #   run.sh→verify→bounded iterate→兩型 stop-loss→ADMIT 閘 STOP
│                                     #   exit 碼契約=該檔頭注(枚舉不複列,防副本漂移)
├── README.md                         # 層級指針
├── _template/                        # 八基座骨架(cp -r 實例化)
└── <op-slug>/                        # 活沙盒(如 spawn-cases-semantic-traps,STATUS: done)
```

**契約鏈**:`engine.sh <loop> --target <path>` → `run.sh <driver> <target> [feedback]`(單發)→
`verify.sh <target>`(0/2/64+PROGRESS)→ 綠即 exit 10 停人閘。engine 絕不:semantic 判官/commit/
merge/自動 admit。薄版未實作(誠實範圍):儀表化、restore-best、host 偵測——需要時對照
`/Users/neon/antigravity/loop_wiki/engine.sh` 增量補。

**scope 邊界**:engine.sh=單 driver＋`claude -p` 逐發的機械 iterate/stop-loss 引擎,只做 T0 機械閘。
「同時多模型 author＋判官進自動迴圈」不是 engine.sh 的擴充維度,而是獨立編排層 **Workflow** 承——
判官/多模型同步分發由 Workflow 做,engine.sh 不擴這維;操作坑=SKILL.md codex Gotcha 指針(不重抄)。

### §1.6 root 層 vs sandbox 層 + 設計規範差異 vs 實作差異

antigravity root 層是 `AGENTS.md`=Antigravity/Gemini L1 SSOT,`CLAUDE.md`=Claude-tier 派生。skill-bettor
root 層目前相反:Claude Code 單 host,`ARCHITECTURE.md`=設計事實 SSOT,root `CLAUDE.md`=Claude-tier
entry,root `AGENTS.md` 只是 cross-host 種子;一旦 dual-runnable 才升成 cross-host SSOT。**不要把
root 層主權模型直接套到 loop sandbox。**

sandbox 層處理兩件事:driver entry 檔名差異與 route-layer 層級差異。`claude -p` 認 `CLAUDE.md`,
agy/grok 類認 `AGENTS.md`,codex 不認慣例檔名需 prompt 明令讀。兩檔可採二形:
1. **一實體＋symlink**:兩側 entry contract 真同構,只是 driver 檔名不同。
2. **薄 wrapper＋SSOT 指針**:需要 host-specific 邊界(如 findings-only、codex/agy 權限、`ROUTES.md`)。

禁令是**不得維護兩份治理 SSOT**;不是「永遠不得 symlink」或「永遠必須 symlink」。

`ROUTES.md` 是 base 4+5 的 route SSOT:同時列 macro-loop agent/skill、small-loop 本地
`.agents/agents/*`/`.agents/skills/*` endpoint、validator 與 packet 欄位。若交換不止一種 packet,
schema 定義落 `modules/exchange-formats.md`,並配一個 T0 validator;物理交付觸發可落 `trigger.sh`,
但 trigger 只可在 `packet_state: admitted` 時進 `engine.sh`。大迴圈與小迴圈可鏡射目錄名,
但職責不可鏡射:
- **大迴圈**:八大基座、driver 選型、跨小迴圈調度、route-ledger、人 admit。
- **小迴圈**:domain 知識、任務本地 actor/skill、單一 state node/conditional edge、findings/evidence 回傳。

小迴圈本地 `.agents/` 不是 Antigravity host config；不得在其中放 `settings.json`/`hooks.json`
來形成第二套 driver 設定。它只作為 domain/task route endpoint,由 `ROUTES.md` 暴露給大迴圈。

### §1.7 production seed extension(2026-07-22 fold-in)

若一條小迴圈要宣稱為 production-ready reusable seed,八大基座之外還必須接上 production seed
extension。通用方法 SSOT=
[production-seed-loop.md](production-seed-loop.md);本節只放結構位置:

| extension | generic owner | domain owner |
|---|---|---|
| hardened exchange packet | `ROUTES.md` + `modules/exchange-formats.md` | loop-specific typed validator and packet fixtures |
| physical delivery trigger | `trigger.sh` pattern | loop-specific trigger tests and admitted/draft fallback |
| route-result record | route-result packet kind | loop-specific writer/test |
| baseline governance | baseline-update packet kind | loop-specific stats script and governed update script |
| schema replay | schema-migration packet kind | loop-specific replay/migration scripts |
| template promotion | template-promotion packet kind | loop-specific template registry and promotion validator |
| behavior eval | behavior-eval packet kind | loop-specific behavior cases and pass/fail values |
| seed scaffold | seed-scaffold packet kind | loop-specific scaffold script and hardcoded-path check |
| trend observation | count JSON/JSONL categories | loop-specific logs/evidence policy |
| security boundary | path/command/fallback validators | loop-specific negative controls |

大迴圈折回本 skill 的只有這張方法和 extension 位置。domain 實作和固定數字留在小迴圈自己的
`modules/production-readiness.md`、`baselines/`、`packets/`、`scripts/`。

skill-bettor 單 host 下,兩軸退化為:

| 軸 | 隨什麼變 | 差異內容 |
|---|---|---|
| **設計規範差異** | **op 類型** | spawn/refine/prune=改 skill 內容,verify=public evals+G 閘,禁動 evals/;**spawn-cases**=改考題,verify=結構+trap-ness+可解性三層,禁動 skills/與既有 cases(scope guard 鏡像翻轉);prune 適用 G5 保護(只需 G1+G3) |
| **入口規範差異** | **host/agent contract** | `CLAUDE.md`=Claude-family passive context,可依 Claude Code cascade;`AGENTS.md`=non-Claude/Codex/agy entry。若只是檔名適配可 symlink;若需要明示 `CLAUDE.md`/`PROMPT.md`/`ROUTES.md`、driver 權限與 findings-only 邊界,就用 wrapper。 |
| **route 規範差異** | **macro-loop vs small-loop** | macro-loop 指揮多個小迴圈與八大基座;small-loop 專注 domain/task。兩層可鏡射 `.agents/agents`/`.agents/skills` 目錄,但責任不可鏡射。交換資料流必經 `ROUTES.md` packet 欄位與 `route-ledger.md`。 |
| **實作差異** | **driver 家族** | `claude -p`:讀沙盒 CLAUDE.md、acceptEdits、同家族→畢業判須 fresh subagent;`agy`:讀 AGENTS.md wrapper、`--add-dir` 命門、跨家族判官白吃、可用性看輸出檔非 exit code、**複核角色必須唯讀**(2026-07-11 實測 accept-edits 會改壞 fixture) |

**與 antigravity 原版的差異**:antigravity 版分 agy 專屬(`.agents/*`)與 Claude 專屬(`.claude/*`)兩套
平行 config 目錄(`settings.json`/`hooks.json`/`skills.json`/`agents/verifier.md`),因為它同時要跑雙 host。
skill-bettor 恆為 Claude Code 單 host,driver 只在小迴圈側切換,故不需要 `.agents/`/`.claude/` 雙套
config 目錄——授權走 `run.sh` 的 CLI 旗標,不落 settings 檔;獨立 verifier 走 fresh subagent 而非另立
host config。若沙盒有 `.agents/agents/*` 或 `.agents/skills/*`,它們是小迴圈 domain/task endpoint,
不是第二套 host config。目錄更薄,不是功能縮水。

---

## §2 設計決策 know-why

### ❶ 為何驗證器(Verify)與執行者(Execute)拓撲隔離?
寫代碼/寫資料的模型自審極寬容——同 prompt/同上下文會「合理化」自欺,改壞既有功能產生無聲 regression。
防線＝硬性、純代碼或外部子代理(`scripts/runner.py` 共享引擎機械層;fresh zero-context subagent 語義層)作 Verify
閘,AI 面對無法用花言巧語討好的 exit code(0=Success/2=Fail)。核心不變量＝「執行者≠判官權重」,隔離在
**家族層**:跨家族(agy 作者×Opus 判官)自動滿足;**同家族(Claude×Claude)必落地 fresh zero-context
subagent(禁 fork,fork 繼承脈絡＝非隔離)**。

### ❷ 為何被動上下文 ≤300 行?
過大常駐上下文使模型定位關鍵約束(Never rules)時注意力被稀釋,任務完成率實測顯著下滑(antigravity
`design_governance` pilot 錨:91.6%→71.3%)。被動上下文只宣告:簡介/演化紀律/≤5 條絕對禁止;其餘進
`shared/` 或子技能漸進加載。

### ❸ 背景程序阻塞(Stdin Hang)與授權
`claude -p`/`agy -p` 背景執行無聲卡死(CPU 0、零輸出)——CLI 為互動 TUI 設計,背景無 TTY 時 stdin 仍
open 會阻塞讀取。解＝`< /dev/null` 送 EOF 令其 one-shot 執行退出。跑 `verify.sh` 用
**`--permission-mode acceptEdits`**(而非更寬鬆的 bypassPermissions)——全局 hook 對 `verify.sh` 的
allowlist 回核准後,driver 的 Bash 面＝default-deny(只 allowlist verify.sh)＝權限面更小、幻覺出的
任意 Bash 被擋。安全仍由全局 hook 把關:acceptEdits 不繞 hook(PreToolUse 照跑、黑名單照擋)。

### ❹ Hook payload
Claude Code hooks 收在 `.claude/settings.json` 的 `hooks` 鍵,payload schema **依現場定**,需 hook 的
op 才驗欄位名——不預判寫死。skill-bettor MVP 期尚未有需要生命週期 hook 的 op,沙盒本地 `logs/` 先佔位。

### ❺′ 為何 run.sh 不含迭代邏輯?(2026-07-11 fold-in)
第一版把 iterate-until-pass+stop-loss 寫進 run.sh——每個沙盒各自長出一套不一致的迴圈控制,且
run.sh 的進度計數用「grep 累計 log」實作,單調遞增使 no-progress 永不觸發(實犯)。canonical 分層
(對照 antigravity engine.sh 後修正):**run.sh=單發 dispatch(祈使任務綁 target)、engine.sh=
迭代/stop-loss/快照/軌跡的單點實作**。效益:迴圈控制 bug 只修一處;driver prompt 形式(祈使綁
target)統一防「讀成規範不動手」反模式;engine 的 exit 10 讓「停在人閘」變成機械契約而非自律。

### ❺″ 為何 verify.sh 輸出 PROGRESS 行?
engine 判 no-progress 需要「每輪重算的接近度」。verify 的 exit code 只有 0/2 二值,無法區分
「差一條 check」與「全掛」;PROGRESS(如通過的 G 閘數/驗證層數)給 engine 一個單調且每輪重算的
量,連 2 輪未升即 stop-loss。粒度可依 op 自訂(spawn-cases 用通過層數 0-3),契約只要求「越大越接近綠」。

### ❻ 為何每個 model family 只佔一個 pipeline 階段(2026-07-17 fold-in，antigravity 同日經驗)
多家族派工設計的核心原則：起草者(author)與審查者(judge)兩個角色，先問「能不能落在不同 family」，能
就優先選不同家族——每加一個獨立家族，就多一層「執行者≠判官」式的天然隔離。antigravity 側真跑驗證：
codex(執行)×Opus(判官) 是跨家族天然隔離，比 claude-p(執行)×Opus(判官) 同家族還需要 fresh-subagent
額外工序更乾淨。這條原則不限於 codex 場景，任何委派任務只要有「誰做」「誰審」兩個角色，都適用。

### ❼ 機械 drift-checker + fresh 獨立判官複核(2026-07-17 fold-in，antigravity 同日經驗)
驗證「一份 domain 知識被獨立改寫是否忠實」的通用模式：機械 checker(如 antigravity 的
`r9-dual-file-drift.py`)先抓表面候選（可能有大量假陽性——不同語言/措辭改寫同一事實會被字面 diff
誤判成「新事實」），fresh 獨立判官(zero-context，非 fork)再對候選做語義複核，過濾假陽性、確認真缺口、
甚至抓機械 checker 本身判準寫反的 bug。antigravity 實測：39 條候選裡機械層抓到的僅 ~3 類是真缺口，
其餘是假陽性——沒有 fresh 判官這一步會嚴重高估漂移量。適用場景：任何「同一份知識被不同 driver/不同
時間點獨立改寫」的沙盒(如本 repo 未來若對 `families/*/SKILL.md` 做跨家族改寫，同一模式可套用)。
**校準**:對 `CLAUDE.md`/`AGENTS.md` 這種合法 entry-layer 改寫,字面 drift checker 只能當候選產生器,
不可單獨作 hard gate;需用 judge-loop-chooser/fresh judge 判「合法呈現層差異」還是真缺口。

### ❽ 多輪收斂測試需要刻意限制單輪範圍(2026-07-17 fold-in，antigravity 同日經驗)
強模型(如 codex)單次 dispatch 內建的 agentic iterate-until-pass 太強，自然任務很難逼出 engine 外層
的多輪迴圈——no-progress/regress/restore-best 這些機械路徑因此長期未被真實踩過。要驗證「engine 的
多輪收斂機械本身是否真的 work」，需要刻意造一個單輪範圍受限的 dispatch(如環境變數開關「這輪只修一條
違規就停手」)，而非等一個自然案例湊巧需要多輪。適用於任何要測試「迭代引擎本身」而非「driver 能力」的
場景。

### ❺ 單體轉沙盒化兩分類
八大基座分**基座引擎本身**(run.sh/verify.sh/PLAN——控執行權限/生命週期/調度)與**由既有邏輯轉換出的
業務狀態元件**(被動上下文/PROMPT/家族 shared 知識——攜該沙盒業務邏輯與驗證指標)。單體巨型邏輯拆分
沙盒化時,原規則→CLAUDE.md、原確定性檢查→family evals/runner.py checker、原踩坑→PLAN.md、原調度→run.sh。

---

## §3 driver 選型

per-op driver 三態(`run.sh` switch):
1. **`claude -p`**(Sonnet-tier author,主力):讀沙盒 `CLAUDE.md`,`--permission-mode acceptEdits`。
   同家族(Claude author×Claude judge)必落地 fresh subagent 判官。
2. **`agy`**(Gemini Pro 3.1,DR/跨家族複核):讀沙盒 `AGENTS.md` entry,`--add-dir <沙盒>`
   (命門——agy 不吃 shell CWD,不帶就寫自己 scratch)。跨家族天然隔離,判官白吃。可用性判據＝輸出檔
   非空且合法,**非 exit code**(quota 耗盡＝零輸出 exit 0 靜默 no-op)。
3. **對話內 subagent**(輕量;無沙盒執行體;prune 等輕量 op 適用):由大迴圈主 session 以 Agent tool
   讀沙盒 `CLAUDE.md`/`PROMPT.md` 後直接分發,不由 `run.sh`/engine dispatch 啟動;engine 對此 driver
   只做 T0 驗證(強制 dry-run,跑 iter-0 基線即 SURFACE)。判官歸屬隨 subagent model 家族(同家族→fresh
   subagent 判官;跨家族天然隔離)。
4. **`codex`**(OpenAI GPT，第三家族，2026-07-17 新增；經官方 `codex-companion.mjs`，禁手刻
   `codex exec`)：不讀 `CLAUDE.md`/`AGENTS.md`(不認檔名慣例)，明確指示先讀沙盒 `AGENTS.md`(若存在)
   取得治理規範。**codex 對 skill-bettor 唯一 host(Claude Code)恆跨家族**(OpenAI≠Claude)，判官白吃
   永遠成立——比 `claude -p` 更乾淨(後者同家族需掛 fresh subagent)。詳細用法/`--model`/`--effort`
   tier 對照見 ARCHITECTURE.md §5 tier-dispatch＋SKILL.md codex Gotcha(指針不重抄)。**proof
   run 已補**（2026-07-17 同日稍後）：`codex:codex-rescue` 真跑 gpt-5.4-mini@medium 最小唯讀 tracer
   證通；A 級錨與「模型自報不可信、判 model 看 session log」教訓 → MEMORY
   [[multi-model-dispatch-verification]] 同段（指針不重抄）。**殘餘缺口**：小迴圈側 `--driver codex` 的完整 op 真跑仍未發生，首次使用前先跑小
   target（antigravity 側已在 `loop_wiki/codex_demo`/`design_governance` 真跑驗證，見兩者 PLAN.md）。

**命令層級**:driver 由大迴圈(skill-bettor 主 session,恆 Claude Code host)指揮並選定——小迴圈＝被指揮
的執行體,不自選 driver。與 antigravity 不同,skill-bettor **不涉及雙 host 翻面**(不會有 Antigravity CLI
host 開這個 repo 的情境),故不存在「隔離格隨 host 翻面」的 N×M 矩陣,driver 選型是單軸(見
[retarget-map.md](retarget-map.md) 為何這維度被拿掉)。**`codex` 這個新增選項不改變這個結論**——
它對唯一 host 恆跨家族，不像 `claude -p`/`agy` 需要「隨 host 家族翻面」的表格，是單軸下最簡單的一格。

### §3.1 codex driver 的 context 生命週期與壓縮能力帳(2026-07-25 fold;狀態＝closed-no-target)

**為何 closed**:`run.sh` 是單發 dispatch、engine 每輪重新呼叫 → **每輪 dispatch＝全新 thread 的單一
turn**。82 個 dispatch 路徑量測:峰值 context median 23.7% / p90 42.1% / max 90.8%;91 次派工
**0 次壓縮**——壓縮只在 turn 之間評估,單 turn 不觸發。故「主動壓縮控制」在現行拓撲下**沒有標的**;
closed 的理由是無標的,**不是能力做不到**(能力清單見下,三條都實測過)。

**已驗證但刻意不用的能力**(記帳防未來重調研;錨＝openai-codex plugin v1.0.6
`~/.claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/`,行號 2026-07-25 逐條核過):
1. `app-server-broker.mjs:12` STREAMING_METHODS 含 `thread/compact/start`,request 實測被接受並落
   compacted record;但 `codex-companion.mjs` **無 CLI 出口**送得出去 → 要用得自寫 client,
   違反 `run.sh` 寫死的「禁手刻 `codex exec`,一律走官方 runtime」。
2. `CODEX_HOME` ＋ `model_auto_compact_token_limit` 經 companion/app-server 路徑實測生效
   (env 直通 `lib/app-server.mjs:192`)→ 閾值可調;但同上,無 turn 邊界可觸發它。
3. 壓縮的 `replacement_history` 逐字保留全部 user message,摘要本身是 `encrypted_content`
   **不可讀** → post-compact 語意稽核**不可證偽**。
   **禁回退:寫「壓縮後語意保真」類 checker(恆綠 placebo)。**

**什麼條件讓它復活**(AND,缺一不成立):①決策 3 跨迭代 resume 翻面 → ②同 thread 跨 iteration 續命
→ ③turn 邊界出現 → 壓縮才有標的,能力 1/2 才值得動。屆時能力 3 仍成立(稽核仍不可證偽,別重寫)。

**決策 3(跨迭代 `--resume`)＝不做,但阻塞在上游能力,非「不值得做」**——這個區別是本帳重點,
決定了重議的觸發條件在上游而不在本 repo:`codex-companion.mjs:777` 的 `--resume`/`--resume-last`
是同一個 flag,**無法指定 thread**;它 resolve 的是 `resolveLatestTrackedTaskThread(workspaceRoot)`,
而 `lib/workspace.mjs:3-5` 的 `resolveWorkspaceRoot`＝`ensureGitRepository(cwd)`＝**git root**
(實證 job 檔的 workspaceRoot 是 repo 根,不是沙盒)→ 全 repo 沙盒共用**同一個 resume 池**,
並行跑會**靜默串線**。上游 companion 給出 per-thread resume 出口前,重議＝重踩。

**替代路徑**:「重複踩同一個坑」改用**自動提示**(把 iter N 的失敗證據轉成 iter N+1 dispatch 的
額外提示)解決,與壓縮無關。注入通道沿用既有的 `run.sh <driver> <target> [<feedback>]`
(append 成「額外整改要求」段,不另造通道);2026-07-25 已落地——engine 逐輪重算,
生成器＝`scripts/build_iter_feedback.py`(見 `engine.sh` 頭注「自動提示」條與其
`# 自動提示(2026-07-25 補` 區塊;行號不複列,防副本漂移)。
遮蔽紀律:packet 預設只出 checker+識別碼、丟掉失敗訊息全文——實測轉發全文等於在 driver 動手前
把過關攻略遞到手上(作弊 driver 兩輪從 PROGRESS 0 到全綠)。要全文用 `--verbose-labels` opt-in。

---

## §4 Verify 三層分層

①**T0 機械**(`scripts/runner.py --family <f> --compare` G1-G5,零 LLM;`verify.sh` 聚合層,真 exit code)
②**行為**(family `evals/cases/` 一次性 pre-registered,非每輪 LLM 判官;覆蓋率＝planted-defect 檢出率)
③**畢業 semantic 判官**(holdout 段,fresh zero-context subagent,禁 fork;機械層關不完 Goodhart 的
backstop)。

**selftest 正控(anti-placebo)**:每個 runnable checker 必對 good/hollow fixtures 區分(good=PASS ∧
hollow=FAIL 才算 checker 活),分不出＝placebo,誠實降級為 rubric(人判),不放水。

**硬條款**:verify 必接真實執行(真 exit code)、禁 LLM 模擬環境。stop-loss 兩型
no-progress/exhausted → SURFACE 交人。

### §4.5 oracle-gate/dense-sparse-blind 完成契約(2026-07-19 遷入,composer-integration)

task→質量神諭三態前置閘,判「這個 task 的『完成』由什麼裁定」:
- **dense**(有 T0 硬驗證器)=完成⇔軌跡 iterate-until-T0-green;證據=engine 軌跡落帳
  (`loop_wiki/engine.sh` 的 `TRAJ=`/`log()` → `_engine-run/trajectory.log`),非文字宣稱寫完。
- **sparse**(pre-registered 判官 checkpoint,[evals-design-method.md](evals-design-method.md) 紀律)
  =機械層綠∧checkpoint 過。checkpoint 記錄格式範本→本地 [`dr-to-mvp`](../../dr-to-mvp/SKILL.md)
  dual-score 段(設計分∧實作分 AND,採用不重造;本地 LIVE 錨=mvp-radar 2026-07-19 畢業,
  見 harness-wiki 組件卡)。
- **blind**(無神諭:研究/創作/架構類)=真跑過∧**人 admit 不可約**(engine exit 10=
  awaiting-human-admit;人閘清單=`ARCHITECTURE.md` §8)。
- silent no-op 判活=engine exit 22(`loop_wiki/engine.sh` `suspected silent no-op` 判活區塊,唯一標準=target diff)。

**誠實正名**:「零飄逸」只在 dense 成立——有技術實作等價物處 iterate-until-green 把概率輸出轉確定;
blind 處飄移機械無法根除,只承諾「抓到→SURFACE→人 admit、永不靜默」。對外承諾措辭以此為界。

三態 grounding(`technical_equivalent / candidate / [推論]`)的 SSOT=
`judge-loop-chooser/modules/grounding-and-independence.md`(軸一;引用不重造——該檔明示這是本地
evals 紀律的升格,非外來 import)。**正交分工**:oracle-gate 判「驗證標準是什麼」,judge-loop-chooser
四層 tier 判「驗證者獨立性權重」。

**斷言表 B-1 統一 schema**(定義權在本 §;execution-feedback 模組只消費):
`| id | 斷言 | expected-observation | 對軌跡勾稽方式 | verdict(HELD/REFUTED/UNOBSERVED) |`
——pre-register 時 `expected-observation` 必填(N-variant drift-loop 消費欄)。

fold-in 條件性:有 durable 課才 fold,非完成 gate,不強制(anti-inflation)。

### §4.6 環境自足不變量(2026-07-26;鐵律 7 的前提條件,非並列新規則)

**不變量**:一支 T0 verifier 的 exit code 必須是**被驗物內容**的函數,不得是**執行它的機器狀態**
或**它所在的檔案系統位置**的函數。等價可機械化敘述:同一份 git 追蹤內容,在任意 checkout 位置的
fresh clone 上必須產生相同的 exit code。

**為何掛在鐵律 7 底下而不是新增第 13 條**:§2❶「無法用花言巧語討好的 exit code」只封住**語言通道**。
`[ -x "$HERE/venv/bin/python" ] || fail 'no venv python'` 的 exit 2 是**誠實的 FAIL**——真跑、真
exit code、零 LLM——它只是回答了「這台機器有沒有 venv」而非「被驗物對不對」。真 exit code 的前提,
是那個 code 由被驗物而非宿主狀態決定;沒有這個前提,鐵律 7 的保證是空的。它是**限定條件**不是第二套事實。

**合法 vs 非法依賴的分界=「這個依賴隨不隨 checkout 移動」**(非我發明,是從 repo 現況量出來的:
60 支追蹤中的 `verify.sh`/`selftest.sh`,恰好 3 支引用 venv,其餘 57 支的依賴集合只有
`sh`/`bash`、`python3`、`git`、POSIX 文字工具):

| | 合法(宿主契約) | 非法(checkout 狀態) |
|---|---|---|
| 性質 | repo 之外、對所有 checkout 一致、缺了會**吵鬧地**失敗 | 樹內或某次 setup 產生、隨 checkout 位置漂移、缺了**看起來像被驗物壞掉** |
| 實例 | `bash`/`sh`、`python3` ＋ stdlib(`-m unittest`)、`git` | `<module>/venv/`、`node_modules/`、驗證期 `pip install`、寫死的 checkout 絕對路徑 |

**in-repo canonical 存在證明**:`families/aie-context/shared/runtime/internalization-radar/verify.sh`
在 fresh clone(`git archive HEAD | tar -x`)上 **EXIT=0**、4/4 check PASS,因為它用系統 `python3 -m
unittest`。同批另外三支(pack-core / evals-gate / harness-core)同一測法 **EXIT=2**「no venv python」。
⇒ 環境自足不是外來理想,是本 repo 四支同位組件裡**一支做到、三支偏離**的既有性質。

**四條子判準;C1-C3 靜態便宜可進常設閘,C4 貴且需 canonical 調用宣告故不隨 v1 上線**:

| | 判準 | 現況 | 誤判面／偵測邊界 |
|---|---|---|---|
| C1 | 不引用「fresh clone 上不存在」的路徑 | 60 支中 3 支命中 | verifier **自己 `mkdir -p` 建立**的產物不算(`logs/`);變數拼接的路徑靜態抓不到 |
| C2 | 驗證期不改變環境(裝套件/寫被驗物外持久狀態) | 2 支命中 | 危害已物理證實:那個 `venv/bin/pip` 是 console script,shebang 寫死真 repo 路徑 ⇒ **在副本上執行它會裝進真 repo 的 venv**,「驗證期改環境」與「逃逸隔離」在同一行發生 |
| C3 | 被追蹤內容不含機器不穩定絕對路徑 | copy 面內 31 支 / 53 筆 | 見下方閘 |
| C4 | fresh clone 上真跑 exit 0 | 4 支中 3 紅 | 只證 **checkout-hermetic**,不證 machine-hermetic(仍繼承宿主 `python3`/PATH/site-packages) |

**C3 的物理閘**=`scripts/check_isolation_selfsufficiency.py`(L1)。它守的是隔離的**物理性**:
`runner.install_family()` 把家族 `copytree` 到 agent 工作區,但隔離從來只被實作成「複製到暫存目錄」,
**沒被驗證成「agent 讀到的真的是那份副本」**——副本裡任何一條寫死的 checkout 絕對路徑都把 agent
導回真 repo。判準語義沿用 `check_cross_repo_parity` 的 rewrite-gap 謂詞(「應與 root 無關的位元組
含不含 root」),掃描域零重疊(parity 的 manifest components 無 `families/` 前綴);共用的是隔離帶
紀律實作(到期日/預算/**自我清理**),不是那兩行程式碼。細節與豁免邊界在該檔 docstring,此處不複述。

**刻意不做的兩件事**:①**不把可達性做成判準**——「目前有沒有人真的讀它」是 agent 行為的性質,
下一個 prompt 就會變;「副本不含 root」是位元組的性質,可機械證。可達性只是上界估計,
失敗方向系統性偏向「看起來通過」,拿它下判決就是把估計當判決。②**不對第三方套件發表意見**——
repo 現況零依賴宣告檔(無 root 層 requirements.txt / pyproject.toml),而 `scripts/runner.py`
`import yaml` 來自 homebrew site-packages ⇒ canonical T0 路徑嚴格說也不是 fresh-clone-runnable。
沒有宣告檔就分不出「依賴」與「碰巧有」,把它折進本閘只會讓新閘一上線就對著一個未決問題全紅。
**這是獨立缺口,SURFACE 不代裁。**

---

## §5 cache 不變量

①迭代禁 commit(git 快照入 cache scope)②driver 從沙盒 CWD 起(subdir CLAUDE.md 否則進 conversation
層非穩定快取層)③prefix 字元級穩定(禁 timestamp/uuid)④sizing 落 min-可快取~≤300 行⑤session reuse。
oracle＝`cache_read_input_tokens` > 0。誠實錨:cache 是次要優化,非降本主軸,別為了湊快取犧牲被動
上下文的可讀性。

---

*本檔＝可轉移方法論;antigravity 原版的 D 編號決策帳本、具體 commit 錨、pilot 案例史不搬——見
[retarget-map.md](retarget-map.md)。*
