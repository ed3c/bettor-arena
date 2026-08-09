import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import puppeteer from 'puppeteer-core';

import { CHROME_PORT } from './state.js';
import { runGeminiDeepResearch } from './ui.js';

// stdout is a machine protocol. Provider logs are returned inside each response
// so Python can retain them in the per-invocation receipt without corrupting the
// JSONL channel.
const protocol = process.stdout;
let stdoutLines = [];
let stderrLines = [];

function rendered(args) {
  return args.map((value) => {
    if (typeof value === 'string') return value;
    try { return JSON.stringify(value); } catch { return String(value); }
  }).join(' ');
}

console.log = (...args) => stdoutLines.push(rendered(args));
console.error = (...args) => stderrLines.push(rendered(args));

function tail(lines) {
  return lines.join('\n').slice(-8000);
}

function respond(payload) {
  protocol.write(`${JSON.stringify(payload)}\n`);
}

async function main() {
  if (!process.argv.includes('--stdio-jsonl')) {
    throw new Error('usage: node gemini_session.mjs --stdio-jsonl');
  }
  const browser = await puppeteer.connect({
    browserURL: `http://127.0.0.1:${CHROME_PORT}`,
    defaultViewport: null,
    protocolTimeout: 600000,
  });
  const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

  for await (const line of input) {
    stdoutLines = [];
    stderrLines = [];
    let request;
    let page;
    try {
      request = JSON.parse(line);
      if (!request.label || !request.prompt_path || !request.output_path) {
        throw new Error('label, prompt_path and output_path are required');
      }
      const articleText = fs.readFileSync(request.prompt_path, 'utf8');
      const slug = path.basename(request.output_path).replace(/\.[^.]*$/, '');
      console.log(`[DR-session] ${request.prompt_path} (${articleText.length} chars) → ${request.output_path}`);
      page = await browser.newPage();
      const fakeVideo = {
        title: slug,
        url: `https://www.youtube.com/watch?v=DRSESSION${Date.now()}`,
      };
      const { reportMd } = await runGeminiDeepResearch(page, articleText, fakeVideo, {});
      fs.writeFileSync(request.output_path, reportMd || '', 'utf8');
      console.log(`[DR-session] saved ${(reportMd || '').length} chars → ${request.output_path}`);
      await page.close();
      page = undefined;
      respond({
        label: request.label,
        raw_exit: 0,
        stdout_tail: tail(stdoutLines),
        stderr_tail: tail(stderrLines),
      });
    } catch (error) {
      if (page) {
        try { await page.close(); } catch (closeError) {
          stderrLines.push(`page close failed: ${closeError?.message || closeError}`);
        }
      }
      stderrLines.push(error?.stack || error?.message || String(error));
      respond({
        label: request?.label || null,
        raw_exit: 1,
        stdout_tail: tail(stdoutLines),
        stderr_tail: tail(stderrLines),
      });
    }
  }
  await browser.disconnect();
}

main().catch((error) => {
  process.stderr.write(`[DR-session] fatal: ${error?.stack || error}\n`);
  process.exitCode = 1;
});
