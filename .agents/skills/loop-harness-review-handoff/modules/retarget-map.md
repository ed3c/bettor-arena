# Module: loop-harness-review-handoff — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`loop-harness-review-handoff`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到
> skill-bettor、哪些因為架構前提不同被拿掉/降級、為何不是簡化。**本檔額外多一項別的 retarget-map 沒有的義務**:
> 這個 skill 的全部產出就是「交給 reviewer 一份可信的路徑清單」,如果清單裡有一個 phantom 路徑,整個
> skill 的價值就破功——所以下面每一條入口路徑都跑過 `ls`/`test -e` 驗證,不是憑印象抄。

---

## 1. 為何不能逐字複製——antigravity 原版有三種不可搬的東西

antigravity 原版 `loop-harness-review-handoff` 摻了三類這次移植故意不搬的內容:

1. **一份真實跑過的歷史交接稿當「活實例」**:`docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md`。這是 antigravity 自己一次真實 review 交接的產物——skill-bettor 沒有對應的使用歷史,硬搬＝捏造一個從未發生過的本地事件。
2. **antigravity 自己的設計 SSOT 章節編號**(`harness-spec.md` §9❻ tier-dispatch、§9❼ N×M 矩陣、`antigravity-harness-wiki` 的 10 條迴圈組件卡)。skill-bettor 本地移植版 `harness-spec.md` 只有 §1-§5(tier-dispatch 表根本不在這份檔案裡,搬到了 `ARCHITECTURE.md` §5),`harness-wiki` 本地版只有 2 列組件卡——照抄原版章節號會指向不存在或錯誤的內容。
3. **antigravity 自己的踩坑案例代號**(R7 dangling-id、R8 tool-syntax-leak、design-governance slice-1 判官 HOLD)。這些是 antigravity 迴圈跑出來的具體軌跡,skill-bettor 沒有對應歷史,不能拿別人的案例當自己的證據。

