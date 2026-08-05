# defense-form-ssot — 終極防禦形態 SSOT 歸屬索引(誤改防護地圖)

> **這是索引不是副本**——每個提示詞/判斷邏輯的真相留在它的真檔,本圖只**指針**。
> 抄任何提示詞/邏輯內文進來=雙圖漂移(fold-in 不變量 6:fold 是最大漂移源)。
> **改任一階段 skill 前先查此圖**:看該階段的資料流歸誰、判斷邏輯住哪、提示詞 SSOT 在哪、
> 哪支物理閘守它——防把閉環架構或提示詞誤改/誤簡化。
> **物理遵守**:本圖「§指針清單」由 `scripts/check_ssot_index.py` 機械驗——
> 懸空指針(有人搬/刪 load-bearing 檔沒更新本圖)=漂移,exit 3 抓出。
> **三層分工(不重複)**:迴圈層 SSOT 索引=`harness-wiki`(4 迴圈資料流/閘/提示詞);
> skill 業務關係=`panorama.md`;本圖=**防禦層(物理閘全表=§A)+ skill 階段的 SSOT 歸屬**,
> 指向前兩者不抄。

## §A 防禦形態:物理閘全表(每閘守什麼 · 物理檔 · gcr 組件映射)

> 「層」欄=**何時跑**(執行契約,詳見 §C);與「守什麼」=**驗什麼**正交,別混為一談。
> **本節刻意不寫閘數**:計數複述=無人維護的第二份事實。實錨=標題與 `skill-authoring/SKILL.md`
> 名片曾長期掛「8 物理閘」,而本表當時已 12 列、`GATES` 已 18 支。要現值就數:本表的資料列,
> 或 `check_all_skills.py` 的 `GATES`(層歸屬的可執行面)。兩者都機械可數,散文不是。

| 物理閘 | 守什麼 | 物理檔(SSOT) | 層 | gcr 組件映射 |
|---|---|---|---|---|
| 結構閘 | 官方 spec(name≤64/desc≤1024/body≤500/禁保留字) | `scripts/check_skill_conformance.py` | L1 | gcr validator |
| 名片閘 | 全景圖名片 vs skill 目錄無漂移 | `scripts/check_card_sync.py` | L1 | skill-bettor 獨有 |
| 索引閘 | **本圖指針無懸空 + §C 分層完備性(SSOT 歸屬防漂移)** | `scripts/check_ssot_index.py` | L1 | skill-bettor 獨有(本次新增) |
| 排版閘 | 拆行不拆量(內容保全,改版時) | `scripts/check_reflow.py` | per-change | skill-bettor 獨有 |
| fluff閘 | no-op 無錨散文(已接常設) | `scripts/check_fluff.py` | L1 | gcr no-ops purger |
| 注入閘 | 腳本執行半徑(憑證/隱藏字元/外呼)(已接常設) | `scripts/check_dist_safety.py` | L1 | gcr safety |
| 憑證閘 | .claude/skills SKILL.md 硬編碼憑證常量 | `scripts/check_leak_inline.py` | L1 | gcr safety(P12,補 dist_safety 只掃 families 缺口) |
| case閘 | eval case 品質(弱斷言/schema/rubric)(已接常設) | `scripts/check_case_baseline.py`(--family 串聯) | L1 | gcr validator **部分**(驗 expect.yaml,非 cases.json;無 gcr happy/negative 二分——模型不同) |
| 退役閘 | 增益被 model 覆蓋→退役候選 | `scripts/check_ablation_retirement.py`(--family 串聯) | L3 | gcr ablation |
| route-packet閘 | unknown-discovery-composer skill-local cases.json 產物契約(10-20、trigger 5+5、polarity 5+5、四象限、actor/validator/admit/failure edge) | `scripts/check_unknown_discovery_routes.py` | L1 | skill-bettor 獨有(工程編排 skill 行為閘) |
| parity閘 | feedback 必達每個沙盒的每個 driver(防 cp-r 擴散) | `scripts/check_driver_feedback_parity.sh` | L1c | skill-bettor 獨有 |
| preflight閘 | engine PROGRESS 契約(合規不誤傷/違規要擋/dry-run 豁免) | `loop_wiki/engine_selftest.sh` | L1 | skill-bettor 獨有 |
| 目標閘 | SKILL.md 順序詞/目標導向(**WARN-only 不擋**,與 fluff 對稱的另一半 linter) | `scripts/check_goal_oriented.py` | L1 | gcr P9 目標導向 |
| 放置閘 | 新檔/新目錄對映 `ARCHITECTURE.md` §2 槽位(鐵律 6 的唯一機械錨) | `scripts/check_placement.py` | L1 | skill-bettor 獨有 |
| commit訊息閘 | commit 訊息的 GCR 分子化血緣契約。**opt-in**:訊息含 `Intent-Slice: GCR-SLICE-NN` 才套全契約,一般訊息直接放行 | `scripts/validate_molecular_commit_message.py` | L1 | gcr git_gate(訊息可追溯面) |
| Forgejo 路由閘 | 大迴圈不得直接 mutation、小迴圈 admission／operator／platform 路由、正負 trigger 邊界與 secret 欄位拒絕 | `.claude/skills/forgejo-loop-ops/scripts/route.ts --selftest` + skill-local `cases.json` | per-change | skill-bettor 本機 Forgejo 操作橋 |

