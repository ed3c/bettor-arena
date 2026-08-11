# proof_workflow — 抖動偵測的法則與 Harness

> **讀到這個目錄的 agent：先讀完 §1 法則，再照 §2 的迴圈做事。**§3 Harness 是已實作的
> 機制與它們真的抓到過的缺陷——遇到形似的訊號時查那一節，不要重新發明。
> 法則層只留判準，實例一律住 §3。

## §1 法則

1. **收據是宣稱，對照組是行為。** 收據記「我宣稱走過這些路徑」，對照組真跑入口再看它實際碰
   了什麼。兩者必須**不會被同一個錯誤同時騙到**才算兩種獨立抵達；同一隻手寫的描述與覆蓋不算。

2. **缺席永不讀成綠。** 未執行、未分類、未覆蓋、未涵蓋各有具名出口，且必須與「真的判定為否」
   長得不一樣。對照組報 `NOT EXERCISED` **不是 pass**；抽取失敗產生的空集合會與任何東西相等，
   所以每個推導在比較前先斷言非空。

3. **量測不得擾動被量測物。** tracked artifact 判 **HEAD 位元組**，因為同一趟的 harness 步驟
   可能改寫它；每次執行都會變的位元組（暫存路徑、per-run log）**不進 digest**，否則 digest 追蹤
   的是「上次跑在哪」而不是「機制是什麼」。同一棵樹跑兩次，digest 必須相同。

4. **required 由實驗決定，不由宣告決定。** 移走它、再跑一次、看 exit 變不變。`fatal` 與 `warn`
   在原始碼裡只隔三行，讀出來的分類看起來很對而且會錯。分不出來的一律 FATAL，不得預設成 optional。

5. **宣告只能消音產出，不能消音必要輸入。** `prove_note` 可以帶路徑把一個帳本宣告為範圍外並附
   理由（機器可讀），但同樣的宣告套在必要輸入上必須無效——否則 note 就成了保綠的後門。

6. **每個新機制自帶會紅的負控。** 只被看過同意的機制，不等於已知它會不同意。**把修復擋掉再跑
   一次，必須紅**；不紅就是儀器沒接上。

7. **表面與接線分家。** 對外承諾（loop × mode × 旗標）鎖在 `surface.lock`，內部怎麼接線可以自由
   迭代而不動它。承諾要變就升版並重鎖，重鎖在版本未升時拒絕。

8. **exit code 一路原樣傳到底。** 0／2／64 意義不同；折疊它們的包裝層會讓呼叫端分不出「閘判紅」
   與「工具不在」。管線只回報最後一段，`a | b` 會吞掉 a 的失敗；`cmd; echo $?` 會吞掉 cmd 的失敗。

9. **第二個驅動者才看得見繼承來的耦合。** 只被一種 runtime 驅動過的映像，不知道自己繼承了什麼；
   基底映像的 `ENTRYPOINT`、主機的 docker context、外掛的 session，在原地全是隱形的。**要證明可攜，
   就得讓第二個東西真的驅動它一次。**

10. **主機綠不等於容器綠。** 工具存在性隨環境變（主機有 poppler、容器沒有），而 shell 也不是同一支
    （macOS 的 `sh` 吞掉的錯，Debian 的 `sh` 會吼出來）。跨環境的差異只有跨環境跑才會現形。

11. **present ≠ authenticated。** 問 `--version` 只證明 binary 在。憑證要**花一個真 turn** 驗，否則
    「有裝但沒 session」會在請求中途長成模型拒絕的樣子，而那是完全不同的修法。

12. **先消費失敗物件自己的輸出，再做差異比對。** 跟已知可用的東西比差異，會給你一堆**真的不同但
    無關**的候選，而每個候選都像答案。失敗的東西通常自己就在說原因——log、stderr、它自己的 spec。
    這條在容器那一輪被連續違反兩次（見 §3），代價是四趟重建。

## §2 -test 模式：發現抖動的迴圈

```sh
sh loopctl/loopctl.sh <loop> prove --force-receipt   # 重戳宣稱
sh loopctl/loopctl.sh <loop> test                    # 對照組驗行為
```

