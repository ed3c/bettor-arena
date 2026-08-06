# Module: external-verify — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`external-verify`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到 skill-bettor、
> 哪些因為錯平台/缺上游而被改寫或拿掉、為何不是簡化。

---

## 1. 為何本 skill 大部分內容能直接搬——它跟另外兩個已移植的 harness skill 不同

`loop-harness-standard`/`harness-wiki` 移植時大部分內容要重寫,是因為那兩份文件摻了大量 antigravity
自己迴圈跑出來的歷史證成紀錄(commit 錨、R7/R8/D 編號決策帳本)。`external-verify` 的 SKILL.md 6 步
runbook**先天就不帶這種歷史包袱**——它從頭到尾講的是「怎麼查證一個外部 claim」的通用方法論(三角搜索
→拉 primary→逐 claim 記分→信心分層→雙向自我修正→附來源),跟 antigravity 自己是什麼平台完全無關。
所以本次移植 SKILL.md 本體是**近乎原樣搬**,真正需要重寫的只有兩處:①少數幾條 Gotcha 裡混進的
antigravity 自己查證/踩坑案例(具體域名例子、具體事故案例)、② `modules/verified-truth.md` 這份
「已查證真相」快照——它的每一列都是 Google Antigravity CLI 平台的事實,是徹頭徹尾錯平台的內容,
必須整份重寫。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| 6 步確定性程序(三角搜索/拉 primary/逐 claim 記分/信心分層/雙向自我修正/附來源) | **原樣映** | 全篇最通用的部分,跟平台無關,不需改一個字的方法論骨架。 |
| step 1「優先官方域名(`*.google.dev`／`developers.googleblog.com`／`codelabs.developers.google.com`／官方 github.com/<org>/<repo>`)」 | **域名例子拿掉,泛化為「vendor/工具官方站、官方 blog、官方 github.com/<org>/<repo>`」** | 那組具體域名是 antigravity 查證 Google Antigravity 平台時累積的清單;skill-bettor 未來查證的對象是 Claude Code 官方文件、npm/PyPI 套件文件、TradingView Pine Script 文件等完全不同的域名——留著 Google 域名例子會誤導使用者以為要去查 `google.dev`。這不是刪內容,是換掉一組不適用本地情境的具體例子。 |
| Gotcha「JS-app docs(`antigravity.google/docs/*`)WebFetch 常只回標題」 | **具體 URL 拿掉,泛化為「高度 JS 渲染的官方文件站→改抓靜態鏡像(README/codelab/release note)」** | 現象(JS 渲染站抓不出內文)通用,但 `antigravity.google` 這個域名對 skill-bettor 毫無意義,留著＝死引用。 |
| Role 段「這是 `path-b-reduction` 步驟一的執行化;錨念同 northstar External-Verify / PG-163」 | **`path-b-reduction` 部分改成 inline 說明 + 明確標記已知缺口;`northstar External-Verify / PG-163` 整段拿掉** | `path-b-reduction`(把 claim 約分到確定性鐵錨的方法論)本身**未在本批次移植**,skill-bettor 沒有這個 skill,不可留可點連結假裝存在——已在 SKILL.md Role 段用一句話說明其步驟一在做什麼,讓本檔不靠上游 skill 也讀得懂。`northstar External-Verify / PG-163` 是 antigravity 自己溯源到 northstar 系統的編號引用(PG-163),skill-bettor 沒有 northstar/PG 編號系統,這是 ARCHITECTURE.md §7 講的「dangling 編號 jargon」,直接拿掉而非硬留一個查無此號的引用。 |
| Gotcha「WebFetch 也是二手」的案例錨(truth-verify 五 run 撇號累犯 / H2b haiku 大面積 false-REFUTED,連到 `truth-verify/loop-ledger.md`) | **機制描述(摘要化+標點正規化兩類風險)原樣映,案例錨改成文字旁註「antigravity 自己的迴圈踩過,案例未搬入」** | 風險機制(WebFetch 經小模型改寫,會摘要化/正規化直彎撇號)是通用的,值得完整保留;但具體案例(`truth-verify` 迴圈、H2b haiku 判官事故)是 antigravity 自己一條 skill-bettor 沒有的量測迴圈跑出來的軌跡,`truth-verify/loop-ledger.md` 在 skill-bettor 不存在,留連結＝死指標。 |
| Gotcha「數字對 ≠ 機制對」的 Superpowers-6 案例(連到 `antigravity-harness-wiki/modules/token-efficiency-anchors.md`) | **失敗模式的機制描述保留,案例改成純文字說明(不留連結),明確標記為 antigravity 外部案例僅供理解** | 「二手轉述常見的走樣是百分比對、機制錯」這個通則值得留,案例本身(合併 reviewer 維度錯配、tiering 機制誤讀)也還原成夠具體的文字讓讀者不需要點連結就懂——但原連結 `antigravity-harness-wiki/modules/token-efficiency-anchors.md` 這個模組在 skill-bettor 完全不存在(`harness-wiki` 移植時這份 antigravity 專屬 Superpowers 研究筆記已被明文列為「整份不搬」,見 `harness-wiki/modules/retarget-map.md` Sources 段),不可能留一個指向不存在檔案的連結。 |
| `modules/verified-truth.md`(Google Antigravity CLI 平台事實表:`AGENTS.md` canonical 檔名、`.agents/skills/` 目錄、三層 scope 路徑、`GEMINI.md` 存在性) | **整份不搬,改寫成 skill-bettor 空白模板 + 本次移植時新查證的 Claude Code Skill 規範種子表** | 這份表 100% 是 Google Antigravity 平台的事實,skill-bettor 是 Claude-Code-only 專案,連一列都不適用——逐字複製＝把假鐵錨灌進一個號稱「已查證真相」的檔案,比不移植更糟。改為誠實的空白模板,且用本 skill 自己的 runbook(WebFetch 官方 Claude Code 文件)真的查證了幾條 skill-bettor 自己用得到的事實作為起步種子(見該檔 Sources)。 |
| Not For / Gotcha「本 skill 產出的『已查證真相』會過期,復用前重跑 step 1-2」 | **原樣映** | 純方法論紀律,跟平台無關。 |

## 3. 拿掉/換掉的東西不是「簡化」,而是「錯平台」或「缺上游」

- **能原樣映的映**:6 步確定性程序全部、Not For 兩條、「會過期的快照」紀律、WebFetch/WebSearch 二手
  風險的機制描述、「數字對≠機制對」的失敗模式通則。
- **具體例子錯平台、換掉**:官方域名清單(Google 域名→泛化)、JS-app docs 案例(`antigravity.google`
  具體 URL→泛化)。這兩處都保留了**現象**,只換掉不適用 skill-bettor 情境的**具體例子**。
- **案例錨屬於 antigravity 自己沒有本地基座的迴圈、真拿掉連結**:`truth-verify/loop-ledger.md`、
  `antigravity-harness-wiki/modules/token-efficiency-anchors.md`——這兩個迴圈/模組在 skill-bettor
  都不存在(`truth-verify-loop` 未移植;`token-efficiency-anchors.md` 移植 `harness-wiki` 時已明文
  列為不搬),機制描述保留但案例改成文字旁註,不留死連結。
- **上游 skill 缺口、誠實標記**:`path-b-reduction` 未在本批次移植,本檔用 inline 說明頂替可點連結,
  明確標成「已知缺口(antigravity-external)」而非默默拿掉整段 Role 脈絡。
- **平台事實表整份錯平台、重寫**:`modules/verified-truth.md` 換成 skill-bettor 自己的空白模板+真
  查證種子,不是把 antigravity 的表精簡後留幾行——是換成完全不同的內容。

## 4. 判別「retarget 成立」的鐵錨(disk 已於 2026-07-11 驗證)

- 本地產出真存在:`.claude/skills/external-verify/SKILL.md`、
  `.claude/skills/external-verify/modules/verified-truth.md`(本次落地)。
- 本批次已落地的同批 sibling(`ls`/`test -e` 已核):`loop-harness-standard/SKILL.md`、
  `harness-wiki/SKILL.md`、`unknown-discovery-composer/SKILL.md`、`sdlc-plan-composer/SKILL.md`、
  `judge-loop-chooser/SKILL.md`、`fold-in/SKILL.md`、`html-for-decisions/SKILL.md` 皆已存在——
  `loop-harness-review-handoff/` 於本檔完稿當下(2026-07-11)尚未在 disk 上出現,屬**同批次仍在平行
  進行中**,不代表最終缺席,不斷言其內容。
- **inbound 引用驗證**:`judge-loop-chooser/SKILL.md` 已落地且內文多處引用
  `[external-verify](../external-verify/SKILL.md)`(T2 跨家族查證工具)——本次移植維持 skill 名稱
  `external-verify` 不變,該相對路徑連結成立,不需要 judge-loop-chooser 那邊做任何調整。
- **已知缺口驗證**:antigravity 源 `/Users/neon/antigravity/.agents/skills/path-b-reduction/SKILL.md`
  真實存在(disk 已核),但 skill-bettor 對應路徑 `.claude/skills/path-b-reduction/` 確認不存在
  (`test -e` 已核為 ABSENT)——本檔 Role 段的「已知缺口」標記如實反映這個現況,不是猜測。
- **案例錨拿掉驗證**:`/Users/neon/antigravity/truth-verify/loop-ledger.md` 與
  `/Users/neon/antigravity/.agents/skills/antigravity-harness-wiki/modules/token-efficiency-anchors.md`
  在 antigravity 側都真實存在(disk 已核),但兩者在 skill-bettor 都沒有對應路徑——本檔的「案例錨拿掉
  改文字旁註」如實反映這個落差,不是憑空宣稱。
- 若哪天有人往本 skill 塞回具體 Google 域名清單、`antigravity.google` URL、`northstar`/`PG-NNN`
  編號引用,或試圖把 `path-b-reduction` 當作本地已存在的 skill 來連結,那就是把不適用的平台事實/
  不存在的上游基座搬回來——擋下,除非那個 skill/迴圈真的先在 skill-bettor 落地。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/external-verify/`(SKILL.md +
  `modules/verified-truth.md`)。
- antigravity 已知但未移植的上游:`/Users/neon/antigravity/.agents/skills/path-b-reduction/SKILL.md`
  (本批次不搬,見 §2/§4)。
- antigravity 已知但未移植/未搬入案例錨的迴圈與模組:
  `/Users/neon/antigravity/truth-verify/loop-ledger.md`、
  `/Users/neon/antigravity/.agents/skills/antigravity-harness-wiki/modules/token-efficiency-anchors.md`。
- skill-bettor 既有同構:本次移植的種子驗證表(`modules/verified-truth.md`)本身就是本 skill runbook
  的一次真實應用——用 WebFetch 拉 Claude Code 官方文件、逐 claim 記分,而非直接複製 antigravity 的表。
