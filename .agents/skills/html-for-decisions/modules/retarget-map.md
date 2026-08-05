# Module: html-for-decisions — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`html-for-decisions`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到
> skill-bettor、哪些因為架構前提不同被拿掉/改寫、兩份 reference HTML 各自的去留判斷、腳本
> selftest 改法的理由與鐵錨驗證記錄。

---

## 1. 這個 skill 為何多數內容能保留——它本來就是平台無關的機制

與 `loop-harness-standard`/`harness-wiki` 不同(那兩份摻了大量 antigravity 自己雙 host 矩陣的歷史
證成)，`html-for-decisions` 的核心不變量(markdown=源/HTML=投影、自包含、quiz 全對才 admit、
approve 永遠人、決策面與觀測面語義隔離)**不依賴 antigravity 的雙 host 架構**，也不依賴任何
antigravity 專屬基座——這是一套「怎麼把人閘節點做成高決策密度 HTML」的通用方法論。因此本次移植
以「保留機制、換掉措辭與具體指針」為主，不像另兩份 harness skill 需要大量刪減歷史記錄。

真正需要判斷的，是三類東西：① 兩支 Python 腳本是否真的零耦合 antigravity 路徑(答案：接近是，
但有一處耦合需要修)；② 兩份 reference HTML 是否該原樣搬(答案：不該，見 §3)；③ SKILL.md/
media-know-why.md 裡引用的 antigravity 專屬概念(卡片盒編號、計劃 slice 慣例)怎麼處理。

## 2. 逐項移植決策

