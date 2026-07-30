"""Typed provider declarations consumed by the GraphFakos viewer."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from .models import (
    GraphFakosExpansionRequest,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosSavedView,
    GraphFakosViewerState,
)


def _text(payload: Mapping[str, object], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _strings(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key, ())
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        raise TypeError(f"{key} must be a list of strings")
    return tuple(value)


def _string_map(payload: Mapping[str, object], key: str) -> dict[str, str]:
    value = payload.get(key, {})
    if not isinstance(value, Mapping) or not all(
        isinstance(item_key, str) and isinstance(item_value, str)
        for item_key, item_value in value.items()
    ):
        raise TypeError(f"{key} must be an object with string values")
    return dict(value)


def _integer(payload: Mapping[str, object], key: str, default: int = 0) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


def _object_map(payload: Mapping[str, object], key: str) -> dict[str, object]:
    value = payload.get(key, {})
    if not isinstance(value, Mapping) or not all(
        isinstance(item_key, str) for item_key in value
    ):
        raise TypeError(f"{key} must be an object with string keys")
    return dict(value)


def _mapping_items(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    value = payload.get(key, ())
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, Mapping) for item in value
    ):
        raise TypeError(f"{key} must be a list of objects")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class GraphFakosPerspective:
    """Reusable provider-neutral viewer settings, not provider query semantics."""

    perspective_id: str
    label: str
    summary: str = ""
    layout: str = "grouped"
    render_engine: str = "3d"
    node_kinds: tuple[str, ...] = ()
    edge_kinds: tuple[str, ...] = ()
    filters: dict[str, str] = field(default_factory=dict)
    style_color_by: str = "kind"
    style_size_by: str = "degree"
    style_edge_width_by: str = "confidence"

    def to_dict(self) -> dict[str, object]:
        return {
            "perspective_id": self.perspective_id,
            "label": self.label,
            "summary": self.summary,
            "layout": self.layout,
            "render_engine": self.render_engine,
            "node_kinds": list(self.node_kinds),
            "edge_kinds": list(self.edge_kinds),
            "filters": dict(self.filters),
            "style_color_by": self.style_color_by,
            "style_size_by": self.style_size_by,
            "style_edge_width_by": self.style_edge_width_by,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosPerspective:
        perspective_id = _text(payload, "perspective_id")
        label = _text(payload, "label")
        if not perspective_id or not label:
            raise ValueError("perspective_id and label are required")
        return cls(
            perspective_id=perspective_id,
            label=label,
            summary=_text(payload, "summary"),
            layout=_text(payload, "layout", "grouped"),
            render_engine=_text(payload, "render_engine", "3d"),
            node_kinds=_strings(payload, "node_kinds"),
            edge_kinds=_strings(payload, "edge_kinds"),
            filters=_string_map(payload, "filters"),
            style_color_by=_text(payload, "style_color_by", "kind"),
            style_size_by=_text(payload, "style_size_by", "degree"),
            style_edge_width_by=_text(payload, "style_edge_width_by", "confidence"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosInspectorField:
    key: str
    label: str
    source: str = "node"
    value_format: str = "text"
    editable: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "label": self.label,
            "source": self.source,
            "value_format": self.value_format,
            "editable": self.editable,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosInspectorField:
        key = _text(payload, "key")
        label = _text(payload, "label")
        if not key or not label:
            raise ValueError("inspector field key and label are required")
        editable = payload.get("editable", False)
        if not isinstance(editable, bool):
            raise TypeError("editable must be a boolean")
        return cls(
            key=key,
            label=label,
            source=_text(payload, "source", "node"),
            value_format=_text(payload, "value_format", "text"),
            editable=editable,
        )


@dataclass(frozen=True, slots=True)
class GraphFakosInspectorSchema:
    schema_id: str
    node_kind: str
    fields: tuple[GraphFakosInspectorField, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "node_kind": self.node_kind,
            "fields": [field.to_dict() for field in self.fields],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosInspectorSchema:
        schema_id = _text(payload, "schema_id")
        node_kind = _text(payload, "node_kind")
        raw_fields = payload.get("fields", ())
        if not isinstance(raw_fields, (list, tuple)) or not all(
            isinstance(item, Mapping) for item in raw_fields
        ):
            raise TypeError("fields must be a list of objects")
        fields = tuple(GraphFakosInspectorField.from_dict(item) for item in raw_fields)
        if not schema_id or not node_kind or not fields:
            raise ValueError("schema_id, node_kind, and fields are required")
        return cls(schema_id=schema_id, node_kind=node_kind, fields=fields)


@dataclass(frozen=True, slots=True)
class GraphFakosProgressiveCluster:
    """Provider-neutral cluster summary used for progressive graph exploration."""

    cluster_id: str
    label: str
    node_count: int = 0
    edge_count: int = 0
    visible_node_ids: tuple[str, ...] = ()
    omitted_node_count: int = 0
    omitted_edge_count: int = 0
    expansion_cursor: str = ""
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "visible_node_ids": list(self.visible_node_ids),
            "omitted_node_count": self.omitted_node_count,
            "omitted_edge_count": self.omitted_edge_count,
            "expansion_cursor": self.expansion_cursor,
            "provider_payload": dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosProgressiveCluster:
        cluster_id = _text(payload, "cluster_id")
        label = _text(payload, "label")
        if not cluster_id or not label:
            raise ValueError("cluster_id and label are required")
        return cls(
            cluster_id=cluster_id,
            label=label,
            node_count=_integer(payload, "node_count"),
            edge_count=_integer(payload, "edge_count"),
            visible_node_ids=_strings(payload, "visible_node_ids"),
            omitted_node_count=_integer(payload, "omitted_node_count"),
            omitted_edge_count=_integer(payload, "omitted_edge_count"),
            expansion_cursor=_text(payload, "expansion_cursor"),
            provider_payload=_object_map(payload, "provider_payload"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosPerformanceBudget:
    """Honest visible/raw graph budget for browser and desktop wrappers."""

    rendered_node_count: int
    rendered_edge_count: int
    raw_node_count: int
    raw_edge_count: int
    omitted_node_count: int = 0
    omitted_edge_count: int = 0
    target_fps: int = 30
    max_first_interaction_ms: int = 3000
    level_of_detail: str = "visible"

    def to_dict(self) -> dict[str, object]:
        return {
            "rendered_node_count": self.rendered_node_count,
            "rendered_edge_count": self.rendered_edge_count,
            "raw_node_count": self.raw_node_count,
            "raw_edge_count": self.raw_edge_count,
            "omitted_node_count": self.omitted_node_count,
            "omitted_edge_count": self.omitted_edge_count,
            "target_fps": self.target_fps,
            "max_first_interaction_ms": self.max_first_interaction_ms,
            "level_of_detail": self.level_of_detail,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosPerformanceBudget:
        return cls(
            rendered_node_count=_integer(payload, "rendered_node_count"),
            rendered_edge_count=_integer(payload, "rendered_edge_count"),
            raw_node_count=_integer(payload, "raw_node_count"),
            raw_edge_count=_integer(payload, "raw_edge_count"),
            omitted_node_count=_integer(payload, "omitted_node_count"),
            omitted_edge_count=_integer(payload, "omitted_edge_count"),
            target_fps=_integer(payload, "target_fps", 30),
            max_first_interaction_ms=_integer(
                payload,
                "max_first_interaction_ms",
                3000,
            ),
            level_of_detail=_text(payload, "level_of_detail", "visible"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosWorkspaceManifest:
    """Portable viewer contract for exploration, edit drafts, and wrapper state."""

    graph_id: str
    provider_id: str
    viewer_state: GraphFakosViewerState
    clusters: tuple[GraphFakosProgressiveCluster, ...] = ()
    saved_view: GraphFakosSavedView | None = None
    default_expansion_requests: tuple[GraphFakosExpansionRequest, ...] = ()
    supported_actions: tuple[str, ...] = ()
    supported_captures: tuple[str, ...] = ()
    performance_budget: GraphFakosPerformanceBudget | None = None
    desktop_backend_path: str = "/explore"
    schema_version: str = "graphfakos.workspace.v1"
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "graph_id": self.graph_id,
            "provider_id": self.provider_id,
            "viewer_state": self.viewer_state.to_dict(),
            "clusters": [cluster.to_dict() for cluster in self.clusters],
            "saved_view": self.saved_view.to_dict() if self.saved_view else None,
            "default_expansion_requests": [
                request.to_dict() for request in self.default_expansion_requests
            ],
            "supported_actions": list(self.supported_actions),
            "supported_captures": list(self.supported_captures),
            "performance_budget": (
                self.performance_budget.to_dict()
                if self.performance_budget is not None
                else None
            ),
            "desktop_backend_path": self.desktop_backend_path,
            "provider_payload": dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosWorkspaceManifest:
        budget_payload = payload.get("performance_budget")
        saved_view_payload = payload.get("saved_view")
        return cls(
            schema_version=_text(
                payload,
                "schema_version",
                "graphfakos.workspace.v1",
            ),
            graph_id=_text(payload, "graph_id"),
            provider_id=_text(payload, "provider_id"),
            viewer_state=GraphFakosViewerState.from_dict(
                _object_map(payload, "viewer_state")
            ),
            clusters=tuple(
                GraphFakosProgressiveCluster.from_dict(item)
                for item in _mapping_items(payload, "clusters")
            ),
            saved_view=(
                None
                if saved_view_payload in (None, "")
                else GraphFakosSavedView.from_dict(_object_map(payload, "saved_view"))
            ),
            default_expansion_requests=tuple(
                GraphFakosExpansionRequest.from_dict(item)
                for item in _mapping_items(payload, "default_expansion_requests")
            ),
            supported_actions=_strings(payload, "supported_actions"),
            supported_captures=_strings(payload, "supported_captures"),
            performance_budget=(
                None
                if budget_payload in (None, "")
                else GraphFakosPerformanceBudget.from_dict(
                    _object_map(payload, "performance_budget")
                )
            ),
            desktop_backend_path=_text(payload, "desktop_backend_path", "/explore"),
            provider_payload=_object_map(payload, "provider_payload"),
        )


def _declarations(graph: GraphFakosGraph, key: str) -> tuple[Mapping[str, object], ...]:
    value = graph.provider_payload.get(key, ())
    if not value:
        envelope = graph.provider_payload.get("viewer_envelope", {})
        if isinstance(envelope, Mapping):
            value = envelope.get(key, ())
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def graph_perspectives(graph: GraphFakosGraph) -> tuple[GraphFakosPerspective, ...]:
    return tuple(
        GraphFakosPerspective.from_dict(item)
        for item in _declarations(graph, "perspectives")
    )


def inspector_schema_for(
    graph: GraphFakosGraph,
    node: GraphFakosNode,
) -> GraphFakosInspectorSchema | None:
    schemas = (
        GraphFakosInspectorSchema.from_dict(item)
        for item in _declarations(graph, "inspector_schemas")
    )
    return next((schema for schema in schemas if schema.node_kind == node.kind), None)


def inspector_values(
    node: GraphFakosNode,
    schema: GraphFakosInspectorSchema,
) -> dict[str, object]:
    node_values = node.to_dict()
    values: dict[str, object] = {}
    for inspector_field in schema.fields:
        source = (
            node.provider_payload
            if inspector_field.source == "provider_payload"
            else node_values
        )
        values[inspector_field.label] = source.get(inspector_field.key, "")
    return values


def workspace_manifest_for_graph(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> GraphFakosWorkspaceManifest:
    """Build the portable graph-workspace manifest from current DTOs."""

    return GraphFakosWorkspaceManifest(
        graph_id=graph.graph_id,
        provider_id=graph.provider_id,
        viewer_state=GraphFakosViewerState.from_request(request),
        clusters=_progressive_clusters_for_graph(graph),
        saved_view=GraphFakosSavedView.from_request(
            request,
            view_id=request.saved_view_id or "route",
            label="Current route view",
        ),
        default_expansion_requests=_default_expansion_requests(graph, request),
        supported_actions=_supported_graph_actions(graph),
        supported_captures=_supported_capture_kinds(graph),
        performance_budget=_performance_budget_for_graph(graph),
        desktop_backend_path=_desktop_backend_path(request),
        provider_payload={
            "provider_label": graph.provider_label,
            "graph_role": graph.graph_role,
        },
    )


def _progressive_clusters_for_graph(
    graph: GraphFakosGraph,
) -> tuple[GraphFakosProgressiveCluster, ...]:
    buckets: dict[str, list[GraphFakosNode]] = defaultdict(list)
    for node in graph.nodes:
        buckets[_cluster_id(node)].append(node)
    node_by_id = graph.node_map()
    edge_counts: dict[str, int] = defaultdict(int)
    for edge in graph.edges:
        for node_id in (edge.source_id, edge.target_id):
            node = node_by_id.get(node_id)
            if node is not None:
                edge_counts[_cluster_id(node)] += 1
    envelope_clusters = {
        cluster_id: item
        for item in _provider_cluster_payloads(graph.provider_payload)
        if (cluster_id := _payload_cluster_id(item))
    }
    clusters = []
    for cluster_id, nodes in sorted(buckets.items()):
        envelope = envelope_clusters.get(cluster_id, {})
        node_count = _count_from_payload(envelope, "node_count", len(nodes))
        edge_count = _count_from_payload(
            envelope, "edge_count", edge_counts[cluster_id]
        )
        clusters.append(
            GraphFakosProgressiveCluster(
                cluster_id=cluster_id,
                label=_cluster_label(cluster_id, nodes),
                node_count=node_count,
                edge_count=edge_count,
                visible_node_ids=tuple(node.id for node in nodes[:12]),
                omitted_node_count=max(0, node_count - len(nodes)),
                omitted_edge_count=max(0, edge_count - edge_counts[cluster_id]),
                expansion_cursor=_text(
                    envelope,
                    "expansion_cursor",
                    _text(envelope, "cursor"),
                ),
                provider_payload={
                    key: value
                    for key, value in envelope.items()
                    if key not in {"cluster_id", "id", "node_count", "edge_count"}
                },
            )
        )
    return tuple(clusters)


def _performance_budget_for_graph(
    graph: GraphFakosGraph,
) -> GraphFakosPerformanceBudget:
    raw_node_count = _stats_count(graph, "raw_node_count", len(graph.nodes))
    raw_edge_count = _stats_count(graph, "raw_edge_count", len(graph.edges))
    omitted_node_count = _stats_count(
        graph,
        "hidden_nodes",
        max(0, raw_node_count - len(graph.nodes)),
    )
    omitted_edge_count = _stats_count(
        graph,
        "hidden_edges",
        max(0, raw_edge_count - len(graph.edges)),
    )
    level = "aggregate" if raw_node_count > len(graph.nodes) else "visible"
    return GraphFakosPerformanceBudget(
        rendered_node_count=len(graph.nodes),
        rendered_edge_count=len(graph.edges),
        raw_node_count=raw_node_count,
        raw_edge_count=raw_edge_count,
        omitted_node_count=omitted_node_count,
        omitted_edge_count=omitted_edge_count,
        level_of_detail=level,
    )


def _default_expansion_requests(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> tuple[GraphFakosExpansionRequest, ...]:
    if request.focus_node_id:
        return (
            GraphFakosExpansionRequest(
                source_id=request.focus_node_id,
                depth=max(1, request.max_depth),
            ),
        )
    first_node = next((node for node in graph.nodes if node.id), None)
    return (
        ()
        if first_node is None
        else (GraphFakosExpansionRequest(source_id=first_node.id, depth=1),)
    )


def _supported_graph_actions(graph: GraphFakosGraph) -> tuple[str, ...]:
    if "graph_action" not in graph.capabilities:
        return ()
    return _declared_strings(
        graph.provider_payload,
        "supported_actions",
        ("draft_node", "draft_edge", "retag_group", "merge_alias"),
    )


def _supported_capture_kinds(graph: GraphFakosGraph) -> tuple[str, ...]:
    if "knowledge_capture" not in graph.capabilities:
        return ()
    return _declared_strings(
        graph.provider_payload,
        "supported_captures",
        ("note", "question", "observation", "task"),
    )


def _declared_strings(
    provider_payload: Mapping[str, object],
    key: str,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    value = provider_payload.get(key, ())
    if not value:
        envelope = provider_payload.get("viewer_envelope", {})
        if isinstance(envelope, Mapping):
            value = envelope.get(key, ())
    if not value:
        return fallback
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        return fallback
    return tuple(value)


def _cluster_id(node: GraphFakosNode) -> str:
    value = node.provider_payload.get("cluster_id") or node.visual.group or node.kind
    return str(value or "unclustered")


def _cluster_label(cluster_id: str, nodes: Iterable[GraphFakosNode]) -> str:
    preferred = next(
        (node.label for node in nodes if node.visual.emphasis == "hub"), ""
    )
    if preferred:
        return preferred
    return cluster_id.replace("-", " ").replace("_", " ").title()


def _provider_cluster_payloads(
    provider_payload: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    value = provider_payload.get("clusters", ())
    if not value:
        envelope = provider_payload.get("viewer_envelope", {})
        if isinstance(envelope, Mapping):
            value = envelope.get("clusters", ())
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _payload_cluster_id(payload: Mapping[str, object]) -> str:
    value = payload.get("cluster_id") or payload.get("id")
    return str(value) if value else ""


def _count_from_payload(
    payload: Mapping[str, object],
    key: str,
    default: int,
) -> int:
    value = payload.get(key, default)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _stats_count(graph: GraphFakosGraph, key: str, default: int) -> int:
    value = graph.stats.get(key, default)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _desktop_backend_path(request: GraphFakosRequest) -> str:
    return f"/{request.screen or 'explore'}"


__all__ = [
    "GraphFakosInspectorField",
    "GraphFakosInspectorSchema",
    "GraphFakosPerformanceBudget",
    "GraphFakosPerspective",
    "GraphFakosProgressiveCluster",
    "GraphFakosWorkspaceManifest",
    "graph_perspectives",
    "inspector_schema_for",
    "inspector_values",
    "workspace_manifest_for_graph",
]
