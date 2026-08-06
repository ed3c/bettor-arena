# Module: fold-in — know-why

> 屬 [`fold-in`](../SKILL.md) skill。SKILL.md 有確定性程序＋不變量;本檔 = 為何這樣、durable-home
> taxonomy 設計理由、boundary-aware 通則。逐機制 antigravity → skill-bettor retarget 映射表在
> [modules/retarget-map.md](retarget-map.md)(含 upstream northstar lineage 引註,不重抄)。
> 查證方法 → [`external-verify`](../../external-verify/SKILL.md)。

## 1. 為何 fold,不造新(Slop #2 / anti-inflation)

「能力」不是被收集出來的,是被**調用**出來的——不改變 runtime 行為的能力不是能力。每段經驗都新建一個
skill,`.claude/skills/` 這種規模(目前個位數)一樣會迅速漂成**catalog 墳場**:一堆沒人 activate、彼此
重疊、description 互相搶語義觸發的 husk。fold 的默認立場是——**先假設既有 owner 能吸收它**,只有證明
「真有未覆蓋 niche」才由 Claude Code 內建 `write-a-skill` 出閘新建。這把「新建」從隨手動作降級成需要
人核的例外。

判據不是「經驗多不多」而是**grounding**:一段確定性修法 fold 進 owner 的 changelog/Gotchas/references,
是全顆粒度推進(demand-scoped ✅);造個空殼 skill 把散文塞進去等它被 surface,是 supply-push 增殖(❌)。

這正是「anti-inflation 是判準,不是字面禁令」的具體操作化——判準是「候選是不是真未覆蓋的 niche」,不是
「規模小所以先別加」或「規模大所以隨便加」。skill-bettor 現在規模小、增長快(每日演化管線持續產出新
教訓),更需要這條紀律從第一天就上緊,而不是等 catalog 膨脹了才追悔。

## 2. Layer A/B 為何分

Claude Code 的漸進載入與 antigravity 的 `.agents/skills` 機制同構:skill 的 frontmatter
(`name`/`description`)被索引供語義選取,body ＋ `modules/` 在該 skill 被選中前**不載入**。所以:

- **Layer A(SKILL.md / changelog 條目 / Gotchas 行 / 組件卡列)= 確定性事實／程序／處置**:被載入時
  要能立刻照著做,不夾雜長篇 rationale。胖 SKILL.md = 每次 activate 都付 know-why 的 token,且淹沒
  可執行程序。
- **Layer B(modules/ 或家族 `references/`)= know-why**:為何這樣修、根因論證、取代史 —— 只在真要
  理解時才 lazy-load。

這與 `loop-harness-standard`、`harness-wiki` 的 dogfood 一致(SKILL slim ＋ `modules/` 拆分,同批
移植已示範;`loop-harness-standard` 甚至把 evals 設計法整份下放 `modules/evals-design-method.md`
而非塞進 SKILL.md 正文)。

## 3. durable home 非 ephemeral —— 為何逼「畢業」,以及四路 taxonomy 怎麼設計出來的

對話(以及隨手筆記)是**ephemeral**:下個 session 不保證載入,load-bearing 的操作課會**蒸發**。
antigravity 有一個集中式 durable home ——root `AGENTS.md`「Resolved」帳本,一個檔案裝所有範疇的
「症狀＋根因＋修法＋禁回退鐵錨」。**skill-bettor 沒有這個檔案,也不該造一個同構的**——理由不是
偷懶,是 skill-bettor 的結構本來就比 antigravity 更分艙:

- antigravity 是單一大迴圈(一條 DR 管線)套多個 stage-skill,經驗的「範疇」大多數時候就是「該
  stage」,集中式帳本尚可 scale。
