# notebooklm — 抖動偵測的法則與 Harness

> **讀到這個目錄的 agent：先讀完 §1 法則，再照 §2 的迴圈做事。**§3 Harness 是已實作的機制
> 與它們真的抓到過的缺陷——遇到形似的訊號時查那一節，不要重新發明。
> 法則層只留判準，實例一律住 §3。表面在 `loopctl/contract.json`，程序在
> `.agents/skills/notebooklm-workflow/`，本檔都不複述。

## §1 法則

1. **present ／ authenticated ／ authorized 是三態，不是兩態。** binary 在 ≠ cookie 還能認證
   ≠ 那份文件拿得到。三種修法各不相同（裝套件／`auth refresh`／請人分享），所以三個具名出口，
   而且**缺席永不讀成綠**——`64` 是工具不在，`2` 是判定為否。

2. **匿名抓取拿不到的東西，換旗標救不了。** 判準是 **401 與 404 的差別**：401 是「存在但被閘住」，
   404 是「不在」。看到 401 就別再調 URL 形狀，去找**認證過的那條路**（這裡是 Drive file id）。

3. **上游的 `--json` 只在你給完整 id 時是純 JSON。** 部分 id 會讓它先印一行人類訊息。所以先解析成
   完整 UUID **再**呼叫，而且解析後**仍然斷言純度**——只被看過同意的修復，不等於已知它會不同意。

4. **讀取不得改變被讀物。** 寫只准寫進自己新建的丟棄式 scratch，刪除走 `finally`（失敗、逾時、
   中斷都要帶走它）。來源 notebook 永遠唯讀。

5. **空集合與任何東西相等。** 每個推導在決定任何事之前先斷言非空；空的要有自己的具名狀態，
   不能當成「沒事可做」往下流。

6. **一條連結壞掉 ≠ 機制壞掉。** 依序試到第一個開得了為止，被拒的理由**全部留在收據裡**——
   單試一條會把前者講成後者，而那是兩件事。

7. **每趟都變的位元組不進 digest。** per-run 目錄與他人文件內容一律 `prove_note` 具名排除，
   收據只留 sha256 與計數。進了 digest，追蹤的就變成「上次跑在哪」而不是「機制是什麼」。

8. **registry 的 id 是 PIN，不是捷徑。** 標題仍要對活帳號解析一次，不合就 exit 2。
   悄悄贏的陳舊 pin 會用對的名字收到錯的 notebook。

9. **植入缺陷測不出「機制被整條換掉」。** 植入驗的是錯誤處理；機制回退要**另一種抵達**
   （靜態斷言）。兩者不會被同一個錯誤同時騙過才算兩種。

## §2 -test 模式：發現抖動的迴圈

```sh
sh loopctl/loopctl.sh notebooklm run --target <t> --dry-run   # 便宜、真跑讀取段
sh loopctl/loopctl.sh notebooklm prove --force-receipt        # 重戳宣稱
sh loopctl/loopctl.sh notebooklm test [--live]                # 對照組驗行為
```

**訊號 → 動作**

| 看到 | 做什麼 |
|---|---|
| `64` + `not on PATH` | 裝 notebooklm-py。**不要**跑去修登入 |
| `2` + `not-authenticated` | `notebooklm auth refresh`；太舊才 `login`。別當成套件壞了 |
| `2` + `PARTIAL id` | 有人把部分 id 傳進去了。修呼叫端，**不要**放寬純度斷言 |
| `2` + `follow-not-accessible` | 先 `curl` 那個 URL：**404=id 是假的**（回頭看 hop1 來源可信度）／**401=只是要登入，不代表沒分享給你**——你自己的私人文件同樣 401（§3 已量），所以下一步是查認證，不是去找人要權限 |
| `2` + `follow-library-absent` | CLI 在但它的直譯器 import 不到套件。修安裝，不是修權限 |
| `2` + `follow-none-accessible` | 讀收據 `hop2.attempted`——各條理由不一定同一種修法 |
| `2` + `no-ai-related-source` | 先確認不是**中文標題配不到**（§3 第 3 列），再考慮 `--source-title` |
| `2` + `registry-pin-stale` | 查清楚你要的是哪一本再改 registry。**不要**把 pin 拿掉了事 |
| 收據裡 hop2 綠但沒有 `via` | 機制被換回匿名 URL 路徑了。`notebooklm test` 的靜態斷言會抓，先跑它 |
| 帳號裡多出 `notebooklm-workflow-scratch-*` | `finally` 沒跑到。這是法則 4 的紅，優先修 |
| 改過 `notebooklm/` 任一檔 | 重戳 `prove` + 跑 `test`；**對照組測的是已提交的機制**，提交前的紅是誠實的 |

**兩條不可違反的處理原則**

- **修機制或修儀器，不調鈍儀器。** 把斷言放寬讓紅變綠是把問題藏起來。
- **卡住時換一個變因真跑，不要再往深處解釋。** 一連串假說都在解釋「為什麼它不給」，
  通常表示問錯了對象——而問錯對象在任何一層解釋裡都看不見。

