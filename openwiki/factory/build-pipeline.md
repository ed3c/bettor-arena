---
type: Architecture
title: Factory build pipeline — trigger, build, three validators
description: How trigger.sh orchestrates packet validation, exchange-context generation, the run.sh build dispatch, and the three post-build validators into a route-result JSON with per-stage exit codes and a mandatory human gate.
tags: [factory, pipeline, validators]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [trigger-pipeline, route-result, reduced-ir, materialization]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Factory build pipeline — trigger, build, three validators

The physical entry is `sh trigger.sh <packet> <absolute-output>` (src: loop_wiki/evolve-perfect-seed-repo-factory/AGENTS.md:43-44). Everything below is mechanical script; the only LLM-facing artifact is the exchange-context file it writes for the packet.

```mermaid
flowchart TD
    P[packet JSON] --> V1[cli.ts validate\npacket contract]
    P --> RS[cli.ts refs-status\ndeclared / sentinel / resolved / stale]
    O[absolute output path] --> V2[cli.ts validate-output\nabsolute, safe chars, not existing]
    V1 --> CTX[write per-packet exchange-context.md\nunder _engine-run/]
    RS --> CTX
    CTX --> B[run.sh → cli.ts build\nreduce → materialize]
    B -->|build_exit=0| FQ[run_generated_fast_quality.ts\nexit 2 fail / 64 fatal]
    FQ -->|fast_quality_exit=0| OP[generated scripts/plan.ts\n20-call operator run]
    OP -->|operator_exit=0| VG[verify_generated_repo.ts\nfull product contract]
    B & FQ & OP & VG --> RR[per-packet route-result.json in packets/outbox/\nnext_edge = human_required_before_seed_admit]
```

## trigger.sh — orchestration and evidence

Steps (src: loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh:1-87):

1. `cli.ts validate` and `cli.ts validate-output` — [packet contract](packet-contract.md) plus output-path safety (absolute, no NUL/CR/LF/quote/backslash, must not already exist; src: loop_wiki/evolve-perfect-seed-repo-factory/src/cli.ts:20-24).
2. `cli.ts refs-status` — the refs-status JSON is relayed verbatim; an unrecognized status FAILs (src: trigger.sh:19-25).
3. Writes `_engine-run/exchange-context.<packet_id>.md` recording packet path, fixed/iteration/emergent prompt-context ownership, source_refs, refs_status, human gate, target output (src: trigger.sh:26-39) — the prompt/context ownership model of ROUTES.md (src: loop_wiki/evolve-perfect-seed-repo-factory/ROUTES.md:34-41).
4. Runs `run.sh` with stdout/stderr captured to `_engine-run/build.<packet_id>.{out,err}` (src: trigger.sh:41-44).
5. **Three post-build validators, short-circuited** — a nonzero earlier stage leaves later stages unexecuted (recorded as their initialized exit 1; src: trigger.sh:45-65, ROUTES.md:49-51):
   - `run_generated_fast_quality.ts --repo <out>`: symlinks the factory's `node_modules` into the generated repo (refusing if one already exists), runs `bun run quality:fast` inside it, exit 2 on failure and 64 on precondition (src: loop_wiki/evolve-perfect-seed-repo-factory/src/run_generated_fast_quality.ts:14-30).
   - the generated repo's OWN operator: `bun run <out>/scripts/plan.ts --task "Validate the generated seed and surface the next bounded action"` — a real 20-call execution, not a file-presence check (src: trigger.sh:55; PROMPT.md guard metric: "File presence alone is insufficient; generated code and hollow controls run", src: loop_wiki/evolve-perfect-seed-repo-factory/PROMPT.md:31-34).
   - `verify_generated_repo.ts --repo <out>`: the full product contract — see [generated-repo](generated-repo.md).
6. Writes `packets/outbox/route-result.<packet_id>.json` (`perfect-seed-route-result@1.0.0`) with `build_exit`, `fast_quality_exit`, `operator_exit`, `validator_exit`, source_refs, refs_status, output, and always `next_edge: human_required_before_seed_admit` — "it never writes an admitted seed decision" (src: trigger.sh:66-81; ROUTES.md:43-47). Any nonzero stage makes trigger itself FAIL exit 2 with the per-stage summary line (src: trigger.sh:82-85).