- skill-bettor 是**多家族×多迴圈**的資產工場:一段教訓的正確歸屬,取決於它是屬於**哪個家族的業務
  資產**、還是**跨家族的迴圈引擎本身**、還是**迴圈之間怎麼組合**、還是**repo 級的政策**——四個維度
  互不隸屬,硬塞進一個檔案會讓 家族A的 eval 教訓、harness 引擎教訓、迴圈拓撲事實、repo 政策決策
  混在同一列表,任何人想找「某類教訓在哪」都要線性掃過整檔——這正是 antigravity 自己在
  `AGENTS.md` 規模變大後可能面對的問題,skill-bettor 從結構上先避開。

由此推出的四路 taxonomy(範疇 → durable home,详見 SKILL.md §程序 1/4):

| 範疇 | Durable home | 為何是這裡 |
|---|---|---|
| 單一家族的行為/eval 教訓 | `families/<family>/changelog/` | changelog 本來就是「每日加了什麼/刪了什麼/分數變化」的日誌,已有真實條目格式(見 `pinescript-audit/changelog/2026-07-11.md`「做了什麼／改了什麼(diff)／已知問題」三段式),只需在其中補一條顯式「已解:X。禁回退用 Y。」錨句,不需另建新檔案。 |
| 該家族某子技能的領域知識修正 | 子技能 `SKILL.md`(事實)+`references/`(why) | 子技能本身已是最貼近「owner skill」的單位(如 `repaint-detection`),`references/security-function-patterns.md` 已是現成的 Layer B 範例。家族頂層路由器 SKILL.md 明文「只放地圖不放知識」,故教訓不進那裡,進子技能自己的層。 |
| 跨家族 harness 工程教訓 | `loop-harness-standard` 自己的 Gotchas/modules | 這正是它現在已有的用法——`agy quota 耗盡＝零輸出 exit 0`、`agy --add-dir 命門`都已是這個 skill 的 Gotchas 行,是跨任何家族都適用的驅動器層級事實。這條路是唯一「Layer A 本身就是防回退錨」的一路,因為它不像 changelog 那樣有「哪一天的條目」概念,是持續累積的 Gotchas 清單。 |
| 迴圈拓撲事實變動 | `harness-wiki` 組件卡＋不變量清單 | harness-wiki 明文鐵律「只 MAP 不放內容」——這裡放的不是「教訓」而是「地圖跟真實系統同步」,錨不是「禁回退用 X」句式,而是「組件卡描述與磁碟上的真實迴圈狀態一致」本身。誤把教訓塞進這裡 = 讓地圖開始帶散文,是 harness-wiki 自己 Gotchas 點名的頭號風險。 |
| repo 級跨切面架構決策 | `ARCHITECTURE.md` §10(遷移步驟)+§11(為何不) | §11 的標題本身已寫明「鏡像 antigravity §⑦」——即 skill-bettor 設計者已經在建 `ARCHITECTURE.md` 時,獨立長出了一個「為何不做 X」清單,功能上正是 repo 級範疇的防回退鏡像句式(只是措辭從「禁回退用」換成「不 X」)。fold-in 不需要為這一路發明新格式,只需要把新決策 additive 接進這兩節既有結構。 |

這張表不是憑空設計——是先讀了 `ARCHITECTURE.md`、`loop-harness-standard`/`harness-wiki` 現況、
`pinescript-audit` 家族實際目錄形狀之後,**找出已經存在的四個「被固定查看的地方」**,再把它們的
既有格式各自補上一句顯式防回退錨。唯一真正「設計」的部分,是決定教訓依什麼規則路由到這四路之一
(範疇:家族內容 / 家族過程 / 跨家族引擎 / 跨迴圈拓撲 / repo 政策),而不是發明新檔案。

## 4. discrimination gate —— 為何要 `evals/runner.py` 或 `engine.sh` 鐵錨(否則 husk)

吸收一段「修法」最容易的自欺:把散文(「已優化 eval 穩定性」「改善了偵測」)寫進 changelog 或 Gotchas,
但對應的程式碼裡根本沒有實現,或實現了但沒有可回退偵測的鐵錨。這是 Half-Bridge —— 讀起來平滑,實際
不可宣稱成立。

