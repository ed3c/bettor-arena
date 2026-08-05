# Module: grounding 三態 + 四層獨立性階梯 — know-why(Layer B)

> 屬 [`judge-loop-chooser`](../SKILL.md)。SKILL.md 有路由決策樹 + 快查表;本檔 = **兩條正交軸的
> know-why**(為何是三態不是二元、為何獨立性看權重不看強度、為何兩軸不可塌成一軸)。
> 查證外部 claim → [`external-verify`](../../external-verify/SKILL.md)。`path-b-reduction` 現已本地
> 落地,但只作 claim 約分 helper;本檔 T2 一節不得把它寫成外部 fact checker、verdict 或 admit。

---

## 軸一:grounding／anchor-reality(技術實現等價物,三態)

### 問的問題與取值
> 驗證方法的判決**底下到底有沒有真實技術實現**?取值＝ `technical_equivalent` / `candidate` /
> `[推論]`(三態,不是二元)。

這條軸**不是**在問「被驗的項目是機械還是語意」——一個看似機械的 check(比如 `judge.py` 的
`program` kind)其驗證方法可能是**空心 pattern 匹配**(結構保留卻沒驗到真東西)。check kind 看不到
這個空心,grounding 軸才抓得到。

### 為何三態,不二元(命門)
```
[推論](無真 impl) ─── candidate(真 impl,覆蓋未掙) ─── technical_equivalent(完整覆蓋,已判讀)
```
- **technical_equivalent**:判決約分到「判讀一個真實 planted-defect fixture 的**完整**
  selftest good/hollow 覆蓋結果」。skill-bettor 合格錨 ＝ `evals/cases/<skill>/<case>/fixtures/*.pine`
  這類真植入缺陷的樣本 + `selftest.sh` 已證該 checker 對 good fixture PASS、對 hollow fixture FAIL。
  **覆蓋是掙來的、非假設**——一個 check 存在不代表它真的被驗證過會抓到它宣稱要抓的缺陷。
- **candidate**:真實 fixture/rubric **存在**但覆蓋未掙。字面例子 ——
  `families/pinescript-audit/evals/judge.py` 對缺 `--judge-cmd` 的 `llm_judge` check 標
  `{"status": "skipped", "evidence": "no --judge-cmd provided; excluded from denominator"}`:
  rubric 是真的(如 `explains-why-safe` 要求報告正確解釋 `close[1]`+`lookahead_on` 安全慣用法),
  只是這輪沒被執行去驗。**candidate ≠ [推論]**——把「真 rubric 未驗」判成「沒有這條驗證」會低估
  真件、扭曲覆蓋率真相。
- **[推論]**:無真實現。誠實標三種來源:
  1. bespoke pattern/regex 命中(`judge.py` 的 `_find()` 只做子字串/大小寫不敏感 regex 搜尋,無否定
     語境排除)—— 不判任何真實現的測試 ＝ **空心-T0 placebo**。
  2. LLM 判斷(`llm_judge` check 的 PASS/FAIL)—— 是給人的證據,**非放行令**。
  3. `external_primary`(external-verify 抓的官方文件事實,如 Pine Script v6 語法行為)——
     相鄰**事實**錨,**非方法-執行等價物**,另列。

### 這條軸在 skill-bettor 早已被實踐(demand-pull,非外來 import)
`ARCHITECTURE.md §4`「① T0 機械」列的正是 `judge.py` program/absent checks(權重 ≥70%)+
`runner.py --compare` G1-G3;「② 行為」列的正是 `evals/cases/`(埋 bug fixtures = planted-defect,
負例 = good fixture 不得誤報)——**與本軸同一方法論**。**本 skill 不是新增紀律,是把散在
`evals/` check 設計裡的紀律升格成可判標準**——判「`runner.py --compare` 吐回的 G 閘綠,哪些勾是真的
還是空心」。

