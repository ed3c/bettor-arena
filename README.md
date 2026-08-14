# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 把原本散落在同一個 repository 的小迴圈，收斂成可組合、可證明、可發布的 modules。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 可以在不破壞既有 interface 的前提下快速迭代。

## Read order

1. [`ARCHITECTURE.md`](ARCHITECTURE.md) — engineering SSOT、placement contract 與最高優先級 invariants。
2. [`AGENTS.md`](AGENTS.md) 或 [`CLAUDE.md`](CLAUDE.md) — host-specific thin entrypoint。
3. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md) — normative target contract。
4. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md) — mutable implementation ledger。
5. [`docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md`](docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md) — 《黑客松 AI 開發：SKILL.md 與 MCP》需求→模組/State Machine/evidence 對照與修正。
6. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md) — same-name State Machine routing summary。
7. [`.arena/README.md`](.arena/README.md) — machine-readable control plane 導航。
8. [`loopctl/README.md`](loopctl/README.md) 與 [`proof_workflow/README.md`](proof_workflow/README.md) — public surface 與 evidence semantics。

完整文件索引見 [`docs/README.md`](docs/README.md)。

## Directory topology → State Machine ownership

```text
bettor-arena/
├── .arena/
│   ├── modules/            MODULE LIFECYCLE + path/capability ownership
│   ├── compositions/       MACRO requirements
│   ├── locks/              immutable composition result
│   ├── contexts/           Context Capsule inputs
│   └── mcp-policy.json     MCP exposure allow/deny state
├── .skill-bindings/        SKILL CONSUMER BINDING state
├── .agents/skills/         repository-owned/projected Skill support material
├── .runtime-env/           secret-free runtime projection
├── loopctl/                PUBLIC PORT + STATELESS MCP state machine
├── proof_workflow/         PROOF / CONTROL / MUTATION state machine
├── knowledge-providers/    PROVIDER candidate/query/memory state
├── data/
│   ├── module-proof/       module subject + release evidence
│   ├── mcp/                MCP exposure snapshots
│   ├── origins/            GitHub/Forgejo observation state
│   └── browser/            browser/provider observation state
├── scripts/                trusted deterministic reducers and gates
├── docs/                   Agent/human routing; never machine authority
└── AGENTS.md               mandatory Agent route + non-negotiable boundaries
```

## Runtime topology

```text
Claude Code / Codex CLI
        │
        │ JSON-RPC / stdio, immutable release
        ▼
Stateless MCP Gateway
        │ selected module closure + typed carrier
        ▼
Module Public Port
        │ stable interface_version
        ▼
Bounded Micro Loop
        │ typed result + named exits + artifacts
        ▼
Proof Kernel
        └─ proof + independent control + mutation/hollow evidence
```

Arena 的 Macro／Composition loop 只負責 module selection、dependency/conflict resolution、projection、proof matrix、Human Admit、composition lock、promotion 與 rollback。Micro loop 只處理 bounded task execution，不能自我 admit、promote 或執行 production rollback。

## End-to-end integration data flow

```text
skills-shared immutable Skill release
        +
runtime-env secret-free binding/profile/workload
        ↓
.skill-bindings + .arena module requirements
        ↓
Macro resolver
        ↓
composition lock + selected module closure
        ↓
Context Capsule / host projection
        ↓
loopctl public contract
        ↓
default-deny Stateless MCP
        ↓
typed Skill execution request
        ↓
execution provider
(local disposable process / future admitted cloud sandbox)
        ↓
OS + artifact observations
        ↓
independent assertions
        ↓
proof + control + mutation/hollow receipts
        ↓
external Claude/Codex/provider canaries
        ↓
composition release receipt
        ↓
Human Admit
        ↓
promotion or rollback
```

## PDF architecture integration verdict

The PDF is treated as a **requirement/hypothesis source**, not factual authority. Bettor adopts the useful architecture while correcting unsafe assumptions. See [`PDF_SKILL_MCP_TRACEABILITY.md`](docs/architecture/PDF_SKILL_MCP_TRACEABILITY.md).

| PDF concept | Bettor mapping | State |
|---|---|---|
| SKILL.md capability boundaries | `skills-shared` release + `.skill-bindings/` | contract implemented |
| dynamic tool discovery | `loopctl` public surface + `.arena/mcp-policy.json` | implemented, default deny |
| stateless MCP | Bun/TypeScript MCP runtime | implemented for admitted carriers |
| isolated code execution | portable Skill execution stack | stack implemented, convergence to current `main` pending #53 |
| E2B/Firecracker | execution-provider candidate | not an invariant; not exercised |
| browser automation | Browser Contract v2 | deterministic contract present; live provider subject-specific |
| Skill Arena evals | proof/control/mutation + Skill/provider evals | deterministic contract implemented |
| Self-Healing | bounded Micro recovery + named exits | bounded only; retry-until-pass forbidden |
| Promptfoo runtime governance | rejected as runtime authority | offline/CI adapter only if admitted |
| Human-in-the-loop | Human Admit | explicit non-tool authority |

