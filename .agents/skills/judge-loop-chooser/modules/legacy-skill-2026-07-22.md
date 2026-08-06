# Module: legacy SKILL.md snapshot — loss-audit source, not active workflow

> 屬 [`judge-loop-chooser`](../SKILL.md)。本檔是 `git show HEAD:.claude/skills/judge-loop-chooser/SKILL.md`
> 的保真快照,用途只有一個:重構/壓縮/state graph 化後的 semantic-loss audit。
> **不要把本檔當 active 指令執行**:current workflow 以 [`../SKILL.md`](../SKILL.md) 為準;
> 本檔內的舊狀態詞(例如早期 `path-b-reduction` 未移植、D1-D4 舊表)只代表被保留的歷史語意與對照基準。

---

---
name: judge-loop-chooser
description: |
  把一個可判的 deliverable 路由到它該用的驗證標準與獨立性 tier —— 在 skill-bettor 這代表
  演化 op 的 verify.sh／runner.py --compare 聚合結果、holdout 畢業判決、DR proposal、
  spawn 新家族判斷(不是程式碼改動,那條分支已有內建 code-review 承接,本 skill 不重複)。
  recipe-not-engine：只路由＋SURFACE,不執行、不自動接受任何判官／評分,人 admit 最終。
  三態 grounding(technical_equivalent／candidate／[推論])＋四層獨立性階梯(T0-T3)＋意圖漂移探針。
  何時用：一次演化 op 收斂／一次 holdout 畢業／一份 proposal／一個新家族決策要選驗證標準＋獨立性 tier 時。
  NOT for：審一段程式碼改動(內建 code-review);建/驅動演化小迴圈本身(loop-harness-standard);
  查證單一外部 claim(external-verify)。完整 know-why 在 modules/。
---

# Skill: judge-loop-chooser — 把可判 deliverable 路由到驗證標準 + 獨立性 tier

> **Role**:
> 給一個**可判的 deliverable**
> (skill-bettor＝演化 op 的 T0 聚合結果／
> holdout 畢業判決／DR proposal／
> spawn 新家族判斷),
> 選它該用的**驗證標準**
> (三態 grounding + 意圖漂移探針)
> 與**獨立性 tier**(T0/T1/T2/T3)。
> **只路由 + SURFACE,不執行、不自動接受任何判決**
> —— 人出閘是結構性的
> (recipe-not-engine,同 ARCHITECTURE.md §8 人閘清單)。
>
> **結構**:
> SKILL.md = 路由決策樹 + 不變量 + Gotchas;
> 兩軸為何正交／各 tier 破什麼的 know-why 在
> [modules/grounding-and-independence.md](modules/grounding-and-independence.md);
> 零存取意圖審查 payload 在
> [modules/intent-drift-review.md](modules/intent-drift-review.md)。
>
> **SSOT**:
> 三態 grounding 的**活基座**＝
> 家族 `evals/runner.py` + `evals/judge.py`
> (program／absent／llm_judge 三種 check kind)+
> `evals/cases/` ＋ `evals/holdout/`
> (planted-defect fixtures,good/hollow 正控由
> `selftest.sh` 證)＋ ARCHITECTURE.md §4 Verify 三層。
> 獨立性驗證的活基座＝本地
> [`external-verify`](../external-verify/SKILL.md)
> (T2 事實錨)＋ ARCHITECTURE.md §5 tier-dispatch
> 硬約束(判官永不 Haiku／永不 agy-as-verdict)。
> 漂移時以 `families/*/evals/` 真跑結果 /
> ARCHITECTURE.md 為準。
>
> **Lineage**:
> port 自 antigravity `.agents/skills/judge-loop-chooser/`
> (其本身 port 自 northstar)。
> antigravity 的 deliverable 型
> (DR 報告／COMPLETENESS 覆蓋矩陣／
> Path B 精煉／技術選型 fit-to-plan)
> 在 skill-bettor **不存在對應資產**,
> 已誠實重建為 skill-bettor 自己的 4 型;
> antigravity 的三態 grounding
> ＋ T0-T3 獨立性階梯是**兩軸都可轉移的核心**,原樣映。
> 逐機制映射 + 拿掉/重建了什麼 →
> [modules/retarget-map.md](modules/retarget-map.md)。
> **非原樣搬**(原樣搬 = 引用不存在資產的死 husk)。

