"""Provider-neutral graph viewer DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

GraphFakosScreen = Literal[
    "explore",
    "neighborhood",
    "path",
    "provenance",
    "timeline",
    "diff",
    "provider_status",
    "context_preview",
]


@dataclass(frozen=True, slots=True)
class GraphFakosVisual:
    color: str = ""
    icon: str = ""
    shape: str = "circle"
    size: int = 1
    group: str = ""
    emphasis: str = ""
    muted: bool = False
    pinned: bool = False
    x: float | None = None
    y: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "color": self.color,
            "icon": self.icon,
            "shape": self.shape,
            "size": self.size,
            "group": self.group,
            "emphasis": self.emphasis,
            "muted": self.muted,
            "pinned": self.pinned,
            "x": self.x,
            "y": self.y,
        }


@dataclass(frozen=True, slots=True)
class GraphFakosCitation:
    id: str
    label: str = ""
    uri: str = ""
    path: str = ""
    line: int | None = None
    span: str = ""
    excerpt: str = ""
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "uri": self.uri,
            "path": self.path,
            "line": self.line,
            "span": self.span,
            "excerpt": self.excerpt,
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosProvenance:
    id: str
    provider_id: str
    source_type: str = ""
    source_label: str = ""
    source_uri: str = ""
    excerpt: str = ""
    observed_at: str = ""
    created_at: str = ""
    updated_at: str = ""
    confidence: float | None = None
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "source_type": self.source_type,
            "source_label": self.source_label,
            "source_uri": self.source_uri,
            "excerpt": self.excerpt,
            "observed_at": self.observed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confidence": self.confidence,
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosSnapshot:
    snapshot_id: str
    label: str = ""
    created_at: str = ""
    source_label: str = ""
    source_uri: str = ""
    comparison_ids: tuple[str, ...] = ()
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "label": self.label,
            "created_at": self.created_at,
            "source_label": self.source_label,
            "source_uri": self.source_uri,
            "comparison_ids": list(self.comparison_ids),
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosNode:
    id: str
    label: str
    kind: str
    summary: str = ""
    tags: tuple[str, ...] = ()
    score: float | None = None
    confidence: float | None = None
    source: str = ""
    timestamps: dict[str, str] = field(default_factory=dict)
    provenance_ids: tuple[str, ...] = ()
    citation_ids: tuple[str, ...] = ()
    visual: GraphFakosVisual = field(default_factory=GraphFakosVisual)
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "summary": self.summary,
            "tags": list(self.tags),
            "score": self.score,
            "confidence": self.confidence,
            "source": self.source,
            "timestamps": dict(self.timestamps),
            "provenance_ids": list(self.provenance_ids),
            "citation_ids": list(self.citation_ids),
            "visual": self.visual.to_dict(),
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosEdge:
    id: str
    source_id: str
    target_id: str
    kind: str
    label: str = ""
    weight: float | None = None
    confidence: float | None = None
    direction: str = "directed"
    provenance_ids: tuple[str, ...] = ()
    citation_ids: tuple[str, ...] = ()
    visual: GraphFakosVisual = field(default_factory=GraphFakosVisual)
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "kind": self.kind,
            "label": self.label,
            "weight": self.weight,
            "confidence": self.confidence,
            "direction": self.direction,
            "provenance_ids": list(self.provenance_ids),
            "citation_ids": list(self.citation_ids),
            "visual": self.visual.to_dict(),
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosGraph:
    graph_id: str
    label: str
    provider_id: str
    provider_label: str
    graph_role: str
    capabilities: tuple[str, ...]
    nodes: tuple[GraphFakosNode, ...]
    edges: tuple[GraphFakosEdge, ...]
    provenance: tuple[GraphFakosProvenance, ...] = ()
    citations: tuple[GraphFakosCitation, ...] = ()
    warnings: tuple[str, ...] = ()
    stats: dict[str, object] = field(default_factory=dict)
    generated_at: str = ""
    snapshot: GraphFakosSnapshot | None = None
    provider_details: dict[str, str] = field(default_factory=dict)
    capability_details: dict[str, str] = field(default_factory=dict)
    available_facets: dict[str, tuple[str, ...]] = field(default_factory=dict)
    provider_payload: dict[str, object] = field(default_factory=dict)

    def node_map(self) -> dict[str, GraphFakosNode]:
        return {node.id: node for node in self.nodes}

    def edge_map(self) -> dict[str, GraphFakosEdge]:
        return {edge.id: edge for edge in self.edges}

    def to_dict(self) -> dict[str, object]:
        return {
            "graph_id": self.graph_id,
            "label": self.label,
            "provider_id": self.provider_id,
            "provider_label": self.provider_label,
            "graph_role": self.graph_role,
            "capabilities": list(self.capabilities),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "provenance": [item.to_dict() for item in self.provenance],
            "citations": [item.to_dict() for item in self.citations],
            "warnings": list(self.warnings),
            "stats": dict(self.stats),
            "generated_at": self.generated_at,
            "snapshot": self.snapshot.to_dict() if self.snapshot is not None else None,
            "provider_details": dict(self.provider_details),
            "capability_details": dict(self.capability_details),
            "available_facets": {
                key: list(values) for key, values in self.available_facets.items()
            },
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosDiagnostics:
    node_count: int
    edge_count: int
    provenance_count: int
    citation_count: int
    orphan_node_ids: tuple[str, ...] = ()
    duplicate_edge_ids: tuple[str, ...] = ()
    unknown_provenance_ids: tuple[str, ...] = ()
    unknown_citation_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def healthy(self) -> bool:
        return not (
            self.orphan_node_ids
            or self.duplicate_edge_ids
            or self.unknown_provenance_ids
            or self.unknown_citation_ids
            or self.warnings
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "healthy": self.healthy,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "provenance_count": self.provenance_count,
            "citation_count": self.citation_count,
            "orphan_node_ids": list(self.orphan_node_ids),
            "duplicate_edge_ids": list(self.duplicate_edge_ids),
            "unknown_provenance_ids": list(self.unknown_provenance_ids),
            "unknown_citation_ids": list(self.unknown_citation_ids),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class GraphFakosRequest:
    screen: GraphFakosScreen = "explore"
    query: str = ""
    focus_node_id: str | None = None
    selected_edge_id: str | None = None
    source_node_id: str | None = None
    target_node_id: str | None = None
    comparison_graph_id: str | None = None
    max_depth: int = 1
    filters: dict[str, str] = field(default_factory=dict)
    layout: str = "force"
    include_provenance: bool = True
    include_provider_payload: bool = True
    limit: int = 25
    render_limit: int = 120

    def with_screen(self, screen: GraphFakosScreen) -> GraphFakosRequest:
        return GraphFakosRequest(
            screen=screen,
            query=self.query,
            focus_node_id=self.focus_node_id,
            selected_edge_id=self.selected_edge_id,
            source_node_id=self.source_node_id,
            target_node_id=self.target_node_id,
            comparison_graph_id=self.comparison_graph_id,
            max_depth=self.max_depth,
            filters=dict(self.filters),
            layout=self.layout,
            include_provenance=self.include_provenance,
            include_provider_payload=self.include_provider_payload,
            limit=self.limit,
            render_limit=self.render_limit,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "screen": self.screen,
            "query": self.query,
            "focus_node_id": self.focus_node_id,
            "selected_edge_id": self.selected_edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "comparison_graph_id": self.comparison_graph_id,
            "max_depth": self.max_depth,
            "filters": dict(self.filters),
            "layout": self.layout,
            "include_provenance": self.include_provenance,
            "include_provider_payload": self.include_provider_payload,
            "limit": self.limit,
            "render_limit": self.render_limit,
        }


__all__ = [
    "GraphFakosCitation",
    "GraphFakosDiagnostics",
    "GraphFakosEdge",
    "GraphFakosGraph",
    "GraphFakosNode",
    "GraphFakosProvenance",
    "GraphFakosRequest",
    "GraphFakosScreen",
    "GraphFakosSnapshot",
    "GraphFakosVisual",
]
