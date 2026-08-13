# Knowledge-provider admission evaluations

This directory turns the provider-neutral contracts into a reproducible
provider-versus-control comparison lane. It does not launch Serena, GrepAI,
Code-Graph-RAG, Mem0, an LLM, or an MCP server. It evaluates normalized
observations against immutable repository subjects, current provider
manifests, independent controls, and explicit hard gates.

## Authority boundary

```text
provider or deterministic control
→ normalized observation
→ exact subject / query / participant / manifest checks
→ source-readback, coverage, budget, cleanup, and authority gates
→ paired metrics
→ candidate recommendation
→ Human Admit
```

A green checked-in fixture proves only that the evaluator recognizes a valid
packet and rejects planted defects. It does not prove that a provider is
installed, healthy, fresh, complete, better than its control, or suitable for
production.

## Directory contract

```text
evals/
├── README.md
├── STATUS.md
├── config.json
├── subject.json
├── contracts/
│   ├── participant.schema.json
│   ├── eval-case.schema.json
│   ├── eval-observation.schema.json
│   ├── eval-report.schema.json
│   ├── eval-config.schema.json
│   └── subject.schema.json
├── participants/
│   ├── exact-search-control.json
│   ├── repository-authority-control.json
│   ├── serena.json
│   ├── grepai.json
│   ├── code-graph-rag.json
│   └── mem0.json
├── cases/
│   ├── symbol-public-skill-port.json
│   ├── semantic.json
│   ├── graph.json
│   └── memory.json
└── fixtures/
    ├── good/observations.json.gz
    └── hollow/observations.json.gz
```

The gzip files contain complete JSON arrays. Compression is a storage detail,
not semantic compression. The evaluator reads them transparently.

## Case families

| Family | Provider candidate | Independent control | Decision use |
|---|---|---|---|
| symbol | Serena | exact repository read | Symbol lookup/reference precision and source readback |
| semantic | GrepAI | exact repository search | Intent-only location with bounded candidate volume |
| graph | Code-Graph-RAG | manifest/import/source traversal | Cross-module impact without converting coverage gaps into absence |
| memory | Mem0 | current repository authority | Historical hint recall while preserving conflict and current-authority priority |

Every case has exactly one provider and one control. The default contract
requires all eight case/participant pairs. Omitting a failed participant is a
hard failure rather than a smaller successful experiment.

## Hard gates

The evaluator fails closed on:

- subject, tree, query, participant, or provider-manifest drift;
- duplicate or missing case/participant pairs;
- mixed fixture and live evidence in one report;
- `PASS` without physical execution;
- stale or mismatched index subjects;
- `FOUND` without current-source readback;
- `NO_FLOW` where coverage must remain `UNKNOWN`;
- authority escalation, repository writes, memory writes, gate waiver,
  `TESTED`, promotion, or Human Admit by a provider;
- result, context, latency, or tool-call budget overflow;
- cleanup failure or residue;
- memory conflict erasure or stale memory overriding current authority;
- absolute paths, traversal paths, unexpected fields, or malformed ranks.

## Metrics

The deterministic report contains:

- verified precision and recall;
- false-positive count;
- preservation of `UNKNOWN`;
- latency, context bytes, tool calls, and result count;
- complete paired-coverage status;
- fixture versus subject-bound evidence scope;
- candidate recommendation and explicit Human Admit requirement.

Recommendations use:

```text
PRIMARY_CANDIDATE
SECONDARY_CANDIDATE
EXPERIMENTAL
CONTROL_BASELINE
REJECTED
NOT_EXERCISED
FIXTURE_ONLY
```

No recommendation performs admission. `FIXTURE_ONLY` never elects a winner.

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
0   valid suite and all required hard gates pass
2   checked subject or evidence disagrees with the contract
64  invalid invocation, unreadable input, or missing runtime dependency
```

## Fixture-only lock

The checked-in `config.json` has `fixture_only: true`. Non-fixture
observations are rejected until a separate Human-admitted change pins the
provider adapter, index/storage identity, privacy/retention policy, runtime
profile, and live canary receipt. This prevents a synthetic fixture from
being relabeled as production evidence.

## Current live state

```text
Serena live observation          NOT_EXERCISED
GrepAI live observation          NOT_EXERCISED
Code-Graph-RAG adapter/index     NOT_CONFIGURED
Mem0 adapter/storage/writeback   NOT_CONFIGURED
cross-provider winner            NOT_EXERCISED
automatic admission              FORBIDDEN
```
