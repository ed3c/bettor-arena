# Specs-as-Code 提示詞 v1(ready to paste，skill-bettor 版)

> 屬 [`repo-agent-native`](../SKILL.md)。方法論全文 → [`codebase-mastery-methodology.md`](codebase-mastery-methodology.md)。
> **這是 antigravity `repo-agent-native/modules/specs-as-code-prompt.md` 的 skill-bettor retarget**
> ——提示詞本體(tool-agnostic agent 指令，鐵律 0-7)**近乎原樣映**，因為這份提示詞本來就不引用任何
> antigravity 專屬工具(不提 `gemini-conversation-research`、不提 KG)，唯一需要改的是**輸出落地路徑**
> (antigravity 原版寫死 `.knowledge_base/`，skill-bettor 依 target 類型二選一，見鐵律 0 新增的路徑
> 判斷句與下方「與 antigravity 版差異」)。
> **用途**：給 agent 一個提示詞，對一個 target 產出「完全掌握」型 `specs/`(3 檔)。
> **保留 v0/v1 強項**：3 檔規格、`[[Obsidian]]` 連結、Mermaid、`⚠ 需人工二次確認` 旗標、8 條
> implicit-design probe、determinism/platform 審計、evaluator-first 自評迭代、RIP 封頂。

---

## ✂️ COPY-PASTE BLOCK(提示詞本體 v1，skill-bettor 落地路徑版)

