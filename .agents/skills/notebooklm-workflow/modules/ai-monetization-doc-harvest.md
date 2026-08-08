# module: ai-monetization-doc-harvest

> `notebooklm-workflow` 的第一個業務 module。表面、出口表與邊界在
> [SKILL.md](../SKILL.md),本檔不複述——只回答「這次收哪一本、為什麼、收完拿去幹嘛」。

## 1. 這個 module 要什麼

從 notebook **「AI 知識變現」**收一份 AI 相關的 Google Doc 或 Google Sheet,
再**沿著 Sheet 內部的 `docs.google.com/document/` 連結,真的去存取一份延伸 Google Doc**。

兩跳都要真跑才算數。只收 hop1 是「有一張表」;第二跳才回答那張表**指出去的東西拿不拿得到**——
而拿不到的原因(沒分享、索引不出東西、根本沒有連結)各自是不同的修法,所以它們各有出口。

## 2. 一行呼叫

```sh
# 先乾跑:auth / notebook / 來源挑選三段真跑,fetch 前停
sh loopctl/loopctl.sh notebooklm run --notebook-title 'AI 知識變現' --follow --dry-run

# 真收兩跳
sh loopctl/loopctl.sh notebooklm run --notebook-title 'AI 知識變現' --follow
```

## 3. 挑選規則(為什麼是這一張)

`--source-title` 沒給時,規則是**先 AI 相關、再 spreadsheet 優先、最後按標題排序**,取第一個。

spreadsheet 優先不是美感:**只有 Sheet 有機會承載第二跳要跟的連結**,所以預設挑的是
「能讓 hop2 成立」的那一張,而不是排序最前的那一張。要固定收某一份就用 `--source-title`,
它會蓋掉整條規則並在收據的 `source.why` 留下 `named by --source-title`。

AI 相關的判定用 ASCII 邊界 lookaround 而非 `\b`:Python 的 `\b` 是 Unicode-aware,
`\bAI\b` **配不到**「AI高價值內容知識變現潛力排行榜」——也就是配不到這本 notebook 裡
大半的標題,而那個失敗長得跟「notebook 是空的」一模一樣。

## 4. 實測基線(2026-08-08,`AI 知識變現` = `86da32d8-…`)

| 事實 | 值 |
|---|---|
| ready 的 Doc/Sheet 來源 | 5(4 張 google_spreadsheet + 1 份 google_docs) |
| 預設挑中 | `AI Solopreneur Tracks & Gaps Master Database (2026)`(spreadsheet) |
| hop1 索引字元數 | ~102k |
| hop1 內的 `docs.google.com/document/` 連結 | 11 條 |

這張表**沒有** `url` 欄位(`source list --json` 的 `url` 是 null),所以連結只能從
`source fulltext` 的內文抽——這是為什麼 hop1 抓的是 fulltext 而不是 metadata。

## 5. 收據怎麼用

每趟落 `data/notebooklm/<utc>/`:

- `module.json` — schema `bettor-arena-notebooklm-module@1.0.0`。可以帶走、可以貼進計劃或 issue:
  它只記 id、標題、候選清單、連結清單、字元數與 sha256,**不含任何文件內文**。
- `hop1.txt` / `hop2.txt` — 抽取物本身。是**別人的 Google 文件內容**,gitignore,不進版控、
  不進任何 proof digest。要引用就引 `module.json` 的 sha256 把它釘回那一趟。

## 6. 人閘

第二跳會在你的 Google 帳號裡**建立並刪除**一本 scratch notebook。刪除走 `finally`,
失敗與中斷都會帶走它——但「帳號裡短暫多一本 notebook」這件事本身要你知情,所以
`--follow` 是 opt-in,不是預設。

## 7. 這個 module 沒有做的事

- 不新增來源到「AI 知識變現」。這條迴圈對它是**唯讀**的。
- 不對抓回來的內容下任何判斷(摘要、排名、變現建議)。那是下一段的事,而把它塞進抓取層
  會讓「抓失敗」與「判斷不合意」共用同一個紅。
