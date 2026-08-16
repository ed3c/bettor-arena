# Bettor Arena Modular Integration Requirements — MVP Contract

> 狀態：**規範性目標契約（target contract）**。本文件描述 bettor-arena 下一階段模組化 MVP 的完整需求，
> 不代表文中所有 `.arena/` manifests、module-scoped receipts、project initializer 或 browser contract v2
> 已經存在。缺少實作或收據時，狀態必須是 `PLANNED`、`NOT_IMPLEMENTED` 或 `NOT_EXERCISED`，不得讀成 PASS。
>
> 工程事實與放置契約的最高權威仍是根目錄 `ARCHITECTURE.md`。本文件是其模組化整合需求的低壓縮展開；
> `AGENTS.md` 與 `CLAUDE.md` 只負責強制讀取順序與 host-specific 入口，禁止再複製一份平行規則。

## 0. 規範詞與完成邊界

本文件中的詞義：

- **MUST / 必須**：違反即 contract RED。
- **MUST NOT / 禁止**：出現即 fail closed。
- **SHOULD / 應**：偏離時必須留下具名理由與 receipt。
- **MAY / 可**：不構成 capability 宣稱。
- **PASS**：對應 assertion 已由指定 evidence level 實際抵達。
- **NOT_EXERCISED**：機制存在但本次未執行，永遠不是 PASS。
- **ABSENT**：能力、工具、輸入或 manifest 缺席；必須與檢查失敗分流。

Agent 宣稱「整合完成」前，必須同時說明：目前完成的是 requirement、implementation、offline proof、
adapter proof、live canary、production observation 中的哪一層。

---

## 1. Bettor Arena 的產品角色

bettor-arena 的 MVP 是下列五個角色的組合，不是把多個 scripts 放在同一 checkout：

1. **Module Host**：擁有 module catalog、composition、locks 與 release manifests。
2. **Loop Runtime**：以 `loopctl` 提供大小迴圈唯一 public CLI surface。
3. **Proof Kernel**：提供 proof、independent control、negative mutation 與 release evidence。
4. **Stateless MCP Gateway**：把 allowlisted CLI commands 封裝成 immutable、一次一 workspace 的 MCP tools。
5. **Project Bootstrapper**：讓外部專案按需安裝 module components、Claude Code/Codex CLI core 與 consumer locks。

### 非目標

- 不建立 generic shell-over-MCP。
- 不讓外部 caller 直接操作 module private executable 或任意 `cwd`。
- 不把 host credential、browser profile、cookie、OAuth session、Keychain value 或 `.env` 放進 Git、bundle、MCP payload 或 proof receipt。
- 不用 symlink 冒充 reproducible release。
- 不讓小迴圈直接 admission、promotion 或 production rollback；只能提交給 exact-subject automated controller。

---

## 2. Authority 與 Ownership

| Plane | Owner | 責任 | 不擁有 |
|---|---|---|---|
| Integration / Acceptance | `bettor-arena` | modules 組合、loop runtime、proof/control、stateless MCP、consumer bootstrap | 共用 Skill canonical body、secret values |
| Instruction | `skills-shared` | host-neutral `SKILL.md` body、共用 scripts/tests、skill release identity | repo-specific paths、consumer runtime values |
| Runtime Contract | `runtime-env` | variables、modules、profiles、fixed workloads、policies、secret-free projections | 任意 shell、consumer business code、credential values |
| Domain Product | 外部 owner repo，例如 `agent-shield-monorepo` | domain implementation 與自己的 module releases | bettor private implementation paths |
| Local Authoring Origin | Forgejo | 本機 issue/PR/milestone 與 authoring release | cloud distribution 的可達性宣稱 |
| Cloud Distribution Origin | GitHub | cloud/fresh-clone 可取得的 immutable release | local host session 或 localhost service |

一個事實只能有一個 SSOT。相同內容在不同 repo 出現時，必須是 canonical body、consumer binding、
immutable projection 或 generated adapter 其中之一，禁止兩個可獨立修改的同名 canonical。

---

## 3. 核心名詞

