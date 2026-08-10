from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path
from typing import Any


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def compute_communities(graph: dict[str, Any]) -> list[dict[str, Any]]:
    adjacency: dict[str, set[str]] = {node["id"]: set() for node in graph["nodes"]}
    for edge in graph["edges"]:
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
        adjacency.setdefault(edge["target"], set()).add(edge["source"])
    by_id = {node["id"]: node for node in graph["nodes"]}
    visited: set[str] = set()
    communities: list[dict[str, Any]] = []
    for node_id in sorted(adjacency):
        if node_id in visited:
            continue
        queue = deque([node_id])
        visited.add(node_id)
        members: list[str] = []
        while queue:
            current = queue.popleft()
            members.append(current)
            for neighbour in sorted(adjacency.get(current, set())):
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
        labels = [by_id[item]["label"] for item in members[:8] if item in by_id]
        community_id = str(len(communities))
        communities.append(
            {
                "id": community_id,
                "title": labels[0] if labels else f"Community {community_id}",
                "node_ids": sorted(members),
                "summary": " → ".join(labels),
                "summary_kind": "DETERMINISTIC_TOPOLOGY_SUMMARY",
                "warning": "This is not terminal evidence and is not an LLM-generated conclusion.",
            }
        )
    graph["communities"] = communities
    return communities


def export_graphrag(graph: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    communities = graph.get("communities") or compute_communities(graph)
    community_by_node = {
        node_id: community["id"]
        for community in communities
        for node_id in community.get("node_ids", [])
    }
    entities: list[dict[str, Any]] = []
    for index, node in enumerate(graph["nodes"]):
        location = node.get("location") or {}
        description = node.get("metadata", {}).get("description") or (
            f"{node['kind']} at {location.get('path', 'virtual')}:{location.get('start_line', '')}"
        )
        entities.append(
            {
                "id": node["id"],
                "human_readable_id": index,
                "title": node["label"],
                "type": node["kind"],
                "description": description,
                "text_unit_ids": json.dumps(
                    node.get("evidence_ids", []), ensure_ascii=False
                ),
                "community": community_by_node.get(node["id"], ""),
            }
        )
    relationships: list[dict[str, Any]] = []
    degree: dict[str, int] = {node["id"]: 0 for node in graph["nodes"]}
    for edge in graph["edges"]:
        degree[edge["source"]] = degree.get(edge["source"], 0) + 1
        degree[edge["target"]] = degree.get(edge["target"], 0) + 1
    for index, edge in enumerate(graph["edges"]):
        relationships.append(
            {
                "id": edge["id"],
                "human_readable_id": index,
                "source": edge["source"],
                "target": edge["target"],
                "description": f"{edge['kind']} via {','.join(edge.get('reach', [])) or 'UNKNOWN'}",
                "weight": 2.0 if edge.get("critical") else 1.0,
                "combined_degree": degree.get(edge["source"], 0)
                + degree.get(edge["target"], 0),
                "text_unit_ids": json.dumps(
                    edge.get("evidence_ids", []), ensure_ascii=False
                ),
            }
        )
    text_units: list[dict[str, Any]] = []
    for index, evidence in enumerate(graph["evidence"]):
        text = f"{evidence['summary']} Source: {evidence['source']}"
        text_units.append(
            {
                "id": evidence["id"],
                "human_readable_id": index,
                "text": text,
                "n_tokens": len(text.split()),
                "document_ids": json.dumps([evidence["source"]], ensure_ascii=False),
                "entity_ids": json.dumps(
                    [
                        node["id"]
                        for node in graph["nodes"]
                        if evidence["id"] in node.get("evidence_ids", [])
                    ],
                    ensure_ascii=False,
                ),
                "relationship_ids": json.dumps(
                    [
                        edge["id"]
                        for edge in graph["edges"]
                        if evidence["id"] in edge.get("evidence_ids", [])
                    ],
                    ensure_ascii=False,
                ),
                "covariate_ids": "[]",
            }
        )
    _write_csv(
        output_dir / "entities.csv",
        [
            "id",
            "human_readable_id",
            "title",
            "type",
            "description",
            "text_unit_ids",
            "community",
        ],
        entities,
    )
    _write_csv(
        output_dir / "relationships.csv",
        [
            "id",
            "human_readable_id",
            "source",
            "target",
            "description",
            "weight",
            "combined_degree",
            "text_unit_ids",
        ],
        relationships,
    )
    _write_csv(
        output_dir / "text_units.csv",
        [
            "id",
            "human_readable_id",
            "text",
            "n_tokens",
            "document_ids",
            "entity_ids",
            "relationship_ids",
            "covariate_ids",
        ],
        text_units,
    )
    (output_dir / "README.md").write_text(
        "# GraphRAG BYOG export\n\n"
        "The CSV files are deterministic exports of the authoritative graph. Convert them to Parquet "
        "with `python -m invariant_reach_graph.cli parquet --input <dir>` after installing `pyarrow`. "
        "GraphRAG summaries remain a query projection, never terminal evidence.\n",
        encoding="utf-8",
    )
    return {
        "entities": len(entities),
        "relationships": len(relationships),
        "text_units": len(text_units),
    }


def convert_csv_to_parquet(input_dir: Path) -> dict[str, str]:
    try:
        import pyarrow.csv as pacsv  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Parquet export requires optional dependency: pip install pyarrow"
        ) from exc
    outputs: dict[str, str] = {}
    for name in ("entities", "relationships", "text_units"):
        source = input_dir / f"{name}.csv"
        target = input_dir / f"{name}.parquet"
        table = pacsv.read_csv(source)
        pq.write_table(table, target)
        outputs[name] = str(target)
    return outputs
