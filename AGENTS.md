# AGENTS.md — bettor-arena（Codex／跨 host 強制入口）

工程 SSOT＝`ARCHITECTURE.md`：放置契約＝§2、鐵律全文＝§3。規則原文只住 canonical 文件，
本檔負責 **強制讀取順序、模組化邊界、外部使用限制與完成契約**，不得再建立平行 implementation truth。

- 啟用：`sh bootstrap.sh`（冪等；doctor + 相對 hooksPath）。
- Skill 內容單份住 `.agents/skills/`（host-neutral；`.claude/skills` 只作 pointer/forwarder）。
- `.codex/config.toml` 僅保存可攜 MCP 宣告；host permissions/network/sockets 由人配置後才可信。
- commit 前：走 `ARCHITECTURE.md` §3 的 T0 閘；落新檔前：先查 §2 槽位與 module owner。

---

## 0. Mandatory modular-integration read order

任何涉及 module、大小迴圈、Skills、runtime-env、proof、MCP、Claude/Codex adapter、browser route、
GitHub/Forgejo origin、外部專案初始化或 Agent Shield 整合的工作，**動手前必須依序讀取**：

1. `ARCHITECTURE.md` §1–§3；
2. `docs/architecture/modular-integration-requirements.md`；
3. `docs/agent-runtime-integration.md`；
4. `sh loopctl/loopctl.sh contract` 的目前 public surface；
5. 目標 module／loop 自己的 `AGENTS.md`、`CLAUDE.md`、`PROMPT.md`、`ROUTES.md`、`PLAN.md` 與法則層；
6. 該 module 最新 proof/control receipt 及其 named exclusions。

修改本檔後，既有 Codex／Claude chat 的 passive context 不會自動刷新；必須開新 session 才能驗證讀取結果。

### Current implementation vs target contract

`docs/architecture/modular-integration-requirements.md` 是下一階段 MVP 的規範性目標。文中不存在的 `.arena/`
manifests、module-scoped receipts、project initializer、browser contract v2 等，必須回報 `NOT_IMPLEMENTED`；
存在但未跑的 live/provider path 必須回報 `NOT_EXERCISED`。禁止把規格文字讀成已落地能力。

---

## 1. Bettor Arena 的五個角色

本 repo 必須被理解為：

```text
Module Host
+ Loop Runtime
+ Proof Kernel
+ Stateless MCP Gateway
+ Project Bootstrapper
```

它不是「很多 scripts 在同一 repo」；模組化的最低判準仍是：零入向 private code reference、
自有 verify、自有 selftest、隔離環境 relocation 綠，且每個綠有能使它變紅的對照或 mutation。

---

## 2. 大迴圈與小迴圈邊界

### 大迴圈（Macro / Composition）擁有

- module/component selection；
- capability provider resolution；
- dependency 與 path conflict detection；
- Skills/runtime/Claude/Codex projection generation；
- proof matrix；
- Human Admit；
- composition lock、promotion 與 rollback。

大迴圈只使用 module manifests、composition requirements/locks、public capabilities、`loopctl` public ports
與 receipts。**不得**直接學習或呼叫 module private flags、private executable、prompt fragment 或 per-run temp。

### 小迴圈（Micro / Task）擁有

- 一個 typed task；
- bounded internal iterations；
- 自己的 passive context 與 private implementation；
- module-local state；
- typed result、artifacts、named exits；
- module-local proof/control。

小迴圈可直接讀取自己的文件與 executable。使用另一個 module 時，只准：

```text
typed packet
  → other module public port
  → typed result / artifact reference
  → receipt reference
```

禁止跨 module `source` private shell、import internal module、讀 `_engine-run/` 或為了 caller 改 private flags。

---

## 3. 內部／外部模組消費方式

