---
name: repo-wiki-converge
description: |
  把「任意可讀 repo → agent 可當記憶讀的 wiki」變一鍵流程時使用 — langchain-ai/openwiki 官方
  code-mode init/update 程序的 host-native 移植：官方提示詞逐字、官方三閘（skeleton_critic ×
  question_finder × answer_verifier）以硬隔離子進程執行、官方確定性後處理以 stdlib Python 重建。
  NO API KEY：推理全在 Claude Code 或 Codex CLI 自己的訂閱 session，不裝 node、不設任何 provider key。
  觸發詞：repo wiki、任意 repo 生 wiki、openwiki、repo 理解文檔、kb-ingest repo wiki、wiki 收斂。
  何時用：要對一個可讀 repo 產 agent-grade 理解 wiki 並進 KB 時。
  NOT for：抽源碼級不變量／隱含依賴（repo-agent-native）；抽 Gemini 對話（gemini-conversation-research）；
  查證單一外部 claim（external-verify）；造或改 skill（skill-authoring）。
  官方↔本地逐機制映射與誠實缺口在 modules/official-port-map.md。
---

# Skill: repo-wiki-converge — 官方 OpenWiki 程序的 host-native 移植

> **Role**: 對一個**可讀的 repo** 跑 langchain-ai/openwiki 的官方 code-mode 程序，產出 OKF v0.1
>   wiki 落 `<TARGET>/openwiki/`，再快照進 skill-bettor RepoDoc lane。
>   **執行體是本 session**（Claude Code 或 Codex CLI），不是 openwiki 的 node CLI——所以零 API key。
> **設計立場**: 提示詞**不改寫**。上一版（`repo-wiki.workflow.md`，已退役）把官方「禁設頁數目標、每個
>   實質組件自己一頁」蒸餾成「≤8 頁、800–1200 字」，方向相反，並丟掉官方全部三個閘、OKF、Mermaid、
>   task-routing 表與 evidence gate。本版改以同步腳本從 openwiki 源碼抽取原文，逐字可 diff。
> **`$MODULE` = 本檔所在目錄的上一層**（這份 SKILL.md 住在模組內的 `skill/`；host 的 skill 目錄
>   只是指向它的 symlink）。本 repo 的 `$MODULE` ＝ `kb-ingest/`。底下所有路徑都相對 `$MODULE`，
>   模組換名／換深度／換 repo 都不必改本檔：
>   ```sh
>   MODULE=$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo .)")" && pwd)   # 或直接寫 kb-ingest
>   ```
> **SSOT / 活基座（每個都真存在且可跑）**:
>   - 官方提示詞 = [`$MODULE/openwiki/`](../openwiki/)（`init.system.md`／`update.system.md`／
>     `user.*.md`／`subagents/*.md`）。**禁手改**；重生＝`python3 "$MODULE/port/sync_prompts.py" <openwiki_repo>`。
>   - 官方確定性後處理 = [`$MODULE/port/openwiki_post.py`](../port/openwiki_post.py)
>     （`migrate`／`finalize`＝OKF 修復・mermaid 降級・index 生成・內鏈驗證・`.last-update.json`）。
>   - 官方三閘 runner = [`$MODULE/port/openwiki_subagent.sh`](../port/openwiki_subagent.sh)
>     `<critic|finder|verifier> <TARGET> [payload]`，雙 host、讀取邊界物理隔離。
>   - host 對映與缺口 = [`$MODULE/port/host-runtime.md`](../port/host-runtime.md)。
>   - RepoDoc frontmatter 擴展 = [`$MODULE/port/repodoc-extension.md`](../port/repodoc-extension.md)。
>   - clone 慣例 = [`$MODULE/setup-repo.sh`](../setup-repo.sh)；進 KB＝`python3 -m indexing.ingest_repodoc_cli`
>     （**host profile `repodoc` 專屬**，見下方 S5；沒有該 lane 的 host 跳過此步，wiki 產出不受影響）。
>   - 遷移完整性閘 = [`$MODULE/check_repo_wiki_converge.py`](../check_repo_wiki_converge.py)，
>     安裝宣告 = [`$MODULE/host-profile.json`](../host-profile.json)。
> **Lineage**: 上游 langchain-ai/openwiki（提示詞版本釘在各資產的 provenance 標頭）。層級關係
>   （L1 理解 → L2 不變量 → L3 規格）見 [`$MODULE/mastery-ladder.md`](../mastery-ladder.md)。

