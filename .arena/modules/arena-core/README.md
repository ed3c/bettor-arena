# `arena-core` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.2.0`

## Role

Owns repository engineering SSOT, governed Agent entrypoints, bootstrap/hooks, root documentation routes and deterministic repository gates. The LoopX PDF audit is a machine-checked requirement/State-Machine/data-flow contract; it does not provide a live LoopX runtime.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `macro` | macro | `2.8.0` | denied | `sh loopctl/loopctl.sh macro` |

## Capability boundary

**Provides**

- `arena.passive-context/v1`
- `arena.host-gates/v1`
- `arena.pdf-loopx-traceability/v1`

**Requires**

- `arena.module-catalog/v1`

## Owned implementation roots

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CONTEXT.md`
- `ARCHITECTURE.md`
- `bootstrap.sh`
- `.githooks/`
- `.github/`
- `scripts/gates/`
- `docs/architecture/`

## LoopX PDF contract

```text
docs/architecture/PDF_LOOPX_HARNESS_TRACEABILITY.md
docs/architecture/pdf-loopx-harness.integration.json
docs/architecture/pdf-loopx-harness.integration.schema.json
scripts/gates/check_pdf_loopx_harness_integration.py
```

The contract maps all 15 PDF requirement groups to current modules, State Machines, paths, gates and blockers. It preserves `PARTIAL`, `NOT_IMPLEMENTED` and `NOT_EXERCISED` instead of turning documentation agreement into runtime PASS.

## Runtime and Skills

- Runtime: `git`, POSIX `sh`, `python3`
- Skills: none
- External policy: no network, secrets or model mutation

## Evidence

```sh
python3 scripts/gates/check_arena_core.py
python3 scripts/gates/check_arena_core.py --selftest
python3 scripts/gates/check_pdf_loopx_harness_integration.py
python3 scripts/gates/check_pdf_loopx_harness_integration.py --selftest
```

- Verify: aggregate Agent-entrypoint + LoopX audit gate
- Independent control: `sh proof_workflow/control_macro_entry.sh --json`
- Mutation/hollow: Agent-doc selftest plus 13 LoopX contract mutations

## External boundary

Macro governance and PDF admission are trusted-host operations. They are never exposed as generic MCP tools. PDF prose, fixture PASS, provider presence and UI/checkpoint state cannot create release authority.

## Change discipline

`module.json` is machine authority. This README is navigation. Bump the interface when an externally consumed capability or named contract changes; regenerate composition/context/proof projections after any manifest or context delta.
