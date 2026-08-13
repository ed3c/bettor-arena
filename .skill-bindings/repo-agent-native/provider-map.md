# Provider map

The binding chooses capabilities first and products second. Products are replaceable implementations with explicit evidence ceilings.

## Current map

| Capability | Provider | Configuration | Strength | Boundary |
|---|---|---|---|---|
| exact text/source | `git`, `rg`, direct read | built in | deterministic current-byte baseline | does not infer semantic or runtime behavior automatically |
| semantic candidates | GrepAI | declared in Claude/Codex project MCP | local meaning-based search and call candidates | host executable is not pinned; empty result is not absence |
| bounded Python context | repo-context-pack | repo-owned frozen `uv` project | source-bound, deterministic package for Python analysis | partial language/domain coverage |
| symbol/reference/diagnostics | Serena | exact Git commit in both MCP surfaces | language-aware symbols and diagnostics | candidate/edit plan until source/workspace readback; live backend unexercised |
| cross-language graph impact | Code-Graph-RAG candidate | not configured | Tree-sitter/Memgraph graph, semantic/structural/data-flow tools | current MCP also exposes write/delete/wipe/index operations and external stores; requires a read-only admission wrapper |
| user/project/session memory | Mem0 candidate | not configured | scoped long-term memory and cross-session retrieval | requires retention, provenance, redaction, conflict, expiry, and writeback policy; memory never overrides repository authority |

## Why the four products are not one “brain”

They answer different questions:

```text
GrepAI              where might relevant code be?
Serena              what symbol/reference/diagnostic structure does the language workspace expose?
Code graph          what multi-file or cross-language edges are candidate impacts?
Memory              what prior preference, decision, incident, or hypothesis may guide search?
```

All four feed candidates or hints into the same source-verification procedure. None is allowed to declare a repository invariant on its own.

## Provider selection rules

1. Use exact source discovery first or as the universal fallback.
2. Use GrepAI when identifiers are unknown and meaning-based retrieval reduces search cost.
3. Use Serena when symbol completeness, references, diagnostics, or bounded symbol edits matter.
4. Admit a graph provider only with exact parser/language/subject coverage, freshness receipts, store isolation, and a read-only tool surface for analysis sessions.
5. Admit memory read-only before enabling writeback. Every memory needs scope, provenance, timestamp, retention/expiry, redaction class, and current-authority validation.
6. Keep the provider outputs separate so agreement is observable rather than collapsed into one untraceable summary.

## Alternatives and substitutions

A consumer may replace a provider without changing the shared Skill when it preserves the capability and evidence contract:

- semantic/structural retrieval: SCIP-based indexes, ast-grep, Semgrep, or a repository-specific index;
- symbol/impact analysis: compiler/LSP indexes, CodeQL, Joern, or Sourcegraph-style cross-repository indexes;
- memory: a repository-owned decision log, Letta, Zep/Graphiti, Cognee, or another scoped store.

Replacement is not based on feature count. Compare language coverage, subject identity, incremental freshness, offline/privacy model, read/write surface, operational dependencies, deterministic exports, negative controls, and measured task outcomes.

## Admission gates for Code-Graph-RAG

Before adding it to `.mcp.json` or `.codex/config.toml`:

```text
pin repository/package/image identity
isolate Memgraph/Qdrant per repository or namespace
record parser/language/path coverage and graph subject
expose read-only tools only in normal Agent sessions
block delete_project, wipe_database, index_repository, write_file,
  surgical_replace_code, and structural_replace behind explicit Human Admit
verify FOUND / NO_FLOW / UNKNOWN semantics and coverage gaps
run A/B against current GrepAI + Serena + direct-read pipeline
verify cleanup, persistence, storage, secrets, and network policy
```

## Admission gates for Mem0

Before activation:

```text
choose library, self-hosted, or managed authority explicitly
pin SDK/server and storage identities
define user/project/session namespaces
forbid secrets, credentials, raw signed-in content, and unbounded source bodies
define provenance, timestamps, retention, expiry, delete/export, and redaction
define memory-vs-CONTEXT/ADR/source conflict rule: current authority wins
start read-only; make writeback a separate reviewed transition
A/B memory-conflict, stale-memory, cross-project leakage, and no-memory fallback
```

## Current decision

Keep GrepAI, repo-context-pack, and Serena as configured candidate providers. Keep Code-Graph-RAG and Mem0 absent until their child admission issues produce deterministic controls and current receipts.
