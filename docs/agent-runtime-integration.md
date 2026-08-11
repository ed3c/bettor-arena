# Agent runtime integration — concrete contract

這是 Claude Code 與 Codex CLI 在 bettor-arena 消費目前已落地 Skills/runtime module-set 的低壓縮入口。
新 chat 從 `AGENTS.md → ARCHITECTURE.md → docs/architecture/modular-integration-requirements.md → 本檔`
到達；`AGENTS.md`／`CLAUDE.md` 在 chat 啟動時載入，改檔後要開新 chat。

本檔描述**現行可執行介面**；`docs/architecture/modular-integration-requirements.md` 描述下一階段 Module Host、
Loop Runtime、Proof Kernel、Stateless MCP Gateway 與 Project Bootstrapper 的 target contract。Target 中尚未
落地的 `.arena/` manifests、module-scoped proof v2、Context Capsule、project initializer、multi-origin release
與 browser contract v2，不得由本檔目前的 offline/adapter 綠燈代理。

## Architecture

```text
skills-shared canonical ──> shared requirements ──> shared binding ─┐
                                                                   ├─> module-set ─> Claude/Codex adapters ─> live receipt
runtime-env catalog ──────> runtime requirements ─> runtime binding ┘
                                                        └────────────> workload + policies
```

治理機制相同：canonical → module → collection → requirements → resolved binding → adapter →
receipt/control。transport 不同：shared skills 的 local adapter 是 symlink、sandbox 是 commit bundle；
runtime-env 只同步 secret-free projection，整個上游 checkout 與 `.env` 都不進 consumer。

## Files and interfaces

| Interface | Desired | Resolved / implementation |
|---|---|---|
| shared skills | `.agents/shared-skills.requirements.json` | `.agents/bindings/bettor-arena.json` |
| runtime modules | `.runtime-env/requirements.json` | `.runtime-env/bindings/bettor-arena-local.json` + workload/policies |
| aggregate | `.agents/module-set.json` | `python3 scripts/agent_runtime.py check` |
| public CLI | `loopctl/contract.json` | `sh loopctl/loopctl.sh agent-runtime <run|prove|test>` |
| evidence | proof traversal | `proof_workflow/prove_agent_runtime.sh` + `control_agent_runtime_entry.sh` |

## Verdict levels

- `run --offline`：requirements、bindings、module closure、workload/policies 與 digest 全閉包。綠不代表 host adapter 或 model turn。
- direct `check --adapter`：再要求 Claude/Codex 兩個 skill surface 的實際 bytes 等於 binding。
- `run`：strict；再要求同 HEAD/tree/module-set/binding 的雙 lane live receipt。receipt 缺席或 stale 都 exit 2。
- `run --live [--force-receipt]`：adapter 綠後才花兩個真 model turn，輸出只記 exit 與是否看到 `OK`，不保存 model output 或 credential。

`NOT_EXERCISED` 永遠不是 PASS。現在 portable offline closure 可以獨立驗證；只有 strict 綠才可說
「這個 commit 的 Claude Code 與 Codex CLI 無斷點執行已被實測」。

## Update workflow

1. 在上游 repo 改 canonical 並提交；dirty source 不能 sync。
2. 更新 consumer requirements；從該 clean upstream 執行 `sync` dry-run。
3. review resolved binding 的 source commit/tree、requirements digest、module/skill digests。
4. `--apply` 後跑 `agent-runtime run --offline` 與 `agent-runtime test`。
5. 把上游 commit promotion 到實際 canonical host；再跑 adapter check。
6. 有意花費兩個 canary turn 時跑 `agent-runtime run --live`；最後 strict `agent-runtime run`。
7. 產 proof/control receipt、stage 全 closure、過 pre-commit，才提交 bettor。

Rollback 不手改 binding：checkout 上游舊 clean commit，用同一 requirements 重 sync。private publication
是 delivery policy，不是 module contract；本線不 push，也不把 remote visibility 改成 public。

## Risks that must stay explicit

- symlink 是 development channel，不是 immutable release；canonical dirty 時 local surface 可能先於 binding 漂移。
- binding 固定 bytes，但還沒有簽章/attestation；Git object id 是 identity，不是供應鏈信任的全部。
- 多 repo promotion 尚無原子 transaction；任一 repo merge 一半時 strict gate 應紅，不能自動回滾別 repo。
- requirements 刪除 module 需要 migration/deprecation review；digest freshness 本身不知道 consumer 是否仍在用舊能力。
- live receipt 有時效與費用；同 HEAD receipt 證一次抵達，不證外部 provider 永久可用。
- secret rotation、host service health、Forgejo/CDP availability 各有 owner；它們不能被 module binding 的綠代理。
