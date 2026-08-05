# Module: 官方 OpenWiki ↔ skill-bettor 逐機制映射（誠實帳本）

> 上游：`langchain-ai/openwiki` @ `9a02b3516fe1706d6e8f23557ac42f42a6d0896a`
> （各提示詞資產標頭記著它自己抽取自哪個 commit；以資產標頭為準，本行只是本次移植的基準）。
> 本檔回答三個問題：①哪些機制一對一映了 ②哪裡刻意不照抄、為什麼 ③哪裡是**真缺口**、代價是什麼。

## 1. 一對一映射

| 官方機制 | 上游位置 | 本地實作 |
|---|---|---|
| code-mode `init` system prompt | `src/agent/prompts/code.ts` `CODE_SYSTEM_PROMPTS.init` | `$MODULE/openwiki/init.system.md`（逐字） |
| code-mode `update` system prompt | 同上 `.update` | `$MODULE/openwiki/update.system.md`（逐字） |
| user prompt 模板 | `CODE_USER_PROMPTS.{init,update}` | `$MODULE/openwiki/user.{init,update}.md` |
| 佔位符解析 | `src/agent/prompt.ts` `createSystemPrompt` | `sync_prompts.py` `PLACEHOLDERS`（無 language、無 `.openwikiignore` 分支） |
| link-integrity 附加段 | `createLinkIntegrityInstructions()` | `sync_prompts.py` 自動附加到兩個非 chat system prompt |
| `skeleton_critic` | `src/agent/skeleton_critic.ts` | `openwiki/subagents/skeleton-critic.md` + `openwiki_subagent.sh critic` |
| `wiki_question_finder` | `src/agent/wiki_qa_subagents.ts` | `subagents/question-finder.md` + `... finder` |
| `wiki_answer_verifier` | 同上 | `subagents/answer-verifier.md` + `... verifier` |
| `beforeAgent: migrateWikiToOkf` | `src/agent/okf-middleware.ts:43` | `openwiki_post.py migrate` |
| `afterAgent: validateWikiMermaid` | `okf-middleware.ts:71` → `src/mermaid/{fences,validate}.ts` | `openwiki_post.py` `pass_mermaid` |
| `afterAgent: synchronizeWikiIndexes` | `okf-middleware.ts:76` → `src/okf/index-sync.ts` | `pass_indexes` |
| `afterAgent: validateWikiInternalLinks` | `okf-middleware.ts:83` → `src/agent/wiki-link-validator.ts` | `pass_links` |
| OKF frontmatter 規則 | `src/okf/frontmatter.ts` | `openwiki_post.py` `normalize_concept_content` 等 |
| `.last-update.json` | `src/agent/utils.ts:167` | `write_last_update`（同 schema） |

## 2. 刻意偏離（每條都有理由，不是省略）

1. **rebuild 時保留的擴展欄位更寬。** 上游 `PRESERVED_EXTENSION_FIELDS` 只有
   `openwiki_translation_pending`，所以任何頁面一旦 frontmatter 驗證失敗、走重建路徑，其他 producer
   擴展欄位全被丟掉。照抄的話，RepoDoc 路由欄位（`repo`/`commit`/`covers`/`libraries`/`node_kind`）
   會正好在「本來就壞掉」的那些頁上消失，而 `indexing/repodoc.py` 對這種頁是**靜默 skip**——
   壞頁變成 KG 裡的洞，且沒有任何訊號。故本地把 RepoDoc 欄位一併保留。
2. **Mermaid 只走啟發式。** 上游有 `mermaid` peer dep 時用真 parser，沒有時退回三條保守啟發式。
   本移植無 node，永遠是啟發式——上游文件明說這條路徑合法（少報不誤報）。代價：真 parser 會抓到的
   語法錯這裡漏掉，降級只發生在近乎確定壞掉的圖上。
3. **index 連結排序用位元組序，非 `localeCompare`。** ASCII 檔名結果相同；非 ASCII 檔名可能不同序。
4. **heading slug 用 Python `\w`**，上游是 `\p{L}\p{N}`。最接近的 stdlib 對應。
5. **Codex host 沒有 system-prompt 參數**，官方 subagent system prompt 被前置進 turn 而非佔 system role。
   Claude host 走 `--system-prompt`，與上游語意一致。