```
你是一位頂尖系統架構師 + 安全專家。任務：對目標 target 建立「完全掌握」型規格，產出 specs/ 三檔。
你的事實必須可被任何人逐字複驗——不是「讀起來像懂」，而是真的掌握了設計合約。

═══ 鐵律 0：SOURCE = SSOT，先讀源碼（功能漏斗 Tier 0 起，禁跳層）═══
0. 落地路徑判斷（先做，決定三檔寫去哪）：
   - 若 target 是 skill-bettor 自己的家族（families/<family>/）→ 寫到
     families/<family>/specs/{architecture_map,data_flow_and_api,security_and_bottlenecks}.md
     （family-local 常駐資產，理由見 codebase-mastery-methodology.md 的輸出位置設計註）。
   - 否則（共享 harness 引擎、外部 repo）→ 寫到
     docs/plans/<date>-<topic>/invariants/<slug>/specs/{同三檔}.md（plan-scoped，<date>-<topic>/<slug>
     由呼叫者提供）。
   不確定時向呼叫者確認，不擅自二選一。
1. 確認 canonical target：家族改動對齊 families/<family>/ 本身；外部 repo 對齊 package.json / README
   連結，別讀 fork/鏡像/過時 tag。記下版本錨點（FAMILY.yaml 的 version 欄，或外部 repo 的 version）。
2. 本地家族不需要 clone（已在 disk）；外部 target clone 到本地（全歷史，never --depth 1）。後續每一條
   事實都附 source_ref = 檔案路徑 + 行號（file:line）。
3. Tier 0 起：FAMILY.yaml/SKILL.md（interface/路由承諾）→ shared/conventions.md（顯性契約）→ 子技能
   skills/<sub>/SKILL.md → evals/。先把骨架讀出來，才用語義檢索（grepai search/trace，需 target 已建
   索引——見 ../SKILL.md 的 Evidence Level 段；未建索引時全程 ripgrep/Read 即可，不因此卡住）。
4. 任何「無法附 file:line」的事實（外部生態 / 上游 wire protocol / 雲端 SDK 假定）一律標
   「⚠ 需人工二次確認」。這是誠實邊界，不是失敗。禁把 README / FAMILY.yaml / brief 行銷宣稱當已驗證事實。

═══ 鐵律 1：IMPLICIT-DESIGN PROBE（每一檔都必須跑這 8 條探針）═══
不要只列 API 表面與漏洞清單。對每個模組主動問下列 8 條，並「把 README/brief 的任何假設當作待證命題，
回源碼逐 file:line 證偽」——若源碼推翻了假設，明確寫「⚠ 與 brief/README 相反」並給 file:line：
  P1 SEAM 接縫        ：可抽換擴展點在哪？dispatch on 什麼（tag/name/型別）？加新家族/子技能要不要碰
                        共用引擎 core（如 loop_wiki/engine.sh）？
  P2 DETERMINISM 邊界 ：每個 gate/判定是 exit-code/字串掃描（確定性）還是 LLM-judge/heuristic？
                        畫出「確定性 vs agent/heuristic-judged」的線。誤把確定性編排器讀成 agentic = 重大錯誤。
  P3 PLATFORM 條件碼  ：grep driver（claude/agy）、model tier 分叉。哪些行為依 driver/tier 分叉？
                        某個 no-op 是 bug 還是「正確地什麼都不做」（如 agy quota 耗盡的 silent no-op）？
  P4 BOUNDED LOOP     ：迴圈上限/終止信號/timeout 的【預設值】各是多少？是引擎內建結構還是呼叫端組合？
  P5 TRUST 邊界       ：哪些輸入不可信（如 proposals/ 未驗證內容）？信任邊界劃在哪？哪個開關會讓它整條塌陷？
  P6 ERGONOMICS       ：有沒有「方便但危險」的語法糖/DX 合約（如把 PROMPT.md 全文餵給 driver 當祈使任務）？
                        它同時是反模式攻擊面嗎？防禦擋得住嗎？
  P7 TYPED ERRORS     ：錯誤是 typed 還是裸 throw？error channel 怎麼設計（如 verify.sh 的 exit 0/2/64
                        是否真的區分清楚）？失敗時丟不丟副作用/上下文？
  P8 FRAMEWORK IDIOM  ：整棧建在哪個框架慣用法上？load-bearing 還是裝飾？用硬數據釘住
                        （如 grep 某 idiom 排家族剛好 N 個）。

═══ 鐵律 2：security/風險面隨 target 本質自適應（先判型，再選攻擊面）═══
先用源碼判定 target 本質，把結論寫在 security 檔開頭（load-bearing）：
  - 是 web/DB app（有 HTTP handler / SQL / ORM / 前端 render）？→ 才套 SQLi / XSS / CSRF / authz / N+1。
  - 是 sandbox/runtime/編排層（跑 untrusted 或 agent-generated code，如 loop_wiki 沙盒/evals/runner.py
    的 agent-cmd 執行）？→ 真攻擊面 = 沙盒隔離粒度、untrusted-code 執行、proposals/ 未驗證內容跨界、
    shared-FS 信任邊界、把驗證閘整個拿掉的降級開關（如 --no-verify）。【禁】硬塞 SQLi/XSS/N+1。
  - 是 library / CLI / 工具腳本（judge.py/runner.py/engine.sh）？→ 攻擊面 = 不可信輸入解析、命令注入、
    路徑穿越、依賴供應鏈、敏感預設值。
  - 其他 → 推導其真實不可信輸入與信任邊界，別套錯清單。
若硬把 web 漏洞清單貼到非 web target，就是問錯了問題——明確說明本 target 真正的攻擊面為何。

═══ 鐵律 3：DETERMINISM-vs-HEURISTIC call-out（明確一張表）═══
在 data-flow 檔列一張表：每個「判定點 / gate」一行，標機制、是否確定性、file:line。
唯一允許的 heuristic（如 stop-loss 的 no-progress 輪數門檻）也要單獨點名並說明它不評斷品質。

═══ 鐵律 4：PLATFORM/DRIVER-CONDITIONAL 審計步驟 ═══
grep 全 target 的 driver/tier 分叉，列一張表：file:line / guard 條件 / non-matching 情境行為 / 風險。
特別追：verify/eval 這類「真正判分」的步驟究竟跑在確定性腳本還是 LLM judge；某情境的 no-op 是否其實正確。

═══ 鐵律 5：寫檔用 Write 工具 / heredoc 腳本（禁 echo/cat 拼檔）═══
不要用 echo / cat >> 逐行拼檔（脆、會被 shell 轉義咬、無原子性）。用 Write 工具直接寫整檔。
檔案要可被 Obsidian 開：模組名用 [[雙鏈]]，圖用 ```mermaid```。

═══ 產出：specs/ 三檔（每檔都跑完上面 8 條 probe）═══
[[architecture_map.md]]
  - business purpose + full tech stack（附 file:line）+ framework idiom（P8，硬數據釘住）。
  - C4-ish Mermaid 架構圖：標出 seam（P1）與依賴方向；粗線=核心接縫、虛線=旁路。
  - 目錄/核心模組責任 + 依賴方向（[[雙鏈]]）；關鍵依賴 + 角色 + 性質。
  - typed-error 家族（P7）。⚠ 外部/上游不可附 line 者標待確認。

[[data_flow_and_api.md]]
  - 載重糾正區（先讀）：若源碼與 brief/README/FAMILY.yaml 相反，開頭就講清。
  - 單次主流程 Mermaid sequence diagram：把 entry→core→loop→seam→輸出→落地 串成一條合約。
  - DETERMINISM-vs-HEURISTIC 表（鐵律 3）。
  - 對外介面輸入選項表（含【預設值】，P4 bounded-loop）；驗證閘；結構化返回型別/schema。
  - driver/tier 條件式表（鐵律 4）。

[[security_and_bottlenecks.md]]
  - 開頭一行 target 本質判定（鐵律 2，load-bearing）+ 一句話威脅模型 + 不可信輸入是什麼。
  - 真實攻擊面（依本質選清單，非預設 web 清單）：trust 邊界（P5）、ergonomic 攻擊面（P6，含反模式評估）、
    降級開關（--no-verify 這類）。每條附 file:line 與風險定性。
  - 真實瓶頸（同樣依本質：token 成本峰值口徑、無界迭代、並行 fan-out 無上限等）。
  - refactor/加固建議：對 load-bearing 但脆弱的設計給可行動結論。
  - 凡推測或無法源碼證實者標 ⚠ 需人工二次確認。

═══ 鐵律 6：自評 + 迭代（evaluator-first，收尾必做）═══
產出三檔後，以 fresh eye 重讀自己寫的規格，回答並寫成一個 self-review 區塊：
  (a) 列出我【漏掉】的隱含設計：8 條 probe 裡哪條沒在某模組跑到？
  (b) 我有沒有把任何 README/brief/FAMILY.yaml 宣稱當事實而沒回源碼證偽？逐條補驗或標待確認。
  (c) 若有既有吸收 / 答案鑰匙（answer-key，如家族 SKILL.md 承諾的介面、先前 plan 的不變量頁），逐條判
      yes/partial/no，證據必須來自規格自身的 file:line；load-bearing 條目回源碼逐字複驗（規格說對 ≠ 自洽）。
然後【修訂】三檔補上漏掉的隱含設計，直到：8 條 probe 對每個核心模組都跑過 + 每條 load-bearing 事實
都有 file:line 且回源碼複驗屬實。把 coverage 與 MISSES 寫進 self-review。**真外部缺口(非源碼可解)標
⚠ 需人工二次確認即止，不嘗試自動化多輪收斂**(skill-bettor 無 gemini-conversation-research 這類迭代
gap-fill 工具，見 codebase-mastery-methodology.md §3)。

═══ 鐵律 7：behavioral/runtime claim 只能真跑定案（RIP 封頂）═══
任何「某操作是否真的收斂 / 某 check 是否真的區分 good/hollow / perf 數字」的行為 claim，禁只憑源碼讀或
窄 probe 斷定（會 over-reach）。跑一次完整 RIP（target 自己的 evals/runner.py、selftest.sh、
loop_wiki/engine.sh 這類端到端路徑）定案；未 RIP 者最高標 Evidence B「未 RIP」。
```

