# Module: loop-harness-review-handoff — Layer B know-why

> 屬 [`loop-harness-review-handoff`](../SKILL.md) skill。SKILL.md ＝ 6 步確定性程序＋不變量;本檔 ＝ 為何這樣設計。
> worked instance:skill-bettor 尚無本地實例(見 [SKILL.md](../SKILL.md) 頂部誠實記);骨架 ＝ [reference/handoff-template.md](../reference/handoff-template.md)。

## 1. 為何 fresh-session＝評審隔離(零上下文獨立,同家族亦成立)

交接的核心目的是**獨立審計**——reviewer 不能是「建這套東西的同一個 context」,否則它會替自己的決策辯護(sycophancy 的結構版)。獨立性的技術實現有兩個層次:

- **跨家族天然隔離**:Opus 審 Gemini(agy)產物(或反之)——不同模型家族,無共享 context、無共同訓練近似偏見,獨立性白吃。這與 harness 的「驗證器隔離發生在**家族層**」同源([`loop-harness-standard` 鐵律 2](../../loop-harness-standard/SKILL.md)「驗證器／執行者拓撲隔離」、[`harness-spec.md` §2❶](../../loop-harness-standard/modules/harness-spec.md))。
- **同家族靠 fresh-session 達獨立**:Opus 審 Opus 建的東西、或 Fable 審另一 Fable session 的產物時,**新 session 的零上下文**就是隔離手段——它看不到建置過程的 rationalization、只看 curate 給它的入口與真檔。**關鍵:必須是 fresh session,不能是 fork**。fork 帶著母 session 的完整上下文＝把「要被獨立審的思路」原封搬進 reviewer＝獨立性歸零。這正是 harness 側「同家族(Claude author×Claude judge)必落地 fresh zero-context subagent(**禁 fork**)」的評審交接鏡像([`loop-harness-standard` 鐵律 2](../../loop-harness-standard/SKILL.md)、[`harness-spec.md` §2❶](../../loop-harness-standard/modules/harness-spec.md))。

**推論**:交接提示詞必須設計成**零上下文自足**——因為 fresh session 沒有任何背景,提示詞本身要 curate 足夠入口 + 明訂紀律,否則 reviewer 要嘛淹死在整個 repo(違反不變量 4)、要嘛憑空瞎猜(無錨散文)。antigravity 的 worked instance `REVIEW-HANDOFF-fable5.md` 開頭就是這句「設計成零上下文自足」;skill-bettor 沒有對應實例,直接照 [reference/handoff-template.md](../reference/handoff-template.md) 骨架填空即可,不必先补一份本地「範例」才能用。

## 2. reviewer tier 選型 rationale

| reviewer | 適用 | 為何 | 錨 |
|---|---|---|---|
| **Fable 5** | 設計/高推理架構評審(效益疊加審計、逼出未想到的優化、廣角架構問題) | 高推理 tier 才抓得到跨基座的疊加 vs 冗餘、才逼得出「哪維度沒被審」的 completeness gap;低 tier 抓不到隱蔽 Goodhart/結構性冗餘 | [`ARCHITECTURE.md` §5 tier-dispatch](../../../../ARCHITECTURE.md)「大迴圈編排/計劃」行＋硬約束③「tier 匹配推理需求」 |
| **Opus** | 裁決型(判 HOLD/PASS、對 finding 下定論、當畢業 semantic 判官) | Opus-tier 隔離判官抓得到機械層＋Sonnet-author 皆未抓的 Goodhart | [`ARCHITECTURE.md` §5](../../../../ARCHITECTURE.md)「裁決/畢業判官/llm_judge」行＋[`evals-design-method.md`「tier 邊界重申」](../../loop-harness-standard/modules/evals-design-method.md)。**誠實記**:skill-bettor 目前**沒有**類似 antigravity design-governance slice-1 那種「Opus 判官真的逮到過 Goodhart」的本地活證——這條 rationale 目前是**繼承的設計原則**,尚無本地 worked case,需要時可從 `families/pinescript-audit` 的畢業段(尚未真跑,見 `ARCHITECTURE.md` §7 鐵律 2「holdout 只跑一次」目前仍是 0 次)產出第一個 |
| **agy 不當判官** | ——(排除) | agy＝Gemini,skill-bettor 定位為「DR/跨家族複核」,**只產 findings 不 verdict**;判官/裁決角色永遠是 Opus(fresh subagent)或人,agy 不是評審角色 | [`ARCHITECTURE.md` §5](../../../../ARCHITECTURE.md)「DR/跨家族複核」行＋§5 硬約束①「判官硬地板永不 Haiku/永不 agy verdict」 |

