import json, os
EXTERNAL_ANTIGRAVITY_ROOT = os.environ.get("GCR_EXTERNAL_ANTIGRAVITY_ROOT", "/Users/neon/antigravity")
p = os.environ.get("ANTIGRAVITY_GRAPH_PATH", os.path.join(EXTERNAL_ANTIGRAVITY_ROOT, ".cache/kg/graph.json"))
if not os.path.exists(p):
    print("GRAPH_MISSING", p); raise SystemExit
g = json.load(open(p))
if isinstance(g, dict):
    nodes = g.get("nodes", []); edges = g.get("edges", [])
else:
    nodes, edges = g, []
def nid(n): return n.get("id", "") if isinstance(n, dict) else ""
print("nodes:", len(nodes), "edges:", len(edges))
hits = [nid(n) for n in nodes if isinstance(n, dict) and
        ("notebooklm" in nid(n).lower() or "badf3207" in nid(n).lower())]
print("notebooklm/conv 命中:")
for h in hits[:25]:
    print("  ", h)
print("total lib: nodes =", sum(1 for n in nodes if isinstance(n, dict) and nid(n).startswith("lib:")))
