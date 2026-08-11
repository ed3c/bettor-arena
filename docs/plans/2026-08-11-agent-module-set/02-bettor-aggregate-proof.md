# Slice 02 — bettor aggregate interface and proof

## Match

- `check_runtime_env_binding.py` 已能離線驗 runtime projection。
- `loopctl` 已有 contract/surface lock。
- `proof_workflow/lib/prove.sh` 與各 control 已提供 receipt/control 模式。

## Generate

- `.agents/module-set.json`：列出 skills/runtime bindings、Claude/Codex surfaces 與 live canary states。
- `scripts/gates/check_agent_module_set.py`：集合 closure 的單一離線閘。
- `loopctl agent-runtime <run|prove|test>`：穩定操作面。
- `prove_agent_runtime.sh` 與 `control_agent_runtime_entry.sh`：正控與植入缺陷負控。
- `docs/agent-runtime-integration.md`：Agent 的具體需求、更新與判決語義。

## Validate

Actor：Claude Code / Codex CLI（live opt-in）；deterministic actor：aggregate gate。

- T0：兩個 binding、兩個 carrier surface、workload/policy closure 都存在且 digest 正確。
- control：各自破壞 shared binding、runtime binding、Claude surface、Codex surface，四案都必紅。
- live 未跑：整體狀態 `incomplete`，不可 PASS。
- live 真跑且兩者各有 receipt：才可宣稱「無斷點 carrier integration exercised」。
