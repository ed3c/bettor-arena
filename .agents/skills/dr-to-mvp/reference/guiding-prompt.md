# 引導提示詞：研究問題 → 可信基底 → prototype → 八大基座畢業 MVP（skill-bettor 版）

> **這是 [`dr-to-mvp`](../SKILL.md) 的 Layer B reference**（可貼 playbook）。SKILL.md＝脊椎路由表＋不變量;本檔＝逐階段 prompt 骨架＋閘＋▣停點。漂移時以各 owner skill 的真檔為準;移植命門見 [modules/retarget-map.md](../modules/retarget-map.md)。
> **這是什麼**：把「一個研究問題／一批 DR 語料」一路引導到「一個畢業的家族資產（`families/<f>/`）」的**冷啟動編排提示詞**。可貼可跑。
> **紀律**：pointer-rich,**不複述** SSOT（漂移時以被指的真檔為準）。每階段標 **LIVE ✓（本地真跑過）** vs **設計 only（未證,Path B 不宣稱成立）**。
> **SSOT 來源**：`proposals/README.md`（Phase R schema＋生命週期）、`.claude/skills/dr-research-loop/`（DR 執行）、`.claude/skills/loop-harness-standard/modules/harness-spec.md`（八大基座）。
> **鐵律**：全程 recipe-not-engine——每個 ▣ SURFACE 點停下等人 admit,**不 auto-chain**。畢業/merge/homing 永遠人核。
> Domain 詞與 Mode B 語料 intake → [modules/domain-terms-and-intake.md](../modules/domain-terms-and-intake.md)。
> State graph 重構資訊保全帳 → [modules/semantic-loss-ledger.md](../modules/semantic-loss-ledger.md)。

---
## Output Contract（產物語意真相，不可壓縮）

本 playbook 產出的 plan/report/dispatch packet 必須讓 fresh LLM 不讀原對話也能執行。
每個 Match／Generate／Validate state 至少寫一列 route ledger：

```md
| state | decision | evidence | grounding | actor | validator | chosen edge | failure edge |
|---|---|---|---|---|---|---|---|
```

硬規則：
- 不寫 `Opus or Codex or agy` 這種未裁決三選一；actor 依語意角色指定。
- scripts 驗 deterministic facts；Codex 實作/重現/改檔；Opus fresh 判語意與畢業；agy/Gemini 做研究或跨家族 findings，不作 final verdict；human admit phase transition、graduation、homing。
- 每個 load-bearing claim 標 `technical_equivalent` / `candidate` / `[推論]` / `human_required`。
- 不把 `semantic truth`、`validate later`、`按需驗證` 當可交付指令；要寫清楚判什麼、憑什麼、誰判、失敗後走哪條 edge。
- Domain 詞首次出現要展開；本檔未收的詞補 `Glossary delta`：`term | intended meaning | source | grounding | unresolved`。


## 0. 先校正拓撲（問法本身的兩個誤解）

**誤解 1：「DR 是 prototype 的入口」——不是。**
DR／proposal 是「填外部知識缺口」的一步,產物＝**待驗敘事、不是鐵錨**（Path B;proposal driver 不得自宣 verified/adopted）。可信基底的真來源＝proposal 過 **T0 四閘（exit 10）＋ D3 adopt** 的裁決。prototype 的真入口是 **D4**,種子＝**已驗基底 ＋ 一個 D3 的 UK 可行度缺口**。完整鏈：

```
研究問題 / DR 語料
  └─ proposals/ 上游迴圈（owner=dr-research-loop;沙盒骨架=loop_wiki/_template_dr）
       draft（DR 迭代中,verify 未綠）→ verified（T0 四閘 exit 10）→ adopted（judge-loop-chooser D3 審過+人核）
  └─ 下游落地（adopted 後,SURFACE-gated 人 admit）
       可信基底（真實度計分卡＋等價物矩陣＋分層架構＋最脆弱三處）        ← prototype 的種子在這
       gap 收斂（KK/KU/UK/UU）：KU→repo-agent-native（L2 不變量）；UK→D4
       D4 prototype 端到端（推導→實測）                                ← prototype 真入口在這
  └─ MVP-builder（種子→畢業資產）
       ① 基底=設計分 answer-key → ② cp -r loop_wiki/_template → ③ 種子成 src/+verify.sh
       → 小迴圈 engine.sh <loop> --driver → verify.sh 閘 → 畢業 dual-score → 人 LAND-DECISION → homing 進 families/
```
> DR 是「填外部知識缺口」的一步,不是主幹;把 DR 當事實直接做設計＝幻覺入庫。**家族產物禁回指 proposals/（CI FAIL）**,本脊椎編排整條管線故可指上游。

**誤解 2：「prototype」是一個東西——其實有兩種,別混。**