- **Module**：有單一 owner、明確 roots、public capabilities、dependencies、effects 與 proof contract 的版本化單位。
- **Component**：module 可按需安裝的部分，例如 `client`、`runtime`、`proof`、`fixtures`、`operator-skill`。
- **Capability**：跨 module 依賴的版本化介面，例如 `wiki-update-request.consume/v1`。
- **Public Port**：外界可依賴的 `loopctl` command、typed library API 或 MCP tool。
- **Private Internals**：private flags、internal scripts、prompt fragments、temp state、driver wiring 與 implementation paths。
- **Composition**：一個專案選定的 modules/components/capability providers 集合。
- **Composition Lock**：resolved versions、digests、Skills、runtime、origins、adapters 與 proof subjects 的 immutable 結果。
- **Logical Release**：可由一個或多個 origins 取得、由 release manifest 與 transitive closure digest 命名的發行物。
- **Receipt**：某次抵達的不可混同證據；不是需求文件，也不是永久 availability 保證。

---

## 4. 大迴圈與小迴圈

### 4.1 大迴圈（Macro / Composition Loop）

大迴圈擁有：

```text
需求
  → module/component selection
  → capability provider resolution
  → conflict detection
  → Skills/runtime/host projection generation
  → module proof matrix
  → automated admission
  → composition lock
  → release promotion / rollback
```

大迴圈只依賴：

- module manifests；
- composition requirements/locks；
- public capabilities；
- `loopctl` public ports；
- proof/control summaries；
- release/origin metadata。

大迴圈 **MUST NOT** 直接學習或呼叫另一 module 的 private flags、private scripts 或 per-run temp paths。

### 4.2 小迴圈（Micro / Task Loop）

小迴圈擁有：

- 一個 typed task；
- bounded internal iterations；
- 自己的 passive context；
- module-local runtime state；
- typed result、artifacts 與 named exits；
- module-local proof/control。

小迴圈可以直接讀自己的 `AGENTS.md`、`CLAUDE.md`、`PROMPT.md`、`ROUTES.md`、`PLAN.md`、
modules、source 與 executable。使用別的 module 時，只能經：

```text
typed packet
  → other module public port
  → typed result / artifact reference
  → receipt reference
```

禁止：

```text
source ../../other-module/private.sh
import ../../other-module/internal.py
Read ../../other-module/_engine-run/*
呼叫另一 module 的 private flag
```

### 4.3 共同不變量

- 大小迴圈共用同一套 Module Contract。
- 大迴圈看 manifests 與 evidence；小迴圈看自己的 implementation。
- 兩者的縫合面只能是 public interface、typed packet、artifact reference、exit code 與 receipt。
- automated admission、promotion、production rollback 只屬於大迴圈的 typed controller。

---

## 5. 模組消費模式與 Symlink 邊界

### 5.1 同一 module 內部

Module adapter 可以直接呼叫自己 closure 內的 executable 與文件；外界仍只看 public port。

### 5.2 同 repo 跨 module

使用 local `loopctl` 或 stable library API。即使兩個 module 在同一 repo，也不得以相對路徑耦合 private internals。

### 5.3 外部專案

- **Remote Consumer Mode**：外部專案只裝 consumer core，經 stateless MCP 呼叫 bettor modules。
- **Embedded Module Mode**：安裝 selected immutable module bundle，供離線、客製或 owner-level CI 使用。

### 5.4 Symlink 規則

Symlink 只允許作為：

- 本機 `skills-shared` development channel；
- `.agents/skills → .claude/skills` 的 passive instruction projection；
- module 自己可證明的 repo-local pointer。

Symlink **MUST NOT** 作為：

- 跨 repo executable dependency；
- cloud runtime dependency；
- `node_modules`、venv、browser profile 或 credential carrier；
- immutable release 或 provenance 證明。

固定口訣：

```text
Symlink = Local Development Channel
Bundle + Lock = Reproducible Execution Channel
CLI / MCP = Public Consumption Channel
```

---

## 6. Module Contract v1

目標位置：`.arena/modules/<module-id>/module.json`。

每個 module 至少宣告：

