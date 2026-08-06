---
name: skill-authoring
description: |
  skill-bettor 的 skill 設計規範(家規層)——新建/重構/審查本 repo 任一 skill 前先讀。
  涵蓋:兩類 skill 的分界(families/ 領域資產 vs .claude/skills/ 工程編排)、Claude Code 格式
  checklist、slim+modules 拆分、語意真相/低壓縮產出契約、semantic loss ledger、legacy snapshot、canonical terms、canonical 指針頭注慣例、固化範例指針。
  觸發詞:新建 skill、skill 規範、skill 設計、frontmatter、固化範例、skill-authoring。
  NOT for:判「該不該新建」(先走 fold-in 不變量 1);通用 Claude Code 格式細節(內建 write-a-skill)。
---

# Skill: skill-authoring — skill-bettor 的 skill 設計規範(家規層)

> **Role**:內建 `write-a-skill` 管 Claude Code 平台通用格式;本檔只管
> **skill-bettor 家規**—— 兩類 skill 的分界與各自規範、本 repo 的慣例。**本檔自己
> 也用此規範寫(dogfood):slim+全形冒號+ 指針不抄**。「該不該新建」的判準不在本檔——先走
> [fold-in](../fold-in/SKILL.md) 不變量 1 (預設 fold 不造新;真未覆蓋
> niche+人核才新建)。

## 兩類 skill 的分界(skill-bettor 特有,最重要的一條)

| | **領域資產 skill**(`families/<family>/`) | **工程編排 skill**(`.claude/skills/`) |
|---|---|---|
| 給誰用 | 訂閱者的 agent+eval harness 的被測體 | 大迴圈(主 session)自己 |
| 品質閘 | **eval 分數**(runner.py G 閘+holdout+人 admit)——這是產品,曲線=賣點 | selftest/自審——這是工具,壞了自己疼 |
| 改動路徑 | **只准走演化 op 沙盒**(proposals→verify→diff→eval→admit),直接 Edit=違反知識單向流 | fold-in 直接 Edit(additive,commit 說 why) |
| 結構契約 | 路由器 SKILL.md(只地圖)+子技能(<500 行+references/+scripts/)+shared/(引用不複製) | slim SKILL.md(確定性程序+Gotchas)+modules/(know-why)+retarget-map(若為移植) |
| 觸發設計 | description 要 pushy(模型傾向 under-trigger),列具體語境;受 trigger-evals 正交性檢查 | 觸發詞明列;NOT for 指向鄰接 skill 防互搶 |

**分界判準**:內容會被 eval 判分、會發佈給訂閱者 → 家族;內容是「怎麼運營這個工廠」→
`.claude/skills/`。 混放=把工廠說明書賣給客人,或把商品當內部工具改(繞過 eval 閘)。