| | **D4 驗證型 prototype** | **MVP 種子 prototype** |
|---|---|---|
| 問的問題 | 一個 UK 可行度缺口（「做出來才知」） | 已驗證,要長成耐久家族資產 |
| 歸宿（分軸＝升格路徑非壽命） | 答完 absorb,ANSWER→NOTES→基底;artifact **留錨不刪、永不升格** | 升格進 `loop_wiki/<loop>/src/`,八大基座迭代 |
| 用什麼 | `~/.claude/skills/prototype`（一命令、surface state、混壞 case） | `cp -r loop_wiki/_template` 八大基座＋`engine.sh` |
| 本地實例 | （冷啟動時視 UK 而定） | `families/agent-harness/shared/runtime/harness-core`（`7481e78`） |

**所以「交給八大基座做 MVP」＝拿一個已驗證的種子 prototype（不是拿 DR proposal、不是拿①驗證型 prototype 的半成品）,跑 MVP-builder ①②③。**

---

## 1. 大迴圈引導提示詞（逐階段可貼；每段＝指針＋prompt 骨架＋閘＋▣SURFACE）

### Phase R — 研究到可信基底　【LIVE ✓（`families/agent-harness/`:DR 語料型,既有語料 cluster 深整合）】
> SSOT：`proposals/README.md`（schema＋生命週期）＋ `.claude/skills/dr-research-loop/`（DR 執行）＋ `.claude/skills/judge-loop-chooser/`（D3 adopt）。**照那幾處做,別在這裡重述**。

```
1. 判模式：有具體研究題/URL → Mode A（跑 proposals/ DR 迴圈）；只有一批既有語料 → Mode B（主題分類→cluster 深整合,可無新 DR,複用既有機械錨）。
2. 跑 proposals/ 上游（DR 走 dr-research-loop,禁重造 monitor+retry;跑 live 瀏覽器 DR 前查 :9333 佔用）。產物給絕對路徑。
3. T0 四閘機械驗（loop_wiki/_template_dr/scripts/check_*.py）：schema/意圖漂移/引用完整 → exit 10=verified。
   （確定性錨＞LLM 說詞:存在性 VERIFIED ≠ perf/framing 對,分開判;反幻覺走 external-verify。）
4. D3 adopt（judge-loop-chooser）：對照 proposal origin_question 審意圖漂移/Half-Bridge → adopted 才進下游。
   判官＝Opus,agy 不當判官（只出 findings）。
5. 合成可信基底：真實度計分卡（marketing<vendor<primary）＋技術等價物矩陣（+存在性+成熟度+license 欄）
   ＋分層架構＋最脆弱三處。設計原則從查證反推（把「精準」責任從 LLM 移到確定性中介層）。
   ▣ 若下游要商用+零 copyleft：等價物過授權/專利合規軸（external-verify）。開源≠可商用零義務。
```
**閘**：可信基底每條 load-bearing claim 有確定性錨（T0/D3 裁決/primary source）或明標 UNVERIFIED（無錨＝Half-Bridge,不宣稱）。
**▣ SURFACE**：基底給人核——哪些 claim CONTRADICTED、哪些留待 prototype 實測。
> **know-why：跑 DR 前先查既有同主題基底**。語料與 `proposals/`／既有家族產物同主題時,該處已驗機械錨**複用不重跑**,只對「新語料相對既有的增量具名實體」做驗——`families/agent-harness/` 即 DR 語料型 Phase R（既有語料主題分類→cluster,無新 DR）。反面：判官別盲錨語料裡沒出現的領域常識實體（external-verify「錨定 source 自身 bibliography、禁盲搜」）。

### Phase G — 可行度 gap 收斂 → D4 驗證型 prototype　【LIVE ✓（種子跳 D4 型,見 know-why）】
> SSOT：`.claude/skills/unknown-discovery-composer/`（四象限）＋ `.claude/skills/repo-agent-native/`（KU L2）＋ 全局 `~/.claude/skills/prototype`（D4 驗證型）。

