# Agent audit packet — bettor-arena module integration

> Review target: `feat/agent-module-set`。這是審計交接，不是完成宣告。
> Repository visibility requirement: GitHub `ed3c/bettor-arena` 必須保持 **PRIVATE**。

## Reviewer entry

依序讀：

1. `AGENTS.md`（薄入口；工程 SSOT 指到 `ARCHITECTURE.md`）
2. `ARCHITECTURE.md` §1–§3（模組化定義、槽位、不變量）
3. `docs/agent-runtime-integration.md`（跨三 repo 的具體契約）
4. `.agents/module-set.json`（機器可讀 aggregate interface）
5. 本檔（本次變更、實測與未實測）

不要把 `NOT_EXERCISED`、`hashed-not-run`、檔案存在或 auth status 讀成 live PASS。

## Audit question

此設計是否真的建立以下 closure，而沒有讓 consumer 依賴 sibling checkout、絕對機器路徑或 secret value？

```text
canonical SSOT
  -> module
  -> profile / collection
  -> consumer requirements (desired)
  -> resolved binding (commit/tree/digests)
  -> Claude/Codex adapter
  -> same-HEAD receipt
  -> independent planted-defect control
```

shared-skills 與 runtime-env 應共享這個治理 lifecycle，但不共享 transport：前者 local host 可用
symlink、sandbox/CI 用 immutable bundle；後者只同步 secret-free projection，禁止 symlink 整個 repo。

## Change inventory

| Surface | Purpose |
|---|---|
| `.agents/shared-skills.requirements.json` | bettor desired shared/repo-owned skill set 與 Claude/Codex surfaces |
| `.agents/bindings/bettor-arena.json` | skills-shared source commit/tree、requirements/registry/per-skill digests |
| `.runtime-env/requirements.json` | bettor desired runtime profile、精確 module closure、workload/policies |
| `.runtime-env/bindings/bettor-arena-local.json` | runtime-env v2 resolved module/interface/digest closure |
| `.agents/module-set.json` | 兩個上游 binding、兩個 carrier 與 live receipt 的 aggregate interface |
| `scripts/agent_runtime.py` | offline / adapter / strict 三層 verdict 與 opt-in live canary |
| `loopctl agent-runtime <run|prove|test>` | 外部唯一 public surface；surface version `2.8.0` |
| `proof_workflow/prove_agent_runtime.sh` | portable closure traversal proof |
| `proof_workflow/control_agent_runtime_entry.sh` | baseline + 缺 live + 四個 isolated planted defects |

Upstream implementation commits（目前是本機隔離分支 commit；未隨本 PR 發布到它們各自的 GitHub repo）：

- skills-shared `ad7acbf`：portable consumer binding + requirements digest。
- runtime-env `5b7c74d`：consumer requirements → `consumer-binding/v2` module closure。

因此 reviewer 可以完整審 bettor 的 requirements、resolved projections 與 aggregate mechanism，但若要逐行
審 upstream resolver source，必須另取得這兩個 commit；不能只靠 bettor 內的 binding 推論其實作正確。

## Claim matrix at handoff

| Claim | State | Evidence / blocker |
|---|---|---|
| Portable desired/resolved closure | PASS | `agent_runtime.py check --offline`; two upstream `sync --check` both UNCHANGED |
| runtime workload + three policy projections | PASS | `check_runtime_env_binding.py` worktree/selftest |
| loopctl surface/wiring | PASS | `loopctl.sh --selftest`; lock `2.8.0` |
| Agent-runtime proof/control at `fafe06c` | PASS | proof digest `abd7c6a5aad7`; baseline offline/adapter green; missing live remains exit 2; shared/runtime/Claude/Codex four defects each exit 2 |
| Local shared-skill adapter equals binding | **INCOMPLETE** | `forgejo-delivery-loop`、`html-for-decisions`、`shared-skills-infra` bytes differ on both carriers |
| Claude Code real canary at this HEAD | **NOT_EXERCISED** | adapter must first equal binding; no same-HEAD receipt |
| Codex CLI real canary at this HEAD | **NOT_EXERCISED** | same blocker; no same-HEAD receipt |
| “all local services integrated” | **FALSE / out of evidence** | service health、Forgejo、CDP、provider availability have separate owners and receipts |
| Upstream source publicly reviewable from this PR | **NO** | upstream commits are not in bettor repo and are not published by this handoff |

Full workflow re-stamp at `fafe06c` produced 11 receipts: 8 PASS and 3 retained RED。The RED receipts are
`micro`（missing iteration context and local `node_modules/.bin/prettier`）、`openwiki`（missing consumed
request artifact）、`equivalence`（legacy peer/live state NOT_EXERCISED）。They are unrelated to the portable
agent-runtime closure but remain publication evidence; the rebuilt workflow lock records their measured bytes and
must not be read as making those three traversals green。

The three adapter drifts are not auto-fixed because the canonical skills working tree contains user changes. Pointing
symlinks at `/private/tmp` or overwriting those changes would produce a temporary green while breaking the release model。

## Reproduce

```sh
# Portable closure (expected 0)
sh loopctl/loopctl.sh agent-runtime run --offline

# Synthetic independent control (expected 0; it requires planted checks to return 2)
sh loopctl/loopctl.sh agent-runtime test

# Existing runtime projection gate (expected 0)
python3 scripts/gates/check_runtime_env_binding.py

# Public surface lock (expected 0)
sh loopctl/loopctl.sh --selftest

# Strict current state (expected 2 until adapter promotion + live receipt)
sh loopctl/loopctl.sh agent-runtime run
```

Do not run `agent-runtime run --live` during a documentation-only audit. It spends two real model turns and is designed
to stop before spending when adapter bytes differ。

## Required review findings format

請 reviewer 以 severity 排序，每項至少含：

- violated invariant / threat
- exact file and line
- reproducible command or counterexample
- whether it blocks portable, adapter, live, or publication state
- smallest fix that preserves the deep-module interface

必答：

1. Binding 是否足以重建「哪個 source + 哪份 desired + 哪些 resolved bytes」？
2. shared/runtime 的 lifecycle 一致是否只停在文件，還是由 schema/CLI/control 真的綁住？
3. local symlink 與 immutable bundle 是否被錯誤混成同一 release channel？
4. strict verdict 是否存在任何把 missing/stale live receipt 讀成 PASS 的路？
5. staged-index pre-commit 是否已覆蓋 aggregate closure？若沒有，列為 publication blocker。
6. rollback、concurrent promotion、signature/attestation 與 module removal migration 還缺哪個最小機制？

## Known publication blocker

本 handoff 準備時，`gh auth status` 回報 `ed3c` keyring token invalid；GitHub repo 可讀為 PRIVATE，
但 default branch 為空且本地尚無 GitHub remote。完成 auth 與 remote 初始化前，不得宣稱已上傳或已建立 PR。