### release ≠ 一個綠勾(skill-bettor 版三級)
northstar/antigravity 版有「green anchor → gate → 人 admit」多級閘。skill-bettor 同精神:
1. **證據**:該 check 真指到一個 `evals/cases`/`evals/holdout` 下的 fixture,且該 fixture 本身
   有 `selftest.sh` 的 good/hollow 正控佐證。
2. **provenance**:來源可追溯(fixture 路徑/expect.yaml check id,非「模型自稱有測到」)。
3. **人 admit**:把 G 閘結果交人收下(ARCHITECTURE §8 人閘①)。綠勾是**證據**,不是**授權**——
   消費一個「pattern 命中」但無 fixture 錨的 check 當 technical_equivalent ＝ placebo。

---

## 軸二:四層獨立性階梯(whose-weights)

### Same-Weights 陷阱有兩個可分離的成分
驗「輸出有沒有服務意圖」而 producer 與 verifier 都是 LLM 時:
- **脈絡/路徑相關**——verifier 繼承 producer 的框架、既定假設、對話史。
- **權重相關**——同權重對同輸入有**同系統性盲點**(共享幻覺、重疊訓練分佈缺口)。

多數「修法」只碰**一個**。persona 多樣化 / 換更強的**同 vendor** tier / 多迭代都**破不了任一個
完整**(仍同權重或同血緣)。**Sonnet author × Sonnet judge ＝ Sonnet-on-Sonnet(同權重)**;
**Sonnet author × Opus judge** 減緩脈絡相關(不同 drafting 史)但仍**同 vendor**(Claude),不是真正
跨家族。skill-bettor 唯一真跨家族的組合是 **agy(Gemini)產出 findings,交 Claude 側複核**(或反向)。

### 四層(cheapest first;每層抓下層抓不到的)
- **T0 確定性**(exit-code / `verify.sh` 聚合 / `runner.py --compare` / selftest good-hollow)
  → 無權重 ⇒ 破**兩半**。最大化這份額。
- **T1 零存取**(fresh zero-context subagent + 封裝包＝intent + artifact + rubric,**無 drafting
  史**,**禁 fork** —— 這是 ARCHITECTURE §3 基座 6、§7 鐵律 2 已寫死的硬約束,非本 skill 新加)→
  只破**脈絡**相關。同家族(Sonnet author × Sonnet/Opus judge)**必落地**此層。
- **T2 跨家族 Diamond**([`external-verify`](../../external-verify/SKILL.md) 官方 doc /
  [`path-b-reduction`](../../path-b-reduction/SKILL.md) claim 約分 / agy(Gemini)跨家族 findings,
  **非 verdict**——ARCHITECTURE §5 硬約束「agy 只產 findings 不 verdict」)→
  唯一**觸**權重相關,且**僅靠三角測,非「解決」**(共享網路語料盲點仍在)。
  `path-b-reduction` 現已本地落地,用途是把 claim 約分到「物理鐵錨/人為槓桿/微觀總代價/約分消去」;
  它是 T2 的語意約分 helper,不是外部事實查證器,也不是 admit verdict。
- **T3 人**→ 最終權威(LAND-DECISION,ARCHITECTURE §8 人閘清單)。

### 操作判準
1. **「能單憑封裝包重現」＝閘**。無脈絡可重現 ⇒ 騎在可勾稽的斷言上 ⇒ 逃出權重 ⇒ 信 T1。不可重現
   (要整體語感)⇒ `needs_diamond` ⇒ T2/T3。
2. **斷言化 rubric 有自己的盲點**——它抓它斷言的,漏 **negative-space**(被靜默省略的,如 changelog
   列 5 個已知問題,diff 只處理了 1 個卻宣稱「已處理已知問題」),那既抗斷言又抗 packet-reproduce ⇒
   不可約 T2/T3。空心保結構的 overfit 會過所有結構斷言(＝ hollow-T0)。**把線往下壓,永不到零。**