## 🚩 STOP — 你在合理化(違反即停)
| 念頭 | 現實 |
|---|---|
| 「llm_judge 給了 PASS,直接收下當完成」 | ❌ 無 auto-accept;PASS 是給人的證據,非放行令(ARCHITECTURE §8 人閘②/鐵律 3) |
| 「同家族(Sonnet author×Sonnet judge)自己審自己,反正都是 Claude」 | ❌ Same-Weights:同權重同盲點 → 必落地 fresh zero-context subagent(禁 fork);Opus 判 Sonnet 減緩但仍同 vendor,不等於跨家族 |
| 「G1-G3 --compare 全綠,就是真的抓到問題了」 | ❌ hollow-T0 placebo:program check 可能是空心 pattern(如 `pattern: 'lookahead'` 理論上連「沒有 lookahead 風險」的報告都會命中)→ 需 selftest good/hollow 佐證才算 technical_equivalent |
| 「這條 5-axis 技術選型 fit-scoring 要不要也搬進來」 | ❌ skill-bettor 沒有 OSS 堆疊選型情境,且餵軸的 3 個技能本地無基座,已誠實拿掉(retarget-map) |
| 「通過率 1.0、G 閘全綠,案例夠硬了」 | ❌ 通過率不是 grounding;2026-07-11 changelog 已明記「案例對強模型太簡單」——高分可能是案例太弱,不是 skill 真強(negative-space) |

## When to Use
- 一個演化 op 沙盒 T0 全綠、`STATUS` 轉 `candidate` 時,
  要判「G 閘的勾是真的還是空心」。
- holdout 畢業段要判「Opus fresh 判官的 verdict 該信到什麼獨立性 tier」。
- 一份 `proposals/` 的 DR 產出要判「該不該放行轉入某家族」。
- 要決定該不該 spawn 新子技能/新家族(人閘④)時,檢查決策證據是真缺口還是感覺。
- 要決定某個判決該靠 T0 確定性 / T1 零存取 / T2 跨家族 / T3 人。

## Not For
- ❌ 審一段程式碼改動(Standards/Spec 是否達標)→
  內建 `code-review`(程式碼變動走這條,不重複造)。
- ❌ 建/驅動演化小迴圈本身(dispatch、iterate-until-pass、stop-loss)→
  [loop-harness-standard](../loop-harness-standard/SKILL.md)。
- ❌ 查證單一外部 claim 的真假 →
  [external-verify](../external-verify/SKILL.md)
  (它是本 skill 的 T2 工具,不是替代)。
- ❌ 判「該不該造新 skill／怎麼寫」的 Claude Code skill 撰寫規範 → 內建 `write-a-skill`。
- ❌ 5-axis 技術選型 fit-to-plan 判斷 → 已誠實拿掉,見 retarget-map
  (skill-bettor 目前無 OSS 堆疊選型情境,且無餵軸技能本地基座)。

## 不變量(違反即停)
1. **recipe-not-engine**:只路由 + SURFACE。
   llm_judge 分數/跨家族 findings/G 閘全綠都**不可**
   auto-accept 一個 merge/畢業 verdict ——
   人出閘結構性(兩道人閘:ENTRY 選標的+標準、
   EXIT 收下 verdict;模型階梯只活在兩閘之間,
   同 ARCHITECTURE §8 人閘清單)。
2. **三態 grounding,不二元化**:
   technical_equivalent(check 錨到 planted-defect
   fixture 的**完整** selftest good/hollow 覆蓋)/
   candidate(fixture/rubric 真存在,覆蓋未掙,
   如 llm_judge `skipped`)/
   [推論](無真 fixture,bespoke pattern 空猜)。
   **candidate ≠ [推論]**(真 fixture 未驗 ≠ 沒 fixture)。
3. **獨立性看「誰的權重」,不是「誰更強」**:
   Sonnet author × Sonnet/Opus judge 都是 Claude vendor,
   同權重或同家族血緣;唯 agy(Gemini)findings 才真正跨家族。
   強 tier ≠ 獨立 tier。
