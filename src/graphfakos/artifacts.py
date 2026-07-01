"""Persisted graph artifact helpers."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path

from .models import GraphFakosGraph

GRAPHFAKOS_ARTIFACT_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "GraphFakos Graph Artifact",
    "type": "object",
    "required": [
        "graph_id",
        "label",
        "provider_id",
        "provider_label",
        "graph_role",
        "capabilities",
        "nodes",
        "edges",
    ],
    "properties": {
        "graph_id": {"type": "string"},
        "label": {"type": "string"},
        "provider_id": {"type": "string"},
        "provider_label": {"type": "string"},
        "graph_role": {"type": "string"},
        "capabilities": {"type": "array", "items": {"type": "string"}},
        "nodes": {"type": "array", "items": {"type": "object"}},
        "edges": {"type": "array", "items": {"type": "object"}},
        "provenance": {"type": "array", "items": {"type": "object"}},
        "citations": {"type": "array", "items": {"type": "object"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "stats": {"type": "object"},
        "generated_at": {"type": "string"},
        "snapshot": {"type": ["object", "null"]},
        "provider_details": {"type": "object"},
        "capability_details": {"type": "object"},
        "available_facets": {"type": "object"},
        "provider_payload": {"type": "object"},
    },
    "additionalProperties": True,
}


def graph_artifact_schema() -> dict[str, object]:
    return dict(GRAPHFAKOS_ARTIFACT_SCHEMA)


def validate_graph_artifact_payload(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, dict):
        raise TypeError("GraphFakos artifact payload must be an object")
    missing = [
        key for key in GRAPHFAKOS_ARTIFACT_SCHEMA["required"] if key not in payload
    ]
    if missing:
        raise ValueError(f"GraphFakos artifact is missing required fields: {missing!r}")
    if not isinstance(payload.get("nodes"), list):
        raise TypeError("GraphFakos artifact field 'nodes' must be a list")
    if not isinstance(payload.get("edges"), list):
        raise TypeError("GraphFakos artifact field 'edges' must be a list")
    if not isinstance(payload.get("capabilities"), list):
        raise TypeError("GraphFakos artifact field 'capabilities' must be a list")
    return payload


def graph_from_dict(payload: object) -> GraphFakosGraph:
    return GraphFakosGraph.from_dict(validate_graph_artifact_payload(payload))


def load_graph_artifact(path: str) -> GraphFakosGraph:
    artifact_path = Path(path).expanduser().resolve(strict=True)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    return graph_from_dict(payload)


def write_graph_artifact(
    graph: GraphFakosGraph,
    output_path: str,
) -> dict[str, object]:
    payload = graph.to_dict()
    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "output_path": str(path),
        "graph_id": graph.graph_id,
        "provider_id": graph.provider_id,
        "artifact": True,
    }


__all__ = [
    "GRAPHFAKOS_ARTIFACT_SCHEMA",
    "graph_artifact_schema",
    "graph_from_dict",
    "load_graph_artifact",
    "validate_graph_artifact_payload",
    "write_graph_artifact",
]
