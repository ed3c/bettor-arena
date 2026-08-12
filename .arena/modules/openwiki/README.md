# `openwiki` module

Machine authority: [`module.json`](module.json)  
Interface version: `1.0.0`

## Role

Consumes typed wiki-update requests and regenerates the portable OpenWiki as-built projection without collapsing module and host roots.

## Public ports

| Loop | Class | Interface | External policy | Entry |
|---|---|---|---|---|
| `openwiki` | micro | `1.0.0` | control-only | `sh loopctl/loopctl.sh openwiki` |

## Capability boundary

**Provides**

- `wiki-update-request.consume/v1`
- `repo-wiki.projection/v1`

**Requires**

- `arena.loopctl/v1`
- `arena.proof-kernel/v1`
- `wiki-update-request.produce/v1`

## Owned implementation roots

- `kb-ingest/`
- `openwiki/`

## Runtime and Skills

- Runtime: `git`, `python3`, POSIX `sh`; network optional for explicit regeneration
- Skills: required `repo-wiki-converge`; repo-owned `openwiki-port`

## Evidence

- Verify: `python3 kb-ingest/check_repo_wiki_converge.py`
- Independent control: `sh proof_workflow/control_openwiki_entry.sh --json`
- Mutation / hollow evidence: `bash kb-ingest/port/test_relocation.sh`

## External boundary

Full mutation remains local/trusted-host only. Proof/test may be exposed only as explicitly allowlisted controls.

## Change discipline

`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Internal refactors do not require an interface bump unless input/output, named exits, effects, required flags or artifact contracts change.