3. **對抗式跨家族 > 獨立 eval,只在**其輸出＝可證偽的攻擊向量、由確定性 oracle 裁決,**不是**辯論到
   共識(兩模型辯到 consensus collapse 無效)。
4. **tier-by-role**:便宜 tier(Flash/Haiku 級機械掃描)OK,若有確定性 oracle 兜底(ARCHITECTURE §5
   「機械執行」列已寫死);**Opus/人**用在無 oracle 處(方向 / 局部最小 / negative-space)。判官硬地板
   永不 Haiku、永不 agy-as-verdict(ARCHITECTURE §5 硬約束①,不可簡化)。
5. **persona 注入破 T1 起點**(2026-07-17 實測):persona-mounting 插件(如 ponytail 的 SubagentStart
   hook,fail-open 注入所有 Task 子代理)會把人格 ruleset 灌進 fresh subagent——T1 的定義=zero-context
   起點,任何注入都已破壞定義。選 T1 前查 active persona hooks;限縮=`PONYTAIL_SUBAGENT_MATCHER`
   只匹配實作型 agent_type,判官型 dispatch 用不匹配的 type(設定與正控測試 →
   `docs/plans/2026-07-17-agent-native-sdlc-panorama/03-slice-ponytail-mounting.md`)。

### 為何「畢業/spawn 決策」不是一個模型 tier
op 執行尺度(author 寫 diff)可配模型(Sonnet)。但「**該不該 merge / 該不該 spawn 新家族 ＝ 人的
LAND-DECISION,永不是模型 tier**」(ARCHITECTURE §8:merge admit / holdout 畢業 admit / spawn 新家族
皆列人閘)。這類決策的驗證也塌回人/獨立知識論,永不是更便宜的同 vendor tier —— 這就是 T1 單獨不夠、
T2 Diamond + T3 人是結構性的原因。

---

## 兩軸為何正交(不可塌成一軸;誤改命門)

| 軸 | 問題 | 取值 |
|---|---|---|
| ① grounding | 判決底下有沒有真實現? | technical_equivalent / candidate / [推論] |
| ② 獨立性 | 驗證者誰的權重? | T0 / T1 / T2 / T3 |

一個 check 可以 **T0-independent 但 HOLLOW**:獨立性軸判它 T0 可信(純機械、無 LLM 權重涉入),
grounding 軸判它 placebo(空心 pattern 沒驗真東西 —— 如 `pattern: 'lookahead'` 命中「沒有 lookahead
風險」的報告)。**hollow-T0 cell 正是獨立性軸單獨漏、grounding 軸才補的格。** 把 grounding 寫成
「T0/機械＝等價物」的簡單 mapping ＝ 塌軸 ＝ 丟掉 anchor-reality 判別力(＝這條紀律在防的扭曲)。
兩軸各自升旗:`needs_diamond`(獨立性)與 grounding `[推論]` 獨立。negative-space residue ＝ 兩軸都
不可約 ⇒ T3 人。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/judge-loop-chooser/modules/
  grounding-and-independence.md`(其 SSOT 錨 `data.js` COMPLETENESS_RUBRIC —— 該檔案在 antigravity
  自己模組化後已從 `automate.js` 搬到 `data.js`,舊 skill 文件裡的行號引用已偏移,本次 port 不繼承
  該行號)。northstar 更上游源見該檔案自己的 Sources 段。
- skill-bettor 活基座:`families/pinescript-audit/evals/runner.py` +
  `families/pinescript-audit/evals/judge.py` + `families/pinescript-audit/evals/cases/` +
  `families/pinescript-audit/evals/holdout/` + `ARCHITECTURE.md` §4(disk 已驗證,見 retarget-map
  的鐵錨清單)。
- **不搬**:antigravity 版 truth-verify 實測錨(2026-07-05/06 六 run 的具體數字)——那是 antigravity
  自己迴圈的證成軌跡,不是 skill-bettor 的證據;SKILL.md Gotchas 已用一句話轉述課,不重複数字表格。