## 確定性 checklist(新建/重構前逐項)
```
[ ] 1. 先過 fold-in 不變量 1:確認是真未覆蓋 niche+人核,不是 husk/domain-fact 傾倒
[ ] 2. 目錄式:.claude/skills/<name>/SKILL.md(全大寫);name 小寫-連字號
[ ] 3. frontmatter description 用 | block scalar;全文禁 ASCII 冒號+空格(YAML 靜默跳過整支 skill,
      連名字都 recall 不到)——一律用全形「:」;觸發詞+NOT for 必列;官方硬約束
      (name≤64/description≤1024/body≤500 行/禁保留字)機械閘=`scripts/check_skill_conformance.py`
[ ] 4. slim:SKILL.md 只留 Role/When to Use/Not For/確定性程序/不變量/Gotchas/Modules;
      know-why 一律下放 modules/(排版拆行不算違反 slim——slim 管內容取捨,不管換行數,見條款 11)
[ ] 5. 語意真相與低壓縮產出契約:skill 本文與該 skill 會產生的計畫/報告/派工包,
      都必須讓 fresh LLM 在缺乏對話上下文時仍能判斷:原始意圖、被判物、證據、grounding、
      actor、validator、human admit、failure edge。不得把「追求語意真相」壓成口號;
      需要選 Opus/Codex/agy/腳本時,要寫語意角色、不可替代理由、可見輸入、輸出責任、
      以及何時停止或升級。產物若只寫「按需驗證」「處理相關問題」「Opus or Codex or agy」
      這類模糊占位,等同 skill 失敗,即使 SKILL.md 本身寫得清楚也不收。
[ ] 6. 流程/路由類 skill 若有 ≥3 個條件分支、actor/validator 選擇、或跨 skill 組合,
      主 SKILL.md 必須寫 stateful workflow 契約:Match/Generate/Validate 節點、conditional edge、
      route-ledger 或等價決策帳、grounding 標籤(technical_equivalent/candidate/[推論]/human_required);
      每個節點寫目的、輸入、判準、輸出、gate、failure edge。slim 只代表 know-why/歷史下放
      modules,不代表把 load-bearing 路由語意壓成單一 prompt。Opus/Codex/agy/腳本按語意角色
      定責,不得留下未裁決三選一。細節可在 owner skill,家規只收抽象條款+活例指針(防雙圖漂移)。
[ ] 7. 既有 skill 重構/壓縮/狀態機化前,必做 semantic loss ledger:逐條對照舊版語意,標
      ACTIVE_IN_SKILL / PRESERVED_IN_MODULE / LEGACY_ARCHIVED / CANONICAL_OWNER_WITH_LEGACY_COPY;
      每列至少有 old_semantic_unit、classification、current_durable_home、check。domain-bearing
      舊文若不留在 active SKILL.md,必須逐字保存在 `modules/legacy-skill-YYYY-MM-DD.md`
      或等價 module,並由 SKILL.md Modules 區引用。domain 專有名詞必建 Canonical Terms
      或指向既有 glossary;禁止靜默刪除、改名或讓 fresh LLM 猜。
[ ] 8. 移植類必附 modules/retarget-map.md(誠實帳本:搬了什麼/拿掉什麼/為何拿掉不是簡化);
      引用外部 repo 的規範一律「canonical 指針頭注」——指針不抄內容(防雙圖漂移)
[ ] 9. 禁 dangling 編號 jargon:引用決策碼/不變量帶一句語義或磁碟路徑
[ ] 10. 含確定性邏輯 → 該邏輯必須真在 load-bearing 檔案落地(runner.py/engine.sh/腳本),
      skill 只指向;無鐵錨的「已優化」散文=husk,不收;skill 目錄內附帶可執行腳本時
      另過條款 f(聲明式調用+注入=執行半徑安全面),見 modules/authoring-clauses.md
[ ] 11. 新 skill/load-bearing 檔落地後同步登記:①迴圈類回 harness-wiki 組件卡 ②工程層回
      modules/panorama.md 名片 ③新 load-bearing SSOT 檔加進 defense-form-ssot 指針清單
      ——機械閘=`check_card_sync.py`(名片)+`check_ssot_index.py`(指針無懸空);先落地才登記
[ ] 12. 人面可讀性三條款(雙受眾分離/拆行不拆量/條件配圖)過一遍,見
      modules/authoring-clauses.md;重排版類修改另跑 diff 自審(除排版與新增圖外零內容變更)
[ ] 13. families 分發資產另過安全與品質左移(安全四項+fluff 黑名單 grep)——工程編排
      skill 不適用本項,見 modules/authoring-clauses.md+modules/fluff-blacklist.txt
[ ] 14. family eval skill 進 production/evaluated 前,`evals/cases/<skill>/` 必須通過
      `scripts/check_case_baseline.py`:10-20 cases、positive/negative 各 ≥5、每案 expect.yaml
      schema/rubric/弱斷言檢查、near-duplicate ratio ≥0.95 一票否決。incubating 且明確標
      eval harness 下一 op 的 family 不假裝已覆蓋;要畢業就先補 cases。
[ ] 15. 工程編排 skill 若主要產物是 packet/route/decision object,不要錯套 family case 閘;
      要新增專屬 behavior validator + skill-local `cases.json` + 10-20 cases +
      `should_trigger` true/false 各 ≥5 + positive/negative 各 ≥5,並接入 `check_all_skills.py`
      與 defense-form-ssot 指針清單。unknown-discovery-composer 的物理錨=
      `scripts/check_unknown_discovery_routes.py`。
```