> **共享 vs domain 分層(2026-07-20 架構校正)**:防禦閘=**repo 級共享**(`scripts/`,演算法
> domain-agnostic);family 靠 `--family <name>` **自行串聯**(不埋在某 family)。family eval 引擎
> (`runner.py`/`judge.py`/cases)才屬 domain,留 `families/<f>/evals/`。check_all_skills 泛型發現
> 每個有 evals/cases 的 family 串聯,非硬編碼(新 family 自動覆蓋)。
> 表現閘(runner --compare G1-G3)/畢業判官(judge.py+Opus fresh)/holdout 一次性/ablation_retirement
> =**op-time/畢業段**,非常設閘。
> `unknown-discovery-composer` 套用 GCR 機制的順序計畫=
> `docs/plans/2026-07-22-unknown-discovery-gcr-order/00-gcr-mechanism-order.md`;
> 該計畫明確區分「route-packet deterministic gate 已完成」與「A/B L2 行為消融未完成」。
> 難度稀釋閘(`scripts/check_difficulty_gate.py`,gcr git_gate 真重建,補 G1-G3 對新易 case 灌水盲點)
> =**常設**(2026-07-21 接進 check_all_skills;per-family 用 discover_difficulty_pair 對 evals/baselines
> 同 track 兩快照回溯稀釋審計)。
> **本表「層」欄 ≠ `GATES` 的 `layer` 欄**(同名兩義,對照時必踩):本表答「何時跑」(層契約);
> `GATES.layer` 只答「該表的泛型迴圈跑不跑它的閘本體」。故放置閘/commit訊息閘/目標閘在本表是 L1
> (每 commit 真跑),在 `GATES` 卻是 `layer=None`——它們由 hook 直呼或由專用 invoker/linter 迴圈跑,
> 登記進 `GATES` 只為納入自證覆蓋集。語義定義在該表頭注,不在此複述。
> 一鍵入口=`scripts/check_all_skills.py`(委派常設閘+映射)。動態注入機制(`!`cmd``/
> `context: fork`)官方形態=`external-verify/modules/verified-truth.md` C6。
> **常設 SKILL.md linter(逐檔迴圈掃)**:fluff/goal_oriented 由 check_all_skills 對每支 SKILL.md
> 逐檔迴圈掃(憑證閘則目錄掃一次),goal_oriented=WARN-only 不擋(fluff FAIL-level 擋)。
> **commit 時物理遵守**:`.githooks/pre-commit` 每次 commit 跑 check_all_skills+placement,
> 全綠才准 commit(啟用=`git config core.hooksPath .githooks`;禁 --no-verify 繞)。
> **gcr 組件映射的等價強度已機械量測(2026-07-21)**:上表「gcr 組件映射」欄非名對名宣稱——clc 迴圈
> (`loop_wiki/clc/`)把 8+ 閘 × gcr 12 機制逐行為讀碼/跑驗,得**全景行為真等價 56.4%(22/39)**:架構同源
> (artifact-alive 100%)、物理非同一(gcr 的 P10 爬蟲/P12 200字 linter/P8 三維網格仍未做;
> happy-negative 5+5、10-20 cases、Levenshtein 近重複硬阻斷已於 2026-07-22 落地)。external-verify 另證 gcr 藍圖源自 Philipp Schmid「Don't Ship Skills
> Without Evals」+SkillsBench(arXiv:2602.12670)非幻覺——故本 repo 與 gcr **同源自 Schmid 非誰抄誰**;
> gcr 的 `createSession`/`@google/gemini` 才是幻覺符號(真=`interactions.create`/`google-genai`)。
> codex×agy 對抗審計×Opus fresh 判官拆穿一個 false-present(near-dup WARN≠硬阻斷)、頂住一個誤 refute
> (purge_loop 骨架級真等價)。**已解:gcr 等價強度=56.4% 全景可重跑量測。禁回退用「名對名宣稱等價」。**
> 錨=`bash loop_wiki/clc/verify.sh`(exit 0,報六率)+ `loop_wiki/clc/EQUIVALENCE-VERDICT.md`(三軸帳,不抄)。

