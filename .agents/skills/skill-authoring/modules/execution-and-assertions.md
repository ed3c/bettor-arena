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

對模型輸出的可判 claim，優先使用：

```text
stable predicate id
operator
scalar/typed expected value
repository-relative source
independent evaluator mechanism + digest
```

Evaluator 必須從 exact source/test/runtime subject 重觀測 value。答案文字是否碰巧包含 alias 只可產 `lexical_advisory`，且明示 `admission_effect: none`；它不證明 semantic entailment、程序執行或 fact precision。

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

## 行為量測與比較

量測的共同面與 treatment 面必須分離：

```text
共同：carrier id/version、scenario、fixture commit、subject bundle digest、
      output schema、ground truth、eval config、scorer、predicate evaluator
變因：no/current/candidate 的 Skill package 與 instruction digest
```

Comparator 對共同面做 exact equality；「同 evaluator」是完整 schema/ground-truth/config/scorer/predicate-observer digest set，不是同一個 script 檔名。「同 subject」是 deterministic commit + replay bundle，不是相同 path/branch。release-grade identity 還要固定 treatment package、共同 task prompt、runner 與每個 harness 的 model。`no_skill` 只是不安裝 Skill，不會自動帶入 Skill 程序或啟動 semantic、symbol、graph、memory tools。

共同 prompt 可提供每臂都需要的 output schema 與 closed typed predicate ontology：穩定 ID、型別、operator、合法 value domain，但不得給 observed answer 或 treatment procedure。這不是答案洩漏；沒有 public ontology 時，exact scalar evaluator 只是在測模型是否碰巧猜中 evaluator 私有 alias。文字 alias 命中仍只能是 advisory。

控制臂不是固定四臂。預設因果比較為 `no_skill`、`current_skill`、`candidate_skill`；只有 host 自動選 Skill 的 routing profile 才加 `wrong_skill`，只有宣稱多 Skill 組合效果時才加 `composed_skills`。顯式指定 treatment 的 runner 加 `wrong_skill` 並不會量到 routing。

單次 fixture PASS 只證 bounded task。程序泛化至少另需：

```text
>=3 repetitions / condition
>=2 real harnesses
multiple task families + metamorphic task/context/tool/state variants
source mutation + provider degradation + memory conflict + cross-module impact
no/current/candidate paired evidence with counterbalanced execution order
paired conservative lower bound + worst-family + cross-host gap + metamorphic report
```

`skills-shared` 的 repository-level eval framework 擁有 reusable profile、normalized observation、identity audit、task-blind aggregation、mutation admission 與 capability unlock；單支 Skill 只擁有 task-family suite、oracle/observer 和 local receipts。這個 seam 才能泛化到不同 Skill：協定可重用，oracle 不可硬套。public dev suite 可淘汰但不可 unlock；release 另需 candidate 選定後才解封的 holdout、完整 identity、rollback 與 Human Admit。`Skill.md-native` 類 runtime plane 擁有 digest-pinned compatibility cell、sandbox/security、reproducibility、confidence 與 cost。兩者分表：前者回答「Skill 是否造成可泛化能力提升」，後者回答「在哪個 agent/runtime/model 上可重現且安全」。禁止另造一個加權總分讓 runtime 品質補償 behavior/security hard failure。

量測 evidence origin 也不得折疊：

```text
verifier_observed       deterministic mechanism 真正觀測
artifact_asserted       輸出結構/必要 artifact 存在
model_reported_advisory 模型聲稱 routing/tool/fallback；admission 無效
```

文件連續性 acceptance：每個外部指針前先寫本地一句摘要；直接證據最多一跳；未執行與未決策不得用完成式語氣。對三個以上的分支或階段，用 input → condition → branch → result 圖補足閱讀路徑。
