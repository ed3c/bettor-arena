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
# 先乾跑:auth / notebook 解析 / registry pin 核對 / 來源挑選四段真跑,fetch 前停
sh loopctl/loopctl.sh notebooklm run --target ai-monetization --dry-run

# 真收兩跳(target 自帶 --follow)
sh loopctl/loopctl.sh notebooklm run --target ai-monetization
```

`--target ai-monetization` 是 `notebooklm/registry.json` 的一條;notebook 標題、來源挑法、
要不要跟連結全在那裡,所以這次收割的形狀看得見於 diff,而不是留在誰的 shell 歷史裡。
臨時換一本就用 `--notebook-title '<標題>' --follow`,兩者只能擇一。

## 3. 挑選規則(為什麼是這一張)

`--source-title` 沒給時,規則是**先 AI 相關、再 spreadsheet 優先、最後按標題排序**,取第一個。

spreadsheet 優先不是美感:**只有 Sheet 有機會承載第二跳要跟的連結**,所以預設挑的是
「能讓 hop2 成立」的那一張,而不是排序最前的那一張。要固定收某一份就用 `--source-title`,
它會蓋掉整條規則並在收據的 `source.why` 留下 `named by --source-title`。

AI 相關的判定用 ASCII 邊界 lookaround 而非 `\b`:Python 的 `\b` 是 Unicode-aware,
`\bAI\b` **配不到**「AI高價值內容知識變現潛力排行榜」——也就是配不到這本 notebook 裡
大半的標題,而那個失敗長得跟「notebook 是空的」一模一樣。

## 4. 第二跳為什麼不能走 URL(量出來的,不是推論)

**CLI 的 `source add <url>` 是匿名抓取**,而這張表指出去的每一份文件都要登入。三個獨立訊號:

| 探針 | 結果 |
|---|---|
| `notebooklm source add <doc-url>`(5 份,含帶/不帶 `/edit`、含/不含 `--type url`) | 全部 exit 1,`RPC ADD_SOURCE ... rpc_code=9`(FAILED_PRECONDITION) |
| 同一本 scratch notebook 加 `https://example.com`(正控) | exit 0——**機制沒壞,是那些文件拿不到** |
| 未認證 `curl` 那些 doc URL | **401**;亂編一個 id 則是 **404** |

401 與 404 的差別是關鍵:文件**存在但被閘住**,不是不存在。所以第二跳改走
`sources.add_drive(file_id, mime=GOOGLE_DOC)`——**認證過的 Drive by-reference**。CLI 沒有這條路,
所以 `notebooklm/drive_fetch.py` 用 CLI 自己的直譯器跑(路徑從 CLI 的 shebang 推,不寫死)。

對照組有一條**靜態斷言**擋回退:`stage_follow` 一旦又出現 `source add`,`notebooklm test` 就紅。
這條與植入缺陷那幾條是**兩種抵達**——後者驗錯誤處理,前者驗機制沒被換掉,不會被同一個錯誤同時騙過。

## 5. 實測基線(2026-08-08,`AI 知識變現` = `86da32d8-…`)

| 事實 | 值 |
|---|---|
| ready 的 Doc/Sheet 來源 | 5(4 張 google_spreadsheet + 1 份 google_docs) |
| 預設挑中 | `AI Solopreneur Tracks & Gaps Master Database (2026)`(spreadsheet) |
| hop1 索引字元數 | 102,236 |
| hop1 內的 `docs.google.com/document/` 連結 | 11 條 |
| hop2 實際取得 | `[AI Product Note] Taalas｜2026-08-07`,2,264 字 |

這張表**沒有** `url` 欄位(`source list --json` 的 `url` 是 null),所以連結只能從
`source fulltext` 的內文抽——這是為什麼 hop1 抓的是 fulltext 而不是 metadata。

連結是**依序試到第一個開得了為止**,被拒的留在收據的 `hop2.earlier_refusals`。單試一條會把
「這條連結壞了」講成「第二跳不能用」,而那是兩件事。

## 6. 收據怎麼用

每趟落 `data/notebooklm/<utc>/`:

- `module.json` — schema `bettor-arena-notebooklm-module@1.0.0`。可以帶走、可以貼進計劃或 issue:
  它只記 id、標題、候選清單、連結清單、字元數與 sha256,**不含任何文件內文**。
- `hop1.txt` / `hop2.txt` — 抽取物本身。是**別人的 Google 文件內容**,gitignore,不進版控、
  不進任何 proof digest。要引用就引 `module.json` 的 sha256 把它釘回那一趟。

## 7. 人閘

第二跳會在你的 Google 帳號裡**建立並刪除**一本 scratch notebook。刪除走 `finally`,
失敗與中斷都會帶走它——但「帳號裡短暫多一本 notebook」這件事本身要你知情,所以
`--follow` 是 opt-in,不是預設。

## 8. 這個 module 沒有做的事

- 不新增來源到「AI 知識變現」。這條迴圈對它是**唯讀**的。
- 不對抓回來的內容下任何判斷(摘要、排名、變現建議)。那是下一段的事,而把它塞進抓取層
  會讓「抓失敗」與「判斷不合意」共用同一個紅。