## 🚩 STOP — 你在合理化（違反即停）

| 念頭 | 現實 |
|---|---|
| 「官方提示詞太長，我摘要重點餵就好」 | ❌ 這正是上一版失敗的原因。摘要必丟閘：頁數上限、缺 critic、缺 evidence gate 全是「精簡」的產物 |
| 「頁數控制一下，8 頁夠了」 | ❌ 官方明文 `do not target a page count or page length`；每個實質組件必須有自己的頁 |
| 「skeleton 我自己審一遍就好，不用開子進程」 | ❌ critic 必須**先獨立 map 完 repo 才准讀 skeleton**。同 session 自審＝已被 skeleton 錨定，看不見它漏了什麼 |
| 「verifier 讓它順便看一下源碼比較準」 | ❌ 它一看源碼就是在用源碼作答，閘失效。邊界由 sandbox 物理保證，別繞 |
| 「跑完了，wiki 寫出來就算完成」 | ❌ `openwiki_post.py finalize` 沒跑＝沒有 index、mermaid 沒驗、壞鏈沒標、`.last-update.json` 沒寫 |
| 「子進程回空／報錯，大概是沒問題」 | ❌ 空輸出**不是 PASS**。runner 已 fail loud，別把它當通過 |

## When to Use
- 有一個**可讀 repo**（本地 clone 或本 repo 自己）要產 agent 可當記憶讀的理解 wiki。
- 一份既有 openwiki 目錄要照 target 的新 commit 更新（走 `update`，不是重跑 `init`）。

## Not For
（下列都是 **host 的其他 skill**，按名字叫用即可。這裡刻意不寫相對路徑：本檔住在模組內，模組不該
假設 host 裝了哪些 skill、放在哪個目錄——那種連結在別的 repo 一定斷。）
- ❌ 源碼級不變量／隱含依賴／確認的缺席 → `repo-agent-native`（L2；本 skill 是 L1）。
- ❌ 研究一個 Gemini 對話 → `gemini-conversation-research`。
- ❌ 查證單一外部 claim → `external-verify`。
- ❌ 造／改 skill → `skill-authoring`。
- ❌ 用 DR 當 repo 掌握主幹（漏斗倒置）——源碼是 SSOT。

## 不變量（違反即停）
1. **官方／非官方是目錄邊界，不只是檔內標記。** `$MODULE/openwiki/` **只放上游逐字位元組**——7 個由
   `sync_prompts.py` 生成的資產，禁手改、**禁新增任何檔**（連筆記都不行）。所有本地增補一律進
   `$MODULE/port/`（誰引用誰、目的為何見其 `README.md`）。要調整行為＝在 port 加檔或改
   `sync_prompts.py` 後重生，絕不動 `OPENWIKI-OFFICIAL` 標記內的文字。
   純度由 `check_repo_wiki_converge.py` 強制、漂移由 S0 的 `--check` 抓。
2. **三個閘各自的讀取邊界不可繞。** critic 先自 map 再讀 skeleton；finder 只讀源碼；verifier 只讀 wiki。
   一律走 `openwiki_subagent.sh`（sandbox 物理保證），不用同 session 自審代替。
3. **後處理必跑。** 官方提示詞把 index 生成／frontmatter 修復／mermaid 驗證／鏈結驗證當**既成事實**在講；
   不跑 `openwiki_post.py`，那些句子就是空話，產出是半成品。
4. **只寫 `<TARGET>/openwiki/`。** 不改 target 源碼、不改它的 `AGENTS.md`／`CLAUDE.md`、不改
   `openwiki/INSTRUCTIONS.md`（那是人寫的 brief，不是生成物）。
