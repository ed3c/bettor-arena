# kb-ingest — openwiki 移植層的法則與 Harness

> 這是給**下一個讀 kb-ingest 的 agent** 的系統提示詞。先讀 §1 法則，動手前跑 §2 的閘。
> 實例、真的抓到過的缺陷、邊界全在 §3 Harness，**不要把實例往前搬進法則**。
> 逐檔用途寫在 `port/README.md`；證明與對照組的設計法則在 `proof_workflow/README.md`。

## §1 法則

1. **三個根不能塌成一個。** `MODULE_ROOT`＝這個目錄，模組能自證的一切都從它解析；`HOST_ROOT`＝
   它被安裝進去的 checkout，**只有 host-profile 檢查能碰**；**刻意沒有第三個根**——共享 skill
   registry 在哪解析是那個 registry 的契約，從這裡斷言它，等於讓一個必須能被 `cp` 到任何 repo
   的模組去依賴一個沒有 repo 擁有的 checkout。
2. **「分不出來」要有自己的出口。** exit `3` 不是比 `1` 更糟的 `1`：它是「這個閘無法建立它該檢查的
   東西」（沒有 host 宣告、宣告解析不了、profile 名字不認得、不在 git worktree）。**塌進 fail
   已經很糟，塌進靜默通過是災難。**
3. **upstream 位元組與本地新增分屬不同目錄，界線做成物理的。** `openwiki/` 只放機器產生的官方資產，
   每份包在 `OPENWIKI-OFFICIAL:BEGIN/END` 裡；`port/` 放其他一切。手寫的東西**永遠不進** `openwiki/`。
4. **逐字宣稱要用產生器，不用手抄。** 「prompt 與 upstream 位元組相同」這種宣稱，手抄一千行之後
   **第一個 typo 就讓它不可證偽**；產生器讓 `git diff` 變成證明、升級 upstream 變成一道指令。
5. **prompt 承諾的事若其實由 code 完成，就得把那層 code 也移植。** 官方 prompt 把 middleware 的
   效果當成既成事實在講；少了那層，那些句子是空頭支票。
6. **讀取邊界要物理化，不能用散文宣告。** 邊界＝子行程看得見的目錄：critic 給拋棄式 worktree、
   finder 給**刪掉 `openwiki/`** 的同一個 worktree、verifier 給只有 wiki 的暫存副本。
   一個偷看得到 source 的 verifier 是在**從 source 回答**，不是在測 wiki 能不能回答。
7. **可搬移性要真搬一次驗。** 在它原地跑 gate 證明不了什麼——那裡每個 host 假設都是**碰巧**滿足的。
   建一個拋棄式 host、換名字換深度複製進去、再跑。
8. **正控制單獨不算數：每個失敗模式都要回一個具體的 exit code。** 只有正控制時，
   「檢查通過」與「檢查什麼都沒解析到卻回傳成功」**長得一模一樣**——那正是搬移重構的失敗方式。
9. **搬移測試不接進 gate。** 接了就變成 gate 呼叫「那支呼叫 gate 的腳本」。
10. **`--dry-run` 用真組件，只按名字跳過 LLM。** 缺席要具名（例如 `skipped-no-skeleton`），
    不可靜默通過；不可逆的段落要對**暫存副本**跑，並在前後做位元組比對。
11. **與 upstream 的偏離要寫下來。** 不要假設 byte-equality：mermaid 走啟發式、index 排序用位元組
    而非 `localeCompare`、slug 用 Python `\w`。**低估可以，高估不行。**

## §2 動手前後的閘（依序）

```sh
python3 kb-ingest/port/sync_prompts.py <openwiki_repo> --check   # 官方資產有沒有漂
python3 kb-ingest/check_repo_wiki_converge.py                    # 模組自證：0 pass · 1 fail · 3 cannot tell
bash    kb-ingest/port/test_relocation.sh                        # 換名換深度真搬一次
bash    kb-ingest/port/wiki_update_worker.sh <request.json> --dry-run
sh      loopctl/loopctl.sh openwiki test                         # 入口對照組
```

**訊號 → 動作**

