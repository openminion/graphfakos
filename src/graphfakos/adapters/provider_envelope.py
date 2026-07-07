"""Provider-envelope adapter for large GraphFakos viewer inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..models import (
    GraphFakosCitation,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
    GraphFakosSnapshot,
    GraphFakosVisual,
)
from ..provider import validate_graph


class ProviderEnvelopeGraphProvider:
    """Load a provider-neutral viewer envelope from disk."""

    provider_id = "provider-envelope"
    provider_label = "Provider Envelope"
    graph_role = "provider_viewer_envelope"
    capabilities = (
        "cluster_overview",
        "large_graph_lod",
        "content_preview",
        "evidence",
        "static_export",
        "local_preview",
    )

    def __init__(self, envelope_path: str) -> None:
        self._path = Path(envelope_path).expanduser().resolve(strict=True)
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("provider envelope must be a JSON object")
        self._envelope = payload
        producer = _mapping(payload.get("producer"))
        self.provider_id = str(producer.get("package") or self.provider_id)
        self.provider_label = str(producer.get("package") or self.provider_label)

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        graph = graph_from_provider_envelope(
            self._envelope, source_path=str(self._path)
        )
        validate_graph(graph)
        return graph


def graph_from_provider_envelope(
    envelope: Mapping[str, Any],
    *,
    source_path: str = "",
) -> GraphFakosGraph:
    """Convert a provider-neutral viewer envelope into a GraphFakos graph."""

    clusters = tuple(_mapping(item) for item in envelope.get("clusters") or ())
    nodes = [_cluster_node(cluster) for cluster in clusters]
    nodes.extend(_raw_node(_mapping(item)) for item in envelope.get("nodes") or ())
    edges = [_raw_edge(_mapping(item)) for item in envelope.get("edges") or ()]
    edges.extend(
        _bundle_edge(_mapping(item)) for item in envelope.get("edge_bundles") or ()
    )
    stats = _mapping(envelope.get("graph_stats"))
    omitted = tuple(_mapping(item) for item in envelope.get("omitted") or ())
    hidden_nodes = sum(
        int(item.get("count", 0) or 0)
        for item in omitted
        if item.get("reason") == "node_budget"
    )
    hidden_edges = sum(
        int(item.get("count", 0) or 0)
        for item in omitted
        if item.get("reason") == "edge_budget"
    )
    graph = GraphFakosGraph(
        graph_id=str(envelope.get("snapshot_id") or "provider-envelope"),
        label=_graph_label(envelope),
        provider_id=str(
            _mapping(envelope.get("producer")).get("package") or "provider"
        ),
        provider_label=str(
            _mapping(envelope.get("producer")).get("package") or "Provider"
        ),
        graph_role="provider_viewer_envelope",
        capabilities=tuple(_capabilities(envelope)),
        nodes=tuple(nodes),
        edges=tuple(edges),
        provenance=tuple(
            _provenance(item) for item in envelope.get("provenance") or ()
        ),
        citations=tuple(_citations(envelope)),
        warnings=tuple(_warning_text(item) for item in omitted),
        stats={
            **stats,
            "hidden_nodes": hidden_nodes,
            "hidden_edges": hidden_edges,
            "level_of_detail": envelope.get("level_of_detail", ""),
            "provider_envelope": True,
            "source_path": source_path,
        },
        generated_at=str(envelope.get("generated_at") or ""),
        snapshot=GraphFakosSnapshot(
            snapshot_id=str(envelope.get("snapshot_id") or "provider-envelope"),
            label=_graph_label(envelope),
            created_at=str(envelope.get("generated_at") or ""),
            source_label=str(
                _mapping(envelope.get("root_identity")).get("root_path") or ""
            ),
            provider_payload={
                "schema_version": envelope.get("schema_version", ""),
                "snapshot_version": envelope.get("snapshot_version", ""),
            },
        ),
        provider_details={
            "schema": str(envelope.get("schema_version") or ""),
            "lod": str(envelope.get("level_of_detail") or ""),
            "source": source_path,
        },
        capability_details={
            "cluster_overview": "Cluster aggregate nodes and edge bundles are rendered by default.",
            "large_graph_lod": "Raw omitted counts remain provider-owned and expansion-ready.",
        },
        available_facets={
            "node_kind": tuple(sorted({node.kind for node in nodes})),
            "edge_kind": tuple(sorted({edge.kind for edge in edges})),
        },
        provider_payload={
            "viewer_envelope": envelope,
            "render_hint": dict(_mapping(envelope.get("render_hint"))),
        },
    )
    return graph


def _cluster_node(cluster: Mapping[str, Any]) -> GraphFakosNode:
    cluster_id = str(cluster.get("id") or "cluster")
    node_count = int(cluster.get("node_count", 0) or 0)
    edge_count = int(cluster.get("edge_count", 0) or 0)
    centroid = _mapping(cluster.get("centroid_hint"))
    return GraphFakosNode(
        id=f"cluster:{cluster_id}",
        label=str(cluster.get("label") or cluster_id),
        kind="cluster",
        summary=f"{node_count} raw nodes, {edge_count} raw edges.",
        tags=("cluster", str(cluster.get("kind") or "structural")),
        score=min(1.0, max(0.1, node_count / 10_000)),
        source="viewer-envelope",
        visual=GraphFakosVisual(
            color=str(cluster.get("color_hint") or ""),
            shape="pill",
            group=cluster_id,
            size=max(1, min(5, node_count // 1000)),
            x=_float_or_none(centroid.get("x")),
            y=_float_or_none(centroid.get("y")),
        ),
        provider_payload=dict(cluster),
    )


def _raw_node(node: Mapping[str, Any]) -> GraphFakosNode:
    cluster_id = str(node.get("cluster_id") or "")
    return GraphFakosNode(
        id=str(node.get("id") or ""),
        label=str(node.get("label") or node.get("id") or ""),
        kind=str(node.get("kind") or "node"),
        summary=str(node.get("summary") or ""),
        tags=tuple(
            item
            for item in (
                "sampled",
                str(node.get("source_kind") or ""),
                str(node.get("freshness") or ""),
            )
            if item
        ),
        score=_float_or_none(node.get("confidence")),
        confidence=_float_or_none(node.get("confidence")),
        source=str(node.get("source_kind") or ""),
        provenance_ids=(f"provenance:{node.get('id')}",),
        citation_ids=(f"citation:{node.get('id')}",),
        visual=GraphFakosVisual(group=cluster_id, size=1),
        provider_payload=dict(node),
    )


def _raw_edge(edge: Mapping[str, Any]) -> GraphFakosEdge:
    return GraphFakosEdge(
        id=str(edge.get("id") or ""),
        source_id=str(edge.get("source_id") or ""),
        target_id=str(edge.get("target_id") or ""),
        kind=str(edge.get("kind") or "relates"),
        label=str(edge.get("kind") or "relates"),
        confidence=_float_or_none(edge.get("confidence")),
        provider_payload=dict(edge),
    )


def _bundle_edge(bundle: Mapping[str, Any]) -> GraphFakosEdge:
    source = str(bundle.get("source_cluster_id") or "")
    target = str(bundle.get("target_cluster_id") or "")
    return GraphFakosEdge(
        id=str(bundle.get("id") or f"bundle:{source}:{target}"),
        source_id=f"cluster:{source}",
        target_id=f"cluster:{target}",
        kind="edge_bundle",
        label=f"{bundle.get('edge_count', 0)} bundled edge(s)",
        weight=_float_or_none(bundle.get("edge_count")),
        provider_payload=dict(bundle),
    )


def _provenance(payload: object) -> GraphFakosProvenance:
    item = _mapping(payload)
    node_id = str(item.get("node_id") or "")
    return GraphFakosProvenance(
        id=str(item.get("id") or f"provenance:{node_id}"),
        provider_id="provider-envelope",
        source_type=str(item.get("source") or "viewer-envelope"),
        source_label=node_id,
        excerpt=str(item.get("summary") or node_id),
        observed_at=str(item.get("observed_at") or ""),
        provider_payload=dict(item),
    )


def _citations(envelope: Mapping[str, Any]) -> tuple[GraphFakosCitation, ...]:
    content_index = _mapping(envelope.get("content_index"))
    citations: list[GraphFakosCitation] = []
    for node_id, raw_content in sorted(content_index.items()):
        content = _mapping(raw_content)
        source_ref = _mapping(content.get("source_ref"))
        citations.append(
            GraphFakosCitation(
                id=f"citation:{node_id}",
                label=str(content.get("title") or node_id),
                path=str(source_ref.get("path") or ""),
                line=_int_or_none(source_ref.get("line")),
                excerpt=str(content.get("text") or ""),
                provider_payload=dict(content),
            )
        )
    return tuple(citations)


def _capabilities(envelope: Mapping[str, Any]) -> tuple[str, ...]:
    capability_payload = _mapping(envelope.get("capabilities"))
    defaults = {
        "cluster_overview",
        "large_graph_lod",
        "content_preview",
        "static_export",
        "local_preview",
    }
    enabled = {key for key, value in capability_payload.items() if bool(value)}
    return tuple(sorted(defaults | enabled))


def _graph_label(envelope: Mapping[str, Any]) -> str:
    stats = _mapping(envelope.get("graph_stats"))
    node_count = int(stats.get("raw_node_count", 0) or 0)
    lod = str(envelope.get("level_of_detail") or "")
    return f"Provider Viewer Envelope ({node_count:,} nodes, {lod} LOD)"


def _warning_text(payload: Mapping[str, Any]) -> str:
    reason = payload.get("reason", "omitted")
    count = payload.get("count", 0)
    return f"{count} item(s) omitted by {reason}"


def _mapping(payload: object) -> dict[str, Any]:
    return dict(payload) if isinstance(payload, dict) else {}


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "ProviderEnvelopeGraphProvider",
    "graph_from_provider_envelope",
]
