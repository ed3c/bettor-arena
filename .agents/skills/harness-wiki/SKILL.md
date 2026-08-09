---
name: harness-wiki
description: |
  skill-bettor 多迴圈全景 SSOT(組合架構地圖)——改任一迴圈階段/prompt/閉環前先查此圖,防止把閉環架構
  或不變量誤改/誤簡化。記錄已有迴圈(演化 op 迴圈/DR proposal 迴圈)的資料流歸屬+收斂閘+組合關係,
  並指針到各自 SSOT(不複製,避免雙圖漂移)。
  觸發詞:harness 全景、迴圈組合架構、改迴圈前查、閉環誤改防護、多迴圈 SSOT、harness-wiki。
  何時用:編輯任一迴圈邏輯、要看迴圈怎麼組合、要加新迴圈類型時。
  NOT for:跑某迴圈(去該迴圈自己的機制)、建/驅動新迴圈的工程規範(去 loop-harness-standard)。
---

# Skill: harness-wiki — skill-bettor 多迴圈全景 SSOT(誤改防護地圖)

> **Role**:skill-bettor 的「知識演化 harness」是小迴圈組件的組合。
> 本檔是那個組合的**地圖**——資料流歸屬、每迴圈收斂閘、
> 不可簡化的跨迴圈不變量。
> 改任一迴圈邏輯前查此圖,確保沒把閉環架構或不變量誤改。
> **與 [loop-harness-standard](../loop-harness-standard/SKILL.md) 的分工**:
> 本檔記錄**已有**迴圈長怎樣(組件卡),
> loop-harness-standard 定義**怎麼建/驅動新迴圈**(工程規範)。互指針不重疊。
> **誠實現況**:迴圈類型以「組件卡」為準,隨落地 additive 增列;不要憑舊硬數字推斷。
> 2026-07-19 前三條端到端已證:演化 op 迴圈、DR proposal 迴圈、dr-to-mvp Phase M 冷啟動 MVP 迴圈。
> 2026-07-20/21 後補 clc 字面推論挑戰迴圈、N-variant 執行反哺迴圈、dx-adversarial-fix 決策 cockpit。
> **2026-07-21 增第六類=dx-adversarial-fix 活對齊決策 cockpit**——**首個決策面迴圈**(非 eval/演化型):
> 藍圖↔實作對齊 gap 物理交付人裁,經 narration 閘(verdict_by 必 opus)+ 人 admit 派改善 Workflow;
> 端到端已跑(D1–D6 決策經此接進 check_all_skills 常設閘)。詳組件卡該列 + SSOT 索引。
> **2026-07-22 增第七類=plan-truth production seed loop**——首個「完美種子」型小迴圈:
> 把資料流歸屬、迴圈判斷邏輯、prompt/context 所有權、物理 packet、route-result、baseline/trend
> 統計與 production gate 全部落成可驗證資產。通用方法進 loop-harness-standard
> `modules/production-seed-loop.md`;本圖只記組件卡與 prompt registry 指針。
> 本圖維持「地圖」紀律(指針不複製、不可簡化不變量清單)——
> 組件卡隨新迴圈落地 additive 增列,不預先虛構欄位。
> **2026-08-03 增第八類=bounded perfect-seed repo factory candidate**——
> 針對 DR/GCR/repo/grill-me 四種物理輸入,重建一條不繼承 plan-truth 母體的大型庫存的
> bounded production-seed candidate；輸出 standalone repo＋repo-local skill＋精確 20-call DAG。
> 它目前是 `validated/candidate`，不是人已 admit 的「完美」真相。
> **2026-08-09 增 technical-equivalence research 小迴圈**——技術觀點經 hash-bound
> request／research／verification／fresh-judge packet 產 candidate sync bundle；proof 與 control
> 分離，offline／live carrier／fresh judge／Human admit 四軸分記。目前只證成 offline surface。

## When to Use
- 要**改任一迴圈邏輯/閉環**——先查此圖看該階段的資料流歸屬+不可簡化不變量,別誤簡化。
- 要看**整個 harness 怎麼組合**(小迴圈如何疊成每日管線)。
- 要**加一條新迴圈類型**——照「擴充原語」接上,不破既有組合。