| antigravity 內容 | skill-bettor 處置 | 為何這樣做 |
|---|---|---|
| 核心不變量 7 條(HTML 只給人閘/md=源 HTML=投影/自包含/quiz+approve 人閘/語意真相標態/色票驗證/決策觀測面隔離) | **原樣映**(僅措辭微調) | 平台無關,是本 skill 的核心資產,拿掉即掏空 skill 本體。 |
| 確定性程序 7 步 | **原樣映,md SSOT 位置換成 skill-bettor 自己的**(見 SKILL.md 程序步驟 1-2) | 程序骨架通用;「md SSOT 在哪」這件事本來就該因 repo 而異——antigravity 是計劃 slice,skill-bettor 是依 `ARCHITECTURE.md` §8 節點類型分流到 `evals/results`／`PLAN.md`／`changelog/` 等。 |
| `ARCHITECTURE.md` §8「人閘清單」 vs antigravity 的「計劃/迴圈的人閘節點」措辭 | **改綁到 skill-bettor 自己的 5 類人閘**(merge admit/holdout 畢業判/案例輪替/spawn 新家族或子技能/對外發佈) | 任務說明明確要求:「這是 skill-bettor 自己的 LAND-DECISION 節點清單,HTML 決策面機制該服務它」。 |
| 「06 §A C03/C04 卡」卡片盒編號引用 | **拿掉編號,保留概念**(三受眾媒介矩陣、HTML 稅) | skill-bettor 沒有這套卡目(已 grep 確認 `.claude/skills/` 全域無「06 §A」「卡片庫」「卡片盒」字樣)。原樣搬編號＝指向 skill-bettor 查無此卡的死指針;但「三受眾/HTML 稅」這個判準本身是可轉移方法論,值得留。 |
| `docs/plans/2026-07-09-loop-harness-panorama/10-media-and-boundary.md` 計劃 slice 分工說明 | **拿掉,誠實記錄 skill-bettor 沒有對應慣例** | 已用 `find` 確認 skill-bettor 無 `docs/plans/` 目錄慣例(遷移走 `families/`+`loop_wiki/evolve-<family>-<op>/`)。硬搬會製造一個 skill-bettor 尚不存在的文件家族的假分工示範。media-know-why.md §5 改為誠實記錄「skill-bettor 沒有這個概念,等有了第一個 worked instance 再回頭指」。 |
| 2026-07-09 dogfood 錨(loop-harness-panorama 儀表板 v0→人裁 5 項→回填) | **保留,但明確標記為 antigravity 自己的歷史,非 skill-bettor 的** | 任務說明白紙黑字:skill-bettor 沒有自己的 worked LAND-DECISION instance,不得假裝有。這段錨的價值是「證明機制可行」,不是「skill-bettor 已驗證過」——media-know-why.md §2 已加上明確區分句。 |
| northstar `viz-sync`/`solo-pipeline` → antigravity 逐機制映射表(media-know-why.md 原 §4,一張大表) | **不重複整張表,改成一段「這是上一手的移植決策,結論原樣成立」的推論** | 比照 `harness-wiki/modules/retarget-map.md` 已立的先例(該檔明文:「antigravity 對比 northstar 架構的具體歷史決策,skill-bettor 沒有對應的候選架構要拒絕,不搬」)。這裡是同一個判準的第二次應用:northstar 比較是 antigravity 自己的沿革,不因為 skill-bettor 現在也間接繼承這個機制,就要把兩手前的比較表重新抄一遍。skill-bettor 版 media-know-why.md §4 只記結論(「skill-bettor 比 antigravity 更沒有這些基座,結論不必重新論證」)+ 指回 antigravity 原檔查完整表。 |
| `judge-loop-chooser` 交叉引用 | **改指本地路徑** `../judge-loop-chooser/SKILL.md` | 同批移植的真實 sibling(見任務說明),即使建立時間可能略早略晚,路徑約定已知。 |
| 全局 `dataviz` skill 的 validator 調用(`node <dataviz-skill>/scripts/validate_palette.js ...`) | **原樣保留**(含 `<dataviz-skill>` 佔位符寫法) | 任務明確指示:dataviz 是全局 skill,在 skill-bettor 的 Claude Code session 裡同樣可用,路徑佔位符寫法本來就不是字面路徑,不需改。 |
| `{{PLAN_DIR}}` 佔位符(decision-report.prompt.md) | **改名 `{{SOURCE_DIR}}`** | antigravity 的「計劃目錄」在 skill-bettor 沒有一對一等價物——skill-bettor 的決策來源依人閘類型可能是家族目錄、`loop_wiki` 沙盒、或 `proposals/`。改用更中性的名字避免暗示一個不存在的「計劃目錄」慣例。功能不變,只是命名更準確。 |
| Schema v1 S0-S10 section 物理邊界表 | **原樣映**(僅槽位的範例措辭去 antigravity 化,如「計劃名/計劃狀態」→「決策標的名(家族名/op 名)/家族或 op 狀態」) | 任務要求:「schema 本身多是生成契約,大致可攜——retarget 範例內容/佔位符為 domain-neutral 或 skill-bettor 風味,非 antigravity 風味」;schema 骨架(哪個 section 放什麼、順序、色票)是通用資產,不必動。 |
| 狀態色 tokens(採納/借形/待裁/僅記錄/husk 五色,CVD 驗證過的順序) | **原樣映** | 這是已跑過 dataviz validator 驗證的具體色值+順序,是可攜的驗證過產物,不因 repo 而變。 |

## 3. 兩份 reference HTML——不對稱處置,判斷理由分別記錄

**`loop-panorama-decisions.html`(決策面範例)→ 保留一份副本,改名
`reference/antigravity-example-decision-dashboard.html`,加大段 banner 標明來源與使用限制。**

判斷理由:`prompts/decision-report.prompt.md` 的生成契約**在其步驟 2 明文指示**「複用骨架,從
骨架範例取 `<style>` 全段與各 section 的 DOM 結構」,並且步驟開頭就給出骨架範例的檔案路徑。這不
是單純的「skeleton study material」(nice-to-have),而是生成契約本身運作所需的錨——如果
skill-bettor 完全沒有任何範例檔,第一次執行本 skill 產生決策面時,執行 LLM 沒有任何 DOM/CSS 骨架
可循,schema v1「S0-S10 物理邊界收斂」的核心價值(不同家族/op 產出同構報告)在首次使用時就落空。
因此判斷「骨架研讀價值高」,決定保留,但用以下方式避免誤認 provenance:
- 檔名改為 `antigravity-example-*`,明示這不是 skill-bettor 自己的案例。
- 檔案開頭加入大段 HTML 註解 banner,寫明來源路徑、內容屬 antigravity 歷史(2026-07-09 loop-
  harness-panorama 計劃)、使用規則(只取骨架不取資料)、以及「skill-bettor 有了自己的 worked
  instance 後應考慮替換」的但書。
