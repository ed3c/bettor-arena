# Module: repo-agent-native — 抽取方法論 know-why(S2.5 破盒推論／OPBE／Evidence Level)

> 屬 [`repo-agent-native`](../SKILL.md)。Layer B：SKILL.md 只留確定性程序＋pointer，深度推理框架寫這裡
> (progressive loading，被選中前不載)。**本檔內容近乎原樣映自 antigravity 版同名檔**——這是一套與 KG／
> 索引平台無關的推理紀律，skill-bettor 沒有理由改寫核心邏輯，只調整少數點名了 antigravity 專屬 sink 層
> 的措辭(見文末異動說明)。

## Evidence Level 為何這樣分(污染傳播直覺)

原理：一個事實的**證據來源**決定它能不能被下游當事實傳播。A→A 安全；D→any 高風險(用一個沒源碼支撐的
猜測去推別的結論＝幻覺鏈)。skill-bettor 無機器污染矩陣，但**直覺不變**：抽取時每步問「這是我讀到的(A)、
追蹤到的(A-)、語義命中的(B+)、還是我在猜(C/D)」。GrepAI/Serena 只是候選與加速器：
實測過的 trace 也可能漏 reference，必須以 `rg`、compiler/LSP workspace 範圍與源碼 body 交叉核對。
C/D 進頁面只能標 `inferred`／`unverified`，不能寫成 `INV-xxx [A]`。語義搜尋空結果
不能證明 absence。這就是 `source_ref` 鐵律的認識論理由——沒有 `檔案路徑:行號`，你不知道自己在傳播事實
還是幻覺。

## S2.5 破盒推論五步(完整框架)

觸發：S2 Pass 4 的 `outgoing-calls` 出現 `indexed: false` 的 callee，或某行為無法從已讀源碼解釋。核心
原則：**你讀了 A 的源碼，但 A 呼叫了 B；B 的行為／前提／失效模式是 A 的「隱含依賴」，不在 A 的源碼裡。
破盒推論＝主動從已知事實推導它們。**

1. **未索引服務識別**：對每個 `indexed:false` callee 分類——`INTERNAL_SERVICE`(同生態另一 repo/家族，
   可再索引→排下輪 S1)／`EXTERNAL_INFRA`(檔案系統、外部 API、CLI 工具如 `claude`/`agy`，不可索引→用
   協議/介面規格推論)／`AMBIGUOUS`(需讀更多源碼)。
2. **共享狀態耦合偵測**：關鍵問「這段程式讀了什麼資料？誰寫的？」——找 **read** 而非 write(如某家族
   `runner.py` 讀 `evals/baselines/<date>.json`，誰在什麼時機寫入這份 baseline？)。輸出 `coupling`：
   store／writer(檔案+fn+Evidence)／reader(檔案+欄位+Evidence)／`temporal_constraint`(如「eval 跑完才
   有 baseline，第一次跑沒有可比對象」)／`failure_mode`(如讀到過期 baseline → 誤報 regression)。
   - **routing 子模式**：某個 config/參數值決定走哪條分支、讀哪份資料 → 不同值 → 完全不同行為。標
     `IMPL-ROUTE-xxx`，未查清楚前 Evidence=C。
3. **靜默失敗鏈推導**：對每個 fire-and-forget／背景執行的呼叫問三題——Q1 呼叫者收到的成功訊號是否代表
   端對端成功(如 `agy` exit 0 但 quota 耗盡＝零輸出的 silent no-op，已知 skill-bettor 記憶案例)？Q2
   若靜默失敗，哪個 timeout／檢查點先觸發？Q3 該失敗可觀測嗎(log/exit code/輸出檔存在性)？
4. **逾時鏈推導**：每個 timeout／stop-loss 常數的值由什麼外部條件隱性決定？寫 `implicit_bound`(如
   `loop_wiki/engine.sh` 的 `no-progress=2 輪`／`exhausted=$MAX_ITERS` 這類門檻，是否被呼叫端假設過)。
5. **循環依賴檢查**：「函數庫在 A，但執行路徑從 B 觸發」→ 可能 B→A 呼叫／A 是共用 shared 原語(code reuse
   非 runtime dep)。讀觸發點源碼定案。

