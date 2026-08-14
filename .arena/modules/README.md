# Module catalog

Each child directory is one independently owned module. `module.json` is the machine authority; the sibling `README.md` explains responsibility, state machine, inputs, outputs and verification. Root projections and receipts must be generated from these contracts, not maintained as second source lists.

## Current modules and State Machine roles

| Module | State-machine responsibility | Public capability / output |
|---|---|---|
| [`agent-runtime-integration`](agent-runtime-integration/) | Skill/runtime binding → host projection → typed execution → assertion receipt | `agent-runtime.aggregate/v1`, `skill-execution.runner/v1` |
| [`arena-core`](arena-core/) | repository entry → placement/bootstrap → host gates | `arena.host-gates/v1`, `arena.passive-context/v1` |
| [`code-truth-graph`](code-truth-graph/) | closed source packet → parse/build → graph/result artifacts | `code-truth-graph.build/v1` |
| [`environment-contracts`](environment-contracts/) | runtime/origin/browser declaration → probe → status/equivalence receipt | browser and logical-release contracts |
| [`knowledge-providers`](knowledge-providers/) | provider manifest → bounded query/memory proposal → readback → candidate | provider query and proposal-only memory contracts |
| [`loop-runtime`](loop-runtime/) | CLI parse/validate → public dispatch → Context Capsule/MCP result | `arena.loopctl/v1`, context carrier, stateless MCP |
| [`loopx-kernel`](loopx-kernel/) | Objective/Todos/Gates/Evidence/Quota contract → typed state boundary | `loopx.contracts/v1`; terminal leaf, not composition-selected |
| [`loopx-worker-gateway`](loopx-worker-gateway/) | six-host request/event/receipt protocol → bounded Worker observation | `loopx.worker-gateway/v1`; terminal leaf, not composition-selected |
| [`mcp-adapters`](mcp-adapters/) | typed high-level adapter → policy check → public capability | `arena.mcp-adapters/v1` |
| [`module-catalog`](module-catalog/) | module proposal → ownership/composition resolve → deterministic lock | `arena.module-catalog/v1` |
| [`notebooklm`](notebooklm/) | target/auth/resolve → bounded harvest/follow → scratch cleanup → receipt | `notebooklm.harvest/v1` |
| [`openwiki`](openwiki/) | wiki request → dry/full opt-in → verify → tracked projection/receipt | OpenWiki projection and update consumer |
| [`perfect-seed-factory`](perfect-seed-factory/) | typed packet → build/quality/operator/validator → Human edge | seed build and wiki-update producer |
| [`project-bootstrapper`](project-bootstrapper/) | preset → plan/resolve/render/verify/apply/rollback | `arena.project-bootstrap/v1` |
| [`proof-kernel`](proof-kernel/) | closure subject → proof/control/mutation → release aggregate | `arena.proof-kernel/v1` |
| [`technical-equivalence`](technical-equivalence/) | source claim → implementation equivalent → control/judge/Human decision | `technical-equivalence.evaluate/v1` |

## Composition state machine

```text
module manifest + README
→ one tracked-path owner
→ selected composition component
→ dependency / conflict / capability resolution
→ composition lock
→ Context Capsule lock
→ module proof subject
→ proof + control + mutation
→ release receipt
→ Human Admit
```

The selected module IDs must agree across:

```text
.arena/compositions/bettor-arena.requirements.json
.arena/locks/bettor-arena.lock.json
data/module-proof/release-receipt.json
```

A missing module in a generated lock or release receipt is RED even when the module's focused tests pass.

## PDF architecture mapping

The existing module set covers much of the supporting Harness foundation:

```text
composition / public ports / hard evidence / Skill execution
OpenWiki / Code Truth / provider-neutral contracts / runtime projection
```

It does not yet include modules for:

```text
LoopX Objective/Todos/Gates/Evidence/Quota state kernel
single-writer event ledger and reducer
LangGraph strategy/HITL
evidence-bound decision memory
six-host worker gateway live matrix
cloud/local execution fabric
Langfuse/OTel projection
Harness Web console
```

Current mapping:
[`../../docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md`](../../docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md).

## Adding or changing a module

1. Create or update `<id>/module.json`.
2. Create or update `<id>/README.md`.
3. Name owner, state machine, inputs, outputs, public capability, proof and Human boundary.
4. Add the desired component to the composition requirements.
5. Regenerate lock, contexts, subjects and release receipt.
6. Run the module's verify, control and mutation/hollow commands.
7. Update [`../../docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md`](../../docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md) and [`../../docs/traceability/STACK_PR_INDEX.md`](../../docs/traceability/STACK_PR_INDEX.md) when ownership or delivery topology changes.

## Verification

```sh
python3 scripts/gates/check_module_catalog.py
python3 scripts/arena_proof.py check
python3 scripts/arena_context.py check
python3 scripts/gates/check_pdf_harness_integration.py
```

No module may claim live provider, host, cloud, browser or Human state from its manifest alone.
