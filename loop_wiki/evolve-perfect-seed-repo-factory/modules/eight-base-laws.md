# 八大基座法則對映 — perfect-seed repo factory

> **本檔是什麼**：全局工程法則（skills-shared
> `skills/forgejo-delivery-loop/agent-docs/_global/claude/CLAUDE.md`，§0–§7 按流排列）
> 在本迴圈八大基座上的落點，融合 ix-agy `loop_wiki/invariant-reach-graph` 的
> 抵達分層／settled 判準／推翻落帳方法論。法則原文只住全局檔，本檔不複述——
> 只寫「本迴圈哪個部件承接這條法則」的可觸發形式（訊號→動作→為何有效）。
> 各基座檔的操作契約不被本檔覆寫；衝突時以 `PROMPT.md`／`ROUTES.md` 為準並回報人裁。

## 對映總表

| 全局 §           | base                        | 本迴圈 owner                                     |
| ---------------- | --------------------------- | ------------------------------------------------ |
| §0 契約          | B7 goal contract            | `PROMPT.md`                                      |
| §1 入料          | B1 rules/context            | `AGENTS.md`＋`CLAUDE.md`＋typed packet validate  |
| §2 構形          | B5 specialization           | `src/contracts.ts`＋router＋domain skill         |
| §3 閘門          | B2 settings/authorization   | `run.sh`／`trigger.sh` 單發 dispatch             |
| §4 觀測          | B3 lifecycle/observation    | `_engine-run/` 收據＋`PLAN.md`                   |
| （流上無對應段） | B4 route discovery          | `ROUTES.md`                                      |
| §5 判定          | B6 independent verification | `verify.sh`＋`selftest.sh`＋`portability.sh`＋人 |
| §6 落帳          | B8 state ledger             | `PLAN.md`＋根 `AGENTS.md` 路由列                 |
| §7 邊界          | 橫切                        | 全部                                             |

## 抵達分層 × 本迴圈驗證面（融合 invariant-reach-graph）

一個綠燈值多少，看它由哪種抵達支撐；**三者互不蘊含**：

| 本迴圈驗證面                                                                      | 抵達                        | 證明什麼                 | 不證明什麼                       |
| --------------------------------------------------------------------------------- | --------------------------- | ------------------------ | -------------------------------- |
| required-file 清單、結構 grep、Prettier／typed ESLint／strict tsc（fast receipt） | STATIC                      | 結構存在、靜態缺陷缺席   | 會不會執行、行為對不對           |
| bun 測試（factory＋generated）、`trigger.sh` 實跑、`selftest.sh` hollow 負控      | SANDBOX                     | 合成輸入下會執行且如斷言 | 真實任務、真實 operator 下的行為 |
| `portability.sh`（HEAD 抽出＋乾淨安裝＋雙負控）                                   | SANDBOX（第二份、買獨立性） | 綠不是被本機狀態買到的   | 仍非生產                         |
| Production Use axis（**pending，未接**）                                          | PROD                        | 真的執行過且帶這些值     | ——本迴圈目前缺此抵達             |

**settled 判準**：validated→seed 是 settled 級宣稱，需**至少兩種獨立抵達存活**＋人 admit。
本迴圈 PROD 抵達尚未接線，所以 seed 升級必然停在人閘——這不是流程債，是判準的正確後果。
fast receipt 的 claim boundary（`preflight-only-not-code-quality-axis`）與
「Evidence Level 不是抵達多樣性」同構：STATIC 內部的高分永遠推不動抵達層級。

**獨立性判準**：問「這兩個證據會不會被同一個錯誤同時騙過」。會，就不算兩種。
`verify.sh` 與 `selftest.sh` 共用同一 template＋bun＝同源；`portability.sh` 的負控
（archive 禁 `node_modules`、安裝前必先 fail、拔一檔必 exit 2）就是在買獨立性，
同時證明儀器該紅的時候真的會紅（planted-defect）。

## B1 rules/context（§1 入料）

- 訊號：packet 經中間層（migrate、摘錄、搬運）取回 → 動作：進廠先 validate 形狀，
  refs 走三態（`declared`／`sentinel`／`resolved`），sentinel 永不冒充錨 → 為何：
  壞素材的失敗長得像對方拒絕；wire 上同形的兩態不可讀成其中一態。