| 情境 | 合法方式 |
|---|---|
| module 使用自己的 implementation | 由自己的 public adapter 呼叫 repo-internal path |
| 同 repo 跨 module | stable library API 或 `loopctl` public CLI |
| 外部 repo 只消費能力 | immutable bettor release + stateless MCP |
| 外部 repo 要離線／客製 | selected immutable embedded module bundle |
| local shared Skill 開發 | requirements-filtered symlink／forwarder |
| cloud / CI / released execution | bundle + lock + provenance receipt |

固定規則：

```text
Symlink = Local Development Channel
Bundle + Lock = Reproducible Execution Channel
CLI / MCP = Public Consumption Channel
```

Symlink 禁止承載跨 repo executable、venv、`node_modules`、runtime-env checkout、browser profile、cookie、
credential 或 cloud execution dependency。

---

## 4. Public surface 與 Stateless MCP

1. `loopctl` 是唯一 canonical CLI surface；外部 caller 不得直呼 module private entrypoint。
2. MCP tools 必須由 CLI contract 生成，不得手寫第二份 flags/schema/exit semantics。
3. 未明確宣告 `external_policy.exposed=true` 的 command，預設不出現在 MCP `tools/list`。
4. 每個外部 call 必須 pin immutable commit/tag/logical release，使用 disposable worktree 或 immutable bundle。
5. 不讀 owner live checkout；不接受 caller 指定 server-host absolute path、任意 `cwd` 或 private flag。
6. 只接受 typed packet、inline bundle 或 content-addressed artifact reference。
7. 回傳 typed result、artifact digest、context/driver/proof reference；stdout/stderr 依 contract bounded/redacted。
8. 呼叫結束後必須清除 worktree、temp、process、lease 與 runtime state。
9. Macro loop 不能包成一個長 MCP call；拆成 `plan → resolve → verify → status` continuation packets。
10. Human Admit、apply live repo、promotion、production rollback、secret rotation 與 permission widening 為 host/operator-only。

---

## 5. 雙層 passive context 與 driver 封裝

### Root / 大迴圈 context

```text
AGENTS.md
CLAUDE.md
ARCHITECTURE.md
CONTEXT.md
modular-integration-requirements.md
composition requirements / lock
loopctl/contract.json
```

### Loop / 小迴圈 context

```text
<loop>/AGENTS.md
<loop>/CLAUDE.md
<loop>/PROMPT.md
<loop>/ROUTES.md
<loop>/PLAN.md
<loop>/modules/eight-base-laws.md
<loop>/module.json（落地後）
<loop>/schemas/*
```

MCP/CLI 封裝的是 **Context Materialization**，不是任意 prompt execution：

```text
resolve immutable release
  → materialize native root + loop context files
  → verify context digest and freeze it for one run
  → cwd = loop root
  → launch claude -p or codex exec through allowlisted driver adapter
  → validate typed output
  → emit context + driver receipt
```

Claude 與 Codex 的 host entry 可以不同，但 canonical semantics、module/skill lock 與 task packet 必須相同。

---

## 6. 八大基座不得被 MCP 壓平

| Base | 必須仍有的載體 |
|---|---|
| B1 Rules / Context | root/loop `AGENTS.md`、`CLAUDE.md`、typed packet |
| B2 Settings / Authorization | driver adapter、runtime policy、human-owned permissions |
| B3 Lifecycle / Observation | receipt、`PLAN.md` |
| B4 Route Discovery | `ROUTES.md` |
| B5 Specialization | module contract、domain Skill、router |
| B6 Independent Verification | verify、selftest、control、portability、Human Admit |
| B7 Goal Contract | `PROMPT.md` |
| B8 State Ledger | append-only `PLAN.md`／composition ledger |

不可把八大基座全文拼成一個 MCP prompt 後刪掉 native files；那會讓 Claude/Codex passive context、
proof traversal 與 module relocation 無法被獨立驗證。

---

## 7. Proof / Control / Anti-jitter 完成面

每個 module 必須有不同抵達：

