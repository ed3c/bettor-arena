#!/usr/bin/env python3
"""S9 追加 — 把 gcr S8 DR 查證過的 OSS 技術實現等價物升 KG Library。

MENTIONS 掛在 conv:gemini:badf3207c3d54a13（同 notebooklm-py 待遇）——語義=「研究本對話
DS 工作流主題所 surfacve + external-verify 過的 OSS 等價物」。只加 Library + MENTIONS，
不重抽概念（text=None, extra_concepts=None）。idempotent（upsert dedup）。

用法：python3 s9_libs_badf3207.py           # dry-run
      python3 s9_libs_badf3207.py --commit  # 實際 upsert
需用有 chromadb 1.5.9 的直譯器：/Users/neon/northstar/.venv/bin/python
"""
import json
import os
import sys

EXTERNAL_ANTIGRAVITY_ROOT = os.environ.get("GCR_EXTERNAL_ANTIGRAVITY_ROOT", "/Users/neon/antigravity")
sys.path.insert(0, EXTERNAL_ANTIGRAVITY_ROOT)

from indexing.ingest_conversation import (  # noqa: E402
    ingest_conversation, conversation_node_id, library_node_id,
)

CONV_ID = "badf3207c3d54a13"
TITLE = "基於 Antigravity 2.0 與 NotebookLM 代理式架構的數據科學自動化工作流深度研究報告"
URL = f"https://gemini.google.com/app/{CONV_ID}"
GRAPH = os.environ.get(
    "ANTIGRAVITY_GRAPH_PATH",
    os.path.join(EXTERNAL_ANTIGRAVITY_ROOT, ".cache/kg/graph.json"),
)

# 8 維矩陣 + 維度 4 收斂的 2 glue 基元。全 external-verify VERIFIED、permissive、raw_name=org/repo 消歧。
LIBRARIES = [
    {"raw_name": "Data-Centric-AI-Community/fg-data-profiling", "name": "fg-data-profiling",
     "repo_url": "https://github.com/Data-Centric-AI-Community/fg-data-profiling", "license": "MIT"},
    {"raw_name": "feast-dev/feast", "name": "feast",
     "repo_url": "https://github.com/feast-dev/feast", "license": "Apache-2.0"},
    {"raw_name": "PrefectHQ/prefect", "name": "prefect",
     "repo_url": "https://github.com/PrefectHQ/prefect", "license": "Apache-2.0"},
    {"raw_name": "cube-js/cube", "name": "cube",
     "repo_url": "https://github.com/cube-js/cube", "license": "Apache-2.0"},
    {"raw_name": "Cinnamon/kotaemon", "name": "kotaemon",
     "repo_url": "https://github.com/Cinnamon/kotaemon", "license": "Apache-2.0"},
    {"raw_name": "alibaba/OpenSandbox", "name": "OpenSandbox",
     "repo_url": "https://github.com/alibaba/OpenSandbox", "license": "Apache-2.0"},
    {"raw_name": "vllm-project/vllm", "name": "vllm",
     "repo_url": "https://github.com/vllm-project/vllm", "license": "Apache-2.0"},
    {"raw_name": "langfuse/langfuse", "name": "langfuse",
     "repo_url": "https://github.com/langfuse/langfuse", "license": "MIT"},
    {"raw_name": "tobymao/sqlglot", "name": "sqlglot",
     "repo_url": "https://github.com/tobymao/sqlglot", "license": "MIT"},
    {"raw_name": "langchain-ai/langgraph", "name": "langgraph",
     "repo_url": "https://github.com/langchain-ai/langgraph", "license": "MIT"},
]

commit = "--commit" in sys.argv


def load_existing_ids():
    if not os.path.exists(GRAPH):
        return set()
    g = json.load(open(GRAPH))
    nodes = g.get("nodes", []) if isinstance(g, dict) else g
    return {n.get("id", "") for n in nodes if isinstance(n, dict)}


def main():
    existing = load_existing_ids()
    conv_id = conversation_node_id(CONV_ID)
    print("=" * 66)
    print(f"S9 LIBS — MENTIONS from {conv_id}  ({'存在' if conv_id in existing else 'NEW'})")
    print("=" * 66)
    rows = []
    for lib in LIBRARIES:
        lid = library_node_id(lib["raw_name"])
        state = "JOIN 既有" if lid in existing else "NEW"
        rows.append((lib["raw_name"], lid, lib["license"], state))
        print(f"  {lib['raw_name']:42s} → {lid:22s} {lib['license']:12s} [{state}]")
    new_n = sum(1 for *_, s in rows if s == "NEW")
    join_n = sum(1 for *_, s in rows if s != "NEW")
    print(f"\nLibrary: {new_n} NEW / {join_n} JOIN 既有（跨源 enrich）")
    print(f"MENTIONS 邊: {len(rows)}（conv → 每 lib，idempotent）")
    print(f"估計 node delta ≈ +{new_n}   edge delta ≈ +{len(rows)}（既有 MENTIONS 會 dedup）")
    print("=" * 66)

    if not commit:
        print("\n[dry-run] 未寫入。加 --commit 實際 upsert。")
        return 0

    print("\n[commit] upserting libraries + MENTIONS（不動概念）…")
    res = ingest_conversation(CONV_ID, TITLE, URL, text=None, extra_concepts=None,
                              libraries=LIBRARIES, graph_path=GRAPH)
    print(f"[ok] {res.conv_node_id}: {len(res.libraries)} libraries → "
          f"graph now {res.node_count} nodes / {res.edge_count} edges")
    print("     libraries:", res.libraries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
