# Module: Browser carrier content isolation

> 屬 [`gemini-conversation-research`](../SKILL.md)。本模組定義 Codex/ChatGPT Chrome 擴充功能的 P0 carrier contract。antigravity 的 CDP 腳本直接寫檔；Chrome browser-client 多了一層工具回傳面，因此「最後 stdout 是 metadata」仍不足，必須同時限制中間 browser result。

## Hard boundary

在 Gemini 對話分頁上，主會話禁止**輸出**下列能力；互動前的 locator ground truth 可由 bounded adapter 在 browser runtime 內呼叫，但結果不得回傳、不得寫 stdout：

- `tab.playwright.domSnapshot()` 或 DOM-CUA snapshot 的內容；
- conversation root 的 `textContent()`、`innerText()`；
- screenshot/OCR；
- 回傳 turn HTML、Markdown、button label、assistant answer 或 DR report 的 `evaluate()`；
- 任何把上述值交給 `nodeRepl.write`、tool stdout、chat 或 argv 的做法。

「只截一部分」不是安全邊界；若內容仍由 browser tool 回到主會話，就是 AUP violation。失敗時 fail-loud，不可把 adapter 內部 snapshot 改成主會話輸出。

## Only supported browser surfaces

從目前 checkout 的**絕對路徑** import repo-root
`scripts/extract-gemini-conversation-browser-runtime.mjs`。底層只使用以下六個 export：

- `launchGeminiDeepResearchFromPromptFile`：在使用者既有已登入 Chrome 的新 Gemini tab，從檔案讀 prompt，驗證 hash，啟用 DR、送出、點 Start research，並以 immersive panel 讀回驗證；只回 receipt。
- `inspectGeminiConversationMetadataFromBrowserTab`：只回布林值、計數、canonical URL。
- `captureGeminiGuidanceProjectionFromBrowserTab`：只掃描 document order 最後一個、明確角色為 model 的 response root；候選還必須同時屬於該 root 內的 suggestion container 且有可見文字。generic chip/source/citation container 是負例。把 labels 與最多 600 chars 的 local context 直接寫 JSON 檔；只回 receipt。找不到明確 ownership 就輸出 0 candidates，不可退回 `main` 或全頁 button 掃描。
- `clickGeminiGuidanceButtonFromProjection`：以 latest-model-scoped candidate index 點擊；caller 必須傳 capture receipt 的 projection SHA-256，adapter 單次讀取 exact bytes 並先比對，再重驗 model turn count/index、suggestion ownership、label 與 bounded parent-context SHA-256。歷史/被替換 projection、global DOM ordinal、candidate-limit 截斷或 ownership 缺失一律 fail closed；不把 label/context 回主會話。
- `submitGeminiEmergentPromptFromDecisionFile`：只接受 runner 的 `action_required + submit_emergent_prompt` decision file；caller 必須傳 runner decision SHA-256，adapter 單次讀取、先比對授權 bytes，再從相同 bytes 解析 prompt；composer fill 後以長度+SHA-256 read-back、送出後 bounded acknowledgement。最後 user turn 已是相同 prompt 時回 `already_submitted`，禁止重複污染對話；只回 receipt。
- `extractGeminiConversationFromBrowserTab`：把完整 turns/DR/citations 寫 Markdown；只回 receipt。

guided edge 的唯一公開 orchestrator 是 repo-root
`scripts/run-gemini-guided-conversation-browser-runtime.mjs` 的
`runGeminiGuidedConversationBrowserEdge`。它接 caller claim 的既有登入 `tab`、file-only run input、projection/decision/receipt/conversation paths，內部組合 capture → Bun runner → optional click 或 emergent submit/capture。`allowClick` 與 `allowSubmit` 都預設 `false`。click 必須同時有 `action_required + click_guidance_candidate + 合法 candidate index`；submit 必須有 `action_required + submit_emergent_prompt`。送出後先寫 metadata-only `response_pending` receipt，持久保存送出前 model baseline；poll 逾時保留此 journal，續跑的 `already_submitted` 只有在 conversation/run/prompt/decision/submitted-turn 全部匹配時才可沿用 baseline。不同種類的 user/model count 禁止互相比較。model turn 相對 baseline 前進、非 streaming，且兩次連續 metadata poll 的 user/model counts 與最後回答字數一致，才可抽取並回 `analysis_required`。一次呼叫只執行一條 edge。

所有 receipt 必須滿足：

```yaml
main_context_projection: metadata_only
raw_content_returned: false
receipt_json_chars: <=4096
```