5. **全歷史 clone**（never `--depth 1`）；shallow ⇒ 官方的 git-history 證據路徑崩，rationale 無從接地。
6. **收斂 = QA 迴圈全 PASS ∧ critic 無 UNRESOLVED ∧ finalize 零壞鏈**；merge／進 KB 永遠人 admit
   （全域鐵律 3）。全綠是候選，不是 merge 令。

## 確定性程序

0. **preflight**：`python3 "$MODULE/check_repo_wiki_converge.py"`（core：資產齊全＋逐字性＋自測＋
   三閘邊界證明；宣告的 host profile 另跑）。**exit 0 通過／1 有東西壞了／3 說不出結論**——
   3 是「宣告檔缺席或壞了」，不是比 1 輕的紅，別當成跳過。
   若手上有 openwiki checkout，加跑 `python3 "$MODULE/port/sync_prompts.py" <openwiki_repo> --check`
   確認提示詞未漂移。任何紅先修本地基座，不進作者輪。
   改過閘或搬過模組，加跑 `bash "$MODULE/port/test_relocation.sh"`：它把模組複製到別名
   別深度的臨時 host 跑正控，再逐項注入破壞要求對應的紅。**閘自己綠不代表閘還在檢查**——
   那支才是證明它會紅的東西。
1. **取得 TARGET**：`bash "$MODULE/setup-repo.sh" <repo_name> <clone_url>`
   → `TARGET=<repo_root>/<repo_name>/<repo_name>`、`OUT=<repo_root>/<repo_name>/`，其中 `<repo_root>`
   ＝`SKILL_BETTOR_REPO_ROOT` 或該腳本的預設值（本 repo＝`repo/`，已 gitignore；絕不 `/tmp`）。
   腳本會印出實際落點，以它為準，別自己拼路徑。要記錄 target 的 `git rev-parse HEAD`。
2. **既有 wiki → migrate**：`python3 "$MODULE/port/openwiki_post.py" migrate <TARGET>/openwiki`
   （首次 init 可跳過）。這是官方 `beforeAgent`，讓作者面對的是已合規的 frontmatter。
3. **主跑（本 session 就是 doc agent）**：讀
   [`openwiki/init.system.md`](../openwiki/init.system.md)（或 `update.system.md`）
   ＋ 對應 `user.*.md` ＋ [`port/host-runtime.md`](../port/host-runtime.md)
   ＋ [`port/repodoc-extension.md`](../port/repodoc-extension.md)，
   **照官方 Init workflow 逐步做**。其中兩處必須外呼子進程：
   - 官方步驟 5（skeleton 完成後）→ `bash "$MODULE/port/openwiki_subagent.sh" critic <TARGET> <payload>`。
     每個回傳的 `RQ-` 開一個 TODO 全數解決，**再呼一次且僅一次**（附上前次請求與各項處置）。
   - 官方步驟 8（頁面內容寫完後）→ `finder` 取問題集，每題一個 TODO；
     `verifier` 每批 2–3 題**同一波併發**送出；PARTIAL/FAIL 先把該波修完再重驗，只重送未過的 ID。
4. **finalize**：
   `python3 "$MODULE/port/openwiki_post.py" finalize <TARGET>/openwiki --target <TARGET> --command init --model "<host>+<model>"`
   → mermaid 降級、index 生成、壞鏈就地標記、`.last-update.json`。壞鏈與降級圖是**就地標記不阻斷**，
   下一次 update 照註解修復。
5. **快照 + 進 KB**（**host profile `repodoc` 專屬**；`host-profile.json` 未宣告 `repodoc` 的 host
   直接跳到 S6，wiki 本身已完成）：把 `<TARGET>/openwiki/` 複製一份到 `<OUT>/repo_wiki/<slug>/`
   （durable 快照，slug＝TARGET basename），先
   `python3 -m indexing.ingest_repodoc_cli <OUT>/repo_wiki/<slug>/ --dry-run`，
   綠了再真跑寫入 KG。`--embed` 才需要向量庫，基本 graph ingest 不需要。