同一個 commit 的 equivalence control receipt 預設不可覆寫；真的要重跑同一個 HEAD，必須透過
`loopctl equivalence test --force-receipt` 顯式要求。control 只接受 clean、commit 綁定目前 HEAD 的 proof，
不得拿 `-dirty` receipt 去比 detached HEAD。命名目前 HEAD 的 clean receipts 會先是 working-tree
runtime evidence；把它們 commit 後 HEAD 必然前進，所以它們在下一個 commit 裡只可能是歷史證據，
不能把「tracked」與「仍命名目前 HEAD」假裝成可同時成立。

**訊號 → 動作**

| 看到 | 做什麼 |
|---|---|
| `GAP: <path> is REQUIRED … no proof covers it` | 真洞。把它加進該迴圈的證明，**不要**改對照組 |
| `GAP: <path> is really produced … no proof treats it as a terminus` | 若是交付終點就覆蓋它；若是 per-run scratch，用 `prove_note <id> <ledger> <理由>` **具名宣告**範圍外 |
| `misdeclared_optional` | 被實驗判為 required 卻標成 optional。改標記，不是改實驗 |
| digest 兩次不同 | 有 harness 在改自己的證據，或有 per-run 位元組進了 digest。查 §3 的漂移案例 |
| `NOT EXERCISED` | 該條**沒跑**。找出為什麼跑不到（多半是被測機制還沒提交），不要當它綠 |
| selftest 綠但你剛植入了缺陷 | 儀器沒接上。先修儀器再信任何綠 |
| 容器裡紅、主機上綠 | **不是環境噪音**。工具缺席、shell 不同、繼承的 ENTRYPOINT——查 §3「容器真跑抓到的缺陷」 |
| `present but NOT authenticated` | 有 binary 沒 session。修的是憑證怎麼進容器，不是 driver 選型 |

**兩條不可違反的處理原則**

- **修機制或修儀器，不調鈍儀器。** 把斷言放寬讓紅變綠是把問題藏起來。
- **對照組測的是「已提交的機制」**（它在 HEAD 的丟棄式 worktree 裡跑）。所以修完必須提交，
  才會看到轉綠——提交前的紅是誠實的。

**修完的收尾**（缺一步下次就會以陳舊狀態誤判）

```sh
for l in macro micro openwiki; do sh loopctl/loopctl.sh $l prove --force-receipt; done
git add -A && sh loopctl/loopctl.sh workflow lock && git add loopctl/workflow.lock
```

---

## §3 Harness

### 已實作的機制

| 檔案 | 它證明什麼 |
|---|---|
| `lib/prove.sh` | 遍歷記錄器。步驟四種：`harness`（真跑記 exit／會改帳的只 hash 記 `hashed-not-run`）、`context`（概率側讀的文檔，缺席即 FATAL）、`artifact`（末端產物，tracked 判 HEAD）、`optional`（可容忍缺席的 host 資產）、`note`（具名排除）。`--selftest` 是它自己的負控 |
| `prove_*.sh` | contract 宣告機制各自的遍歷；收據落 `data/proof-workflow/<loop>-<commit12>[-dirty].json`，帶 `proof_digest` |
| `control_{macro,micro,openwiki,equivalence}_entry.sh` | 四個入口的對照組：真跑入口、丟棄式 worktree 內逐一移走輸入分類 required／optional；equivalence 另以 Git inventory 對 proof 並把 offline/live/judge/Human 四態分記 |
| `control_workflow_lineage.sh` | lineage 機制自己的對照組（感知／stale lock／未蓋章／局外檔靜默／tag 重放） |
| `control_mcp_surface.sh` | MCP 包裝的對照組（pin 是否真擋住未提交工作／活樹零變動／無 worktree 殘留／未宣告參數被拒） |
| `lib/capture.sh` | 真跑的物理痕跡：每條 argv／exit／stdout／stderr 落 `proof_workflow/data/<run_id>/`，各自 sha256 |
| `lib/compare_control.py` | 宣稱與行為的比對；`--selftest` 兩個方向都驗 |

### 真的抓到過的缺陷（形似訊號時先查這裡）

