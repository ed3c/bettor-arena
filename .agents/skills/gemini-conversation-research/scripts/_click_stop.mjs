import puppeteer from 'puppeteer-core';
const convId = process.argv[2];
const b = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9333' });
try {
  const pages = await b.pages();
  const p = pages.find(pg => pg.url().includes(convId));
  const clicked = await p.evaluate(() => {
    const btn = [...document.querySelectorAll('button')].find(b => (b.getAttribute('aria-label') || '').includes('停止回覆'));
    if (btn) { btn.click(); return true; }
    return false;
  });
  console.log(JSON.stringify({ clicked }));
} finally { await b.disconnect(); }