**tier 匹配推理需求的通則**:Opus 做純機械＝浪費、Haiku 裁決＝抓不到 Goodhart。交接評審屬**高推理**任務(架構疊加分析＋逼未知)→ Fable 5 或 Opus,不下放低 tier。

## 3. anti-sycophancy 與 anchored-claims 為何(Path B 紀律)

交接評審最大的失敗模式**不是**「reviewer 找不到問題」,而是「reviewer 回一堆平滑的、聽起來對但站不住的敘事」——「這個設計很優雅」「效率提升明顯」「架構清晰」。這些是 sycophancy 的變體:**表演式同意 + 未錨斷言**。兩條紀律對治:

- **anti-sycophancy**(使用者交互契約直接搬進交接提示詞):不附和、不表演式同意、技術上站不住就反對、對「疊床架屋/儀式性/冗餘」直說該砍。reviewer 的價值在**點破**,附和的 reviewer ＝ 零信息。
- **anchored-claims(Path B)**:每個 claim 必須約分到**確定性鐵錨**——檔案:行、exit code、實測數字、官方 primary source。無錨的平滑敘事標為**未錨**、不可宣稱成立。一個「更好」若不能落到 skill-bettor 自己的真事件(例如 `families/pinescript-audit/changelog/2026-07-11.md` 記的 +41.7pp 實測 Δ),它就是散文。

**為何強制 read-only grounding**:交接提示詞授權 reviewer 跑 `loop_wiki/_template/selftest.sh`／`loop_demo/claude_agy/{selftest.sh,verify.sh}`／`families/pinescript-audit/evals/runner.py`(mock agent)／`git show <commit>`——不是禮貌,是**逼 claim 落地**。reviewer 能自己驗的,就不該憑印象斷。這也讓 reviewer 的獨立性有牙齒(自己 ground、不靠建置者餵結論)。

## 4. session-adjustment(差量交接方法)

交接不是每次都從零重審全量——那既浪費高 tier reviewer 的推理預算,又讓 findings 稀釋。**差量交接**:

1. **鎖定已變動 slice**:自上次交接以來,哪些基座/決策/checker 真的動了(`git log --oneline` 圈範圍——skill-bettor 目前 main tree 3 個 commit 起,可直接核對)。
2. **標記已答維度**:上次交接已被 reviewer 充分審過、且結論仍成立的維度([audit-dimensions](audit-dimensions.md) 的某幾項)標為「已答,除非相關 slice 變動否則略過」。
3. **本次重點 ＝ 已變動 ∪ 未答維度**:把 reviewer 的注意力集中在增量 + 從未被審的維度,而非重刷全表。
4. **reviewer tier 隨重點調**:純裁決一個 finding → Opus;廣角逼一批未想到的優化 → Fable 5。

**誠實記**:skill-bettor 目前**沒有任何一次真實交接歷史**,本節方法論是為第二輪以後預留的紀律——首次使用本 skill 時無「上次」可比,等同全量交接。這與 antigravity(已有至少一輪交接歷史可差量)不同,不要假裝已經有第二輪可比對。

**為何**:高 tier reviewer 的邊際價值在**新增/未審**表面,不在複述上次結論;差量交接把有限的高推理預算投在真正的增量前沿。

## Sources / 錨
- worked instance(外部,結構參考用,非本地內容):antigravity `docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md`。
- 設計 SSOT(本地):`.claude/skills/loop-harness-standard/{SKILL.md,modules/harness-spec.md,modules/evals-design-method.md}`。
- tier-dispatch 權威錨(本地):`ARCHITECTURE.md` §5(tier-dispatch 路由表＋硬約束①-④)、§7(防退化鐵律)。
- agy 角色邊界(本地):`ARCHITECTURE.md` §5「DR/跨家族複核」行、`loop-harness-standard` SKILL.md 基座卡「6 獨立 verifier」行。
