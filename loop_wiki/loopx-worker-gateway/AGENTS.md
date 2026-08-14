# AGENTS.md — LoopX Worker Gateway

Read [`CONTEXT.md`](CONTEXT.md) and [`README.md`](README.md) before changing this module.

Rules:

1. Keep the six static host manifests contract-only and `NOT_EXERCISED` until an exact live receipt exists.
2. Use typed executable + `argv[]`; raw shell text, `shell=True`, arbitrary host paths and secret values are forbidden.
3. A Worker may modify only its leased disposable workspace and submit observations/artifacts.
4. The gateway cannot write LoopX task state, Gate verdicts, Human decisions, durable memory, promotion or rollback.
5. Gray-box internal calls remain `UNKNOWN`; never infer them from prose or stdout.
6. `OBSERVED_SUCCESS` is only a process/filesystem observation. Independent Gates and the LoopX reducer remain separate.
7. Physical network/filesystem isolation belongs to runtime-fabric. The host-local gateway must not claim it.
8. Every change needs the positive fixture and a planted control capable of turning the relevant claim red.
9. Do not select this module into the shared composition or expose it through MCP in this terminal leaf.
10. Do not merge, promote or Human Admit from an Agent session.