```
6. D3 盤點基底自身可行度未知（KK/KU/UK/UU）：
   KU（讀源可答）→ repo-agent-native（L2 抽業務不變量）。
      ⚠ 深研真實參考實作常「反證」基底中心論點（最高價值揭露）。
   UK（做出來才知）→ 第 7 步。   UU → 盲點 pass。
7. D4 對每個 UK gap 跑驗證型 prototype（~/.claude/skills/prototype,預設輕量非八大基座）：
   紀律：標 PROTOTYPE、一命令跑、每步 surface state、**混入該擋的壞 case** 實測防護真起作用、誠實留白
   （明寫「本 prototype 未證什麼」）。答完 → NOTES 記問題+裁決 → **fresh 判官原始重算 spot-check（先於 absorb）**
   → absorb 回基底;artifact **留存作驗證錨**（不刪、不升格）。
```
**閘**：claim 從「推導」升「實測」（實測揭露 nuance）。
**▣ SURFACE**：哪個 UK 缺口已被實測關閉、基底更新到第幾版——人決定「夠不夠格開 MVP」。
> **know-why：某類 v1 種子可跳過 D4 驗證型**。當 v1 的 UK 核心**本身就是要進 `src/` 長成產品的②MVP 種子**（而非①答完留錨的驗證型）,對它跑 D4 是多餘的:那個 UK 直接在 Phase M 小迴圈用 mock 純內部層驗即可（實例:`families/agent-harness/` 的 evals-gate「證據防偽是否真擋 mode-downgrade」是 UK,但 evals-gate 本身就是 MVP `src/`,於是在 Phase M hermetic 層用 gate config 強制 mode 驗,不先建驗證型）。**判準**：UK 是否可由「即將成為 src/ 的種子」自身承載——是則跳 D4、直接 Phase M;否則仍走 D4 各自實測。

### Phase M — 種子 prototype → 八大基座畢業 MVP　【LIVE ✓（`families/agent-harness/`:兩畢業 MVP、117 tests、判官揭洞整改、雙分綠人 admit）】
> SSOT：`.claude/skills/loop-harness-standard/modules/harness-spec.md`（八大基座卡）＋ `ARCHITECTURE.md §3`。**照它,別重述八大基座規範**。

```
8.  ① 定設計分 answer-key：基底 golden-path + 最脆弱三處 + G 盲點 → DESIGN-SCORE.md 對照表
       （每格 done/designed-cut/MISS;MISS=設計分 FAIL）。這是「畢業設計分判官」的機械答案卡。
9.  ② scaffold 八大基座：
       cp -r loop_wiki/_template loop_wiki/<loop>
       骨架含：PROMPT.md(#7 目標契約=SC清單+guard+stop-loss+dual-score 畢業閘) · PLAN.md(#8 狀態帳本) ·
               CLAUDE.md(#1 driver 被動上下文) · run.sh(單發 dispatch) ·
               verify.sh(#6 T0 硬閘:design-gate + 分層 tests + e2e,--fast/full 兩層) · anti/(#4 防退化) · logs/。
       另建 DESIGN-SCORE.md、dispatches/、src/、tests/(good/hollow fixtures);driver=agy 時 engine 落 AGENTS.md symlink。
10. ③ 把第 7 步驗證過的種子 prototype 移進 <loop>/src/,補 verify.sh 第一條回歸測試（實作分 T0 起點）。
11. 小迴圈 iterate-until-pass × stop-loss：
    loop_wiki/engine.sh <loop> --target <path> --driver claude|agy    # engine=迭代/停損;exit 10=awaiting-human-admit
    for 每個 open SC：
      a. 寫 dispatches/round-NN.md 逐字 brief（輸入側紀錄——唯一答案洩漏向量+可審計性）。
      b. 派 fresh zero-context driver（Agent tool subagent,執行者≠判官、禁 fork）整改 src/+加回歸測試。
      c. 判官（主 session Opus）獨立驗：跑 verify.sh full + --fast、git diff 確認零 src 弱化/零測刪除、
         **實質 spot-check 該輪的核心新 claim**（別只信 exit 0）。exit0→commit→下一 SC;
         exit≠0→記 PLAN 失敗軌跡,達 stop-loss(3 無進展)→▣SURFACE 人。
      ⚠ 判官永不外包、永不用 agy（agy=Gemini only）;改既有測試需 PLAN HUMAN-AUTHORIZED 條目。
12. 畢業：設計分（DESIGN-SCORE 零 MISS,跑 fresh subagent 設計分判官、**不餵 big-loop rationale**）
    ∧ 實作分（verify.sh full LIVE exit0）→ 兩軸皆綠。**判官不只抓洞,更逼「不帶已知缺口畢業」**。
```
**閘**：dual-score AND（降維/移除某 SC 仍須過設計分＝證明是 designed-cut 非漏做）。
**▣ SURFACE（終點,必停）**：畢業＝人 LAND-DECISION admit。admit 後 **families 型 homing**：MVP 現住 gitignored `prototype/`＝孤本,
　搬進 `families/<f>/shared/runtime/<mvp>/`（隨家族 checked-in,訂閱者 git pull 即得可跑模組）;搬運排除 `.git`/`venv`/快取,
　跨模組絕對路徑改 `__file__` 相對定位;畢業後 metrics 回填 `FAMILY.yaml`（雙軌:機械 success_rate ∧ 語意 semantic_pass_rate）。
> **know-why：families 型 homing 的接縫**。實例 `families/agent-harness/`（`0e9ea32`）:evals-gate `src/ingest.py` 的 `DEFAULT_ENVELOPE_SCHEMA_PATH` 從 prototype 絕對路徑改為 `__file__` 相對（指同層 `../harness-core/contract/envelope.schema.json`）——搬完 verify 必綠是硬不變量。**硬體/真機類 e2e 無設備標 `deferred(needs-hardware)` 不卡 homing**（編排邏輯 hermetic 全驗即可 merge;真機閉合待設備）。本 repo homing 只用 families 型（living-skills 家族 repo 的唯一適用型;antigravity 另有 remote／reference-impl 型,單 repo 場景不適用,見 [modules/retarget-map.md](../modules/retarget-map.md) §2）。families 型完整帳 → `families/agent-harness/changelog/2026-07-12.md`。

