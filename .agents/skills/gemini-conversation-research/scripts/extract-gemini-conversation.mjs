#!/usr/bin/env node
// ⚠ 名稱易混淆（cc-20260712）：本檔只抓「單一最大內容面板」（一次拿一份已完成的
// DR 報告），**不做多輪 turn 結構抽取**。gemini-conversation-research 的 S0 real
// entrypoint 是 repo 根目錄 /Users/neon/antigravity/scripts/extract-gemini-conversation.mjs
// （turn-structured 多輪 QA + 可選附加 DR report 面板，同一份輸出）。相對路徑
// `scripts/extract-gemini-conversation.mjs` 在本 skill 目錄脈絡下會誤解析到「這一份」
// 而非根目錄那份——SKILL.md / conversation-pipeline.md 已改用絕對路徑消歧。
// 本檔保留給「只要單獨抓一份已完成 DR 報告、不需要對話 turn 結構」的場景。
//
// S0 EXTRACT — Gemini/AI Studio 對話（含 Deep Research 報告）抽取 → 保真 Markdown 寫檔。
//
// SSOT 鐵錨：抽取邏輯 = data.js 的 htmlToMarkdown(17) + extractReportHtmlInBrowser(24)
// （cc-20260712 核實：非 automate.js——automate.js 現僅 290 行純調度層，這兩個函式
// 實際定義在 data.js，由 automate.js import 調度）。
// 這兩個是純函式，本檔逐字元複製（非重造 DR 引擎 — 那條禁令針對 monitor+retry；抽取已完成報告是純操作）。
// 漂移時以 data.js 為權威（改抽取 selector 去改 data.js，回頭同步這裡）。
//
// AUP 隔離（P0）：stdout 只印 metadata JSON，正文只寫檔，永不進主 context。
//
// 用法：node extract-gemini-conversation.mjs <convId> [--port 9333] [--out <path>]
//   CDP fallback：連使用者既有已登入 :9333 Chrome，目標對話已開分頁 → 零導航直讀。

import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import TurndownService from 'turndown';
import { gfm } from 'turndown-plugin-gfm';

// ── 逐字元複製自 automate.js:12-34（htmlToMarkdown 及其 turndown 規則）──
const turndownService = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced', bulletListMarker: '-', emDelimiter: '*', hr: '---' });
turndownService.use(gfm);
turndownService.addRule('cellBr', { filter: (n) => n.nodeName === 'BR' && !!n.closest && !!n.closest('td,th'), replacement: () => '<br>' });
turndownService.addRule('mathTex', {
  filter: (n) => !!(n.getAttribute && n.getAttribute('data-math')),
  replacement: (content, n) => {
    const tex = (n.getAttribute('data-math') || '').trim();
    if (!tex) return content;
    return n.nodeName === 'DIV' ? ('\n\n$$' + tex + '$$\n\n') : (' $' + tex + '$ ');
  },
});
function htmlToMarkdown(html) {
  let md = turndownService.turndown(html);
  md = md.replace(/\\\[cite:([\d,]+)\\\]/g, '[cite:$1]').replace(/\\\[(\d+)\\\]/g, '[cite:$1]');
  md = md.replace(/(?:\[cite:[\d,]+\]\s*){2,}/g, (m) => '[cite:' + [...new Set(m.match(/\d+/g))].join(',') + ']');
  return md.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+\n/g, '\n').trim();
}

// ── 逐字元複製自 automate.js:43-97（extractReportHtmlInBrowser，在瀏覽器 context 執行）──
function extractReportHtmlInBrowser() {
  const cands = [...document.querySelectorAll('deep-research-immersive-panel .markdown-main-panel, .markdown-main-panel, deep-research-immersive-panel .markdown, message-content, .model-response-text, .markdown')];
  const sig = cands.filter(p => p.querySelector('table') || p.querySelector('h1') || p.querySelector('h2'));
  const pool = sig.length ? sig : cands;
  const root = pool.sort((a, b) => b.innerHTML.length - a.innerHTML.length)[0];
  if (!root) return '';
  const node = root.cloneNode(true);
  const cw = document.createTreeWalker(node, NodeFilter.SHOW_COMMENT, null);
  const cs = []; let c; while (c = cw.nextNode()) cs.push(c); cs.forEach(n => n.remove());
  node.querySelectorAll('sup[data-turn-source-index]').forEach(s => {
    const n = s.getAttribute('data-turn-source-index');
    const host = s.closest('source-footnote') || s;
    host.replaceWith(document.createTextNode('[cite:' + n + ']'));
  });
  node.querySelectorAll('sources-carousel, sources-carousel-inline').forEach(e => e.remove());
  node.querySelectorAll('.katex').forEach(k => {
    if (k.closest('[data-math]')) return;
    const t = (k.textContent || '').replace(/\s+/g, '').trim();
    k.replaceWith(document.createTextNode(t ? (' $' + t + '$ ') : ''));
  });
  node.querySelectorAll('response-element, source-footnote').forEach(e => {
    const f = document.createDocumentFragment(); while (e.firstChild) f.appendChild(e.firstChild); e.replaceWith(f);
  });
  node.querySelectorAll('th p, td p').forEach(p => {
    const f = document.createDocumentFragment(); while (p.firstChild) f.appendChild(p.firstChild); p.replaceWith(f);
  });
  node.querySelectorAll('*').forEach(e => { [...e.attributes].forEach(a => { if (a.name !== 'href' && a.name !== 'data-math') e.removeAttribute(a.name); }); });
  let html = node.innerHTML;
  const seen = new Set(); const li = [];
  const dsl = document.querySelector('deep-research-source-lists');
  let usedList = null;
  if (dsl) {
    for (const list of dsl.querySelectorAll('div.source-list')) {
      let hdr = '', p = list.previousElementSibling;
      for (let i = 0; i < 3 && p; i++) { const tx = (p.innerText || '').replace(/\s+/g, ' ').trim(); if (tx) { hdr = tx; break; } p = p.previousElementSibling; }
      if (/生成報告/.test(hdr) && !/未用|查閱/.test(hdr)) { usedList = list; break; }
    }
  }
  (usedList ? [...usedList.querySelectorAll('a[href]')] : []).forEach(a => {
    const u = a.href;
    if (!/^https?:/.test(u) || /gemini\.google|accounts\.google/.test(u) || seen.has(u)) return;
    seen.add(u);
    let t = (a.innerText || '').replace(/\s+/g, ' ').replace(/在新視窗中開啟|Opens in a new window/g, '').trim();
    let host = ''; try { host = new URL(u).hostname.replace(/^www\./, ''); } catch (e) {}
    if (host && t.toLowerCase().startsWith(host.toLowerCase())) t = t.slice(host.length).trim();
    li.push('<li><a href="' + u + '">' + (t || host || u).replace(/</g, '&lt;') + '</a> — ' + host + '</li>');
  });
  if (li.length) html += '<h2>來源 (Sources)</h2><p><em>行內 <code>[cite:N]</code> 對應下列第 N 筆（<code>data-turn-source-index</code> = used 清單 1-based 位置;一個引用點可含複數來源如 <code>[cite:23,27]</code>）。</em></p><ol>' + li.join('') + '</ol>';
  return html;
}

