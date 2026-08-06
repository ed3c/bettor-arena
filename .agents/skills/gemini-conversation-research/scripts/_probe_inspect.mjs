import puppeteer from 'puppeteer-core';
const convId = process.argv[2];
const b = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9333' });
try {
  const pages = await b.pages();
  const p = pages.find(pg => pg.url().includes(convId));
  if (!p) { console.log(JSON.stringify({ error: 'not_open', convId })); process.exit(1); }
  const m = await p.evaluate(() => {
    const q = (sel) => document.querySelectorAll(sel).length;
    return {
      url: location.href,
      title: document.title,
      counts: {
        'model-response': q('model-response'),
        'user-query': q('user-query'),
        'message-content': q('message-content'),
        '.model-response-text': q('.model-response-text'),
        '.markdown': q('.markdown'),
        'input-area-v2': q('input-area-v2'),
        '.ql-editor': q('.ql-editor'),
        'div[contenteditable="true"]': q('div[contenteditable="true"]'),
        'textarea': q('textarea'),
        'button[data-test-id="send-button"]': q('button[data-test-id="send-button"]'),
      },
      lastModelResponseInnerHTMLLen: (() => {
        const els = document.querySelectorAll('model-response');
        if (!els.length) return null;
        return els[els.length - 1].innerHTML.length;
      })(),
      qlEditorTextLen: (() => {
        const el = document.querySelector('.ql-editor');
        return el ? (el.innerText || '').length : null;
      })(),
      lastTurnCandidates: (() => {
        const els = document.querySelectorAll('model-response');
        if (!els.length) return null;
        const last = els[els.length - 1];
        const cands = [...last.querySelectorAll('.markdown-main-panel, .markdown, message-content, .model-response-text')];
        return cands.map((c, i) => ({ i, tag: c.tagName, cls: c.className, htmlLen: c.innerHTML.length, textLen: (c.innerText||'').length }));
      })(),
      lastTurnInnerTextLen: (() => {
        const els = document.querySelectorAll('model-response');
        if (!els.length) return null;
        return (els[els.length - 1].innerText || '').length;
      })(),
      composerButtons: (() => {
        const c = document.querySelector('input-area-v2');
        if (!c) return null;
        return [...c.querySelectorAll('button')].map(b => ({
          ariaLabel: b.getAttribute('aria-label') || '',
          testId: b.getAttribute('data-test-id') || '',
          cls: b.className,
          disabled: b.disabled,
        }));
      })(),
      lastTurnActionBar: (() => {
        const els = document.querySelectorAll('model-response');
        if (!els.length) return null;
        const last = els[els.length - 1];
        return {
          thumbUp: !!last.querySelector('[aria-label*="Good response"], [aria-label*="讚"], [data-test-id*="thumb"]'),
          copyBtn: !!last.querySelector('[aria-label*="Copy"], [aria-label*="複製"]'),
          responseFooter: !!last.querySelector('message-actions, response-footer, .response-footer, .actions-container-v2'),
          stopBtnGlobal: !!document.querySelector('button[aria-label*="Stop"], button[aria-label*="停止"]'),
        };
      })(),
    };
  });
  console.log(JSON.stringify(m, null, 2));
} finally { await b.disconnect(); }
