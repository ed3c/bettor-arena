# Knowledge-provider admission evaluations

This directory turns the provider-neutral contracts into a reproducible comparison lane. It does not launch Serena, GrepAI, Code-Graph-RAG, Mem0, an LLM, or an MCP server. It evaluates normalized observations against immutable repository subjects, current provider manifests, independent controls, and explicit hard gates.

## Authority boundary

```text
provider or deterministic control
→ normalized observation
→ exact subject / query / provider identity checks
→ source-readback and coverage checks
→ precision / recall / cost metrics
→ candidate recommendation
→ Human Admit
```

A green fixture proves the evaluator can recognize a valid packet. It does not prove that a provider is installed, healthy, fresh, complete, better than its control, or suitable for production.

## Files

```text
evals/
├── README.md
├── participants.json
├── contracts/
│   ├── participants.schema.json
│   ├── eval-case.schema.json
│   ├── eval-observation.schema.json
│   └── eval-report.schema.json
├── cases/
│   ├── symbol-public-skill-port.json
│   ├── semantic-provider-registry.json
│   ├── graph-provider-impact.json
│   └── memory-authority-conflict.json
└── fixtures/
    ├── good/observations.json
    └── hollow/observations.json
```

## Case families

| Family | Provider candidate | Independent control | Decision use |
|---|---|---|---|
| symbol | Serena | exact repository read | Symbol lookup/reference precision and source readback |
| semantic | GrepAI | exact repository search | Intent-only location with bounded candidate volume |
| graph | Code-Graph-RAG | manifest/import/source traversal | Cross-module impact without converting coverage gaps into absence |
| memory | Mem0 | current repository authority | Historical hint recall while preserving conflict and current-authority priority |

The controls are participants, not hidden oracles. Provider observations and control observations use the same subject, query digest, budgets, cleanup requirements, and output vocabulary.

## Metrics

The deterministic evaluator reports:

- verified precision and verified recall;
- false-positive count;
- preservation of `UNKNOWN` where coverage is incomplete;
- latency, context bytes, tool calls, and result count;
- subject, query, participant, manifest, and index identity;
- source-readback coverage;
- cleanup and residue;
- memory conflict preservation and current-authority outcome.

`FOUND` is allowed only with `SOURCE_READBACK_CONFIRMED` when the case requires source readback. A graph or semantic candidate is not confirmed merely because the provider returned it. `NO_FLOW` is forbidden for an oracle item whose declared coverage remains unknown.

## Recommendations are not admission

The report may emit:

```text
PRIMARY_CANDIDATE
SECONDARY_CANDIDATE
EXPERIMENTAL
REJECTED
NOT_EXERCISED
FIXTURE_ONLY
```

No recommendation performs admission. `FIXTURE_ONLY` can never elect a winner. A non-fixture candidate still requires Human Admit, exact runtime identity, immutable index subject, privacy and retention review, and current canary artifacts.

## Commands

```bash
python3 scripts/evaluate_knowledge_providers.py
python3 scripts/evaluate_knowledge_providers.py --selftest
python3 scripts/evaluate_knowledge_providers.py \
  --observations <subject-bound-observations.json> \
  --output <report.json>

python3 scripts/check_knowledge_provider_module.py
python3 scripts/check_knowledge_provider_module.py --selftest
sh tests/knowledge-provider-evals/run-all.sh
```

Exit semantics:

```text
0   valid suite and required hard gates pass
2   parsed subject disagrees with the contract or a hard gate fails
64  invalid invocation or unreadable input
```

## Live rollout

The checked-in cases bind the exact Bettor subject on which the evaluation contract was authored. Their checked-in observations are marked `fixture: true`; they exercise evaluator behavior only.

A live run must:

1. create an exact case or intentionally reuse an exact immutable case subject;
2. pin provider adapter and index identity;
3. run the provider and its independent control in isolated, bounded workspaces;
4. normalize each result into `knowledge-provider-eval-observation/v1`;
5. preserve `NOT_EXERCISED`, `ABSENT`, `SKIPPED_BY_POLICY`, and `FAIL`;
6. run this evaluator;
7. compare paired metrics without hiding hard-gate failures;
8. submit the report and raw receipt digests for Human Admit.

Current repository state remains:

```text
Serena live observation          NOT_EXERCISED
GrepAI live observation          NOT_EXERCISED
Code-Graph-RAG adapter/index     NOT_CONFIGURED
Mem0 adapter/storage/writeback   NOT_CONFIGURED
cross-provider winner            NOT_EXERCISED
```
