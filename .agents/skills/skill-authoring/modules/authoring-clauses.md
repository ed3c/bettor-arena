# authoring-clauses — 條款全文(checklist 指針目標)

> 源計劃=docs/plans/2026-07-20-skill-spec-decompression/02+09(2026-07-20 admit)

## 統一 eval/test 契約(所有 skill 遵守;「Skills Need Evals」對 skill-bettor 的落地)

> 每支 skill 都受一組可跑閘約束——這就是「不 ship 未評測 skill」的機械形態。
> 契約錨在官方 Agent Skills spec(external-verify 2026-07-20,見 verified-truth.md),
> **非** gcr Gemini 藍圖(其 validator/ablation/llm_judge/git_gate 在 skill-bettor 已有
> 等價物,不重蓋;對映帳=計劃 09)。分兩類,不共用一套閘:

| 閘 | 工程層 `.claude/skills/` | families 分發資產 | 綁定點 |
|---|---|---|---|
| conformance(官方 name≤64/desc≤1024/body≤500/禁保留字) | 必過 | 必過 | product-ops 晨檢 + 本 checklist 3 |
| card_sync(名片同步) | 必過 | N/A | product-ops 晨檢 |
| reflow(拆行不拆量,改版時) | 必過(條款 b) | 必過 | 重排 commit 前 |
| fluff(no-op 散文) | WARN | FAIL(條款 e) | authoring + families op |
| dist_safety(帶腳本者:憑證/隱藏字元/外呼) | 帶腳本才過(條款 f) | 必過(條款 d) | authoring |
| case 品質(弱斷言/schema/rubric) | N/A | 必過=`check_case_baseline.py`(跑前驗 case) | families op |
| eval 分數(runner G 閘+holdout) | N/A(自審工具) | **必過=產品閘** | 演化 op + 畢業段 |
| 行為遵循消融(L2,▣ 選配) | 試點已跑(非 husk,計劃 09/11) | 已含於 eval | 待人 admit |

機械閘全在 `scripts/check_*.py`(各帶 --selftest);L0(conformance)+L1(selftest 存在性)
已綁定晨檢=每日生效;L2 消融待 ▣。**新增/改 skill 前跑對應閘,非綠不 ship。**

## 人面可讀性規範(雙受眾分離/拆行不拆量/條件配圖;checklist 第 11 項指向本節;兩類 skill 皆適用)

**a. 雙受眾分離**:SKILL.md 是模型面,token 量維持 tight,不因人面理解需求增補
(harness-spec.md §3❷ 實測被動上下文膨脹使任務完成率 91.6%→71.3%,tight 是正確性
約束非風格偏好)。人面理解一律導向派生投影——`.claude/skills/` 落地/退場/職責變更後
additive 登記 [panorama.md](panorama.md) 名片(一句話+上游+下游);families
已有路由器 SKILL.md+FAMILY.yaml 承接同等功能,不重造第二張圖。先落地才登記,不占位。