skill-bettor 的確定性鐵錨,依範疇分兩種 load-bearing 檔案:

1. **家族範疇**:該修法真的在該家族 `evals/runner.py`(或 `judge.py`、`scan_*.py` 掃描腳本、
   `expect.yaml` 案例定義)落地。例——修好 `evals/runner.py` 裡 `parse_agent_output` 的 token 累加
   口徑(pinescript-audit changelog 已知問題 #1:累加跨迭代 cache_read 導致「多思考」被誤判為
   「skill 膨脹」)—— 這類 bugfix 才夠格吸收;若只是在 changelog 寫「token 口徑已改善」但
   `runner.py` 裡的計算邏輯沒動,就是 husk。
2. **跨家族 harness 範疇**:該修法真的在 `loop_wiki/engine.sh` 或 `loop_wiki/_template/` 落地。
   例——修好 `engine.sh` 裡一個會讓 stop-loss 計數器漏算的 Goodhart-checker 漏洞(checker 分不出
   good/hollow 卻仍判過)—— 這類修法要能指向 `engine.sh` 裡具體改動的函式/行為,而非只描述「引擎
   更穩了」。
3. **純操作性教訓(無程式碼變動)**:如「DR proposal 迴圈裡 agy 額度耗盡時輸出檔案為空但 exit code
   為 0(silent no-op)」—— 這類教訓沒有「修法」可指(沒有 bug 要修,是驅動器行為事實),鐵錨換成
   **可重現的實測觀察**(真的跑過一次、看過真實輸出檔為空＋exit 0 的組合),且必須落進一個真檔案
   (`loop-harness-standard` 的 Gotchas 行),不能只停留在對話裡口頭轉述。

有這些鐵錨,「吸收成立」才有判別力(一個「連接但不判別」的假吸收 —— 光有散文沒有對應實現或實測
—— 會被鐵錨抓出)。無鐵錨 → gate 擋下,退回,別存 husk。

## 5. port 命門(antigravity → skill-bettor 這一手)

