# as-run — bettor-arena 遷移線的完整執行帳

> 這是**低壓縮 as-run 帳**:每一項寫「做了什麼／跑了什麼／證據在哪／還沒做什麼」。
> 規格根＝Forgejo `neon/bettor-arena#2`(PRD);橫向視圖＝milestone「bettor-arena migration (PRD #2)」;
> 交付機制＝`.agents/skills/forgejo-delivery-loop/`。本檔是該 skill 三個 SSOT 中的
> 「未完成項低壓縮追蹤」欄,chat 與 PR 都是它的投影。
>
> **與 openwiki 的分工**:`openwiki/` 是 as-built(現在的系統長什麼樣,官方三閘驗過);
> 本檔是 as-run(做的過程、跑了什麼、什麼沒跑)。前者答「是什麼」,後者答「怎麼來的、還缺什麼」。

## 1. 狀態總表(每列都可在 Forgejo 點開)

| # | 切片 | 狀態 | 落地證據(commit) | 跑過的驗證 |
|---|---|---|---|---|
| #3 | S1 骨架:root-coupling 閘+bootstrap+放置契約 | 完成 | `08b2fdf` | 閘 selftest(注入必紅)、bootstrap 契約測試、突變體負控 |
| #4 | S2 遷移引擎 v2 | 完成 | `5473211`+fixpacks | selftest 正負控、真 dry-run 241 檔、apply receipt |
| #5 | S3 工廠沙盒遷入 | 完成 | `b7983da` | verify 11 步、selftest good/hollow、portability 雙負控、trigger 端到端 |
| #6 | S4 kb-ingest 遷入+port 改名 | 完成 | `550a44a` | sync --check 對 pin 綠+單位元組負控、模組閘、relocation 16 控 |
| #7 | S5 skills SSOT 統一 | 完成 | `ae3a2db` | 指針閘 selftest、20 條 symlink 實查、`claude -p` 活發現煙測 |
| #8 | S6 host 配置 | 完成 | `d69f2bd` | rm 守衛 selftest、settings 零絕對路徑、真 session 越界被擋 |
| #9 | S7 快閘硬化 | 完成 | `c435d42`+`bd294c5` | 三 lane 負控、夾具真 commit 擋/放、<5s 預算、index-blob 與 strict 修復 |
| #10 | S8 molecular 閘重建 | 完成 | `99fa15d` | 100 條真實語料並列判決矩陣、夾具真 commit 煙測、bun 缺席負控 |
| #11 | S9 source_refs 追溯鏈 | 完成 | `568f5d7` | 形狀負控、resolve-refs NOT_RUN 語義、端到端 receipt 鏈 |
| #12 | S10 MCP 面 | 完成 | `3bfd114` | context-pack 12 tests、production 30 tests、tampered hash 負控 |
| #13 | S11 driver 對齊 | 完成 | `c38b1d5` | 雙 driver 真跑煙測、cache 四規入 SSOT |
| #14 | hook 三支武裝 | 完成 | `9c401d1`/`38e4251`+執行位修復 | 活負控:普通訊息碰 protected surface 真被擋、commit 數不變 |
| #15 | settings 側門追認 | 完成(人裁) | — | 內容逐位元組複驗;防回退錨入全局記憶 |
| #18 | 快閘殘債 | 完成 | `0d01497`/`6f8cd13`/`186f175`/`dc37c1c` | uvx 去網路路徑、pgid watchdog 孤兒負控、_gate_common 抽共用 |
| #19 | receipt 碰撞語義 | 完成 | `8fe5c12` | 碰撞拒寫負控(突變重驗)、O_EXCL 原子建檔 |
| #20 | refs_status 三態化 | 完成 | `c329882`+`2c36ddf` | tampered→stale 負控、source/lineage 對稱斷言 |
| #21 | as-built openwiki | 完成 | `a02b90b` | 官方三閘(critic 兩輪/finder 10 題/verifier 10-10 PASS)、後處理冪等 |
| #22 | wave-4 殘債 | 完成 | `2c36ddf` | stale 態、毀損 exit 2、15b trap、O_EXCL |
| #23 | wiki 維護自動觸發 | 完成 | `8a32aa9`→`a286d67` | 交付即發 typed 請求、消化站全鏈、湧現分離 grep 負控、通電真跑一輪 |
| #24 | delegated-executable 漂移 | 完成 | ts `40b9b1f` | 6 個 launch site 逐一讀 caller 分類、注入未分類必紅負控 |
| #16 | 來源側移除段 | **完成** | ts `7787bd5`(移除+回釘)、`9d90693`(forwarder 三態)、`5b344bf`(#26 退役) | 6 個目標出 index(第 6 個=`.claude/skills/repo-wiki-converge` symlink,由 forwarder 閘在移除當下找到);刪後 5 支閘綠;`test_golden_seed_migration_context.sh` 既有紅=#30 |
| #17 | 憑證輪替 | **完成** | `243650f`(憑證衛生閘) | 閘 selftest 五案+突變負控;帳號密碼 2026-08-07 由人在 UI 改畢,`git ls-remote` 兩 remote 實測 exit 0 |
| #26 | engine_nv.sh 宣告但未建造 | **完成(撤)** | ts `fe4abe2`(具名 NOT-RUN)→ 2026-08-07 人裁退役 | selftest 與 `_nv_fixtures/` 已刪、§2 槽位與 harness-wiki 記退役理由;方法論(harness-spec §4.5+四 checker)不隨之退役 |
| #27 | delivery-loop 移植 Forgejo | **完成** | ts `b8d42bd`(三支工具+`/delivery`)、arena `b30f909`(null 修正) | 收據閘 selftest 四案、milestone 實建、registry 零 github.com;ts 側真跑派送兩半皆通 |
| ts#1 | GCR-SLICE-02 admit | **完成** | ts `2cd905f`→`0f8e451` | 旅程真走完:PR-head preview → fast-forward merge → canonical smoke,兩相位投影相同且等於綁定 artifact hash;milestone `gcr-admitted-tracer` blocked_dependency→in_progress→verified |
| #30 | context 套件既有紅 | **完成** | ts `90bbe7f` | 生產者錯:REQUIRED_TARGET_PATHS 仍列 5 個源樹已無的檔案,恆停在 migration-target-repair。guard 擴成兩 twin 逐項比對(單側刪一條原本靜默) |
| #31 | 宣告值無人斷言 | **完成** | ts `90bbe7f` | 兩個字串斷言收口(前綴洩漏),同型缺陷在上一行的 python_spawn_boundary_coverage 一併修;9 個無人讀的 key 全屬生產者輸入,已記進 notes |
| ts#27b | 收據物化 | **完成** | ts `fc2b196`、arena `517dd59` | PR merge 後線才有交付載體;真跑 sync 炸出 explicit-null 與 merged-PR 兩缺陷,兩份姊妹副本同日一起掃 |
| #2 | PRD 母票 | **完成** | 本輪 | 驗收條款逐條真跑:5 結構閘+5 selftest+fast_quality+7 tests+工廠三支+kb-ingest 閘,全綠零紅 |
## 2. 跑過什麼(真跑,非宣稱)

- **六波 workflow**(22+ agent):implement→tdd→code-review 逐片,findings 回流成 fix commit 或新票。
- **通電一輪**(真 packet `poweron-2026-08-06`):trigger 交付→自動發 wiki-update 請求→消化站
  LLM 再生(sonnet)→finder/verifier 官方閘真開火→finalize 重錨 gitHead→receipt 回鏈+凍結入版控。
- **全閘掃描**(16 道,兩 repo):15 綠、1 具名 NOT-RUN、0 紅。掃描本身也被教會三態(64≠壞掉)。
- **PR**:#1 已 merge(S1–S11 全切片);#25 待審(post-merge 增量)。

## 3. 沒跑什麼(缺席具名,不冒充綠)

- **物理刪除**(#16):2026-08-07 **人 admit 後真跑並 commit**。先前那次是 dry-run 誤觸,已完整復原;本次走 `HUMAN_ADMIT` 守衛、停在 commit 前交人審。
- **Forgejo 帳號密碼輪替**(#17):git 早前已換 scoped token;**密碼本體 2026-08-07 由人在 UI 改畢**,兩 repo `git ls-remote` 實測 exit 0 才准結票。
- **engine_nv.sh**(#26):從未建造。2026-08-07 人裁**撤**——selftest 與治具刪除,留著一個永遠 NOT-RUN 的正控等於養一個沒人讀的燈。
- **看板第四層**:Forgejo 9.0.3 projects API 404,agent 不能驅動;改用 milestone,缺口寫在
  `.agents/skills/forgejo-delivery-loop/modules/delivery-mechanism.md` §7。
- **跨 repo `Closes #N` 自動關閉**:仍未實測,故仍不宣稱(本輪的關票全部由顯式 API PATCH 完成,
  不是靠 commit 訊息觸發——這一點刻意不含糊)。
- **CQ／PU 由 record-only 升 blocking**:**觸發條件 2026-08-07 已成立**——第一個 admitted tracer
  (ts-skill-bettor#1,GCR-SLICE-02)走完真實旅程並產出 admission-result@v1。升級本身**尚未做**,
  這條從「尚未發生」改記為「已到期未做」,開票 arena#32 追。兩者在帳上不能長得一樣。

## 4. 過程中的事故與修正(留帳而非美化)

1. **人閘誤觸**:dry-run 一支「交人執行」的刪除腳本時,`sh <script>` 外層不含 rm token,繞過了
   Tier-2 刪除閘並真的刪了三個子樹。未 commit,`git reset --hard` 全復原。修正:腳本加
   `ISSUE16_HUMAN_ADMIT=1` 守衛+負控;教訓入全局側門記憶。
2. **twin-race**:主 session 與子 agent 平行跑同一 playbook,互砍 worker、共用 log 互相截斷、
   重複燒模型開銷。receipt 碰撞護欄與 git 仲裁守住一致性。教訓:單一 owner。
3. **驗證面不完整**:移除等價 pair 後只跑 checker(綠)沒跑比對套件,漂移隨 commit 出去,下一輪
   全閘掃描才抓到。教訓:checker 綠 ≠ gate suite 綠。
4. **無界 treadmill**:wiki verifier 每輪生新題,all-PASS 不可終止(實測 8→3→2)。停損編進機制:
   PARTIAL-only 遞延 backlog,FAIL 恆紅,receipt 記遞延數。
5. **agent 以等待句收尾**:三次子 agent 掛好 monitor 就終結回報。收尾由主 session 接管。

6. **截斷普查冒充完整普查**:查引用時 `git grep` 後面接了 `head -30`,真實清單 12 筆,漏掉 6 個活引用。
   #26 的刪除腳本前置擋下才發現。教訓:枚舉引用永不截斷——被截斷的普查與完整的普查長得一模一樣,
   直到下游有人不同意。
7. **回釘順序錯導致靜默劣化**:先改記憶體裡的登記表、後寫檔,而 checker 從磁碟讀,於是算出來的 payload
   仍帶著 stale 條目,兩個狀態旗標被釘成劣化值(`runtime_boundary_coverage_complete` True→False)
   ——**而套件照樣 PASS**。它被抓到不是因為閘紅了,是因為人看 diff 覺得「這不是計數、是旗標變差」
   而去重算。暴露出宣告值無人斷言的缺口(#31)。
8. **變異對照本身寫壞**:`sed` 把 preview 與 canonical 兩邊都改成同一個值,兩者仍相等,閘自然回 passed。
   教訓:負控要先證明它真的只動到單一變因,否則它證明的是別的事。
9. **修在發現處而非所有存在處**:explicit-null 的 `dict.get` 缺陷在 audit renderer 修過一次,
   姊妹工具 `delivery_sync` 的兩份副本都還留著,直到真跑 sync 才炸出來。本輪已同日一起掃兩側。
10. **反引號被 shell 吃掉**:用 `python3 -c "…"` 改文件時,雙引號字串裡的反引號是命令替換,
   於是寫進帳的段落少了每一個 code span。改用落檔腳本重寫。小,但同型:**在 shell 裡拼字串就是在拼運氣**。

## 5. 這條線怎麼繼續

`python3 scripts/gates/check_delivery_receipt.py --line bettor-arena-migration` 取上下文;
open issues 走 forgejo-delivery-loop 的執行循環(隔離工作面→tdd→code-review→PR `Closes #N`);
漂移開新 issue 掛同 milestone,不夾帶進進行中的 PR。
