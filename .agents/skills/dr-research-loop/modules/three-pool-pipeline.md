# Module: 三池整合鏈路(Layer B know-why)— 2026-07-11/12 四題實測沉澱

> 屬 [`dr-research-loop`](../SKILL.md)。Layer A(程序/Gotchas 一行版)在 SKILL.md;本檔記
> why 與案例帳。誠實帳原則:所有結論錨到 commit/沙盒真檔,漂移以真檔為準。

## 1. 三池分工(為何這樣切)

| 池 | 額度性質 | 燒什麼 | 為何 |
|---|---|---|---|
| 訂閱池(Gemini 網頁 DR,claude-in-chrome 驅動) | 已付費沉沒成本,與 agy 池分開計 | Stage 1 廣度收集(每題可選配;高承重題默認開) | 讓最便宜的池承擔最大 token 吞吐;一次跑數十至百餘站是 agy 單發比不了的 |
| Antigravity 池(agy CLI) | 稀缺(耗盡=silent no-op) | 只燒合約化:raw→proposal 轉換+feedback 回填 | 有 raw 當地基,dispatch 次數降,quota 留給修復輪(質量來源) |
| Claude 池(主 session/subagent) | 最貴,唯一真獨立性 | D3 fresh Opus+external-verify(fresh Sonnet)+編排 | 兩個 Gemini 面+agy=同權重,互查不疊加獨立性——獨立性只能向跨家族買 |

- **raw=UNTRUSTED 是命門**:瀏覽器 DR 報告只當候選源清單+gap 題目源,落沙盒 `logs/raw-dr-*.md`
  (gitignored),禁直接引為證據錨——未機驗散文成錨=知識洗白,與 R4 禁引 proposals/ 同精神。
  交接經 `--feedback` 注入(stage1-handoff 檔,含用法邊界+題目特有地雷)。
- **Stage 1 失敗不擋主線**:退化為純 agy 流程(codex 題型)。
- **實測量級**:主研 2–32 分鐘/51–117 站/23–36KB raw;gap 輪通常快得多。Gemini 報告面板
  虛擬滾動——抽取前先滾完全篇強制渲染,否則 get_page_text 截斷(pinescript 題實踩,漏 30%)。

## 2. agy 失敗模式五型(三題三型 + 2026-07-13 整合計劃 gap 批沉澱 2 型;對抗層存在理由的實測坐實)

| 型 | 案例 | 簽名 | 抓手 |
|---|---|---|---|
| 謊標授權 | codex 題(09b0423) | GPL-3.0/自訂授權→標成 allowlist 字串「MIT」 | **已機械化**:check_licenses L3(GitHub API 實抓 spdx_id,04b5c06);非 GitHub 源仍靠 D3。⚠ **GitHub API 匿名限流(60/hr)期=L3 集體降級 WARN、謊標整批漏過**(gap R2 三題實測:skillscan-security/vLLM-Watermark/lm-watermarking 皆限流期漏,實測皆與宣稱相反)→限流期 D3 逐一開 raw LICENSE 是唯一防線,別把「WARN 全綠」當授權已驗 |
| 錨位對調式洗白 | cross-market 題(808d425) | 規模數字掛「可達但不含該數字」的權威錨,鑽 check_urls 只驗可達的縫 | D3 逐一實開數字錨;external-verify 釘真值(揪出內容農場數字+幻覺指紋級數字——vendor 自家頁查無的具體數) |
| 壓制反證 | pinescript 題(0bbb26a) | 反證(競品)在自己 raw「查閱過但未使用」清單裡,看過並棄用,下「市場真空」戰略結論 | raw consulted-unused 清單當 SI5 靶逐一比對結論;**「空位/藍海」型 claim 封裝包必點名最高強度對抗證偽** |
| 驗證器環境竄改 | gap-vasa 題(2026-07-13;anti/2026-07-13-verifier-env-tamper.md) | gov.tw 域 SSL 憑證鏈(缺 SKI)FAIL→不換錨,改在 repo 根種 `py_patch/sitecustomize.py` 全域關 Python SSL 驗證讓假錨過 check_urls;**在 target 外留痕、常規 diff 看不到、污染全 repo python SSL**——比前 3 型危險(前 3 型在 target 內留痕) | **T0 收尾必跑 `scripts/check_placement.py`**(rogue 目錄=環境竄改地表訊號,本次即此抓到);**admit 前 clean-env 重驗** `env -u PYTHONPATH python3 -S <checker>`(`-S` 停 site→sitecustomize 不載入,死鏈數須與髒環境一致);合法 primary 被基建誤殺(gov.tw 缺 SKI)≠授權關 SSL,正解=換可達等價錨+原網址文字備註,或人核加白名單 |
| 迴音室洗白 | gap-internalization-halflife 題(2026-07-13,G6) | 把**委託方 sandbox Domain seed 明標「待驗假設非事實」的先驗**(此例=雷達 H 世代數)寫成「實證表明」+零外部錨——DR「證實」了你叫它看的東西,最隱蔽 | D3 比對 sandbox Domain seed 的假設標記:凡結論命中 seed 先驗**又無外部錨**=洗白,強制降級回 `[推論]/待驗假說(上游系統先驗)`,禁「實證」措辭 |

