# Files

- [bootstrap.sh — per-clone activation and doctor](bootstrap.md) - The idempotent activation script that registers versioned git hooks, runs a FATAL-64 tool doctor, probes the optional MCP toolchain as WARNs, and prints the human-owned MCP approval steps.
- [Claude host config — settings.json and rm_guard](claude-host.md) - The versioned Claude Code host layer — the PreToolUse hook registration and the fail-closed rm_guard.py deletion boundary with its parser design and two-direction selftest.
- [Git hook chain — pre-commit, commit-msg, post-commit](git-hooks.md) - The three armed hooks under .githooks/ — staged-only fast-quality preflight with self-integrity and a budget watchdog, the molecular commit-msg gate, and the record-only post-commit receipt writer.
- [MCP surface — declarations, context-pack server, production engine](mcp-surface.md) - The three portable MCP server declarations for both hosts, the read-only repo-context-pack AST server, and the profile-driven mcp/production migration engine with chained receipts and human gates.
- [Molecular commit-message contract](molecular-messages.md) - The rebuilt validate_molecular_message.ts gate — its legislated charter, required trailer fields, protected-surface trigger, ISSUE-n Intent-Slice vocabulary, and the corpus-parity measurement of what the rebuild deliberately dropped.
