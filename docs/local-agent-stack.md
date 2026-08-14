# 本機 Agent stack：CGR、Mem0、Herdr

本檔是 bettor-arena 的本機操作交接，範圍只有 Code Graph RAG（下稱 CGR）、Mem0 與
Herdr。`docs/agent-runtime-integration.md` 管跨 repo 模組綁定與 Claude/Codex live receipt；
兩者是不同判決面，任一面綠都不能代理另一面。

以下現況最後實測於 **2026-08-13（Asia/Taipei）**。running 是易變狀態；接手 Agent 先跑
「重測現況」，再採信本表。

## 四態判決

| 元件 | installed | running | wired | data-ready |
|---|---|---|---|---|
| CGR | CLI `0.0.589`；本機 source checkout 宣告 `0.0.623`，兩者有版本差 | Memgraph、Qdrant 與 Lab 可達 | 未寫入 `.codex/config.toml`／`.mcp.json` | 否；`cgr status` 無 synced project，graph 是 0 nodes／0 relationships |
| Mem0 | CLI `0.2.11` | API、dashboard、PostgreSQL 三服務可達 | 否；CLI 仍指向 Mem0 Platform，self-host client adapter 未驗 | 否；`/auth/setup-status` 回 `needsSetup=true` |
| Herdr | CLI `0.8.0` | named session `bettor-arena` running | 否；`herdr integration status` 顯示 Codex、Claude 等 integrations 均未安裝 | 不適用；它管理 terminal workspace，不持有專案知識 |

「完整 self-hosted stack 已啟動」目前只對**基礎服務層**成立。它不表示 Mem0 已完成模型設定、
CGR 已索引 bettor-arena，或任何 Agent 已經能呼叫這些服務。

## 本機拓撲

所有 published ports 都綁 `127.0.0.1`。`3000` 已由 Forgejo 使用，因此兩個 dashboard 必須
保留目前的避讓值。

| 服務 | 本機端點 | 用途 |
|---|---|---|
| Forgejo | `127.0.0.1:3000` | 既有服務；不是本 stack 的 compose service |
| CGR Lab | `http://127.0.0.1:3001` | Memgraph 圖形介面；CGR 預設 `3000`，啟動時必帶 override |
| Memgraph | `127.0.0.1:7687`、`127.0.0.1:7444` | CGR graph store |
| Qdrant | `127.0.0.1:6333`、`127.0.0.1:6334` | CGR vector store |
| Mem0 dashboard | `http://127.0.0.1:3002/setup` | 首次設定與日常 UI |
| Mem0 API | `http://127.0.0.1:8888` | self-hosted REST API；OpenAPI 在 `/docs` |
| Mem0 PostgreSQL | `127.0.0.1:8432` | app DB 與 pgvector |

先從 repo 位置推導本機 checkout，避免把某個使用者的 home path 寫進 tracked 檔：

```sh
BETTOR_ARENA_ROOT="$(git rev-parse --show-toplevel)"
BETTOR_PROJECTS_ROOT="$(dirname "$BETTOR_ARENA_ROOT")/github_projects"
BETTOR_MEM0_SERVER="$BETTOR_PROJECTS_ROOT/mem0/server"
BETTOR_MEM0_OVERRIDE="$BETTOR_MEM0_SERVER/history/bettor-arena.compose.override.yaml"
BETTOR_CGR_STATE="${CGR_STATE_DIR:-$HOME/.cgr}"
```

若任何推導路徑不存在，先停下來重新定位 checkout；不要讓 compose 靜默改用另一份設定。

## 重測現況

### CGR

```sh
cgr --version
cgr daemon status
cgr status
cgr stats
docker compose -f "$BETTOR_CGR_STATE/docker-compose.yaml" ps
curl -fsS -o /dev/null -w 'cgr_lab=%{http_code}\n' http://127.0.0.1:3001
```

`cgr daemon status` 只量 Memgraph 與 Qdrant，不量 Lab；所以 Lab 的 compose row 與 HTTP receipt
不可省。`cgr status` 必須明列 bettor-arena，且 `cgr stats` 必須非零，才算 data-ready。

### Mem0

```sh
test -f "$BETTOR_MEM0_SERVER/.env"
test -f "$BETTOR_MEM0_OVERRIDE"
docker compose \
  --project-directory "$BETTOR_MEM0_SERVER" \
  -f "$BETTOR_MEM0_SERVER/docker-compose.yaml" \
  -f "$BETTOR_MEM0_OVERRIDE" ps
curl -fsS http://127.0.0.1:8888/auth/setup-status
curl -fsS -o /dev/null -w 'mem0_dashboard=%{http_code}\n' http://127.0.0.1:3002/setup
mem0 --json config show
```