- `proof`：宣稱走過哪些 context/harness/artifact；
- `control`：真從 public port 執行並觀察 touched paths/exits；
- `mutation` 或 hollow fixture：load-bearing guard 失效時必須轉紅；
- `consumer-canary`：外部 Claude/Codex 經 released adapter 真呼叫；
- `release-receipt`：composition promotion 時聚合相同 subject 的 evidence。

每個 skipped、absent、hashed-not-run、not-exercised item 都要具名並說明理由。缺席、工具不存在、
檢查失敗與 PASS 必須使用不同出口；exit code 原樣傳到底。

目標 proof v2 以 module closure digest 作 validity key；repo commit/tree 保存 provenance。修改 module A 只使 A
與 transitive dependents stale，不得重寫無依賴關係的 module B receipt 來追隨 HEAD。

---

## 8. 模組衝突與 generated roots

1. 每個 tracked path 只能有一個 module owner。
2. Root projections 必須由 module fragments deterministic generation；module 禁止直接維護平行版本。
3. 跨 module 優先依賴 versioned capability，不依賴 private provider path。
4. Exclusive capability（signed-in browser、writer lease 等）同時只能有一個 active provider。
5. Runtime state 必須 namespaced：`data/module-runs/<module>/<run-id>/`。
6. 每個 entrypoint 使用 exact environment allowlist。
7. Embedded module 必須可抽出、安裝自己的 dependency、跑自己的 verify；禁向上解析 repo root。
8. Project 安裝走 `plan → resolve → render temp → verify → apply → receipt`，rollback fail closed。
9. 上一版 request corpus 必須對新 implementation 做 compatibility replay。

下列 root projections 在 generator 落地後不得手改：

```text
.mcp.json
.codex/config.toml
.agents/module-set.json
.agents/shared-skills.requirements.json
.runtime-env/requirements.json
loopctl/contract.json
```

---

## 9. Skills、runtime-env、origins 與 browser boundary

### Skills

- selected modules 對 required skills 求 requirements-filtered closure；
- shared 與 repo-owned 同名、或同名不同且不相容 bytes，composition RED；
- local symlink 綠不代理 immutable bundle 或 cloud availability。

### runtime-env

- 只同步 secret-free requirements/bindings/examples/workloads/policies；
- consumer pre-commit 不讀 sibling checkout、不連網、不自動 sync；
- secret、session、Keychain、browser profile 各有自己的 broker owner。

### GitHub / Forgejo

- Forgejo 是 local authoring origin；GitHub 是 cloud distribution origin；
- 兩者屬同一 logical release，不是 competing canonical；
- promotion 必須驗 `exact-commit`、`same-tree` 或 `same-release-manifest`；
- origin 不可達或 commit 不存在時，禁止 fallback 到 mutable `main`。

### Browser

必須分開 Actor、Product Surface、Transport、Session Owner、Workflow Capability 與 Evidence：

- Claude Code／Codex CLI／agy 是 actors；
- Playwright、stealth-browser、Antigravity CDP 是 transports/adapters；
- agy 是 independent replay actor，不持有 cookie；
- signed-in profile/session 不得 local→cloud file sync；
- `gemini-conversation-research` 正文 file-only；
- `dr-research-loop` 的 browser lane 是 optional Stage 1 raw input；
- `external-verify` raw primary first，browser fallback 必須標 evidence downgrade。

---

## 10. 外部專案初始化核心

外部 project 至少有兩種 preset：

- **Remote Consumer**：只安裝 consumer core，經 stateless MCP 使用 selected modules。
- **Embedded Module**：materialize immutable runtime/proof/fixtures，供離線、客製與 owner-level CI。

Claude Code / Codex CLI 必要 core：

```text
AGENTS.md + CLAUDE.md
bootstrap.sh
consumer requirements + lock
.agents/skills + binding
.claude/skills
.mcp.json
.codex/config.toml
consumer verifier
```

Core hard requirements 應縮小為 Git、POSIX shell、Python。Bun、uv、NotebookLM、browser、container、mobile
等由 selected module doctor 宣告；未安裝 module 的工具缺席不應讓 core bootstrap 失敗。