| 缺陷 | 怎麼被發現 | 修法 |
|---|---|---|
| micro digest 兩次不同 | 連跑兩次比對 | `verify.sh` 的測試改寫 `route-result.fixture-dr.json`，且其 `output` 是每次新的 mktemp 路徑 → tracked artifact 改判 HEAD，該檔具名排除 |
| 迭代 lane 覆蓋錯兩次 | 對照組報 `_engine-run` 無覆蓋 | 先 hash 一個實例（gitignore 故不可重放、且位元組含執行路徑）→ 改成**欄位斷言** ＋ 帳本具名排除 |
| 比對器誤報已覆蓋的檔 | `request-<id>.json` 被報成 gap | family 規則取「basename 到第一個點」，對連字號 id 失效 → 改在 **ledger（目錄）層**判覆蓋 |
| 陳舊收據替新樹作答 | 修好的東西仍報紅 | 一律優先 clean 收據 → 改成**跟著樹的髒淨狀態**選 |
| selftest 假綠 | 植入缺陷後仍印 GREEN | BSD sed 無 `\|`，抽取靜默失敗產生空集合 → **每個推導比較前先斷言非空** |
| 「一變因實驗」動了兩個變因 | 七個輸入全判 required 且 exit 全相同 | 探針共用 output 目錄，`cli.ts:23` 拒絕已存在路徑 → 每次 run 獨立 output ＋ 基線前後各驗一次可重現 |
| grep 把 pattern 當選項 | 欄位明明在檔裡卻報缺失 | 每個欄位名以 `- ` 開頭 → `grep -Fq -e` |
| lock 與同一個 commit 內容不符 | replay 的 verify | lock 建完後檔案又被改，卻一起出貨 → 雜湊改讀 **index**，並加 staleness 閘 |
| 釘舊 tag 時每次調用 exit 64 | 真跑 MCP | 該表面早於 `--json` → **啟動時**檢查並具名版本與修法 |
| 改了兩支對照組，lineage trailer 卻沒點名 | commit 後讀 trailer | manifest builder 的 `LOOPS` 寫死五個而 CLI 長到七個，漏掉 `workflow` 與 `harness` → **proof_workflow 全部 20 檔不在 manifest 內，改了不動任何戳記** |
| 從 contract 取 loop 名字仍 FATAL | 換掉寫死清單後重建 | `mcp prove` 與 `policy prove` 是同一份證明、共用一份收據 → 改成**從 `writes` 推收據名**，不從命令名推 |
| `.gitignore` 不在任何收據裡 | 被問「以上機制都有收據與對照組嗎」後，把改過的檔跟 manifest 對一次 | 沒人想過要 hash 它，但它**同時決定 `--upload` 帶什麼進沙盒、以及什麼進得了 commit**——改它不動任何 digest。**「編輯過」不等於「被涵蓋」，「對照組有提到」也不等於**；唯一算數的是有收據雜湊過它 |
| `chatgpt.com` 被放行只有 opt-in 才驗到 | 同一次比對 | 真跑的 codex turn 是 opt-in，預設 `policy test` 完全碰不到它 → 補一條**靜態斷言**（host ＋ binary 綁定都要在），與那條真跑各是一種抵達，**不會被同一個錯誤同時騙過** |
| equivalence control 的 live／負控紅把 offline 軸一起標紅 | `control-equivalence-29e9e0393583.json` 抓到 judge 負控沒接上後，回讀四軸欄位 | 當初用一個 `ENTRY_RC` 同時代表「offline baseline」與「整個 control health」，所以會信是因為總 verdict 的確該紅，卻忽略欄位語義已混軸。歷史 failed receipt 凍結不改；改成分傳 `offline_rc`／`control_rc`，並加 live fail 不得降級 offline 的 selftest |
| equivalence control 從 Git 導 inventory，卻仍信 proof 自述的 SHA／digest | `1a32221` 後的獨立 standards review 偽造同名 proof 思考實驗 | 當初會信是因為「檔名集合由 Git 推導」確實堵住漏檔，卻沒堵住 proof 對同一批路徑謊報位元組。歷史 receipts 凍結不改；control 現在獨立重算 HEAD tree、逐檔 SHA、排序 manifest digest 與 counts，per-run selftest receipt 也退出 canonical digest |
| 同 HEAD 同秒並行 controls 共用 capture 目錄；缺檔的 Python exit 1 被當合格紅 | `ecce2d9` 後的獨立 standards review 併行／exit-domain 審查 | 當初會信是因為時間戳加 commit 看似唯一、而「非零就是紅」對單機序列跑也碰巧成立。改為 `mktemp` nonce 目錄、落 receipt 前重驗 stream SHA/bytes；equivalence 負控只收 2，0 是沒抓到，64 或未宣告碼都是 FATAL |
| trailer 把檔案歸錯 loop | 讀 `harness:macro:loopctl/workflow_lock.py` | `setdefault` 讓字母序最前的 loop 佔位。**收據裡沒有任何欄位陳述擁有權**（macro 真的在 commit 路徑上跑 lineage.py，workflow 真的是它的證明，兩邊都 `ran`、位元組相同）→ 不換更好的裁決規則，改成**列出全部認領者** `macro+workflow`；六個檔如此，而這也把單一標籤藏起來的事實掀出來：改它們會動**兩份** digest |

