# loopctl — CLI 表面的法則與 Harness

> 這是給**下一個讀 loopctl 的 agent** 的系統提示詞。先讀 §1 法則，動手前跑 §2 的閘。
> 實例、真的抓到過的缺陷、邊界全在 §3 Harness，**不要把實例往前搬進法則**。
> 證明與對照組的設計法則在 `proof_workflow/README.md`；這裡只講 CLI 表面。

## §1 法則

1. **契約與接線是兩件事。** `contract.json` 說「呼叫端可以講什麼」，`loopctl.sh` 說「怎麼呼叫目標」。
   改其中一個而不改另一個，就是抖動；`selftest.sh` **雙向**綁住它們。
2. **表面動了要有人簽字。** `surface.lock` 只釘 loops × modes × flags。內部怎麼迭代都不該動它；
   真要動，`surface-relock` 會**拒絕**沒有 bump `surface_version` 的請求。
3. **狀態碼原樣傳到底。** `0 ok / 2 check failed / 64 usage-or-FATAL`。pipeline 與 `cmd; echo $?`
   會吞掉它——包裝層必須回傳真正的執行結果。
4. **第二份清單就是下一個缺陷。** 任何「loop 有哪些」「檔案有哪些」「binary 有哪些」都從
   `contract.json` 或收據導出，**不在第二個地方重寫**。
5. **每個成功訊息先斷言再輸出。** 印「已完成」之前先比對前後狀態，斷言成立才印。
6. **缺席要有自己的出口。** 檔案不存在、輸出為空、欄位缺漏——各自 FATAL 或標成獨立狀態，
   **絕不與「真的判定為否」長得一樣**。
7. **昂貴或不可逆之前先跑便宜的驗證面。** 每支入口都有 `--dry-run` 或 `--selftest`；
   先 grep 一次確認有沒有，再花錢。
8. **讀完介面契約再寫呼叫。** 讀 `--help` 命中行的**鄰近幾行**不算讀過介面（§3 有實例，代價是三次真跑）。
9. **改一個檔之前先問它被哪份收據雜湊。** 沒有收據的檔，改了不動任何 digest、lineage 也不會出聲。
10. **`workflow.lock` 由收據長出，不入任何證明。** hash 它會讓 digest 依賴一個依賴 digest 的檔，
    永不收斂而全程看起來是綠的。

## §2 動手前後的閘（依序）

```
sh loopctl/loopctl.sh --selftest          # 契約↔接線雙向、配對、狀態碼、surface.lock
sh loopctl/loopctl.sh <loop> prove        # 收據：這次遍歷了哪些位元組
sh loopctl/loopctl.sh <loop> test         # 對照組：機制真的會不同意嗎
sh loopctl/loopctl.sh workflow lock       # 由收據重建 manifest（先 git add，再 lock，再 add lock）
```

**訊號 → 動作**

| 看到 | 先做這件事 |
|---|---|
| `SELFTEST` 紅在 pairing | 有 loop 只宣告了 `prove` 或只宣告了 `test`——**補另一半，不要把檢查放寬** |
| `surface-relock` 拒絕 | 你動到了外部承諾。bump `surface_version`，或把改動退回內部 |
| commit 被 lineage 閘擋下 | 先 `<loop> prove --force-receipt` 再 `workflow lock`，**不是**改 message |
| 對照組報 `NOT EXERCISED` | 那格**沒有通過**，只是沒跑。補齊條件或在輸出裡具名 |
| 一支證明 FATAL 說沒有收據 | 樹是髒的而收據是乾淨的（或反之）——先蓋章再驗 |

**收尾**：改動 → 重蓋 contract 宣告的全部 prove 收據 → `workflow lock` → 一條命令內 `git add` ＋ `commit`。
被閘拒絕時**第一個動作是退出暫存**，不是重試（共用 tree 的暫存區是公共狀態）。

## §3 Harness

### 已實作的機制（改動前先認得它們）

| 檔 | 它保證什麼 |
|---|---|
| `contract.json` / `loopctl.sh` / `selftest.sh` | 呼叫端能講什麼 ↔ 怎麼接線，雙向綁定 |
| `surface_digest.py` / `surface.lock` | 外部承諾的指紋；只含 loops × modes × flags |
| `workflow_lock.py` / `lineage.py` / `.githooks/*` | 收據 → manifest → commit trailer → 閘 |
| `replay.sh` | `<commit\|tag>` → 用那個版本自己的 CLI 重跑 |
| `mcp_tools.py` / `mcp_server.py` / `result_json.py` | contract 生成的 MCP 工具面；`DENIED_TOOLS` 帶理由 |
| `Dockerfile` / `container-run.sh` / `container_preflight.sh` | 映像、runtime 選擇、**一個真 turn** 分辨 present 與 authenticated |
| `sandbox-policy.yaml` | deny-by-default 出口 ＋ binary 綁定 |
| `codex-openshell-config.py` / `codex-sandbox.sh` | 從 runtime-env projection 渲染 Codex custom provider；sandbox 只持 opaque placeholders，不持 `auth.json` |
| `automode-bench.sh` / `automode_report.py` | 三臂自動許可實驗（`off`／`on`／`reduce`）× 兩個 venue（`sandbox`／`direct`）；跑之前先讀報表的判準 |
| `skills-bundle.sh` | 共用 skills 以**具名 commit** 進沙盒；canonical 髒即拒絕，覆寫出口把 id 蓋成 `-dirty` |
| `evolve-technical-equivalence-research/` | hash-bound 技術觀點→實作等價物；獨立 control 在 disposable HEAD 做消融與 planted defects；offline/live/judge/Human 四態分記，sync bundle 停在人閘 |

