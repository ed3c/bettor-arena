# Module: loop-harness-standard — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`loop-harness-standard`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到
> skill-bettor、哪些因為架構前提不同被拿掉/降級、為何不是簡化。

---

## 1. 為何多數內容不能逐字複製——antigravity 原版摻了大量它自己的歷史證成紀錄

antigravity 原版 `harness-spec.md`(333 行)與 `evals-design-method.md`(90 行)裡,相當比例是
**antigravity 自己迴圈跑出來的證成紀錄**:具體 commit hash(`c65d927`/`3b602e5`/`add922c`)、具體踩坑
案例(R7 dangling-id、R8 tool-syntax-leak、M15-M20 subtle 播錯案例)、D1-D12 決策編號帳本、
`design_governance` pilot 的逐輪判官 finding。這些是 antigravity 自己的軌跡,不是可搬的方法論——
逐字複製會:①違反這份標準自己教的紀律(≤300 行反膨脹);② 跟 skill-bettor 已有的 `ARCHITECTURE.md`
§3-§7(已用 families/evals/holdout 詞彙萃取過一次同一套方法論)重複又打架。

**本移植只萃取可轉移的方法論**(8 基座卡精神、Verify 三層、evals 設計三段法、cache 不變量、驗證器
隔離原則),不搬歷史證成紀錄——skill-bettor 未來自己累積的軌跡,記在各家族 `changelog/`,不是繼承
antigravity 的。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| 2×2 host×driver 矩陣(Claude Code／Antigravity CLI 雙 host) | **拿掉,降為單軸 driver 選型** | skill-bettor 恆為 Claude Code 單 host,不存在「開這個 repo 的 CLI 換家族」的情境;N×M 矩陣、隔離翻面表整套不適用。這不是簡化,是架構前提真的不同(antigravity 兩個 CLI 都會開同一個 repo,skill-bettor 只有一個)。 |
| `.agents/*`(settings.json EAGER／hooks.json／skills.json／agents/verifier.md)agy 側平行目錄 | **拿掉獨立 host config 目錄,授權走 `run.sh` CLI 旗標;保留 sandbox-local domain endpoint 能力** | skill-bettor 的 op 沙盒本來就沒有雙 host 平行 config 維護的需求;agy/codex driver 啟用時才落 `AGENTS.md` entry。若 entry contract 與 `CLAUDE.md` 真同構,可採一實體＋symlink;若需 codex/agy 權限、findings-only、`ROUTES.md` 等 host-specific 邊界,採薄 wrapper 指回 `CLAUDE.md`。但小迴圈可有 `.agents/agents/*` 和 `.agents/skills/*` 作 domain/task route endpoint;它們不是 `settings.json`/`hooks.json`/`skills.json` 這類 host config。 |
| D1-D12 決策編號帳本 | **不搬** | 那是 antigravity 團隊自己的決策沿革記錄,skill-bettor 沒有對應歷史,硬搬＝引用不存在的脈絡。 |
| 具體 commit 錨、R7/R8/M15-M20 案例史、design_governance pilot 逐輪 finding | **不搬,改用「本地 worked instance 指針」句式** | 這些是 antigravity 自己迴圈的證成軌跡。skill-bettor 對應的是 `families/pinescript-audit/evals/`(已有的首個成長曲線原點)——指到那裡,不複製 antigravity 的案例。 |
| `PLAN.md`/`PROMPT.md`/`CLAUDE.md` 命名與職責 | **原樣映**(命名本來就相同) | antigravity Claude 側早已用這套短名(非 agy 側 `IMPLEMENTATION_PLAN.md`/`AGENTS.md`),skill-bettor `_template/` 已照此建;本移植只是把規範文件補上。 |
| 8 基座組件卡 | **改寫詞彙**(scripts/tests fixtures → family evals/runner.py;.claude/agents/verifier.md → fresh subagent inline 描述) | 精神一對一映,措辭改用 skill-bettor 已在 ARCHITECTURE.md §3 用過的詞彙,避免同一概念兩套講法。 |
| Verify 三層 | **原樣映**(T0/行為/畢業判官三層概念完全通用) | 這是全篇少數與 host/driver 矩陣無關、純屬「怎麼分層驗證」的方法論,無需改。 |
| evals 設計三段法(維度×槓桿/runnable-rubric/planted-defect) | **原樣映,worked instance 換成本地家族** | 方法論通用;`COMPLETENESS_RUBRIC`@`data.js` 這類 antigravity 專屬錨換成 `families/pinescript-audit/evals/`。 |
| cache 五不變量 | **原樣映**(Claude Code cache 機制與 host 無關) | 這條本來就是 Claude Code 平台事實,不因單/雙 host 而變。 |

## 3. 拿掉的東西不是「簡化」,而是「不引入不存在的架構前提」

- **能一對一映的映**:8 基座卡精神、Verify 三層、驗證器/執行者隔離原則、cache 不變量、evals 設計法、
  防退化鐵律裡與 host 無關的條款。
- **架構前提不同、真拿掉**:2×2 host 矩陣、隔離翻面表、agy 側獨立 `.agents/*` config 目錄——
  skill-bettor 單 host 的事實,不是能力縮水。
