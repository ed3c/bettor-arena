---
name: loop-harness-review-handoff
description: |
  把一次大小迴圈 harness 的架構 review／audit／優化**交接**給獨立 fresh-session reviewer 時使用——
  設計零上下文自足的交接提示詞,讓一個新 session 的高推理 reviewer(Fable 5 設計評審／Opus 裁決;
  agy 不當判官因 Gemini only)獨立審計並優化八大基座(scripts↔tests 結構／執行效率度量／
  passive-context 混雜／效益疊加／Goodhart 逃逸＋fold-back／驗證器經濟學)。
  findings-only、每 claim 帶確定性錨、admit 永遠是人。fresh-session＝評審隔離(同家族靠新 session
  零上下文達獨立、跨家族天然)。
  何時用:要把 skill-bettor 的一次演化小迴圈架構 review/audit/優化派給獨立新 session reviewer 時。
  觸發詞:交接架構評審、reviewer handoff、fresh-session 獨立審計、八大基座 review、
  loop-harness 優化交接、審計維度 checklist、loop-harness-review-handoff。
  NOT for:跑迴圈本身(直接用 loop_wiki/engine.sh,無專屬 skill 包裝)、選驗證標準＋獨立性 tier
  (judge-loop-chooser)、未知路由／發掘編排(unknown-discovery-composer)、查外部／post-cutoff claim
  (external-verify)、建/改新迴圈工程規範本體(loop-harness-standard)。
  完整 know-why 在 modules/handoff-know-why.md。
---

# Skill: loop-harness-review-handoff — 大小迴圈架構 review/audit 交接方法論

> **Role**:設計一份**零上下文自足**的交接提示詞,
> 派給獨立 **fresh-session reviewer**
> (Fable 5＝設計/高推理架構評審／Opus＝裁決;
> agy 不當判官[Gemini only])
> 獨立審計與優化 skill-bettor 演化小迴圈的八大基座。
> 輸出 **findings-only**,**admit＝人**。
>
> **結構**:SKILL.md ＝ 6 步確定性程序＋5 條不變量＋Gotchas;
> 為何 fresh-session＝隔離、reviewer tier 選型 rationale、
> anti-sycophancy/anchored-claims 為何、session-adjustment 方法
> 在 [modules/handoff-know-why.md](modules/handoff-know-why.md);
> 八大基座已知審計維度 checklist＋逼未知
> 在 [modules/audit-dimensions.md](modules/audit-dimensions.md)。
>
> **worked instance 現況(誠實記,勿捏造)**:
> skill-bettor 目前**沒有**這個 skill 的本地真實使用實例
> ——不像 antigravity 有一份真實跑過的歷史交接稿
> `docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md`
> (antigravity repo,跨 repo 外部參照,非本地檔案)。
> 那份 antigravity 實例仍可當**骨架/結構研究材料**參考
> (它是這個方法論本身的一個 worked instance,泛化其形式≠內容可搬),
> 但不是 skill-bettor 的內容。
> 本地要用時直接照
> [reference/handoff-template.md](reference/handoff-template.md)
> 已泛化好的可複用骨架填空——那才是本地實際可套用的範本。
>
> **設計 SSOT(交接指向的權威,只指針不抄)**:
> [`ARCHITECTURE.md`](../../../ARCHITECTURE.md)(設計意圖)
> → [`loop-harness-standard`](../loop-harness-standard/SKILL.md)
> ＋`modules/harness-spec.md`
> ／`modules/evals-design-method.md`(八大基座設計規範)
> → [`harness-wiki`](../harness-wiki/SKILL.md)
> (本地多迴圈全景,誠實現況＝只 2 列組件卡)
> → canonical 範例 `loop_demo/claude_agy`(本地唯一範例,無 `agy/` 對照版)
> → pilot 證據 `families/pinescript-audit/{evals/,changelog/2026-07-11.md,FAMILY.yaml}`
>   (誠實註記:這是家族 eval **成長曲線**證據,
>   非 harness-engineering **pilot**,
>   skill-bettor 尚無 antigravity
>   `design_governance`/`agy_demo` 那種對照)
> → 引擎 `loop_wiki/engine.sh`＋`loop_wiki/_template`
> → `git log`。

## When to Use
- 要把 skill-bettor 一次 loop-harness 的**架構 review／audit／優化**
  交接到新 session(獨立 reviewer 零上下文審計)時。
- 已有一批八大基座實作/決策要被獨立高推理評審點名「效益疊加 vs 冗餘可砍」＋逼出未想到的優化時。

