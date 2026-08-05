import json, os, sys
EXTERNAL_ANTIGRAVITY_ROOT = os.environ.get("GCR_EXTERNAL_ANTIGRAVITY_ROOT", "/Users/neon/antigravity")
sys.path.insert(0, EXTERNAL_ANTIGRAVITY_ROOT)
G = os.environ.get("ANTIGRAVITY_GRAPH_PATH", os.path.join(EXTERNAL_ANTIGRAVITY_ROOT, ".cache/kg/graph.json"))
g = json.load(open(G))
nodes = {n["id"]: n for n in g.get("nodes", [])}
edges = g.get("edges", [])
conv = "conv:gemini:badf3207c3d54a13"
print("== graph.json 節點/邊驗證 ==")
print("conv 節點在:", conv in nodes, nodes.get(conv, {}).get("props", {}).get("title", "")[:40] if conv in nodes else "")
disc = [e for e in edges if e.get("src") == conv and e.get("type") == "DISCUSSES"]
ment = [e for e in edges if e.get("src") == conv and e.get("type") == "MENTIONS"]
print("DISCUSSES 邊:", len(disc), "| MENTIONS 邊:", len(ment), [e.get("dst") for e in ment])
lib = nodes.get("lib:notebooklm-py")
print("lib:notebooklm-py:", bool(lib), lib.get("props", {}) if lib else "")
# vector store 端：確認 chromadb collection 有嵌入（用 antigravity 自己的 store）
try:
    from indexing.store import GraphStore
    gs = GraphStore()
    print("== chromadb vector store ==")
    print("GraphStore node_count:", gs.node_count(), "edge_count:", gs.edge_count())
except Exception as e:
    print("GraphStore 讀取:", type(e).__name__, str(e)[:80])