每條隱含依賴：`id`／`type`／`callee`／`known_facts`(帶 Evidence)／`inferred_prerequisites`／
`silent_failure_chain`／`resolution_status`(UNRESOLVED 需索引 callee 才升 CONFIRMED)。

## OPBE(Optional Param Branch Exhaustion) — 為何 Pass 3 不夠

教訓(繼承自上游 lineage 的通用 bug pattern，非 skill-bettor 本地案例，仍具參考價值)：函數/CLI 的每個
optional 參數都可能是 routing key，觸發完全不同代碼路徑／檔案讀寫／驗證邏輯。只讀 entry point＋required
params＝漏掉成功／失敗分支。

OPBE 三步：①ripgrep 列**所有** optional 參數(CLI flags／函數簽章預設值／config 欄位)；②ripgrep 所有
`if/switch`對這些參數的判斷；③追某參數到下游(如 `runner.py --skill <sub>` 的 `<sub>` 如何決定要載入
哪個家族子技能)。輸出每個 routing 參數的 value → {行為分支、下游依賴、Evidence、source_ref}。

**四個盲點(繼承教訓，防護內建)**：

| 盲點 | 根因 | 防護 |
|------|------|------|
| 只讀失敗路徑 | 從錯誤往上找，未從 entry point 往下枚舉全部分支 | OPBE 強制枚舉 |
| optional 參數被忽略 | 假設「主要參數」就是完整 spec | 讀簽章/CLI parser 列 ALL params |
| 常數未關聯呼叫點 | 常數定義在檔頂/另一檔，不在使用處附近 | 檔頂/import 常數掃描 |
| routing 不可見 | 某參數決定的下游行為差異讀不出 | 標 `IMPL-ROUTE-xxx`，Evidence=C 直到查清楚 |

## 8 條 implicit-design probe(Codebase Design Mastery，推理紀律)

對「完全掌握」型抽取，除了不變量還問 8 個設計決策問題(⟂ S2.5 的隱含**依賴**，這 8 條問**設計決策**)：
seam(邊界在哪)／determinism(哪裡確定性、哪裡機率)／platform(平台假設)／bounded-loop(迴圈有界嗎)／
trust(信任邊界)／ergonomics(誰用、怎麼用)／typed-errors(錯誤型別化嗎)／framework-idiom(沿用框架慣例嗎)。
每個答案同樣要 `source_ref`。

**雙重 Evidence-Level 教訓(gotcha)**：單次觀察能 **OBSERVE** 失敗，但**不足以 ATTRIBUTE** root-cause
——歸因要回源碼。而 behavior/perf claim 連源碼讀＋窄 probe 都會 over-reach——這類要**完整真跑(RIP)**
才定案(如：某 op 是否真的收斂、`verify.sh` 的某個 exit code 是否真的對應宣稱的失敗原因，光讀腳本推論
會漏掉環境相依的實際行為)。鐵律：歸因要回源碼；behavior/perf 要真跑，別靠靜態讀腦補。

## Empty-Output 為何 fail-loud

`invariants: []` 空殼靜默寫進計劃目錄＝silent Half-Bridge，下游(如讀 `00-intent-and-knowhow.md` 的人
或後續 gate)把「沒抽到」誤讀成「沒有不變量」。防護：0 產出時**必**寫 `extraction_failure_reason`，
SURFACE 標 `EMPTY_FAILED`。這是 Path B 紀律的實例——沒有確定性鐵錨(至少 1 個帶 `source_ref` 的不變量)
就不可宣稱抽取成立。

---

## 異動說明(對照 antigravity 版的差異，非重新論證全文)
本檔內容 99% 原樣映自 antigravity `.agents/skills/repo-agent-native/modules/extraction-methodology.md`
——推理框架本身與 KG／索引平台無關。僅有的改動：①拿掉「repo-fullstack-debugger 也重用它」一句(該
skill 在 skill-bettor 不存在，見 `../SKILL.md` Not For 段)；②範例從 ixsecurity/pubsub/gopush 換成
skill-bettor 本地可指的對象(`runner.py`／`engine.sh`／`agy` quota)，方法論本身不變；③OPBE 的「北極星
blackhorse login post-mortem」具體命名拿掉，改註記「繼承教訓、非本地案例」，避免讀者誤以為是
skill-bettor 自己發生過的事故。
