from __future__ import annotations

import json
import subprocess
import sys

from graphfakos.adapters.provider_envelope import graph_from_provider_envelope


def _provider_envelope() -> dict[str, object]:
    return {
        "schema_version": "pragmagraph.viewer.v1alpha1",
        "producer": {"package": "pragmagraph", "contract": "viewer-envelope"},
        "snapshot_id": "fixture:viewer-scale-200k:20260706",
        "snapshot_version": "fixture.v1",
        "root_identity": {"namespace": "viewer-scale-200k", "root_path": "synthetic"},
        "generated_at": "2026-07-06T00:00:00+00:00",
        "graph_stats": {
            "raw_node_count": 200_000,
            "raw_edge_count": 290_000,
            "visible_node_count": 2,
            "visible_edge_count": 1,
            "cluster_count": 2,
        },
        "render_hint": {
            "preferred_engine": "3d",
            "theme": "space",
            "layout": "islands",
        },
        "level_of_detail": "cluster",
        "nodes": [
            {
                "id": "scale-001:node:0000",
                "label": "File Scale 001",
                "kind": "file",
                "source_kind": "python",
                "cluster_id": "scale-001",
                "summary": "Observed file content.",
                "confidence": 0.9,
                "freshness": "fresh",
            },
            {
                "id": "scale-002:node:0000",
                "label": "Symbol Scale 002",
                "kind": "symbol",
                "source_kind": "python",
                "cluster_id": "scale-002",
                "summary": "Observed symbol content.",
                "confidence": 0.8,
                "freshness": "changed",
            },
        ],
        "edges": [
            {
                "id": "edge:visible",
                "source_id": "scale-001:node:0000",
                "target_id": "scale-002:node:0000",
                "kind": "references",
            }
        ],
        "clusters": [
            {
                "id": "scale-001",
                "label": "Scale 001",
                "kind": "file",
                "node_count": 100_000,
                "edge_count": 140_000,
                "color_hint": "#64d9f3",
                "centroid_hint": {"x": 0.2, "y": 0.3},
                "expansion_cursor": "scale-001:offset:0",
            },
            {
                "id": "scale-002",
                "label": "Scale 002",
                "kind": "symbol",
                "node_count": 100_000,
                "edge_count": 150_000,
                "color_hint": "#9e7cff",
                "centroid_hint": {"x": 0.8, "y": 0.6},
                "expansion_cursor": "scale-002:offset:0",
            },
        ],
        "edge_bundles": [
            {
                "id": "bundle:scale-001:scale-002",
                "source_cluster_id": "scale-001",
                "target_cluster_id": "scale-002",
                "edge_count": 1200,
            }
        ],
        "omitted": [
            {"reason": "node_budget", "count": 199_998},
            {"reason": "edge_budget", "count": 289_999},
        ],
        "content_index": {
            "scale-001:node:0000": {
                "title": "File Scale 001",
                "text": "Actual provider content preview.",
                "source_ref": {"path": "src/file.py", "line": 1},
            }
        },
        "capabilities": {"content_preview": True, "durable_mutation": False},
    }


def test_provider_envelope_converts_to_cluster_graph() -> None:
    graph = graph_from_provider_envelope(_provider_envelope())

    assert graph.provider_id == "pragmagraph"
    assert graph.stats["provider_envelope"] is True
    assert graph.stats["hidden_nodes"] == 199_998
    assert any(node.kind == "cluster" for node in graph.nodes)
    assert any(edge.kind == "edge_bundle" for edge in graph.edges)
    assert graph.citations[0].excerpt == "Actual provider content preview."


def test_provider_envelope_cli_renders_3d_space_route(tmp_path) -> None:
    envelope_path = tmp_path / "viewer.json"
    html_path = tmp_path / "viewer.html"
    envelope_path.write_text(
        json.dumps(_provider_envelope(), sort_keys=True),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui",
            "--provider-envelope",
            str(envelope_path),
            "--render-engine",
            "3d",
            "--theme",
            "space",
            "--html-out",
            str(html_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    html = html_path.read_text(encoding="utf-8")

    assert payload["provider_id"] == "pragmagraph"
    assert payload["node_count"] == 4
    assert "data-theme='space'" in html
    assert "render-engine='3d'" in html
    assert "3D navigation mode is selected" in html
    assert "199998 node(s)" in html