本移植只萃取**可轉移的方法論骨架**(6 步確定性程序精神、5 條不變量、fresh-session 隔離原理、reviewer tier 選型的通則、anti-sycophancy/anchored-claims 紀律、session-adjustment 差量交接、審計維度分類的思路),把**指向的內容**全部換成 skill-bettor 已有的真實檔案,拿不到真實檔案的就誠實標「尚無」,不臨時杜撰一個。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| 活實例 `docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md` | **無本地對應,明標「尚無 worked instance」** | skill-bettor 沒有這個 skill 的使用歷史。antigravity 的實例僅作跨 repo 結構參考(SKILL.md/reference/handoff-template.md 已標註),不當本地內容抄。 |
| 入口 curation:計畫意圖 `00-intent-and-knowhow.md`(D1-D9) | `ARCHITECTURE.md`(設計意圖;無 D 編號決策帳本,改用 §1-§11 章節) | skill-bettor 沒有這種計畫階段決策文件,`ARCHITECTURE.md` 本身就是設計意圖 SSOT,已含對映表/八大基座卡/tier-dispatch/人閘清單。 |
| 入口 curation:設計 SSOT `loop-harness-standard` SKILL＋`harness-spec.md` §1-§9、`antigravity-harness-wiki/modules/loop-architecture-ssot.md` | `.claude/skills/loop-harness-standard/{SKILL.md,modules/harness-spec.md §1-§5,modules/evals-design-method.md}`、`.claude/skills/harness-wiki/SKILL.md`(2 列組件卡) | 本地版章節號不同(§1-§5 非 §1-§9),tier-dispatch 表搬到了 `ARCHITECTURE.md` §5,不在 `harness-spec.md` 裡——本檔已在下方逐路徑校正引用。 |
| 入口 curation:canonical 範例 `loop_demo/{agy,claude_agy}` | `loop_demo/claude_agy`(**只此一份**) | `loop_demo/RETARGET-NOTE.md` 已記錄:skill-bettor 恆單 host,只搬融合版 `claude_agy/`,不搬 `agy/`(對它是冗餘子集)。 |
| 入口 curation:pilot 證據 `loop_wiki/design_governance/`＋`loop_wiki/agy_demo/` | `families/pinescript-audit/{evals/,changelog/2026-07-11.md,FAMILY.yaml}` | **不是同類證據,誠實標記為不同種類**:antigravity 的是「harness-engineering pilot」(判官逐輪 finding、fold-back 案例史);skill-bettor 的是「家族 eval 成長曲線」(有 skill vs 無 skill 的分數對照,+41.7pp)。skill-bettor **目前沒有**自己的 harness-engineering pilot 對照物——這是誠實的缺口,不是換個名字掩蓋。 |
| 入口 curation:引擎 `loop_wiki/engine.sh` | `loop_wiki/engine.sh`(＋`loop_wiki/_template`) | 本地活實作,原樣映,無需 retarget。 |
| 入口 curation:執行故事 `git log` | `git log --oneline`(main tree 目前 3 commit 起) | 原樣映;skill-bettor 的 git 歷史雖淺但真實存在(`git init` 已完成,雖然 `ARCHITECTURE.md` §10 checklist 尚未勾選——本身是個活的漂移案例,已收進 audit-dimensions 逼未知 §4)。 |
| reviewer tier 選型錨:`harness-spec §9❻`、`evals-design-method §tier 邊界` | `ARCHITECTURE.md` §5(tier-dispatch 路由表＋硬約束①-④)、`evals-design-method.md`「tier 邊界重申」段 | tier-dispatch 表在 skill-bettor 是 `ARCHITECTURE.md` 的內容,不在 `harness-spec.md` 裡——這是移植 `loop-harness-standard` 時已經做的搬遷決策,本 skill 只是正確引用它,不重複發明。 |
| Opus 裁決 rationale 的活證(design-governance slice-1 HOLD) | **無本地活證,誠實標記「尚無」** | skill-bettor 的 holdout 畢業段(`families/pinescript-audit`)**尚未真跑過一次**(holdout 只跑一次的鐵律意味著目前是 0 次)。rationale 是繼承的設計原則,不是已驗證的本地事實——`modules/handoff-know-why.md` §2 已明標此落差。 |
| agy 角色邊界錨:記憶檔案 `agy-runs-gemini-only` | `ARCHITECTURE.md` §5「DR/跨家族複核」行＋§5 硬約束① | antigravity 那份記憶檔案是 `~/.claude/projects/-Users-neon-antigravity/` 專案作用域,不保證在 skill-bettor session 可見/存在;skill-bettor 有自己的本地權威(`ARCHITECTURE.md` §5 已明文寫死同一事實),改引用它,不依賴跨專案記憶。 |
| Goodhart/fold-back 案例代號 R7(dangling-id)/R8(tool-syntax-leak) | `families/pinescript-audit/changelog/2026-07-11.md`「已知問題 5」(案例對強模型太簡單,需要語意級陷阱) | 不搬案例代號本身(那是 antigravity 自己 checker 的名字),改用 skill-bettor 自己已經記錄在 changelog 裡的、性質相近的早期 Goodhart 訊號當具體審計素材。 |
| 8 項已知審計維度 | **6 項保留 + 2 項移除**(見 [audit-dimensions.md](audit-dimensions.md) ④⑤) | 「AGENTS.md·CLAUDE.md 差異」「N×M 覆蓋」兩項的架構前提(雙 host、root 雙檔)在 skill-bettor 不存在,移除並非簡化,是不佯裝一個不存在的問題;其餘 6 項(scripts/tests 結構、執行效率、passive-context、效益疊加、Goodhart 逃逸、驗證器經濟學)是真正跨系統通用的方法論,retarget 詞彙後原樣映,並各自換上本地真實錨(見上表與 audit-dimensions.md 內文)。 |
| 6 步確定性程序＋5 條不變量＋Gotchas 骨架 | **原樣映**(措辭與錨改本地) | 這是全篇最可轉移的部分——fresh-session 隔離、tier 選型通則、findings-only、anchored-claims、curate-not-dump、completeness-critic——與 host/driver 矩陣無關,是「怎麼設計一份交接」本身的方法論。 |

## 3. 拿掉的東西不是「簡化」,而是這三種情況之一