## §B skill 階段 SSOT 歸屬(改階段前查:提示詞住哪 · 判斷邏輯住哪)

- **提示詞 SSOT**:每支工程 skill 的提示詞=**它自己的 `SKILL.md` body**(改階段行為=改那個檔,
  非改本圖;本圖只指到它)。know-why 在各自 `modules/`。
- **判斷邏輯 SSOT**:結構性=對應物理閘(§A);語意性=判官 dispatch(落 `dispatches/`,
  慣例 SSOT=sdlc-plan-composer S4)。
- **資料流歸屬**:迴圈類的資料流/收斂閘=`harness-wiki` 組件卡(不在本圖重畫);
  skill 業務上下游=`panorama.md` 名片。
- **誤改防護**:改某階段前,①查本圖 §A 該階段受哪些閘 ②查 harness-wiki 若動到迴圈拓撲
  ③改完跑 `check_all_skills.py`+對應閘。**簡化任何閉環/提示詞前,先確認不是 load-bearing**
  (harness-wiki 不變量+本圖指針=判 load-bearing 的依據)。

## §C 執行分層契約(何時跑 · 什麼刻意不接 · 為什麼)

> §A 答「驗什麼」,§C 答「何時跑」。兩者正交:過了放置契約(檔案放哪)不等於過了層契約(何時跑)。
> 執行面=`scripts/check_all_skills.py` 的 `GATES` 表(直譯器/自證宣告/層歸屬各只寫一處);
> 本節=契約與理由,**不複述**各腳本做什麼(那在各腳本頭注)。

### 覆蓋集判定原則(這條比清單本身重要)

> **自證覆蓋跟隨「自動執行者」,不跟隨「腳本存在」。**

一支腳本進「閘的閘」,若且唯若它有自動執行者(hook / aggregator / engine.sh 自動呼叫)。
沙盒內組件的自動執行者是該沙盒自己的 `verify.sh`,自證歸該沙盒、不上升——這一條同時生成了
下方整張「刻意不接」表,不是逐支拍腦袋。**校準**(全局 CLAUDE.md「孤兒≠該立刻接」):
無差別把「§分層宣告」表列的每一支都接=製造誤報與慢閘,是另一種失敗。

### 四層

| 層 | 觸發 | 內容 | 預算 | 硬約束 |
|---|---|---|---|---|
| **L1 commit-always** | 每 commit,無條件 | 常設閘全體(parity 除外) | ≤8s(**實測 5s**,原 14.8s) | 純 repo 靜態狀態;零 LLM;零網路 |
| **L1c commit-on-touch** | staged diff 命中才跑 | ①閘的閘 ②parity 全掃 | ≤12s,且只在真改了東西時付 | 謂詞寫在 hook(唯一知道 staged diff 的地方),內容留在 aggregator |
| **L2 push/週期** | `git push`(remote 生效後)+ 手動 + product-ops 晨檢 | L1 ∪ L1c ∪ 沙盒正控 ∪ 消融引擎 run-test | ≤4min | 必須是 L1 的**真超集** |
| **L3 on-demand** | 人顯式起火,人在場 | 真消融 / `purge_loop` / `runner --set holdout` | 無預算(分鐘～小時、燒額度) | **永不自動觸發**;退役/畢業永遠人 admit |

