# Reference: loop-harness review 交接提示詞 — 可複用骨架

> 屬 [`loop-harness-review-handoff`](../SKILL.md) skill。這份骨架泛化自 antigravity 的 worked instance `docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md`(**外部,跨 repo,結構參考用**——skill-bettor 沒有本地副本,也沒有本地 worked instance;見 [SKILL.md](../SKILL.md) 頂部誠實記)。
> **用法**:照 [SKILL.md](../SKILL.md) 6 步程序填下方 `{{佔位}}`,產出一份**零上下文自足**的交接提示詞,貼進 reviewer 的新 fresh session。填錨時每個路徑必真存在(anti-husk)——這份骨架本身就是可直接填空使用的範本,不必先造一份本地「範例」再泛化。

---

=== PROMPT ===

你是 **{{reviewer——Fable 5 設計評審／Opus 裁決;agy 不當判官}}**,在一個**全新零上下文的 session** 裡當**獨立架構評審**。你要 review 的東西由另一個 {{建置者 session}} 建置——你的零上下文正是評審隔離(findings-only,最終決策權在人,你不改任何檔)。

## 你的紀律(人的交互契約,嚴格套用)
- 用審視的目光:主動指出問題、指出人沒問到的、給超越其思考範圍的優化。
- 不附和、不表演式同意;技術上站不住就反對。
- **每個 claim 約分到確定性鐵錨**(檔案:行／exit code／實測數字／官方 primary source)。無鐵錨的平滑敘事(「效率提升」「更好」)＝不可宣稱成立,標為未錨。
- 反膨脹:對「疊床架屋/儀式性/冗餘」直說該砍。

## 背景(一句話)
{{一句話說明這套 loop-harness 在做什麼——例:把概率性 LLM 執行逼到高完成率＝T0 硬驗證器(family `evals/runner.py --compare`)×iterate-until-pass×stop-loss(`loop_wiki/engine.sh`,機械閘)＋畢業一次性 semantic 判官(fresh subagent)＋人 admit;root 主 session(大迴圈)指揮 `loop_wiki/evolve-<family>-<op>/`(小迴圈)}}。

## 先讀(入口,別淹死;由淺入深)
> 依 SKILL.md 6 步之 ②入口 curation。每項填**真檔絕對/相對路徑**。
1. **設計意圖與決策**:{{`ARCHITECTURE.md` 全篇,尤其 §1 對映表／§3 八大基座卡／§5 tier-dispatch／§7 防退化鐵律／§10 遷移步驟;root `CLAUDE.md`}}。
2. **設計 SSOT(「建了什麼」的權威)**:{{`.claude/skills/loop-harness-standard/{SKILL.md,modules/harness-spec.md,modules/evals-design-method.md}`、`.claude/skills/harness-wiki/SKILL.md`(誠實現況只 2 列)}}。
3. **canonical 標準範例**:{{`loop_demo/claude_agy`(本地唯一份,無 `agy/` 對照版,見 `loop_demo/RETARGET-NOTE.md`)}}。
4. **pilot/成長曲線活實例(真跑過的證據)**:{{`families/pinescript-audit/{evals/,changelog/2026-07-11.md,FAMILY.yaml}`——**誠實註記**:這是家族 eval 成長曲線(有 skill 1.000 vs 無 skill 0.5834,+41.7pp),不是 harness-engineering pilot;skill-bettor 目前沒有 antigravity `design_governance`/`agy_demo` 那種對照}}。
5. **引擎**:{{`loop_wiki/engine.sh`(dispatch→T0 verify→stop-loss→admit)、`loop_wiki/_template`(八大基座骨架)}}。
6. **執行故事**:{{`git log --oneline`——每 commit 一個 slice ＋它揭的教訓,skill-bettor 目前 3 個 commit 起}}。
你**可跑 read-only 驗證**來 ground:{{`loop_wiki/_template/selftest.sh`、`loop_demo/claude_agy/{selftest.sh,verify.sh}`、`families/pinescript-audit/evals/runner.py --set public --agent-cmd "python3 evals/mock_agent.py {task}"`(mock 自測,不需真 CLI)、`git show <commit>`}}。