4. **negative-space 不可約人**:
   changelog/proposal 要求但 diff/報告**靜默省略**的,
   既抗斷言又抗 packet-reproduce → 不可約 T2/T3。
   把線往下壓,永不壓到零。
5. **無 code-branch**:
   skill-bettor 的可判物是演化資產/proposal/家族決策,
   不是程式碼改動本身 —— 程式碼走既有 `code-review`,
   本 skill 不重複造一條判決表。

## 確定性程序(路由決策樹)

```mermaid
graph LR
  A[判 D1-D4 型] --> B[grounding 三態]
  B --> C[獨立性 tier]
  C --> D[SURFACE]
  D --> E[人出閘]
```

1. **判 deliverable 型**(load-bearing,寫在路由開頭):

   | # | deliverable 型 | 觸發時機 | 判什麼 | 主要驗證法 | 起始獨立性 tier |
   |---|---|---|---|---|---|
   | D1 | 演化 op T0 聚合(`verify.sh` exit + `runner.py --compare` G1-G3) | `STATUS` 轉 `candidate` 時 | G 閘全綠是不是真的服務底層缺陷偵測,還是空心 check 撐綠 | grounding 三態逐 check 判(program/absent/llm_judge 三種 kind 各查一次)+ selftest good/hollow 佐證 | T0(聚合本身)但「check 是否 hollow」需 T1 起 |
   | D2 | holdout 畢業判決(llm_judge checks + Opus fresh 判官 verdict) | 畢業段,只跑一次 | PASS/FAIL 是真的忠實評了品質,還是同家族/同 session 自我確認 | 三態 grounding(llm_judge 天生 [推論]-grade,除非 rubric 要求可勾稽證據)+ 獨立性階梯 | T1 起(必 fresh zero-context subagent,禁 Haiku) |
   | D3 | DR proposal(agy 產,`proposals/YYYY-MM-DD-<topic>.md`) | 轉入家族前,7 天 TTL 內 | claim 是否約分到可執行驗證,還是散文宣稱(Half-Bridge) | 三態 grounding 逐 claim +意圖漂移審查(對照原研究題目,見 [modules/intent-drift-review.md](modules/intent-drift-review.md)) | T2(agy 只產 findings,非 verdict) |
   | D4 | spawn 新子技能/新家族判斷(人閘④) | changelog 已知問題 → 該不該開新 op/家族 | 決策證據是真實覆蓋缺口(negative-space),還是主觀感覺 | 通常 [推論]-grade 戰略判斷,無 verify 層可套 | T3(不可約,LAND-DECISION) |

   D1 的 diff 本身若懷疑 Goodhart(G 閘綠但沒解決底層問題)、
   D3 的 proposal 若懷疑跑偏原研究題目,
   都套用 [modules/intent-drift-review.md](modules/intent-drift-review.md)
   的探針,而非另立判準。
2. **對每個選定的驗證方法,判 grounding 三態**
   (下方快查 / modules 決策樹)→ 標 anchor + provenance,
   或降 [推論]。
3. **判獨立性 tier**:
   verdict 能單憑封裝包(intent + artifact + rubric)
   在 zero-access 重現嗎?
   - yes → **T1 零存取**(fresh zero-context subagent,
     禁 fork,只破脈絡相關)。
   - no → **needs_diamond** → **T2 跨家族**
     (external-verify 官方源 / agy 跨家族 findings)/
     **T3 人**。
4. **SURFACE 輸出**(別自動接受):
   `可判項 | 驗證方法 | grounding 三態(anchor kind+ref) | 獨立性 tier | [推論]/不可約 T3`
5. **人出閘**:
   把矩陣 + needs_diamond 升旗交人 admit
   (merge admit / holdout 畢業 admit / 案例輪替 /
   spawn 決策 / 對外發佈,ARCHITECTURE §8 人閘清單)。
   **永不自動 chain 下一步**。