**跨層硬不變量:閘對 repo 唯讀。** L1/L1c/L2 跑完 `git status --porcelain` 必須與跑之前逐字相同。
2026-07-26 實犯並修:parity 移除 codex-only 濾網後開始 dispatch 全部 24 沙盒,而其中兩支是舊世代
self-looping `run.sh`(自帶 while 迴圈、自呼 verify.sh),被 dispatch 一次就 append 自己的 `PLAN.md`
——一輪全掃讓兩支各多 48 行。修法=隔離中的沙盒**整支不 invoke**(隔離語義是「不跑」,不是
「跑了再忽略結果」)。回歸錨:全掃前後 `git status --porcelain` diff 為空。

**L1c 謂詞**(照抄自 `.githooks/pre-commit`):

```
閘的閘帶: ^scripts/  |  ^loop_wiki/engine.*\.sh$  |  ^\.githooks/
parity 帶: ^loop_wiki/[^/]+/run\.sh$  |  ^scripts/check_driver_feedback_parity\.sh$
```

parity 的正當性:它是**純黑箱跑 run.sh**,不涉 engine、不涉 skill。run.sh 沒動→結果不可能變→
跑它是純浪費(全掃實測 22–25s)。`cp -r` 出新沙盒必然讓 diff 命中 `run.sh`,它要守的擴散面
完整落在謂詞內。**淨效果**:常態 commit 14.8s→5s;改防禦腳本 ≈7s;改 run.sh ≈30s。
閘的閘從「永不執行」變成「每次改到它就執行」——**同時**降成本與補覆蓋,不是取捨。

**parity 的 codex 分支:CI 上恆 SKIP(覆蓋缺口,明文而非靜默)**。本閘用一個 macOS 家目錄下的
絕對路徑探測 codex plugin 在不在,而 `skill_ci.yml` 跑在 ubuntu-latest ⇒ **CI 上每個沙盒的 codex
分支都 SKIP,且整體仍 exit 0**(2026-07-26 真跑實錨:把該路徑換成不存在的值模擬 ubuntu,
兩沙盒皆 `codex: SKIP`、綠)。故 **CI 綠 ≠ codex 分支被驗過**;codex 的 parity 覆蓋只在裝了該
plugin 的本機成立。這條刻意**不修**:該常量與各沙盒 `run.sh` 裡真正 exec 它的那份必須逐字相同,
改成 glob 會製造不對稱(探針找到新版、run.sh 仍指舊版 → 無 capture → 以錯誤診斷判 FAIL 擋 commit,
已真跑證偽)。理由全文在該腳本頭注,不在此複述。

### 閘的閘的雙判準

1. 硬判準=`exit == 0`(唯一全體共有的語義)。
2. 第二判準=stdout/stderr **任一行**含字面 `SELFTEST GREEN`(**不是末行**——`check_dist_safety`
   的摘要行之後還會印 hollow 靶的 3 行 FAIL)。
3. 範圍=**只對覆蓋集內的腳本**要求,不是 repo 裡每一支腳本。不留 grandfather 清單。

**為何保留關鍵字**(它買到 exit code 買不到的東西):威脅模型是**意外閹割**——某支 selftest 的
body 被早退/註解掉會安靜 exit 0,印不出 token 則抓得到。對抗式作者確實印 token 比 `return 0`
容易造假,但那條靠 planted-defect 齒測、不靠本層。齒測錨:重建當天的三靶探針(good-py / good-sh /
gutted-no-token)證實 exit-code-only 會放過 gutted 那支,加 token 後轉紅。

### 「刻意不接」清單(沒有明文,下一個人會重接一次)