```json
{
  "schema": "bettor-arena/module/v1",
  "id": "perfect-seed-factory",
  "interface_version": "1.0.0",
  "implementation_version": "2026.08.11.1",
  "roots": ["loop_wiki/evolve-perfect-seed-repo-factory"],
  "components": {
    "client": {"required": true},
    "runtime": {"required": false},
    "proof": {"required": false},
    "fixtures": {"required": false}
  },
  "provides": [
    "seed-repo.build/v1",
    "wiki-update-request.produce/v1"
  ],
  "requires": [
    "arena.proof-kernel/v2",
    "arena.typed-packet/v1"
  ],
  "conflicts": [],
  "skills": {
    "required": [
      {"name": "loop-harness-standard", "interface": "loop-harness/v1"}
    ]
  },
  "runtime": {
    "required_profiles": ["bettor-arena-local"],
    "tools": ["bun"]
  },
  "loops": [
    {
      "id": "micro",
      "class": "micro",
      "interface_version": "1.0.0",
      "external_policy": "allowed-with-inline-bundle"
    }
  ],
  "effects": {
    "reads": ["typed input packet"],
    "writes": ["fresh output directory", "typed result packet"],
    "network": "driver-dependent",
    "secrets": "none"
  },
  "proof": {
    "spec": "proof_workflow/specs/perfect-seed-factory.json",
    "negative_controls": [
      "missing packet",
      "existing output path",
      "stale refs",
      "hollow generated repo"
    ]
  },
  "external_policy": {
    "exposed": true,
    "mutation": "disposable-worktree-only",
    "network": "none",
    "secrets": "none"
  }
}
```

### Interface 與 implementation 分離

下列修改通常不升 interface version：

- private driver 替換；
- source file 重構；
- prompt 內部改進；
- retry、timeout 或 private verifier 改善；
- internal directory 移動，但 public adapter 不變。

下列修改必須升 interface version：

- input/output schema 破壞性變更；
- named exit 語義改變；
- 新增 caller 必填旗標；
- write scope 擴大；
- read-only 變 mutation；
- artifact contract 改變；
- external network/secret boundary 放寬。

---

## 7. 目前模組的 MVP 對映

| Module ID | 現行 implementation | Class | 預設外部政策 |
|---|---|---|---|
| `arena-core` | root docs、bootstrap、hooks、loopctl core | Macro/Core | 不暴露 |
| `proof-kernel` | `proof_workflow/lib/*`、capture/compare | Core | 不暴露 |
| `mcp-gateway` | `loopctl/mcp_server.py`、`mcp_tools.py` | Core | server only |
| `shared-skills` | `.agents/*` + skills binding | Core | 不暴露 |
| `runtime-env` | `.runtime-env/*` | Core | fixed canaries only |
| `perfect-seed-factory` | `loop_wiki/evolve-perfect-seed-repo-factory/` | Micro | bounded run/prove/test |
| `openwiki` | `kb-ingest/` + `openwiki/` projection | Micro | prove/test；full mutation 不暴露 |
| `notebooklm` | `notebooklm/` | Micro | offline prove/test；authenticated run 預設不暴露 |
| `code-truth-graph` | `loop_wiki/code-truth-graph/` | Micro | inline bundle run/prove/test |
| `technical-equivalence` | `loop_wiki/evolve-technical-equivalence-research/` | Micro | offline prove/test；live 不暴露 |
| `container-runtime` | Dockerfile/container scripts | Provider | build/preflight 不暴露 |
| `agent-runtime` | `scripts/agent_runtime.py` | Aggregate | offline check 可；live 不暴露 |

這張表是 migration target。每個 row 只有在 module manifest、proof spec、control 與 lock 都落地後，
才能從文件分類提升為 machine-enforced module。

---

## 8. 雙層被動上下文與八大基座

### 8.1 大迴圈被動上下文

```text
AGENTS.md
CLAUDE.md
ARCHITECTURE.md
CONTEXT.md
modular-integration-requirements.md
composition requirements / lock
loopctl/contract.json
```

只承載全域 engineering invariants、module ownership、composition、release、automated admission 與 public surface。

### 8.2 小迴圈被動上下文

```text
<loop>/AGENTS.md
<loop>/CLAUDE.md
<loop>/PROMPT.md
<loop>/ROUTES.md
<loop>/PLAN.md
<loop>/modules/eight-base-laws.md
<loop>/module.json
<loop>/schemas/*
```

