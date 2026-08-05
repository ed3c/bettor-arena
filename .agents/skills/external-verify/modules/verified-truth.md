# Module: 已查證真相 — skill-bettor 本地累積表

> 屬 [`external-verify`](../SKILL.md) skill。本檔的**角色**跟 antigravity 原版相同:一份會隨時間增列
> 的「已對外部 primary source 查證過的事實」快照,復用前依 SKILL.md step 1-2 重跑,別讓過期真相被當
> 定局沿用。
>
> **與 antigravity 原版的差異(誠實現況)**:antigravity 原版這份表的每一列都是 **Google Antigravity
> CLI 平台**的事實(`AGENTS.md` canonical 檔名、`.agents/skills/` 目錄、`~/.gemini/...` 三層 scope、
> `GEMINI.md` 存在性)——那是**錯平台的事實**,skill-bettor 是 Claude-Code-only 專案,逐字複製視同灌入
> 假鐵錨,故整份不搬(見 [modules/retarget-map.md](retarget-map.md))。本檔改為 skill-bettor 自己的
> 表,目前只有下方這批**移植當下(2026-07-11)順手用 WebFetch 對官方文件真查證過**的 Claude Code
> Skill 規範事實;其餘留白——等 skill-bettor 未來真的碰到 post-cutoff/不可錨 claim、真的跑過
> SKILL.md 的 6 步 runbook,才 append 新列,不預先杜撰更多列撐場面。

## 已查證真相表(2026-07-11 snapshot)

| Claim | 判定 | 信心層 | 鐵錨 |
|---|---|---|---|
| Claude Code 專案 skill 路徑 = `.claude/skills/<skill-name>/SKILL.md`;個人 skill = `~/.claude/skills/<skill-name>/SKILL.md` | ✅ 真 | CONSENSUS(primary) | Claude Code Docs「Where skills live」表 |
| 官方建議 `SKILL.md` 本體 **保持在 500 行以下**,細節搬到獨立參考檔案 | ✅ 真 | CONSENSUS(primary) | 同上文件原句:"Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files."(直接支持 skill-bettor `ARCHITECTURE.md` 已在用的「子技能 <500 行+references/」慣例——不是本檔發明,是官方文件本來就這樣建議) |
| Claude Code 的 `.claude/commands/<name>.md` 已併入 skills;兩者建立同一個 `/name` 且行為相同 | ✅ 真 | CONSENSUS(primary) | 同上文件原句:"Custom commands have been merged into skills. A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way." |
| 在 **Claude Code** 這個 surface,SKILL.md frontmatter **全欄位選填**,只有 `description` 被「建議」(非強制);`name` 未填則退回目錄名 | ✅ 真(但見下一列的範圍落差) | CONSENSUS(primary) | 同上文件原句:"All fields are optional. Only `description` is recommended so Claude knows when to use the skill." |
| ⚠ 兩份官方文件對 frontmatter 驗證嚴格度的敘述有落差,哪個規則實際套用到 Claude Code 本地 skill 尚待查證 | 未證(待查) | FRONTIER-CONTESTED | 更廣的「Agent Skills」開放標準頁明訂 `name`/`description` 為**必填**且有嚴格 regex(`name` ≤64 字元、僅小寫字母/數字/連字號、禁 XML tag、禁保留字 `anthropic`/`claude`;`description` 非空、≤1024 字元、禁 XML tag),但 Claude Code 專屬頁面同時稱「全欄位選填」。兩頁可能談的是不同 surface(API/claude.ai 上傳 skill vs. Claude Code 檔案系統 skill),本次未進一步查證兩條規則是否都對 Claude Code 本地 `.claude/skills/` 生效——**不可**斷言本地 skill 一定套用那組嚴格 regex 驗證,寫 `name`/`description` 時保守起見仍建議照嚴格規則走(小寫/連字號/避開保留字) |
| Skill 內容分三層 progressive disclosure:metadata(常駐,約 100 tokens/skill)/ SKILL.md 本體(觸發才載,建議 5k tokens 以內)/ bundled 資源(需要才讀,近乎零成本) | ✅ 真 | CONSENSUS(primary) | Agent Skills overview 頁的三層對照表 |