### 容器與沙盒（OrbStack / Apple container / OpenShell）

外部調用走容器，所以容器**是第二個驅動者**（法則 9）：它會照出主機上永遠看不見的耦合。

| 機制 | 它是什麼 |
|---|---|
| `loopctl/Dockerfile` | OCI 映像。確定性基座（git／python3／bun／node／ruff／poppler）**build 時就檢查**；兩支 driver 不 build-check，因為安裝管道與認證都不是 build 時能判定的事 |
| `loopctl/container-run.sh` | runtime 無關的 wrapper。`LOOPCTL_RUNTIME` 可覆寫，否則 Apple `container` 優先、退 docker、都沒有即 FATAL。旗標對照過 Apple container 自己的 command reference，不是猜的 |
| `loopctl/container_preflight.sh` | 容器內的預檢。**driver 各花一個真 turn**，把 absent／present-but-unauthenticated／authenticated 分成三種狀態 |

**兩種隔離模型，風險面不同**——選錯不是效能問題是安全問題：

| | bind-mount（Docker） | upload（OpenShell sandbox） |
|---|---|---|
| 主機樹 | 容器可達，靠 `--user` 避免 root 檔案污染你的 `.git` | **不可達**，容器拿到的是副本 |
| **`.git`** | 在 | **不在**（實測：上傳含所有原始碼與 dotfile，唯獨沒有 `.git`） |
| 網路 | 無管制 | YAML policy，proxy 在 HTTP method/path 層強制，**且能對 MCP `tools/call` 的 tool 名與 params 下規則** |

**因此分工是硬的，不是偏好**——loopctl 的身份模型整個建在 git 上（證明蓋 commit、replay checkout ref、
lineage 讀 index、收據判 HEAD 位元組）：

| 用途 | 用哪個 | 為什麼 |
|---|---|---|
| 證明／對照組／replay／lineage | **bind-mount** | 需要 `.git`。**沒有 git 的樹上長不出 git 錨定的證明** |
| 跑 agent turn（外部客戶調用） | **OpenShell sandbox** | 那才是它解的問題：網路政策、MCP 工具層規則、主機樹不可達 |

把證明機制塞進上傳模型，等於為了「上傳比較安全」拆掉 git 錨定——那是把整套可追溯性換掉。

### 容器真跑抓到的缺陷