The fast-quality result here is "local preflight evidence, not an asynchronous Code Quality or Production Use axis receipt" (src: ROUTES.md:51-52) — the same claim boundary as [the repo gate](../gates/fast-quality.md).

## run.sh and cli.ts build

`run.sh` is a one-shot dispatch: resolve packet path, `exec bun run src/cli.ts build --packet … --output … </dev/null` (src: loop_wiki/evolve-perfect-seed-repo-factory/run.sh:1-13). `build` re-validates everything, hashes the packet bytes once, derives the refs status, reduces, materializes, and prints `{"status":"candidate-human-admit-required", …receipt}` (src: loop_wiki/evolve-perfect-seed-repo-factory/src/cli.ts:104-117). Errors from any command print `FAIL: <message>` and exit 1 — except the typed `ReceiptCheckError` (unreadable resolve receipt), which exits 2: the check ran and failed on unreadable evidence (src: cli.ts:119-124; commit 2c36ddf).

## reduce.ts — the reduced IR

`reducePacket` turns the bounded source into the IR records documented in `modules/architecture.md` (source / evidence / claims / unknowns / decisions; src: loop_wiki/evolve-perfect-seed-repo-factory/modules/architecture.md:5-15). Bounds are hard constants: `MAX_SOURCE_BYTES = 512 KiB`, `MAX_REPO_FILES = 200`, `MAX_REPO_FILE_BYTES = 128 KiB`, ignored dirs `.git/node_modules/dist/coverage/__pycache__`; repo walks skip symlinks and sort entries for determinism (src: loop_wiki/evolve-perfect-seed-repo-factory/src/reduce.ts:5-40). Every evidence record carries a stable id, source_ref, sha256, excerpt (src: reduce.ts:10-15); large files keep a hash with an explicit `N/A-binary-or-large` excerpt reason (src: modules/architecture.md:25). `repo` sources are walked file-by-file into per-file evidence records; text sources (`dr`/`gcr`/`grill-me`) are read whole under `MAX_SOURCE_BYTES`; either way, a source that yields nothing fails loud — "source produced zero evidence records" (src: reduce.ts:92) — which is the G1 "nonzero evidence" validator of [the workflow](overview.md).

## materialize.ts — template → product

`materializeRepo` pins `TEMPLATE_VERSION = "perfect-seed-repo@1.1.0"`, refuses an existing output, copies `templates/repo/` (excluding its `node_modules`) with `errorOnExist`, then writes the IR data files into `data/` (src: loop_wiki/evolve-perfect-seed-repo-factory/src/materialize.ts:6-51). It closes with the provenance triple: `lineage.json` (`perfect-seed-lineage@1.0.0`, carrying packet/template/task hashes, source_refs, refs_status, and the terminal human gate), the file-hash `artifact-manifest.json` (which excludes itself and the build receipt from its own entries), and `build-receipt.json` (`perfect-seed-build-receipt@1.0.0`) binding `artifact_manifest_sha256` and `terminal_state: "candidate-human-admit-required"` (src: materialize.ts:53-87).

## Focused tests

Each pipeline behavior is pinned by name in `tests/seed_factory.test.ts` (src: loop_wiki/evolve-perfect-seed-repo-factory/tests/seed_factory.test.ts): "materializes a runnable repo from ${kind}" across all four source kinds (:89); "rejects an unknown source kind" (:129); "does not overwrite an existing output" (:137); "rejects an unsafe output path before materialization" (:147); "rejects an artifact manifest path that escapes the generated repo" (:155); "build carries source_refs through the reduced IR into the lineage manifest" (:369); "generated fast gate never removes a pre-existing local dependency symlink" (:573). The boundary rule: "The factory template is the code SSOT. Generated repos are versioned products. Runtime call plan/results may change per task; source evidence and lineage must not be rewritten to make a result look better" (src: modules/architecture.md:19-22).