只承載該 task family 的 Goal、routes、state、actors、verification 與 packet contracts。

### 8.3 八大基座

| Base | Contract | 典型載體 |
|---|---|---|
| B1 Rules / Context | Agent 必須讀到的規則與 typed input | `AGENTS.md`、`CLAUDE.md`、packet |
| B2 Settings / Authorization | driver、permissions、runtime boundary | adapter flags、runtime policy |
| B3 Lifecycle / Observation | run state 與 evidence | receipt、`PLAN.md` |
| B4 Route Discovery | 失敗後去哪裡 | `ROUTES.md` |
| B5 Specialization | domain capability 與 router | module contract、domain skill |
| B6 Independent Verification | 另一種抵達 | verify、selftest、control、portability、人 |
| B7 Goal Contract | 不可漂移的任務目標 | `PROMPT.md` |
| B8 State Ledger | append-only trajectory | `PLAN.md`、composition ledger |

### 8.4 Context Capsule

目標位置：`.arena/contexts/<loop-id>/context.json`。Context Capsule 必須：

1. 列出 root 與 loop context files；
2. 驗證所有 bytes 來自 pinned release；
3. 一次 run 期間 digest 凍結；
4. 不向 owner live checkout 借內容；
5. 記錄 Claude/Codex driver profile；
6. 把實際 context digest 寫入 driver receipt。

MCP 封裝的不是任意 prompt，而是：

```text
resolve immutable release
  → materialize native context files
  → set cwd to loop root
  → launch claude -p / codex exec
  → validate typed output
  → emit context + driver receipt
```

---

## 9. CLI 與 Stateless MCP

### 9.1 CLI 是 canonical interface

```text
Module Contract
  → loopctl CLI Contract
  → generated MCP tools
```

禁止 CLI 與 MCP 各手寫一套 schema、flags 或 exit semantics。

### 9.2 MCP 預設拒絕

只有 `external_policy.exposed=true` 的 command 才能出現在 `tools/list`。缺少 external policy 時，預設不暴露。

每個 MCP call 必須：

- pin immutable commit/tag/logical release；
- 建立 fresh disposable worktree 或 immutable module bundle；
- 不讀 owner live checkout；
- 不接受 caller 指定 server-host absolute path；
- 只接受 typed packet、inline bundle 或 content-addressed artifact ref；
- 限制時間、input/output bytes、network 與 secrets；
- 返回 typed result、artifact digest 與 proof reference；
- 完成後清除 worktree、temp、process 與 lease。

### 9.3 小迴圈 MCP

小迴圈適合一個 bounded call：

```text
request bundle → isolated run → typed artifacts → cleanup
```

### 9.4 大迴圈 MCP

大迴圈禁止包成一個長連線 call。必須拆成 continuation packets：

```text
compose.plan
  → compose.resolve
  → compose.verify
  → compose.status
```

下列操作預設只能由 host/operator 提供不可推斷的輸入，或由具名 typed controller 依 exact-subject policy 執行；不可讓模型自行決定：

- apply 到外部 live repo；
- automated admission 中的執行邊；
- GitHub/Forgejo promotion；
- production rollback；
- secret rotation；
- permission widening。

---

## 10. Proof Workflow v2 與防抖動

### 10.1 Module-scoped subject

目標 receipt validity key：

```text
module manifest digest
+ module-owned files digest
+ direct dependency interface digests
+ proof spec digest
+ selected skill digests
+ selected runtime contract digests
```

Repo commit/tree 仍記錄 provenance，但不應讓無關 module 每次因 repo HEAD 移動而 stale。

### 10.2 每個 module 的五類 evidence

| Evidence | 必須回答 |
|---|---|
| `proof` | 宣稱哪些 context/harness/artifact 被走過 |
| `control` | 真從 public port 執行，實際 touched paths/exits 是否符合 |
| `mutation` / hollow | load-bearing guard 失效時套件是否真的變紅 |
| `consumer-canary` | 外部 Claude/Codex 經 released adapter 是否可達 |
| `release-receipt` | composition promotion 時所有 module evidence 是否同一 subject |

### 10.3 Named exclusions