| 缺陷 | 怎麼被發現 | 修法 |
|---|---|---|
| `failed to query local Docker daemon` 但 `docker ps` 兩行前才成功 | openshell `--from` 建映像 | OrbStack 靠 docker **context**（CLI 層概念）導向自己的 socket；直接說協議的東西走 `/var/run/docker.sock`，而跑過 Docker Desktop 的機器那裡是**死 socket → refused 不是 absent** → wrapper 自動導向並註明 |
| `ContainerRestarting`，沒有任何一行說原因 | 基準 sandbox 成功 → 一變因證明問題在我的映像；**但差異比對連錯兩次**（ENTRYPOINT、CMD——都是真差異，都不是原因，因為 runtime 本來就覆寫 entrypoint） | 讀失敗容器的 log，它第一次就寫著：`sandbox user 'sandbox' not found in image` → 加 user／group（法則 12） |
| 同上，下一輪 | 同樣讀 log | `trusted ip helper not found; checked /usr/sbin/ip` → proxy 模式需要 `iproute2` |
| 上傳 `Permission denied`，但那是 0644 人人可讀的檔 | 進運行中的 sandbox 看實際權限 | **不是 unix 權限，是政策層拒絕**：home 不在受管 workspace。OPA 治理的沙盒會拒絕它沒被告知的路徑 → home 設為 `/sandbox` |
| `cannot open loopctl/…`（猜路徑兩次） | 開一個只 `ls` 的 sandbox 看檔案落在哪 | 絕對 `WorkingDir` 會變成 agent workspace，而上傳落在 **HOME**——我把兩者拆成兩處 → `WORKDIR /sandbox` |
| `preflight FATAL: not inside a git work tree` | 列出上傳內容 | **上傳不含 `.git`**。不是參數能繞過的事，見上方分工表 |
| `error: unzip is required to install bun` | build 失敗 | 錯誤訊息直接指名 → 補 `unzip` |
| `curl \| bash` 吞掉 curl 的失敗 | 修上一條時發現 | 管線只回報最後一段，下載失敗會把空腳本餵給 bash 而該層照樣成功 → 拆成下載、執行兩步 |
| `pdftotext not found` → ingest FATAL | 容器內跑 macro 證明 | 主機有 poppler、映像沒有（法則 10）→ 補 `poppler-utils` |
| 收據裡的說明文字被吃掉，且執行了一個雜散命令 | 容器的 `sh` 吼出 `loopctl.sh: not found` | `prove_note` 文字裡的**反引號在雙引號參數裡是命令替換**；macOS 上靜默、Debian 上現形 → 改單引號，全 harness 掃過只有這一處 |
| 背景任務回報 exit 0 而實際 exit 1 | 對照 build log | 我自己用 `cmd; echo EXIT=$?` 收尾，**把狀態碼吞掉**（法則 8）→ 用 `&&` 串接 |

### 認證：實測結果（不是推論）

容器內掛載 host session 後，`container_preflight.sh` 各花一個真 turn：

```
codex exec (read-only role)   authenticated — 真的答了一個 turn
claude -p  (writing role)     present but NOT authenticated (exit 1)
```

掛 `~/.codex` 帶得進 session，掛 `~/.claude` ＋ `~/.claude.json` **帶不進**（憑證在 macOS
Keychain）。這是 §1 法則 11 的實例：兩支都 `present`，只有真跑才分得出來。

**寫入角色現在通了，但不是靠掛載**——見下一節。掛載這條路已經放棄，不要再試。

### 寫入角色的憑證：不要在容器內登入

Keychain 掛不進去，但**在容器內登入並持久化 HOME 是最差的一條**——token 會落在
`~/.claude/.credentials.json`，而沙盒存在的理由就是裡面跑的東西不可信。

正解是把憑證留在外面：host 上 `claude setup-token` 鑄一個長效 bearer，交給 gateway

```
openshell provider create --name claude-code --type generic \
  --credential CLAUDE_CODE_OAUTH_TOKEN=<token>
openshell sandbox create --provider claude-code --policy loopctl/sandbox-policy.yaml -- claude
```

沙盒拿到的不是值，是佔位符——實測（gateway 0.0.59，探針沙盒 `printenv`）：

```
CLAUDE_CODE_OAUTH_TOKEN=openshell:resolve:env:v2540341773931874873_CLAUDE_CODE_OAUTH_TOKEN
```

內建 `claude-code` provider spec 只自動探索 `ANTHROPIC_API_KEY`／`CLAUDE_API_KEY`，但那是探索
清單不是限制：`--type generic` 接受任意 key 名。

**佔位符是 capability 不是 secret**——沙盒內每個 process 都讀得到它，任何能連到
`api.anthropic.com` 的都能讓 proxy 替它簽名。所以 policy 的 `binaries:` 綁定在這個模型下
**是唯一還在守線的東西**，「token 又不在裡面，binary 清單只是多一層」剛好講反。

| 測試（`--network none`，隔絕網路才分得出「本地拒絕」與「送出失敗」） | 結果 |
|---|---|
| 無 token | `Not logged in · Please run /login`，**不碰網路** |
| 亂填 `not-a-token` | `Unable to connect (ENOTIMP)`，送出了 |
| 佔位符字串 | 同上，送出了 |

所以 client 端**完全不檢查 token 形狀**，佔位符不會在打到 proxy 前被打回。

