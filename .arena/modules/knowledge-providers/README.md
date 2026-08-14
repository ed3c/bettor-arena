# `knowledge-providers` module

Owner: subject-bound read-only knowledge-provider contracts and memory proposal
governance.

The module owns:

- `docs/knowledge-providers/`
- `scripts/check_knowledge_providers.py`
- `tests/knowledge-providers/`
- `tests/test_knowledge_providers.py`

It provides capability contracts only. It does not own provider installation,
MCP credentials, index daemons, source truth, LoopX state transitions, gate
waivers, Human Admit, or production promotion.

Public capabilities:

```text
knowledge-provider.query/v1
knowledge-provider.memory-proposal/v1
```

Verification:

```bash
python3 scripts/check_knowledge_providers.py
python3 scripts/check_knowledge_providers.py --selftest
sh tests/knowledge-providers/run-all.sh
```
