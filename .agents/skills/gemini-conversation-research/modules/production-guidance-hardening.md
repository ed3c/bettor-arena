# Module: Production Guidance Hardening

> 屬 [`gemini-conversation-research`](../SKILL.md)。當 GCR 對話要進入 skill-bettor 小迴圈、計畫包、或 `repo/agent-skills-repo` production seed 時，讀本模組。目的不是多寫一段 prompt，而是把對話引導、agy Gemini 3.6 Flash High 執行經驗、末端 repo 產物與小迴圈資料流綁成可驗證的物理契約。

## Required Production Path

```text
P0 Source Artifact
  -> P1 Guided Conversation Seed Template
  -> P2 Agy Context Replay Request
  -> P3 Plan-Package Input Packet
  -> P4 Prototype Small-Loop Mirror
  -> P5 Final Repo Runtime Surface
  -> P6 Terminal Neural Sensing
  -> P7 Promotion / Human Admit
```

The path is invalid if it collapses match/generate/verify into one prompt or if it produces only prose without runnable gates.

P1 的 runnable gate 不是瀏覽器 profile owner，而是 file-only
`scripts/run_guided_conversation.py` 與其 Bun technical equivalent。它必須直接接
`gcr-guidance-projection@0.2.0` candidate hashes、輸出三個 prompt slots、保留 queued branches，
並以最多三輪收斂；未知 branch 不得自動 click。任何只有 golden trace/validator、沒有 runner
decision/result artifact 的 seed 都仍是 `P1.seed_trace_missing`。

## Agy Gemini 3.6 Flash High Role

Use agy as an independent Gemini-context replay actor, not as the only judge and not as a hidden oracle.

Required recorded fields:

```yaml
agy_replay:
  model_display_name: "Gemini 3.6 Flash"
  thinking_mode: "High"
  execution_role: "independent-context-replay"
  prompt_source: "fixed_prompt + iteration_auto_prompt + emergent_prompt"
  stdout_policy: "stdout may be summary only; parse file artifacts when present"
  evidence_status: "candidate_until_artifact_compared"
```

If agy output only summarizes, parse its artifact file path before judging quality. If no artifact path exists, mark `human_required` or `candidate`; do not silently promote.

## Terminal Neural Sensing

Every GCR-to-production run must sense the terminal repo shape, not only the conversation trace:

```yaml
terminal_neural_sensing:
  prototype_small_loop:
    required_paths:
      - "prototype/<plan>/<repo>/small-loop/inputs/plan-package-inputs.yaml"
      - "prototype/<plan>/<repo>/small-loop/packets/inbox/"
      - "prototype/<plan>/<repo>/small-loop/baselines/project-seed-stats.json"
  final_repo:
    required_paths:
      - "repo/<repo>/README.md"
      - "repo/<repo>/PROJECT-SSOT.md"
      - "repo/<repo>/plan-package.compat.yaml"
      - "repo/<repo>/openwiki/"
      - "repo/<repo>/scripts/"
      - "repo/<repo>/tests/"
    forbidden_paths:
      - "repo/<repo>/small-loop/"
      - "repo/<repo>/packets/"
      - "repo/<repo>/templates/skill-defense-governance/"
  proof_commands:
    - "scripts/test_plan_package_runner.sh"
    - "repo/<repo>/scripts/check_plan_package_compat.py"
    - "repo/<repo>/scripts/check_openwiki.py"
    - "repo/<repo>/scripts/check_wiki_graph_sync.py"
    - "python3 -m pytest repo/<repo> -q"
```

## Production Missing-Dimension Ledger

These are the parts agents tend to miss:

| dimension | failure mode | required hardening |
|---|---|---|
| live extraction evidence | URL-only seed gets treated as verified conversation | raw artifact hash + extracted turn count + source-ingest packet |
| model provenance | "agy" is named but not replayed or versioned | model display name, thinking mode, output artifact policy |
| branch abandonment | contextual buttons are observed but not exhausted or deferred | branch queue with explicit deferred reason |
| terminal usability | final repo has files but no usage entry or test runner | README/OpenWiki entry + executable validator |
| repo/small-loop boundary | final repo accidentally contains control-plane packets/templates | forbidden path gate |
| code/data lineage | copied code blocks lose source relation | code fence preservation + raw/traditional artifact hashes |
| semantic compression | requirement summary replaces original terms | `simplified_information`, `lost_information`, `missing_domain_terms` ledger |
| failure history | only passing traces are kept | failure trace sample or explicit no-failure-yet marker |
| rollback | promotion has no rollback handle | dataset version + molecular commit + plan-package input id |
| privacy/license | conversation or wiki data is embedded before classification | trace privacy + code/model/data license fields |

## Promotion Rule

Promote a GCR-guided production artifact only when:

1. The seed conversation template emits a golden case and physical trace.
   The trace must come from the guided runner's completed file result; a hand-authored trace alone is insufficient execution evidence.
2. A plan-package source-ingest packet records input/output artifacts, hash, prompt contexts, and route.
3. Prototype mirrors the small-loop input and packet.
4. Final repo exposes runtime usage, OpenWiki, scripts, tests, and compat manifest, but no small-loop control plane.
5. Terminal validators pass and are listed in the route result or plan-package materialization packet.
6. Any agy Gemini 3.6 Flash High evidence is `candidate` until compared with concrete terminal artifacts.
