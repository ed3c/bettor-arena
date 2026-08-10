# loop_wiki — 小迴圈的法則與 Harness

> 這是給**下一個讀 loop_wiki 的 agent** 的系統提示詞。先讀 §1 法則，動手前跑 §2 的閘。
> 實例、真的抓到過的缺陷、邊界全在 §3 Harness，**不要把實例往前搬進法則**。
> 每個迴圈自己的讀取順序在它的 `AGENTS.md`；證明與對照組的設計法則在 `proof_workflow/README.md`。

`loop_wiki/` 是小迴圈的家。目前住著 `evolve-perfect-seed-repo-factory`。
下面的法則對**任何**放進來的迴圈都成立，不是那一個的特例。

## §1 法則

1. **判斷住在型別層，shell 只轉述。** `contracts.ts` 決定 sentinel／resolution，`trigger.sh`
   只中繼 CLI 吐出的 JSON。**shell 一旦自己再判一次，就有了第二個真相來源。**
2. **每個狀態都要有具名出口與具體修法。** `refs_status` 是 `declared|sentinel|resolved|stale`，
   `stale` 的訊息直接寫出「重跑 resolve-refs --peer，或移除過期收據改以 declared 交付」。
   **不認得的值一律 FAIL，不當成 pass。**
3. **輸出路徑必須是新的。** 絕對路徑、無不安全字元、**已存在就拒絕**。覆蓋一個既有輸出，
   會讓「這次產生的」與「上次殘留的」永遠分不開。
4. **迴圈不自我修復。** `run.sh` 是一次性分派、不含迭代邏輯；封包或建置失敗**浮到呼叫端**由人或
   程式修，不叫 LLM 自我修復、自我admit。
5. **產物的擁有權往下切乾淨。** 巨迴圈擁有編排與人工admit；本迴圈擁有一個封包的驗證、IR、
   材料化、路由結果與失敗面；**產生出來的 repo 擁有它自己的 operator skill 與資料，
   不擁有工廠的治理**。
6. **模組不向上依賴根目錄。** 樣板自帶鎖檔與驗證面（`templates/repo/bun.lock`），
   判準是**搬一次真跑**：抽到別處、裝自己的鎖檔、跑自己的驗證面。**向上解析的耦合在原地永遠綠。**
7. **綠燈值多少看它由哪種抵達支撐。** STATIC（型別／lint）只證「可能」、SANDBOX（測試）證
   「在合成輸入下會執行」、PROD（真跑）證「真的帶這些值執行過」——**三者互不蘊含**。
8. **per-run 產物不入證明的雜湊。** `_engine-run/` 裡的東西是**上一次執行的事實**，不是迴圈的事實；
   它嵌了那次的輸出路徑、每跑每變。用**欄位斷言**覆蓋它，並把帳本具名排除。
9. **對照實驗只准動一個變因。** 共用輸出目錄會讓「每個輸入都必要」這種結論憑空長出來——
   那是路徑衝突，不是依賴關係。

## §2 動手前後的閘（依序）

```sh
cd loop_wiki/evolve-perfect-seed-repo-factory
sh verify.sh                 # 靜態面：lineage / 格式 / lint / type 收據
sh selftest.sh               # 真建一個 repo、真跑它的 plan、再植入一個缺陷要求它紅
sh portability.sh            # 搬移：抽出去也要能跑
sh trigger.sh packets/inbox/dr-example.json /absolute/new/path
sh loopctl/loopctl.sh micro test        # （回到 arena 根）入口對照組
```

**訊號 → 動作**

| 看到 | 先做這件事 |
|---|---|
| `output already exists` | **不要刪了重跑。** 換一個新路徑——舊輸出是上一次的證據 |
| `refs_status=stale` | 收據與封包對不上。照訊息二選一，**不要把 stale 當 declared 用** |
| micro 的 digest 兩次不同 | 找那個**每跑每變**的檔（多半是嵌了 mktemp 路徑的 fixture），改判 HEAD 或具名排除 |
| 所有輸入都被判成 required | 探針共用了輸出目錄（法則 9）。每次 run 給獨立輸出，並前後各驗一次可重現 |
| 只有 lint 綠就想收工 | 那是 STATIC 一種抵達。load-bearing 的不變量要**兩種獨立抵達**存活（法則 7） |

**收尾**：改動 → 回 arena 根重蓋收據 → `workflow lock` → 一條命令內 `git add` ＋ `commit`。

## §3 Harness

### 已實作的機制（改動前先認得它們）

| 檔 | 它保證什麼 |
|---|---|
| `trigger.sh` | 入口：驗封包 → 驗輸出路徑 → refs-status → 產生交換脈絡 → 引擎執行 |
| `src/cli.ts` / `src/contracts.ts` | 型別化的判斷面；`validateOutputPath` 三道拒絕（非絕對／不安全字元／已存在） |
| `verify.sh` / `selftest.sh` / `portability.sh` | 三種抵達：靜態收據、真建真跑並植入一次缺陷、搬出去再跑 |
| `src/verify_generated_repo.ts` | 產生出來的 repo 自己的驗證面，與工廠的分開 |
| `baselines/seed-stats.json` ＋ `record_trend.ts` | 基線與趨勢閘；drift 走 `drift-review` 邊 |
| `ROUTES.md` | 每個節點的 actor／validator／pass 邊／**失敗邊**——失敗邊具名才修得動 |
| `modules/eight-base-laws.md` | 全局法則落在八個基座的哪一格，以及 STATIC/SANDBOX/PROD 分類 |
| `packets/inbox/*.json` | 真封包，不是玩具；`legacy-dr-example.json` 保住舊格式的遷移路徑 |

### 真的抓到過的缺陷（形似訊號時先查這裡）

| 症狀 | 真因 |
|---|---|
| 兩次一模一樣的執行、digest 不同 | `verify.sh` 的測試改寫 `route-result.fixture-dr.json`，而它的 `output` 欄是**每次新的 mktemp 路徑** → tracked artifact 改判 HEAD ＋ 該檔具名排除 |
| 迭代 lane 覆蓋錯兩次 | 先去 hash 一個 gitignored 的實例（不可重放、位元組還含執行路徑）→ 改成**欄位斷言** ＋ 帳本具名排除 |
| 七個輸入全被判成 required、exit 全一樣 | 探針共用輸出目錄，`cli.ts` 拒絕已存在路徑 → **那是路徑衝突不是依賴**。每次 run 獨立輸出 ＋ 基線前後各驗一次 |
| grep 明明有的欄位卻報缺失 | 欄位名以 `- ` 開頭被當成選項 → `grep -Fq -e` |
| worker 以降級狀態默默跑完 | 應該 re-exec 而不是繼續——**降級不可以是靜默的**（同類見 `kb-ingest/README.md`） |

### 邊界（刻意不做的）

- **`_engine-run/` 不入雜湊**（法則 8）：它是上一次執行的事實。覆蓋它的是欄位斷言，
  而它的產生者（`trigger.sh`）本身是被雜湊的。
- **工廠不決定產生出來的 repo 該怎麼治理**（法則 5）。
- **不叫 LLM 自我修復**（法則 4）：合法的機器狀態只有 candidate / validated / failed /
  human-required，「完美」是最佳化目標不是狀態。
- **`micro test` 的分類不跑概率性段落**：每跑每變的輸出會讓分類失去意義。
