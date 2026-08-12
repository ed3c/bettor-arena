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

const TRANSIENT_PAGE_ERRORS = [
  "detached Frame",
  "detached frame",
  "Execution context was destroyed",
  "Cannot find context",
  "Target closed",
  "Session closed",
  "Protocol error",
];

const SYNC_PAGE_METHODS = new Set([
  "isClosed",
  "listenerCount",
  "off",
  "on",
  "once",
  "removeListener",
  "url",
]);

function transientPageError(error) {
  const message = error?.message || String(error);
  return TRANSIENT_PAGE_ERRORS.some((marker) => message.includes(marker));
}

function resumableGeminiUrl(value) {
  try {
    const url = new URL(value);
    return (
      url.origin === "https://gemini.google.com" &&
      /^\/app\/[^/?#]+/.test(url.pathname)
    );
  } catch {
    return false;
  }
}

async function createRecoverablePage(browser) {
  let current = await browser.newPage();
  const state = { recoveries: 0, resumeUrl: null };

  const rememberUrl = () => {
    let value;
    try {
      value = current.url();
    } catch {
      return;
    }
    if (resumableGeminiUrl(value)) state.resumeUrl = value;
  };

  const recover = async (method, error) => {
    if (state.recoveries >= 1) {
      throw new Error(
        `Gemini page recovery exhausted during ${method}: ${error?.message || error}`,
      );
    }
    rememberUrl();
    if (!state.resumeUrl) {
      throw new Error(
        `Gemini page closed during ${method} before a resumable conversation URL was observed`,
      );
    }
    const previous = current;
    const replacement = await browser.newPage();
    try {
      await replacement.goto(state.resumeUrl, {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
    } catch (resumeError) {
      try {
        await replacement.close();
      } catch {}
      throw new Error(
        `Gemini page resume navigation failed during ${method}: ${resumeError?.message || resumeError}`,
      );
    }
    current = replacement;
    state.recoveries += 1;
    console.log(
      `[DR-session] resumed closed Gemini page at the digest-bound conversation URL (${state.recoveries}/1)`,
    );
    try {
      if (!previous.isClosed()) await previous.close();
    } catch {}
  };

  const invoke = async (owner, method, args) => {
    rememberUrl();
    if (current.isClosed())
      await recover(`${owner}.${String(method)}`, new Error("Target closed"));
    const target = owner === "page" ? current : current[owner];
    try {
      const result = await target[method](...args);
      rememberUrl();
      return result;
    } catch (error) {
      if (!transientPageError(error)) throw error;
      await recover(`${owner}.${String(method)}`, error);
      const replacement = owner === "page" ? current : current[owner];
      const result = await replacement[method](...args);
      rememberUrl();
      return result;
    }
  };

  const keyboard = new Proxy(
    {},
    {
      get(_target, property) {
        const value = current.keyboard[property];
        return typeof value === "function"
          ? (...args) => invoke("keyboard", property, args)
          : value;
      },
    },
  );

  const page = new Proxy(
    {},
    {
      get(_target, property) {
        if (property === "keyboard") return keyboard;
        const value = current[property];
        if (typeof value !== "function") return value;
        if (SYNC_PAGE_METHODS.has(property)) {
          return (...args) => {
            const result = current[property](...args);
            if (property === "url") rememberUrl();
            return result;
          };
        }
        if (property === "close") return (...args) => current.close(...args);
        return (...args) => invoke("page", property, args);
      },
    },
  );
  return { page, state };
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
    let pageState = { recoveries: 0 };
    try {
      request = JSON.parse(line);
      if (!request.label || !request.prompt_path || !request.output_path) {
        throw new Error('label, prompt_path and output_path are required');
      }
      const articleText = fs.readFileSync(request.prompt_path, 'utf8');
      const slug = path.basename(request.output_path).replace(/\.[^.]*$/, '');
      console.log(`[DR-session] ${request.prompt_path} (${articleText.length} chars) → ${request.output_path}`);
      ({ page, state: pageState } = await createRecoverablePage(browser));
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
        page_recoveries: pageState.recoveries,
        stdout_tail: tail(stdoutLines),
        stderr_tail: tail(stderrLines),
      });
    } catch (error) {
      if (page) {
        try {
          await page.close();
        } catch (closeError) {
          stderrLines.push(`page close failed: ${closeError?.message || closeError}`);
        }
      }
      stderrLines.push(error?.stack || error?.message || String(error));
      respond({
        label: request?.label || null,
        raw_exit: 1,
        page_recoveries: pageState.recoveries,
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
