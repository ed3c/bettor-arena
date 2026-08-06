---
description: forgejo-delivery-loop 轉發層——四層原生追蹤面（PRD issue→slice issues→PR→milestone）的狀態、切線、issue 循環與收據同步入口
argument-hint: "[<line-id> | run <line-id> | sync <line-id> [--dry-run] | new-line <line-id>]"
allowed-tools: Bash(python3 scripts/gates/check_delivery_receipt.py:*), Bash(python3 scripts/delivery_status.py:*), Bash(python3 scripts/delivery_sync.py:*), Read, Glob, Grep
---

用 Skill 工具載入 `forgejo-delivery-loop`，然後按 `$ARGUMENTS` 分派（本檔零邏輯，程序 SSOT＝
`.agents/skills/forgejo-delivery-loop/SKILL.md` ＋ `modules/delivery-mechanism.md`；本 repo 的活錨＝
PRD http://localhost:3000/neon/bettor-arena/issues/2 與 milestone /milestone/1）：

- **無參數**：兩支各答一半，都要跑——`python3 scripts/gates/check_delivery_receipt.py`（收據閘，
  零網路，答「交付證據在不在、形狀對不對」）＋ `python3 scripts/delivery_status.py`（顯式審計，
  打網路，答「此刻真實狀態」：每線 PRD／open slices／open PRs／milestone 完成率／plan 位址）。
- **`<line-id>`**：`check_delivery_receipt.py --line <line-id>` 取登記上下文，`delivery_status.py --line <line-id>` 取活狀態——
  這是切工作面開工前的定向步驟。
- **`run <line-id>`**：進入 SKILL.md「未完成項執行循環」：goal 鎖線 → 每張 open issue：隔離工作面 →
  /tdd 實作 → /code-review → PR body 寫 `Closes #N`（merge 留給人）；漂移或新發現一律開新 issue
  掛同 milestone，不夾帶進進行中的 PR。
- **`sync <line-id>`**：`python3 scripts/delivery_sync.py --line <line-id>`——從 forge 現況重寫
  `delivery.json` 的四層位址與 commit 戳，**寫完立刻跑收據閘**（閘紅＝這次 sync 不算數）。
  先看不寫加 `--dry-run`。手改收據會漂，所以這步有工具而不是散文。
- **`new-line <line-id>`**：按 modules §6 的鋪法開新線：PRD issue → slice issues（`## Parent` 回鏈＋
  checkbox＋`Blocked by`）→ 掛 milestone → `registry.json` 登記。

Forgejo API 一律透過既有 git credential helper 在記憶體取憑證；秘密不落盤不輸出
（`check_credential_hygiene.py` 守）。禁用雲端 GitHub 與 `gh` CLI——本 repo 的追蹤面只在
`http://localhost:3000`（人裁 2026-08-06）。

$ARGUMENTS
