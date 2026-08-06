# Module: autoresearch-composer — northstar → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`autoresearch-composer`](../SKILL.md)。本檔 = port 的命門與誠實帳本：哪些機制一對一映到
> skill-bettor、哪些沒基座被拿掉/降級、為何不是簡化。

---

## 0. 為什麼是現在、為什麼落在 `.claude/skills/` 而不是 `families/`

skill-bettor 自己的 `sdlc-plan-composer`（2026-07-11 從 antigravity 同批移植）在 S5 就已經記錄過這個
缺口，且明確標記為「潛在重新評估點」而非死結——見其 `modules/retarget-map.md` §5「開放問題」第 2 條：
「`autoresearch` 系列在 skill-bettor session 實際可用...但任務明確指示維持誠實留白，不要發明一個...僅
記錄這個潛在的重新評估點」。2026-07-17 使用者明確要求把 `autoresearch-composer` 遷移進來，正是在兌現
那個記錄——不是臨時起意的新缺口填補。

**兩個候選位置，選了哪一個、為什麼**：
- `families/<name>/`——skill-bettor 的「業務資產」層，強制要求真代碼 + eval harness（`evals/cases`,
  `holdout`, `candidates`, `runner.py`, `judge.py`, `baselines/*.json`，走 proposals→eval-gate→人 admit
  →merge 流程，見 `families/pinescript-audit`/`families/agent-harness` 兩個現存範例）。
- `.claude/skills/<name>/`——流程/路由 meta-skill 層，目前已有 `sdlc-plan-composer`/
  `unknown-discovery-composer`/`judge-loop-chooser`/`repo-agent-native`/`path-b-reduction`/
  `external-verify`/`fold-in`/`loop-harness-standard` 等，皆是從 antigravity 移植的**文件/路由型**
  skill，沒有自己的可執行代碼，不走 `families/` eval-gate。2026-07-23 起，這類
  skill 仍可走 `repo/agent-skills-repo` 的 skill-asset governance gate（cases + A/B ablation + lifecycle validator）。

`autoresearch-composer` 本質是純路由 + 契約注入文件（沒有自己的可執行代碼），跟 `families/`
現存兩個範例的性質（真代碼、真 eval harness、真 baseline）
明顯不同類——硬塞進 `families/` 會需要生造假 `FAMILY.yaml` metrics（全 null 之外還要生造一個不存在的
「代碼模組」對應關係）。落在 `.claude/skills/` 才是誠實的分類：它就是 `sdlc-plan-composer`/
`unknown-discovery-composer` 的同類 sibling，not a business asset。新的 cases/A-B gate 是
skill-asset governance hard gate，不是 `families/` business-asset gate。

---

## 1. 逐機制 retarget 映射表

| northstar 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| §1 Iteration-Loop Gate（5 判據） | **原樣保留** | 平台無關的迭代迴圈判準。 |
| §2 讓位路由表的「原生治理 skill」欄 | **沿用 antigravity 2026-07-17 retarget 後的版本**（`diagnose`/`diagnosing-bugs`/`tdd`/`grilling`/`/security-review`+`sast-validator`/`improve-codebase-architecture`/`to-prd`），非直接抄 northstar 的 superpowers 清單 | 這些全是 mattpocock 全局 skill（`~/.agents/skills/`）或 Claude Code bundled skill，非 project-scoped——antigravity 已於 2026-07-17 驗證存在並完成同一輪 retarget（見 antigravity `.agents/skills/autoresearch-composer/modules/retarget-map.md`），skill-bettor 與 antigravity 同一台機器同一使用者，這些全局資源同樣可用，直接沿用其結論比重新查一輪更省，也更一致。 |
| `/autoresearch:ship` 讓位 `devops-hub` | **拿掉，誠實留白（無讓位對象）** | skill-bettor 是 living-skills 資產工場，不是要 ship 的部署型服務，沒有部署管線治理層。 |
| §2 新增行：`/autoresearch:evals` 與 `families/*/evals/` 的區分提醒 | **skill-bettor 特有，antigravity 版沒有這行** | antigravity 沒有 `families/` 這個概念，不需要這條澄清；skill-bettor 有，容易被誤認成同一件事（都叫 evals），故補一行防混淆。 |
| §2 新增行：`/autoresearch:scenario` 若為某 family 補案例時的優先序 | **skill-bettor 特有** | 同上——skill-bettor 的 `families/*/evals/{cases,holdout,candidates}` 有自己的一套慣例（見 `pinescript-audit` 範例），需求若是「幫某 family 補 eval 案例」應優先用該慣例，不是繞道 autoresearch。 |
| §3 Iteration-Loop Contract block | **原樣保留** | 平台無關。 |
| `executor` 槽的 `cycle-dispatch` | **拿掉，改指主會話手動分治** | skill-bettor 無 ENCD/`cycle-dispatch`（同 antigravity 版判斷，`sdlc-plan-composer` 本地版亦無此中介層）。 |
| §3.5 重構特化（northstar 原版：`radon`/`code-refactor-operator-reviewer`/`/refactor-loop`） | **整段拿掉，不繼承**（連 antigravity 版都已拿掉，本 port 沿用該決定，非重新評估） | northstar 專屬工具鏈，antigravity/skill-bettor 皆無。 |
| §3.6 rejection_log / edit_budget | **原樣保留** | 平台無關。 |
| §4 與 `sdlc-plan-composer` 的組合 | **原樣保留，且今日已實際 wiring**（`.claude/skills/sdlc-plan-composer/SKILL.md` S5 row 已改指本 skill） | skill-bettor 本有本地 `sdlc-plan-composer` fork，Output Contract 目錄結構相同（`docs/plans/<date>-<topic>/`）。 |
| 新增邊界說明：「不接 `families/`」 | **skill-bettor 特有** | antigravity 沒有 `families/` 這個第二套資產層，不需要這條邊界聲明；skill-bettor 有,必須明確劃開,防止未來有人誤把 autoresearch 迭代產物直接當 family 用而繞過 eval-gate（違反「知識單向流…沒有旁門」鐵律）。 |
| 整合接點：`encd-infrastructure-hub`/`skill-cycle`/`mega-flow-harness-hub` | **拿掉** | skill-bettor 無這類編排層（同 antigravity 版判斷）。 |
| YAML frontmatter 治理欄位（`liveness`/`functional_type`/`hub_modifier` 等） | **拿掉**，換 `name`+`description` 極簡 frontmatter | 與 skill-bettor 其他 `.claude/skills/*` sibling 一致慣例。 |

