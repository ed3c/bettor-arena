# runtime-env consumer binding

本目錄只放可公開、可重算的 runtime 契約投影，不放 `.env` 或任何密鑰值。

| 路徑 | 職責 |
|---|---|
| `bindings/bettor-arena-local.json` | 上游 repository/commit/tree、profile closure、內容與輸出 hash |
| `examples/bettor-arena-local.env.example` | 由 binding 可重算的無密鑰 dotenv 範例 |
| `workloads/bettor-arena-local.json` | proof/control 固定入口、mutation class 與 evidence path |
| `policies/claude-code-native-isolation.json` | Claude Code fail-closed sandbox 與跨 carrier deny 要求 |
| `policies/codex-cli-native-isolation.json` | Codex CLI workspace/shell environment 與外部 deny-read 要求 |
| `../scripts/gates/check_runtime_env_binding.py` | 本 repo 離線驗證器；pre-commit 使用 `--staged` |

同步是顯式維護動作。從乾淨且已 pin 到預期 revision 的 `runtime-env`
checkout 執行：

```bash
<runtime-env-checkout>/runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --target-root <bettor-arena-checkout>

# 人或 Agent 審閱 dry-run receipt 後才寫檔
<runtime-env-checkout>/runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --target-root <bettor-arena-checkout> \
  --apply

# 與該 runtime-env checkout 比對上游 freshness；只讀、不修檔
<runtime-env-checkout>/runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --target-root <bettor-arena-checkout> \
  --check
```

更新時必須把 binding、example、workload 與兩個 policies 一起 stage。pre-commit 只讀本 repo Git
index，不呼叫上游、不讀 sibling checkout、不連網，也不會自動修改檔案；因此任何
上游 freshness 檢查仍必須由上述顯式 `sync --check` 啟動。