每一個不執行、不 hash 或不納入 verdict 的項目，都必須留下理由。`NOT_EXERCISED`、`hashed-not-run`、
`absent`、`skipped-by-policy` 必須是不同狀態。

### 10.4 Global release receipt

只有 composition promotion 才要求全域 release receipt。Module A 改動只使 A 與 transitive dependents stale；
不依賴 A 的 module B receipt 不得被無關重寫。

---

## 11. 防止模組衝突的機械規則

1. **Single Path Owner**：每個 tracked path 只能由一個 module 擁有。
2. **Generated Root Projections**：`.mcp.json`、`.codex/config.toml`、`.agents/module-set.json`、
   Skills/runtime requirements、`loopctl/contract.json` 由 fragments 生成，module 不直接手改。
3. **Capability Dependency**：優先依賴 versioned capability，不寫死 provider module。
4. **Exclusive Capability Group**：signed-in browser、writer lease 等只能選一個 active provider。
5. **Typed Packet Boundary**：module 間只傳 packet、artifact ref、receipt ref。
6. **Exact Environment Allowlist**：每個 entrypoint 只收到自己宣告的環境變數。
7. **Namespaced Runtime State**：`data/module-runs/<module>/<run-id>/`，禁共用無 owner 的 output path。
8. **No Upward Dependency**：embedded module 必須可抽出、安裝自己的 dependency、跑自己的 verify。
9. **Transactional Install**：`plan → resolve → render temp → verify → apply → receipt`；rollback fail closed。
10. **Compatibility Replay**：上一版 request corpus 必須能由新 implementation 驗證相容性。

---

## 12. Skills-shared 與 runtime-env

### 12.1 Skills closure

每個 module 宣告 required/optional/repo-owned skills。Composition resolver 對 selected modules 求聯集：

- 相同 name + 相同 digest：合併；
- 不同 digest + 相容 interface：必須有 promotion proof；
- 不同 digest + 不相容 interface：composition RED；
- shared 與 repo-owned 同名：shadowing RED。

外部 project 與 sandbox 只 materialize requirements-filtered closure，不注入整座 `skills-shared/skills`。

### 12.2 Skills 雙通道

- Local development：clean/mutable canonical checkout + symlink。
- Immutable execution：clean source release + requirements-filtered bundle + consumer lock。

### 12.3 Runtime projection

`runtime-env` 只同步 secret-free binding/example/workload/policies。Pre-commit 只驗 consumer-local projections，
不讀 sibling checkout、不連網、不自動 sync。

### 12.4 Host adapters

Claude Code 與 Codex CLI 使用同一 module/skill lock，但 host projection 分開：

- Claude：`CLAUDE.md`、`.mcp.json`、`.claude/skills/*`；
- Codex：`AGENTS.md`、`.codex/config.toml`、`.agents/skills/*`。

Project trust、MCP approval、permissions、network、sockets 與 secret setup 永遠由人或 trusted host operator 擁有。

---

## 13. GitHub / Forgejo Multi-Origin Release

GitHub 與 Forgejo 是同一 logical release 的 origins，不是兩個 competing canonical：

```text
Logical Release
  ├── Forgejo local authoring origin
  └── GitHub cloud distribution origin
```

Binding 必須能表達：

- immutable repository identity；
- role（authoring / distribution）；
- scope（local-only / cloud）；
- commit/tree；
- release manifest digest；
- transitive module closure digest。

等價層級：

1. `exact-commit`；
2. `same-tree`；
3. `same-release-manifest`。

Gate 分工：

- pre-commit：offline integrity；
- local preflight：Forgejo origin reachability；
- GitHub CI/cloud：GitHub origin reachability；
- trusted promotion broker：dual-origin equivalence；
- runtime environment：adapter/live receipt。

Origin 不可達或 commit 不存在時，禁止靜默 fallback 到 mutable `main`。

---

## 14. Browser 模組化

Browser integration 必須拆成六層：

```text
Actor
  → Product Surface
  → Browser Transport
  → Session/Profile Owner
  → Workflow Requirements
  → Evidence Receipt
```

### Actors / surfaces / transports 不得混同