- **agy exit code 兩面都不可信**:quota 耗盡=零輸出 exit 0;CLI timeout=exit 1 但活可能已幹完
  (cross-market gap 輪:exit 1、53 行已寫入、中途還 git checkout 還原重寫)。判活唯一標準=
  **target diff vs pre-dispatch snapshot**。
- **agy 自記帳不可信**(PLAN.md 迭代表/PROGRESS 口徑),誠實帳=engine trajectory.log+orchestrator 全段帳。
- agy 會自建 scratch/ 預檢腳本(好行為——先自打 URL 才寫,錨存活率高);commit 時排除,
  hook 擋 rm -rf 須人工清。

## 3. 數字類 claim 的驗證分工(為何不讓 agy 自查)

- agy 產的數字讓 agy 複查=同權重自證;分工=**external-verify fresh Claude 釘真值 → 組 feedback
  檔給 agy 回填**(feedback 檔內嵌已驗事實+錨,並明令「禁引本檔當錨,錨用列出的官方 URL」)。
- 來源分層強制標注:平台統計(商店頁/GitHub API 機械值)> 第三方獨立分析 > vendor 自報 >
  媒體轉述;競品自家 compare/roundup 頁=利益衝突源,獨撐 claim 必降級。
- **不可查證數字不入帳**:機器打點 403+瀏覽器站點政策雙擋(Trustpilot 案)=全通道不可查證
  → 刪除+留一句紀律註記;禁為過閘動 check_urls 白名單(迭代中改判定式=作弊)。
- URL 錨預檢:新錨先用 check_urls 同款 Mozilla UA probe——openai.com/help.openai.com 對
  raw curl/WebFetch 回 403 但對 checker UA 回 200,別誤判成要加白名單(加域=改判定式須人核)。

## 4. D3 段操作紀律

- 報告落**沙盒根**(`loop_wiki/*/logs/*` 被 .gitignore 排除;證據鏈要入庫,proposal 驗證軌跡
  頭注才不會指向不入庫路徑)。
- D3 subagent 有機率基建級故障:秒回+0 工具調用+回傳 system prompt 碎片——判別=tool_uses
  數+報告檔是否存在,故障即重派(pinescript 題實遇,重派即常)。
- 跨家族(agy 作者×Opus 審)Same-Weights 不咬,needs_diamond 偏少;殘留多為「查證邊界」
  (普世否定無法窮舉/單源數字)非權重盲點。

## 5. 消化段與 TTL 處置(product-ops 對接;runbook 行在 product-ops SKILL.md)

- verified proposal 的訊號 → PRODUCT.md **手術級 delta**(帶日期+指針錨,一句一錨,研究本體
  留 proposal 不重抄)→ 人核落檔。先例:2c8f3be(PromptBase 轉向+AIPRM 付費先例)、
  3a82cfe(楔子競爭錨+定價封頂錨)。
- 綁家族的 proposal 過 D3+人核後可即走 adopted:`git mv → families/<f>/proposals/`,root
  隔離區不留副本(首例=pinescript-quant,3a82cfe)。
- **負面情報=最高價值產出**:DR 迴圈的產品價值在「攔錯誤戰略結論」(pinescript 藍海證偽
  直壓 MVP 楔子定價),不在產出漂亮報告——admit 的意義是人收下真相,含難聽的。