6. **人 admit**：把 critic 最終 status、QA 全 PASS 證據、finalize 報告一行（degraded／indexes／broken）
   交人裁。要升到 L2 不變量 → `repo-agent-native`（demand-pull，非自動）。

## Stateful Workflow（不要壓成單 prompt）

| Node | Actor | Input | Output | Conditional Edge |
|---|---|---|---|---|
| S0 preflight | 本 session | kb-ingest 資產 | 遷移報告 | fail → 修基座 |
| S1 source-setup | setup-repo.sh | clone URL／本地路徑 | 全歷史 TARGET + OUT | shallow → `fetch --unshallow` |
| S2 migrate | openwiki_post.py | 既有 `openwiki/` | 合規 OKF frontmatter | 首次 init → 跳過 |
| S3a skeleton | 本 session | TARGET + init.system.md | `openwiki/_skeleton.md` | — |
| S3b critic | 子進程（worktree） | skeleton + 獨立 map | RQ 清單／PASS | CHANGES_REQUESTED → 解決後複審一次 |
| S3c 內容 | 本 session | skeleton + evidence gate | wiki 頁面 | — |
| S3d finder | 子進程（worktree，無 wiki） | 只有源碼 | ≤10 題 + 驗收標準 | — |
| S3e verifier | 子進程（只有 wiki 快照） | 題目批次 | PASS/PARTIAL/FAIL | 非 PASS → 修頁 → 只重驗該 ID |
| S4 finalize | openwiki_post.py | wiki | index／降級圖／壞鏈標記／metadata | 壞鏈非阻斷，記錄 |
| S5 ingest | ingest_repodoc_cli | 快照 wiki | RepoDoc/Library/Concept 圖 | dry-run FAIL → 補 frontmatter |
| S6 handoff | 本 session | 報告 | 人 admit／L2 scope 種子 | 要不變量 → repo-agent-native |

## Gotchas
- **官方步驟 5 的 critic 只准兩輪**：初審必須一次交出全部缺口，複審只驗前次項目＋新回歸；不得第三次。
  它自己的 prompt 已寫死這條，別加輪。
- **`_skeleton.md` 寫完要刪**（官方明文），但**刪在最後**——critic 需要它。
- **`index.md` 不准手寫**。它由 `finalize` 確定性生成；手寫的會在下次 finalize 被覆蓋。
- **frontmatter 出現 `openwiki_generated: true` ＝ 那頁沒寫完**：是後處理救回來的最小 block，
  要換成真的 `type`／`title`／`description` 再移除該欄。
- **`covers`／`libraries` 漏了 → 該頁被 RepoDoc ingest 靜默跳過**（`indexing/repodoc.py` 硬要 `repo`+`title`，
  且無 `node_kind: RepoDoc` 又無 `repo`+`covers` 就 skip）。dry-run 的 `skipped` 欄要看。
- **`": "`（冒號+空格）出現在 frontmatter description 任一處 → skill 被靜默跳過**；多行用 `|` block scalar
  + 全形「：」。
- **`\|` 在 `grep -E`／`pgrep` 下是字面、非「或」**——ERE 用 `|`。
- **Codex host 沒有 system-prompt 參數**，官方 system prompt 被前置進 turn；Claude host 走 `--system-prompt`。
  行為差異記在 modules/official-port-map.md，不是 bug。
- **反捏造層是刻意留空的**。舊 `verify-claims.sh`（`(src: path:line)` 錨＋逐字引文＋每個 why 必接地）已移除，
  以換取提示詞 100% 官方。官方三閘抓得到「wiki 答不出來」，抓不到「答得出來但數字是編的」——
  人 admit 時要自己獵具體數字。決策與代價見 modules/official-port-map.md。

## Modules
- [modules/official-port-map.md](modules/official-port-map.md) — 官方機制 ↔ 本地實作逐條映射、
  刻意偏離點、已退役資產與其最後 commit、誠實缺口清單。
