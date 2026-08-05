#!/usr/bin/env python3
"""S9 INGEST driver — conv:gemini:a2d11a2f284bace6（大小迴圈 evals 自動提示研究，Mode B）。

同 s9_ingest_badf3207.py 模式：CLI main() 不傳 libraries，故程式化呼叫；dry-run 預設。
隔離：.md 讀進本程序 → Ollama extract_concepts，原文不進主 agent context。
用法：python3.12 s9_ingest_a2d11a2f.py            # dry-run
      python3.12 s9_ingest_a2d11a2f.py --commit   # 實際 upsert
"""
import json
import os
import sys

EXTERNAL_ANTIGRAVITY_ROOT = os.environ.get("GCR_EXTERNAL_ANTIGRAVITY_ROOT", "/Users/neon/antigravity")
sys.path.insert(0, EXTERNAL_ANTIGRAVITY_ROOT)

from indexing.ingest_conversation import (  # noqa: E402
    ingest_conversation, conversation_node_id, library_node_id,
)

CONV_ID = "a2d11a2f284bace6"
TITLE = "Eval-driven loop auto-prompting: zero-human harness (Mode B QA + 3 DR)"
URL = f"https://gemini.google.com/app/{CONV_ID}"
MD = "/Users/neon/ts-skill-bettor/gemini_research/gcr/loop-evals-autoprompt-qa-session.md"
GRAPH = os.environ.get(
    "ANTIGRAVITY_GRAPH_PATH",
    os.path.join(EXTERNAL_ANTIGRAVITY_ROOT, ".cache/kg/graph.json"),
)

# external-verify VERIFIED 真 repo（gap-02 由 GitHub 源碼落錨 caps；raw_name=org/repo 消歧）。
# anthropics/claude-code 僅以 issue 佐證出現，留 Concept 不升格。
LIBRARIES = [
    {"raw_name": "SWE-agent/SWE-agent", "name": "SWE-agent",
     "repo_url": "https://github.com/SWE-agent/SWE-agent", "license": "MIT"},
    {"raw_name": "All-Hands-AI/OpenHands", "name": "OpenHands",
     "repo_url": "https://github.com/All-Hands-AI/OpenHands", "license": "MIT"},
    {"raw_name": "Aider-AI/aider", "name": "aider",
     "repo_url": "https://github.com/Aider-AI/aider", "license": "Apache-2.0"},
    {"raw_name": "SWE-bench/SWE-bench", "name": "SWE-bench",
     "repo_url": "https://github.com/SWE-bench/SWE-bench", "license": "MIT"},
]

# S1 六維度 + 3 DR + verify 帳本的 grounded 概念（latin-slug 存活；CJK 名會退化被丟）。
# 全部見於 session/DR/verify 產物本文；E7 類 confabulation 已剔除、不入庫。
EXTRA_CONCEPTS = [
    "Eval-Driven Auto-Prompting", "Stop Hook", "Headless CLI Loop", "Ralph Loop",
    "Iterate-Until-Pass", "Stop-Loss", "State Ledger", "Negative Knowledge",
    "Anti-Repeat Ledger", "Diff Hash Deduplication", "Failure Signature",
    "No-Progress Detection", "Reward Hacking", "Goodhart's Law", "Verifier Bypass",
    "conftest Hijack", "Memory Poisoning", "Prompt Injection",
    "MINJA", "A-MemGuard", "MemLineage", "Spotlighting",
    "Context Compaction", "Context Folding", "Memory Condenser",
    "Fresh Context Re-invocation", "Reflexion", "LLM-as-Judge", "Intent Alignment",
    "EvilGenie", "SWE-bench Verified", "SWE-bench Pro", "Terminal-Bench",
    "Firecracker", "gVisor", "Sandbox Isolation", "Read-Only Mounts",
    "Network-Off Sandbox", "Human Gate", "PR Review Gate", "Plan Approval",
    "Iteration Cap", "Cost Limit", "Work Queue", "Scheduled Tasks",
    "Event-Driven Trigger", "Lifecycle Hooks", "Completion Promise",
    "Benchmark Manipulation", "Pre-Registered Evals",
]

commit = "--commit" in sys.argv
res = ingest_conversation(
    CONV_ID, TITLE, URL,
    text=open(MD, encoding="utf-8").read(),
    extra_concepts=EXTRA_CONCEPTS,
    libraries=LIBRARIES,
    graph_path=GRAPH if commit else None,
) if commit else None

if not commit:
    # dry-run：載入既有 graph 判 NEW vs JOIN（同 badf3207 driver 模式）
    from indexing.concepts import canonical_concept_id
    g = json.load(open(GRAPH, encoding="utf-8"))
    existing = {n["id"] for n in g.get("nodes", [])}
    conv_node = conversation_node_id(CONV_ID)
    print(f"[dry-run] conv node: {conv_node} ({'JOIN' if conv_node in existing else 'NEW'})")
    new = joins = dropped = 0
    for c in EXTRA_CONCEPTS:
        cid = canonical_concept_id(c)
        if not cid or cid == "concept:":
            dropped += 1
            print(f"  DROP (slug 退化): {c}")
        elif cid in existing:
            joins += 1
        else:
            new += 1
    print(f"[dry-run] extra_concepts: {len(EXTRA_CONCEPTS)} → NEW {new} / JOIN {joins} / DROP {dropped}")
    for lib in LIBRARIES:
        lid = library_node_id(lib["raw_name"])
        print(f"[dry-run] lib {lib['raw_name']} → {lid} ({'JOIN' if lid in existing else 'NEW'})")
    print("[dry-run] 未寫入。--commit 實際 upsert（含 Ollama 全文概念抽取）。")
else:
    # ConversationIngestResult 是 dataclass 非 dict，直接印屬性（cc-20260720 修：json.dumps 會 TypeError）
    print(res)