- `claude-code`：Agent actor；可經 Claude-in-Chrome 或 MCP broker。
- `codex-cli`：Agent actor；沒有 native desktop browser，經 MCP broker 使用 Playwright/stealth transport。
- Codex desktop/IDE：與 bare CLI 是不同 product surface。
- `playwright-cdp`：transport，不是 Agent。
- `stealth-browser-playwright`：transport + broker-owned profile contract。
- `antigravity-puppeteer-cdp`：specialized browser adapter。
- `agy`：independent replay/research actor，不持有 cookies，不是 browser transport。

Workflow capability 必須具體到：navigate、tab claim、signed-in session、submit、wait、DOM read、
extract-to-file、download、MCP control、content isolation、metadata receipt、cloud-safe。

### 三個 research Skills

- `gemini-conversation-research`：browser-required；正文 file-only，主 context 只收 bounded metadata receipt。
- `dr-research-loop`：核心 proposal loop browser-optional；Stage 1 subscription breadth lane 才 browser-required，輸出先標 UNTRUSTED raw。
- `external-verify`：raw HTTP / GitHub API / static primary first，browser 只是 fallback，必須記錄 evidence class 降級。

Browser profile、cookies 與 signed-in session 禁止由 local hot-sync 到 cloud。Cloud route 必須擁有獨立 session broker 與 live receipt。

---

## 15. 外部專案初始化

### 15.1 Remote Consumer Mode

必要 core：

```text
AGENTS.md
CLAUDE.md
bootstrap.sh
.arena/consumer.requirements.json
.arena/consumer.lock.json
.agents/skills + binding
.claude/skills
.mcp.json
.codex/config.toml
consumer verifier
```

Implementation 留在 bettor release；consumer 經 MCP 使用 selected loops。

### 15.2 Embedded Module Mode

除 consumer core 外，materialize selected immutable runtime/proof/fixtures。適合離線、domain retarget、
修改 module 或 consumer-owned CI。

### 15.3 Bootstrap transaction

```text
project plan
  → resolve
  → conflict report
  → render temp tree
  → verify
  → apply
  → append-only receipt
```

預設 dry-run。Rollback 只在 target bytes 未被後續修改時成功。

### 15.4 Core 與 module-specific tools

Core hard requirements 應縮小為 Git、POSIX shell、Python。Bun、uv、NotebookLM、browser、container、
mobile toolchain 等由 selected module doctor 宣告，不得因未安裝 module 的工具缺席而讓 core bootstrap 失敗。

---

## 16. Agent Shield / PDF 架構的整合位置

`agent-shield-monorepo` 擁有 PDF 所描述的 domain product：contracts、risk、wallet、mobile、dashboard、
document processing 與 cloud/local product runtime。bettor-arena 只消費 selected immutable module releases，
並驗證 local/cloud、Skills、runtime、browser routes、origins、proof/control 與 rollback。

「PDF parsing / document ingestion」是一個可獨立發布的 module；不代表整套 Agent Shield product。

來源 PDF 提出 E2B Serverless Firecracker MicroVM、每任務動態啟動 sandbox、OpenShell、tmux、VFS、
PDF parsing 與 local/cloud dual runtime。來源中的 `<150ms`、授權、成本、同步延遲與特定 provider capability
都是 research inputs，必須先經 `external-verify` 與 runtime canary，才能升格為 architecture invariant。

Local/cloud 更新按資料類型分流：

- source code：single-writer lease + branch/patch；
- generated artifacts：content-addressed store；
- policy：versioned `policy_epoch`；
- dependencies/OS：image/template rebuild；
- memory/DB：API/event/object store；
- secrets/browser session：broker only，永不 file sync。

禁止以 `newest wins` 或 `prefer cloud` 無條件覆蓋 source code。

---

## 17. Target Control Plane

目標增量，不要求第一步搬動既有 implementation roots：

```text
.arena/
├── schemas/
├── modules/<module-id>/module.json
├── contexts/<loop-id>/context.json
├── presets/
├── compositions/*.requirements.json
├── locks/*.lock.json
├── generated/
├── releases/
└── templates/
```

Root projections 由 `.arena/modules/*/fragments/` deterministic generation。既有 `kb-ingest/`、`notebooklm/`、
`loop_wiki/`、`proof_workflow/` 可先保留原位，以 manifest-first、move-later 遷移。

---

## 18. MVP 實作階段

