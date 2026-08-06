# Forgejo loop contracts

## 分工

| 層 | owner | 可以做 | 不可以做 |
|---|---|---|---|
| 大迴圈 | `forgejo-loop-ops` | 優先序、WIP、降級、下一個小迴圈提示 | 批次 mutation、repo 寫入、admission |
| 小迴圈外部操作 | `forgejo-loop-ops` + existing Chrome | 單一 issue／PR／merge 的預檢、操作、回讀 | 改 source、跳 gate、複製私密語料 |
| repo 末端實作 | output repo 的 `repo-terminal-operator` | terminal slice、CQ、production-use、commit | Forgejo／GitHub／cloud admission |
| 中央契約 | `skills/repo-neural-perception` | schemas、capability policy、typed receipts | repo 專屬實作 |

## 資料流

```text
grill／DR／GCR decision
  -> large-loop queue projection
  -> one typed Forgejo request
  -> existing Chrome auth or read-only API preflight
  -> one repo-local terminal operator
  -> focused CQ + production-use + molecular commit
  -> issue／PR／merge readback
  -> neural preview／canonical receipt
  -> human admission
  -> next-mode prompt
```

## 既有契約

- `skills/repo-neural-perception/schemas/forgejo-terminal-issue-request.v1.json`
- `skills/repo-neural-perception/schemas/forgejo-api-observation.v1.json`
- `skills/repo-neural-perception/schemas/admission-result.v1.json`
- `data/forgejo/requests/`
- `runtime/forgejo/`
- `repo/agent-skills-repo/.agents/skills/repo-terminal-operator/`

## 從 local_stack 經驗保留與拒絕的部分

來源：

- `/Users/neon/local_stack/.agent/skills/_archive/forgejo-ops/skill.md`
- `/Users/neon/local_stack/execution/scripts/forgejo-ops.sh`

保留：loopback version check、HTTP credential helper、API／UI 操作後回讀、錯誤快速失敗。

拒絕：硬編碼專案、改寫 `origin`、主工作樹切 branch、force push、
`--allow-unrelated-histories`、匿名 API 當登入、`SKIP_PUSH_GATE`、無界重試與 secret echo。

舊 Skill 已標為 `CONSOLIDATED`，因此它是 provenance，不是 runtime dependency。
