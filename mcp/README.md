# mcp — 工具面與遷移機制的法則與 Harness

> 這是給**下一個讀 mcp 的 agent** 的系統提示詞。先讀 §1 法則，動手前跑 §2 的閘。
> 實例、真的抓到過的缺陷、邊界全在 §3 Harness，**不要把實例往前搬進法則**。
> 逐指令用法在 `production/README.md` 與 `context-pack/README.md`；
> 證明與對照組的設計法則在 `proof_workflow/README.md`。

兩個住戶，職責不重疊：
`production/`＝把 MCP 設定**遷移**到別的 repo 的機制；`context-pack/`＝一支**唯讀**的 MCP server。

> **⚠ 目前 `mcp/` 沒有任何證明雜湊它**（`workflow.lock` 裡 0 個 `mcp/` 路徑）。
> 意思是：改這裡的任何一支程式，**digest 不動、lineage trailer 不出聲**。
> 這是已知缺口，不是設計；動它之前先讀法則 10。

## §1 法則

1. **機制不擁有政策。** `migrate.py` 是三個 repo 共用的遷移機制，**profile 屬於各 repo**。
   host 權限設定（socket、loopback allowlist、sandbox policy）是主機／工作階段的東西，
   **刻意不鏡像**——`apply` 永遠不替換那類檔案。
2. **收據記雜湊，不記輸出。** `verify` 存的是雜湊而非指令輸出，否則**收據本身會變成憑證或
   prompt dump**——一份為了可稽核而存在的檔案，反而成了外洩面。
3. **收據串鏈，而且驗整條。** 每份收據含前一份的 SHA-256；`check-receipts` 驗完整條鏈。
   單看一份收據，證明不了中間沒有被抽掉一份。
4. **rollback 要求那一份 apply 收據，且拒絕 apply 之後被改過的目標。** 「還原」不能還原到
   一個已經不是當初那個的目標上。
5. **拒絕清單 fail-closed，而且具名。** 路徑穿越、symlink 目的地、受保護分支、髒目的地覆蓋、
   字面秘密、重量級執行器宣稱常駐——**每一條各自拒絕，不合併成一句「不合法」**。
6. **工具面刻意窄，並說出自己不是什麼。** context-pack 不是 search、不是 LSP：
   GrepAI／Serena 負責找，它只負責把**選定的**來源重新打開。只收 repo-relative 的 `.py`。
7. **每個結果綁在來源位元組上，並回報 partial。** SHA-256 綁定 ＋ completeness 欄位；
   **「部分完整」要說出來**，讓下游知道還得讀原始碼。
8. **證據有優先序，預算耗盡時丟低的。** signature 與未解析的動態呼叫是**必需**；
   預算不夠時丟低優先事實，**不是丟必需的**。
9. **不宣稱本機對齊控制得了遠端 cache。** 穩定的 prompt 前綴**可能**改善伺服器端重用，
   但**命中要在 API 邊界量**。這條寫在 README 裡是因為它很容易被講成既成事實。
10. **凍結的基準收據只能因為程式真的變了而重釘。** 為了讓 formatter 或 linter 過而重釘一份
    benchmark 收據，是**偽造證據**——寧可讓那兩個檔帶著格式債，並寫下為什麼。
11. **新的 project MCP 由人 admit 一次。** 那是供應鏈閘，不要繞過。

## §2 動手前後的閘（依序）

```sh
# production
python3 -m unittest discover -s mcp/production/tests -v
python3 mcp/production/migrate.py --repo-root <abs> --profile <p> plan      # 先 plan
python3 mcp/production/migrate.py --repo-root <abs> --profile <p> verify --receipt
python3 mcp/production/migrate.py --repo-root <abs> --profile <p> check-receipts

# context-pack
uv sync --project mcp/context-pack --locked
uv run --project mcp/context-pack --frozen python -m unittest discover -s mcp/context-pack/tests -v
uv run --project mcp/context-pack --frozen python mcp/context-pack/benchmarks/compare_extractors.py
```

**訊號 → 動作**

| 看到 | 先做這件事 |
|---|---|
| `apply` 想動 host 設定檔 | 那不是可攜的 MCP payload（法則 1）。把它留給主機 |
| `check-receipts` 斷鏈 | **不要重建鏈**。先查是誰抽掉或重寫了中間那份 |
| rollback 被拒 | 目標在 apply 之後被改過。先確認要還原的是哪一份現實 |
| context-pack 回 `partial` | 那**不是**失敗，是誠實。預算不夠時要去讀原始碼補（法則 7/8） |
| benchmark 收據與程式對不上 | 先問「程式變了嗎」。**只有程式變了才重釘**（法則 10） |
| 想在這裡加一個非唯讀的工具 | 停。context-pack 的價值來自它窄（法則 6） |

## §3 Harness

### 已實作的機制（改動前先認得它們）

| 檔 | 它保證什麼 |
|---|---|
| `production/migrate.py` | `plan` / `apply` / `verify` / `rollback` / `check-receipts`；stdlib only；六類拒絕各自具名 |
| `production/profile.schema.json` ＋ `profile.json` | 遷移的可攜宣告；政策留在各 repo |
| `production/probe_stdio.py` | 走**真的 JSON-RPC transport** 探一支 Codex 設定的 stdio MCP，fail-closed |
| `production/receipts/*.json` | append-only 且以前一份的 SHA-256 串鏈 |
| `production/templates/*` | claude / codex / serena 三種 host 的樣板，彼此不互相假設 |
| `context-pack/src/.../engine.py` | AST 擷取；拒絕絕對路徑／穿越／symlink 逃逸／不支援語言／過大檔／讀取中被改動的檔 |
| `context-pack/src/.../server.py` | 兩個工具面：`build_python_context_pack`、`context_pack_status` |
| `context-pack/benchmarks/` ＋ `receipts/` | 凍結在特定機器與日期的比較收據（`m1-pro-2026-07-29`） |

### 真的抓到過的缺陷（形似訊號時先查這裡）

| 症狀 | 真因 |
|---|---|
| 兩個 `.py` 過不了 ruff-format | **刻意不修。** 它們被一份凍結的 benchmark 收據釘住，為了格式而重釘收據＝偽造證據（法則 10）。理由寫在 commit 裡 |
| `test_in_process_tools_list_and_call` 紅 | **先存在的失敗，與這輪改動無關**——在 HEAD 驗過完全相同。**不要在它上面疊修改**，先讓它獨立地紅或綠 |
| 收據看起來像稽核紀錄，其實含輸出 | 那正是法則 2 要擋的形狀：一份可稽核的檔案變成外洩面 |

### 邊界（刻意不做的）

- **不鏡像 host 權限設定**（法則 1）。
- **context-pack 不做搜尋、不做 LSP、不碰 TypeScript**（法則 6）；窄是它的價值。
- **不宣稱本機記憶體對齊會影響遠端 cache**（法則 9）。
- **`mcp/` 目前不在任何證明的雜湊裡**——這是**缺口不是決定**。要補的話，
  `migrate.py` 與 `engine.py` 各自帶得動的驗證面（unittest）就是現成的 `prove_harness` 目標；
  卡住的是 context-pack 有一個先存在的紅測試，接進去會讓整份證明變紅。
  **先讓那個測試獨立地綠，再接。**