### Phase 0 — Requirements 與 Source Truth

- 本文件、AGENTS/CLAUDE read order；
- GitHub/Forgejo logical release schema；
- 修復不可解析的 source pins；
- 建 remote provenance receipts。

### Phase 1 — Module Catalog

- module schema；
- current modules manifests；
- path ownership map；
- bettor composition requirements/lock；
- 由 fragments 重生現有 loopctl surface，結果必須 byte-compatible。

### Phase 2 — Module-scoped Proof v2

- closure digest；
- proof/control/mutation receipts；
- transitive invalidation；
- global release receipt。

### Phase 3 — Context Capsule 與 Driver CLI

- root/loop context manifests；
- `claude -p` / `codex exec` adapters；
- context/driver receipts；
- parity controls。

### Phase 4 — Stateless MCP Generalization

- external exposure default false；
- selected module closure only；
- generic typed inline carrier；
- no live dependency borrowing；
- cleanup controls；
- external consumer canary。

### Phase 5 — Project Initializer

- consumer-core / embedded-core presets；
- plan/apply/verify/rollback；
- generated Claude/Codex adapters；
- conflict and orphan projection gates。

### Phase 6 — Reference Consumer

以 `agent-shield-monorepo` 驗證 remote consumer、embedded module、browser workflows、GitHub cloud origin、
Forgejo local origin、local/cloud parity 與 rollback。

---

## 19. MVP Acceptance Criteria

以下全部成立才可宣稱 MVP 完成：

1. 修改 module A 不會讓無依賴關係的 module B closure receipt stale。
2. 修改 micro loop private driver 不會改變未升版的 external interface digest。
3. 新專案可由 `project plan/apply` 初始化，預設不寫檔。
4. Claude Code 與 Codex CLI 解析到同一 selected Skill bytes。
5. MCP tool list 與 CLI contract 一致，未明確 exposed 的 command 不出現。
6. Caller pin 舊 release 時，owner `main` 修改不影響執行。
7. 每個 MCP call 使用 fresh isolated worktree/bundle，結束後無殘留。
8. Caller 不能傳 server-host absolute path、private flag 或 mutable `HEAD`。
9. Module path conflict 在 apply 前被拒絕。
10. Remove/rollback 不留下 orphan projections，且 target drift 時 fail closed。
11. 每個 module 有 proof、control、mutation/hollow evidence。
12. `NOT_EXERCISED`、ABSENT、FAIL 與 PASS 不可互相代理。
13. GitHub cloud 與 Forgejo local origins 有 reachability 與 equivalence receipt。
14. Signed-in browser local route 不會把 profile/session 傳入 cloud。
15. 只有 composition promotion 才要求全域 release receipt 與 automated-admission receipt。

---

## 20. Agent Completion Report

任何觸及此整合面的 Agent，收手前必須報告：

```text
changed module ids
changed interface versions
changed implementation/closure digests
affected transitive dependents
changed public CLI/MCP surface
path ownership conflicts
proof result
control result
mutation/hollow result
Claude adapter result
Codex adapter result
GitHub origin status
Forgejo origin status
dual-origin equivalence status
live/browser canary status
remaining NOT_EXERCISED / NOT_IMPLEMENTED
rollback subject
```

缺少其中適用項目時，不得宣稱 modular integration complete。

---

## 21. Current-State Honesty

本文件落地時，現有可用基礎包括：

- `ARCHITECTURE.md` 的放置與大小迴圈鐵律；
- `loopctl/contract.json` 的 stable CLI surface；
- stateless MCP 的 immutable worktree 基礎；
- `proof_workflow` 的 traversal receipt 與 independent controls；
- `skills-shared` requirements/binding；
- `runtime-env` secret-free projection；
- Claude/Codex adapter 與 agent-runtime offline/adapter/live 分層。

仍屬 target、不能假裝已實作的主要項目：

- `.arena` Module Contract/Composition/Context Capsule；
- module-closure-scoped proof v2；
- project initializer；
- requirements-filtered generic module bundle；
- macro continuation-packet MCP；
- GitHub/Forgejo logical release equivalence；
- browser contract v2；
- cloud-independent signed-in browser broker；
- signed supply-chain attestation。
