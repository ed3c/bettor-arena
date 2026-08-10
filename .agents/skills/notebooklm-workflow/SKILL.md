---
name: notebooklm-workflow
description: >-
  操作 bettor-arena 的 notebooklm 迴圈——把一個具名 NotebookLM notebook 的 Google Doc/Sheet
  收成本地可稽核產物,並(opt-in)沿著 Sheet 內的 docs.google 連結真去存取延伸文件。
  唯一表面是 `sh loopctl/loopctl.sh notebooklm <run|prove|test>`;繞過它去學 notebooklm/workflow.py
  的私有旗標,下一步就是為了遷就呼叫端去改入口本身。
  觸發詞:notebooklm、NotebookLM 抓取、知識變現 notebook、Google Sheet 內的 Doc、
  notebooklm 迴圈、notebooklm run、跟著連結抓延伸文件、notebooklm-workflow。
  NOT for:安裝或登入 notebooklm CLI 本身(那是 notebooklm-py 上游 SKILL 的事,本 skill
  只消費它並把「未登入」與「未安裝」分成兩種出口);跑其他迴圈(loopctl 的其他 loop);
  建新迴圈的工程規範(loop-harness-standard);記錄迴圈拓撲(harness-wiki)。
---

# notebooklm-workflow

> 本 skill 只講**怎麼驅動 notebooklm 迴圈**。迴圈本身的放置契約在 `ARCHITECTURE.md` §2 的
> `notebooklm/` 槽,對外表面在 `loopctl/contract.json`,證明與對照組在 `proof_workflow/`。
> 這裡不複述任何一份,只留「什麼時候按哪一顆、紅了怎麼讀」。
>
> **要改機制、或紅了不知道那是什麼:先讀 [`notebooklm/README.md`](../../../notebooklm/README.md)。**
> 那是該模組的法則層(九條判準 ＋ 訊號→動作表 ＋ 已經真的抓到過的缺陷)。本 skill 是操作面,
> 它是判斷面;紅的時候查它,不要從這裡重新推。

## 1. 表面

```sh
sh loopctl/loopctl.sh notebooklm run --notebook-title '<標題>' [--source-title '<標題>'] [--follow] [--dry-run]
sh loopctl/loopctl.sh notebooklm prove [--force-receipt]     # 這條迴圈的遍歷收據
sh loopctl/loopctl.sh notebooklm test [--live]               # 對照組:植入缺陷,要求它真的紅
sh loopctl/loopctl.sh contract                         # 旗標全表 + surface_digest
```

旗標只有 contract 列的那些會被轉發,其餘一律 exit 64。要看完整 io 契約就跑 `contract`,
不要讀 `notebooklm/workflow.py` 的 argparse——那是接線不是表面。

## 2. 開工順序(不可跳)

1. **先乾跑**：`... notebooklm run --notebook-title '<標題>' --dry-run`。
   auth、notebook 解析、來源挑選三段是**真跑**的,fetch 之前停;每個呼叫點的 argv 會印出來,
   包含 `--follow` 才會走的那幾條。乾跑綠 = 通路與權限已驗,而且還沒花任何抓取成本。
2. **要第二跳才加 `--follow`**。它是這條迴圈唯一的寫入路徑,而寫的是它自己新建、
   結束時(含失敗、含中斷)一定刪掉的 scratch notebook。`--notebook-title` 指的那本**永遠不會被寫**。
3. 產物落 `data/notebooklm/<utc>/`(gitignore):`module.json` 是收據,`hop1.txt` / `hop2.txt` 是抽取物。
   收據可以帶走、可以貼進計劃;抽取物是別人的 Google 文件內容,**不進版控**。

## 3. 紅了怎麼讀(exit code 不重映射)