No example success rate, latency, user count, market share or YC claim from the PDF is copied into repository truth without independent evidence.

## Stable public surfaces

### `loopctl`

```sh
sh loopctl/loopctl.sh contract
sh loopctl/loopctl.sh --selftest
```

`loopctl/contract.json` 是 canonical external surface；`loopctl.sh` 是 wiring。Private flags、driver、prompt、implementation directory 與 temporary files 不是外部 contract。

### Stateless MCP

MCP tools 由 canonical contract 與 `.arena/mcp-policy.json` 生成，採 **default deny**。每次 call pin immutable subject、只 materialize selected module closure，並使用 disposable workspace。Caller 不得傳 server-host absolute path、任意 `cwd`、secret、browser profile 或 generic shell command。

### Project bootstrapper

```sh
bun scripts/arena_project.ts --help
bun scripts/gates/check_project_bootstrap.ts
```

Project initialization 採 `plan → resolve → render temp tree → verify → apply → receipt`。Rollback 只允許在 target bytes 未被後續修改時執行。

## Module and evidence model

- Module manifests： [`.arena/modules/`](.arena/modules/)
- Composition requirements： [`.arena/compositions/`](.arena/compositions/)
- Deterministic lock： [`.arena/locks/`](.arena/locks/)
- Context Capsules： [`.arena/contexts/`](.arena/contexts/)
- Module proof subjects： [`data/module-proof/`](data/module-proof/)
- MCP exposure snapshot： [`data/mcp/`](data/mcp/)
- Origin / browser status： [`data/origins/`](data/origins/) / [`data/browser/`](data/browser/)

Evidence states are not aliases:

```text
PASS ≠ FAIL ≠ ABSENT ≠ NOT_IMPLEMENTED ≠ NOT_EXERCISED
```

A receipt is a claim. A control must execute the public port and observe behavior. A mutation or hollow control must prove that a load-bearing guard can turn red。

## Git Town / molecular Stack PR index

Git Town is optional local tooling; **GitHub base/head metadata is publication truth**. A child PR that says `merged=true` may have merged only into its parent branch. That does not mean its bytes are on `main`.

### Portable Skill execution stack

```text
main
└─ #43 repo-agent-native Bettor binding                     MERGED TO MAIN
   └─ #48 harness-wiki portable execution contracts         MERGED INTO STACK PARENT
      └─ #50 host-owned executable Skill runner             MERGED INTO STACK PARENT
         └─ #52 provider-neutral knowledge boundary         MERGED INTO STACK PARENT
            └─ #53 portable-skill-execution convergence     OPEN / DIVERGED FROM MAIN
```

**Current integration authority:** #53 must be rebuilt or synchronized with current `main`, rerun exact-head gates, then merged before #48/#50/#52 are described as integrated into `main`.

### Knowledge-provider admission leaf

```text
main
└─ #56 provider admission packets/evals   OPEN
```

#56 currently has failing exact-head GitHub checks, so it is not merge-authorized. Its checked-in observations are fixture-only and cannot establish Serena/GrepAI/Code-Graph-RAG/Mem0 live health or superiority.

When Git Town is installed locally, use it only to manage the same dependency graph; never let local stack metadata override GitHub parent/base identity or exact-head checks.

## Local verification

```sh
python3 scripts/gates/check_readme_coverage.py --selftest
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_proof.py check
python3 scripts/arena_context.py check
bun scripts/gates/check_mcp_policy.ts
bun scripts/gates/check_project_bootstrap.ts
bun scripts/gates/check_environment_contracts.ts
```

Run `sh bootstrap.sh` once to install repository-relative hooks and perform the core doctor checks. Host trust, MCP approval, network widening, browser sign-in and secret-bearing providers remain human-owned activation steps.

## Current boundary

The deterministic module catalog, ownership model, module-scoped proof identities, Context Capsules, default-deny Bun/TypeScript MCP runtime, project bootstrapper, logical-origin contract and Browser Contract v2 are present in current `main`.

The portable Skill execution + knowledge-provider stack is **not yet fully converged into current `main`**: #53 is the open convergence leaf. Provider admission #56 is also open and currently has failing exact-head checks. These states must not be hidden by the fact that intermediate stacked child PRs show as merged.

Live Claude/Codex subscriptions, signed-in browser sessions, Forgejo/GitHub environment equivalence, cloud MicroVM providers and other external systems remain `NOT_EXERCISED` unless a current receipt says otherwise.

E2B／Firecracker and similar cloud runtimes are provider candidates, not Arena invariants. They enter the architecture only after independent license/spec verification and a runtime canary.