`container test` 把這兩臂都留下，但**判在「有沒有那句本地拒絕」而不是判連線錯誤**——連線錯誤要等
client 重試耗盡才出現，第一版等它等到 `timeout` 砍掉、以 exit 124 誤判成紅；拒絕那句是秒回的，
「窗內沒出現」才是便宜又正確的訊號。無 token 那臂先跑，它是負控制：**少了它，「佔位符沒被拒絕」
可能只是那句話換了寫法而永遠不會出現**。

**端到端真跑（policy 治理下的沙盒，一顆真 token，一個真 turn）**：

```
ENV=openshell:resolve:env:v8831555111520736500_CLAUDE_CODE_OAUTH_TOKEN
--- turn:
ok
TURN_RC=0
```

**兩件事必須同時成立，少一件另一件就沒有價值**——turn 通了但 token 躺在環境裡，只是把祕密裝進盒子；
佔位符買不到一個 turn，那就是壞掉的沙盒。所以 `policy test` 的 `credential-turn` 兩個都判：
`sandbox-holds-a-placeholder-not-the-token` ＋ `placeholder-buys-a-real-turn`。

分工：`container test` 只驗 client 接受形狀（不需要憑證，跑得起來就跑）；**proxy 到底有沒有替換
是 gateway 的性質，驗在 gateway 所在的那一支**，且 gate 在 provider 存在與否——對照組不能自己
鑄訂閱 token，**沒有就是 NOT EXERCISED，不是通過**。

於是兩個寫入 carrier 都走 provider placeholder；任一邊都不掛載 host credential store。

### codex 在 OpenShell 內寫入：custom provider 路徑

```
sh loopctl/codex-sandbox.sh --dry-run "<prompt>"     # 前置全跑、不建任何東西
sh loopctl/codex-sandbox.sh "<prompt>"               # 真跑，改動檔案下載回 data/codex-sandbox/<utc>/
```

**被推翻的是「Codex 必須拿真 session」這個過度擴張的結論。**量測只證明 ordinary
`auth.json` 路徑會在請求前解析 JWT，所以 placeholder 塞進 `auth.json` 會死在本地。Codex 的
custom model provider 另有 `env_key` 與 `env_http_headers`：同步的 runtime-env policy 把 access
placeholder 放進 Authorization、account placeholder 放進 `ChatGPT-Account-ID`，直接送往
`https://chatgpt.com/backend-api/codex`；OpenShell proxy 再替換真值。sandbox 不讀、不掛、不重建
`~/.codex/auth.json`。`supports_websockets=false` 讓這條路固定走可檢查的 HTTPS。

四個關卡各自的真相（每一個都只有真跑才看得見）：

| 症狀 | 真因 |
|---|---|
| `invalid ID token format`／`agent identity JWT payload is not valid JSON` | placeholder 被餵進會本地解析 JWT 的 login／agent-identity 路徑；修法是改走同步的 custom model provider，不是把真 `auth.json` 搬進 sandbox |
| `HTTP CONNECT failed with status 403`，而 policy 明明列了 codex | npm 把 codex 裝成 **`.js` shim**，真正連線的是它 spawn 出來的 vendored 原生檔，**policy 綁的路徑沒有任何 process 擁有**。claude 沒事只因為 npm 給的是 ELF。Dockerfile 改指原生檔並在 build 期斷言 ELF |
| 模型答了、tokens 也燒了，但沒有檔案 | codex 用 **bubblewrap 關自己的 shell 指令**，在容器內建不了 user namespace。`-s danger-full-access` 關掉那層內沙盒——**不是放寬邊界**：外層的 Landlock／seccomp／出口白名單全在，這正是 OpenShell 自己丟掉 AppArmor 時給的同一個理由 |
| model 回 401 missing bearer | custom provider 沒選中、`env_key` 沒指向 provider placeholder，或 provider 沒掛上；先驗 projection、provider type 與 placeholder 形狀，禁 fallback 到真 token |

`codex-openshell-config.py --policy .runtime-env/policies/codex-openshell-chatgpt-placeholder.json --selftest`
驗 synchronized policy 的 endpoint、env 名、HTTPS transport
與 `CODEX_AUTH_JSON` 禁令；`codex-sandbox.sh --dry-run` 另外把 provider 查不到、gateway 問不到、
model 名不合法分流。provider 真值的刷新屬 gateway/bootstrap plane，不再由 sandbox 解析 token 到期日。

