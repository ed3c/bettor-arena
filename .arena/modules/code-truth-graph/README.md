# `code-truth-graph` module

Machine authority: [`module.json`](module.json)
Interface version: `1.0.0`

## Role

Builds a content-addressed code truth graph from a closed typed source bundle and returns typed graph/result artifacts.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `ctg` | micro | `1.0.0` | allowlisted | `sh loopctl/loopctl.sh ctg` |

## Capability boundary

**Provides**

- `code-truth-graph.build/v1`

**Requires**

- `arena.loopctl/v1`
- `arena.proof-kernel/v1`

## Owned implementation roots

- `loop_wiki/code-truth-graph/`

## Runtime and Skills

- Runtime: `git`, `python3`, POSIX `sh`; local runtime profile
- Skills: required `repo-fullstack-debugger`

## Evidence

- Verify: `sh loop_wiki/code-truth-graph/verify.sh`
- Independent control: `sh proof_workflow/control_ctg_entry.sh --json`
- Mutation / hollow evidence: `sh loop_wiki/code-truth-graph/selftest.sh`

## External boundary

MCP-exposed only through a closed inline/content-addressed carrier in a disposable worktree; no host paths, network or secrets.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
