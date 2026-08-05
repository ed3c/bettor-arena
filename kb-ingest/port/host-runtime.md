# Appendix — host runtime mapping (skill-bettor addition, NOT upstream text)

Upstream OpenWiki runs its prompts inside a Deep Agents runtime with a virtual
filesystem and a middleware layer. This port runs the same prompts inside a
Claude Code or Codex CLI session with no Node, no API key, and no middleware.
This file is the adapter. It is deliberately kept out of the
`OPENWIKI-OFFICIAL` markers so the prompt assets stay byte-comparable to
upstream.

## Path mapping

| Prompt says | Means here |
|---|---|
| `/` (filesystem root) | `<TARGET>` — the repository being documented |
| `/openwiki/quickstart.md` | `<TARGET>/openwiki/quickstart.md` |
| `/openwiki/_skeleton.md`, `/openwiki/_plan.md` | same, under `<TARGET>/openwiki/` |
| "Shell execute commands run on the host" | true as written; run from `<TARGET>` |

The prompts forbid passing host absolute paths such as `/Users/...` to
filesystem tools. That rule exists because upstream's virtual root would turn
them into nested garbage paths. Here they resolve normally, so the rule is
downgraded to a convention: work `<TARGET>`-relative, and never write outside
`<TARGET>/openwiki/`.

## What the CLI did that a script must now do

`src/agent/okf-middleware.ts` wraps every run with deterministic passes. The
prompts reference their effects as facts. Skip them and those lines are lies.

| Upstream | Here |
|---|---|
| `beforeAgent: migrateWikiToOkf` | `python3 kb-ingest/port/openwiki_post.py migrate <TARGET>/openwiki` |
| `afterAgent: validateWikiMermaid` | `openwiki_post.py finalize` step 1 |
| `afterAgent: synchronizeWikiIndexes` | `finalize` step 2 |
| `afterAgent: validateWikiInternalLinks` | `finalize` step 3 |
| `wrapToolCall` front-matter warning | **absent** — see gap below |
| `.last-update.json` write | `finalize` |
| `AGENTS.md` / `CLAUDE.md` `OPENWIKI:START…END` block | **not ported** — this port never edits the target's agent files |

**Gap, stated plainly.** Upstream validates front matter on *every* write and
feeds the failure straight back into the tool result, so the agent self-corrects
mid-run. There is no host hook to attach that to here, so front-matter repair
happens only in the batch passes. Net effect: a page can carry bad front matter
until `finalize` rewrites it, and the rewrite stamps `openwiki_generated: true`
rather than producing the accurate `type`/`title`/`description` the agent would
have written. Treat any `openwiki_generated: true` left in the wiki as an
unfinished page and fix it in the next update run — the prompts already instruct
exactly that.

## Subagents

The three official review subagents are invoked as isolated child processes:

```sh
bash kb-ingest/port/openwiki_subagent.sh critic   <TARGET>          payload.txt
bash kb-ingest/port/openwiki_subagent.sh finder   <TARGET>          payload.txt
bash kb-ingest/port/openwiki_subagent.sh verifier <TARGET>          payload.txt
```

Their read boundaries are enforced by which directory the child can see, not by
prose. See the header of `openwiki_subagent.sh`.

Divergence: `codex exec` has no system-prompt flag, so on the Codex host the
official system prompt is prepended to the turn instead of occupying the system
role. On Claude Code it goes to `--system-prompt`.

## Not ported

`--language` translation, `.openwikiignore`, connectors, LangSmith, the
visualizer, telemetry, and personal mode. The prompt assets are generated with
placeholders resolved for *no language and no `.openwikiignore`*; if either is
ever needed, extend `sync_prompts.py` rather than hand-editing an asset.