## grounding 三態快查(操作;完整決策樹 → modules)
```
驗證方法的判決能約分到「判讀一個真實 planted-defect fixture 的【完整】selftest good/hollow 覆蓋」嗎?
  ├─ yes → technical_equivalent,CITE anchor(check id + fixture 路徑 + selftest 結果)
  │        skill-bettor 合格錨:program/script check 對應 evals/cases 或 evals/holdout 下的真 fixture,
  │        且 selftest.sh 已證 good=PASS ∧ hollow=FAIL
  │
  ├─ 真實 fixture/rubric 存在但覆蓋未掙(如 llm_judge 無 --judge-cmd → status:"skipped",
  │        排除分母、不計失敗)→ candidate,標覆蓋狀態 + 來源;路由去掙覆蓋(SURFACE only,不跑、不自動升級)
  │
  └─ 無真實現 → [推論]-grade,誠實標:
       · bespoke pattern/regex 無否定排除(如 pattern:'lookahead' 理論上連「沒有 lookahead 風險」的
         報告都會命中)—— 不判任何真實現 = 空心-T0 placebo
       · llm_judge 判斷(PASS/FAIL) —— 給人證據,非放行令
       · external_primary(external-verify 抓的官方事實)—— 相鄰事實錨,非方法-執行等價物,另列
negative-space(changelog/proposal 要求但診斷/報告靜默省略的)→ 既無真錨又抗 assertion → 不可約 T3 人
```
> 這正是 ARCHITECTURE.md §4「① T0 機械 / ② 行為 / ③ semantic 判官」
> 逐層要的紀律 —— 本 skill 把散在
> §4 表格裡的判準升格成「逐 check / 逐 claim」可判標準
> (判「G 閘的勾是真的還是空心」)。

## 獨立性階梯快查(cheapest first;完整 know-why → modules)
```
T0 確定性 —— exit-code / verify.sh 聚合 / runner.py --compare / selftest good-hollow
              → 無權重,破【脈絡+權重】兩半。最大化這份額。
T1 零存取 —— fresh zero-context subagent(Opus,禁 fork)+ 封裝包(intent+artifact+rubric),無 drafting 史
              → 只破【脈絡】相關。同家族(Sonnet author × Sonnet/Opus judge,皆 Claude vendor)必落地
              此層,packet-reproducible 時信。
T2 跨家族 —— external-verify 官方源 / agy(Gemini)findings 複核(非 Claude 審 Claude)/
              [antigravity 的 path-b-reduction,cross-repo,未移植 —— 見 retarget-map]
              → 唯一【觸】權重相關(僅三角測,非解決;共享網路語料盲點仍在)。
T3 人 ——— 最終 LAND-DECISION(merge admit / holdout 畢業 admit / spawn 決策 / 對外發佈,
              ARCHITECTURE §8 人閘清單)。
```

## Gotchas
- **description 別混 ASCII `冒號+空格`**:
  出現在 frontmatter description 任一處 → YAML 解析成
  mapping → 整個 skill 被靜默跳過(連名字都 recall 不到)。
  多行一律 `|` block scalar、用全形「：」。
- **通過率/案例分數不是 grounding**:
  2026-07-11 changelog(`families/pinescript-audit/changelog/`)
  已明記 repaint-detection 案例「對強模型太簡單」——
  對照組(無 skill)在內容層其實也找得到 bug,
  Δ 主要量在介面契約遵循而非真偵測力;
  高分/高通過率不代表已服務「找到真缺陷」的原始意圖,
  可能是案例太弱。
- **llm_judge 的 `skipped` 是 candidate 不是失敗**:
  `judge.py` 對缺 `--judge-cmd` 的 llm_judge check
  標 `status: "skipped"`、排除分母 ——
  這是「真 rubric 存在,覆蓋未掙」的字面例子,
  別誤判為 [推論]或失敗。
- **pattern check 缺否定排除 = 潛在 hollow-T0**:
  `judge.py` 的 `_find()` 只做子字串/regex 命中,若
  pattern 未排除否定語境
  (如 `pattern: 'lookahead'` 結構上也會命中
  「沒有 lookahead 風險」的報告),命中
  不等於偵測到真缺陷 —— 本地尚未觀察到此案例實際觸發
  (現有 run 皆為真陽性,見 retarget-map),但這是
  check 設計本身要覆核的結構性風險,不是可以略過的假設性宣稱。