## 固化範例(worked examples,新 skill 照這些寫)
- **地圖類**:[harness-wiki](../harness-wiki/SKILL.md)——組件卡+不變量+
  「只指針不抄」鐵律+誠實現況標記。
- **規範類**:
  [loop-harness-standard](../loop-harness-standard/SKILL.md)
  ——組件卡+鐵律+Gotchas 帶 「已解/禁回退」錨+modules 拆分。
- **程序類**:[fold-in](../fold-in/SKILL.md)——確定性程序+不變量+四路決策樹+
  actuator 委派。
- **營運類**:[product-ops](../product-ops/SKILL.md)——runbook 型
  (每步綁真實指令與真檔案), 只執行不重定義(紅線在 PRODUCT.md、規範在
  loop-harness-standard,雙向指針不重抄)。
- **領域資產類**:`families/pinescript-audit/`——路由器+子技能+shared+
  evals 全套結構契約。

## Gotchas
- **ASCII 冒號+空格是最貴的一個字元**:出現在 frontmatter description 任一處 →
  YAML 解析成 mapping → 整支 skill 靜默消失。多行一律 `|` block scalar+全形
  冒號。
- **改 skill 後同 session 觸發 ≠ 最新版**(2026-07-11 實測):Skill 工具可能
  載入註冊時的快照, 剛 commit 的段落不在其中。驗證一律以磁碟檔為準(`cat` 檔案),
  別用「觸發後看到什麼」當驗收。
- **Edit 錨字串先 Read 目標行原文**(2026-07-17 三次實撞):本 repo skill 檔多用
  全形標點 (「，」「（）」「：」),context 裡的轉錄常變半形 → Edit old_string 必
  miss。已解:先 Read 再 Edit; 仍 miss 時用 python 子串定位替換。禁回退用「憑
  context 記憶直接 Edit」。
- **家族 skill 不在本規範管轄的部分**:家族內容品質由 eval 閘裁,不由本 checklist 裁——本
  檔只管 「結構契約」那一列;想改家族內容,去開演化 op。
- **建迴圈類 skill 前**先對
  [loop-harness-standard](../loop-harness-standard/SKILL.md)
  八大基座 組件卡核設計規範,防 authoring 時把基座規範飄移。
- **行為指引型 skill(紀律/流程類,無確定性邏輯可 1:1 測)的評測法＝行為遵循消融**:乾淨 cell 雙
  臂 (with/without SKILL.md)+pre-registered 期望表+機械斷言+人工覆核,量紀律
  軸轉移 delta;方法 SSOT＝
  `/Users/neon/antigravity/.agents/skills/antigravity-skill-authoring/modules/skill-verification-methodology.md`
  §行為指引型(2026-07-20 dr-to-mvp 自測 delta +2.16/4 軸實錨)。**副產:
  trigger-evals 缺的 runner 接線 答案**——model-triggered=
  PreToolUse hook matcher `Skill`;顯式 `/skill`=
  `UserPromptExpansion` hook (官方 hooks.md:1181,兩路互斥)——
  `families/pinescript-audit/evals/trigger-evals.json`「尚未接
  runner」 的已知簡化自此有官方+實測雙錨的接法(指針,實作待該家族 op)。
- **行密度自查用 max 非 mean**(平均值幻覺):表格/URL 長行豁免須在 commit message
  列明——詳 modules/authoring-clauses.md。
- **L2 行為消融 eval 的 marker 必 skill-specific**(2026-07-20 試點錨):量 skill 淨值
  只計「該 skill 獨有機械」的 marker(A 有 B 無),**別把 base model 本來就會的通用能力
  算進 skill 功勞**(否則高 delta=假象,同「案例太簡單」陷阱行為層版)。判官試點帳=
  `docs/plans/2026-07-20-skill-spec-decompression/logs/L2-ablation-judge-loop-chooser.md`。