---

## 2. 誠實接縫（Path B——別在未證的關節上鋪平滑敘事）

| 接縫 | 狀態 | 出處 |
|---|---|---|
| Phase R（proposals 驗證+D3 adopt） | **LIVE ✓** DR 語料型（既有語料主題分類→cluster,無新 DR） | `families/agent-harness/changelog/2026-07-12.md` |
| Phase G（種子跳 D4，Phase M mock 層驗） | **LIVE ✓** evals-gate 證據防偽 UK 由種子自身在 hermetic 層驗 | 同上 |
| Phase M（種子→八大基座 MVP） | **LIVE ✓** 一 op 兩畢業 MVP（harness-core `7481e78`/evals-gate `613da6e`,117 tests,判官揭 HIGH 安全洞整改 round-06b CLOSED,雙分綠） | `families/agent-harness/{FAMILY.yaml,changelog/2026-07-12.md}` |
| families 型 homing | **LIVE ✓** 兩 runtime homing 進 `shared/runtime/`（隨家族 checked-in,`__file__` 相對 schema 實測通過,三面向 fresh 對抗全 pass） | 同上（`0e9ea32`） |
| dual-score 設計分判官 | **LIVE ✓** fresh opus 設計分判官掃 DESIGN-SCORE 判 PASS ＋ verify exit0 ＝ AND 綠;同役判官逼「不帶已知缺口畢業」（給 PASS 卻主動揭 HIGH 洞→編排者裁 FAIL→整改→複審 CLOSED） | 同上 |
| **eval harness（cases/holdout/runner/judge/baseline）** | **設計 only / 待下一 op**——`families/agent-harness/` 兩子技能 metrics 全 null,eval harness 明標下一 op（非 spawn op 範圍） | `FAMILY.yaml` metrics: null |
| **Antigravity-CLI host 覆蓋** | **不適用**——skill-bettor 單 host（Claude Code）,無 2×2 矩陣（retarget-map §2） | modules/retarget-map.md |

> **反-husk**：本脊椎的 LIVE 錨全部指向本地 `families/agent-harness/` 真檔,不繼承 antigravity 的 cutplan/ix-agy 案例史（那是它自己的軌跡,見 retarget-map §1）。

---

## 3. 一頁速查（最小命令序列）

```bash
# Phase R：研究 → 可信基底（proposals 上游迴圈;DR 走 dr-research-loop,判官=Opus,錨>LLM）
#   draft → T0 四閘 exit 10=verified → judge-loop-chooser D3 → adopted → 合成基底（含真實度計分卡+等價物矩陣+license 欄）
#   跑 live 瀏覽器 DR 前查 :9333 佔用

# Phase G：UK gap 實測（驗證型,artifact 留錨）
#   ~/.claude/skills/prototype（預設輕量;答完 absorb→基底→artifact 留錨不升格）;種子型 UK 可跳 D4 直進 Phase M

# Phase M：種子 → 八大基座畢業 MVP
cp -r loop_wiki/_template loop_wiki/<loop>                              # 八大基座骨架實例化
#   ③ 種子進 <loop>/src/ + verify.sh 首條回歸
loop_wiki/engine.sh <loop> --target <path> --driver claude|agy         # 迭代/停損;exit 10=awaiting-human-admit
#   迴圈：write dispatches/round-NN.md → 派 fresh driver 整改 src/ → 判官跑 verify.sh full+--fast+spot-check
#         → commit → 下一 SC；stop-loss 3 → SURFACE
#   畢業：DESIGN-SCORE 零 MISS(設計分判官) ∧ verify.sh exit0(實作分) → ▣ 人 LAND-DECISION
#   homing：搬進 families/<f>/shared/runtime/<mvp>/（排除 .git/venv;__file__ 相對）+ 回填 FAMILY.yaml metrics
```

**每個 ▣ 停**：recipe-not-engine,人 admit 才續下一 Phase。
