# Intent and know-how

## Intent

讓 `bettor-arena` 消費兩個可獨立演進的上游模組：`skills-shared` 與 `runtime-env`。
Agent 在新 chat 讀到 repo 的被動上下文後，能找到一個穩定入口，知道哪些能力已鎖定、
哪些 host adapter 已接、哪些 live seam 還沒被實際執行。

完成不等於「檔案存在」。本線的完成定義是：

1. 上游 canonical 有明確 interface 與 deterministic consumer projection。
2. bettor 只依賴投影，不依賴本機 sibling checkout。
3. Claude Code 與 Codex CLI 的發現面分開驗證，任一缺席都使集合不完整。
4. proof receipt 與獨立 planted-defect control 成對存在。
5. `NOT_EXERCISED`、`failed`、`passed` 三態不壓成布林綠燈。

## Brownfield invariants

- `skills-shared/registry.json` 只放裁決，禁止絕對機器路徑；`sites.local.json` 才持有 host 路徑。
- shared skill 一名只可有一份 canonical body；repo 只能持有 pointer 或明確 repo-owned body。
- `runtime-env` 的 catalog、module、profile、workload、policy 都不可持有 secret value；同步要求乾淨 Git source。
- consumer pre-commit gate 零網路、不得讀 sibling checkout；upstream freshness 是顯式 maintenance action。
- bettor 的對外 loop surface 由 `loopctl/contract.json` 宣告並以 `surface.lock` 鎖定。
- proof 的 `hashed-not-run` 與 live `NOT_EXERCISED` 都不是成功。

## Interface comparison

### A. 整 repo symlink 到 bettor（拒絕）

介面寬、隱含本機絕對路徑、CI/sandbox 無法重現；上游工作樹 dirty 時 consumer 也說不清版本。

### B. 複製上游內容進 bettor（拒絕）

短期可跑，長期必分岔；`skills-shared` 的 single-body rule 直接被破壞。

### C. desired requirements + resolved binding + carrier adapter（採用）

consumer 宣告需要什麼，上游 resolver 產出 commit/tree/digest 綁定；local adapter 可用 symlink，
sandbox/CI adapter 用 immutable bundle。介面小，兩個 transport 都能被獨立測試，形成真 seam。

## Deep-module boundary

`agent-runtime check` 是 bettor 對 Agent 的單一集合介面。它隱藏兩種上游 transport 與 host
差異，但不隱藏驗收狀態；輸出必須保留 `passed / failed / not_exercised`。