- **歷史紀錄、故意不搬**:D 編號決策帳本、commit 錨、R7/R8/M15-M20 案例史——那是 antigravity 自己的
  軌跡,skill-bettor 累積自己的在 `families/*/changelog/`。

## 4. 判別「retarget 成立」的鐵錨

- 本地活基座真存在:`loop_wiki/_template/`、`loop_wiki/engine.sh`(disk 已驗證)。
- 本地 worked instance 真存在:`families/pinescript-audit/evals/`(2026-07-11 已有首個成長曲線原點)。
- `loop_demo/{agy,claude_agy}` 本地目錄範例:見 loop-harness-standard SKILL.md 移植同批工作,
  若尚未落地以該任務狀態為準,不得假設已存在。

若哪天有人往本 skill 塞回 D 編號決策碼、antigravity 具體 commit 錨,或試圖重建雙 host 矩陣(除非
skill-bettor 真的要接 Antigravity CLI host),那就是把不適用的架構前提搬回來——擋下。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/loop-harness-standard/`(SKILL.md +
  `modules/{harness-spec,evals-design-method}.md`)。
- skill-bettor 既有同構:`ARCHITECTURE.md` §3-§7(同一套方法論的 tight/at-a-glance 版,本移植是其
  深度展開版,兩者不重複——ARCHITECTURE.md 給常駐脈絡,本 skill 給 on-demand 深度 know-why)。

---

## 2026-07-19 增補:oracle-aware 完成契約遷入(composer-integration Slice A)

- 上游 `harness-spec.md §5.1`(antigravity,2026-07-19 命名)→ 本地 **§4.5**(緊接 §4 Verify
  三層——本地章節結構不同,照本地落位,不抄上游編號)。
- **拿掉**:上游 checkpoint 記錄格式範本對 antigravity `dr-to-mvp/SKILL.md:46` 的行號指針(本地
  等價=`.claude/skills/dr-to-mvp` dual-score 設計分∧實作分段,採用不重造,不釘上游行號);上游
  cache oracle 句(本地 §5 已有);上游證成史/設計理由(留唯讀指針
  `/Users/neon/antigravity/docs/plans/2026-07-19-composer-integration-oracle-completion/01-*.md`,不搬)。
- **新增於本地而上游無**:誠實正名條款成文(「零飄逸只在 dense 成立」——HANDOFF §2 正名,防產品側
  過度承諾);B-1 斷言表 schema 定義權落 §4.5(上游定義權在其計劃檔 01,本地無該檔,升格進 spec)。
- 三態 grounding 不遷:本地 SSOT 已在 `judge-loop-chooser/modules/grounding-and-independence.md`,
  §4.5 只指針。

## 2026-07-19 增補:execution-feedback 遷入(composer-integration Slice B)

- module+4 checker+fixtures+verify.sh 自上游
  `/Users/neon/antigravity/.agents/skills/loop-harness-standard/{modules/execution-feedback.md,scripts/execution-feedback/}`
  遷入;**checker/fixtures 逐位元組帶入不改邏輯**(diff -rq 已證同構;no-smuggled-plan-delta 含
  上游 branch-1 剝標籤修 :23-25)。module 內文 retarget:
- **改指本地**:`harness-spec §5.1`→`§4.5`(×2);`§9❶ 人閘`→`ARCHITECTURE.md §8`;B-1 schema
  定義權「上游計劃檔 01」→本地 §4.5;軌跡實名 `driver.iterN.json`(上游)→`driver.iterN.out`
  (本地 engine.sh dispatch 落檔 `driver.iterN.out` 實名,執行時 grep 驗真);「codex exec 主+`< /dev/null` 鐵律」→本地唯一入口
  codex-companion+「寫≠真跑」補真跑(ARCHITECTURE §5 codex 列)。
- **拿掉**:antigravity 記憶引用(`anti-inflation-is-discriminator`/`agy-quota-silent-noop`——後者
  實質改指 ARCHITECTURE §5 agy 列同義警告);「D12 引擎家族」編號;定位段對上游 §9❶「三類編排
  skill」的指針(本地無此節,留實質句)。
- **新增於本地而上游無**:判官禁 ponytail hook 注入條款(本地已知 SubagentStart fail-open 注入
  風險);variant 目錄收攏形態「由 engine_nv wrapper(Slice C)定」的顯式留白。
- 上游計劃檔 02/05 以絕對路徑唯讀指針保留於 module 頭注,證成史不搬。

## 2026-07-19 更正(composer-integration Slice E,seam 審計追加)

- Slice A 節「拿掉 checkpoint 範本對 dr-to-mvp 行號指針」實際效果=**整條指針被拿掉,seam 第三環斷**
  (上游定案鏈:sdlc Output Contract→完成契約 §→dr-to-mvp dual-score;上游 slice 04 A5=dr-to-mvp
  零改動,方向=單向採用)。Slice E 已補回**本地**指針:§4.5 sparse 條→`dr-to-mvp` dual-score 段,
  LIVE 錨=mvp-radar 2026-07-19 畢業。「不釘上游行號」的原意保留,錨改本地活實作。