### 真的抓到過的缺陷（形似訊號時先查這裡）

| 症狀 | 真因 |
|---|---|
| `SELFTEST GREEN` 但兩個檢查其實死了 | BSD sed 無 `\|`，抽取靜默失敗成空集合 → **每個推導比較前先斷言非空** |
| trailer 沒點名剛改的檔 | builder 的 loop 清單寫死五個而 CLI 有七個 → **從 contract 導出**；且要從 `writes` 推收據名，`mcp` 與 `policy` 共用一份收據 |
| trailer 把檔歸錯 loop | `setdefault` 讓字母序最前的佔位。**收據裡沒有任何欄位陳述擁有權** → 列出全部認領者，不猜 |
| lock 與同一個 commit 內容不符 | lock 建完檔又被改 → 雜湊改讀 **index**，加 staleness 閘 |
| 釘舊 tag 時每次調用 exit 64 | 該表面早於 `--json` → **啟動時**檢查並具名版本與修法 |
| 沙盒內 `HTTP CONNECT 403` 而 policy 明明列了 codex | npm 裝的是 `.js` shim，真正連線的是它 spawn 的原生檔——**policy 綁的路徑沒有任何 process 擁有** |
| `agent identity JWT payload is not valid JSON` | `--with-access-token` 要的不是 ChatGPT access token。**看起來像 token 壞掉，其實是餵錯欄位** |
| 模型答了、燒了 tokens、沒有檔案 | codex 用 bwrap 關自己，容器內建不了 namespace |
| guarded 那組三次全空 | `-a never` 不是 `codex exec` 的旗標——那個 `always\|never\|auto` **是 `--color` 的**（法則 8） |
| 報表印出正確表格「之後」才當掉 | codex 沒有 cost 欄位，`median` 對空集合拋例外。讀取端有防、**彙總端沒有** |
| OpenShell `Connection refused` 而 `docker ps` 正常 | OrbStack 走 docker **context**；`DOCKER_HOST` 要指到 orbstack socket。**這段曾散成四份，第四個呼叫端忘了** → 收斂進 `capture.sh` |
| 想「加一個省 token 的模式」時 | **先看 `reduce` 這一臂為什麼長這樣。** 它與 `off` 旗標**逐位元組相同**，只多一個 `.claudeignore`——因為 `on` 貴的原因是換掉工具面→cached prefix 變了→整個重寫。往 `reduce` 加任何一個旗標，它就變成第二個 `on`，而報表還是寫 `reduce`。selftest 有一條專門把這個等式釘住，並且驗過會紅 |
| 直接執行的三臂量測沒有分離 | n=3 時**組內散布壓過組間差異**（off 的 cost 跨 0.135–0.466）。唯一看得見的形狀是 `on` 從沒有便宜的那一次，而 off／reduce 各有一次 cache-write 只有 ~3000——與 prefix 理論一致，**但一致不等於成立**。要下結論得加 n，或換一個真的會誘發貪婪探勘的任務 |
| 前置說「provider 不存在」，但它明明在 | `openshell provider list 2>/dev/null \| grep -q` 把**「問不到」與「答案是否」折成同一件事**——gateway 連不上時，它印出一句自信的「去建一個 provider」，而那個 provider 一直都在。三種結局要分開：問不到（64，具名對方的抱怨第一行）／問到了且沒有／問到了且有。**同一個形狀在 `control_sandbox_policy.sh` 也有一份** |
| 安全對照組在儀器缺席時**通過最用力** | 探針 `code=$(curl … 2>/dev/null)`，curl 不存在 → 空 → `${code:-000}` → `000` 判成 denied → PASS。**掃同類時才發現的**：修完 provider 那條後掃「失敗被消音再當布林用」的形狀，這一個在安全檢查上。curl 的 exit code 與 HTTP 狀態分開帶（`nocurl/0`），缺席走自己的 FATAL 分支 |
| skills bundle 上傳了但 agent 看不到 | 目標路徑寫錯**與完全沒上傳長得一模一樣**（同樣的數字、同樣的沉默）。路徑從 binary 量出來（`.claude/skills` ／ `.codex/skills`），並由**同一個 resolver 函式**供給執行與 selftest——第一版在測試裡重寫字面值，那是同義反覆，對任何實作都會通過 |
| 新加的守衛「綠」，但它其實什麼都沒查 | 把 resolver 樁成回空集合 → 掃描報 0 個不符、exit 0。**「解析不到卻回傳成功」與「查遍了沒問題」長得一模一樣** → 空集合改成 FATAL(64)，並用樁把這件事驗進 selftest |
| 上一列那個修法**弄紅了另一個檢查** | 環境變數集中設好後，wrapper 跳過自己的選擇邏輯、不再印公告，而對照組正在斷言那句話。**收斂共用設定會讓「驗這個設定本身」的檢查失去對象** → 那一格改用 `env -u` 問 |

### 邊界（刻意不做的）

- **`workflow.lock` 不入任何證明**（循環）；它的完整性來自「可重建」。
- **`--upload` 沙盒沒有 `.git`**，所以證明與 replay 不能住在那裡；bind-mount 用來證明，
  upload 沙盒用來跑 agent turn。這條分工是硬的。
- **codex 的 `auth.json` 路徑不能吃 placeholder**，但這不是整個 client 的限制：custom model provider
  會把 placeholder 直接放進 HTTPS header。若有人又把真 session 放回沙盒，`tests/test_codex_openshell_placeholder.sh`
  與 runtime-env policy 必須立刻紅。
- **死鎖出口**：機制自己壞掉時，commit message 寫 `Workflow-Lineage-Override: <理由>`，理由必填。