- **架構前提不同,真拿掉**:AGENTS.md/CLAUDE.md 差異維度、N×M 覆蓋維度——skill-bettor 單 host 的事實,不是能力縮水(承 [`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md)、[`harness-wiki/modules/retarget-map.md`](../../harness-wiki/modules/retarget-map.md) 已建立的判準)。
- **對應歷史不存在,誠實標「尚無」而非捏造**:worked instance(交接稿)、Opus 裁決本地活證、harness-engineering pilot。這些是 antigravity 自己迴圈跑出來的軌跡,skill-bettor 還沒有——不是把它們刪掉遮醜,而是明寫「還沒有,需要時從哪裡產生第一個」。
- **章節/檔案座標不同,需重新核對而非照搬數字**:`harness-spec §9❻/❼` → `ARCHITECTURE.md §5`、案例代號 R7/R8 → changelog 已知問題清單。這類是最容易犯的錯——数字看起来像「一样的東西」,但如果不重新核對,會指向本地根本不存在的章節。

## 4. 判別「retarget 成立」的鐵錨(逐路徑驗證紀錄)

以下路徑於本次移植時逐一以 `test -e`/`ls` 驗證存在(執行於 2026-07-11):

**skill-bettor 本地(必須真實,否則整個 skill 失去意義)**
- `ARCHITECTURE.md`、`CLAUDE.md` — 存在。
- `.claude/skills/loop-harness-standard/{SKILL.md,modules/harness-spec.md,modules/evals-design-method.md,modules/retarget-map.md}` — 全部存在。
- `.claude/skills/harness-wiki/{SKILL.md,modules/retarget-map.md}` — 存在。
- `loop_demo/claude_agy/{scripts,tests,evals.json,verify.sh,selftest.sh,PLAN.md,PROMPT.md,run.sh,CLAUDE.md}`、`loop_demo/RETARGET-NOTE.md` — 全部存在。
- `loop_wiki/{engine.sh,_template,README.md}` — 存在;`_template/` 內含 `{selftest.sh,verify.sh,PROMPT.md,run.sh,PLAN.md,CLAUDE.md,logs,anti}`。
- `families/pinescript-audit/{FAMILY.yaml,changelog/2026-07-11.md}`、`evals/{runner.py,judge.py,mock_agent.py,no_skill_agent.sh,trigger-evals.json,baselines,cases,holdout,candidates}`、`skills/repaint-detection/{SKILL.md,scripts/scan_repaint.py,references/security-function-patterns.md}` — 全部存在。
- 本次移植批次的 6 個手足 skill(`.claude/skills/{external-verify,fold-in,html-for-decisions,judge-loop-chooser,sdlc-plan-composer,unknown-discovery-composer}/SKILL.md`)——移植過程中逐一確認落地(起始檢查時 2 個尚缺,完稿前 6 個全數確認存在)。

**antigravity 外部(僅結構參考,明確標註非本地路徑)**
- `/Users/neon/antigravity/docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md` — 存在(於 antigravity repo)。
- `/Users/neon/antigravity/.agents/skills/antigravity-harness-wiki/modules/loop-architecture-ssot.md` — 存在(於 antigravity repo)。
- `/Users/neon/antigravity/loop_wiki/{design_governance,agy_demo}` — 存在(於 antigravity repo)。**skill-bettor 沒有這兩個目錄的本地副本**——本檔與 SKILL.md/audit-dimensions.md 出現的任何 `design_governance`/`agy_demo` 字樣皆帶明確「antigravity 外部」標註,沒有裸引用。

若哪天有人在本 skill 的內容裡發現裸的 `loop_wiki/design_governance`、`loop_wiki/agy_demo`、`AGENTS.md`(root)、`N×M` 字樣**沒有**明標「antigravity 外部/已移除」,那就是移植時漏標的死指針或雙圖漂移——比照本檔 §2 表格與 §4 清單修正。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/loop-harness-review-handoff/`(SKILL.md +
  `modules/{handoff-know-why,audit-dimensions}.md` + `reference/handoff-template.md`)。
- 外部參考(結構研究用,非本地內容):`/Users/neon/antigravity/docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md`。
- skill-bettor 既有同構:`.claude/skills/loop-harness-standard/modules/retarget-map.md`、
  `.claude/skills/harness-wiki/modules/retarget-map.md`——本檔的移植紀律(萃取方法論、逐機制映射表、
  「拿掉≠簡化」判準、鐵錨驗證)與這兩份同源,只是多了「逐路徑 `test -e`」這一項因為本 skill 的產出
  本身就是路徑清單。
