# MCP production migration

`migrate.py` is the shared migration mechanism for the three local repositories.
It does not own their MCP policy. Each repository owns its profile and host
configuration:

- `ts-skill-bettor`: `mcp/production/profile.json`
- `skill-bettor`: `mcp/production/profile.json`
- `ix-agy`: `.agents/mcp-production/profile.json`

Host permission profiles are intentionally not mirrored. In particular,
`ts-skill-bettor` validates the required MCP declarations inside
`.codex/config.toml`, but `apply` never replaces that file: its OrbStack socket,
loopback Forgejo allowlist, and sandbox policy are host/session configuration,
not portable MCP payload.

The engine uses Python's standard library only. It refuses path traversal,
symlink destinations, protected-branch mutation, dirty destination overwrite,
literal secrets, and resident payload claims for heavy executors. `apply`
supports only profile-declared mirrors and writes a recovery backup plus an
append-only receipt. `rollback` requires the exact apply receipt and refuses
targets changed after apply.

## Commands

Run the checked-in engine against any standard Git worktree:

```sh
python3 mcp/production/migrate.py \
  --repo-root /absolute/worktree \
  --profile path/inside/repo/profile.json \
  plan

python3 mcp/production/migrate.py \
  --repo-root /absolute/worktree \
  --profile path/inside/repo/profile.json \
  apply

python3 mcp/production/migrate.py \
  --repo-root /absolute/worktree \
  --profile path/inside/repo/profile.json \
  verify --receipt
```

`verify` records hashes rather than command output, so a receipt cannot become a
credential or prompt dump. Receipts are chained by the SHA-256 of the preceding
receipt; `check-receipts` validates the complete chain.

## Admission boundary

A technically passing probe is reported as
`technical_pass_human_pending` whenever the profile declares human gates. The
engine never clicks Claude/Codex project approval, opens a replacement chat, or
declares context-kernel LAND. Those actions remain human-owned.

Capability registration may be permanent while computation remains bounded:
control/tool surfaces can stay resident or session-scoped; GrepAI indexing,
Serena LSP payloads, OpenWiki reads, context construction, browsers, and devices
remain demand-pull or session-owned.
