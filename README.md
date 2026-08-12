# bettor-arena

> **Module Host + Loop Runtime + Proof Kernel + Stateless MCP Gateway + Project Bootstrapper**

`bettor-arena` 把原本散落在同一個 repository 的小迴圈，收斂成可組合、可證明、可發布的 modules。外部 consumer 只依賴穩定的 `loopctl`／MCP contract；內部 implementation 可以在不破壞既有 interface 的前提下快速迭代。

## Read order

1. [`ARCHITECTURE.md`](ARCHITECTURE.md) — engineering SSOT、placement contract 與最高優先級 invariants。
2. [`AGENTS.md`](AGENTS.md) 或 [`CLAUDE.md`](CLAUDE.md) — host-specific thin entrypoint。
3. [`docs/architecture/modular-integration-requirements.md`](docs/architecture/modular-integration-requirements.md) — normative target contract。
4. [`docs/architecture/modular-integration-status.md`](docs/architecture/modular-integration-status.md) — mutable implementation ledger。
5. [`.arena/README.md`](.arena/README.md) — machine-readable control plane 導航。
6. [`loopctl/README.md`](loopctl/README.md) 與 [`proof_workflow/README.md`](proof_workflow/README.md) — public surface 與 evidence semantics。

完整文件索引見 [`docs/README.md`](docs/README.md)。

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

The deterministic module catalog, ownership model, module-scoped proof identities, Context Capsules, default-deny Bun/TypeScript MCP runtime, project bootstrapper, logical-origin contract and Browser Contract v2 are present in the repository. Live Claude/Codex subscriptions, signed-in browser sessions, Forgejo/GitHub environment equivalence, cloud MicroVM providers and other external systems remain `NOT_EXERCISED` unless a current receipt says otherwise.

E2B／Firecracker and similar cloud runtimes are provider candidates, not Arena invariants. They enter the architecture only after independent license/spec verification and a runtime canary.
