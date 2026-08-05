# Module: dr-to-mvp — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`dr-to-mvp`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到 skill-bettor、
> 哪些因為架構前提不同被拿掉/降級、為何不是簡化。與 [loop-harness-standard 的 retarget-map](../../loop-harness-standard/modules/retarget-map.md) 同構——
> 那份處理「工程規範」的移植,本份處理「編排脊椎」的移植,兩者遵同一紀律。

---

## 1. 為何不能逐字複製——antigravity 原版摻了大量它自己的軌跡錨

antigravity 原版 `SKILL.md`＋`reference/guiding-prompt.md` 裡,相當比例是 **antigravity 自己迴圈跑出來的
證成紀錄**:具體 LIVE 錨（`cutplan/`、`autopilot-bridge`＝ix-agy repo）、具體 commit（`b6d196`/`d4f4e35`）、
N×M host×driver 覆蓋帳、cc-20260711 首次端到端。這些是 antigravity 自己的軌跡,不是可搬的方法論——
逐字複製會:① 引用不存在的脈絡（skill-bettor 沒有 cutplan/ix-agy);② 把不適用的架構前提（2×2 host 矩陣）
搬回來;③ 與 skill-bettor 自己的 worked instance（`families/agent-harness/`）打架。

**本移植只萃取可轉移的脊椎方法論**（R→G→M 定序、兩種 prototype 消歧、DR-is-gap-filler 拓撲、
phase-handoff SURFACE gate、誠實接縫紀律），把 owner 指針重定向到 skill-bettor 本地物,LIVE 錨換成本地真跑。
skill-bettor 未來自己累積的軌跡,記在 `families/*/changelog/`,不繼承 antigravity 的。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| **Phase R owner** `gemini-conversation-research`（S0-S9,研究一個 Gemini 對話） | `proposals/`（DR 隔離區＋schema SSOT）＋ `.claude/skills/dr-research-loop/`（DR 執行）＋ `.claude/skills/judge-loop-chooser/`（D3 adopt 閘） | gcr 是「研究 Gemini **對話**」的輸入模態,antigravity 專屬;skill-bettor 的研究輸入＝下注訊號→proposals（MVP 期人工挑題）。**輸入模態不適用,不需 port 整個 gcr**——只保留「研究到可信基底」的方法論,重定向到 proposals 管線。 |
| antigravity D1（落地驗證,確定性錨＞LLM 說詞） | proposals **T0 四閘**（`loop_wiki/_template_dr/scripts/check_*.py`,exit 10=verified） | 「確定性錨＞LLM」＝機械驗證器判定,概念一對一;skill-bettor 的機械閘＝該骨架四支 checker,schema SSOT＝`proposals/README.md`。 |
| antigravity D2（SYNTHESIS 真實度計分卡＋等價物矩陣） | proposal **adopted**（judge-loop-chooser D3 審過:意圖漂移錨＝`origin_question`、Half-Bridge 撤回） | 「合成可信基底」概念一對一;skill-bettor 用 proposal 生命週期 `draft→verified→adopted` 承載,adopt 閘＝D3。**「SYNTHESIS」一詞在本脊椎泛指「已驗基底」,不強綁 antigravity 的 SYNTHESIS.md 格式。** |
| **Phase G owner** `repo-wiki-converge`（KU→L1 wiki） | **拿掉,KU→`.claude/skills/repo-agent-native/`（L2 不變量）直接** | skill-bettor 未 port `repo-wiki-converge`;KU 象限「讀源可答」直接走 repo-agent-native 抽業務不變量即可,L1 wiki 中間層對冷啟動非必需。需要時再 cross-ref antigravity,不預 port。 |
| **Phase G 拋棄式 prototype** `~/.claude/skills/prototype` | **原樣映**（user-level,兩 repo 皆外部） | 全局 skill,不在任一 repo;D4 throwaway 用它、答完刪的紀律通用,無需改。 |
| **Phase G/M** `bash kb-ingest/setup-prototype.sh [--mvp] <plan> <repo>` | `cp -r loop_wiki/_template loop_wiki/<loop>`（八大基座骨架實例化）＋ `loop_wiki/engine.sh <loop> --driver claude\|agy`（迭代/停損引擎） | skill-bettor 無 `kb-ingest/`;八大基座骨架＝`loop_wiki/_template/`（`cp -r` 實例化,retarget-map for loop-harness-standard §4 已 disk 驗證存在）,迴圈引擎＝`engine.sh`（engine=迭代/stop-loss;`_template/run.sh`=單發 dispatch,不自帶迴圈）。`--mvp` 旗標消失＝MVP 路徑本就是 `_template`+`engine.sh`,拋棄式路徑走 user-level prototype skill。 |
| **Phase M owner** `loop-harness-standard/modules/mvp-builder-and-adlc-equivalents.md §2` | `.claude/skills/loop-harness-standard/modules/harness-spec.md`（八大基座卡）＋ `ARCHITECTURE.md §3`（at-a-glance） | skill-bettor 的 loop-harness-standard port 把八大基座卡放進 `harness-spec.md`（該次移植改寫詞彙:scripts/tests fixtures→family evals/runner.py 等,見其 retarget-map §2）。Phase M owner 指針換到那裡。 |
| **迴圈驅動** `run.sh <driver> <target>`（大迴圈=D12 engine） | `loop_wiki/engine.sh <loop> --target <path> --driver claude\|agy`（`exit 10`=awaiting-human-admit） | driver 選型從 N×M 矩陣降為**單軸**（見下）;engine 語義（迭代到過關×停損×人 admit 停點）一對一。 |
| **homing** 搬離 gitignored `/prototype/` → 上 remote/入 `/repo/`/owner skill `reference-impl/`（ix-agy 型） | **families 型 homing** → `families/<f>/shared/runtime/<mvp>/`（隨家族 checked-in） | skill-bettor＝living-skills 家族 repo,homing 目的地明確＝對應家族的 `shared/runtime/`（訂閱者 git pull 即得）。antigravity 的三型 homing 譜（remote／ix-agy reference-impl／families）本脊椎只保留 **families 型**（本 repo 唯一適用型,完整帳＝`families/agent-harness/changelog/2026-07-12.md`）;其餘型＝antigravity-only（單 repo 家族場景無對應物）,見 antigravity 源不在本 repo 重述。 |
| **2×2 host×driver 矩陣**（Claude Code／Antigravity CLI 雙 host） | **拿掉,降為單軸 driver 選型** | skill-bettor 恆為 Claude Code 單 host,不存在「開這個 repo 的 CLI 換家族」的情境;N×M 覆蓋帳、隔離翻面表整套不適用。架構前提真的不同,非簡化。 |
| **LIVE 錨** cutplan（SC1-17/118 tests）、autopilot-bridge（ix-agy d4f4e35） | **`families/agent-harness/`**（harness-core `7481e78`、evals-gate `613da6e`,homed 進 `shared/runtime/`,verify 綠 117/177） | antigravity 的 LIVE 錨指向它自己的 repo/ix-agy,skill-bettor 對應的本地 worked instance＝那次真跑產兩畢業 MVP＋families 型 homing 的完整帳（`families/agent-harness/{FAMILY.yaml,changelog/2026-07-12.md}`）。**指本地,不複製 antigravity 案例史。** |
| **`pgrep -fl automate.js`**（DR :9333 佔用） | **原樣映,但改為條件式**（Phase R 跑 live 瀏覽器 DR 時才適用） | DR 執行引擎 SSOT 在 dr-research-loop;live browser DR 仍不可與影片管線搶同一 `:9333` 帳號。語料型 Phase R（無新 DR）不觸發此閘。 |
| **判官=Opus／agy=Gemini only／fresh 禁 fork** | **原樣映**（tier-dispatch 概念完全通用） | skill-bettor CLAUDE.md tier-dispatch 同紀律:Opus=判官/畢業(fresh);Sonnet=author;Haiku/Flash=機械(禁 verdict);agy Pro 3.1=DR/複核(只 findings 不 verdict)。無需改。 |
| **PROMPT.md／PLAN.md／CLAUDE.md／verify.sh 命名** | **原樣映**（`loop_wiki/_template/` 已照此建） | 八大基座短名兩 repo 相同;骨架真檔已存在,本移植只把脊椎指針對上。 |

