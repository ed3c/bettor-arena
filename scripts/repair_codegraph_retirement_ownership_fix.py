#!/usr/bin/env python3
import json
from pathlib import Path

# scripts/gates/** is already owned by arena-core; do not double-own the checker.
path = Path('.arena/modules/knowledge-providers/module.json')
value = json.loads(path.read_text(encoding='utf-8'))
target = 'scripts/gates/check_code_graph_rag_retirement.py'
for paths in (value['roots'], value['components']['proof']['paths']):
    while target in paths:
        paths.remove(target)
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Context Capsule source list must not include the deleted active participant.
path = Path('.arena/contexts/knowledge-providers.json')
value = json.loads(path.read_text(encoding='utf-8'))
retired = 'docs/knowledge-providers/evals/participants/code-graph-rag.json'
value['common'] = [item for item in value['common'] if item != retired]
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Replace stale normative routing with the retired Blindspots evidence route.
path = Path('docs/knowledge-providers/CONTEXT.md')
text = path.read_text(encoding='utf-8')
old = '''4. Use Code-Graph-RAG only through an admitted read-only adapter with exact
   graph coverage and freshness.
5. Use Mem0 only for bounded recall or mutation proposals with provenance,
'''
new = '''4. For cross-module impact, combine exact source readback with admitted
   SCIP/LSP semantic facts and Tree-sitter structural coverage in the
   subject-bound Blindspots/SQLite evidence loop. Missing or stale coverage is
   `UNKNOWN`. Code-Graph-RAG is historical `RETIRED` evidence only.
5. Use Mem0 only for bounded recall or mutation proposals with provenance,
'''
if old not in text:
    raise SystemExit('knowledge-provider CONTEXT route anchor missing')
path.write_text(text.replace(old, new), encoding='utf-8')

path = Path('.skill-bindings/repo-agent-native/provider-map.md')
text = path.read_text(encoding='utf-8')
text = text.replace(
    '| cross-language graph impact | Code-Graph-RAG candidate | not configured | Tree-sitter/Memgraph graph, semantic/structural/data-flow tools | current MCP also exposes write/delete/wipe/index operations and external stores; requires a read-only admission wrapper |',
    '| cross-language impact evidence | SCIP/LSP + Tree-sitter + SQLite Blindspots loop | subject-bound contracts; live coverage separately evidenced | compiler/symbol facts plus structural slices with direct source readback | incomplete/stale/unsupported coverage remains `UNKNOWN`; SQLite is rebuildable evidence, not source authority |',
)
text = text.replace(
    'Code graph          what multi-file or cross-language edges are candidate impacts?',
    'Blindspots lenses   which multi-file/cross-language impacts are corroborated or still unknown?',
)
text = text.replace(
    '4. Admit a graph provider only with exact parser/language/subject coverage, freshness receipts, store isolation, and a read-only tool surface for analysis sessions.',
    '4. For impact analysis, require exact subject identity, SCIP/LSP and Tree-sitter coverage declarations, SQLite evidence provenance, and direct source readback. Do not revive Code-Graph-RAG as an active provider.',
)
start = text.find('## Admission gates for Code-Graph-RAG')
end = text.find('## Admission gates for Mem0')
if start == -1 or end == -1 or end <= start:
    raise SystemExit('provider-map Code-Graph-RAG section anchors missing')
replacement = '''## Code-Graph-RAG retirement\n\nCode-Graph-RAG is retained only as historical `REJECTED / ABSENT` evidence. It must not be added to `.mcp.json`, `.codex/config.toml`, provider evaluation participants, runtime activation, or queue prerequisites. Cross-module impact uses the source/SCIP/LSP/Tree-sitter/SQLite Blindspots path, with incomplete coverage remaining `UNKNOWN`.\n\n'''
text = text[:start] + replacement + text[end:]
text = text.replace(
    'Keep GrepAI, repo-context-pack, and Serena as configured candidate providers. Keep Code-Graph-RAG and Mem0 absent until their child admission issues produce deterministic controls and current receipts.',
    'Keep GrepAI, repo-context-pack, and Serena as configured candidate providers. Code-Graph-RAG is retired from the active route and remains historical `REJECTED / ABSENT`; Mem0 remains absent until its admission work produces deterministic controls and current receipts.',
)
path.write_text(text, encoding='utf-8')

path = Path('docs/knowledge-providers/alternatives.md')
text = path.read_text(encoding='utf-8')
text = text.replace(
    '| Code-Graph-RAG | cross-language graph, structural and semantic query, data-flow candidates | heavier stores, parser coverage, mutable MCP surface | read-only admission candidate |',
    '| Code-Graph-RAG | historical evaluated graph route | heavier stores, parser coverage, mutable MCP surface | **RETIRED**; preserved only for decision history, never active selection |',
)
path.write_text(text, encoding='utf-8')