## §3 Harness

### 已實作的機制

| 檔案 | 它證明什麼 |
|---|---|
| `workflow.py` | 兩跳的全部判斷與**每一個具名出口**。`--selftest` 用 PATH 上的假 CLI 驅動每種缺席，零網路 |
| `drive_fetch.py` | 認證過的 Drive by-reference。exit **3**＝套件不可 import、**4**＝Drive 拒了這份文件，兩者不共用出口 |
| `registry.json` | 互動資料：profile、notebook pin、harvest target。憑證**只留指針不留值** |
| `../proof_workflow/prove_notebooklm.sh` | 遍歷收據；per-run 產物具名排除 |
| `../proof_workflow/control_notebooklm_entry.sh` | 6 個植入缺陷 ＋ 1 條靜態斷言 ＋ opt-in `--live` 臂 |

### 真的抓到過的缺陷（形似訊號時先查這裡）

| 缺陷 | 怎麼被發現 | 修法 |
|---|---|---|
| 11 條連結全部 `ADD_SOURCE rpc_code=9` | 三個一變因探針：五份文件全失敗／同一本加 `example.com` 成功（機制沒壞）／未認證 curl 回 **401**，亂編 id 回 **404** | 401≠404 ⇒ 存在但被閘住 ⇒ CLI 的 URL 攝取是**匿名**的 ⇒ 改走 `sources.add_drive`（library only，CLI 無此旗標） |
| 上一條的**病因判斷是錯的**：我寫「沒分享給這個帳號」 | 用 Google Drive MCP 當**獨立第二抵達**逐一驗那 11 個 file id（2026-08-08） | **11/11 存在、原生 Google Doc、owner 就是本帳號**（`[AI Product Note] <公司>｜<日期>` 系列，3–5KB），亂編 id 回 `Entity not found`（負控有效）。所以閘是**認證**不是**分享**——**你自己的私人文件對匿名抓取一樣 401**。兩種抵達對「機制該怎麼改」一致（走認證路徑），對「為什麼」不一致，而**錯的那個會把人送去要一份他本來就擁有的權限**。`workflow.py` 的 `follow-not-accessible` 訊息仍列著舊病因，待修 |
| library 在別的環境，import 不到 | 上一條的修法要用 library | 直譯器**從 CLI 的 shebang 推**。寫死絕對路徑會被 root-coupling 閘擋，而且下一台機器就錯 |
| `json.loads` 死在一份真的存在的文件上 | 用部分 id 呼叫 `--json` | stdout 前面多一行 `Matched: <id> (<title>)` → 全 UUID ＋ **解析後仍斷言純度** |
| 中文標題全被判為「與 AI 無關」 | 挑選段挑不到任何來源 | Python 的 `\b` 是 Unicode-aware，`\bAI\b` **配不到**「AI高價值…」→ 改 ASCII 邊界 lookaround。**這個失敗長得跟「notebook 是空的」一模一樣** |
| 對照組兩條案例莫名 exit 127 | 只有那兩條紅，訊息是 `basename: command not found` | `PATH=x 函式呼叫` 的賦值在 POSIX sh **會留在當前 shell**，連記錄器自己的工具一起砍掉 → 改 `capture … -- env PATH=… <絕對 python3>` |
| 四個植入缺陷「全部沒被抓到」 | 植入後仍報 EXIT=0 | 我的量測寫成 `cmd; echo "$(basename …) EXIT=$?"`——**命令替換先跑並重設 `$?`** → 先把 rc 存進變數。儀器沒壞，量尺壞了 |
| 一條永遠成立的斷言 | 自審 diff | `case(..., "hop2" in txt or True, True)` → 刪掉。**假斷言比沒有斷言更糟**，它佔著一個看起來被覆蓋的位置 |
| 植入沒套用卻看起來被抓到 | 寫對照組時預先想到 | 錨點失效 ⇒ 測的是未修改的檔 ⇒ 永遠「紅得正確」 → `plant()` **先斷言錨點存在**，找不到就自己判紅 |
| 第一次 commit 被格式閘擋下 | pre-commit | 閘擋下**不會回滾 `git add`**。判準＝stage 與 commit 綁在同一條命令；被拒就先退暫存再重試 |
| `workflow lock` FATAL 說少了 container 收據 | 第二次 commit 前 | 第一次 commit 之後 **HEAD 變了**，八條迴圈的收據要在**新的 commit** 重戳一輪。收據跟著 commit，不跟著工作 |

### 邊界（刻意不做的事）

- **業務跑不進容器／沙盒。** 輸入含 bearer 憑證，upload 模型讓沙盒內每個 process 都讀得到；
  映像也沒有 `notebooklm`。`prove` 與 `test` 零網路，bind-mount 容器裡可跑。
- **不對抓回來的內容下判斷。** 摘要／排名／變現建議是下一段的事；塞進抓取層會讓
  「抓失敗」與「判斷不合意」共用同一個紅。
- **`--live` 預設關。** 關著時那一臂印 `NOT EXERCISED`——**那不是通過**。
