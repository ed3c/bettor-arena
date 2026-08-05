# Module: sdlc-plan-composer — S4 多模型子代理分發(四角色分工+fallback)

> 屬 [`sdlc-plan-composer`](../SKILL.md) S4。**檔位 enumeration 的 SSOT=`ARCHITECTURE.md` §5**
> (2026-07-17 擴充版:codex 三檔+agy 註記+硬約束⑤+額度 fallback 鏈)——本檔只放**分發方法論**,
> 不重抄檔位表(1 enumeration+N 指針,決策記錄=計劃包 `docs/plans/2026-07-17-agent-native-sdlc-panorama/
> docs/decisions/tier-dispatch-carrier-choice.md`)。codex 呼叫協定=[codex-integration.md](codex-integration.md);
> 24 atomic skill 的性質映射=[mattpocock-skill-inventory.md](mattpocock-skill-inventory.md)。
> 誕生=該計劃包 2026-07-17 實跑+Q1-Q8 人裁,先例證據=
> `docs/plans/2026-07-17-agent-native-sdlc-panorama/implementation-notes.md` 與同目錄 `00-intent-and-knowhow.md` §4 tracer 帳。

## 四角色頂層分工(先套這個透鏡,再查例外)

| 角色 | 檔位 | 管什麼 |
|---|---|---|
| **計畫** | Fable 5 主會話 | S-1..S5 編排/S3 方案比較/交接設計評審 |
| **Judge** | Opus fresh zero-context(禁 fork) | 一切 verdict;**斷供=判決排隊,永不降檔** |
| **執行** | codex(檔位×effort → §5 該列;入口=`codex:codex-rescue`) | implement/tdd/diagnose 修復/repro/第二實作/交叉 driver |
| **真相** | agy(Pro 3.1=研究/複核 findings-only 唯讀;Flash=機械掃) | DR 批次/external-verify 執行體/跨家族複核;迴圈化=[truth-verify-loop](../../truth-verify-loop/SKILL.md) |

## 例外七條(分工不覆蓋的載重部位;違反=INCOMPLETE)

1. **人=第五角色**:admit 永遠人;Opus 產的是 verdict 候選。
2. **零 LLM 腳本>一切模型**:verify.sh/runner.py/check_*.py 是「執行」最大宗,不歸 codex。
3. **Sonnet 不可替代位**:eval agent 量尺釘死(ARCHITECTURE §7 鐵律 3),分工與 fallback 永不觸碰。
4. **機械池不升格**:Haiku/Flash/mini 成為 fallback 不取得 author/verdict 權。
5. **S1 人在場 skill 不歸模型角色**+**自主模式降級程序**(2026-07-17 實跑先例):grilling 家族
   (grilling/grill-me/grill-with-docs/domain-modeling/loop-me)在用戶不在場時照跑=空轉;降級=
   意圖重建寫入 `00-intent-and-knowhow.md`+開放問題清單交人閘(裁決用 AskUserQuestion 分批 ≤4 題,
   推薦項放首位),用戶回場後可補跑 grilling 修正——降級記錄在案,非省略。
6. **ponytail persona=疊加層**,與四角色正交;判官型禁疊
   ([judge-loop-chooser 操作判準 5](../../judge-loop-chooser/modules/grounding-and-independence.md))。
7. **演化 op author 維持 Sonnet 預設**(Q8 人裁):資產賣給 Claude Code 訂閱者,author 與目標市場
   同家族+量尺對齊;codex 以 §6 雙 harness 交叉驗證身分並跑,不取代。

## 分發程序(每個 S4 委派逐步)

1. **判任務性質**:編排/作者/判官/機械/研究/人機對話(atomic skill → inventory 映射表)。
2. **套四角色 → §5 選檔位與 effort**。
3. **葉節點檢查**(SKILL.md §S4 葉節點約束):design-an-interface/code-review/
   improve-codebase-architecture=委派即讓其自分治,外層不再包。
4. **外部 CLI 檔位 → tracer 分層**:第一層=零額度名單探針(`agy models`/`codex --version`+config 讀取);
   第二層=最小真 dispatch 判活——**判活看輸出檔/session log,永不信 exit code 與模型自報**
   (2026-07-17 proof run 實測:codex 自稱 gpt-5,session log 實為 gpt-5.4-mini)。
5. **斷供 → §5 fallback 鏈**;事件記帳(計劃執行=`implementation-notes.md`;小迴圈=沙盒 `PLAN.md`),
   **禁 silent fallback**——跨家族 findings 由 Sonnet 代打=獨立性降級,消費端必須看見標記,
   silent=獨立性洗白。降級不改原檔位禁令。
