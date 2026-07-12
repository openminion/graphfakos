#!/usr/bin/env python3
"""Generate deterministic provider envelopes for viewer scale validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def benchmark_envelope(total_nodes: int) -> dict[str, object]:
    nodes_per_cluster = 100 if total_nodes == 1_000 else 1_000
    cluster_count = total_nodes // nodes_per_cluster
    visible_cluster_count = min(cluster_count, 240)
    total_edges = int(total_nodes * 1.45)
    clusters = []
    nodes = []
    for index in range(cluster_count):
        cluster_id = f"scale-{index + 1:04d}"
        clusters.append(
            {
                "id": cluster_id,
                "label": f"Scale {index + 1:04d}",
                "kind": "community",
                "node_count": nodes_per_cluster,
                "edge_count": int(nodes_per_cluster * 1.45),
                "expansion_cursor": f"{cluster_id}:offset:0",
            }
        )
        if index < visible_cluster_count:
            nodes.append(
                {
                    "id": f"{cluster_id}:representative",
                    "label": f"Representative {index + 1:04d}",
                    "kind": "cluster",
                    "cluster_id": cluster_id,
                    "summary": f"Aggregate representative for {nodes_per_cluster} nodes.",
                    "confidence": 0.9,
                }
            )
    edge_bundles = [
        {
            "id": f"bundle:{index:04d}:{index + 1:04d}",
            "source_cluster_id": f"scale-{index:04d}",
            "target_cluster_id": f"scale-{index + 1:04d}",
            "edge_count": 120 + index % 80,
        }
        for index in range(1, visible_cluster_count)
    ]
    visible_nodes = len(nodes) + len(clusters)
    return {
        "schema_version": "graphfakos.viewer.v1alpha1",
        "producer": {"package": "graphfakos", "contract": "viewer-envelope"},
        "snapshot_id": f"fixture:viewer-scale-{total_nodes}:20260712",
        "snapshot_version": "fixture.v2",
        "root_identity": {
            "namespace": f"viewer-scale-{total_nodes}",
            "root_path": "synthetic",
        },
        "generated_at": "2026-07-12T00:00:00+00:00",
        "graph_stats": {
            "raw_node_count": total_nodes,
            "raw_edge_count": total_edges,
            "visible_node_count": visible_nodes,
            "visible_edge_count": len(edge_bundles),
            "cluster_count": cluster_count,
        },
        "render_hint": {
            "preferred_engine": "3d",
            "theme": "space",
            "layout": "islands",
        },
        "level_of_detail": "cluster",
        "nodes": nodes,
        "edges": [],
        "clusters": clusters,
        "edge_bundles": edge_bundles,
        "omitted": [
            {"reason": "node_budget", "count": max(0, total_nodes - visible_nodes)},
            {"reason": "edge_budget", "count": max(0, total_edges - len(edge_bundles))},
        ],
        "capabilities": {"content_preview": True, "durable_mutation": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for total_nodes in (1_000, 200_000, 1_000_000):
        output = args.out_dir / f"viewer-scale-{total_nodes}.json"
        output.write_text(
            json.dumps(benchmark_envelope(total_nodes), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