> 本表**只**收「已對官方 primary source 查證過」的事實,不收專案內部踩坑得來的經驗法則(例如
> frontmatter YAML 對 `": "` 這類字元組合的解析地雷——那屬於 SKILL.md Gotchas 段的**未外部驗證**實務
> 知識,不是官方文件明文規定,別跟本表混為一談)。

## Sources(★ = primary)
- ★ Extend Claude with skills — Claude Code Docs: `https://code.claude.com/docs/en/skills`
- ★ Agent Skills — Claude Platform Docs: `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview`

## 已查證真相表(2026-07-20 snapshot — SkillBench 生態批次)

> 來源:他處 AI 產出的 SkillBench/SkillsBench 綜述語料,經
> `docs/plans/2026-07-20-skill-spec-decompression/PLAN.md` §1(行 32-46)逐 claim 查證。
> 逐條卡片格式(非單一寬表)——理由=過期重驗可獨立進行、新增條目 diff 最小,見該計劃 §4 決策一。

### #1 SkillsBench 論文(arXiv:2602.12670)
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://arxiv.org/abs/2602.12670`
- 逐字關鍵句:"at most three modules outperform larger bundles"(結構事實:87 tasks/8 domains/+16.6pp)
- 走樣註記/反證:語料自創專名「Paired Skill Lift」,全文無此詞,真實機制=paired evaluation(同 agent 有/無 skill 對照跑同任務)
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #2 SWE-Skills-Bench(arXiv:2603.15401)
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://arxiv.org/abs/2603.15401`
- 逐字關鍵句:"39 of 49 skills yield zero pass-rate improvement, average gain only +1.2%"
- 走樣註記/反證:語料引用時隱瞞此為負面結論,誤植為正面背書——本身是 PRODUCT.md 佐證提案(04 §3 Task 2,▣ 人裁未執行)的鐵錨來源
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #3 SkillLearnBench(arXiv:2604.20087)
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://arxiv.org/abs/2604.20087`
- 逐字關鍵句:PLAN.md 查證當下未摘錄逐字句,以下為結構事實(非逐字引文)——continual skill learning,20 tasks/15 sub-domains
- 走樣註記/反證:無
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #4 SkillFlow(arXiv:2504.06188)
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://arxiv.org/abs/2504.06188`
- 逐字關鍵句:PLAN.md 查證當下未摘錄逐字句,以下為結構事實(非逐字引文)——multi-stage retrieval over ~36K SKILL.md corpus
- 走樣註記/反證:無
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #5 benchflow-ai/skillsbench repo
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://github.com/benchflow-ai/skillsbench`
- 逐字關鍵句:PLAN.md 查證當下未摘錄逐字句,以下為結構事實(非逐字引文)——Apache-2.0、87 tasks
- 走樣註記/反證:預設沙盒=Modal 雲,Docker 是替代非預設
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #6 Arcade SkillBench 六維權重
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://www.arcade.dev/blog/skillbench-agent-skills-benchmark/`(04 OQ3 已回填,查證時已取得,免複查)
- 逐字關鍵句:35/25/12/8/10/10 六維權重數字逐字吻合、A–F 評級存在
- 走樣註記/反證:原文 39,000,語料引為「50,000」無錨
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #7 anthropics/skills repo
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://github.com/anthropics/skills`
- 逐字關鍵句:PLAN.md 查證當下未摘錄逐字句,以下為結構事實(非逐字引文)——repo 存在
- 走樣註記/反證:混合授權——多數 Apache-2.0,但 docx/pdf/pptx/xlsx 是 source-available 非開源(引用時不得逕稱「全 Apache-2.0」)
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

### #8 Microsoft 63,000 開發者部署
- 判定:CONTRADICTED-hallucination(來源自身反證:官網自述 10 人/v1 未出;非僅查無證據,04 §6d/§6b 條 5 暫行慣例)
- 信心層:(幻覺類免填,反證見下)
- 鐵錨 URL:未定(執行時三角搜索起點:Workable 職缺頁/公司官網;PLAN.md 查證當下未存 URL 快照,複查者需重新三角定位)
- 逐字關鍵句:無(幻覺類,無逐字支持句;反證見下)
- 走樣註記/反證:語料宣稱來源(Workable 職缺頁+公司官網)經查無 Microsoft/63,000 字樣;實況=10 人 startup,v1 尚未發布。**標記目的=防復活,非留待補完**
- 查證日期:2026-07-20
- 過期紀律:**永不復活**——非「執行時補」欄位,任何日後語料重提此 claim 一律視為舊語料復燃,直接引本卡駁回;若出現新反證/正證需經 external-verify 六步重跑並另經人裁覆蓋本條標籤

