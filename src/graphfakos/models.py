"""Provider-neutral graph viewer DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, cast

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

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosVisual:
        return cls(
            color=_string(payload.get("color", ""), "visual.color"),
            icon=_string(payload.get("icon", ""), "visual.icon"),
            shape=_string(payload.get("shape", "circle"), "visual.shape"),
            size=_int(payload.get("size", 1), "visual.size"),
            group=_string(payload.get("group", ""), "visual.group"),
            emphasis=_string(payload.get("emphasis", ""), "visual.emphasis"),
            muted=_bool(payload.get("muted", False), "visual.muted"),
            pinned=_bool(payload.get("pinned", False), "visual.pinned"),
            x=_float_or_none(payload.get("x"), "visual.x"),
            y=_float_or_none(payload.get("y"), "visual.y"),
        )


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
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosCitation:
        return cls(
            id=_required_string(payload, "id", "citation.id"),
            label=_string(payload.get("label", ""), "citation.label"),
            uri=_string(payload.get("uri", ""), "citation.uri"),
            path=_string(payload.get("path", ""), "citation.path"),
            line=_int_or_none(payload.get("line"), "citation.line"),
            span=_string(payload.get("span", ""), "citation.span"),
            excerpt=_string(payload.get("excerpt", ""), "citation.excerpt"),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "citation.provider_payload",
            ),
        )


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
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosProvenance:
        return cls(
            id=_required_string(payload, "id", "provenance.id"),
            provider_id=_required_string(payload, "provider_id", "provenance.provider_id"),
            source_type=_string(payload.get("source_type", ""), "provenance.source_type"),
            source_label=_string(payload.get("source_label", ""), "provenance.source_label"),
            source_uri=_string(payload.get("source_uri", ""), "provenance.source_uri"),
            excerpt=_string(payload.get("excerpt", ""), "provenance.excerpt"),
            observed_at=_string(payload.get("observed_at", ""), "provenance.observed_at"),
            created_at=_string(payload.get("created_at", ""), "provenance.created_at"),
            updated_at=_string(payload.get("updated_at", ""), "provenance.updated_at"),
            confidence=_float_or_none(payload.get("confidence"), "provenance.confidence"),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "provenance.provider_payload",
            ),
        )


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
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosSnapshot:
        return cls(
            snapshot_id=_required_string(payload, "snapshot_id", "snapshot.snapshot_id"),
            label=_string(payload.get("label", ""), "snapshot.label"),
            created_at=_string(payload.get("created_at", ""), "snapshot.created_at"),
            source_label=_string(payload.get("source_label", ""), "snapshot.source_label"),
            source_uri=_string(payload.get("source_uri", ""), "snapshot.source_uri"),
            comparison_ids=_string_tuple(
                payload.get("comparison_ids", ()),
                "snapshot.comparison_ids",
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "snapshot.provider_payload",
            ),
        )


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
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosNode:
        return cls(
            id=_required_string(payload, "id", "node.id"),
            label=_required_string(payload, "label", "node.label"),
            kind=_required_string(payload, "kind", "node.kind"),
            summary=_string(payload.get("summary", ""), "node.summary"),
            tags=_string_tuple(payload.get("tags", ()), "node.tags"),
            score=_float_or_none(payload.get("score"), "node.score"),
            confidence=_float_or_none(payload.get("confidence"), "node.confidence"),
            source=_string(payload.get("source", ""), "node.source"),
            timestamps=_string_dict(payload.get("timestamps", {}), "node.timestamps"),
            provenance_ids=_string_tuple(
                payload.get("provenance_ids", ()),
                "node.provenance_ids",
            ),
            citation_ids=_string_tuple(
                payload.get("citation_ids", ()),
                "node.citation_ids",
            ),
            visual=GraphFakosVisual.from_dict(
                _mapping(payload.get("visual", {}), "node.visual"),
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "node.provider_payload",
            ),
        )


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
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosEdge:
        return cls(
            id=_required_string(payload, "id", "edge.id"),
            source_id=_required_string(payload, "source_id", "edge.source_id"),
            target_id=_required_string(payload, "target_id", "edge.target_id"),
            kind=_required_string(payload, "kind", "edge.kind"),
            label=_string(payload.get("label", ""), "edge.label"),
            weight=_float_or_none(payload.get("weight"), "edge.weight"),
            confidence=_float_or_none(payload.get("confidence"), "edge.confidence"),
            direction=_string(payload.get("direction", "directed"), "edge.direction"),
            provenance_ids=_string_tuple(
                payload.get("provenance_ids", ()),
                "edge.provenance_ids",
            ),
            citation_ids=_string_tuple(
                payload.get("citation_ids", ()),
                "edge.citation_ids",
            ),
            visual=GraphFakosVisual.from_dict(
                _mapping(payload.get("visual", {}), "edge.visual"),
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "edge.provider_payload",
            ),
        )


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
            "stats": _json_compatible_dict(self.stats),
            "generated_at": self.generated_at,
            "snapshot": self.snapshot.to_dict() if self.snapshot is not None else None,
            "provider_details": dict(self.provider_details),
            "capability_details": dict(self.capability_details),
            "available_facets": {
                key: list(values) for key, values in self.available_facets.items()
            },
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosGraph:
        snapshot_payload = payload.get("snapshot")
        return cls(
            graph_id=_required_string(payload, "graph_id", "graph.graph_id"),
            label=_required_string(payload, "label", "graph.label"),
            provider_id=_required_string(payload, "provider_id", "graph.provider_id"),
            provider_label=_required_string(
                payload,
                "provider_label",
                "graph.provider_label",
            ),
            graph_role=_required_string(payload, "graph_role", "graph.graph_role"),
            capabilities=_string_tuple(payload.get("capabilities", ()), "graph.capabilities"),
            nodes=tuple(
                GraphFakosNode.from_dict(item)
                for item in _mapping_list(payload.get("nodes", []), "graph.nodes")
            ),
            edges=tuple(
                GraphFakosEdge.from_dict(item)
                for item in _mapping_list(payload.get("edges", []), "graph.edges")
            ),
            provenance=tuple(
                GraphFakosProvenance.from_dict(item)
                for item in _mapping_list(
                    payload.get("provenance", []),
                    "graph.provenance",
                )
            ),
            citations=tuple(
                GraphFakosCitation.from_dict(item)
                for item in _mapping_list(payload.get("citations", []), "graph.citations")
            ),
            warnings=_string_tuple(payload.get("warnings", ()), "graph.warnings"),
            stats=_object_dict(payload.get("stats", {}), "graph.stats"),
            generated_at=_string(payload.get("generated_at", ""), "graph.generated_at"),
            snapshot=(
                None
                if snapshot_payload in (None, "")
                else GraphFakosSnapshot.from_dict(
                    _mapping(snapshot_payload, "graph.snapshot"),
                )
            ),
            provider_details=_string_dict(
                payload.get("provider_details", {}),
                "graph.provider_details",
            ),
            capability_details=_string_dict(
                payload.get("capability_details", {}),
                "graph.capability_details",
            ),
            available_facets=_string_tuple_dict(
                payload.get("available_facets", {}),
                "graph.available_facets",
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "graph.provider_payload",
            ),
        )


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
    self_loop_edge_ids: tuple[str, ...] = ()
    disconnected_node_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def healthy(self) -> bool:
        return not (
            self.orphan_node_ids
            or self.duplicate_edge_ids
            or self.unknown_provenance_ids
            or self.unknown_citation_ids
            or self.self_loop_edge_ids
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
            "self_loop_edge_ids": list(self.self_loop_edge_ids),
            "disconnected_node_ids": list(self.disconnected_node_ids),
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

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosRequest:
        return cls(
            screen=cast(
                GraphFakosScreen,
                _string(payload.get("screen", "explore"), "request.screen"),
            ),
            query=_string(payload.get("query", ""), "request.query"),
            focus_node_id=_string_or_none(payload.get("focus_node_id"), "request.focus_node_id"),
            selected_edge_id=_string_or_none(
                payload.get("selected_edge_id"),
                "request.selected_edge_id",
            ),
            source_node_id=_string_or_none(
                payload.get("source_node_id"),
                "request.source_node_id",
            ),
            target_node_id=_string_or_none(
                payload.get("target_node_id"),
                "request.target_node_id",
            ),
            comparison_graph_id=_string_or_none(
                payload.get("comparison_graph_id"),
                "request.comparison_graph_id",
            ),
            max_depth=_int(payload.get("max_depth", 1), "request.max_depth"),
            filters=_string_dict(payload.get("filters", {}), "request.filters"),
            layout=_string(payload.get("layout", "force"), "request.layout"),
            include_provenance=_bool(
                payload.get("include_provenance", True),
                "request.include_provenance",
            ),
            include_provider_payload=_bool(
                payload.get("include_provider_payload", True),
                "request.include_provider_payload",
            ),
            limit=_int(payload.get("limit", 25), "request.limit"),
            render_limit=_int(payload.get("render_limit", 120), "request.render_limit"),
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise TypeError(f"{field_name} must be a mapping")


def _mapping_list(value: object, field_name: str) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, list):
        return tuple(_mapping(item, field_name) for item in value)
    if isinstance(value, tuple):
        return tuple(_mapping(item, field_name) for item in value)
    raise TypeError(f"{field_name} must be a list of mappings")


def _required_string(
    payload: Mapping[str, object],
    key: str,
    field_name: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string(value: object, field_name: str) -> str:
    if isinstance(value, str):
        return value
    raise TypeError(f"{field_name} must be a string")


def _string_or_none(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _string(value, field_name)


def _bool(value: object, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise TypeError(f"{field_name} must be a bool")


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int")
    return value


def _int_or_none(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _int(value, field_name)


def _float_or_none(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    return float(value)


def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        items: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise TypeError(f"{field_name} must contain only strings")
            items.append(item)
        return tuple(items)
    raise TypeError(f"{field_name} must be a list of strings")


def _string_dict(value: object, field_name: str) -> dict[str, str]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, str] = {}
    for key, item in mapping.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise TypeError(f"{field_name} must map strings to strings")
        parsed[key] = item
    return parsed


def _string_tuple_dict(value: object, field_name: str) -> dict[str, tuple[str, ...]]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, tuple[str, ...]] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise TypeError(f"{field_name} must use string keys")
        parsed[key] = _string_tuple(item, f"{field_name}.{key}")
    return parsed


def _object_dict(value: object, field_name: str) -> dict[str, object]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, object] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise TypeError(f"{field_name} must use string keys")
        parsed[key] = item
    return parsed


def _json_compatible_dict(value: Mapping[str, object]) -> dict[str, object]:
    return {key: _json_compatible(item) for key, item in value.items()}


def _json_compatible(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _json_compatible(item)
            for key, item in cast(Mapping[object, object], value).items()
        }
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    return value


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