6. **subagent 邊界從 prompt 級升級為物理級。** 上游 deepagents subagent 共享同一虛擬 fs，邊界只能靠
   prose 宣告。本地每個角色跑在自己的目錄裡：critic/finder 用拋棄式 `git worktree`（finder 的
   worktree 內 `openwiki/` 被刪，故它**無法**讀 wiki）、verifier 跑在只含概念頁的快照上。
   這是**比上游更嚴**，不是偏離語意。
7. **產物落點雙份。** 官方寫 `<TARGET>/openwiki/`（照做）；額外複製一份到
   `<OUT>/repo_wiki/<slug>/` 當 durable 快照給 RepoDoc ingest，因為 `/repo/` 是 gitignored 工作區、
   target clone 隨時可能被重建。

## 3. 真缺口（沒有等價物，代價明列）

| 缺口 | 上游有什麼 | 這裡的後果 |
|---|---|---|
| **寫入時 frontmatter 回饋** | `wrapToolCall` 每次寫檔即驗，錯誤塞回 tool result 讓模型當場改 | 只有批次修復。壞頁會被 `finalize` 蓋成最小 block + `openwiki_generated: true`，語義比 agent 自己寫的差。要在下一輪 update 補 |
| **反捏造層** | 無（上游本來就沒有） | 舊 `verify-claims.sh` 提供的 `(src: path:line)` 錨、逐字引文比對、「每個 why 必 git-cite 或標 unverified」已隨回歸官方移除。官方三閘抓「wiki 答不出來」，抓不到「答得出來但數字是編的」。`engine-baseline.md` 記錄過 Flash 捏造 `100k files` 這類失效模式——在純官方閘下不保證被攔，人 admit 時要自己獵具體數字 |
| **`AGENTS.md`/`CLAUDE.md` OPENWIKI 區塊維護** | CLI 只重寫自己的 `<!-- OPENWIKI:START -->…<!-- OPENWIKI:END -->` 區塊 | 未移植。本 skill 不碰 target 的 agent 指令檔 |
| **翻譯 / `.openwikiignore` / connectors / visualizer / telemetry / personal 模式** | 全有 | 未移植。提示詞資產是以「無 language、無 ignore」解析的；要加就改 `sync_prompts.py`，別手改資產 |

**「NO API KEY」差異化已縮水（2026-08 誠實更新）。** 官方 runtime 已支援 ChatGPT 訂閱 OAuth
（`openai-chatgpt` provider，鏡 Codex CLI 的 PKCE 流程）：走 ChatGPT 訂閱跑官方 CLI 同樣不需要
API key。因此本 port 的 NO-API-KEY 差異化只剩 **Claude lane**——「用 Claude Code 訂閱 session
當推理體」仍是官方沒有的；「不設 OpenAI key」已不是。別再拿整句「零 API key」當賣點。

## 4. 已退役資產（git 即封存）

`b8d076a` 是它們最後存在的 commit：

| 檔案 | 為何退役 |
|---|---|
| `kb-ingest/repo-wiki.workflow.md` | 「蒸餾版」與官方**規範相反**（≤8 頁 vs 官方明文禁設頁數目標），且缺三閘／OKF／Mermaid／task-routing／evidence gate |
| `kb-ingest/judge.prompt.md`、`refine.prompt.md` | Opus 判官五軸 + `CONVERGED=` 迴圈，被官方 critic + QA 兩閘取代（避免兩套 rubric 打架） |
| `kb-ingest/agy-pass.sh` | Gemini(agy) 作者路徑；NO-API-KEY 遷移後作者就是本 session，此路徑無存在意義 |
| `kb-ingest/verify-claims.sh` | 見上表「反捏造層」——為換取提示詞 100% 官方而移除，代價已明列 |

`$MODULE/engine-baseline.md` **保留**：agy×判官引擎雖退役，那三個 FAILED 假設是實測資料
（claim contract → round-1 ≥80 FAIL；pre-verifier → 判官批次 −60% FAIL；輪數 ≤1+2 FAIL），
是「錨定成本擠壓覆蓋廣度」這個結論的唯一證據，不刪。

## 5. 升級上游

```sh
git -C <openwiki_repo> pull
python3 "$MODULE/port/sync_prompts.py" <openwiki_repo>   # 重生資產
git diff "$MODULE/openwiki"                                    # 上游改了什麼，一目了然
```
`--check` 模式（S0 preflight 用）只驗不寫，資產被手改或上游漂移都會紅。
提示詞若新增佔位符，`sync_prompts.py` 不會靜默留字面 `{FOO}` 給模型看——資產裡出現未解析的
`{大寫底線}` 就是訊號，補進 `PLACEHOLDERS` 再重生。
