---
name: truth-verify-loop
description: |
  真相驗證量測迴圈——對文章/概念/重大 claim 集跑「抽取 claims→分批多 tier worker 驗證→跨家族
  聚合→Opus fresh 判官→純腳本計分→落帳」的閉環方法論+本地實例化契約。2026-07-17 自 antigravity
  port(人裁 Q7,計劃包 2026-07-17-agent-native-sdlc-panorama);四角色分工中 agy「查詢真相」的
  迴圈化形態。**本地引擎尚未實例化**——引擎/合約/工具鏈的上游 SSOT=antigravity `truth-verify/`
  (同機唯讀指針),首次真跑時按本檔實例化契約建 `loop_wiki/tv-<topic>/` 沙盒,先 selftest 後真跑。
  觸發詞:truth-verify、真相驗證迴圈、claims 逐字驗證、多 tier 事實查核、跨家族聚合驗證。
  NOT for:驗證標準/獨立性 tier 的選擇(judge-loop-chooser);單一外部 claim 查證不必開迴圈
  (external-verify);claim 約分落帳紀律(path-b-reduction);skill 變現情報批次(dr-research-loop)。
---

# Skill: truth-verify-loop — 真相驗證量測迴圈(方法論+本地實例化契約)

> **Role**:把「查詢真相」從單點查證升級為可量測閉環:claims 抽取→worker 驗證(多 tier+跨家族)→
> 聚合→判官→**純腳本計分 vs sealed 真值**→落帳。本檔=方法論+防誤改不變量+首次實例化工序;
> **永不抄上游內容**(抄=會漂的第二份)。
> **上游 SSOT(同機唯讀指針,2026-07-17)**:引擎=`/Users/neon/antigravity/truth-verify/t0/*.{sh,py}`;
> 合約=`.../truth-verify/contracts/`(+`contracts/dispatch/` 逐字模板);帳本範例=`.../truth-verify/
> {hypotheses.md,loop-ledger.md}`;原版地圖=`/Users/neon/antigravity/.agents/skills/truth-verify-loop/`。
> **誠實態**:skill-bettor 側零 run 歷史、引擎未實例化——本檔先於引擎存在是刻意的(人裁 Q7「現在
> 就 port」),但**用前必走 §實例化契約,禁直接引用上游路徑跑**(上游 fixtures/sealed 是 antigravity
> 的證成軌跡,不是本 repo 的證據)。
> **Lineage**:antigravity truth-verify-loop(承 kb-ingest judge-loop 收斂原語);逐機制取捨帳=
> [modules/retarget-map.md](modules/retarget-map.md)。

## When to Use
- 一份文章/概念集/重大 proposal 的 claims 需要**可計分**的多 tier 驗證(不只 findings,要 vs sealed
  真值的檢出率),或同一驗證要跨家族(Claude×Gemini×GPT)聚合抗單模型盲區。
- 要複用/擴充這條量測迴圈:換題目(重生 fixtures 四件套)、加 config 軸、開新 pin。
- 改它任一階段(合約/工具/判官 dispatch)前——先讀本檔不變量,防閉環被誤簡化。

## Not For
- ❌ 「這個 deliverable 該用什麼驗證標準/tier」→
  [judge-loop-chooser](../judge-loop-chooser/SKILL.md)
  (本迴圈是其語彙的一個實例)。
- ❌ 單點外部 claim 查證 →
  [external-verify](../external-verify/SKILL.md)
  (本迴圈 worker 內嵌其紀律;沒有量測需求就別開迴圈)。
- ❌ 約分/落帳誠實紀律的規範本體 →
  [path-b-reduction](../path-b-reduction/SKILL.md)
  (本迴圈全程執行它)。
- ❌ 原樣複製 antigravity 檔案進本 repo
  (其 `AGENTS.md` Resolved 指針/KB ingest 鐵律/實測數字=該 repo 自己的基座與證成,
  搬過來=死 husk;取捨帳見 retarget-map)。

## 階段拓撲(指針;各階段合約/閘的 SSOT 在上游,實例化時 retarget 進沙盒)

```mermaid
graph LR
  A[抽取 claims] --> B[分批多 tier 驗證]
  B --> C[跨家族聚合]
  C --> D[Opus 判官]
  D --> E[純腳本計分]
  E --> F[落帳]
```

1. 抽取(T0 schema 閘)
2. 切批(type 過濾)
3. worker 驗證(多 tier;四值 claim 標籤 SUPPORTED/REFUTED/UNVERIFIABLE/…——
   **per-claim 機械可聚合輸出,非裁決**,裁決權仍受判官地板約束;+逐字引文)