---

## 2. 拿掉的東西不是「簡化」，而是「不引入不存在的基座」/ 真實能力差距誠實記錄

- **能一對一映的映**：§1 Gate 五判據、§3 Contract block 全部欄位、§3.6 選填特化、§4 與
  `sdlc-plan-composer` 的組合關係、Output Contract 目錄結構。
- **沿用 antigravity 同日 retarget 結論的**（比重新查一輪更一致）：§2 讓位路由表七行原生 skill。
- **無基座、真實能力差距、誠實拿掉並記錄**：`encd-infrastructure-hub`/`skill-cycle`/
  `mega-flow-harness-hub` 整合接點、§3.5 整段重構特化工具鏈、`cycle-dispatch` executor 選項、
  `devops-hub` 讓位對象（`:ship` 改誠實留白）、skill-conformance-hub 治理 YAML 欄位。
- **skill-bettor 特有的新增邊界**（非拿掉，是補充）：與 `families/` 的職責劃分聲明——這是
  northstar/antigravity 都不需要、但 skill-bettor 因為有 `families/` 這個第二套資產層而必須明講的一條。

---

## 3. 判別「retarget 成立」的鐵錨

- 外部 autoresearch 引擎：`~/.claude/commands/autoresearch/`（12 個 sub 命令檔）+
  `~/.claude/commands/autoresearch.md`（核心）現場 `ls` 確認存在（2026-07-17，全局裝，同一台機器同一
  使用者，與 antigravity 共用）。
- skill-bettor 本地讓位對象：`~/.agents/skills/{diagnose,diagnosing-bugs,tdd,grilling,grill-with-docs,
  grill-me,improve-codebase-architecture,to-prd}/SKILL.md` 為全局資源（非 project-scoped，antigravity
  已於同日驗證存在）；`/security-review`／`sast-validator` 為 Claude Code bundled skill/agent，非
  project-scoped。
- skill-bettor 本地委派方：`.claude/skills/sdlc-plan-composer/SKILL.md`（S5 row 已改指本 skill）。
- superpowers plugin：`installed_plugins.json` 查證 skill-bettor 未在其 project 清單中（同 antigravity/
  northstar 之外的另外兩個專案 `local_stack`/`TrueMe_Android` 才有掛號）——本 port 的 §2 讓位表本來就不
  依賴 superpowers，這條只是附帶確認，不影響本檔任何決策。

若哪天有人往 SKILL.md 塞回 `encd-infrastructure-hub`/`skill-cycle`/`cycle-dispatch`/
`code-refactor-operator-reviewer`/`/refactor-loop`/`devops-hub`/skill-conformance-hub 的
`liveness`/`grounding` 欄位，或把本 skill 的產物直接當 `families/` 資產用而繞過 eval-gate，那就是把死
husk 搬回來或開旁門——擋下。

---

## Sources / Lineage

- northstar 源：`/Users/neon/northstar/.claude/skills/autoresearch-composer/skill.md`（v0.3.0）。
- antigravity 同日 retarget 版（本 port 的直接參照，非重新從 northstar 原檔推導）：
  `/Users/neon/antigravity/.agents/skills/autoresearch-composer/{SKILL.md,modules/retarget-map.md}`。
- skill-bettor 慣例／同型 port 先例：
  [`sdlc-plan-composer/modules/retarget-map.md`](../../sdlc-plan-composer/modules/retarget-map.md)（§5
  開放問題第 2 條即本次 fill-gap 對象）、
  [`unknown-discovery-composer/modules/retarget-map.md`](../../unknown-discovery-composer/modules/retarget-map.md)。
- 上游 fill-gap 對象：`.claude/skills/sdlc-plan-composer/`（S5「優化迴圈委派」原記「誠實留白/開放問題」，
  本 port 落地後已改指回本 skill）。
