# Repo Context Pack MCP

Read-only, repository-bound MCP server for building evidence-budget Python AST context packs.

It is deliberately narrower than a code search or LSP server:

- GrepAI and Serena find candidate files and symbols.
- `repo-context-pack` re-opens the selected source under the configured repository root.
- It rejects absolute paths, traversal, symlink escapes, unsupported languages, oversized files,
  and files that change while being read.
- Every result is bound to the source bytes with SHA-256 and reports partial completeness.
- Signature and unresolved dynamic-call evidence is mandatory; lower-priority facts are dropped
  when the explicit byte budget is exhausted.

It does **not** claim that local memory page alignment controls remote prompt caching. Stable prompt
prefixes may improve server-side cache reuse, but cache hits must be measured at the API boundary.

## Bootstrap and verify

```bash
uv sync --project mcp/context-pack --locked
uv run --project mcp/context-pack --frozen python -m unittest discover \
  -s mcp/context-pack/tests -v
uv run --project mcp/context-pack --frozen \
  python mcp/context-pack/benchmarks/compare_extractors.py
```

The host starts `repo-context-pack-mcp` with the repository root as its working directory. An
absolute `REPO_CONTEXT_ROOT` may override that root for an intentionally different deployment.
Claude Code intentionally requires a human to approve each newly added project MCP once; approve
`repo-context-pack` when the project trust prompt appears. Do not bypass that supply-chain gate.

## Tools

- `build_python_context_pack(relative_path, symbol, max_bytes)`
- `context_pack_status()`

Only repository-relative `.py` paths are accepted. TypeScript support is not implied.