### #9 DeepMind 評估 50,000 技能/no-op
- 判定:NOT-FOUND-hallucination(查無 primary;非查得反證,04 §6d/§6b 條 5 暫行慣例,與 #8 CONTRADICTED 標籤分立)
- 信心層:(幻覺類免填,反證見下)
- 鐵錨 URL:未定(查無 primary,無可指三角搜索起點)
- 逐字關鍵句:無(幻覺類,無逐字支持句;反證見下)
- 走樣註記/反證:無任何 DeepMind primary 來源可指;SkillsBench 論文全文 grep「no-op」零命中;疑三個真數字混裝(39K[Arcade]+36K[SkillFlow]+workshop 掛名)。**標記目的=防復活**
- 查證日期:2026-07-20
- 過期紀律:**永不復活**——非「執行時補」欄位,任何日後語料重提此 claim 一律視為舊語料復燃,直接引本卡駁回;若出現新反證/正證需經 external-verify 六步重跑並另經人裁覆蓋本條標籤

### #10 Arcade Deploy blog
- 判定:VERIFIED-primary
- 信心層:CONSENSUS(primary)
- 鐵錨 URL:`https://www.arcade.dev/blog/introducing-arcade-deploy-instant-hosting-for-your-custom-ai-tools/`(04 OQ3 已回填,查證時已取得,免複查)
- 逐字關鍵句:"arcade deploy"單命令雲端託管
- 走樣註記/反證:無(但護城河章節「業界已普遍採取」定調本身無錨,當設計選項看待,非既成事實)
- 查證日期:2026-07-20
- 過期紀律:復用前重跑 external-verify SKILL.md step 1-2(§37-42);論文/repo 有新版本或勘誤即失效

**引用規範**(一句一條):
- 提「Paired Skill Lift」一律改稱「paired evaluation(同 agent 有/無 skill 對照)」,前者非 SkillsBench 論文原詞。
- 提 benchflow-ai/skillsbench 預設沙盒一律稱「Modal 雲端」,Docker 只在明確語境下稱「替代選項」。
- 提 Arcade SkillBench 語料規模一律稱「39,000」,「50,000」不得沿用(無錨數字)。
- 提 anthropics/skills 授權一律稱「以 Apache-2.0 為主、docx/pdf/pptx/xlsx 例外 source-available」,不得逕稱「全 Apache-2.0 開源」。

**加驗觸發條件**(gcr 語料實體整批驗真,PLAN.md §1b:57-66):
- 預設不開:單條已由本批 external-verify 完畢,無需升級。
- 唯一觸發條件:人決定對 gcr 語料的外部實體(SkillBench 1.1/Philipp 團隊/Matt repo)整批驗真——屆時依
  `truth-verify-loop` SKILL.md「本地實例化契約」建 `loop_wiki/tv-skillbench-entities/`,先 selftest
  後真跑,成本 ▣ 人裁(指針該 skill,不展開六階段拓撲/不變量細節)。

## 已查證真相表(2026-07-20 snapshot — Claude Code Agent Skills 官方規範)

> 查證緣起:gcr 對話宣稱「skill 動態注入腳本」等機制,查 Claude Code / Anthropic 官方
> primary 釘死平台真相(別建在 Gemini 藍圖上)。全 primary,錨見各條。

### #C1 skill 目錄可 bundle 可執行腳本 + 官方結構
- 判定:VERIFIED-primary
- 鐵錨 URL:`https://code.claude.com/docs/en/skills` + `https://platform.claude.com/.../agent-skills/best-practices`
- 逐字關鍵句:"Skills can bundle and run scripts in any language";結構=`SKILL.md`(唯一必需)+選配 `scripts/`/`reference.md`/`examples/`
- 查證日期:2026-07-20;過期紀律:官方 docs 改版即失效,復用前重跑 step 1-2

### #C2 腳本「執行、不注入」+ Progressive Disclosure 三層(承重鐵律)
- 判定:VERIFIED-primary
- 逐字關鍵句:"Utility scripts can be executed through bash **without loading their full contents into context**. Only the script's output consumes tokens.";三層="Metadata pre-loaded → Files read on-demand → Scripts executed efficiently"
- 走樣/反證:gcr「注入 context」機制 **CONTRADICTED**——官方 filesystem-backed on-demand,非 context-injection

### #C3 frontmatter 官方硬約束(已落 check_skill_conformance.py)
- 判定:VERIFIED-primary
- 逐字關鍵句:"requires two fields: name ... description: Maximum 1,024 characters";name "Maximum 64 characters, lowercase ... no reserved words: 'anthropic', 'claude'";body "under 500 lines for optimal performance"
- 註:CC 端 listing 截斷 1,536 字元 vs frontmatter 硬上限 1,024——不同層級兩數,非矛盾

### #C4 觸發=description 語義自選,無 skill-invoke hook matcher
- 判定:VERIFIED-primary
- 逐字關鍵句:"the description helps Claude decide when to load the skill automatically"、"The description is injected into the system prompt";hook events 30 個中**無** SkillInvoke;`UserPromptExpansion` 只攔用戶手打 `/skill` 展開;skill frontmatter 可**內含** scoped hooks
- 走樣/反證:gcr「hook/matcher 觸發 skill」無 Claude Code 原生對應

### #C5 安全=權限+信任+自審,非沙盒
- 判定:VERIFIED-primary
- 逐字關鍵句:"Review project skills before trusting a repository, since a skill can grant itself broad tool access";`disableSkillShellExecution` managed setting;`Skill(name)` allow-deny
- 走樣/反證:官方無腳本沙盒/憑證隔離/blast-radius 技術保證;gcr 若宣稱沙盒=未驗證加碼

### #C6 動態上下文注入機制(2026-07-20 第二輪;**修正 C2 過度修正**)
- 判定:VERIFIED-primary(錨 code.claude.com/docs/en/skills §"Inject dynamic context")
- **`!`cmd`` 行內注入**:逐字 "The `` !`<command>` `` syntax runs shell commands before the
  skill content is sent to Claude. The command output replaces the placeholder";preprocessing
  非 Claude 執行;`!` 行首或空白後才觸發(`KEY=!`cmd`` 不觸發);多行用 ```! fence。作用在 SKILL.md body。
- **`context: fork`**:逐字 "Set to `fork` to run in a forked subagent context";"It won't have
  access to your conversation history ... Results are summarized and returned";配套 `agent` 欄位。
- **`hooks` frontmatter**:欄位存在,但 schema=**事件式**(`PreToolUse:`→matcher→hooks[]),
  **非** `before/after`;scoped to 該 skill lifecycle。
- 修正註:C2「執行不注入」只講 `scripts/` helper(execute-not-load);`!` 注入是**另一機制**
  (命令 stdout preprocessing 塞進 prompt)。兩者共通=**只有輸出進 context、程式碼本身不進**。
  首版「注入是 Gemini-ism/Claude 無此機制」**過度修正,已推翻**——官方自用「injection」術語。

### #C7 常見 SKILL.md 貼文的幻覺/自造語法(CONTRADICTED,防被當官方引用)
- **「Claude Code Skills 2.0」版本名**:NOT-FOUND——官方無此版本名,只有 CLI 版號 v2.1.x;社群品牌化。
- **`hooks: before/after` frontmatter**:CONTRADICTED——真實是事件鍵巢狀(`PreToolUse` 等),無 before/after。
- **OpenCode 與 Claude Code「同規範」涵蓋 `!`/`context:fork`/`hooks`**:走樣——那三者是 Claude Code
  專屬擴充(官方逐字 "Claude Code extends the standard with ... subagent execution, and dynamic
  context injection"),OpenCode 靜默忽略未知欄位;只有 name+description+progressive-disclosure 跨 tool。

**引用規範(Claude Code 官方形態;2026-07-20 二輪校正)**:
- `scripts/` helper=「執行、只 stdout 進 context」;`!`cmd``=「官方動態上下文注入(命令輸出 preprocessing)」
  ——**兩機制別混,也別再說「注入不存在」**(首版誤斷已改)。共通=程式碼本身不進 context。
- 觸發=description 語義自選(無 skill-invoke 事件);但 skill 可**內含**事件式 scoped hooks。
- 安全=權限+workspace trust+自審,非沙盒;禁宣稱 blast-radius 沙盒保證。
- gcr「SkillBench 1.1」是 benchmark 論文(arXiv:2602.12670)非規範;「50,000+ 生態」NOT-FOUND 不得引。
- `context: fork` 是真官方機制(subagent 隔離防 context 汙染);`hooks: before/after` 是自造,勿用。

### #C8 gcr「047d548 技能治理藍圖」外部事實查證(2026-07-21,clc 全景等價驗證第 4 軸)
> 查證動機:判「defense-form ≟ gcr」時,先查 gcr 藍圖本身是真是幻覺(幻覺則「等價於它」無意義)。
- **gcr 方法論=VERIFIED-primary**:整份藍圖=Philipp Schmid(Google DeepMind)「Don't Ship Skills
  Without Evals」真實方法論的系統化。錨=`philschmid.de/testing-skills` 逐字:「10–20 prompts enough
  to begin」「Don't skip negative tests(too-broad description triggers on every prompt)」「regex
  assertions」「second model-assisted pass(LLM judge)」「run evals with skill unloaded→if pass,
  retire(ablation 退役)」「run 3–5 trials per case, look at distribution」。gcr 的 10-20/happy-negative/
  regex/judge/ablation/3-6 trials **全部對得上真來源**。
- **gcr 頭條數字=VERIFIED-primary**:錨=SkillsBench arXiv:2602.12670(87 tasks/8 domains)。curated
  skills **+16.6pp(33.9%→50.5%)、25.5% normalized gain**=gcr「~15% 增益」真來源;**self-generated
  skills offer no benefit**=gcr「盲堆疊 AI skill 退化」真來源。(gcr「1.1/100 任務/117 cases/50,000+」
  =近似 embellish,真是 87 任務;「50,000+」仍 NOT-FOUND。)
- **gcr 程式符號=CONTRADICTED-hallucination**:Interactions API **存在且為官方 primary interface**
  (錨=`ai.google.dev/gemini-api/docs/interactions-overview`,2026-06 GA),但 gcr 的具體符號全錯——真
  API=`interactions.create()`(**非** `createSession()`)、多輪用 `previous_interaction_id`(非 session)、
  套件 `google-genai`/`@google/genai` v2.3.0(**非** `@google/gemini`)、真 import `from google import
  **genai**`(**非** gcr 的 `import gemini`)。gcr P11 的 SDK 範例是圍繞真 API 編造的裝飾。
- **gcr 的 git-hook/CI 熔斷/500 行/「DeepMind G1 治理政策」框架=gcr 自行 embellish**:testing-skills
  **明言不提** git hooks/CI gates/skill 行數死線(WebFetch 逐字「does not mention git hooks, CI gates,
  or line-limit thresholds」);「>500 行 degrade reasoning」來自 Schmid 另一篇(talk/agent-skills-tips)非本文。
- **對等價判定的意義**:skill-bettor 的 500 行閘/fluff/10-20 cases(WARN)/ablation 退役與 gcr **同源自
  Schmid**——兩者是同一方法論的獨立實作(skill-bettor retarget 到 expect.yaml/Claude,gcr embellish 成
  部分虛構的完整藍圖),非誰抄誰。故「51.3% 行為等價」讀作「共享 methodology 骨幹,各自實作與擴充分歧」。
- 查證日期 2026-07-21;過期紀律:Interactions API 版號/SkillsBench 版本會演進,引用前重跑 step1-2。

---
**空白模板紀律**:上面這批是移植當下順手查證的種子,**不是**要求以後每次都補滿一張大表。之後 append
新列的規則跟 antigravity 原版相同——真的碰到 post-cutoff/不可錨 claim、真的跑過 SKILL.md 6 步
runbook,才寫新列;沒發生驗證就不假裝已驗證。
