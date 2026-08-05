#!/usr/bin/env node
// S1.5 PROBE — 同一對話追問（file-based，AUP 隔離：正文只寫檔，stdout 只印 metadata）。
// 打字/送出邏輯逐字元複製自 ui.js runGeminiDeepResearchAttempt 的 input 插入 + send-button 段落（非重造 DR 引擎——
// 那條禁令針對 monitor+retry；這裡是純聊天追問，不啟用 Deep Research 工具）。
//
// 用法：node probe-gemini-conversation.mjs <convId> <promptFile> [--port 9333] [--out <path>]
//       node probe-gemini-conversation.mjs <convId> --extract-only [--port 9333] [--out <path>]
//       （--extract-only：不送新訊息，只重新抽取目前最後一個 turn——用於補救「抽早了、抽到串流中途」）

import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import TurndownService from 'turndown';
import { gfm } from 'turndown-plugin-gfm';

const turndownService = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced', bulletListMarker: '-', emDelimiter: '*', hr: '---' });
turndownService.use(gfm);
function htmlToMarkdown(html) {
  const md = turndownService.turndown(html);
  return md.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+\n/g, '\n').trim();
}

const argv = process.argv.slice(2);
const extractOnly = argv.includes('--extract-only');
const convId = argv[0];
const promptFile = extractOnly ? null : argv[1];
if (!convId || (!extractOnly && !promptFile)) {
  console.error('usage: node probe-gemini-conversation.mjs <convId> <promptFile> [--port 9333] [--out <path>] [--extract-only]');
  process.exit(2);
}
const port = argv.includes('--port') ? argv[argv.indexOf('--port') + 1] : '9333';
const outArg = argv.includes('--out') ? argv[argv.indexOf('--out') + 1] : null;
// 預設輸出必須落在**執行這支腳本的那個 repo**,不是寫死的某一棵樹。
// 2026-07-28 脫鉤前的實況:這裡寫死 /Users/neon/skill-bettor/,所以從 ts-skill-bettor 執行
// 會把產物寫進對側 repo(ARCHITECTURE §12 把這一類記為 rewrite-gap:改寫沒套到 .mjs)。
// 本檔位於 <repo>/.claude/skills/gemini-conversation-research/scripts/,故往上四層即 repo 根。
const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../../..');
const outPath = outArg || path.join(repoRoot, 'gemini_research/gcr', `${convId}-probe-${Date.now()}.md`);
const promptText = extractOnly ? null : fs.readFileSync(promptFile, 'utf8');

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
try {
  const pages = await browser.pages();
  const page = pages.find((p) => p.url().includes(convId));
  if (!page) { console.error(JSON.stringify({ error: 'target_tab_not_open', convId })); process.exit(1); }
  await page.bringToFront().catch(() => {});
  await delay(1000);

  const priorTurns = await page.evaluate(() => document.querySelectorAll('model-response').length);
  let newTurnAppeared = extractOnly; // extract-only：不送訊息，視為「已在目標 turn」

  if (!extractOnly) {
    await page.evaluate((text) => {
      const input = document.querySelector('input-area-v2 .ql-editor, .ql-editor, div[contenteditable="true"], textarea');
      if (!input) return;
      input.focus();
      if (input.tagName === 'DIV') {
        const range = document.createRange();
        const sel = window.getSelection();
        range.selectNodeContents(input);
        sel.removeAllRanges();
        sel.addRange(range);
      } else {
        input.value = '';
      }
      document.execCommand('insertText', false, text);
      // 注意：Gemini Web 頁面 CSP 啟用 Trusted Types，直接寫 innerHTML 會擲
      // TypeError（'requires TrustedHTML assignment'）——不用 innerHTML fallback，
      // execCommand('insertText') 已足夠讓 ql-editor 收到文字並觸發 quill 的 input 事件。
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }, promptText);
    await delay(1500);

    const sendClicked = await page.evaluate(() => {
      const sendBtn = document.querySelector('button[data-test-id="send-button"], button.send-button, button[aria-label="傳送訊息"], button[aria-label="Send message"]');
      if (sendBtn && !sendBtn.disabled) { sendBtn.click(); return true; }
      return false;
    });
    if (!sendClicked) { console.error(JSON.stringify({ error: 'send_button_not_found_or_disabled' })); process.exit(1); }
    await delay(3000);

    // 等回應完成：新 turn 出現 + 連續 4 次輪詢（間隔 3s，共 ≥9s 靜默）文字長度不變。
    // 不依賴「stop 按鈕消失」——實測該 selector 在此頁面持續命中某個常駐元素，非可靠訊號。
    const deadline = Date.now() + 150000;
    let stable = 0;
    let lastLen = -1;
    while (Date.now() < deadline) {
      const state = await page.evaluate(() => {
        const turns = document.querySelectorAll('model-response');
        const last = turns[turns.length - 1];
        return { turnCount: turns.length, lastLen: last ? last.innerText.length : 0 };
      });
      if (state.turnCount > priorTurns) newTurnAppeared = true;
      if (newTurnAppeared) {
        if (state.lastLen === lastLen && state.lastLen > 0) {
          stable += 1;
          if (stable >= 4) break;
        } else {
          stable = 0;
        }
        lastLen = state.lastLen;
      }
      await delay(3000);
    }
  } else {
    await delay(1000);
  }

  const html = await page.evaluate(() => {
    const turns = document.querySelectorAll('model-response');
    const last = turns[turns.length - 1];
    if (!last) return '';
    // 同一 turn 內可能有多個候選容器（如巢狀小 .markdown 片段）——取 innerHTML 最長者，
    // 同 extract-gemini-conversation.mjs 的 extractReportHtmlInBrowser 選最大候選策略。
    const cands = [...last.querySelectorAll('.markdown-main-panel, .markdown, message-content, .model-response-text')];
    const pool = cands.length ? cands : [last];
    const root = pool.sort((a, b) => b.innerHTML.length - a.innerHTML.length)[0];
    return root.innerHTML;
  });

  if (!html || html.length < 50) { console.error(JSON.stringify({ error: 'empty_response', htmlLen: (html || '').length, newTurnAppeared })); process.exit(1); }
  const md = htmlToMarkdown(html);
  const promptLabel = extractOnly ? '(extract-only, no new prompt)' : path.basename(promptFile);
  const header = `<!-- source: https://gemini.google.com/app/${convId} | probe prompt: ${promptLabel} | extracted: S1.5 gcr CDP:${port} -->\n\n`;
  const finalMd = header + md;
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, finalMd, 'utf8');

  console.log(JSON.stringify({
    ok: true, convId, outPath, response_chars: md.length, prior_turns: priorTurns, new_turn_appeared: newTurnAppeared, extract_only: extractOnly,
  }, null, 2));
} finally {
  await browser.disconnect();
}