| 腳本 | 判定 | 理由 | 不接的代價 |
|---|---|---|---|
| `check_reflow.py` | per-change | 需 diff 基準(`--git HEAD`),零參數常設無意義 | 改版時忘了跑=拆行拆量無人擋;可接受(authoring 流程內有指針) |
| `check_behavior_conformance.py` | 不接-歸屬clc | 吃 clc 語料,離開沙盒無輸入;`clc/verify.sh` 已跑其自證 | 零——已被沙盒層覆蓋,上升=重複執行 |
| `check_equivalence_claims.py` | 不接-歸屬clc | 同上(`clc/selftest.sh`+`verify.sh`) | 零 |
| `check_equivalence_conformance.py` | 不接-歸屬clc | 同上 | 零 |
| `check_extraction_recall.py` | 不接-歸屬clc | 同上 | 零 |
| `check_precision_gate.py` | 不接-歸屬clc | 同上;另有 `clc/rebuild/` 重建對照 | 零 |
| `diff_executor.py` | 不接-歸屬dx | 需兩實作+輸入語料;`dx-adversarial-fix/verify.sh` 已跑 | 零 |
| `decision_router.py` | 不接-歸屬dx | 需人裁後的 `decision.json` 才有東西可路由 | 零 |
| `check_narration.py` | 不接-歸屬dx | live decision server 的 POST 前置閘,非 repo 靜態狀態 | 零 |
| `validate_molecular_commit_lineage.py` | 不接-歸屬evolve | 需 GCR molecular commit 上下文;該沙盒 `verify.sh` 已跑 | 零 |
| `build_iter_feedback.py` | **閘本體不接;自證接 L1c** | 閘本體 op-time(需 `verify.iterN.out`);但自證是靜態的、<0.2s、零 LLM | 若連自證也不接:改壞它只在下次迭代才發現,症狀是「提示變空」=**靜默退化** |
| `check_codex_turn_health.py` | 同上 | 同上(讀 codex turn 產物) | 同上;codex 判活失效=迴圈假活 |
| `runner.py` | 同上 | 閘本體真跑燒 LLM,**絕不能**進 commit | 同上 |
| `judge.py` | 同上(隨 runner) | 判分引擎 | 同上 |
| `check_ablation_retirement.py` | L3 | 消融燒 LLM + 退役永遠人 admit(`weekly_audit.sh` 明文只指路不 invoke,避免有人隨手跑就燒額度) | 退役候選晚一週浮現;可接受(退役本就是人閘) |
| `ablation_audit.sh` | L3(**只指路不 invoke**) | 同上;它硬性要求 `--as-of YYYY-MM-DD`、明文禁預設 today,自動跑就得由呼叫端捏日期 | 同上 |
| `purge_loop.py` | L3 | 頭注自陳「on-demand 昂貴工具」;逐行刪→跑家族 eval,成本量級分鐘/小時 | 無——它本來就人起火 |
| `runtest_ablation_dualarm.py` | L2 | 零 LLM(≈1.7s),驗的是消融引擎不是 repo 狀態 | 消融引擎壞掉只在真消融時發現,代價=一次燒掉的額度 |
| `loop_wiki/engine_nv_selftest.sh` | L2 | 驗 `engine_nv.sh` 的 N-variant dispatch;該 wrapper 是**人啟動的兩相位工具**,每次使用人都在場 | 誤改只在下次真用時發現,而那時人在場;為手動工具付 ≈18s/commit 不划算 |
| 24 支沙盒 `selftest.sh` | L2 | 一沙盒一正控(good/hollow 雙臂),與 repo 靜態狀態無關;合計 ≳2min | 見下方隔離帶 |
| `loop_wiki/engine_selftest.sh` 的**自證** | **刻意不自證** | 它整支就是那支 selftest(不解析參數:`--selftest`/`--bogus-flag`/零參數 rc 皆 0)。對它跑閘的閘=同義反覆 | 零;誠實宣告不自證好過綠一個空洞 |

### runner 不是閘:兩支的層標要反過來讀

