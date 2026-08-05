#!/usr/bin/env python3
"""S9 INGEST driver — conv:gemini:badf3207c3d54a13（NotebookLM×Antigravity2.0 DR）。

為何是 driver 而非直接 CLI：`indexing.ingest_conversation` 的 CLI main() 不傳 libraries，
且 --dry-run 只印計數不算真 delta。此 driver 補兩者：
  - 程式化呼叫 ingest_conversation(..., libraries=[teng-lin/notebooklm-py]) 做 Library 升格。
  - dry-run 用真 builder + 載入既有 graph 判每概念 NEW vs JOIN，印完整 node/edge delta。

隔離：.md 讀進本程序 → Ollama extract_concepts，原文不進主 agent context（同影片軸 = 等價層）。
用法：python3 s9_ingest_badf3207.py            # dry-run（預設，零 KG 變更）
      python3 s9_ingest_badf3207.py --commit   # 實際 upsert
"""
import json
import os
import sys

EXTERNAL_ANTIGRAVITY_ROOT = os.environ.get("GCR_EXTERNAL_ANTIGRAVITY_ROOT", "/Users/neon/antigravity")
sys.path.insert(0, EXTERNAL_ANTIGRAVITY_ROOT)

from indexing.ingest_conversation import (  # noqa: E402
    ingest_conversation, conversation_node_id, library_node_id,
)
from indexing.concepts import canonical_concept_id, extract_concepts  # noqa: E402

CONV_ID = "badf3207c3d54a13"
TITLE = "基於 Antigravity 2.0 與 NotebookLM 代理式架構的數據科學自動化工作流深度研究報告"
URL = f"https://gemini.google.com/app/{CONV_ID}"
MD = "/Users/neon/ts-skill-bettor/gemini_research/gcr/badf3207c3d54a13-conversation.md"
GRAPH = os.environ.get(
    "ANTIGRAVITY_GRAPH_PATH",
    os.path.join(EXTERNAL_ANTIGRAVITY_ROOT, ".cache/kg/graph.json"),
)

# 唯一升格 Library（外驗 VERIFIED）；其餘 3 repo 為陪襯，留 Concept 不升格。
LIBRARIES = [
    {"raw_name": "teng-lin/notebooklm-py", "name": "notebooklm-py",
     "repo_url": "https://github.com/teng-lin/notebooklm-py", "license": "MIT"},
]

# S1 分析 + external-verify 的 grounded 分析概念（補 Ollama 漏掉的報告真貢獻）。
# 全部見於報告本文（S1 六維度 + verify.yaml）；非編造。
# ⚠ canonical_concept_id 是 latin-slug：純 CJK 名 → 'concept:' 退化被丟棄，故一律用 latin/英名
#   （這也讓 Feature Engineering/EDA/Multi-Agent 等 JOIN 既有影片/repo 概念 = 跨源價值）。
EXTRA_CONCEPTS = [
    "NotebookLM Bridge Pattern", "RPC Reverse Engineering", "Agentic Cloud Sandbox",
    "Token Burn Illusion", "Tool Drowning", "Cognitive Overload", "Progressive Disclosure",
    "Three-Tier Data Workflow", "Exploratory Data Analysis", "Feature Engineering",
    "Data Pipeline Automation", "RAG", "Hallucination-Free Knowledge Base",
    "Context Engineering", "Multi-Agent Orchestration",
    "Gemini 3.5 Flash", "Gemini 3.1 Pro", "Token Quota",
    "text-to-SQL", "SQL Semantic Understanding", "BIRD-CRITIC", "R-VES", "Auto-Debug Loop",
    "MCP", "Model Context Protocol", "Out-of-Memory", "Sandbox Quota",
    "Terminal-Bench", "MCP Atlas",
]

commit = "--commit" in sys.argv


def load_existing_ids():
    if not os.path.exists(GRAPH):
        return set()
    g = json.load(open(GRAPH))
    nodes = g.get("nodes", []) if isinstance(g, dict) else g
    return {n.get("id", "") for n in nodes if isinstance(n, dict)}


def main():
    with open(MD, encoding="utf-8") as f:
        text = f.read()
    print(f"[S9] extract_concepts via Ollama qwen3:4b（{len(text)} chars 讀入本程序，不進主 context）…")
    ollama_names = extract_concepts(text)  # 同影片軸引擎
    names = list(ollama_names) + EXTRA_CONCEPTS  # UNION S1/verify grounded 概念
    print(f"     Ollama {len(ollama_names)} + extra {len(EXTRA_CONCEPTS)} = {len(names)} raw（去重前）")
    # 去重（保序）by canonical id
    seen, concepts = set(), []
    for n in names:
        if not isinstance(n, str) or not n.strip():
            continue
        cid = canonical_concept_id(n)
        if not cid or cid == "concept:" or cid in seen:
            continue
        seen.add(cid)
        concepts.append((n, cid))

    existing = load_existing_ids()
    conv_id = conversation_node_id(CONV_ID)
    new_concepts = [(n, c) for n, c in concepts if c not in existing]
    join_concepts = [(n, c) for n, c in concepts if c in existing]

    lib_rows = []
    for lib in LIBRARIES:
        lid = library_node_id(lib["raw_name"])
        lib_rows.append((lib["raw_name"], lid, "JOIN 既有" if lid in existing else "NEW"))

    print("\n" + "=" * 68)
    print(f"S9 DELTA PREVIEW — {conv_id}")
    print("=" * 68)
    print(f"Conversation 節點 : {conv_id}  ({'已存在(idempotent)' if conv_id in existing else 'NEW'})")
    print(f"概念總數          : {len(concepts)}  (NEW {len(new_concepts)} / JOIN 既有 {len(join_concepts)})")
    print(f"DISCUSSES 邊      : {len(concepts)}  (conv → 每概念)")
    print(f"Library 升格      : {len(lib_rows)}")
    for raw, lid, state in lib_rows:
        print(f"    - {raw}  →  {lid}   [{state}]  + MENTIONS 邊")
    print(f"\n跨源 JOIN 既有概念（{len(join_concepts)}，合流不新建）:")
    for n, c in join_concepts[:30]:
        print(f"    ↔ {c}   ({n})")
    print(f"\nNEW 概念（{len(new_concepts)}）:")
    for n, c in new_concepts[:40]:
        print(f"    + {c}   ({n})")
    est_nodes = (0 if conv_id in existing else 1) + len(new_concepts) + sum(1 for _, l, s in lib_rows if s == "NEW")
    est_edges = len(concepts) + len(lib_rows)
    print(f"\n估計 node delta ≈ +{est_nodes}   edge delta ≈ +{est_edges}")
    print("=" * 68)

    if not commit:
        print("\n[dry-run] 未寫入任何東西。確認無誤後加 --commit 實際 ingest。")
        return 0

    print("\n[commit] upserting…")
    res = ingest_conversation(CONV_ID, TITLE, URL, text=text, extra_concepts=EXTRA_CONCEPTS,
                              libraries=LIBRARIES, graph_path=GRAPH)
    print(f"[ok] {res.conv_node_id}: {len(res.concepts)} concepts, "
          f"{len(res.libraries)} libraries → graph now {res.node_count} nodes / {res.edge_count} edges")
    print("     libraries:", res.libraries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