- SKILL.md、media-know-why.md、decision-report.prompt.md 三處引用都附帶「antigravity 歷史案
  例/非 skill-bettor 內容」的說明,不單獨出現一個看起來像本地案例的裸連結。

**`context-trace-example.html`(觀測面範例)→ 不保留副本,只留文字說明。**

判斷理由:與決策面範例不同,`context_trace.py` 是**確定性渲染器**——它的 `render_html()` 直接從
解析出的 trace dict 產生 HTML,不需要參照任何既有範例檔案來決定骨架(骨架寫死在腳本的
`render_html()` 函式裡)。antigravity 原版 SKILL.md 自己都說這份範例「是輸出樣品非模板」("它是
輸出樣品非模板")——換言之它從未被任何生成契約當作骨架來源引用過,純粹是「這裡有一份真實輸出長
怎樣」的展示。skill-bettor 只要在第一次真實 session 上跑一次 `context_trace.py <session.jsonl>`,
就能自己生成一份等價的展示樣品,不需要繼承 antigravity 的。保留副本的邊際價值低於「保留一份不是
自己产的示例、還要解釋兩次為什麼不是本地內容」的認知負擔,因此判斷不保留,SKILL.md/media-know-
why.md 均已改為純文字說明(此檔不存在于 skill-bettor,需要時自產)。

**一致性檢查**:這個「留一份、不留另一份」的不對稱決策,鐵錨是「生成契約是否真的消費該檔案作為
骨架輸入」——消費(decision-report.prompt.md 確實讀它)則留,不消費(context_trace.py 自帶渲染
邏輯)則不留。這不是隨意的偏好,是可驗證的技術判斷。

## 4. 兩支 Python 腳本——可攜性驗證與一項必要修改

**驗證方法**:對兩支腳本先在 antigravity 原始位置各跑一次 `--selftest`,確認移植前基準綠燈;
`grep -n "antigravity\|/Users/neon"` 掃過兩支腳本全文,確認無字面路徑耦合。

```
$ python3 /Users/neon/antigravity/.agents/skills/html-for-decisions/scripts/check_decision_html.py --selftest
SELFTEST PASS (exit 0)
$ python3 /Users/neon/antigravity/.agents/skills/html-for-decisions/scripts/context_trace.py --selftest
SELFTEST PASS (exit 0)
$ grep -n "antigravity\|/Users/neon" check_decision_html.py context_trace.py
(無輸出——零字面路徑耦合)
```

**`context_trace.py`**:零耦合確認為真,**原樣複製**(僅 docstring 補一行 retarget 記事,函式邏
輯/render_html 骨架/selftest 合成 fixture 全部不動)。它的 `--selftest` 本來就用程式碼內建的合成
JSONL fixture,不讀任何外部檔案——這本身就是良好的可攜設計典範,不需要修。

**`check_decision_html.py`**:字面上沒有 `/Users/neon` 或 `antigravity` 硬編路徑,但有一處**結構
性耦合**——`REFERENCE = SKILL_DIR / "reference" / "loop-panorama-decisions.html"`,`--selftest`
靠讀這個檔案當 good fixture、記憶體內剝除兩個標記做出 hollow fixture。這在 antigravity 原倉庫沒
問題(該檔本來就在),但 skill-bettor 已經決定「不把這份檔案的內容當作自己的東西」(§3),若原樣
複製這個依賴,checker 的可攜性會被「要不要保留這份 antigravity 範例」的內容決策綁架——刪掉範例檔
會連帶弄壞 selftest,這是一種不必要的耦合。

**修法**:把 `--selftest` 改成完全合成的最小 fixture(見新檔 `GOOD_FIXTURE` 常數),手法對齊
`context_trace.py` 自己已經在用的模式(合成 JSONL fixture)——不是新發明,是把 checker 補齊到跟
它的姊妹腳本同一種可攜性水準。改完後拿掉了 `SKILL_DIR`/`REFERENCE` 這兩個常數與檔案讀取邏輯。

**驗證(在 skill-bettor 新路徑上實跑,非重述 antigravity 側結果)**:

```
$ python3 /Users/neon/ts-skill-bettor/.claude/skills/html-for-decisions/scripts/check_decision_html.py --selftest
check_decision_html — good（合成正控 fixture，非讀外部檔）
  [PASS] declare  ...
  [PASS] snapshot ...
  [PASS] selfhost ...
  [PASS] quiz     ...
  [PASS] title    ...
  [PASS] hollow   剝除宣告/quiz 後如預期 FAIL（declare,quiz）——checker 有判別力
SELFTEST PASS (exit 0)

$ python3 /Users/neon/ts-skill-bettor/.claude/skills/html-for-decisions/scripts/context_trace.py --selftest
  [PASS] 去重後 2 calls / 人類 turns=1 / 工具計數 Bash=1 / 輸出 tokens=130 /
         prefix-miss 抓到 1 起 / oracle 2/2 / html 含各標記
SELFTEST PASS (exit 0)

$ python3 /Users/neon/ts-skill-bettor/.claude/skills/html-for-decisions/scripts/check_decision_html.py \
    /Users/neon/ts-skill-bettor/.claude/skills/html-for-decisions/reference/antigravity-example-decision-dashboard.html
  [PASS] declare / snapshot / selfhost / quiz / title   全 PASS（exit 0）
```

（第三個驗證：確認即使 checker 已改為合成 selftest，它仍然能正確判讀真實 reference 檔案——banner
註解不干擾任何一項 regex 判定，五檢查照樣全過，兩者互不依賴但互相相容。）

## 5. 拿掉/改寫的東西不是「簡化」,而是「原樣搬會製造死指針或假 provenance」

- **能一對一映的映**:七條不變量、確定性程序骨架、schema v1 物理邊界、狀態色 tokens、Gotchas 清
  單、`judge-loop-chooser`/`dataviz` 交叉引用。
- **概念留、編號/具體指針拿掉**:三受眾媒介矩陣(留概念,棄「06 §A」卡片盒編號)、northstar 比較
  (留結論,棄整張表——理由與 harness-wiki 的既有先例一致)。
- **誠實標記為尚不存在,不假裝已完成**:skill-bettor 自己的 worked LAND-DECISION instance、
  2026-07-09 dogfood 錨(那是 antigravity 的,不是 skill-bettor 的)。
- **技術修正(非內容刪減)**:`check_decision_html.py` 的 selftest 去外部檔依賴。

## 6. 判別「retarget 成立」的鐵錨

- 兩支腳本在 skill-bettor 新路徑上 `--selftest` 皆 exit 0(見 §4 實跑記錄,非複誦 antigravity 側
  結果)。
- `reference/antigravity-example-decision-dashboard.html` 確實存在、確實帶 banner、確實仍可被
  checker 讀出全 PASS(§4 第三項驗證)。
- `context-trace-example.html` **確實不存在**於 skill-bettor(`test -e` 應回傳假)——這是刻意的
  缺席,不是遺漏。
- SKILL.md/media-know-why.md 全文 grep 不出裸的「06 §A」「docs/plans/2026-07-09」「卡片庫」
  「卡片盒」等未加說明的 antigravity 專屬引用(有出現處均已附帶「antigravity 自己的」等明確標記)。

若哪天有人往本 skill 塞回 antigravity 具體計劃 slice 引用、或把 `context-trace-example.html`
原樣搬進來當 skill-bettor 案例,那就是把不成立的 provenance 或不存在的目錄慣例搬回來——擋下。

---

## Sources / Lineage
- antigravity 源:`.agents/skills/html-for-decisions/`(SKILL.md + `modules/media-know-why.md`
  + `prompts/decision-report.prompt.md` + `scripts/{check_decision_html,context_trace}.py` +
  `reference/{loop-panorama-decisions,context-trace-example}.html`,2026-07-11 讀取快照)。
- skill-bettor 既有同構:`ARCHITECTURE.md` §8(人閘清單)——本 skill 的「哪個節點算 LAND-DECISION」
  判準指針到此,不重複定義。
- 移植先例:`loop-harness-standard/modules/retarget-map.md`、`harness-wiki/modules/
  retarget-map.md`(本檔§2 的「northstar 比較不重複」判斷即援引後者已立的先例)。