## 3. 拿掉的東西不是「簡化」,而是「不引入不存在的架構前提」

- **能一對一映的映**：R→G→M 定序、兩種 prototype 消歧、DR-is-gap-filler 拓撲、SURFACE handoff gate、
  判官/執行者隔離、dual-score AND 畢業、recipe-not-engine 人 admit——這些與 host 數目無關的脊椎方法論。
- **架構前提不同、真拿掉**：2×2 host 矩陣、隔離翻面表、ix-agy 型 reference-impl homing、L1 wiki 中間層——
  skill-bettor 單 host＋families repo 的事實,不是能力縮水。
- **歷史紀錄、故意不搬**：cutplan/autopilot-bridge LIVE 案例史、`b6d196`/`d4f4e35` commit 錨、N×M 覆蓋帳——
  那是 antigravity 自己迴圈的軌跡,skill-bettor 累積自己的在 `families/*/changelog/`。

## 4. 判別「retarget 成立」的鐵錨（本地真檔,disk 已驗證）

- 八大基座骨架真存在：`loop_wiki/_template/`（CLAUDE.md/PLAN.md/PROMPT.md/run.sh/verify.sh/anti/）、
  `loop_wiki/engine.sh`（迭代/停損引擎,`exit 10`=awaiting-human-admit）。
- Phase R 上游真存在：`proposals/README.md`（schema SSOT）＋ `loop_wiki/_template_dr/scripts/check_*.py`（T0 四閘）
  ＋ `.claude/skills/dr-research-loop/`。
- Phase M owner 真存在：`.claude/skills/loop-harness-standard/modules/harness-spec.md`（八大基座卡）。
- LOCAL worked instance 真存在：`families/agent-harness/`（2026-07-12 兩畢業 MVP＋families 型 homing 完整帳）。

若哪天有人往本 skill 塞回 cutplan/ix-agy 案例史、antigravity 具體 commit 錨,或試圖重建 2×2 host 矩陣
（除非 skill-bettor 真的要接 Antigravity CLI host）,那就是把不適用的架構前提搬回來——擋下。

---

## Sources / Lineage
- antigravity 源：`/Users/neon/antigravity/.agents/skills/dr-to-mvp/`（`SKILL.md` ＋ `reference/guiding-prompt.md`）。
- 移植同批前例：`.claude/skills/loop-harness-standard/modules/retarget-map.md`（工程規範的移植帳,同紀律;
  本脊椎 Phase M 委派的 owner 即該 skill）。
- 本地 worked instance：`families/agent-harness/{FAMILY.yaml,changelog/2026-07-12.md}`（dr-to-mvp 在 skill-bettor 的首個完整帳）。
