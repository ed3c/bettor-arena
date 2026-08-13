# Agent runtime integration — concrete contract

這是 Claude Code 與 Codex CLI 在 bettor-arena 消費目前已落地 Skills/runtime closure 的低壓縮入口。
新 chat 從 `AGENTS.md → ARCHITECTURE.md → CONTEXT.md → docs/README.md →
docs/agents/domain.md → modular-integration-requirements.md → modular-integration-status.md → 本檔`
到達；`AGENTS.md` 在 chat 啟動時載入，Skill discovery 與 passive context 也具 session scope，改檔後要開新 chat。

完整 Module Platform 的 target contract 在
`docs/architecture/modular-integration-requirements.md`；目前已落地與尚未實作的層級以
`docs/architecture/modular-integration-status.md` 為準。本檔只描述現有
skills-shared/runtime-env module-set 的可執行契約，不能代理後續 phases。

## Architecture

```text
skills-shared canonical ──> shared requirements ─> shared binding ─┐
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
| repository analysis | `.skill-bindings/repo-agent-native/binding.json` | shared `repo-agent-native` projection + consumer binding gate |
| domain policy | `CONTEXT.md`, optional `CONTEXT-MAP.md`, applicable ADRs | `docs/agents/domain.md` + nearest README |

## Repository-analysis Skill route

`repo-agent-native` is the portable procedure for source-anchored brownfield understanding. Its shared body lives once in
`skills-shared`; Bettor owns only the consumer binding and provider observations.

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ docs/agents/domain.md
→ applicable docs/adr/
→ nearest directory README.md
→ .skill-bindings/repo-agent-native/README.md
→ projected shared repo-agent-native README/SKILL.md
→ matching capability modules only
→ manifest/public contract/source/tests/receipts
→ exact issue and PR
```

Current provider roles remain distinct:

| Capability | Current Bettor state | Evidence ceiling before readback |
|---|---|---|
| exact source | built-in `git`/`rg`/direct read | `A` only after current source body read |
| semantic candidates | GrepAI declared, host executable unpinned | `B+` candidate |
| bounded Python context | repo-context-pack declared | `B+`; cannot prove absence |
| symbols/references/diagnostics | Serena declared at an exact Git pin | `A-` only after source/workspace readback |
| cross-language graph | Code-Graph-RAG candidate, not configured | `B+` candidate after future admission |
| project/session memory | Mem0 candidate, not configured | advisory hint, never repository authority |

Configuration presence is not provider health. Index freshness, LSP initialization, graph coverage, memory provenance, Claude/Codex output quality, and physical current-versus-candidate A/B remain `NOT_EXERCISED` until current subject-bound receipts exist.

The binding gate is:

```bash
python3 scripts/gates/check_repo_agent_native_binding.py --selftest
python3 scripts/gates/check_repo_agent_native_binding.py
```

It verifies symlink projection rather than a shadow copy, document-route closure, provider config agreement, exact Serena pin, candidate-provider absence, evidence ceilings, fallbacks, and planted failures.

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

For `repo-agent-native`, also update the exact shared candidate commit in its consumer binding, rerun the binding selftest, open fresh Claude/Codex sessions, and execute the four-condition physical A/B contract before claiming output superiority.

Rollback 不手改 binding：checkout 上游舊 clean commit，用同一 requirements 重 sync。private publication
是 delivery policy，不是 module contract；本線不 push，也不把 remote visibility 改成 public。

## Risks that must stay explicit

- symlink 是 development channel，不是 immutable release；canonical dirty 時 local surface 可能先於 binding 漂移。
- binding 固定 bytes，但還沒有簽章/attestation；Git object id 是 identity，不是供應鏈信任的全部。
- 多 repo promotion 尚無原子 transaction；任一 repo merge 一半時 strict gate 應紅，不能自動回滾別 repo。
- requirements 刪除 module 需要 migration/deprecation review；digest freshness 本身不知道 consumer 是否仍在用舊能力。
- live receipt 有時效與費用；同 HEAD receipt 證一次抵達，不證外部 provider 永久可用。
- GrepAI 目前從 host `PATH` 啟動；未有 executable/package pin 前不得稱可重現 provider identity。
- Code-Graph-RAG 的標準 MCP 面含 write/delete/wipe/index 操作；未有 read-only wrapper 與 store isolation 前不得啟用。
- Mem0 需要 LLM/embedding/storage、retention、provenance、redaction、expiry、delete/export 與 conflict policy；未有契約前不得自動寫回。
- secret rotation、host service health、Forgejo/CDP availability 各有 owner；它們不能被 module binding 的綠代理。
