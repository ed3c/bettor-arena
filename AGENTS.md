# AGENTS.md — bettor-arena（Codex／跨 host 強制入口）

工程 SSOT＝`ARCHITECTURE.md`：放置契約＝§2、鐵律全文＝§3。完整模組化 MVP 契約＝
`docs/architecture/modular-integration-requirements.md`。本檔只負責**強制讀取順序、不可違反邊界與完成報告**，
禁止把完整規格複製進 root passive context。

- 啟用：`sh bootstrap.sh`（冪等；doctor + 相對 hooksPath）。
- Skill 內容單份住 `.agents/skills/`；`.claude/skills` 只作 pointer/forwarder。
- `.codex/config.toml` 只保存可攜 MCP 宣告；host permissions/network/sockets 由人配置。
- commit 前走 `ARCHITECTURE.md` §3 的 T0 閘；落新檔前先查 §2 槽位與 module owner。

## Mandatory read order

涉及 module、大小迴圈、Skills、runtime-env、proof、MCP、Claude/Codex adapter、browser route、
GitHub/Forgejo origin、外部專案初始化或 Agent Shield 整合時，動手前依序讀取：

1. `ARCHITECTURE.md` §1–§3；
2. `docs/architecture/modular-integration-requirements.md`；
3. `docs/agent-runtime-integration.md`；
4. `sh loopctl/loopctl.sh contract`；
5. 目標 loop 自己的 `AGENTS.md`、`CLAUDE.md`、`PROMPT.md`、`ROUTES.md`、`PLAN.md` 與法則層；
6. 最新 proof/control receipt 與 named exclusions。

修改 `AGENTS.md`／`CLAUDE.md` 後，必須開新 Agent session 才能驗證 passive context。

`modular-integration-requirements.md` 是 target contract，不是完成宣告。不存在的 `.arena/` manifests、
module-scoped proof v2、Context Capsule、project initializer、multi-origin release 或 browser contract v2
必須回報 `NOT_IMPLEMENTED`；存在但未跑的 live/provider path 必須回報 `NOT_EXERCISED`。

## Bettor Arena role

本 repo 必須被理解為：

```text
Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper
```

模組化最低判準仍是：零入向 private code reference、自有 verify、自有 selftest、隔離環境 relocation 綠，
且每個綠有能使它轉紅的 hollow／mutation evidence。

## Macro / Micro boundary

| | 大迴圈 Macro / Composition | 小迴圈 Micro / Task |
|---|---|---|
| 擁有 | module selection、dependency/conflict、projection、proof matrix、Human Admit、lock、promotion/rollback | typed task、bounded iteration、local state、typed result、named exits、module proof/control |
| 可讀 | manifests、composition locks、public capabilities、receipts | 自己的 passive context、source、private executable |
| 使用其他 module | 只走 capability / `loopctl` public port | typed packet → public port → artifact/receipt ref |
| 禁止 | 學習 private flags、prompt fragments、per-run temp | source/import 另一 module internal、讀另一 module `_engine-run/` |

大小迴圈的縫合面只能是 public interface、typed packet、artifact reference、exit code 與 receipt。
Human Admit、promotion、production rollback 只屬於大迴圈或 trusted host operator。

## Internal / External consumption

```text
Symlink = Local Development Channel
Bundle + Lock = Reproducible Execution Channel
CLI / MCP = Public Consumption Channel
```

- 同一 module 內部：public adapter 可呼叫自己 closure 內的 executable。
- 同 repo 跨 module：stable library API 或 `loopctl`。
- 外部 repo：預設 immutable bettor release + stateless MCP；離線／客製才用 embedded bundle。
- Symlink 只允許 shared Skill/passive instruction 的本機投影；禁止承載跨 repo executable、venv、
  `node_modules`、runtime checkout、browser profile、cookie、credential 或 cloud dependency。

## CLI, MCP, and passive context

1. `loopctl` 是唯一 canonical CLI；MCP tools 必須由 CLI contract 生成。
2. 未明確宣告 `external_policy.exposed=true` 的 command，預設不出現在 `tools/list`。
3. 每個 MCP call 必須 pin immutable release，使用 disposable worktree／bundle，不讀 owner live checkout。
4. Caller 不得指定 server-host absolute path、任意 `cwd`、private flag、secret 或 browser profile。
5. 只接受 typed packet、inline bundle 或 content-addressed artifact ref；完成後清除所有 runtime state。
6. 大迴圈不能包成一個長 MCP call；拆成 `plan → resolve → verify → status` continuation packets。
7. Apply live repo、Human Admit、promotion、production rollback、secret rotation、permission widening 不對模型暴露。