- 訊號：想憑名字宣稱「已有等價物」而跳過重建 → 動作：讀碼＋真跑，或重建並列量測 →
  為何：幻覺等價。本迴圈活例：對 plan-truth 母迴圈的 semantic superiority 維持
  `candidate` 待人裁，不憑描述判等價。

## B2 settings/authorization（§3 閘門）

- 訊號：要按下昂貴或不可逆執行 → 動作：先跑自帶便宜驗證面（`sh verify.sh`；
  `portability.sh` 是顯式人／CI 動作）→ 為何：組件作者留驗證面就是讓人在花錢前驗通路。
- 缺席≠否：`trigger.sh` 分記 `build_exit`／`fast_quality_exit`／`operator_exit`／
  `validator_exit`，早段非零→後段標 `not_run`，不偽裝成 fail。
- 成功訊息先斷言再輸出：baseline 用 `cmp` 位元組比對、trend 用行數斷言，成立才 PASS。
- 狀態碼一路傳到底：verify 鏈直跑、不過 tee／tail；一段假 PASS 會扭曲整條路由。

## B3 lifecycle/observation（§4 觀測）

- 綠燈按上表分類抵達；load-bearing 宣稱至少兩種獨立抵達存活才算數。
- 量測工具的綠也是單一抵達的宣稱：hollow 負控＋portability 雙負控＝「該紅時真的會紅」。
- 多態要驗生產端：合法機器狀態 `candidate`／`validated`／`failed`／`human_required`
  各自要有生產碼發射點（hollow control 證明 `failed` 有真生產端）；
  只有測試在構造、沒有生產碼發射的狀態等於不存在。
- 同源判準：`verify.sh` 綠證的是 factory＋此 template；不證 generated repo 在使用者
  真任務下的行為——觀察對象與待證對象不同源時，反證無效。

## B4 route discovery

- 串連時序不可對調：F0→M0→G1→V1→G2→V2→R1→H1；跳過任一 VALIDATE 節點＝
  把靜態推論包裝成已驗證（invariant-reach-graph「②不能省」的同構）。
- failure edge 必須具名（`packet-repair`、`drift-review`……），禁「retry as needed」。

## B5 specialization（§2 構形）

- 每個呼叫端都要記得的事，升級成型別：`src/contracts.ts` 的 typed packet＝
  只能由授權方構造的型別；packet 無 shell-bearing 欄位＝「編譯不過」級的禁止。
- 無聊優於聰明：reduced IR 逐欄明列 entropy removed；20-call 固定數量＝顯式優於隱式。
- 最簡實作：asynchronous axes 誠實標 pending（`modules/production-readiness.md`），
  不用未成熟的複雜性冒充已接線。
- 根目錄 decoupling（模組能自由遷移）：訊號＝想把「在 `loop_wiki/<loop>/` 底下會跑」
  讀成「這個 loop 搬得走」→ 動作＝`sh portability.sh`（`git archive HEAD:$PREFIX` 抽到
  臨時目錄、`bun install --frozen-lockfile`、跑抽出樹自己的 `verify.sh`）→ 為何：
  向上解析的耦合在原地永遠綠。本迴圈的解耦形狀是**可 grep 的具體物**，不是宣稱：
  `PREFIX` 由 `git rev-parse --show-prefix` 解析（不寫死深度）、`bun.lock` 自帶、
  `run_fast_quality.ts` 以顯式相對路徑呼叫 `./node_modules/.bin/*`（無 upward resolution
  可觸發）、`trigger.sh:100` 明寫 standalone tree 無外圍 git 也要能跑。
- 這條的三個負控就是它的可證偽面：archive 不得帶 `node_modules`（帶了則安裝步驟不證事）、
  安裝前 `verify.sh` 必須先紅（不紅則綠不是被 archive 買到的）、拔掉 `tsconfig.json`
  必須拿回 exit 2（否則儀器不會紅）。少任何一個，portability 的綠退回單純宣稱。
- claim boundary 要照抄不得放大：receipt 寫的是
  `relocatability-of-HEAD-only-not-of-the-working-tree`；髒子樹直接 exit 64 拒跑，
  因為那時證的是沒人在看的那個 commit。