- **agy quota 耗盡 = 零輸出 exit 0**
  (判 D3 proposal 可用性時適用):
  可用性判據＝輸出檔非空且合法,
  **非 exit code**(silent no-op)——完整 gotcha 見
  [loop-harness-standard](../loop-harness-standard/SKILL.md)
  同名條目,不在此重複列。
- **無機器閘判 grounding 本身**:
  skill-bettor 對 T0 聚合(`verify.sh`/`runner.py --compare`)
  有真機械閘,但「check 是否 hollow」與「grounding 三態」
  本身沒有機械閘 —— 仍 **SURFACE-only**,人 VERIFY。
  別把 G 閘綠誤讀成「grounding 已判過」。
- **一致性 ≠ 正確性(借來的教訓,非本地實測)**:
  antigravity 的 `truth-verify-loop`(未移植)量過
  「跨家族一致 SUPPORTED 仍騙過雙家族判官」與
  「可判卻標 UNVERIFIABLE 的棄權盲區」兩種 agreement-gated
  review 結構洞 —— 這是可轉移的**警示**,
  不是 skill-bettor 自己的數據;
  skill-bettor 尚無類似量測迴圈,
  若未來真的跑一輪 D2 畢業判官對照實驗,
  結果記在該家族 `changelog/`,不是繼承 antigravity 的數字。

## 執行漂移探針(敘事層 vs 執行層;2026-07-19 fold)

既有意圖漂移探針(modules/intent-drift-review.md 的 SI1-SI8)
審**敘事層**:產物/計劃是否服務原意圖。
本節加一個正交維度=**執行層漂移**:
方向沒漂(所建之物都服務中心),但**「該收手的點」漂了**——
在最便宜、最決定性的驗證問題(有沒有人買/需求成不成立)
還沒答之前,持續往下游建造。

**執行漂移探針**
(判「這個執行是否越過了『繼續建造已不再是對的動作』那一刻」):
1. **供給/基建比例倒掛**:
   核心產品產出 vs 基建/計劃/自我審計的比例是否倒掛
   (如轉化只做 1/92、基建/計劃/條款/審計佔 95%+)。
2. **最大未知被後推**:
   需求/WTP(最大未知)是否被推到所有基建之後——
   違 MVP「先打最大未知」。
3. **核心賣點的證據只能靠跑卻沒跑**:
   如「每天變強」只有 1 個點(快照非曲線),
   護城河命題零數據支撐。
三者任一成立=執行漂移(方向對、時機錯)。
判定=正反雙 fresh Opus 判官對辯(各預寫對方反駁)合成。

> **自指警示**:
> 「審計是否審計過度」的審計本身可能就是過度審計的實例——
> 裁決做完即停,不遞迴。
> 防回退錨:
> `docs/plans/2026-07-18-aie-master-plan/91-execution-drift-verdict.md`
> (供給 1/92 vs 基建海量、WTP 零驗證,兩 lens 共識 DRIFT;
> 金句「機器在中心上、生意漂了」=方向沒漂該收手的點漂了)。

## Modules
- [modules/grounding-and-independence.md](modules/grounding-and-independence.md) —
  兩條正交軸的 know-why:
  grounding 三態(錨到 `evals/runner.py`+`evals/judge.py`+`evals/cases`)+
  四層獨立性階梯(whose-weights、Same-Weights 陷阱、
  packet-reproducible 判準)+ 為何正交(hollow-T0 cell)。
- [modules/intent-drift-review.md](modules/intent-drift-review.md) —
  零存取戰略意圖 reviewer payload(SI1-SI8 + needs_diamond),
  retarget 成「演化 op diff 是否服務原 `PROMPT.md`／proposal／
  changelog 意圖」與「DR proposal 是否服務原研究題目」兩個場景。
- [modules/retarget-map.md](modules/retarget-map.md) —
  antigravity → skill-bettor 逐機制映射表 +
  **誠實拿掉/重建了什麼**
  (deliverable 型全換、5-axis fit-scoring 拿掉、
  path-b-reduction 未移植)+
  為何拿掉不是簡化而是「不引入不存在的資產」。