## Not For
- ❌ 跑迴圈本身／診斷管線失敗
  → 直接呼叫 `loop_wiki/engine.sh`
  (見 root `CLAUDE.md` 核心指令;
  skill-bettor 沒有等價 antigravity
  `dr-research-loop` 的「跑迴圈」skill,
  調度是直接 CLI,不經 skill 路由)。
- ❌ 選某 deliverable 的驗證標準＋獨立性 tier
  → [judge-loop-chooser](../judge-loop-chooser/SKILL.md)。
- ❌ 未知路由／發掘編排
  → [unknown-discovery-composer](../unknown-discovery-composer/SKILL.md)。
- ❌ 查證外部/post-cutoff claim
  → [external-verify](../external-verify/SKILL.md)。
- ❌ 建/改一條新迴圈的工程規範本體
  → [loop-harness-standard](../loop-harness-standard/SKILL.md)
  (本 skill 是**把它的 review 交接出去**,不是定義基座)。

## 確定性程序(6 步,逐步產出交接提示詞)
1. **reviewer tier 選型**:
   設計/高推理架構評審 → Fable 5;
   裁決型 → Opus;
   **agy 永不當判官**(Gemini only;
   skill-bettor 的權威錨＝
   [`ARCHITECTURE.md` §5 tier-dispatch](../../../ARCHITECTURE.md)
   「DR/跨家族複核」行＝agy「只產 findings 不 verdict」
   ＋§5 硬約束①「判官硬地板永不 Haiku/永不 agy verdict」)。
   **fresh-session＝評審隔離**——同家族 reviewer
   靠**新 session 零上下文**達獨立(非 fork)、跨家族天然隔離。
   tier 邊界另錨
   [`evals-design-method.md`「tier 邊界重申」](../loop-harness-standard/modules/evals-design-method.md)。
2. **入口 curation(由淺入深別淹死;curate 非丟整 repo)**:
   設計意圖(`ARCHITECTURE.md` 全篇,
   尤其 §1 對映表／§3 八大基座卡／§5 tier-dispatch／§7 防退化鐵律;
   root `CLAUDE.md` 入口)
   → 設計 SSOT(`loop-harness-standard` SKILL
   ＋`modules/harness-spec.md` §1-§5
   ＋`modules/evals-design-method.md`;
   `harness-wiki` SKILL,誠實現況只 2 列)
   → canonical 範例(`loop_demo/claude_agy`,本地唯一份)
   → pilot 證據(`families/pinescript-audit/evals/`
   ＋`changelog/2026-07-11.md`＋`FAMILY.yaml`;
   **誠實標記這是家族成長曲線,非 harness pilot**)
   → 引擎(`loop_wiki/engine.sh`＋`loop_wiki/_template`)
   → 執行故事(`git log --oneline`)。
   並**授權 reviewer 跑 read-only 驗證 ground**
   (`loop_wiki/_template/selftest.sh`、
   `loop_demo/claude_agy/{selftest.sh,verify.sh}`、
   `families/pinescript-audit/evals/runner.py --set public --agent-cmd "python3 evals/mock_agent.py {task}"` 的 mock 自測、
   `git show <commit>`)。
3. **套審計維度 checklist**:
   把
   [modules/audit-dimensions.md](modules/audit-dimensions.md)
   的六項已知審計維度逐項放進交接任務
   (原 antigravity 版另兩項「AGENTS.md·CLAUDE.md 差異」「N×M 覆蓋」
   對 skill-bettor 不適用,
   已在該檔明標移除理由,不佯裝存在),
   並帶「逼未知」的 completeness-critic 提問。
4. **session-adjustment(差量交接)**:
   依 review target 的內容、
   **自上次交接已變動的 slice**(`git log --oneline` 圈範圍)、
   reviewer tier,
   調整本次重點與**已答維度**——只重點審已變動＋未答維度,不每次重審全量。
   **誠實現況**:skill-bettor 目前沒有任何一次真實交接歷史,
   首次使用本 skill 時「差量」等同「全量」;
   此步驟是為第二輪以後預留的紀律,非本次可套用的捷徑。
5. **findings 紀律**:交接提示詞內明令
   ——每 claim 帶**確定性錨**
   (檔案:行／exit code／實測數字／官方 primary source),
   未錨**明標**(Path B);
   不附和不表演式同意;
   read-only grounding;
   **findings-only**(不改檔、不下 admit)。
6. **輸出結構**:交接提示詞要求 reviewer 產出——
   - ① **效益疊加表**(排序＋可砍清單)
   - ② **未想到的優化**(優先序＋rationale＋錨)
   - ③ **設計問題逐一答＋推薦解**
   - ④ 結尾 **Top-3 最高槓桿改動**。