- **重構不是摘要**:既有 skill 被壓縮、狀態機化或 modules 重分層時,必先用穩定 baseline
  (`git show <commit>:<path>`,不要用會漂移的 `HEAD~N`)對照目前檔案列 semantic loss ledger。每條
  舊語意只能落四類:ACTIVE_IN_SKILL(主檔必保留)、PRESERVED_IN_MODULE(明確 module 指針)、
  LEGACY_ARCHIVED(逐字舊文封存)、CANONICAL_OWNER_WITH_LEGACY_COPY(正確 owner + 舊文仍可追溯)。
  不接受 deleted/retired 當成功狀態。Domain 專有名詞必進 Canonical Terms 或既有 glossary;不能因 slim
  消失。舊語意若不在 active SKILL.md,必須保留在 module 並由 SKILL.md Modules 區引用。活例：
  - [unknown-discovery-composer semantic-loss-ledger](../unknown-discovery-composer/modules/semantic-loss-ledger.md)
    + [domain-lexicon.md](../unknown-discovery-composer/modules/domain-lexicon.md)
    + [legacy-skill-2026-07-22.md](../unknown-discovery-composer/modules/legacy-skill-2026-07-22.md)
  - [dr-to-mvp semantic-loss-ledger](../dr-to-mvp/modules/semantic-loss-ledger.md)
    + [domain-terms-and-intake.md](../dr-to-mvp/modules/domain-terms-and-intake.md)
    + [legacy-skill-2026-07-22.md](../dr-to-mvp/modules/legacy-skill-2026-07-22.md)。
  - [judge-loop-chooser Semantic Loss Ledger](../judge-loop-chooser/SKILL.md)
    + [legacy-skill-2026-07-22.md](../judge-loop-chooser/modules/legacy-skill-2026-07-22.md)。
- **流程類 skill 禁壓掉路由語意**(2026-07-22 sdlc-plan-composer fold):
  slim 不是把 state graph 壓成單一 prompt;若該 skill 負責路由/組合/驗證策略,主檔必須保留
  節點目的、輸入、判準、輸出、gate、failure edge。know-why/歷史下放 modules,但 load-bearing
  決策語意留在 SKILL.md。活例：
  [sdlc-plan-composer](../sdlc-plan-composer/SKILL.md)、
  [judge-loop-chooser](../judge-loop-chooser/SKILL.md)、
  [unknown-discovery-composer](../unknown-discovery-composer/SKILL.md)。
- **語意真相必須傳到產物**:skill 本文寫清楚但產出的 plan/report/dispatch packet 又壓成
  `Opus or Codex or agy`、`按需驗證`、`處理相關問題` 這類模糊語,仍算失敗。
  產物必須帶足上下文,讓 fresh LLM 不讀原對話也能知道判什麼、憑什麼、誰判、何時停。
  對語意裁決類產物,還必須寫清 original_intent_ssot、artifact_under_judgment、
  semantic_question、grounding_state、independence_tier、needs_diamond、human_gate;
  缺任一項即不能把 findings 交給下一個 LLM 當可判輸入。

## Modules
- [modules/panorama.md](modules/panorama.md) — skill 層業務全景圖
  (17 支名片+主流程圖+ 外部標準對照;人面投影,pointer-only;新 skill 落地/退場時
  additive 更新)
- [modules/authoring-clauses.md](modules/authoring-clauses.md)
  — checklist 9/11/12 全文 (附帶腳本/雙受眾分離/拆行不拆量/條件配圖/安全左移/fluff 自查)
- [modules/fluff-blacklist.txt](modules/fluff-blacklist.txt)
  — 條款 e 的 no-op 詞黑名單(canonical)
- [modules/defense-form-ssot.md](modules/defense-form-ssot.md)
  — 終極防禦形態 SSOT 歸屬索引(誤改防護地圖。§A 物理閘全表=每閘驗什麼;§B skill 階段的
  提示詞/判斷邏輯/資料流歸屬;**§C 執行分層契約**=何時跑、什麼刻意不接、為什麼,含 known-red
  隔離帶與週期語意——`ARCHITECTURE.md` 鐵律 10 要求新閘落檔即宣告層,指的就是 §C;
  指針不抄,改階段前先查;物理遵守=scripts/check_ssot_index.py 驗指針無懸空 + §C 分層完備性)
