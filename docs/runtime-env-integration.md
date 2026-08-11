# runtime-env 私有整合契約

## 範圍與真源

`runtime-env` 是 bettor-arena 的私有 runtime contract 來源。GitHub repository
visibility 必須維持 `PRIVATE`；這條整合不執行 public-release issue、不改為
public，也不為公開消費者加 PAT import path。私有 repo 內的 commit、tag 或 release
不改變這個 visibility 邊界。

資料權責只有一條：

1. runtime-env 來源 repo 擁有 variable、module、profile、workload 與 carrier policy。
2. bettor-arena 的 `.runtime-env/` 是單向產生、secret-free 的 consumer projection。
3. 主機憑證值只留在 runtime broker 擁有的 dotenv、Keychain 或 carrier session；
   bettor-arena 禁止出現 `.env`、token、cookie、private key 或編碼後憑證。

Markdown 只負責路由與操作，不複製 catalog 欄位或 policy 內文。機器可判的具體值以
runtime-env 來源與 `.runtime-env/**/*.json` 為準。

## 必備投影

- `.runtime-env/bindings/bettor-arena-local.json`
- `.runtime-env/examples/bettor-arena-local.env.example`
- `.runtime-env/workloads/bettor-arena-local.json`
- `.runtime-env/policies/claude-code-native-isolation.json`
- `.runtime-env/policies/codex-cli-native-isolation.json`
- `.runtime-env/policies/codex-openshell-chatgpt-placeholder.json`

這些檔禁手改。變更 profile、workload 或 policy 後，只能用 runtime-env `sync`
整批重生，並一起 review source commit/tree 與 content hash。

## Agent 操作流程

來源路徑必須是 runtime-env 自己 `docs/local-integration.md` 宣告的 canonical
checkout，不得拿任意 clone 或 worktree 代理。下列 placeholder 是為了避免把單一主機
的絕對家目錄寫進 tracked 文件，不是讓 Agent 自由選路徑：

```sh
RUNTIME_ENV_CHECKOUT=<canonical-runtime-env-checkout>
BETTOR_ARENA_CHECKOUT=<bettor-arena-checkout>
```

來源必須是 clean Git revision，而且它自己的 local integration contract 必須真的
宣告該路徑。不可用 `git remote get-url` 直接把未審核 URL 印到 Agent log；
credential-free origin 由 `sync` 本身 fail closed 檢查：

```sh
git -C "$RUNTIME_ENV_CHECKOUT" status --short
test "$(git -C "$RUNTIME_ENV_CHECKOUT" rev-parse --show-toplevel)" = "$RUNTIME_ENV_CHECKOUT"
grep -F "$RUNTIME_ENV_CHECKOUT" \
  "$RUNTIME_ENV_CHECKOUT/docs/local-integration.md" >/dev/null
```

先 dry-run，review `WOULD-CREATE` / `WOULD-UPDATE`；只有明確獲授權時才 `--apply`：

```sh
"$RUNTIME_ENV_CHECKOUT/runtime-env" sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root "$BETTOR_ARENA_CHECKOUT"
```

```sh
"$RUNTIME_ENV_CHECKOUT/runtime-env" sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root "$BETTOR_ARENA_CHECKOUT" \
  --apply
```

重生後做唯讀 freshness check：

```sh
"$RUNTIME_ENV_CHECKOUT/runtime-env" sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root "$BETTOR_ARENA_CHECKOUT" \
  --check
```

consumer 驗證的資料輸入只有投影，不讀來源 catalog 或網路：

```sh
"$RUNTIME_ENV_CHECKOUT/runtime-env" verify-consumer \
  --target-root "$BETTOR_ARENA_CHECKOUT" \
  --binding bettor-arena-local
```

對已 staged 但尚未 commit 的 projection，必須改驗 Git index：

```sh
"$RUNTIME_ENV_CHECKOUT/runtime-env" verify-consumer \
  --target-root "$BETTOR_ARENA_CHECKOUT" \
  --binding bettor-arena-local \
  --staged
```

此時 verifier 程式從顯式指定的 runtime-env checkout 啟動，但它的驗證輸入只有
bettor-arena projection；它不載入來源 catalog。目前 bettor-arena 尚無已安裝且
固定版本的 runtime-env CLI，所以 pre-commit 尚未常設這條驗證；不得把顯式
`verify-consumer` 綠講成「每次 commit 都會自動擋漂移」。

commit 前另跑 bettor-arena 自己的 T0 與 diff 檢查；兩邊綠不互相代理：

```sh
python3 scripts/gates/check_placement.py
python3 scripts/gates/check_root_coupling.py
python3 scripts/gates/check_credential_hygiene.py
git diff --check
```

## Live runtime 與完成定義

projection freshness 是 offline 合約綠燈，不代表 localhost service、Keychain、browser
session 或 cloud carrier 可用。要宣稱 Forgejo 本機 runtime ready，必須在來源 checkout
由能抵達 host localhost 與 Keychain 的主機執行面另跑；Agent sandbox 內的
`localhost` 不得代理 host 執行面：

```sh
bash "$RUNTIME_ENV_CHECKOUT/scripts/verify-local-runtime.sh" \
  --canonical-path "$RUNTIME_ENV_CHECKOUT"
```

上一支 direct verifier 只輸出當次狀態，不產 receipt。要完成可引用驗收，必須再走
runtime-env 擁有的固定 workload，把 metadata-only、mode `0600` 的 receipt 寫進
broker-owned 私有狀態目錄：

```sh
FORGEJO_RECEIPT_PATH=<new-absolute-path-under-a-user-owned-0700-directory>
"$RUNTIME_ENV_CHECKOUT/runtime-env" workload run \
  --id forgejo-delivery-loop \
  --entrypoint credential-canary \
  --target-root "$BETTOR_ARENA_CHECKOUT" \
  --receipt "$FORGEJO_RECEIPT_PATH"
```

receipt 是 immutable；每次必須用新檔名，不得覆寫舊收據。

`UNREACHABLE`、`MISSING`、`REFUSED` 是三種不同狀態，不得互相改寫；Forgejo 未啟動時
只能宣稱 offline integration 綠，live readiness 仍紅。

這條整合只在下列事實各自完成驗證，而 live claim 另有持久 receipt 時完成：

- 六個 projection 齊全且 `sync --check` 綠。
- `verify-consumer` 綠，且 bettor-arena T0 與 diff check 綠。
- 所宣稱的 live capability 有當次 fixed-workload receipt；未宣稱的可選 carrier 缺席不冒充失敗。
- runtime-env GitHub repository visibility 仍為 `PRIVATE`。