「§分層宣告」裡有兩支不驗任何 repo 事實,故不在 §A。它們的層標**讀作「我是這層的載體」,
不是「我是這層跑的一道閘」**——同一欄兩種語義,這是本契約最容易讀反的一處。

| 腳本 | 層標 | 層標的意思 | 不接的代價 |
|---|---|---|---|
| `scripts/check_all_skills.py` | L1 | **我是 L1 的執行器**(標準入口)。它只委派+彙總,自己不驗任何東西 | **未被緩解**:它沒有自己的自證(`--selftest` 是 `--layer meta` 的別名=跑**別人**的自證,不是驗自己)。它靜默壞掉(如吞例外恆綠)整層一起假綠,而閘的閘照樣報綠。這是覆蓋圖上唯一的自指缺口,不是疏漏而是尚未解 |
| `scripts/weekly_audit.sh` | L2 | **我是 L2 的載體之一**,不是 L2 跑的一道閘。它自己就是呼叫者:內容=`check_all_skills.py --layer push` + 消融只指路不 invoke。標 L2 是說「跑我 == 跑完 L2」,不是「L2 會跑我」 | 它壞掉=週期審計靜默不跑。現況無 remote/無 cron,L2 本就人驅動(見下方「週期語意的誠實處置」),人在場會當場看到它沒輸出;故代價目前有界,remote 生效後由 pre-push 接手才是真載體 |

### known-red 隔離帶(全部帶到期日;到期自動失效轉 FAIL)

**自我清理只在閘仍會 invoke 目標時成立**——不是每條隔離帶都有,兩種形態的偵測時機不同:

- **invoke 後看 rc**(`check_all_skills.py` 的 `SANDBOX_SELFTEST_QUARANTINE`):沙盒照跑,
  rc==0 就 SURFACE「已轉綠,請移除」。**轉綠當天就會被喊。**
- **整支不 invoke**(`check_driver_feedback_parity.sh` 的 `PARITY_QUARANTINE`):隔離語義是
  「不跑」(理由=上方唯讀不變量,跑一次就弄髒工作樹),故**轉綠無從偵測**。那支「已轉綠請移除」
  的分支在隔離窗內**不可達**,只有到期後才走得到:到期 → 不再豁免 → 真跑一次 → 若綠才喊移除。
  實測(2026-07-26):把一支已綠的沙盒改名成隔離帶內的名字餵給本閘,輸出只有「隔離中,不 invoke」
  與 `exit 0`,零轉綠提示。

故對第二種,**到期日是唯一的偵測時機,不是保險**——它同時扮演「重新評估」與「唯一喚醒」。
沒有到期日的隔離帶會腐爛成永久豁免。

**本表受 `scripts/check_ssot_index.py` ③ 雙向驗**(L1,每 commit):閘裡寫死的每個
`*_QUARANTINE` (目標, 到期日) 必須在下表有同時含兩者的一列,反向亦然。日期有兩份副本
(閘 + 本表)——只活在閘裡沒人看得見,只活在表裡不會過期,兩份無閘同步則本節退回散文。

| 項目 | 到期 | 為何隔離而非修 |
|---|---|---|
| `evolve-unknown-discovery-plan-truth/selftest.sh` | 2026-08-09 | golden-seed 清單鎖(`files_planned` 1085→1095 等)是**活庫存計數**,repo 每加檔就漂;重新 blessing 屬該沙盒 owner,且其 `CLAUDE.md` 非協商項 6 明禁為了讓 target 過而改 `selftest.sh` |
| parity: `spawn-aie-holdout-cases` / `spawn-cases-semantic-traps` | 2026-08-09 | 移除 codex-only 濾網後新覆蓋面抓到的**真缺口**:兩支是舊世代 self-looping `run.sh`(簽名 `run.sh <driver>`,不吃 target/feedback 參數),故 feedback 到不了 driver;且 dispatch 一次就寫自己的 `PLAN.md`,故**整支不 invoke**。要不要遷到 engine.sh dispatch 世代是人裁 |

### 標準入口(單一命令;擴充既有 aggregator,不新造檔)