antigravity `fold-in` 本身是 port 自 northstar `/fold-in`(Claude Code 斜線命令
`.claude/commands/fold-in.md`,DDR-205 Layer A/B、Slop #2、PG-103/155/156)。那一手的完整
northstar→antigravity 逐機制映射表記在 antigravity 自己的
`.agents/skills/fold-in/modules/fold-in-know-why.md` §5——那是**第三手參照**,本檔不重抄它,只在
[modules/retarget-map.md](retarget-map.md)引註為 upstream lineage。本檔與 retarget-map.md 只負責
**antigravity → skill-bettor** 這一手的映射,新鮮寫出、不假設讀者看過 northstar 那份。

## 6. 為何 fold-in 要 boundary-aware(掌握系統邊界)＋ 技術等價物判斷通則

fold-in 早期世界觀是「把經驗塞進一組**扁平的 N 個 skill**」。但 skill-bettor 的知識演化 harness 已經
是**小迴圈組件的組合**(見 [`harness-wiki`](../../harness-wiki/SKILL.md)):演化 op 迴圈、DR proposal
迴圈,各自閉合、各有獨立收斂閘,未來會 additive 增列。這對 fold-in 有兩個硬後果:

1. **系統邊界是活的,不是硬數字**。harness-wiki 現在誠實地只列 2 條迴圈——但「只有 2 條」本身會
   隨時間變(D5 一旦把 DR proposal 迴圈沙盒化實跑、或新家族長出新的 op 類型,就會變 3、4 條)。
   若 fold-in 把 owner 候選寫死成「family changelog 或 loop-harness-standard 二選一」,下次新迴圈
   類型出現時就會結構性看不見它當 owner 候選。修法不是把數字寫死改成「3」(下次又 stale),而是
   **讓 owner 候選源＝讀 harness-wiki 組件卡**——它本就是「系統邊界的單一真相」。fold-in 每次先讀
   它,才叫「掌握系統邊界」。

   antigravity 的 `antigravity-harness-wiki` 已經踩過這個坑一次:曾把一個真迴圈(DS 分析工作流)
   誤判為「只是 domain 內容」打掉,後來才更正為正式迴圈組件 `ds-workflow-loop`——這是**antigravity
   自己的歷史案例**,skill-bettor 才剛起步(2026-07-11 首日),還沒有對應的真實負向錨。這裡引用
   antigravity 的案例只為**校準風險意識**,不是宣稱 skill-bettor 已經犯過同樣的錯——若哪天
   skill-bettor 真的發生「把一條真迴圈誤判成 domain 內容打掉」,那時才該把具體案例記進
   `harness-wiki` 自己的 Gotchas,而非現在虛構一個。

2. **fold-in 是最主要的變異操作,所以是最大漂移源**。harness-wiki 存在的唯一理由＝防雙圖漂移
   (改某迴圈時閉環／不變量／資料流被誤改誤簡化)。而 fold-in 正是那個「改某迴圈相關結構」的操作。
   若 fold 動了某迴圈的閘／資料流歸屬／不變量／SSOT 指針卻沒回同步 harness-wiki,那張**防漂移的
   地圖自己先漂**——最諷刺的 husk。故不變量 6 逼「fold 完回核組件卡＋不變量清單」,且**只改指針
   永不抄內容**(抄＝製造會漂的第二份,正是 harness-wiki 自己 Gotchas 點名的頭號風險)。方向是
   單向的:fold-in 這端「知道去同步」harness-wiki;harness-wiki 那端的反向紀律(「改某迴圈後回核
   本圖」)本就在它自己的 Gotchas——兩端咬合,不重複承載。

**技術等價物判斷(retarget 的通則化)**:判斷「一段機制能不能從一個系統映到另一個系統」的通用判別
閘是:對照**目標平台/目標範疇真實基座**判——(a) 有 1:1 技術等價物 → 映;(b) 無對應基座 → 誠實拿掉
並記錄,**絕不留半橋**(引用不存在基座的散文＝死 husk)。反身版就是不變量 6 的反-husk 錨:fold-in
指向的 SSOT(如 harness-wiki、如某家族 changelog)**必須是真檔案**——指向 phantom 基座＝自己造
husk。這把「evals/runner.py 或 engine.sh 鐵錨」(§4,行為類 fold 用)與「指向真基座」(方法論／路由類
fold 用)統一成同一條 discrimination:**吸收成立 ⟺ 錨在真實基座上**,只是行為類的基座是程式碼
＋durable home 錨句,方法論類的基座是被指向的真 SSOT 檔案。

## 7. routing 閉環(2026-07-12 增補:雙側路由+迴圈 owner 路+機械化升級閾值)

**為何補「producer 側」這一路**:2026-07-11/12 四題 DR 實跑後的 fold 全走了 orchestrator 側
(skill Gotchas/modules)——但沙盒紀律要求 driver 開工先讀 anti/,而 template anti/ 一直是空的:
同一批教訓,學乖的只有派工的人,犯錯的作者一無所知。原四路 taxonomy 的盲點在只有「範疇」軸、
沒有「受眾」軸——每段教訓要問兩個問題:①屬哪個範疇(選哪路 durable home)②**誰需要在行為上
改變**(orchestrator → owner skill;producer → template `anti/`,cp -r 即傳播到每個新沙盒)。
兩側都該收到的就雙落(Layer A 一行+anti 檔,內容不重抄,各寫各的受眾視角)。

**為何「迴圈專屬教訓」獨立成路**:原 taxonomy 把迴圈教訓歸「跨家族 harness → loop-harness-standard」
——單迴圈時代成立;第二條迴圈(DR)落地後,單條迴圈的專屬教訓(agy 失敗模式諸型、feedback 輪
直發機制)塞進通則 skill=汙染通則、且該迴圈的使用者找不到。harness-wiki 組件卡的「擁有者 SSOT」
欄本來就是現成路由表——照欄路由,新迴圈落地即自動有家,routing 隨組件卡 additive 增長而閉環。

**為何機械化升級閾值=「重複 ≥2 例 或 單例 Goodhart 逃逸級」**:單例就機械化=為噪音加閘
(驗證器經濟學:每個 checker 都有假陽性維護成本+fixtures 負擔);但「騙過既有機械閘的結構性
漏洞」(如字面 SPDX 謊標恰好轉成 allowlist 字串)不能等第二次——它證明的是閘的盲區而非事件
噪音,L3 因此在單題(兩例)後即升。裸根域錨三題重複、每次都要 D3 人力抓=典型該升未升的
存量候選。升級永遠=改判定式:人核+good/hollow fixtures 鎖回歸,承 L3 先例(04b5c06)。

## 8. 計劃執行進度路(2026-07-19 增補:為何閘同位、為何不建中央狀態檔)

**場景**:多階段計劃(如 dr-to-mvp R→G→M)跑完某 Phase 後,計劃文件與現實脫節——「計劃寫著待辦,
資產其實已畢業」。這段經驗來自 2026-07-19 aie-context-pack 全鏈實跑(7 源萃取→辯論→T2→R5/G4/M5
三閘→畢業 homing),當天 fold 回計劃時定型的方法論。

**為何進度事實與閘同位、不建中央 STATUS 檔**:與 harness-wiki「只 MAP 不放內容」同一個論證的
反身版——計劃檔的 ▣ checklist 本來就是閘的宣告位,進度是「閘被人 admit 過了」這個事實,寫回閘旁
=單一位置;另開中央進度總表=同一事實兩處登記,fold-in 自己反覆證明過雙帳必漂(誰忘了同步誰漂)。
40 §D3.1 那張逐任務一覽看似例外,實際是 40 自己的閘位(它是派工規格檔,進度=它的規格被執行的
狀態),仍是同位不是中央。

**為何勾選格式=打勾＋日期＋一句錨**:勾=人 admit 過的二值狀態(不是 producer 自報);日期=
additive 審計軌(哪天過的閘);錨=指真檔的證據指針(判官報告/verify 輸出/派工帳),敘事不算。
三件缺一即回到 Half-Bridge:無錨的勾=「自稱完成」,正是整套驗證紀律要防的東西。

**為何逐派工 provenance 另落 dispatches/round-NN.md**:per-dispatch 帳(原定 tier vs 實際/真跑
log/fallback 原因)高頻且冗長,直接寫進計劃檔會把任務骨架淹掉(被動上下文膨脹傷注意力);計劃檔
持一個指針,細帳集中輪次檔——高頻細節與低頻骨架分離,同 Layer A/B 分層的粒度論證。

**為何未完成項要寫「為何待」**:`- [ ]` 光禿禿留著,三週後沒人記得它是「刻意等外部錨」(如
mcp-serve 等 7/28 final)還是「漏做」——一句 why 讓 designed-wait 與 negligence 可區分,同
DESIGN-SCORE 的 designed-cut 論證。

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/fold-in/`(SKILL.md +
  `modules/fold-in-know-why.md`)。
- northstar 源(第三手,不重抄):antigravity `modules/fold-in-know-why.md` §5 記錄的
  northstar→antigravity 映射,原始出處 `/Users/neon/northstar/.claude/commands/fold-in.md`
  (DDR-205、PG-103/155/156)。
- skill-bettor 既有同構:`ARCHITECTURE.md`、`loop-harness-standard`/`harness-wiki`(同批移植)、
  `families/pinescript-audit/changelog/2026-07-11.md`(四路 taxonomy 的實例依據)。
