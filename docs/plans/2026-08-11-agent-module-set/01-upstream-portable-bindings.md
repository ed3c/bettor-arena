# Slice 01 — upstream portable bindings

## Match

- `shared_skills.py install/check/link` 是現有 local-host adapter。
- `runtime-env sync` 已產 consumer binding/workload/policy，但 binding 尚未記 module closure。

## Generate

- skills-shared：新增 deterministic `consumer sync/check`，輸出 registry/source/skill digests，禁止絕對路徑。
- runtime-env：新增 requirements contract，binding 記錄 resolved module closure 與 per-module digest。
- 各 repo 加 Agent 可讀 Markdown，明示 lifecycle 與更新/rollback 邊界。

## Validate

Actor：兩個上游 CLI（deterministic）；validator：既有 shell test suite。

- clean fixture 正控。
- registry/module byte mutation → `--check` drift。
- missing skill/module → fail closed。
- relocation 後輸出不含 source checkout 絕對路徑。
- secret value 不得出現在任何 binding。