## Not For
- ❌ 跑某條迴圈 → 去它的擁有機制(本檔只 MAP,不執行)。
- ❌ 判斷**怎麼建/驅動一條新迴圈**的工程規範(八基座/driver 選型/verify 分層)→
  [loop-harness-standard](../loop-harness-standard/SKILL.md)(本圖只記錄已有,不定義怎麼造新的)。

## 組件卡(每迴圈:擁有者 SSOT · 資料流 in→artifact→out · 收斂閘 · 證成狀態)

| 迴圈(組件) | 擁有者 SSOT | 資料流 in → artifact → out | 收斂閘 | 證成狀態 |
|---|---|---|---|---|
| **演化 op 迴圈** | [loop-harness-standard](../loop-harness-standard/SKILL.md) + `loop_wiki/engine.sh` | proposal/changelog 已知問題 → `loop_wiki/evolve-<family>-<op>/` 沙盒 diff → `scripts/runner.py --family <f> --compare`(2026-07-20 共享引擎) | `verify.sh` exit 0(T0)+ 畢業段 holdout 一次性 + 人 merge admit;新案例型 op 另有語意鑑別坐實段(多 tier 對照+Opus 判官,方法 → loop-harness-standard `modules/evals-design-method.md` §4) | **端到端已證**(proof-run=`loop_wiki/spawn-cases-semantic-traps`:iter1 真攔壞案例→iter2 三層閘全綠→人 admit merge b9a6265;成長曲線原點+41.7pp 見家族 changelog) |
| **DR proposal 迴圈**(skill 變現情報批次) | [dr-research-loop](../dr-research-loop/SKILL.md) + `loop_wiki/_template_dr/`(骨架)| `proposals/QUEUE.md` 題目 →(選配 Stage 1:訂閱池瀏覽器 DR raw=UNTRUSTED 支流,經 --feedback 注入)→ `loop_wiki/dr-<topic>/` 沙盒(engine.sh dispatch agy 主/claude 備/subagent 輕量)→ `proposals/YYYY-MM-DD-<topic>.md` | T0 四閘(schema/anchors/licenses/urls,含 L3 GitHub 授權實抓)exit 10 → judge-loop-chooser D3 findings(數字類 needs_diamond→external-verify)→ 人 admit(status→verified)+ 7 天 TTL 未過即歸檔;feedback 輪=run.sh 直發(已綠 target 不走 engine) | **端到端已證×14**(2026-07-11/12 市場情報×4:claude-code/codex/cross-market/pinescript-quant verified,末者 adopted 轉家族;2026-07-13 整合計劃 gap 批×10:全 verified→adopted 進 `docs/plans/2026-07-12-living-skills-plan-integration/gap-research/`,非家族;三池變體與 **agy 失敗模式五型**案例帳=dr-research-loop `modules/three-pool-pipeline.md`,指針不抄) |
| **mvp-radar**(dr-to-mvp Phase M 冷啟動 MVP 迴圈) | [dr-to-mvp](../dr-to-mvp/SKILL.md) + `loop_wiki/_template/`(骨架) | 種子草稿(既有 slice 文檔)→ `loop_wiki/mvp-radar/` 沙盒(engine.sh iterate-until-pass+stop-loss)→ homing 進 `families/aie-context/shared/runtime/internalization-radar/` | verify.sh T0 4 checks + dual-score 8 SC(設計分∧實作分 AND)+ 人 LAND-DECISION admit | **2026-07-19 conform_only 快路徑畢業**(判官帳=`loop_wiki/mvp-radar/logs/graduation-judgment.md`;沙盒保留,資產已 homing) |
| **N-variant 執行反哺迴圈**(sparse/blind 任務;oracle-gate=harness-spec §4.5) | [loop-harness-standard execution-feedback 模組](../loop-harness-standard/modules/execution-feedback.md);**wrapper 已退役**,承載改為 Workflow fan-out + 併發 Agent | 計劃斷言表(B-1 pre-registered)→ N 個併發 Agent 各跑一版 → 各自軌跡+APPROACH → 編排 session 派 fresh Opus 判官出 verdict → 勝者 diff / plan-delta 皆 SURFACE 給人 | dispatch 前假多樣機械擋 + verdict 機械勾稽(HELD 必附軌跡引用/plan-dir 乾淨/rerun 必過 no-smuggled)+ 逐斷言 HELD/REFUTED/UNOBSERVED + 人 admit | ⚠ **2026-08-07 退役**(人裁 #26)。此格原寫「selftest 已證(2026-07-19 落地:good/hollow 全過)」——**那句是假的**:`loop_wiki/engine_nv.sh` 從未存在(git 全歷史無 blob),其 selftest 的 8 條 case 一直以 exit 127 失敗,一個缺席的主體長得像八個壞掉的行為。退而非建的理由:同型工作已由 Workflow fan-out + 併發 Agent 事實承載,再建一個 shell wrapper 是造第二條路。**方法論不隨之退役**:斷言表 schema 仍在 harness-spec §4.5,四支 checker 仍在 `loop-harness-standard/scripts/execution-feedback/`;退的只是那個從未存在的 wrapper 與它的正控/治具 |
| **clc 字面推論挑戰迴圈**(等價 claim 自動攔截;把 7 輪人工挑戰自動化) | [skill-authoring](../skill-authoring/SKILL.md) METHODOLOGY + `scripts/check_equivalence_claims.py`(共享檢查器)+ `loop_wiki/clc/`(claims 語料) | 等價 claim「X≡gcr Y」→ `loop_wiki/clc/evals/claims.jsonl`(每 claim 帶物理錨)→ verify.sh live 重跑每個錨 → 分層對齊率(架構/組件/原子)+ 攔截無錨者 | verify.sh 報**兩率**(artifact-alive=錨解析/真等價=行為對照)+ selftest 三態;禁 artifact-alive 冒充等價 | **端到端已跑**(2026-07-20:自動發現 ablation selftest 離群→修正;artifact-alive 100% 但被「如何證明」拆穿→補行為對照,真等價率 72.2%(13/18);**2026-07-21 擴語料到全景 8 閘×gcr 12 機制→真等價 48.7%(19/39)**,+external-verify(gcr 源自 Schmid/SkillsBench 非幻覺)+codex/agy 對抗審計×Opus fresh 判官(拆 1 false-present/頂 1 誤 refute);錨=`loop_wiki/clc/EQUIVALENCE-VERDICT.md`) |
| **dx-adversarial-fix 活對齊決策 cockpit**(channel-B live server;藍圖↔實作對齊 gap 物理交付人裁,非 eval/演化型=決策面迴圈) | 本迴圈自身 `loop_wiki/dx-adversarial-fix/`(shell/data 分離)+ `scripts/check_narration.py`(敘述閘)+ `scripts/decision_router.py`(決策→composer 路由)+ 復用入口 `.claude/skills/html-for-decisions/scripts/open_decision_cockpit.sh` | 左欄孤兒/gap(gcr 段+完整防禦拓撲 6+1 tier,`_automation_map` source-read `check_all_skills` live 解析)→ 中欄 Opus 敘述決策([judge-loop-chooser](../judge-loop-chooser/SKILL.md) 語意真相)→ 網頁 POST → server narration 閘(過)+ stdout `DECISION:` 事件由 **Monitor** 串流接收(非 client long-poll)→ router 派改善 Workflow → `apply_improvement` 回流 → `/version` srcsig 自動刷新 | narration 閘(context≥60/why≥40/explain≥25/provenance **verdict_by 必 opus**;FAIL→409 擋 POST)+ POST 一次性狀態機(pending→ready→consumed,禁重放)+ 人 admit;閘與其他迴圈**不共用**(這是決策面非 eval 面) | **端到端已跑**(2026-07-21:D1–D6 決策 surfaced→人 admit→dist_safety/difficulty/P8–P12 經此人閘接進 check_all_skills 常設閘,commit 068af77/bab2d2a;左欄頂完整防禦拓撲 live 解析+disk liveness) |
| **plan-truth production seed loop**(完美種子母體;資料流/提示詞/統計/交付全硬化,非家族 eval 型) | loop-specific SSOT=`loop_wiki/evolve-unknown-discovery-plan-truth/{AGENTS.md,ROUTES.md,modules/plan-truth-dataflow.md,modules/exchange-formats.md,modules/production-readiness.md}`;通用方法=[loop-harness-standard production-seed-loop](../loop-harness-standard/modules/production-seed-loop.md);prompt registry=[modules/prompt-registry.md](modules/prompt-registry.md) | raw human constraint → `modules/semantic-truth-context.md` fixed context → packet inbox/outbox + `trigger.sh` exchange-context → route-result/baseline/trend/product/openwiki artifacts → human admit;大迴圈可指揮,小迴圈只回 evidence/findings | `verify.sh` + `selftest.sh` + `scripts/test_production_readiness.sh` + `scripts/replay_packets.py` + dataflow baseline check;固定數字以 `loop_wiki/evolve-unknown-discovery-plan-truth/baselines/dataflow-stats.json` 為準(含 openwiki template registry entry);收斂仍 human_required | **歷史 T0 證成、目前 known-red**(2026-08-03 live `verify.sh`=671/679 FAIL；plan-package/production-readiness/molecular-lineage 等閘紅，故不得用舊 361/361 receipt 宣稱 current production-ready；final repo 自身 pytest 16/16 綠只證 bounded local behavior) |
| **bounded perfect-seed repo factory**(四類 intake→standalone repo＋skill＋20-call DAG) | `loop_wiki/evolve-perfect-seed-repo-factory/{AGENTS.md,PROMPT.md,ROUTES.md,modules/architecture.md,modules/exchange-formats.md,modules/production-readiness.md}`;通用方法同上;prompt registry=[modules/prompt-registry.md](modules/prompt-registry.md) | admitted DR/GCR/repo/grill-me packet → minimum-lineage＋低成本 static preflight → hash-bound reduced IR(source/evidence/claims/unknowns/decisions) → versioned repo template → generated operator skill → exact 20 local calls/results → route-result/trend → human admit | `verify.sh` 先產 preflight-only receipt(minimum-lineage/Prettier/typed ESLint/strict-tsc)，再跑四 route、schema replay、baseline governance、template lifecycle、生成 repo tests；`trigger.sh` 同樣在 operator 前 fail-fast；`selftest.sh` good PASS/hollow skill-removed FAIL；`verify_generated_repo.ts` exact-20/dependency/human-gate/manifest confinement | **validated candidate**(2026-08-04：低成本 gate 已物理接線並有 format/lint/type hollow 控制；Code Quality／Production Use 異步 axis 仍未接 request/terminal receipt/stale/promotion，故不得宣稱 async-integrated 或 production-ready；尚未人 admit) |
| **technical-equivalence research**(技術觀點→實作等價候選) | `loop_wiki/evolve-technical-equivalence-research/{AGENTS.md,PROMPT.md,ROUTES.md,profile/technical-equivalence.md,modules/architecture.md,modules/exchange-formats.md,modules/production-readiness.md}`；proof=`proof_workflow/prove_equivalence.sh`；control=`proof_workflow/control_equivalence_entry.sh` | hash-bound viewpoint request → Gemini primary/gap research result → independent code-audit/probe/rebuild evidence → verification bundle → fresh-zero-context judge packet/result → candidate sync bundle → target-side Human admit | proof hash 完整 canonical inventory；control 在 committed disposable worktree 真跑、逐一移除核心輸入、植入 digest/judge-authority/HEAD-binding 缺陷；offline/live carrier/fresh judge/Human admit 四態分記，互不代理 | **offline_surface_implemented**(2026-08-09：離線 public seam 與成對 proof/control 已接；live Gemini 明確 opt-in，兩批 40 筆 judge calibration 與外部 Human admit 未執行，故不得宣稱 complete migration) |
| **Forgejo 大小迴圈操作橋**(工作狀態投影,非 Git writer) | [forgejo-loop-ops](../forgejo-loop-ops/SKILL.md) + 中央 schema=`skills/repo-neural-perception/schemas/` + output repo 的 `repo-terminal-operator` | grill／DR／GCR decision → bounded large-loop projection → 一個 hash-bound Forgejo request → existing Chrome 小迴圈 → repo-local terminal receipt → readback／next prompt | router cases/selftest + typed request schema + idempotency marker readback + repo-local CQ／production-use + 人 merge/admit；各閘互不代理 | **路由與 19-case 正負臂已證；既有 Chrome 登入已實操**。正式 repo bootstrap／selected issue／PR／merge 仍須各自 live receipt，不以路由綠冒充外部 mutation 完成 |

> 各迴圈的**收斂閘不共用**:
> 演化 op 迴圈的閘是「verify.sh 綠 + holdout 一次性」,
> DR proposal 迴圈的閘是「可執行驗證 + 7 天 TTL」,
> mvp-radar(dr-to-mvp Phase M)迴圈的閘是「T0 機械閘 + dual-score AND + 人 LAND-DECISION」,
> N-variant 執行反哺迴圈的閘是「4 機械 checker + 逐斷言勾稽 + 人 admit」——
> 合併會違反「各迴圈各閘,不共用不代理」不變量(見下)。

### 提示詞與判斷邏輯 SSOT 歸屬索引(2026-07-20;只指針不抄——改某迴圈的提示詞/閘之前,先在這裡找到它住哪)

| 迴圈 | 提示詞 SSOT(被動上下文/任務/判官) | 判斷邏輯 SSOT(閘/exit 碼) |
|---|---|---|
| 演化 op | 沙盒 `CLAUDE.md`+`PROMPT.md`(骨架=`loop_wiki/_template/`);llm_judge 判官 prompt=共享 `scripts/judge.py`(rubric 由家族 cases 提供);畢業判官 dispatch prompt=落該計劃/沙盒 `dispatches/` | 家族 `scripts/runner.py --family <f> --compare`(2026-07-20 共享引擎) G1-G5+`verify.sh`;engine exit 碼契約=`loop_wiki/engine.sh` 頭注(枚舉不複列,防副本漂移) |
| DR proposal | 沙盒 `PROMPT.md`(骨架=`loop_wiki/_template_dr/`);D3 判官 dispatch prompt=落 `dispatches/` | proposal schema 四閘=`proposals/README.md`+`_template_dr/scripts/check_*.py`;engine 同上(exit 碼契約見 engine.sh 頭注) |
| mvp-radar(dr-to-mvp Phase M) | 沙盒 `PROMPT.md`+**逐輪 driver/判官 prompt=`dispatches/round-NN.md`**(落檔慣例的原型) | 沙盒 `verify.sh` T0+dual-score AND(`DESIGN-SCORE.md` answer-key)+engine 同上 |
| N-variant 執行反哺 | `variant-*/APPROACH.md`+判官材料=`judge-materials.md`(**模板 SSOT 隨 wrapper 退役而空缺**——原宣稱住在從未存在的 `engine_nv.sh` 內嵌模板裡;下次真要跑 N-variant 時由該次的 Workflow 腳本現地定義,不預留假指針);斷言表=該計劃 `NN-slice.md`(B-1 schema,定義權=harness-spec §4.5) | exit 碼契約**無**(wrapper 已退役,2026-08-07 #26)+4 checker=`loop-harness-standard/scripts/execution-feedback/` |
| dx-adversarial-fix 活對齊 cockpit | shell 固定框架=`loop_wiki/dx-adversarial-fix/decision-shell.html`(零 LLM 維護);敘述內容=`decision-data.json`(Opus/codex/agy 產,增量物理更新);**判官敘述 provenance verdict_by 必 opus**(judge-tier 硬約束綁進 `check_narration.py`);決策→composer 路由=`decision_router.py`(judge-loop-chooser/unknown-discovery/sdlc-plan) | 敘述閘=`scripts/check_narration.py`(POST 前 context/why/explain/provenance→FAIL 409);POST 狀態機+version srcsig 自動刷新=`decision_server.py`;完整防禦拓撲=同檔 `_automation_map()`(source-read `check_all_skills` 的 STANDING/FAMILY_EVAL/難度/dist_safety/SKILL.md-linter,6+1 tier live+disk liveness) |
| plan-truth production seed | raw human constraint=`loop_wiki/evolve-unknown-discovery-plan-truth/modules/semantic-truth-context.md`;task contract=`PROMPT.md`;generated exchange context=`trigger.sh` + `_engine-run/exchange-context.<packet_id>.md`;完整 prompt/context owner registry=[modules/prompt-registry.md](modules/prompt-registry.md) | packet schema=`modules/exchange-formats.md` + `scripts/validate_exchange.py`;production gates=`modules/production-readiness.md` + `scripts/test_production_readiness.sh`;count drift=`scripts/compute_dataflow_stats.py` + `baselines/dataflow-stats.json`;human admit remains final |
| bounded perfect-seed repo factory | fixed semantic context=`loop_wiki/evolve-perfect-seed-repo-factory/modules/semantic-truth-context.md`;task contract=`PROMPT.md`;generated context=`trigger.sh` + `_engine-run/exchange-context.<packet_id>.md`;generated repo skill=`templates/repo/.agents/skills/seed-repo-operator/SKILL.md` | input schema=`src/contracts.ts`;fast judgment=`src/{check_factory_minimum_lineage,run_fast_quality,run_generated_fast_quality}.ts`;20-call judgment graph=`templates/repo/src/{capabilities,functions,operator}.ts`;repo gate=`src/verify_generated_repo.ts`;production aggregate=`verify.sh`/`selftest.sh`;human admit remains final |
| technical-equivalence research | task contract=`loop_wiki/evolve-technical-equivalence-research/PROMPT.md`;fixed profile=`profile/technical-equivalence.md`;generated primary/gap prompt=`equivalence.py`;judge material=`judge-packet.<digest>.json` under ignored `_runs/` | packet/digest/grounding/judge logic=`equivalence.py`;hard/soft drift=`drift.py`;proof=`proof_workflow/prove_equivalence.sh`;independent behavior control=`proof_workflow/control_equivalence_entry.sh`;external Human admit remains final |
| Forgejo 大小迴圈操作橋 | workflow prompt=[forgejo-loop-ops/SKILL.md](../forgejo-loop-ops/SKILL.md)；跨 host Codex 入口=`.agents/skills/forgejo-loop-ops/SKILL.md`；瀏覽器 operator=`chrome:control-chrome` | 確定性路由=`forgejo-loop-ops/scripts/route.ts` + `cases.json`；外部 request／observation schema=`skills/repo-neural-perception/schemas/forgejo-*.json`；repo 寫入判斷留 output repo operator |

> 編排 session **臨場手寫**的 ad-hoc 判官/子代理 prompt 無自然落點=歷史盲區——
> 慣例已定:派發前落 `<plan-dir>/dispatches/<role>-<slug>.md`
> (慣例 SSOT=sdlc-plan-composer S4 派工 Gotcha,2026-07-20 fold;
> 只活在 transcript=斷言×軌跡勾稽時無檔可引)。
> 本表=指針索引,抄任何 prompt 內文進來=違反下方不變量 5。

## 資料流全景圖(視覺化;命令拓撲+判官歸屬。目錄結構圖 → loop-harness-standard
## `modules/harness-spec.md` §1/§1.5,規範差異表 → 同檔 §1.6,只指針不重畫)
```text
                [ 大迴圈 = 主 session(Fable,恆 Claude Code host)]
                  讀 root CLAUDE.md;tier-dispatch 見 ARCHITECTURE.md §5
                              │ 指揮(op 一沙盒;driver 由大迴圈選定)
                              ▼
        [ loop_wiki/engine.sh ] ── iter-0 基線 ──┬─ 綠 → conform_only
                              │ dispatch          │
                              ▼                   ▼
        [ 沙盒 run.sh <driver> <target> ]   (跳過 driver,直達 admit 閘)
           ├─ claude -p(Sonnet author;讀沙盒 CLAUDE.md)＝同家族
           ├─ agy(Gemini;讀 AGENTS.md symlink;唯讀複核)＝跨家族
           └─ codex(經官方 codex-companion;每次 dispatch=全新 thread 單 turn)＝跨家族
                              ▲ 自動提示回邊(2026-07-25):verify.iter{N}.out
                              │   →scripts/build_iter_feedback.py→_engine-run/feedback.iter{N+1}.md
                              │   →下一輪 run.sh 第 3 位置參數(與靜態判官 findings 合併,不覆蓋)
                              │ 整改 target(祈使綁 target)
                              ▼
        [ verify.sh <target> ] T0 機械閘:exit 0/2/64+PROGRESS 行
           │ exit 2 → engine iterate(no-progress=2 / exhausted=N → SURFACE)
           ▼ exit 0
        [ engine exit 10 = AWAITING-HUMAN-ADMIT(引擎終點,絕不自動)]
                              │
              ┌───────────────┴─────────────────┐
              ▼                                 ▼
   [ 畢業段(大迴圈執行)]                [ 新案例型 op 加驗ㄧ段 ]
   holdout 只跑一次+trigger evals        語意鑑別坐實:多 tier 無 skill
   +Opus fresh 判官(禁 fork)            fan-out(Haiku 機械層並行)
              │                          +Opus 判官矩陣(findings-only)
              └───────────────┬─────────────────┘
                              ▼
                     [ 人 merge admit ]
                              ▼
        [ publish:FAMILY.yaml metrics+baselines/+changelog/ → 訂閱者 pull ]

  (供給側支流)proposals/ 隔離區 ◀──(DR proposal 迴圈,dr-<topic> 沙盒,agy 主 driver)── QUEUE.md 題目
              └─ 可執行驗證通過才轉入家族;7 天 TTL 歸檔;家族內容禁引用隔離區
```

## 不可簡化的不變量(誤改防護清單)
1. **知識單向流不可倒置**:proposals → 驗證 → 沙盒 diff → eval 閘 → 人 admit → merge,
   沒有旁門。
2. **各迴圈各閘、不共用不代理**:演化 op 迴圈的 verify.sh 綠 ≠ DR proposal 迴圈的可執行驗證;
   上層綠不代表下層綠。
3. **收斂 = 人 admit 非分數/自宣**:G 閘全綠只是候選資格,不是 merge 令(演化迴圈);
   7 天未過驗證即歸檔(DR 迴圈)。
4. **holdout 只跑一次**:演化迭代只准碰 public set,holdout 分數只在畢業段產生一次。
5. **prompt/config SSOT 單一真源**:本全景圖與 ARCHITECTURE.md 只**指針**,
   任何地方複製 prompt/評測腳本內容 = 雙圖漂移。
   原始提示詞與生成 prompt 的歸屬索引=[modules/prompt-registry.md](modules/prompt-registry.md);
   它列 owner 與短錨,不替代 owner prompt。
6. **semantic 判官層不可簡化**:機械閘對語意差異全盲(2026-07-11 實證:
   5 個無 skill tier 機械分完全齊平,語意正誤只有判官矩陣看得到)——
   任何「機械分夠了,砍掉畢業判官」的提議都撞此不變量。
   證據錨:`families/pinescript-audit/evals/candidates/_validation/2026-07-11-semantic-control/`。

## Gotchas
- **本檔最大風險 = 自我變成 husk/雙圖**:誘惑「把某 evals 判準/某迴圈細節抄進來方便看」——**擋下**,
  只留指針。它一旦抄內容,就從「防誤改的地圖」墮落成「會漂移的第二份」。
- **加新迴圈前先讀 [loop-harness-standard](../loop-harness-standard/SKILL.md) 的轉換 recipe**,落地後
  才回本圖登記組件卡——別跳過落地直接先幫它編一列。
- **改某迴圈後,回頭核本圖的組件卡+不變量清單沒被打破**(尤其資料流歸屬+各層各閘)。
- **production seed 不能只登記成「更多測試」**:必須同時登記資料流 owner、prompt/context owner、
  route-result、baseline/trend 統計、schema replay、seed scaffold 與 security fallback。少一個就不是
  production seed,只是一般候選小迴圈。
- **engine exit 20 雙語意**(2026-07-17 盤點):`--dry-run`(engine.sh `--dry-run,略過 driver dispatch` 分支)
  與 exhausted stop-loss(engine.sh 迴圈末 `exhausted stop-loss` 行)共用 exit 20,
  判別看 `RESULT=` 行(dry-run-surface vs exhausted)——寫自動化別只讀 exit code。

## Modules
- [modules/retarget-map.md](modules/retarget-map.md) — antigravity `antigravity-harness-wiki` →
  skill-bettor 逐機制映射與誠實帳本(為何拿掉 8+ 迴圈組件卡、拿掉 N×M host×driver 全景)。
- [modules/prompt-registry.md](modules/prompt-registry.md) — prompt/context/dataflow/judgment-logic
  ownership index;防止 raw prompt 被誤改、誤抄、誤簡化成隱性 chat state。
