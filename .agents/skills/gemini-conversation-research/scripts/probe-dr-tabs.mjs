import puppeteer from 'puppeteer-core';
const ids = ['6bc41b9ab8e94b7b','badf3207c3d54a13','debe2d8dab78509d','e5e663924486f1f4'];
const b = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9333' });
const delay = ms => new Promise(r=>setTimeout(r,ms));
try {
  const pages = await b.pages();
  const out = [];
  for (const id of ids) {
    const p = pages.find(pg => pg.url().includes(id));
    if (!p) { out.push({ id, open:false }); continue; }
    const m = await p.evaluate(() => {
      const panel = document.querySelector('deep-research-immersive-panel');
      const bodyTxt = document.body.innerText || '';
      const h1 = document.querySelector('deep-research-immersive-panel h1, .markdown-main-panel h1');
      return {
        title: (h1 && h1.innerText || '').slice(0,80),
        hasPanel: !!panel,
        hasSourceLists: !!document.querySelector('deep-research-source-lists'),
        nblmPy: /notebooklm[-_]py|teng-lin\/notebooklm/i.test(bodyTxt),
        nblm: /notebooklm/i.test(bodyTxt),
        dataAgentKit: /data agent kit/i.test(bodyTxt),
        bodyLen: bodyTxt.length,
      };
    }).catch(e => ({ err: e.message.split('\n')[0] }));
    out.push({ id, open:true, ...m });
  }
  // sidebar order (recency): try reading conversations-list anchors on first available page
  let sidebar = null;
  const anyPage = pages.find(pg => pg.url().includes('gemini.google.com/app'));
  if (anyPage) {
    sidebar = await anyPage.evaluate(() => {
      const anchors = [...document.querySelectorAll('a[href*="/app/"]')];
      return anchors.map(a => (a.getAttribute('href')||'').split('/app/')[1]).filter(Boolean).slice(0,15);
    }).catch(() => null);
  }
  console.log(JSON.stringify({ tabs: out, sidebar_order_top15: sidebar }, null, 2));
} finally { await b.disconnect(); }