## 不變量(違反即停)
1. **findings-only、admit 永遠是人**:
   reviewer 不改任何檔、不下 admit;決策權在人
   (承 skill-bettor `ARCHITECTURE.md` §8 人閘清單
   「merge/畢業/案例輪替永遠人 admit」同一紀律的評審版)。
2. **每 claim 帶錨、未錨明標**:
   無確定性錨的平滑敘事(「效率提升」「更好」)＝不可宣稱成立,標為未錨(Path B 紀律)。
3. **fresh-session＝隔離＋reviewer tier 匹配**:
   設計/高推理→Fable/Opus、裁決→Opus、**agy 不當判官**;
   同家族靠新 session 零上下文達獨立(禁 fork)、跨家族天然。
4. **入口由淺入深別淹死**:
   curate 入口(設計意圖→設計 SSOT→範例→pilot→引擎→git log)
   ＋授權 read-only 驗證,
   **不丟整個 repo**給 reviewer
   (會淹死注意力,同 `harness-spec.md` §2❷ 記的 91.6%→71.3% 上下文腐化風險)。
5. **審計維度 checklist 必掃 known＋逼出 unknown**:
   六項已知維度逐項掃過,並用 completeness-critic 逼出
   「沒被審的維度/沒驗的 claim/沒 pilot 的基座/可能已漂移的不變量/
   §10 遷移步驟裡被誤認完成的項」。

## Gotchas
- **reviewer 同家族靠 fresh-session 隔離、非 fork**
  (fork 帶母上下文＝污染獨立性;
  [loop-harness-standard 鐵律 2](../loop-harness-standard/SKILL.md)
  「驗證器／執行者拓撲隔離」禁 fork 同源)。
  跨家族(如 Opus 審 Gemini 產物)天然隔離。
- **別讓 reviewer 讀整個 repo**:
  curate 入口由淺入深,否則注意力被稀釋、findings 變泛。
  授權 read-only 驗證讓 reviewer 自己 ground,不預先塞滿。
- **ground claims 否則 Half-Bridge 散文**:
  交接提示詞若不強制「每 claim 帶錨」,reviewer 會回一堆「感覺更好」的平滑敘事
  (技術上站不住);錨是 findings 可用性的命門。
- **交接是方法論類 fold 的近親——反-husk 錨＝指向的 SSOT 是真檔案**:
  入口 curation 列的每個路徑必真存在。
  本次移植逐路徑以 `test -e`／`ls` 驗證過
  (見 [modules/retarget-map.md](modules/retarget-map.md)),
  別指 phantom——尤其別把 antigravity 的
  `docs/plans/2026-07-09-loop-harness-panorama/`、
  `loop_wiki/design_governance`、`loop_wiki/agy_demo`
  誤植成本地路徑(它們是外部參照,skill-bettor 沒有本地副本)。
- **agy 是 driver/author 不是 reviewer**:
  交接提示詞若不慎把 agy 排進 reviewer 選項
  會直接違反 `ARCHITECTURE.md` §5 硬約束①
  ——agy 在 skill-bettor 的角色永遠是
  「DR/跨家族複核,只產 findings 不 verdict」,
  不是任何形式的裁決者。

## Modules
- [modules/handoff-know-why.md](modules/handoff-know-why.md)
  — Layer B know-why:
  為何 fresh-session＝隔離(零上下文獨立,同家族亦成立)
  ／reviewer tier 選型 rationale
  (Fable 設計 vs Opus 裁決 vs agy 不當判官,
  錨 `ARCHITECTURE.md` §5＋`evals-design-method.md`)
  ／anti-sycophancy 與 anchored-claims 為何(Path B)
  ／session-adjustment 差量交接方法。
- [modules/audit-dimensions.md](modules/audit-dimensions.md)
  — 八大基座**已知審計維度 checklist**
  (scripts↔tests 結構／執行效率度量＋instrument
  ／passive-context 混雜＋最優切分
  ／效益疊加 vs 冗餘／Goodhart 逃逸＋fold-back 閉環／驗證器經濟學;
  另列 2 項因 skill-bettor 架構前提不同而移除的維度＋理由)
  ＋**逼未知**的 completeness-critic 提問。
- [reference/handoff-template.md](reference/handoff-template.md)
  — 泛化自 antigravity worked instance 的可複用交接提示詞骨架
  (ROLE／紀律／入口 curation／審計任務 A-D／輸出格式＋佔位),
  retarget 為 skill-bettor 詞彙(families/evals/loop_wiki)。
- [modules/retarget-map.md](modules/retarget-map.md)
  — antigravity → skill-bettor 逐機制映射與誠實帳本,
  含每個入口路徑的 `test -e` 驗證紀錄。