---

## 11. Agent Shield / PDF integration boundary

PDF 描述的 Agent Shield domain product 應由 `agent-shield-monorepo` 擁有；bettor-arena 只消費 selected
immutable module releases 並驗證 local/cloud、Skills、runtime、browser routes、origins、proof/control 與 rollback。

PDF parsing / document ingestion 是可獨立發布的 module，不代表整套 product。E2B、Firecracker、`<150ms`、
同步延遲、成本、授權與 provider capability 都是 research inputs；必須先走 `external-verify` 與 runtime canary，
才能升格為架構不變量。

Local/cloud 更新按 source、artifact、policy、image、memory、secret/session 分流；source code 禁止以
`newest wins`／`prefer cloud` 無條件覆蓋。

---

## 12. Agent completion contract

任何觸及此整合面的 Agent，收手前必須報告：

```text
changed module ids
changed interface versions
changed implementation / closure digests
affected transitive dependents
changed public CLI / MCP surface
path ownership conflicts
proof result
control result
mutation / hollow result
Claude adapter result
Codex adapter result
GitHub origin status
Forgejo origin status
dual-origin equivalence status
browser / live canary status
remaining NOT_IMPLEMENTED / NOT_EXERCISED
rollback subject
```

缺少適用項目，不得宣稱 modular integration complete。

---

## 13. 工程法則的實證歸屬（Rule → Evidence Routing）

全局工程法則不直接綁死在可能改名的 loop path；本節只路由到目前擁有實證的 repo-local Harness。
模組化 MVP 的完整要求與 current/target 差距以
`docs/architecture/modular-integration-requirements.md` 為準；八大基座的 worked evidence 目前由
`loop_wiki/evolve-perfect-seed-repo-factory/modules/eight-base-laws.md` 承載。

| 法則主題 | 實證 Harness |
|---|---|
| §4 觀測：綠燈值多少看抵達；兩種獨立抵達才 settled | `loop_wiki/evolve-perfect-seed-repo-factory/modules/eight-base-laws.md` 抵達分層表——訊號：想把 verify 綠讀成 seed 可升級；動作：查表，PROD 抵達未接即停在人閘；為何：SANDBOX 綠只證合成輸入。 |
| §4 觀測：量測工具該紅的時候真的會紅 | 同檔 B3 段——訊號：只有正控綠就想信儀器；動作：跑 `selftest.sh` hollow 負控＋`portability.sh` 雙負控；為何：工具的綠也是單一抵達的宣稱。 |
| §3 閘門：缺席≠否、狀態碼傳到底 | 同檔 B2 段——訊號：多段執行想彙報單一結果；動作：照 `trigger.sh` 分記各段 exit、早段非零→後段 `not_run`；為何：缺席偽裝成 fail／pass 都會扭曲路由。 |
| §2 構形：模組不向上依賴根目錄；搬一次真跑才算解耦 | 同檔 B5 段——訊號：想把原地會跑讀成可搬移；動作：跑 `portability.sh` 的抽出、安裝、verify 與負控；為何：上層 dependency／設定／深度假設只有離開根才爆。 |
| §7 邊界：共享 working tree 的暫存區是公共狀態 | 同檔 §7 段——訊號：多 session 同樹且 commit 被閘拒絕；動作：先退自己的 stage，排查後把 stage 與 commit 綁同一條命令；為何：失敗 commit 不回滾 `git add`。 |
| §6 落帳：推翻是時間線＋note 必填 | 同檔 B8 段——訊號：軌跡被後來證偽；動作：append note 記當初為什麼會信，禁改寫；為何：防重蹈的是誤信原因。 |

<!-- 目前 repo-local Harness：loop_wiki/evolve-perfect-seed-repo-factory。新增 module evidence 時，先更新 canonical requirement/manifests，再由 generator 更新本路由。 -->
