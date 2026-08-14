# harness-wiki local context

This file is the bounded context route for `.agents/skills/harness-wiki/`. It does not replace the repository root `CONTEXT.md`, `AGENTS.md`, `CLAUDE.md`, `ARCHITECTURE.md`, nearest `README.md`, module manifests, source, tests, or receipts.

## Mandatory read order

```text
repository README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ root CONTEXT.md
→ docs/agents/domain.md when present
→ .agents/skills/harness-wiki/SKILL.md
→ modules/prompt-registry.md
→ the one task-relevant module below
→ contracts / scripts / fixtures / exact receipt
```

Do not create a root `CONTEXT-MAP.md` merely to satisfy a template. Add one only after the repository has multiple durable bounded contexts with different vocabularies or owners. A missing route explicitly required by a task packet is `ABSENT`; chat history and Agent memory are not substitutes.

## Local vocabulary

| Term | Meaning | Authority |
|---|---|---|
| portable Skill | An Agent Skills package whose canonical body is `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and host sidecars | canonical Skill source and immutable binding |
| host projection | A path or sidecar that exposes a portable Skill to one Agent host without copying the canonical body | generated/bound adapter surface |
| execution request | A typed proposal to execute one executable with an argument vector in a bounded subject and sandbox | `contracts/skill-execution-request.schema.json` |
| assertion set | Machine-checkable expectations evaluated independently from the Agent that proposed or edited code | `contracts/skill-assertion-set.schema.json` |
| execution receipt | Subject-bound evidence of what actually ran, what the OS returned, which assertions passed, and what residue remains | `contracts/skill-execution-receipt.schema.json` |
| advisory assertion | A model or reviewer observation that may guide work but cannot advance a hard state transition | assertion severity `advisory` |
| hard assertion | A deterministic or independently observed condition required for `PASS` | assertion severity `hard` |
| provider candidate | Search, symbol, graph, or memory output that nominates evidence but is not repository truth until read back against current authority | `docs/knowledge-providers/` contracts |
| memory proposal | Evidence-bound add/supersede/delete request that cannot mutate canonical memory without Human Admit | `docs/knowledge-providers/contracts/memory-proposal.schema.json` |

## Task modules

- Host and file-format compatibility: [`modules/host-skill-compatibility.md`](modules/host-skill-compatibility.md)
- Executable Skill and assertion boundary: [`modules/executable-skill-contract.md`](modules/executable-skill-contract.md)
- Host-owned portable runner and named isolation limits: [`modules/portable-runner.md`](modules/portable-runner.md)
- Provider topology overview: [`modules/knowledge-provider-topology.md`](modules/knowledge-provider-topology.md)
- Executable provider contracts and registry: [`../../../docs/knowledge-providers/README.md`](../../../docs/knowledge-providers/README.md)

## Non-negotiable authority order

```text
current source / manifest / test / runtime receipt / current ADR
    > generated context, semantic search, symbol service, graph, memory, model prose
```

`SKILL.md` teaches a procedure. It does not make a command safe, a provider healthy, an assertion true, or a task complete. Only the host-owned execution and assertion path can produce a hard-gate receipt. Human Admit remains required where repository policy says so.
