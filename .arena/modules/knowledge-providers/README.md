# `knowledge-providers` module

Owner: subject-bound read-only knowledge-provider contracts, deterministic provider-versus-control admission evaluations, and memory proposal governance.

The module owns `docs/knowledge-providers/` and the provider validation/evaluation scripts. Repository-level fixtures under `tests/` remain owned by `proof-kernel`; referencing them does not transfer ownership.

It does not own provider installation, MCP credentials, index daemons, source truth, LoopX transitions, gate waivers, Human Admit, or production promotion.

```text
exact request subject
→ read-only provider/control observation
→ source-readback and coverage gates
→ deterministic precision/recall/resource report
→ candidate recommendation
→ Human Admit
```

Verification:

```bash
python3 scripts/check_knowledge_provider_module.py
python3 scripts/check_knowledge_provider_module.py --selftest
sh tests/knowledge-provider-evals/run-all.sh
```

Checked-in observations are fixtures. They test evaluator behavior only; they do not prove a live provider or elect a winner.
