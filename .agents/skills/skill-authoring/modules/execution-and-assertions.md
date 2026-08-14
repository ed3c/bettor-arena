# Execution and assertion contract

`SKILL.md` 只提出程序；host-owned runner 執行；獨立 assertion engine 判定；Human Admit 決定 promotion。模型說「已測試」、script 存在或 MCP 已連線，都不等於 PASS。

## 程式執行

Skill 可以攜帶 `scripts/`，也可以要求 host 呼叫 repository CLI。直接執行 script 時才需要 executable bit；以 `python3 scripts/check.py` 或 `sh scripts/check.sh` 呼叫不需要。所有命令都要解析成 typed executable 加 `argv[]`，禁止 `shell: true`、`bash -c <model text>`、絕對 host path、`../` traversal、secret value 與 implicit branch。

Bettor 的 executable contract、request/assertion/receipt schemas 與 public runner 分別位於：

- [`harness-wiki/modules/executable-skill-contract.md`](../../harness-wiki/modules/executable-skill-contract.md)：說明程序、runner、assertion engine、LoopX 與 Human Admit 的權責。
- [`harness-wiki/contracts/skill-execution-request.schema.json`](../../harness-wiki/contracts/skill-execution-request.schema.json)：typed command、sandbox、subject 與 Skill digest 的 machine contract。
- [`harness-wiki/contracts/skill-assertion-set.schema.json`](../../harness-wiki/contracts/skill-assertion-set.schema.json)：hard/advisory assertion set。
- [`harness-wiki/contracts/skill-execution-receipt.schema.json`](../../harness-wiki/contracts/skill-execution-receipt.schema.json)：執行結果與 evidence digest 的 subject-bound receipt。
- [`harness-wiki/scripts/run_portable_skill.py`](../../harness-wiki/scripts/run_portable_skill.py)：在 disposable worktree 執行 typed request 的 repo-owned runner；其本機 process adapter 不宣稱 physical network/filesystem isolation。

## 斷言

Hard assertion 至少要包含 OS/test 可觀測結果，例如 `exit_code`、JSON schema、file hash/content、git diff allowlist、AST query、LSP diagnostics、test report、artifact digest 與 exact subject match。LLM review、自然語言 checklist 和 Human comment 是 advisory；它們可以要求重試或阻擋 promotion，但不能把 failed hard assertion 改成 PASS。

PASS 必須同時有：

```text
executed=true
observed integer exit_code
request subject == receipt subject
request Skill digest == receipt Skill digest
stdout/stderr artifact digests
all hard assertions PASS
cleanup PASS
```

狀態不得折疊：`PASS`、`FAIL`、`ABSENT`、`NOT_IMPLEMENTED`、`NOT_EXERCISED`、`SKIPPED_BY_POLICY` 與 `UNMATERIALIZED` 各自保留。這沿用 `forgejo-delivery-loop` 的收據/活狀態分離：receipt 回答某次到底發生什麼，live audit 回答現在還是否成立。

## 驗證迴圈

1. 預先登記 subject、command、sandbox、expected artifacts 與 assertions。
2. 執行一次；保存 stdout/stderr 與 artifact digests。
3. hard assertion 紅時，根據具名 evidence 修正並重跑；同一問題最多三次。
4. 三次仍紅，記錄每次錯誤、質疑抽象層級並停止；禁止隨機改 prompt 直到碰巧綠。
5. 只有 exact-subject receipt 全綠才可報 PASS；promotion 仍等 Human Admit。

文件連續性 acceptance：每個外部指針前先寫本地一句摘要；直接證據最多一跳；未執行與未決策不得用完成式語氣。對三個以上的分支或階段，用 input → condition → branch → result 圖補足閱讀路徑。