完整對話與 guidance projection 只能寫到 `gemini_research/gcr/` 或另一個明確的 file sink。不要在主會話 `Read` 這些檔案。

## Safe guided-conversation sequence

1. 用 `browser.user.openTabs()` 找精確 conversation id，claim 使用者已開啟的 tab；不要另開 profile。
2. 執行 metadata probe；只輸出 receipt。
3. 隔離子代理先把 raw conversation/projection 所需的 semantic state 寫成 file-only run input；主會話只收 candidate index/kind/reason，不讀 label/context。
4. 呼叫 `runGeminiGuidedConversationBrowserEdge`，一次產生 projection、Bun decision 與 bounded receipt。known label 由 deterministic policy 選 branch，unknown label 才可由隔離子代理補 `button_kind_hint` 與非空 `button_kind_hint_reason`；hint 不得覆蓋 known classification。
5. 第一遍保持預設 `allowClick=false + allowSubmit=false`。`click_ready` 且 projection 未截斷、ownership 完整，才可用相同 file inputs 顯式重跑 `allowClick=true`；其他 action 禁止 click。
6. `submit_ready` 才可顯式重跑 `allowSubmit=true`。adapter 從 exact decision bytes 讀 emergent prompt；orchestrator 重驗唯一 composer/send ownership、送出 ACK、先落 `response_pending` model baseline journal，再要求 model turn 相對該 baseline 前進、streaming 結束與至少相隔 250ms 的兩次相同 metadata。續跑 journal 缺失/毀損/不匹配都 fail-loud；任何一步不成立都不抽半截回答。
7. 成功 submit edge 用完整 extractor 寫新 conversation Markdown 並回 `analysis_required`；委派隔離子代理把 captured auto prompt/answer 與 semantic-loss ledger 寫回 structured input，再跑 runner finalization。`truth_verification.verdict=pass` 才可跨 G7 產生 `status=completed` 的 G0-G8 trace，candidate 必須先走 `external_verify`，human-required/fail 走 `human_review`。

## Safe Deep Research launch sequence

1. 選 extension Chrome；用 `browser.tabs.new()` 在**同一已登入 profile** 建 Gemini tab，不啟動測試 profile。
2. 呼叫 `launchGeminiDeepResearchFromPromptFile({tab,promptPath})`；prompt 只從 `/tmp/dr-prompts/*.txt` 讀，不得經 argv/stdout/chat。
3. adapter 內部以 snapshot 只做互動 grounding；`更多工具` 用 `Enter`、Deep Research 用 `Space`、送出用 `Enter`、Start research 用 `Space`，每步讀回驗證。Gemini 目前對 click 可能靜默不生效，禁回退成 click-only。
4. 主會話只收 `gcr-browser-dr-launch-receipt@0.1.0`；一帳號等待約 210 秒脫鉤後才投下一題。
5. 後續只用 metadata probe 判完成，再用 extractor 寫檔。

建議在 browser runtime 內只顯式輸出最後 receipt：

```js
const adapter = await import("/absolute/repo/scripts/extract-gemini-conversation-browser-runtime.mjs");
const receipt = await adapter.captureGeminiGuidanceProjectionFromBrowserTab({
  tab,
  conversationId,
  outPath: "/absolute/repo/gemini_research/gcr/<id>-guidance-01.json",
});
nodeRepl.write(receipt);
```

不要把內部 `tab.playwright.evaluate()` 的結果另存到 top-level 變數後輸出。adapter 內部可把 raw DOM projection 留在 browser runtime memory，立即寫檔，外部唯一回傳值必須是 bounded receipt。

## Regression gate

執行：

```bash
bun run scripts/test-extract-gemini-conversation-browser-runtime.mjs
bun run scripts/test-run-gemini-guided-conversation-browser-runtime.mjs
```

測試以 raw canary 驗證 extraction/guidance 正文確實進檔案、DR/emergent prompt 只從檔案讀、receipt 不含 canary，click 只接收 capture-hash-bound latest-model ownership + label/context hashes；實際執行 stop-control detector 的 DOM fake 證明 streaming flag 入口；orchestrator 必須預設 dry-run、落檔 receipt，只對 exact-byte-grounded decision 點擊或送出，逾時保留 baseline journal，並只在兩次 metadata 穩定後抽取。adapter 可在 runtime 內呼叫 snapshot 建 locator ground truth，但禁止 `nodeRepl.write` 或隱式 `console.log`。這是 carrier-level gate；golden trace receipt 仍須另外聲明 file sink 與 metadata-only projection。