| 看到 | 先做這件事 |
|---|---|
| gate 回 `3` | **不是 fail。** 先補齊 host 宣告／profile／worktree，再談對錯 |
| `sync_prompts --check` 非零 | 要嘛 upstream 升級了，要嘛有人手改了 `openwiki/`。**看 `git diff`，別重抄** |
| gate 在別的 repo 綠、在這裡紅（或反過來） | 你把 MODULE_ROOT 與 HOST_ROOT 塌成一個了（法則 1） |
| 搬移測試某一格回錯 exit code | 那個失敗模式**不再可辨識**——修出口，不要放寬斷言 |
| dry-run 全綠但真跑什麼都沒改 | 看 `changed_wiki_paths`，並確認你讀的是**內容**差異不是 status 差異（§3 有這個缺陷的全貌） |
| skill 名字解析到本地 fork | 指回單一 checkout；同名不同源是幻覺等價 |

## §3 Harness

### 已實作的機制（改動前先認得它們）

| 檔 | 它保證什麼 |
|---|---|
| `check_repo_wiki_converge.py` | 感知閘：資產是機器產生的、post passes 會跑、三個 subagent 的讀取邊界真的成立、RepoDoc lane 仍收 wiki |
| `port/sync_prompts.py` | 官方 prompt 逐字抽取；`--check` 讓漂移變成非零 exit |
| `port/openwiki_post.py` | upstream `okf-middleware.ts` 的 code-owned 段（`migrate` / `finalize`）；偏離逐條寫在 docstring |
| `port/openwiki_subagent.sh` | critic／finder／verifier 各自的**目錄級**讀取邊界，靠 worktree 與副本做成物理的 |
| `port/wiki_update_worker.sh` | 請求 → 前檢 → LLM 重生 → 審查閘 → post passes → 收據；`--dry-run` 走完每個確定性接縫 |
| `port/test_relocation.sh` | 換名換深度真搬一次，並逐一植入失敗模式要求對應 exit code |
| `host-profile.json` | 這個模組被安裝進哪種 host 的宣告；唯一允許碰 HOST_ROOT 的入口 |

### 真的抓到過的缺陷（形似訊號時先查這裡）

| 症狀 | 真因 |
|---|---|
| 模組換個 repo／換個深度就失效 | `parents[1]` 把 MODULE_ROOT 與 HOST_ROOT **塌成一個**，整條 lane 被釘死在一個 repo 的一個深度 |
| gate 綠但其實什麼都沒檢查到 | 只有正控制。**「通過」與「解析不到卻回傳成功」不可分辨** → 每個失敗模式各給一個 exit code |
| worker 以降級狀態默默跑完 | 它應該 re-exec 進 bash 而不是繼續跑（`ca72a92`）——**降級不可以是靜默的** |
| skill 名字撞到本地 fork | `.agents/skills/repo-wiki-converge` 應該是指向單一 checkout 的 symlink。**同名不同源＝幻覺等價** → 改名分家為 `openwiki-port` |
| dry-run 全綠、真跑 `changed_wiki_paths=0` | **量測缺陷，不是管線缺陷。** 舊的邊界閘比對兩份 `git status --porcelain`，而一個**本來就髒**的檔案不論被改寫多少，porcelain 行都是同一行 ` M path` → 新增行為空 → 計數 0。收據裡那次跑了 **53 個 turn**、模型回報 17 頁全部完成。改成比對**內容雜湊** |
| 同一個盲點的另一半（更嚴重） | 擋「寫到 `openwiki/` 之外」的 stray 檢查用的是同一份差集：**目標檔案只要本來就髒，這道防線就直接被繞過**。內容雜湊修掉兩半 |
| 改寫 wiki 卻沒有任何 digest 動 | **29 個檔只有 4 個在 manifest 裡**（index／architecture／quickstart／.last-update）。其餘 25 頁改了不動 digest、不畫 trailer——**在一個以產出這些頁為唯一目的的迴圈裡**。改成從 `git ls-files` 導出全部頁面（頁面由重生流程自己增刪，寫死清單下一輪就過期）|

### 邊界（刻意不做的）

- **`test_relocation.sh` 不接進 gate**（法則 9），所以它要靠 SKILL.md 的 S0 被想起來，
  不會自己跑。動過 gate 或搬過模組**就得手動跑它**。
- **不從這裡斷言共享 skill registry**（法則 1）。
- **概率性段落預設不跑**：對照組靠比對 exit code，而每跑每變的輸出會讓分類失去意義；
  要存在性證明用 `CONTROL_OPENWIKI_FULL=1`，**且只當存在性證明，不參與分類**。
- **不追求與 upstream byte-equality**（法則 11）；追求的是**偏離被寫下來**。