MCP 封裝的是 **Context Materialization**，不是任意 prompt execution：

```text
resolve immutable release
  → materialize root + loop native context files
  → verify/freeze context digest
  → cwd = loop root
  → launch allowlisted claude -p / codex exec adapter
  → validate typed output
  → emit context + driver receipt
```

Root context 保存全域法則；loop context 保存 `PROMPT.md`、`ROUTES.md`、`PLAN.md` 與八大基座的具體落點。
禁止把兩層上下文壓平成一段 MCP prompt 後刪掉 native files。

## Proof and anti-jitter

每個 module 必須有不同抵達：

- `proof`：context/harness/artifact traversal；
- `control`：真從 public port 執行並觀察 touched paths/exits；
- `mutation`／hollow：load-bearing guard 失效時必須轉紅；
- `consumer-canary`：外部 Claude/Codex 經 released adapter 真呼叫；
- `release-receipt`：composition promotion 時聚合同一 subject 的 evidence。

ABSENT、FAIL、NOT_EXERCISED、hashed-not-run 與 PASS 不可互相代理；exit code 原樣傳到底。
目標 proof v2 以 module closure digest 作 validity key：修改 A 只使 A 與 transitive dependents stale，
不得重寫無依賴關係的 B receipt 追隨 repo HEAD。

## Conflict, Skills, runtime, origins, browser

- 每個 tracked path 只能有一個 module owner。
- Root projections 由 module fragments deterministic generation；module 不維護平行版本。
- Module 間只傳 typed packet/artifact/receipt；entrypoint 使用 exact environment allowlist。
- Skills 對 selected modules 求 requirements-filtered closure；shared/repo-owned 同名或不相容 bytes 時 RED。
- `runtime-env` 只同步 secret-free projections；consumer gate 不讀 sibling checkout、不連網、不自動 sync。
- Forgejo＝local authoring origin，GitHub＝cloud distribution origin；兩者屬同一 logical release，
  必須驗 `exact-commit`、`same-tree` 或 `same-release-manifest`，禁止 fallback 到 mutable `main`。
- Claude Code、Codex CLI、agy 是 actors；Playwright、stealth-browser、Antigravity CDP 是 transports/adapters。
  Signed-in profile/session 不得 local→cloud file sync。
- `gemini-conversation-research` 正文 file-only；`dr-research-loop` browser lane 是 optional raw Stage 1；
  `external-verify` raw primary first，browser fallback 必須標 evidence downgrade。

Agent Shield domain product 應由 `agent-shield-monorepo` 擁有；bettor-arena 只消費 selected immutable modules。
PDF parsing/document ingestion 是獨立 module。E2B、Firecracker、啟動延遲、成本、授權與 provider capability
是 research inputs，未經 `external-verify` + runtime canary 不得升格為不變量。

## Completion contract

任何觸及此整合面的 Agent，收手前必須報告：

```text
changed module ids / interface versions / closure digests
affected transitive dependents
changed public CLI / MCP surface
path ownership conflicts
proof / control / mutation-hollow results
Claude / Codex adapter results
GitHub / Forgejo origin and equivalence status
browser / live canary status
remaining NOT_IMPLEMENTED / NOT_EXERCISED
rollback subject
```

缺少適用項目，不得宣稱 modular integration complete。

## Rule → Evidence routing

完整 requirement 與 current/target 差距讀 `docs/architecture/modular-integration-requirements.md`；
目前八大基座 worked evidence 由
`loop_wiki/evolve-perfect-seed-repo-factory/modules/eight-base-laws.md` 承載。

| 法則主題 | 實證 Harness |
|---|---|
| 綠燈價值取決於抵達；兩種獨立抵達才 settled | eight-base-laws 抵達分層表；SANDBOX 綠不能代理 PROD/Human Admit。 |
| 儀器該紅時真的會紅 | B3：`selftest.sh` hollow + `portability.sh` 負控。 |
| 缺席≠否；狀態碼傳到底 | B2：各段 exit 分記，未執行為 `not_run`。 |
| 模組不向上依賴；搬一次才算解耦 | B5：抽出、獨立安裝、verify 與負控。 |
| Shared worktree staging 是公共狀態 | §7：commit 被拒後先退自己的 stage，再以單一命令 stage+commit。 |
| 推翻是時間線，note 必填 | B8：append 誤信原因，禁改寫歷史。 |

<!-- 新增 module evidence 時，先更新 canonical requirement/manifests，再由 generator 更新本路由。 -->