改動怎麼回來：upload 沙盒**沒有 `.git`**，所以不是 diff，是**前後各一份雜湊清單**比對。第一版用
`find -newer` 時間戳，而**時間戳看不見刪除**——那種包比誠實的包更糟：套用的人會把 agent 決定移除的
檔案重新長回來。504 個檔案雜湊兩次幾乎免費，沒有理由取那個有損的讀數。

刪除以**清單**形式回來（`_codex_deleted.txt`），不是以「檔案不在包裡」的形式——tar 沒辦法裝一個
不存在的檔，所以不讀清單就套用會還原掉那些刪除。腳本印出來時加 `+`／`-` 前綴，而 `-` 那些**不會
自動套用**。

### 自動許可的 token 成本：量出來的方向與參考文件相反

```
sh loopctl/automode-bench.sh --dry-run
sh loopctl/automode-bench.sh --runs 3          # 兩個沙盒，只差一個變因
```

參考文件預測自動許可會炸 token（Import Cascade／全量測試日誌／巨型 `find` payload），防法是
`.claudeignore` ＋ 細粒度授權。**同一任務、同一棵樹、兩個沙盒各跑三次，結果是有機制的那組比較貴**：

```
arm  run     cache-w   cache-r  output  turns   cost$
off  1–3    8.9–14.8k  334–385k  1520–1789   9–10  0.177–0.231
on   1–3   23.7–28.6k  267–339k  1188–1642    6–8  0.241–0.283
```

**三個欄位完全不重疊**：cache-write（on 約 2×）、turns（on 較少）、cost（on 高約 22%）。六次全部答對，
兩組 `permission_denials` **都是 0**。

兩個推翻：

- **帳單由 cache-WRITE 主導，不是由讀進多少 context 主導。** 文件用「Context Window 被塞滿」推論成本，
  但 cache 寫入計價遠高於讀取——**讀得多而能重用 cache 的那組反而便宜**。ON 組工具面變窄→prefix 變了→
  重寫 cache，讀得少卻付得多。
- **限制工具不等於省錢**，它換的是策略：沒有 Bash 的那組改用 Read/Glob/Grep，turn 數反而較少但每次
  都在寫新 cache。

**適用範圍要講清楚**：這個任務**沒有觸發**文件講的那三顆炸彈（denials 全 0、沒有跑全量測試、沒有全域
`find`）。所以量到的是「在這個 repo 的這個任務上，該機制較貴」，**不是**「文件錯了」。要驗它的宣稱得
換一個真的會誘發貪婪探勘的任務。

n=1 時中位數有兩個欄位指反方向，n=3 才翻正——所以報表**先印每一次的原始數字再印中位數**：
**組內散布比組間差異大的時候，中位數是騙人的。**

#### Codex CLI：同樣的實驗，結論是「量不到」

```
sh loopctl/automode-bench.sh --platform codex --runs 3
```

```
arm  run   input(incl cached)   cached-in   output  turns
off  1–3   82738/82024/59876    37/39/47k   235/220/224   1
on   1–3   86841/67715/49519    76/59/42k   480/378/239   1
```

**每個欄位都重疊**，中位數差 -17.4% 而組內散布遠大於它。六次全答對、全部一個 turn。所以 codex 這邊
的誠實結論是**沒有可偵測的差異**，不是「機制沒用」也不是「機制有用」——n=3 分不開。

兩個平台的差異本身才是重點：**claude 有三個欄位完全不重疊、codex 一個都沒有**。claude 的成本被
cache-write 主導，而 **codex 這六次的 `cache_write_input_tokens` 全是 0**——讓 claude 那組變貴的
那個機制在 codex 的帳上根本不存在。

#### 三個只有真跑才看得見的（codex）

| 症狀 | 真因 |
|---|---|
| guarded 那組三次全空 | `-a never` **不是 `codex exec` 的旗標**。我從 help 裡 `--json` 附近的 `always\|never\|auto` 推論它——**那是 `--color` 的**。正解是 `-c approval_policy=never`。讀 grep 命中的鄰近行不等於讀介面 |
| 報表在印出正確表格「之後」當掉 | codex **沒有 cost 欄位**，`statistics.median` 對空集合拋例外。讀取端我寫了 `cost=None` 的案例，**彙總端沒有**——一個實例修好不等於那一類修好 |
| PDF 的 `[output_limits]` 設不上去 | `max_stdout_lines` / `max_stdout_bytes` 在 codex 0.147 **不存在**。真正的槓桿是 `tool_output_token_limit` |

