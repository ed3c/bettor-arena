# runtime-env consumer binding

本目錄只放可公開、可重算的 runtime 契約投影，不放 `.env` 或任何密鑰值。

| 路徑 | 職責 |
|---|---|
| `bindings/bettor-arena-local.json` | 上游 repository/commit/tree、profile closure、內容與輸出 hash |
| `examples/bettor-arena-local.env.example` | 由 binding 可重算的無密鑰 dotenv 範例 |
| `workloads/bettor-arena-local.json` | proof/control、carrier status 與經逐次外送核准的 live research 固定入口 |
| `policies/claude-code-native-isolation.json` | Claude Code fail-closed sandbox 與跨 carrier deny 要求 |
| `policies/codex-cli-native-isolation.json` | Codex CLI workspace/shell environment 與外部 deny-read 要求 |
| `../scripts/gates/check_runtime_env_binding.py` | 本 repo 離線驗證器；pre-commit 使用 `--staged` |
| `../scripts/runtime-env/check-stealth-browser.sh` | 只接受乾淨、完整、獨立版控的 stealth-browser checkout，跑 CLI＋DR CDP／HTML／file-sink 最小閉包；不冒充 owner full-suite |
| `../scripts/runtime-env/run-equivalence-live.py` | 驗 request 與 0600、短效、digest-bound Gemini 外送核准後才啟動 live adapter |

本機真值只放 `<runtime-env-checkout>/.env`（本機 canonical 實體目前位於
`runtime-env` checkout 根；0600、untracked）。本 repo 只收
`examples/bettor-arena-local.env.example` 的空值／安全預設。既有 macOS Keychain
Claude login 的 canary 不設定 config override，Codex entrypoint 只收到
`CODEX_HOME`；同一份 `.env` 內另一套 carrier 設定不會進 child process，兩個
native policy 也不互相改寫。三個 status wrapper 只回傳 bounded state，不回傳帳號、
組織或完整模型 inventory。

stealth-browser owner full-suite 仍是獨立 gate。2026-08-10 實測為 365 passed、
11 failed、2 skipped：9 個 timeout，2 個因缺 `profiles/research/locked-fingerprint.json`；
`npm audit` 另報 34 項（1 low、19 moderate、12 high、2 critical）。runtime 的 DR
最小閉包綠燈不能覆蓋這些 owner 缺陷或宣稱整個 repo production-admitted。

固定執行面：

```bash
<runtime-env-checkout>/runtime-env workload run \
  --id bettor-arena-proof --entrypoint claude-auth-status \
  --target-root <bettor-arena-checkout> --env-file <runtime-env-checkout>/.env --json

# 可替換為 codex-login-status、agy-model-inventory、stealth-browser-control。
# equivalence-live 額外要求 EQUIVALENCE_* 三個路徑，且 approval receipt 必須
# 精確綁 request bytes、Gemini destination、風險文字與有效期限。
```

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
