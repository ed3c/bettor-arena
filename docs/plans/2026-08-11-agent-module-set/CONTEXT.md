# CONTEXT — 2026-08-11 agent module set

## Repositories and branches

- bettor-arena: `feat/agent-module-set`, based on authoritative Forgejo `main`.
- runtime-env: `feat/modular-consumer-runtime`, based on `origin/main`.
- skills-shared: `feat/portable-consumer-bindings`, based on committed `main`; canonical dirty user edits remain outside this worktree.

## Terms

- canonical SSOT：上游唯一內容真源。
- requirements：consumer 的 desired state；只說需要的能力/集合，不假裝已解析。
- binding：resolver 產生的 resolved state，固定 source commit/tree 與內容 digest。
- projection：可提交、無 secret、可離線驗的 consumer artifact。
- adapter：把 binding 接到 Claude/Codex/local/sandbox 的 host-specific 實作。
- module set：bettor 對兩個上游 binding 與兩個 carrier surface 的聚合清單。
- receipt：一次正控遍歷的機器證據。
- control：獨立植入缺陷、要求判決真的轉紅的對照組。

## Known absences

- localhost Forgejo 與 research CDP 並非本次必然在線。
- Claude/Codex subscription canary 會花 token，預設不執行。
- OpenShell provider 的存在與可用性屬 host state，不可由 JSON policy 推論。
- 所以「離線集合完整」與「live carriers exercised」是兩個不同判決。