HTTP 200 只證 web surface 抵達。`needsSetup=false`、本機 client 的 add/search 各一筆成功收據，
才足以把 Mem0 判成 wired 且 data-ready。

### Herdr

```sh
herdr --version
herdr session list
herdr integration status
```

named session 的權威查法是 `herdr session list`。裸 `herdr status` 查 default socket；default
stopped 時會看似整個 Herdr 沒跑，不能用它否定 `bettor-arena` named session。

## 啟停

### CGR stack

```sh
LAB_PORT=3001 cgr daemon up
# 需要重啟時：LAB_PORT=3001 cgr daemon restart
# 保留 volumes 停機：cgr daemon down
```

每次 `up`／`restart` 都帶 `LAB_PORT=3001`。省略它會讓 Lab 回到 `3000`，與 Forgejo 衝突。
`cgr start --clean` 與 `cgr delete-project` 會刪 graph；正常啟停使用上列 daemon 命令。

### Mem0 stack

```sh
docker compose \
  --project-directory "$BETTOR_MEM0_SERVER" \
  -f "$BETTOR_MEM0_SERVER/docker-compose.yaml" \
  -f "$BETTOR_MEM0_OVERRIDE" up -d

# 停機並保留 volume：把上一個命令的尾端改成 stop
# 連 container/network 一起移除但保留 volume：把尾端改成 down
```

本機 override 是 ignored host state：它把三個 port 綁回 loopback、把 dashboard 改到 `3002`、
讓 dashboard 指向 `8888`，並關閉 Mem0 telemetry。`.env` 也是 ignored host state，權限應為
owner-only；只檢查是否存在，不輸出內容。這台機器不要用 upstream `make up`，因為它的 `3000`
preflight 不知道 override，會和 Forgejo 衝突。

### Herdr session

```sh
(cd "$BETTOR_ARENA_ROOT" && herdr --session bettor-arena)
herdr session attach bettor-arena
herdr session stop bettor-arena
```

第一行會建立或 attach session；TUI 內用 `Ctrl-b q` detach，保留 server 與 panes。

## 尚未完成的整合需求

依序完成，前一項沒有物理收據就不要宣稱後一項完成：

1. **Mem0 onboarding**：在 `http://127.0.0.1:3002/setup` 建立本機 admin、選定 LLM 與
   embedder provider、輸入 provider credential，並建立本機 API key。credential 只進 browser／
   ignored host state。現有 `.env` 的無效 bootstrap placeholder 只讓 first-run API 能啟動，
   不代表模型可用。完成後重測 `needsSetup=false`，再做一組 add/search round trip。
2. **CGR 版本對齊**：決定以已安裝 CLI `0.0.589` 或 source checkout `0.0.623` 為準；未對齊前，
   不可假設修改 checkout 會改變實際執行行為。
3. **CGR cache 放置裁決**：graph sync 會在 repo root 產生 `.cgr-hash-cache.json`、
   `.cgr-dir-mtimes.json`、`.cgr-parser-fingerprint`。目前 §2 與 `.gitignore` 都未接納；先決定
   redirect 或正式登記為 ignored runtime state，再執行 `cgr start --update-graph`。
4. **CGR data receipt**：sync 後要求 `cgr status` 列出 bettor-arena，且 `cgr stats` 的 nodes 與
   relationships 都大於零。Lab HTTP 200 不能代理這兩項。
5. **Agent 接線**：CGR 的 stdio 入口是 `cgr mcp-server`；若採用，必須同時更新
   `.codex/config.toml` 與 `.mcp.json`，再做真 JSON-RPC probe。Mem0 需另選並驗證 self-hosted
   REST client adapter；目前安裝的 CLI 仍指向 Platform。Herdr integration 會寫 host 設定，先由人
   選定 Codex／Claude carrier，再安裝並重跑 `herdr integration status`。
6. **最終判決**：只有 CGR query、Mem0 add/search、Herdr selected integration 三條各自有 live
   receipt，才可把本 stack 標成 integrated。任何單一 dashboard、container 或 CLI version 綠，
   都只證它自己的軸。

## 安全邊界

- 維持所有 service 只綁 loopback；需要遠端存取時另做具名安全設計，不直接改成全網卡發布。
- tracked 文件只記 credential 的存放契約與狀態，不記值；不要 `cat`、log 或 commit `.env`。
- Mem0 保持 auth enabled、telemetry disabled；setup 完成不等於可以關 auth。
- 刪 graph、刪 volume、重建 provider config 都是 destructive 變更，先解析精確目標並取得明確授權。
