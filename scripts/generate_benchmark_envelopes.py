#!/usr/bin/env python3
"""Generate deterministic provider envelopes for viewer scale validation."""

from __future__ import annotations

import argparse
import json
from math import cos, sin
from pathlib import Path


def nodes_per_cluster_for(total_nodes: int) -> int:
    if total_nodes >= 200_000:
        return 1_000
    return 100


def cluster_kind(index: int) -> str:
    return ("memory", "note", "file", "task", "provider", "warning")[index % 6]


def benchmark_envelope(total_nodes: int) -> dict[str, object]:
    nodes_per_cluster = nodes_per_cluster_for(total_nodes)
    cluster_count = total_nodes // nodes_per_cluster
    visible_cluster_count = min(cluster_count, 240)
    total_edges = int(total_nodes * 1.45)
    clusters = []
    nodes = []
    for index in range(cluster_count):
        cluster_id = f"scale-{index + 1:04d}"
        kind = cluster_kind(index)
        centroid_angle = index * 2.399963229728653
        centroid_ring = ((index % 37) + 8) / 45
        clusters.append(
            {
                "id": cluster_id,
                "label": f"Scale {index + 1:04d}",
                "kind": kind,
                "node_count": nodes_per_cluster,
                "edge_count": int(nodes_per_cluster * 1.45),
                "color_hint": "",
                "centroid_hint": {
                    "x": round(0.5 + 0.46 * centroid_ring * cos(centroid_angle), 4),
                    "y": round(0.5 + 0.42 * centroid_ring * sin(centroid_angle), 4),
                },
                "expansion_cursor": f"{cluster_id}:offset:0",
                "provider_payload": {
                    "sample_window": f"{index * nodes_per_cluster}-{(index + 1) * nodes_per_cluster - 1}",
                    "density": "large" if total_nodes >= 200_000 else "demo",
                },
            }
        )
        if index < visible_cluster_count:
            content = (
                f"{kind.title()} island {index + 1:04d} summarizes "
                f"{nodes_per_cluster} provider-owned facts. Expand with the cursor "
                "to stream exact records without loading the full graph."
            )
            nodes.append(
                {
                    "id": f"{cluster_id}:representative",
                    "label": f"Representative {index + 1:04d}",
                    "kind": kind,
                    "cluster_id": cluster_id,
                    "summary": content,
                    "content": content,
                    "preview": content[:120],
                    "source_kind": "synthetic-provider",
                    "freshness": "current",
                    "confidence": 0.9,
                }
            )
    edge_bundles = []
    for index in range(1, visible_cluster_count + 1):
        targets = {((index % visible_cluster_count) + 1)}
        if index % 5 == 0:
            targets.add(((index + 17) % visible_cluster_count) + 1)
        if index % 11 == 0:
            targets.add(
                ((index + visible_cluster_count // 3) % visible_cluster_count) + 1
            )
        for target in sorted(targets):
            if target == index:
                continue
            edge_bundles.append(
                {
                    "id": f"bundle:{index:04d}:{target:04d}",
                    "source_cluster_id": f"scale-{index:04d}",
                    "target_cluster_id": f"scale-{target:04d}",
                    "edge_count": 120 + (index * 13 + target * 7) % 180,
                    "kind": "aggregate_flow",
                }
            )
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
            "min_nodes_per_cluster": nodes_per_cluster,
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