```bash
python3 scripts/check_all_skills.py                  # 無參 == --layer commit
python3 scripts/check_all_skills.py --layer meta     # 閘的閘(--selftest 為向後相容別名)
python3 scripts/check_all_skills.py --layer push     # L2 真超集
python3 scripts/check_all_skills.py --layer full     # push ∪ engine_nv 正控
```

**`full` 的紅線**:`full` **永不**包含燒額度的東西(`--real` 消融、`runner --set holdout`、
`purge_loop`)。那些是 L3,只有人打得出來的命令。一條指令跑完「該跑的」,但「該跑的」不含花錢的。

**週期語意的誠實處置**:本地無 remote、無 launchd,兩個 workflow 都是死碼。**不為了「自動」去裝
launchd**——那是新機制、新失敗模式、新孤兒。L2 的載體=`product-ops` 晨檢 runbook 的一行手動命令,
加上 remote 生效後自動活化的 pre-push。明文寫下「L2 目前是人驅動」比假裝它自動要好。

## §分層宣告(機械驗;check_ssot_index.py 驗每支有自證能力的腳本恰好宣告一次)

> 新增 `scripts/` 閘/自證腳本時 additive 加一行(層或「不接-歸屬X」);漏加=孤兒,exit 3。
> 這是整份層契約唯一真正防止「下一個人重接一次」的機制,其餘都是文件。

```defense-layers
scripts/check_skill_conformance.py	L1
scripts/check_card_sync.py	L1
scripts/check_ssot_index.py	L1
scripts/check_unknown_discovery_routes.py	L1
scripts/check_case_baseline.py	L1
scripts/check_dist_safety.py	L1
scripts/check_leak_inline.py	L1
scripts/check_fluff.py	L1
scripts/check_goal_oriented.py	L1
scripts/check_difficulty_gate.py	L1
scripts/check_placement.py	L1
scripts/validate_molecular_commit_message.py	L1
scripts/check_all_skills.py	L1
scripts/check_cross_repo_parity.py	L1
scripts/check_isolation_selfsufficiency.py	L1
loop_wiki/engine_selftest.sh	L1
scripts/check_driver_feedback_parity.sh	L1c
scripts/weekly_audit.sh	L2
scripts/runtest_ablation_dualarm.py	L2
loop_wiki/engine_nv_selftest.sh	L2
scripts/check_ablation_retirement.py	L3
scripts/ablation_audit.sh	L3
scripts/purge_loop.py	L3
scripts/check_reflow.py	per-change
scripts/build_iter_feedback.py	不接-歸屬engine(自證接L1c)
scripts/check_codex_turn_health.py	不接-歸屬engine(自證接L1c)
scripts/runner.py	不接-歸屬engine(自證接L1c)
scripts/judge.py	不接-歸屬engine(自證接L1c)
scripts/check_behavior_conformance.py	不接-歸屬clc
scripts/check_equivalence_claims.py	不接-歸屬clc
scripts/check_equivalence_conformance.py	不接-歸屬clc
scripts/check_extraction_recall.py	不接-歸屬clc
scripts/check_precision_gate.py	不接-歸屬clc
scripts/diff_executor.py	不接-歸屬dx
scripts/decision_router.py	不接-歸屬dx
scripts/check_narration.py	不接-歸屬dx
scripts/validate_molecular_commit_lineage.py	不接-歸屬evolve沙盒
scripts/build_equivalence_matrix.py	不接-歸屬跨repo矩陣報表(非閘;自證接meta)
scripts/audit_peer_session_diff.py	不接-歸屬併發人裁報表(非閘;自證接meta)
.claude/skills/forgejo-loop-ops/scripts/route.ts	per-change
```

**`check_cross_repo_parity.py` 為何是 L1 而不是 L1c**:它的結果隨**任何**共用面檔案變動而變,
而共用面涵蓋 `.claude/skills/`、`loop_wiki/`、`ARCHITECTURE.md`——幾乎每個 commit 都碰得到,
寫謂詞等於「永遠命中」。實測 0.42s,直接無條件跑比維護一個恆真的謂詞誠實。
對側 checkout 不在時走 SKIP exit 0(理由見 ARCHITECTURE.md §12),故它不會讓乾淨 clone 變紅。