| 出口 | 意思 | 修哪裡 |
|---|---|---|
| `64` + `not on PATH` | `notebooklm` binary 不在 | 裝套件。**這不是登入問題** |
| `2` + `not-authenticated` | binary 在、cookie 不認證 | `notebooklm auth refresh`;太舊才 `notebooklm login` |
| `2` + `notebook-not-found` / `notebook-ambiguous` | 標題對不上 / 撞名 | 標題不是 id;撞名時本迴圈拒絕替你挑 |
| `2` + `no-ai-related-source` | 沒有 ready 的 AI 相關 Doc/Sheet | 用 `--source-title` 具名指定 |
| `2` + `empty-fulltext` | 來源 READY 但索引出空字串 | 空集合與任何東西相等,所以它有自己的出口而不是往下流 |
| `2` + `no-doc-urls` | 要了 `--follow` 但 hop1 沒有任何文件連結 | 換一張 Sheet;**空的第二跳不是成功的第二跳** |
| `2` + `follow-library-absent` | CLI 在,但它那個直譯器 import 不到 notebooklm **套件** | 裝套件本體。**不是權限問題** |
| `2` + `follow-not-accessible` | **認證過的**那條路被 Drive 拒了 | 先 `curl` 分流:404=id 本身錯(回頭查 hop1)/401=只是要登入,**與有沒有分享無關**(你自己的私人文件也 401,已量)。真正的病因是 session 失去存取、帳號真的碰不到、或不是原生 Doc |
| `2` + `follow-none-accessible` | 每一條連結都被拒 | 看收據 `hop2.attempted`——各條理由不一定同一種修法 |
| `2` + `PARTIAL id` | 上游 `--json` 被人類行汙染 | 有人把部分 id 傳進去了。全 UUID 才有純 JSON |

**present ≠ authenticated** 是這條迴圈量出來的,不是推論的:`auth check --json` 只證 cookie 檔
解析得動,所以本迴圈一律打 `--test` 並要求 `checks.token_fetch` 為真。

## 4. 業務 module

| module | 它做什麼 |
|---|---|
| [ai-monetization-doc-harvest](modules/ai-monetization-doc-harvest.md) | 第一個業務 module:從「AI 知識變現」收一張 AI 相關 Sheet,並沿它內部的 docs.google 連結存取一份延伸 Google Doc |

新 module 一律落 `modules/`,並在上表加一列。module 只負責「這次要收哪一本、收完拿去幹嘛」,
**不得複製 §1–§3 的表面與出口**——複製一次就開始漂移。

## 5. 邊界:這條迴圈跑在主機,不在容器/沙盒

`notebooklm run` **不經** OrbStack / Apple container / OpenShell,而且這是刻意的:

- 它的輸入包含 `~/.notebooklm/profiles/<profile>/storage_state.json`,那是 **bearer 憑證**——
  持有者即可作為該 Google 帳號行事。OpenShell 的 upload 模型讓沙盒內**每個 process 都讀得到**
  傳進去的值(`proof_workflow/README.md` 記的 codex 那條刻意較弱的路,就是同一個弱點),
  所以把它送進沙盒是把風險換方向而不是降低。
- `loopctl/Dockerfile` 的確定性基座不含 `notebooklm`,主機有裝不等於映像有(法則 10)。

`notebooklm prove` 與 `notebooklm test` 是另一回事:兩者**零網路、純 python/sh**,在 bind-mount 容器裡
跑得動(它們需要 `.git`,所以走 bind-mount 不走 upload)。要跨環境驗證就驗這兩支,
不要為了「進容器」把業務跑的憑證搬進去。

## 6. 收手前

改過 `notebooklm/` 或 `proof_workflow/` 任一檔就要重戳並重鎖,否則下次會以陳舊狀態誤判:

```sh
sh loopctl/loopctl.sh notebooklm prove --force-receipt
sh loopctl/loopctl.sh notebooklm test
```

對照組測的是**已提交的機制**(它在 HEAD 的丟棄式 worktree 裡跑),所以提交前的紅是誠實的。
`proof_workflow/README.md` §2 有完整的收尾序列(全部迴圈重戳 + `workflow lock`)。