4. 跨家族側(agy/codex)
5. 聚合(TYPE_C 跨家族必開)
6. 判官(fresh Opus,僅限定裁決範圍,step-0 T0)
7. bounce(T0 退件兩敗升 tier)
8. fold+終驗(最終 T0 必 PASS)
9. 計分(純腳本 vs `fixtures/_sealed/`)
10. 計量
11. 落帳。

## 本地實例化契約(首次真跑的確定性工序;完成前本 skill 只是方法論)

1. `cp -r loop_wiki/_template loop_wiki/tv-<topic>` 起手(八大基座骨架;engine.sh 不改——iterate/
   stop-loss 屬 engine,tv 工具鏈只是 verify 層)。
2. 自上游 cp `t0/` 工具鏈+`contracts/`(含 dispatch 模板)進沙盒,**逐檔 retarget 路徑**;
   `verify.sh` 適配=調 `t0/tv-preverify.sh`(真 exit 0/2,禁 LLM 模擬)。
3. MODEL_MATRIX 對映本 repo ARCHITECTURE.md §5(2026-07-17 擴充版):判官=**Opus fresh(禁 fork,
   永不 agy/codex-as-verdict)**;worker tier 可含 codex 檔(GPT=第四家族,TYPE_C 跨家族聚合更強);
   agy worker 唯讀 dispatch+quota tracer 前置;額度 fallback 按 §5 fallback 鏈,**禁 silent**。
4. fixtures 四件套(`articles/mutated/mut-config/_sealed`)+dev/holdout 切割**本地重生**(上游的
   sealed 是它的考卷,不搬);盲性拓撲先於 run 落檔。
5. `selftest.sh` good/hollow 正控綠(checker 活著)→ 才准真跑;判定式(門檻+停機)先於 run 落檔。
6. 落地(首次端到端真跑)後:回 [harness-wiki](../harness-wiki/SKILL.md) 組件卡 additive 登記一列
   ——**先落地才登記**(其 Gotcha 明訓),本檔落地前不登。

## 不變量(承上游 7 條,retarget 後;改任一階段時不准被簡化)
1. **同 pin 唯一變因**:假設檢定只認同 pin A/B;mid-run 禁改工具/合約/dispatch 措辭。
2. **盲性拓撲**:編排者與判官永不讀 `_sealed/`+`mut-config/`;計分=純腳本;判官另禁 mutated 原檔。
3. **質量閘不可簡化**:false-SUPPORTED=0 硬條件;共識盲區/棄權盲區只有播錯集看得見——播錯集不可拿掉。
4. **判官紀律**:fresh context、下限 Opus、永不 agy/codex;僅限定裁決範圍;改裁必 re-pass 同管線 T0。
   worker(含 agy/codex 家族)的四值標籤=**資料非裁決**——與 §5「只 findings 不 verdict」不衝突,
   裁決只發生在判官段與人(2026-07-17 codex 跨家族審計指出的措辭撞名,特此定界)。
5. **成本全額入帳**:壞包/棄用/救援成本入量測;跨密度禁直比。
6. **量測產物不入 `families/`**(隔離紀律同 proposals/:未經 eval 閘的東西不是資產)。
7. **agy=Gemini only 且唯讀**;silent no-op 判活看輸出檔;它的 token 記副軸不入主成本。

## Gotchas
- **WebFetch 是二手**:逐字驗證一律 raw fetch
  (上游 T0 內建 curl+HTMLParser);
  弱模型會把 fetch 摘要當原文(external-verify 同課)。
- **U+2019 直撇號**:worker 引文含直撇號→T0 假陰性;
  bounce 紀律=無撇號片段優先/text_quote 照抄。
- **模型自報不可信**(本地新增,2026-07-17 codex proof run 實測):
  worker/判官宣稱的自身 model 不作數,
  判實跑 model 看 driver session log(codex=`~/.codex/sessions/`)。
- **persona 注入**:tv 的 worker/判官若走 Task 子代理,
  受 ponytail SubagentStart 注入影響——
  判官型必須落在 `PONYTAIL_SUBAGENT_MATCHER` 之外
  (judge-loop-chooser 操作判準第 5 條)。
- **上游漂移**:本檔指針指向 antigravity 活 repo,
  其模組化/搬檔會使路徑過期——實例化時以 `ls` 實況為準,
  發現漂移回改本檔指針(不改方法論)。

## Modules
- [modules/retarget-map.md](modules/retarget-map.md)
  — antigravity → skill-bettor 逐機制取捨帳
  (搬了什麼/不搬什麼+why/本地新增)。
- 上游 know-why(六 run 實測課/E 主成分/tier 三明治/兩結構洞)=
  `/Users/neon/antigravity/.agents/skills/truth-verify-loop/modules/measurement-methodology.md`
  (指針不抄;那是上游的證成軌跡)。