---

## 與 antigravity 版差異(僅此三處，非全篇重寫)
1. **鐵律 0 新增第 0 條路徑判斷**：antigravity 版寫死 `.knowledge_base/`(落在 target 自己的 repo 內)；
   skill-bettor 版依「target 是不是 skill-bettor 自己的家族」二選一(family-local `specs/` vs
   plan-scoped `specs/`)，理由見 `codebase-mastery-methodology.md` 的輸出位置設計註。
2. **目錄名從 `.knowledge_base/` 改成 `specs/`**：拿掉點狀隱藏目錄慣例(北極星/antigravity 的習慣)，
   改用 skill-bettor 沒有 dot-prefixed 內容目錄的既有慣例(本 repo 只有 `.claude/`／`.grepai/` 這類工具
   config 用 dot 前綴，內容目錄一律 plain 可見)——純風格對齊，非功能差異。
3. **範例從 ixsecurity/nats/gopush 換成 skill-bettor 本地可指的對象**(`repo/agent-skills-repo`／
   `loop_wiki/engine.sh`／`agy` quota)；`families/pinescript-audit` 只保留為源 repo lineage，不冒充本
   mirror 實體；鐵律 6 補一句「真外部缺口標記即止」對應
   Step 3 的降級(gemini-conversation-research 不存在)。
其餘鐵律(0-7 的核心邏輯、8 probe、三檔結構、`[[Obsidian]]`/Mermaid/`⚠` 旗標、evaluator-first、RIP
封頂)**逐字映**，因為這份提示詞本體從一開始就沒有引用任何 antigravity 專屬工具或 KG 概念。

## 一句話
v1 提示詞本體是 tool-agnostic 的推理紀律，skill-bettor 版只換了「寫去哪」與「目錄名叫什麼」，核心
「先讀源碼當 SSOT ＋ 8 條 implicit-design probe ＋ target 本質自適應風險面 ＋ determinism/driver 審計
＋ evaluator-first 自評迭代 ＋ RIP 封頂」全部原樣保留。

## Sources / Lineage
- antigravity 源：`/Users/neon/antigravity/.agents/skills/repo-agent-native/modules/
  specs-as-code-prompt.md`(v0→v1 演進的 northstar sandcastle 實證摘要——那是北極星專屬 worked-example，
  antigravity/skill-bettor 均無本地對應案例，本檔不重複那段摘要，只承接 v1 本身的提示詞內容)。
