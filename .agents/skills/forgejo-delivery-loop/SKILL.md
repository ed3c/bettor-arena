---
name: forgejo-delivery-loop
description: |
  把「小迴圈產出的 repo」與 Forgejo 追蹤面(issues／PR／milestone)綁成有物理收據的閉環——
  據 registry.json 切到對的 repo／milestone／issues;小迴圈物化 repo 時必留 delivery.json 收據,
  T0 閘 scripts/gates/check_delivery_receipt.py(零網路)驗收據,沒登記就擋。未完成項的執行循環＝
  goal 鎖定 open issues → 每張 issue:worktree → tdd 實作 → code-review → PR body 寫 Closes #N →
  merge 後 milestone 進度自動推進;漂移/新發現 → 開新 issue 回圈。三種提示的放置鐵律:
  fixed/iteration/emergent 走 exchange packet 既有欄位,湧現提示落 packets 與 openwiki backlog,
  禁入 development-standards.md 等規範模組。
  觸發詞:交付進度、delivery 收據、issue 驅動實作、切線、forgejo-delivery-loop。
  NOT for:日常晨檢與發佈輪替(product-ops);迴圈拓撲記錄(harness-wiki);建新迴圈工程規範
  (loop-harness-standard);單純 code diff 審(code-review);Forgejo 登入/唯讀預檢(forgejo-loop-ops)。
---

# forgejo-delivery-loop — 小迴圈產出 ↔ Forgejo 追蹤面的物理閉環

> 完整前因後果、機制圖、重靶帳與維護方式 → [modules/delivery-mechanism.md](modules/delivery-mechanism.md)
> (低壓縮全資訊版;本檔只放操作面)。移植自 skill-bettor 的 `github-delivery-loop`,**整條重靶
> 本地 Forgejo,零雲端 GitHub**(人裁 2026-08-06);逐機制對照見該模組 §7。
> 首個活實例＝本 repo 的遷移線:PRD `neon/bettor-arena#2`＋slice issues #3–#27＋
> milestone「bettor-arena migration (PRD #2)」。

## 四層原生儀表板(Forgejo 端的追蹤形狀)

進度不自建工具,疊四層 Forgejo 原生機制(由下而上,每層只做一件事):

| 層 | 載體 | 職責 | 本 repo 的活錨點 |
|---|---|---|---|
| 1 規格根 | **PRD issue** | Problem／Solution／User Stories／Implementation & Testing Decisions／Out-of-scope,決策完整 | `#2` |
| 2 工作單 | **slice issues** | 每張帶 `## Parent` 回鏈 PRD＋acceptance criteria checkbox＋`Blocked by` 依賴序 | `#3`–`#27` |
| 3 交付載體 | **PR** | 分子 commit 鏈可審;body `Closes #N` 讓 merge 自動關工作單 | `#1`(已 merge)、`#25` |
| 4 橫向視圖 | **milestone** | issue 開/關自動投影成完成率;跨線用不同 milestone | 「bettor-arena migration (PRD #2)」 |

**第四層與上游不同,且原因是實測而非偏好**:GitHub 版用 Projects 看板;Forgejo 9.0.3 的
`has_projects` 在 repo 單元為 true(UI 有),但 **API 回 404**(實測 `/repos/{o}/{r}/projects` 與
`/user/projects`),agent 無法驅動看板。milestone 是唯一 API 可驅動且原生投影進度的橫向視圖,
故第四層＝milestone;UI 看板仍可由人手動使用,但**不由機器維護**——這個缺口寫在這裡,不靠沉默掩蓋。

新開一條線時按 1→2→4 鋪(PRD → slices → 掛 milestone),實作期只產生第 3 層;`delivery.json`
收據記的就是這四層的位址。分層因果與「為何不自建儀表板」→ modules §6。

## 三個 SSOT(改這裡,別散落)

| 事實 | SSOT | 消費者 |
|---|---|---|
| 線 ↔ repo ↔ milestone ↔ issues 對映 | [`registry.json`](registry.json) | 本 skill 全部程序＋T0 閘 |
| 每個物化 repo 的交付狀態 | `<物化 repo>/delivery.json`(物理收據) | `scripts/gates/check_delivery_receipt.py` |
| 未完成項的低壓縮追蹤 | 該線計畫文件的 as-run 節(本線＝`docs/plans/2026-08-06-bettor-arena-migration/as-run.md`) | 人＋grill;chat／PR 皆其投影 |

## 觸發(自動,非靠人記得)

小迴圈物化 repo ＝觸發點。物化者**同步寫** `delivery.json`(欄位見 registry.json 頭注:
line／repo／issues[]／pr／milestone_url／synced_at_commit)。
`python3 scripts/gates/check_delivery_receipt.py`(T0,零網路,`--selftest` 自證)掃 registry 列出的
每條線:物化路徑存在而收據缺席或欄位缺漏＝FATAL——與「真的尚未物化」在輸出裡長得不一樣(缺席≠否)。

本 repo 的工廠已有同型交付終點:`trigger.sh` 在 route-result 全綠後確定性寫 wiki-update 請求。
delivery 收據與它是**同一個交付終點的兩張帳**(一張對 wiki,一張對追蹤面),不是兩套機制。

## 切線

開工任何一條線前:`python3 scripts/gates/check_delivery_receipt.py --line <line-id>` 印出該線的
repo／milestone／issues——這就是本次工作的追蹤上下文;跨線不共用 issue 編號空間。

## 未完成項執行循環(goal 驅動)

```
goal 設定：完成 <line> 全部 open issues
for issue in <該線 open issues>:
  隔離工作面(worktree 或乾淨分支;禁在主樹切 branch)
  → /tdd 實作(test-before-code)
  → /code-review(standards+spec 雙軸)
  → PR body 寫 "Closes #N" → 人 merge → milestone 進度自動推進
  漂移或新問題 → 開新 issue(掛同 milestone)→ 回圈頂
```

merge 永遠人 admit;本 skill 只推進到 PR 開好、findings 齊備。Forgejo API 呼叫一律透過既有
credential helper 在記憶體內取憑證,**秘密不落盤不輸出**(本 repo `check_credential_hygiene.py` 守)。

## 三種提示的放置鐵律

- **固定提示**(規範,改動=治理事件)→ 規範模組(如 `modules/development-standards.md`)。
- **自動提示**(迭代上下文,機器生成)→ exchange packet 的 `iteration_auto_context` 與
  `_engine-run/` 帳、wiki-update 請求的 delta 欄。
- **湧現提示**(執行中冒出的新知)→ packet 的 `emergent_prompt_context`＋issue 內文＋
  **openwiki 原生 backlog**;**禁寫入規範模組**——規範只收「已被人 admit 的穩定規則」,
  湧現內容先進 packet／issue／backlog 沉澱,經 fold-in 判 durable home 後才可能升格。
  本 repo 的工廠測試有 grep 負控守這條界。

## 本 skill 自身的維護

演化走小迴圈紀律:改本 skill 的程序前先開 op 沙盒迭代(loop-harness-standard),
T0 錨＝`check_delivery_receipt.py --selftest`;經驗回填走 fold-in(本檔＝Layer A,modules/＝Layer B)。