// ── 抽取驅動（CDP fallback）──
const argv = process.argv.slice(2);
const convId = argv[0];
if (!convId) { console.error('usage: node extract-gemini-conversation.mjs <convId> [--port 9333] [--out <path>]'); process.exit(2); }
const port = argv.includes('--port') ? argv[argv.indexOf('--port') + 1] : '9333';
const outArg = argv.includes('--out') ? argv[argv.indexOf('--out') + 1] : null;
// 預設輸出必須落在**執行這支腳本的那個 repo**,不是寫死的某一棵樹。
// 2026-07-28 脫鉤前的實況:這裡寫死 /Users/neon/skill-bettor/,所以從 ts-skill-bettor 執行
// 會把產物寫進對側 repo(ARCHITECTURE §12 把這一類記為 rewrite-gap:改寫沒套到 .mjs)。
// 本檔位於 <repo>/.claude/skills/gemini-conversation-research/scripts/,故往上四層即 repo 根。
const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../../..');
const outPath = outArg || path.join(repoRoot, 'gemini_research/gcr', `${convId}-conversation.md`);

const delay = (ms) => new Promise(r => setTimeout(r, ms));

const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });
try {
  const pages = await browser.pages();
  let page = pages.find(p => p.url().includes(convId));
  if (!page) { console.error(JSON.stringify({ error: 'target_tab_not_open', convId })); process.exit(1); }
  await page.bringToFront().catch(() => {});
  // 等 SPA 渲染 + 連續滾動載入全對話（Gemini Web）
  await delay(1500);
  for (let i = 0; i < 12; i++) {
    await page.evaluate(() => { const el = document.scrollingElement || document.body; window.scrollBy(0, -el.scrollHeight); }).catch(() => {});
    await delay(400);
  }
  await page.evaluate(() => { const el = document.scrollingElement || document.body; window.scrollTo(0, el.scrollHeight); }).catch(() => {});
  await delay(800);

  // metadata probe（不把 body 帶回）
  const probe = await page.evaluate(() => ({
    hasPanel: !!document.querySelector('deep-research-immersive-panel'),
    hasSourceLists: !!document.querySelector('deep-research-source-lists'),
    title: document.title,
  }));

  const reportHtml = await page.evaluate(extractReportHtmlInBrowser);
  if (!reportHtml || reportHtml.length < 200) { console.error(JSON.stringify({ error: 'empty_extraction', probe, htmlLen: (reportHtml || '').length })); process.exit(1); }
  let md = htmlToMarkdown(reportHtml);

  const header = `<!-- source: https://gemini.google.com/app/${convId} | extracted: S0 gcr CDP:${port} -->\n\n`;
  md = header + md;
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, md, 'utf8');

  const citeCount = (md.match(/\[cite:[\d,]+\]/g) || []).length;
  const sourceCount = (md.match(/^\d+\.\s+\[.*?\]\(https?:/gm) || []).length || (md.split('來源 (Sources)')[1] || '').split('\n').filter(l => /\]\(https?:/.test(l)).length;
  console.log(JSON.stringify({
    ok: true, convId, outPath,
    content_chars: md.length, content_lines: md.split('\n').length,
    cite_markers: citeCount, source_refs: sourceCount,
    hasPanel: probe.hasPanel, hasSourceLists: probe.hasSourceLists, page_title: probe.title,
  }, null, 2));
} finally {
  await browser.disconnect();
}