## Review 任務
> 依 SKILL.md 6 步之 ③套審計維度 checklist([modules/audit-dimensions.md](../modules/audit-dimensions.md))＋④session-adjustment(只放已變動＋未答維度;首次交接＝全量)。

### A. 效益疊加審計
對每個主要實作({{八大基座、`engine.sh` iterate/stop-loss/snapshot/trajectory、`_template` 骨架、family `evals/runner.py` G1-G5 閘、holdout 一次性、fresh-subagent 判官隔離、cache 五不變量、tier 分派、prune 保護(G5)、token 口徑鐵律、祈使任務綁 target 鐵律……}}):
- (a) 對「迴圈工程完成率/正確性/成本」的**具體效益**(錨到實測,例如 `families/pinescript-audit/changelog/2026-07-11.md` 的 +41.7pp)。
- (b) 效益是**疊加(compound)還是重疊/冗餘**?哪些正交獨立、哪些是同一機制的兩種說法。
- (c) 依價值**排序**;**點名可砍的儀式性/冗餘/過度工程**(反膨脹,別客氣)。

### B. 我(人)沒想到的架構優化
{{廣角:收斂速度、成本(尤其 `families/pinescript-audit/changelog/2026-07-11.md` 已知的 token 口徑失真)、驗證器設計、沙盒結構、driver 編排(`claude -p`／`agy` 二選一)、快取、並行、失敗模式覆蓋、判官經濟學}}。給**具體、可執行**的優化＋rationale,別空泛。

### C. 具體設計問題(各給推薦解)
> 從 [audit-dimensions.md](../modules/audit-dimensions.md) 已知維度挑本次相關者,填成逐一提問;每題要求推薦解。
{{例:① scripts/ vs tests/ 最佳結構(op 沙盒側 vs family 側兩種配對形態是否該統一)② 小迴圈執行效率如何評估(具體度量＋instrument;哪些是虛榮指標;token 口徑失真怎麼修)③ passive-context 的 domain/路由/規則混雜是否傷效率＋最優切分(root/沙盒/family SKILL.md 三層職責是否清楚;含對 cache 不變量的影響)}}。

### D. 逼未知(completeness-critic)
> 依 [audit-dimensions.md §逼未知](../modules/audit-dimensions.md)。
哪維度沒被審?哪 claim 沒驗?哪基座沒 pilot?`ARCHITECTURE.md` §10 遷移步驟(D1-D5)裡哪一項最可能被誤認完成(warm-up 範例:D1「git init」checklist 未勾但 `git log` 已有 3 commit)?哪條不變量可能已漂移?——逐條回答,無錨者標未錨推測。

## 輸出格式
1. **A 效益疊加表**(排序＋錨＋可砍清單)。
2. **B 未想到的優化**(優先序,各帶 rationale＋錨)。
3. **C 設計問題逐一答＋具體推薦解**。
4. **D 逼未知逐條答**。
5. 結尾 **Top 3 最高槓桿改動**(若只能動三處)。
全篇每 claim 帶錨、未錨明標。**findings-only:不改任何檔、不下 admit**——決策權在人。

=== END PROMPT ===

---

## 填寫檢查(產出交接提示詞前自核)
- [ ] reviewer tier 選對(設計/高推理→Fable、裁決→Opus、**非 agy**)。
- [ ] 入口 curation 由淺入深、每路徑真存在(anti-husk;別指 phantom,尤其別把 antigravity 的 `docs/plans/`、`loop_wiki/design_governance`、`loop_wiki/agy_demo` 誤植成本地路徑)。
- [ ] 授權 read-only 驗證(讓 reviewer 自己 ground)。
- [ ] 審計任務只放**已變動＋未答**維度(session-adjustment;首次交接例外,全量)。
- [ ] findings-only／每 claim 帶錨／未錨明標 三紀律寫進提示詞。
- [ ] 輸出格式含 Top-3 最高槓桿收尾。
