# Browser Contract v2

[`contract.json`](contract.json) separates browser **actor**, **surface**, **transport**, **session**, **workflow**, **route** and **evidence**.

The contract exists to prevent statements such as “the browser passed” from collapsing distinct facts:

- the actor may be Claude Code, Codex CLI, agy or a human operator;
- the transport may be Playwright, CDP, a broker or another adapter;
- a signed-in local session is host-owned and must never be copied into a bundle or cloud runtime;
- raw research, verification and authenticated workflow routes have different evidence grades.

Verify with:

```sh
bun scripts/gates/check_environment_contracts.ts
bun scripts/arena_browser.ts status
```

The checked-in status is [`../../data/browser/status.json`](../../data/browser/status.json). A deterministic contract PASS does not imply a live signed-in provider canary ran.
