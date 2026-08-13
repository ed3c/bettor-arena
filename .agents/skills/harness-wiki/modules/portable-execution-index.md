# Portable execution index

Read these modules in this order only when the task crosses host, execution, assertion, or provider boundaries:

1. [`host-skill-compatibility.md`](host-skill-compatibility.md)
2. [`executable-skill-contract.md`](executable-skill-contract.md)
3. [`knowledge-provider-topology.md`](knowledge-provider-topology.md)

Machine contracts:

- [`../contracts/skill-execution-request.schema.json`](../contracts/skill-execution-request.schema.json)
- [`../contracts/skill-assertion-set.schema.json`](../contracts/skill-assertion-set.schema.json)
- [`../contracts/skill-execution-receipt.schema.json`](../contracts/skill-execution-receipt.schema.json)

Deterministic contract gate:

```bash
sh .agents/skills/harness-wiki/tests/run-all.sh
```

This gate validates contract shape and planted negative controls. Live host, provider, model, sandbox and cloud execution remain separate receipts.