**`--strict-config` 是 load-bearing 的**：少了它，拼錯的 guard 鍵會被靜默忽略，guarded 那組偷偷變成
第二份 unguarded，**而每個數字都還是合理的**。selftest 有一條專門守它。

**沙盒那個軸在 OpenShell 內量不到，而這是量出來的**：四格各跑一次，`-s read-only` 與
`-s workspace-write` 都死在 `bwrap: No permissions to create a new namespace`，只有
`danger-full-access` 與 bypass 旗標會執行。所以兩組的沙盒模式**釘死不變**，dry-run 直接把
「NOT VARIED」印出來——只跑活著的格子卻宣稱做了 2×2，是報告一個從未發生的比較。

還有一個省下三次 turn 的小機制：**第一次跑出空結果就中止該組**。旗標被拒的那次產生了三份一模一樣的
空檔案，而原因就躺在旁邊的 `.err` 裡沒人讀。

#### 這兩支刻意沒有對照組

`automode-bench.sh` **本身就是對照組**——兩個沙盒只差一個變因。會無聲反轉它結論的不是它自己，是
**評分器**（把「被擋到答不出來」算成省 token 的贏）與**報表**（把單臂當成比較、把缺席的 cost 印成 0），
那兩個各有 selftest 並由收據跑。再造一個燒真 token 的對照組去檢查一個燒真 token 的實驗，買不到東西。

**但 `.gitignore` 就不是這樣。** 它被雜湊，記錄了「規則是哪些位元組」，**卻沒有任何東西量過它真的擋住
什麼**。被問第二次「都有成對嗎」才發現：只要 filter 哪天不生效，每個沙盒都會靜默收到 run traces、
下載回來的 agent 草稿與 benchmark 證據，**而收據全程是綠的**。現在 `container test` 真的開一個沙盒
去驗——**兩個方向一起驗**：被忽略的路徑要不在、被追蹤的要在。**只驗「不在」的話，上傳整個失敗長得
一模一樣。**

還有一個陷阱：文件的 `.claudeignore` 模板封鎖 `*.lock`，照抄會連 `loopctl/workflow.lock` 與
`surface.lock` 一起封掉——那兩個是 manifest 與表面契約，**不是依賴鎖檔，而且正是這個任務要找的東西**。
ON 組改用具名鎖檔，`--selftest` 有一條專門擋這個萬用字元回來。

### 邊界（這些不在證明裡，而且是刻意的）

- **沒有黃燈，而且不會有。** 提案是「紅專注在可行的硬門檻，其餘只警告」。量過之後否決：
  **紅燈本來就沒有擋住任何東西**——`workflow lock` 只要求收據存在不要求為綠，commit 閘只要求
  lock 新鮮，`equivalence` 紅著的時候連續三個 commit 照樣落地。所以警告層買不到任何目前沒有的
  東西，**只會多一個可以停車的地方**；而這個 repo 抓到的缺陷幾乎全是同一種形狀——「未驗證」悄悄
  變成「沒問題」。真正的問題（沒人清得掉的紅會變成沒人讀的紅）用**可行動性**解，不用顏色解：
  每個紅在摘要裡帶**它自己的第一句抱怨**與**清掉它的路線**，而路線由**機制自己印 `NEXT:`** 供給，
  不在證明旁邊另立一份會漂的清單。**沒有宣告路線的紅要明說它沒有**——留白會被讀成「不存在路線」。

- **`loopctl/workflow.lock` 不入任何證明。** 它由收據長出；hash 它會讓 digest 依賴一個依賴
  digest 的檔，每次重建都動且**永不收斂而全程看起來是綠的**。builder 會直接拒絕這種循環。
- **概率性段落預設不跑。** openwiki 對照組的探針靠比對 exit code，而每跑每變的輸出會讓整份分類
  失去意義。要存在性證明用 `--full`（opt-in，且只當存在性證明，不參與分類）。
- **死鎖出口**：機制自己壞掉時，`Workflow-Lineage-Override: <理由>` 寫進 commit message，理由必填。
