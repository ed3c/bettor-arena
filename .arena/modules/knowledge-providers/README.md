# `knowledge-providers` module

Owner: subject-bound read-only knowledge-provider contracts, deterministic
provider-versus-control admission evaluations, and proposal-only memory
governance.

The module owns:

- `docs/knowledge-providers/`;
- `scripts/check_knowledge_providers.py`;
- `scripts/check_knowledge_provider_module.py`;
- `scripts/evaluate_knowledge_providers.py`;
- `scripts/knowledge_provider_eval_*.py`.

Repository-level test wrappers under `tests/` remain owned by `proof-kernel`.
Referencing those controls does not transfer ownership.

It does not own provider installation, MCP credentials, index daemons,
persistent stores, source truth, LoopX transitions, gate waivers, Human
Admit, or production promotion.

```text
exact immutable subject
→ paired provider/control observation
→ identity, freshness, readback, budget, cleanup, and authority gates
→ deterministic report
→ candidate recommendation
→ Human Admit
```

Public capabilities:

```text
knowledge-provider.query/v1
knowledge-provider.memory-proposal/v1
knowledge-provider.eval/v1
```

Verification:

```bash
python3 scripts/check_knowledge_provider_module.py
python3 scripts/check_knowledge_provider_module.py --selftest
sh tests/knowledge-provider-evals/run-all.sh
```

Checked-in observations remain fixture-only. They test the evaluator and its
negative controls; they do not prove live provider execution or elect a
winner.