- **本條觸發的新推論（pending，未接）**：`portability.sh` 只證**工廠自己**搬得走；
  工廠**產出的 generated repo** 目前只有 `run_generated_fast_quality.ts`（STATIC 面），
  沒有任何抽出＋乾淨安裝的搬移證據——依 §4 同源判準，工廠可搬不蘊含產物可搬，
  而「seed repo 可被使用者搬到自己的 root 底下」正是產品宣稱的一部分。
  訊號＝有人拿 portability 綠替 seed 的可遷移性背書 → 動作＝停在人閘，
  或先補 generated-repo 版的抽出＋乾淨安裝＋負控 → 為何：不同源時反證無效。

## B6 independent verification（§5 判定）

- 靜默推論三形狀，下結論前逐條過：樣本→全稱（n 次觀察不是恆）；同形兩態→單態
  （refs 三態就是不併態的實作）；有回應→機制可用（讓對端自報身分，別靠狀態碼）。
- 卡住紀律：同一問題 3 次實質不同嘗試後 STOP（`PROMPT.md` stop-loss 同構）——
  記錄失敗、質疑抽象層級、換更小的路，然後 SURFACE。
- 換變因＞再解釋：連續兩個假說都在解釋同一失敗、或準備讀第三層碼支持解釋時，
  停止解釋，改「只換一個輸入變因」的對照實驗——它不需要知道正解就能掀掉整疊假說。
- 文件字面與人的目標矛盾：停在矛盾處，攤開取捨給人裁（H1 的 return to named node），
  不得默默退回文件鋪好的那條路——那是靜默換目標，不是盡責。

## B7 goal contract（§0 契約）

- 目標是有界契約：exactly twenty calls、guard metric 打在兩個 public seam 的
  **物理行為**，檔案存在不算數。
- 「Perfect」是優化方向不是機器狀態；合法狀態只有四態。
- 要人執行的事給執行檔＋一行呼叫（`sh verify.sh`、`sh trigger.sh <packet> <output>`），
  不給散文步驟。

## B8 state ledger（§6 落帳）

- 落帳三處，缺一處就斷：全局法則檔（只留判準）→ 根 `AGENTS.md`
  「工程法則的實證歸屬」一列 → 本檔（可觸發實證）。
- 推翻是時間線不是布林：`PLAN.md` 軌跡 append-only；誤判列**必填 note 記
  「當初為什麼會信」**——防重蹈的是那個，不是結論。silent refutation 必須為 0。
- 推翻要回頭改三處：本檔補推翻紀錄、根 `AGENTS.md` 主題列跟著改、
  法則被證偽就回全局檔改寫。

## §7 邊界（橫切）

- Never edit tests、baselines、packet state 只為讓 target 過
  （`--no-verify` 禁令的本迴圈形）。
- 迭代期間禁 commit，收斂後一次提交；commit 訊息解釋為什麼。
- Human admission is the terminal edge——人閘不可讓渡，任何綠燈都推不掉它。
- 共享 working tree 上暫存區是公共狀態——訊號：多 session 同一棵樹，且自己的 commit
  剛被閘門拒絕；動作：先 `git restore --staged <自己的檔>`，再去排查閘門，排完把
  stage 與 commit 綁在同一條命令裡重來；為何：失敗的 commit 不回滾 `git add`，
  留在暫存區的檔會被下一個 session 的 commit 整批帶走。
  2026-08-08 實證：`.claude/hooks/rm_guard.py` 被 pre-commit 閘（`.githooks/` 有未
  stage 改動）擋下後留在暫存區，隨即落進另一個 session 的 8628397（24 檔），內容完好
  但 why 錯配到 loopctl 的訊息。當初以為退出暫存一次就安全——那只擋住當下那一次，
  之後每一次被拒絕都重新開一個窗。

## 來源與同步

- 法則原文：skills-shared `skills/forgejo-delivery-loop/agent-docs/_global/claude/CLAUDE.md`
  （本地 checkout `~/.agents/skills-shared`，remote＝本機 Forgejo `neon/skills-shared`；
  法則變動時本檔對映跟著檢）。
- 抵達分層／推翻落帳方法論：ix-agy
  `loop_wiki/invariant-reach-graph/.agents/skills/invariant-reach-graph/`
  （reach-classes／refutation-history／graph-model；OOBE 案例住那裡，不搬）。
- T0 結構閘：`verify.sh` 斷言本檔存在、八個 `## B` 段俱在、
  settled 判準與 note 紀律未被稀釋。
