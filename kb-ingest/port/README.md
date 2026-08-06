# `kb-ingest/port/` — everything skill-bettor added

The boundary this directory exists to make physical:

| Directory | Rule |
|---|---|
| `kb-ingest/openwiki/` | **upstream bytes only.** Seven machine-generated assets, each wrapped in `OPENWIKI-OFFICIAL:BEGIN/END`. Nothing is hand-written here, and nothing skill-bettor invented lives here. |
| `kb-ingest/port/` | **everything else.** Generators, host adapters, reimplementations of upstream's code-owned behavior, and local appendices. |
| `kb-ingest/` (module root) | the module's own entry points and its installation declaration: `check_repo_wiki_converge.py`, `host-profile.json`, the setup scripts, and the two ledgers. Nothing upstream-derived. |

Verify the first row at any time:

```sh
python3 kb-ingest/port/sync_prompts.py <openwiki_repo> --check
```

A non-zero exit means either the assets drifted from upstream or someone hand-edited one.

## Contents, and who reads each file

### `test_relocation.sh` — proof that the module is portable, and that its gate still bites

Builds a throwaway host, copies the module in under a different name at a different depth,
and runs the core gate there. Then breaks it once per failure mode and requires the specific
exit code back (1 for a broken claim, 3 for "cannot tell").

- **Needs**: `python3` and `git`. No model call — the boundary proof runs under `OPENWIKI_DRY_RUN`.
- **Read by**: SKILL.md step S0, whenever the gate changed or the module moved.
- **Why it exists**: the gate passing where it already lives proves little; every host
  assumption is satisfied by accident there. And a positive control cannot tell "the checks
  passed" from "the checks resolved nothing and returned success" — which is precisely how a
  relocation refactor fails. It is **not** wired into the gate: the gate would then call the
  script that calls the gate.

### `sync_prompts.py` — generator

Extracts the official prompts verbatim from an `openwiki` checkout into `../openwiki/`.

- **Reads**: `src/agent/prompts/code.ts`, `src/agent/skeleton_critic.ts`,
  `src/agent/wiki_qa_subagents.ts` in the upstream repo.
- **Writes**: the seven assets in `kb-ingest/openwiki/`. Nothing else.
- **Referenced by**: `repo-wiki-converge` SKILL.md step S0 (preflight `--check`),
  `modules/official-port-map.md` §5 (upstream upgrade procedure),
  `check_repo_wiki_converge.py` (runs its `--selftest`).
- **Why it exists**: the port's central claim is "the prompt text is byte-identical to upstream".
  Hand-copied markdown makes that claim unfalsifiable after the first typo; a generator makes
  `git diff` the proof and an upstream upgrade one command.

### `openwiki_post.py` — the code-owned passes, reimplemented

Upstream's `src/agent/okf-middleware.ts` wraps every run with deterministic passes. The official
prompts reference their effects as accomplished facts. Without them, prompt lines like *"Directory
index.md files are generated deterministically after the run"* are dead letters.

- **Subcommands**: `migrate` (upstream `beforeAgent`), `finalize` (upstream `afterAgent`: mermaid →
  index → links → `.last-update.json`).
- **Reads/writes**: the target repository's `openwiki/` directory only.
- **Referenced by**: SKILL.md steps S2 and S4, `modules/official-port-map.md` §1,
  `ARCHITECTURE.md` §2, `check_repo_wiki_converge.py` (runs its `--selftest`).
- **Deliberate divergences from upstream** are listed in its module docstring; the load-bearing one is
  a wider `PRESERVED_EXTENSION_FIELDS`, so a front-matter rebuild cannot silently drop the RepoDoc
  routing fields and break KB ingest.
- **`--protect <rel-path>`** has no upstream equivalent. It exists because a real target can hold a
  page some *other* tool generates and then asserts byte-equality over; repairing such a page's front
  matter turns a completely separate gate red while the page still looks fine.

### `openwiki_subagent.sh` — the three official review subagents, host-native

Runs `skeleton_critic`, `wiki_question_finder` and `wiki_answer_verifier` as isolated child processes
on Claude Code or Codex CLI. No API key: inference is the host CLI's own subscription session.

- **Reads**: `../openwiki/subagents/*.md` (official system prompts, extracted between the
  `## systemPrompt` heading and the `OPENWIKI-OFFICIAL:END` marker).
- **Writes**: `<TARGET>/.openwiki-review/<role>-latest.txt` and a `<role>-trace.log`. Deliberately
  **outside** `openwiki/`, because anything inside the wiki tree becomes a section directory to the
  index generator.
- **Referenced by**: SKILL.md invariant 2 and steps S3b/S3d/S3e, `ARCHITECTURE.md` §2,
  `check_repo_wiki_converge.py` (runs its boundary proof).
- **Why it is stronger than upstream**: upstream's deepagents subagents share one virtual filesystem,
  so each read boundary can only be asserted in prose. Here the boundary is the directory the child
  can see — throwaway `git worktree` for the critic and finder (with `openwiki/` removed for the
  finder), a wiki-only scratch copy for the verifier.

### `wiki_update_worker.sh` — digestion station for factory wiki-update requests

Consumes the typed request the factory delivery terminus
(`loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh`) drops into `data/wiki-update/` after a
successful delivery, and walks the official update pipeline: parse → preflight →
[LLM regeneration: TODO, a real run is FATAL 64 until wired] → review gates
(`openwiki_subagent.sh`, `OPENWIKI_DRY_RUN` in dry-run; critic is recorded `skipped-no-skeleton`
when the update flow has no `_skeleton.md`) → `openwiki_post.py` migrate/finalize on a scratch copy
(the live wiki is byte-compared and any mutation fails loud) → a receipt back-linking the
`request_id` into `data/wiki-update/`.

- **Needs**: `python3`, `git`, and a host CLI for the gate runner. `--selftest` proves the
  deterministic face with fixture requests (absent file = 64, broken/foreign/hollow = 2, good
  dry-run = 0 with a back-linked receipt).
- **Read by**: whoever lands a factory delivery and wants the wiki caught up; the trigger only
  writes the request — it starts no worker, same record-only boundary as the post-commit hook.
- **Emergent separation**: emergent observations (new page needs, drift) never enter the request
  or any standards module; they land in the openwiki-native backlog
  (`openwiki/quickstart.md` `## Backlog`, normalized by `openwiki_post.py --normalize-backlog`),
  which the request's `emergent_prompt_context` merely points at.

### `host-runtime.md` — appendix

Maps upstream's virtual filesystem onto a real host: what `/` means, which code-owned passes a script
must now perform, how the subagents are invoked, and what is **not** ported (translation,
`.openwikiignore`, connectors, LangSmith, visualizer, telemetry, personal mode).

- **Read by**: the doc agent, alongside the official system prompt, at SKILL.md step S3.
- **Referenced by**: SKILL.md SSOT list and step S3.

### `repodoc-extension.md` — appendix

The producer-extension front-matter fields skill-bettor's `indexing/repodoc.py` requires
(`node_kind`, `repo`, `commit`, `covers`, `libraries`, …), and why they are OKF-legal rather than a
fork.

- **Read by**: the doc agent at SKILL.md step S3.
- **Referenced by**: SKILL.md SSOT list, `openwiki_post.py` module docstring.

## Routing rule

Adding behavior to this port means adding a file **here**, never editing one in `../openwiki/`. If a
change seems to require editing an official asset, the correct move is one of:

1. extend `sync_prompts.py` (for example a new upstream placeholder), then regenerate; or
2. write a new appendix here and reference it from the SKILL's step S3; or
3. upgrade the upstream checkout and regenerate.