**`check_isolation_selfsufficiency.py` 為何是 L1 而不是 L1c**:掃描域=`families/` 的 install copy 面,
而家族資產正是每日演化 op 的高頻改動面——謂詞近乎恆真。純位元組唯讀掃描 191 支,實測 <0.1s,
無條件跑比維護一個恆真謂詞誠實(同 parity 的理由結構)。**它守的不變量本體不住這裡**:
基座 6 環境自足=`loop-harness-standard` 鐵律 7 + `modules/harness-spec.md` §4.6(判準/誤判面/
偵測邊界全文在該處,本檔只登記層歸屬)。現況 31 支逃逸走閘內帶到期日隔離帶,預算只准縮不准漲。

**`build_equivalence_matrix.py` 為何不接任何層**:它產報表不下判決;第③格(真跑 exit 0)
在本 repo 結構上拿不到(不執行 .ts,ARCHITECTURE.md §11),把一個永遠只有 ①② 的東西當閘,
就是在把「檔案存在」冒充「已證等價」——那正是它要揭發的病(見 §13)。自證仍接 meta 層。

## §指針清單(機械驗;check_ssot_index.py 逐條驗存在,懸空=漂移 exit 3)

```ssot-pointers
scripts/check_skill_conformance.py
scripts/check_card_sync.py
scripts/check_ssot_index.py
scripts/check_reflow.py
scripts/check_fluff.py
scripts/check_dist_safety.py
scripts/check_all_skills.py
scripts/check_placement.py
scripts/check_case_baseline.py
scripts/check_unknown_discovery_routes.py
scripts/check_ablation_retirement.py
scripts/check_difficulty_gate.py
scripts/check_equivalence_claims.py
scripts/check_equivalence_conformance.py
scripts/check_behavior_conformance.py
scripts/runtest_ablation_dualarm.py
scripts/ablation_audit.sh
scripts/purge_loop.py
scripts/check_extraction_recall.py
scripts/check_codex_turn_health.py
scripts/build_iter_feedback.py
scripts/check_driver_feedback_parity.sh
loop_wiki/engine_selftest.sh
scripts/check_precision_gate.py
scripts/check_fullcorpus_extraction.py
scripts/diff_executor.py
scripts/decision_router.py
scripts/check_narration.py
scripts/runner.py
scripts/judge.py
scripts/check_leak_inline.py
scripts/check_goal_oriented.py
scripts/validate_molecular_commit_message.py
scripts/check_cross_repo_parity.py
scripts/check_isolation_selfsufficiency.py
scripts/build_equivalence_matrix.py
scripts/audit_peer_session_diff.py
.githooks/commit-msg
.claude/skills/harness-wiki/SKILL.md
.claude/skills/skill-authoring/modules/panorama.md
.claude/skills/skill-authoring/modules/authoring-clauses.md
.claude/skills/skill-authoring/modules/fluff-blacklist.txt
.claude/skills/external-verify/modules/verified-truth.md
.githooks/pre-commit
.githooks/pre-push
.github/workflows/skill_ci.yml
.github/workflows/weekly_audit.yml
scripts/weekly_audit.sh
docs/plans/2026-07-22-unknown-discovery-gcr-order/00-gcr-mechanism-order.md
.claude/skills/forgejo-loop-ops/SKILL.md
.claude/skills/forgejo-loop-ops/cases.json
.claude/skills/forgejo-loop-ops/scripts/route.ts
loop_wiki/evolve-perfect-seed-repo-factory/verify.sh
loop_wiki/evolve-perfect-seed-repo-factory/src/contracts.ts
loop_wiki/evolve-perfect-seed-repo-factory/src/verify_generated_repo.ts
loop_wiki/evolve-perfect-seed-repo-factory/templates/repo/.agents/skills/seed-repo-operator/SKILL.md
```

> 清單=load-bearing SSOT 真檔(物理閘+關鍵邏輯+索引地圖)。新增 load-bearing 檔時 additive 加一行
> (checklist 8 同動作);搬/刪任一檔必同步本清單,否則 check_ssot_index exit 3。
