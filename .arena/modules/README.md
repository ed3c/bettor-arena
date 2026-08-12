# Module catalog

Every admitted module directory contains:

```text
.arena/modules/<module-id>/
├── module.json   # machine authority
└── README.md     # human navigation
```

The manifest owns interface and closure facts. The README explains intent, public ports, evidence and boundaries without creating a second API.

## Current modules

| Module | Class / responsibility |
|---|---|
| [`arena-core`](arena-core/) | Root SSOT, passive entrypoints, bootstrap and repository gates |
| [`module-catalog`](module-catalog/) | Manifests, ownership, composition resolution and locks |
| [`loop-runtime`](loop-runtime/) | `loopctl`, Context Capsules and stateless MCP runtime |
| [`proof-kernel`](proof-kernel/) | Module closure subjects, controls, mutation and release aggregation |
| [`project-bootstrapper`](project-bootstrapper/) | Transactional external-project plan/apply/verify/rollback |
| [`environment-contracts`](environment-contracts/) | GitHub/Forgejo logical release and Browser Contract v2 |
| [`agent-runtime-integration`](agent-runtime-integration/) | Skills/runtime-env bindings and host adapter verdicts |
| [`mcp-adapters`](mcp-adapters/) | Higher-level MCP adapters and production migration |
| [`perfect-seed-factory`](perfect-seed-factory/) | Typed seed-repository micro loop |
| [`openwiki`](openwiki/) | Portable OpenWiki update and projection |
| [`notebooklm`](notebooklm/) | Authenticated NotebookLM harvest loop |
| [`code-truth-graph`](code-truth-graph/) | Closed-packet code truth graph builder |
| [`technical-equivalence`](technical-equivalence/) | Technical claim-to-implementation equivalence loop |

Validation:

```sh
python3 scripts/gates/check_readme_coverage.py
python3 scripts/gates/check_module_catalog.py
```