**b. 拆行不拆量**:重排版=零內容變更,只把串燒行(「；」「→」混接步驟+know-why+指針)
拆成一行一子句+編號子彈。行密度 guideline ≤60 全形字/行(非硬閘,見 02-authoring-clauses.md
§4「替代方案」);自查:
```bash
python3 -c "print(max(len(l.rstrip()) for l in open('SKILL.md')))"
```
(字元計數——2026-07-20 deviation:macOS awk `length()` 按 byte 計,中文一字算 3,
門檻失義。豁免=表格行(`|` 開頭)/含 URL 行/**markdown heading(單行構造永不拆)**/
**絕對路徑 inline code span**(2026-07-20 S5' 全量實踐明文化,24 檔先例一致);
≤60 適用**已重排**檔,未重排檔的義務=改動不推高 max。
連接語素警示(S5' 判官三度實抓):行內 `+`/頓號斷到行首=意外清單標號或語素丟失,
拆行時連接符留行尾。)
程序步驟禁 `→`/`；` 串燒,一步一行用編號清單。

重排執行程序(2026-07-20 fold-in;canonical 派工骨架指針=
`docs/plans/2026-07-20-skill-spec-decompression/dispatches/sonnet-exec-03a-lhrh.md`):
1. 目標檔無 session 外未 commit 改動(乾淨 before 錨;否則 deferred)
2. Read 全檔→拆行(frontmatter 一 byte 不碰;code span/fence 逐字保全)
3. T0=`python3 scripts/check_reflow.py --git HEAD <path>` iterate-until-pass(≤5 輪)
4. 字元密度 before/after 進 commit message(豁免=表格/URL 行,列明)
5. Opus fresh 語意 spot-check(否定詞歸屬+符號清點)→ 人 admit → 獨立 commit
已解:reflow T0=`scripts/check_reflow.py`(雙流:prose 剝標點/code 逐字;selftest 三件組)。
禁回退用:mean 行密度、byte 計數、無語意 spot-check 的純機械放行。
已知限:行首帶圈數字(①-⑳)被 LIST_MARKER 當標號剝除=雙流不可見(2026-07-20 實測,
含 HEAD 基準污染案例)——緩解=第 5 步符號清點必做;修正歸下次腳本迭代(改動需重跑全部已過基準)。

**c. 條件配圖**:≥3 階段的流程型 skill 必附一張 Mermaid 流程圖,節點=階段名+閘,禁抄
內文細節。<3 階段或非流程型 skill 不強制配圖(YAGNI,見源計劃 PLAN.md §3 第 3 條)。
全景圖集中承載跨 skill 關係,單 skill 內配圖只畫該 skill 自己的階段。

## 安全與品質左移(僅 families 分發資產;checklist 第 12 項指向本節)

> 適用範圍:本節兩條款(d/e)只約束 `families/<family>/` 這類發佈給訂閱者執行的分發資產;
> `.claude/skills/` 工程編排 skill 不適用**分發面**(自用工具,無第三方執行面)——但**注入面**
> (skill 目錄內 bundle 可執行腳本)由條款 f 管,適用面廣於 d/e。出廠(publish)閘
> 為第二層 defense-in-depth,非唯一層——第一層在本節的 authoring 自查
> (左移依據=源計劃 PLAN.md §1b gcr 機制映射,2026-07-20 操作者修正)。

**d. 安全左移**:新建/重構 families 子技能前自查四項——
1. 無憑證特徵(API key/token/password 硬編碼樣式)
2. 無 Unicode 隱藏字元(tag chars U+E0000–E007F)
3. 無未宣告外傳(網路呼叫/檔案外傳須在 shared/README 顯式宣告)
4. 宣告 blast radius(該子技能執行時讀寫哪些路徑,寫進子技能 frontmatter 或 shared/README)

自查命令(guideline,非窮舉):
```bash
rg -n '(api[_-]?key|secret|token|password)\s*=\s*["\x27][A-Za-z0-9]{16,}' families/<family>/
rg -P '[\x{E0000}-\x{E007F}]' families/<family>/ -n
```
命中且無法排除為誤判 → 不得 admit,交人核。

**e. fluff 機械自查**:no-op 詞黑名單(命中且無鐵錨即不收)。詞表落
[fluff-blacklist.txt](fluff-blacklist.txt)(canonical,勿在此複製維護第二份;新增/刪詞只改該檔)。

自查命令(逐行讀黑名單當 pattern,略過 `#` 頭注行):
```bash
grep -vE '^#' .claude/skills/skill-authoring/modules/fluff-blacklist.txt \
  | grep -inEf - families/<family>/**/*.md
```
命中者逐條核:同段落內有檔案路徑/行號/exit code/可跑命令等鐵錨 → 留;無錨 → 刪或改寫。

## 附帶腳本的注入契約(checklist 第 9 項指向本節;適用面廣於 d/e)

> 源=antigravity gcr「Skills Need Evals, Don't Ship Blindly」
> (P9/P4/輔助執行層);收錄紀律同源計劃 PLAN.md §1b
> ——只收機制,其 benchmark 數字全 mock 不收。
> 適用面:d/e 管 families 分發面;
> 本節管**任何在 skill 目錄內 ship 可執行腳本**的 skill
> (families 子技能有 scripts/;工程層 skill 若也 bundle 腳本同理)
> ——注入面廣於分發面。
> 註:repo-root 共享工具(如 `scripts/check_reflow.py`)非「注入某 skill」,走各自 selftest。

**f. 附帶腳本的契約**——官方兩種機制,共通鐵律「**只有輸出進 context、程式碼本身不進**」
(2026-07-20 external-verify primary 錨,兩輪查證;**修正首版誤斷**:官方確有「動態上下文
注入」機制,「注入」非 Gemini-ism):
- **`scripts/` helper**:Claude 用 bash 工具執行、只 stdout 回 context(execute-not-load)。
- **`!`cmd`` 行內注入**:引擎送 LLM 前 preprocessing、命令 stdout 取代該行(官方 "Inject
  dynamic context";作用在 SKILL.md body,`!` 在行首或空白後才觸發,多行用 ```! fence)。
- **`context: fork`**:frontmatter 設之→skill body 當 prompt 派生隔離 subagent、不見對話
  歷史、只回摘要(防 context 汙染;配套 `agent` 欄位選 subagent 型)。
兩面契約(下沉可靠性 + 執行安全)各一條:
1. **聲明式調用(可靠性)**:固定順序/高危/需確定性重現的邏輯 → 下沉成腳本,
   skill 只聲明式調用(明確「執行 `<script>`」+ GOAL/CONSTRAINTS),
   **禁 inline 複述腳本內部步驟**(model 每次重解釋=非確定性回歸)。
   反面:需 model 自由度的探索性判斷別硬編碼成腳本(剝奪彈性)。
   補全 checklist 7「確定性邏輯落腳本」缺的**何時下沉+怎麼調用**。
2. **執行即執行半徑(安全)**:skill 目錄內可執行腳本經 bash 以 agent 權限運行=blast radius。
   須過 d 的四項 + 無隱藏後門(未聲明的覆蓋全局行為檔,如私自 rules-file/hook)+ 依賴鎖。
   官方安全模型=權限規則(`Skill()` allow-deny)+ workspace trust + 用戶自審,**非沙盒**
   (官方無腳本沙盒/憑證隔離保證,見 verified-truth.md)——別假設有沙盒兜底。

機械面複用 `scripts/check_dist_safety.py`(對 target 掃憑證/隱藏字元,
對 `<target>/scripts` 掃未宣告外呼)——給帶腳本的 skill 目錄當 target 即可,非 families 專屬。
官方 spec 硬約束(name≤64/description≤1024/body≤500 行/禁保留字)=`scripts/check_skill_conformance.py`
(所有 skill 統一閘)。

## 替代方案裁定(§4 摘,方案 B guideline 已選定)

行密度/fluff 門檻現行=guideline(自查命令+人核+commit message 附數字),非 T0 硬閘
(方案 A)。升級條件:S3 試點完成後,若追蹤 3 次迭代内行密度回彈 >20%(對比重排版後
基線),則升級為方案 A,新腳本落點另議(需先過放置契約)。完整權衡見
`docs/plans/2026-07-20-skill-spec-decompression/02-authoring-clauses.md` §4。
