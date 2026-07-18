"""Provider-neutral graph viewer DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, cast

from ._model_values import (
    _bool,
    _float,
    _float_or_none,
    _int,
    _int_or_none,
    _json_compatible_dict,
    _mapping,
    _mapping_list,
    _object_dict,
    _position_dict,
    _required_string,
    _string,
    _string_dict,
    _string_or_none,
    _string_tuple,
    _string_tuple_dict,
    _tag_tuple,
)

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
class GraphFakosViewerState:
    screen: str = "explore"
    layout: str = "force"
    selected_node_id: str | None = None
    selected_node_ids: tuple[str, ...] = ()
    selected_edge_id: str | None = None
    camera_x: float = 0.0
    camera_y: float = 0.0
    camera_zoom: float = 1.0
    camera_yaw: float = 0.0
    camera_pitch: float = 0.0
    render_engine: str = "svg"
    theme: str = "default"
    scene_level: str = "overview"
    filters: dict[str, str] = field(default_factory=dict)
    expanded_groups: tuple[str, ...] = ()
    hidden_groups: tuple[str, ...] = ()
    saved_view_id: str = ""
    show_orphans: bool = True
    show_neighbor_links: bool = True
    edge_clutter: str = "normal"
    analytics_overlay: str = "degree"
    center_force: float = 0.012
    repel_force: float = 1.0
    link_distance: float = 1.0
    node_scale: float = 1.0
    edge_scale: float = 1.0
    edge_opacity: float = 1.0
    label_density: float = 1.0
    pinned_positions: dict[str, tuple[float, float]] = field(default_factory=dict)
    style_color_by: str = "kind"
    style_size_by: str = "score"
    style_edge_width_by: str = "kind"
    min_degree: int | None = None
    max_degree: int | None = None
    component_id: str = ""
    connected_to_node_id: str = ""
    evidence_filter: str = ""
    cluster_id: str = ""
    timeline_frame: str = ""
    timeline_playback: str = "stopped"
    pivot_node_id: str = ""
    pivot_mode: str = ""

    @classmethod
    def from_request(cls, request: GraphFakosRequest) -> GraphFakosViewerState:
        return cls(
            screen=request.screen,
            layout=request.layout,
            selected_node_id=request.focus_node_id,
            selected_node_ids=request.selected_node_ids,
            selected_edge_id=request.selected_edge_id,
            camera_x=request.camera_x if request.camera_x is not None else 0.0,
            camera_y=request.camera_y if request.camera_y is not None else 0.0,
            camera_zoom=request.camera_zoom if request.camera_zoom is not None else 1.0,
            camera_yaw=request.camera_yaw if request.camera_yaw is not None else 0.0,
            camera_pitch=(
                request.camera_pitch if request.camera_pitch is not None else 0.0
            ),
            render_engine=request.render_engine,
            theme=request.theme,
            scene_level="overview",
            filters=dict(request.filters),
            expanded_groups=request.expanded_groups,
            hidden_groups=request.hidden_groups,
            saved_view_id=request.saved_view_id,
            show_orphans=request.show_orphans,
            show_neighbor_links=request.show_neighbor_links,
            edge_clutter=request.edge_clutter,
            analytics_overlay=request.analytics_overlay,
            center_force=request.center_force,
            repel_force=request.repel_force,
            link_distance=request.link_distance,
            node_scale=request.node_scale,
            edge_scale=request.edge_scale,
            edge_opacity=request.edge_opacity,
            label_density=request.label_density,
            pinned_positions=dict(request.pinned_positions),
            style_color_by=request.style_color_by,
            style_size_by=request.style_size_by,
            style_edge_width_by=request.style_edge_width_by,
            min_degree=request.min_degree,
            max_degree=request.max_degree,
            component_id=request.component_id,
            connected_to_node_id=request.connected_to_node_id,
            evidence_filter=request.evidence_filter,
            cluster_id=request.cluster_id,
            timeline_frame=request.timeline_frame,
            timeline_playback=request.timeline_playback,
            pivot_node_id=request.pivot_node_id,
            pivot_mode=request.pivot_mode,
        )

    def to_route_query(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "screen": self.screen,
            "layout": self.layout,
            "camera_x": self.camera_x,
            "camera_y": self.camera_y,
            "camera_zoom": self.camera_zoom,
            "camera_yaw": self.camera_yaw,
            "camera_pitch": self.camera_pitch,
            "render_engine": self.render_engine,
            "theme": self.theme,
            "scene_level": self.scene_level,
            "show_orphans": self.show_orphans,
            "show_neighbor_links": self.show_neighbor_links,
            "edge_clutter": self.edge_clutter,
            "analytics_overlay": self.analytics_overlay,
            "center_force": self.center_force,
            "repel_force": self.repel_force,
            "link_distance": self.link_distance,
            "node_scale": self.node_scale,
            "edge_scale": self.edge_scale,
            "edge_opacity": self.edge_opacity,
            "label_density": self.label_density,
            "style_color_by": self.style_color_by,
            "style_size_by": self.style_size_by,
            "style_edge_width_by": self.style_edge_width_by,
            "min_degree": self.min_degree,
            "max_degree": self.max_degree,
            "component_id": self.component_id,
            "connected_to_node_id": self.connected_to_node_id,
            "evidence_filter": self.evidence_filter,
            "cluster_id": self.cluster_id,
            "timeline_frame": self.timeline_frame,
            "timeline_playback": self.timeline_playback,
            "pivot_node_id": self.pivot_node_id,
            "pivot_mode": self.pivot_mode,
        }
        if self.selected_node_id:
            payload["focus_node_id"] = self.selected_node_id
        if self.selected_node_ids:
            payload["selected_node_ids"] = ",".join(self.selected_node_ids)
        if self.selected_edge_id:
            payload["selected_edge_id"] = self.selected_edge_id
        if self.saved_view_id:
            payload["saved_view_id"] = self.saved_view_id
        payload.update(self.filters)
        if self.expanded_groups:
            payload["expanded_groups"] = ",".join(self.expanded_groups)
        if self.hidden_groups:
            payload["hidden_groups"] = ",".join(self.hidden_groups)
        return payload

    def to_dict(self) -> dict[str, object]:
        return {
            "screen": self.screen,
            "layout": self.layout,
            "selected_node_id": self.selected_node_id,
            "selected_node_ids": list(self.selected_node_ids),
            "selected_edge_id": self.selected_edge_id,
            "camera_x": self.camera_x,
            "camera_y": self.camera_y,
            "camera_zoom": self.camera_zoom,
            "camera_yaw": self.camera_yaw,
            "camera_pitch": self.camera_pitch,
            "render_engine": self.render_engine,
            "theme": self.theme,
            "scene_level": self.scene_level,
            "filters": dict(self.filters),
            "expanded_groups": list(self.expanded_groups),
            "hidden_groups": list(self.hidden_groups),
            "saved_view_id": self.saved_view_id,
            "show_orphans": self.show_orphans,
            "show_neighbor_links": self.show_neighbor_links,
            "edge_clutter": self.edge_clutter,
            "analytics_overlay": self.analytics_overlay,
            "center_force": self.center_force,
            "repel_force": self.repel_force,
            "link_distance": self.link_distance,
            "node_scale": self.node_scale,
            "edge_scale": self.edge_scale,
            "edge_opacity": self.edge_opacity,
            "label_density": self.label_density,
            "pinned_positions": {
                node_id: [x, y]
                for node_id, (x, y) in sorted(self.pinned_positions.items())
            },
            "style_color_by": self.style_color_by,
            "style_size_by": self.style_size_by,
            "style_edge_width_by": self.style_edge_width_by,
            "min_degree": self.min_degree,
            "max_degree": self.max_degree,
            "component_id": self.component_id,
            "connected_to_node_id": self.connected_to_node_id,
            "evidence_filter": self.evidence_filter,
            "cluster_id": self.cluster_id,
            "timeline_frame": self.timeline_frame,
            "timeline_playback": self.timeline_playback,
            "pivot_node_id": self.pivot_node_id,
            "pivot_mode": self.pivot_mode,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosViewerState:
        return cls(
            screen=_string(payload.get("screen", "explore"), "viewer_state.screen"),
            layout=_string(payload.get("layout", "force"), "viewer_state.layout"),
            selected_node_id=_string_or_none(
                payload.get("selected_node_id"), "viewer_state.selected_node_id"
            ),
            selected_node_ids=_tag_tuple(
                payload.get("selected_node_ids", ()),
                "viewer_state.selected_node_ids",
            ),
            selected_edge_id=_string_or_none(
                payload.get("selected_edge_id"), "viewer_state.selected_edge_id"
            ),
            camera_x=_float(payload.get("camera_x", 0.0), "viewer_state.camera_x"),
            camera_y=_float(payload.get("camera_y", 0.0), "viewer_state.camera_y"),
            camera_zoom=_float(
                payload.get("camera_zoom", 1.0), "viewer_state.camera_zoom"
            ),
            camera_yaw=_float(
                payload.get("camera_yaw", 0.0), "viewer_state.camera_yaw"
            ),
            camera_pitch=_float(
                payload.get("camera_pitch", 0.0), "viewer_state.camera_pitch"
            ),
            render_engine=_string(
                payload.get("render_engine", "svg"), "viewer_state.render_engine"
            ),
            theme=_string(payload.get("theme", "default"), "viewer_state.theme"),
            scene_level=_string(
                payload.get("scene_level", "overview"), "viewer_state.scene_level"
            ),
            filters=_string_dict(payload.get("filters", {}), "viewer_state.filters"),
            expanded_groups=_string_tuple(
                payload.get("expanded_groups", ()),
                "viewer_state.expanded_groups",
            ),
            hidden_groups=_string_tuple(
                payload.get("hidden_groups", ()),
                "viewer_state.hidden_groups",
            ),
            saved_view_id=_string(
                payload.get("saved_view_id", ""), "viewer_state.saved_view_id"
            ),
            show_orphans=_bool(
                payload.get("show_orphans", True), "viewer_state.show_orphans"
            ),
            show_neighbor_links=_bool(
                payload.get("show_neighbor_links", True),
                "viewer_state.show_neighbor_links",
            ),
            edge_clutter=_string(
                payload.get("edge_clutter", "normal"), "viewer_state.edge_clutter"
            ),
            analytics_overlay=_string(
                payload.get("analytics_overlay", "degree"),
                "viewer_state.analytics_overlay",
            ),
            center_force=_float(
                payload.get("center_force", 0.012), "viewer_state.center_force"
            ),
            repel_force=_float(
                payload.get("repel_force", 1.0), "viewer_state.repel_force"
            ),
            link_distance=_float(
                payload.get("link_distance", 1.0), "viewer_state.link_distance"
            ),
            node_scale=_float(
                payload.get("node_scale", 1.0), "viewer_state.node_scale"
            ),
            edge_scale=_float(
                payload.get("edge_scale", 1.0), "viewer_state.edge_scale"
            ),
            edge_opacity=_float(
                payload.get("edge_opacity", 1.0), "viewer_state.edge_opacity"
            ),
            label_density=_float(
                payload.get("label_density", 1.0), "viewer_state.label_density"
            ),
            pinned_positions=_position_dict(
                payload.get("pinned_positions", {}),
                "viewer_state.pinned_positions",
            ),
            style_color_by=_string(
                payload.get("style_color_by", "kind"), "viewer_state.style_color_by"
            ),
            style_size_by=_string(
                payload.get("style_size_by", "score"), "viewer_state.style_size_by"
            ),
            style_edge_width_by=_string(
                payload.get("style_edge_width_by", "kind"),
                "viewer_state.style_edge_width_by",
            ),
            min_degree=_int_or_none(
                payload.get("min_degree"), "viewer_state.min_degree"
            ),
            max_degree=_int_or_none(
                payload.get("max_degree"), "viewer_state.max_degree"
            ),
            component_id=_string(
                payload.get("component_id", ""), "viewer_state.component_id"
            ),
            connected_to_node_id=_string(
                payload.get("connected_to_node_id", ""),
                "viewer_state.connected_to_node_id",
            ),
            evidence_filter=_string(
                payload.get("evidence_filter", ""), "viewer_state.evidence_filter"
            ),
            cluster_id=_string(
                payload.get("cluster_id", ""), "viewer_state.cluster_id"
            ),
            timeline_frame=_string(
                payload.get("timeline_frame", ""), "viewer_state.timeline_frame"
            ),
            timeline_playback=_string(
                payload.get("timeline_playback", "stopped"),
                "viewer_state.timeline_playback",
            ),
            pivot_node_id=_string(
                payload.get("pivot_node_id", ""), "viewer_state.pivot_node_id"
            ),
            pivot_mode=_string(
                payload.get("pivot_mode", ""), "viewer_state.pivot_mode"
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosViewerCommand:
    name: str
    target_id: str = ""
    value: str = ""
    payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "target_id": self.target_id,
            "value": self.value,
            "payload": _json_compatible_dict(self.payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosViewerCommand:
        return cls(
            name=_required_string(payload, "name", "viewer_command.name"),
            target_id=_string(payload.get("target_id", ""), "viewer_command.target_id"),
            value=_string(payload.get("value", ""), "viewer_command.value"),
            payload=_object_dict(payload.get("payload", {}), "viewer_command.payload"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosViewerEvent:
    name: str
    state: GraphFakosViewerState
    target_id: str = ""
    payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "target_id": self.target_id,
            "state": self.state.to_dict(),
            "payload": _json_compatible_dict(self.payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosViewerEvent:
        return cls(
            name=_required_string(payload, "name", "viewer_event.name"),
            target_id=_string(payload.get("target_id", ""), "viewer_event.target_id"),
            state=GraphFakosViewerState.from_dict(
                _mapping(payload.get("state", {}), "viewer_event.state")
            ),
            payload=_object_dict(payload.get("payload", {}), "viewer_event.payload"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosExpansionRequest:
    source_id: str
    depth: int = 1
    edge_kind: str = ""
    node_kind: str = ""
    cursor: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = {
            "source_id": self.source_id,
            "depth": self.depth,
            "edge_kind": self.edge_kind,
            "node_kind": self.node_kind,
        }
        if self.cursor:
            payload["cursor"] = self.cursor
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosExpansionRequest:
        return cls(
            source_id=_required_string(
                payload, "source_id", "expansion_request.source_id"
            ),
            depth=_int(payload.get("depth", 1), "expansion_request.depth"),
            edge_kind=_string(
                payload.get("edge_kind", ""), "expansion_request.edge_kind"
            ),
            node_kind=_string(
                payload.get("node_kind", ""), "expansion_request.node_kind"
            ),
            cursor=_string(payload.get("cursor", ""), "expansion_request.cursor"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosKnowledgeCapture:
    text: str
    kind: str = "note"
    tags: tuple[str, ...] = ()
    source: str = "workbench"
    link_node_id: str = ""
    link_edge_kind: str = "mentions"
    created_at: str = ""
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "kind": self.kind,
            "tags": list(self.tags),
            "source": self.source,
            "link_node_id": self.link_node_id,
            "link_edge_kind": self.link_edge_kind,
            "created_at": self.created_at,
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosKnowledgeCapture:
        return cls(
            text=_required_string(payload, "text", "knowledge_capture.text"),
            kind=_string(payload.get("kind", "note"), "knowledge_capture.kind"),
            tags=_tag_tuple(payload.get("tags", ()), "knowledge_capture.tags"),
            source=_string(
                payload.get("source", "workbench"), "knowledge_capture.source"
            ),
            link_node_id=_string(
                payload.get("link_node_id", ""),
                "knowledge_capture.link_node_id",
            ),
            link_edge_kind=_string(
                payload.get("link_edge_kind", "mentions"),
                "knowledge_capture.link_edge_kind",
            ),
            created_at=_string(
                payload.get("created_at", ""),
                "knowledge_capture.created_at",
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "knowledge_capture.provider_payload",
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosSavedQuery:
    query_id: str
    label: str
    query: str = ""
    filters: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "label": self.label,
            "query": self.query,
            "filters": dict(self.filters),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosSavedQuery:
        return cls(
            query_id=_required_string(payload, "query_id", "saved_query.query_id"),
            label=_required_string(payload, "label", "saved_query.label"),
            query=_string(payload.get("query", ""), "saved_query.query"),
            filters=_string_dict(payload.get("filters", {}), "saved_query.filters"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosSavedView:
    view_id: str
    label: str
    state: GraphFakosViewerState
    pinned_positions: dict[str, tuple[float, float]] = field(default_factory=dict)
    saved_queries: tuple[GraphFakosSavedQuery, ...] = ()
    provider_payload: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_request(
        cls,
        request: GraphFakosRequest,
        *,
        view_id: str = "route",
        label: str = "Route View",
        pinned_positions: dict[str, tuple[float, float]] | None = None,
        saved_queries: tuple[GraphFakosSavedQuery, ...] = (),
        provider_payload: dict[str, object] | None = None,
    ) -> GraphFakosSavedView:
        return cls(
            view_id=view_id,
            label=label,
            state=GraphFakosViewerState.from_request(request),
            pinned_positions=pinned_positions
            if pinned_positions is not None
            else dict(request.pinned_positions),
            saved_queries=saved_queries,
            provider_payload=provider_payload or {},
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "view_id": self.view_id,
            "label": self.label,
            "state": self.state.to_dict(),
            "pinned_positions": {
                node_id: [x, y]
                for node_id, (x, y) in sorted(self.pinned_positions.items())
            },
            "saved_queries": [query.to_dict() for query in self.saved_queries],
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosSavedView:
        return cls(
            view_id=_required_string(payload, "view_id", "saved_view.view_id"),
            label=_required_string(payload, "label", "saved_view.label"),
            state=GraphFakosViewerState.from_dict(
                _mapping(payload.get("state", {}), "saved_view.state")
            ),
            pinned_positions=_position_dict(
                payload.get("pinned_positions", {}),
                "saved_view.pinned_positions",
            ),
            saved_queries=tuple(
                GraphFakosSavedQuery.from_dict(item)
                for item in _mapping_list(
                    payload.get("saved_queries", []),
                    "saved_view.saved_queries",
                )
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "saved_view.provider_payload",
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosGraphAction:
    action_id: str
    action_type: str
    label: str = ""
    target_id: str = ""
    body: str = ""
    tags: tuple[str, ...] = ()
    source_id: str = ""
    target_node_id: str = ""
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "label": self.label,
            "target_id": self.target_id,
            "body": self.body,
            "tags": list(self.tags),
            "source_id": self.source_id,
            "target_node_id": self.target_node_id,
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosGraphAction:
        return cls(
            action_id=_required_string(payload, "action_id", "graph_action.action_id"),
            action_type=_required_string(
                payload,
                "action_type",
                "graph_action.action_type",
            ),
            label=_string(payload.get("label", ""), "graph_action.label"),
            target_id=_string(payload.get("target_id", ""), "graph_action.target_id"),
            body=_string(payload.get("body", ""), "graph_action.body"),
            tags=_tag_tuple(payload.get("tags", ()), "graph_action.tags"),
            source_id=_string(payload.get("source_id", ""), "graph_action.source_id"),
            target_node_id=_string(
                payload.get("target_node_id", ""),
                "graph_action.target_node_id",
            ),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "graph_action.provider_payload",
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosActionStatus:
    action_id: str
    status: str
    message: str = ""
    graph_id: str = ""
    provider_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "status": self.status,
            "message": self.message,
            "graph_id": self.graph_id,
            "provider_payload": _json_compatible_dict(self.provider_payload),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosActionStatus:
        return cls(
            action_id=_required_string(
                payload,
                "action_id",
                "action_status.action_id",
            ),
            status=_required_string(payload, "status", "action_status.status"),
            message=_string(payload.get("message", ""), "action_status.message"),
            graph_id=_string(payload.get("graph_id", ""), "action_status.graph_id"),
            provider_payload=_object_dict(
                payload.get("provider_payload", {}),
                "action_status.provider_payload",
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosGraphAnalytics:
    component_count: int
    node_count: int = 0
    edge_count: int = 0
    hub_node_ids: tuple[str, ...] = ()
    orphan_node_ids: tuple[str, ...] = ()
    max_degree: int = 0
    average_degree: float = 0.0
    density: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "component_count": self.component_count,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "hub_node_ids": list(self.hub_node_ids),
            "orphan_node_ids": list(self.orphan_node_ids),
            "max_degree": self.max_degree,
            "average_degree": self.average_degree,
            "density": self.density,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosGraphAnalytics:
        return cls(
            component_count=_int(
                payload.get("component_count", 0),
                "graph_analytics.component_count",
            ),
            node_count=_int(payload.get("node_count", 0), "graph_analytics.node_count"),
            edge_count=_int(payload.get("edge_count", 0), "graph_analytics.edge_count"),
            hub_node_ids=_string_tuple(
                payload.get("hub_node_ids", ()),
                "graph_analytics.hub_node_ids",
            ),
            orphan_node_ids=_string_tuple(
                payload.get("orphan_node_ids", ()),
                "graph_analytics.orphan_node_ids",
            ),
            max_degree=_int(payload.get("max_degree", 0), "graph_analytics.max_degree"),
            average_degree=_float(
                payload.get("average_degree", 0.0),
                "graph_analytics.average_degree",
            ),
            density=_float(payload.get("density", 0.0), "graph_analytics.density"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosReplayBundle:
    bundle_id: str
    graph: GraphFakosGraph
    viewer_state: GraphFakosViewerState
    schema_version: str = "graphfakos.replay.v1"
    created_at: str = ""
    saved_views: tuple[GraphFakosSavedView, ...] = ()
    analytics: GraphFakosGraphAnalytics | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "bundle_id": self.bundle_id,
            "created_at": self.created_at,
            "graph": self.graph.to_dict(),
            "viewer_state": self.viewer_state.to_dict(),
            "saved_views": [view.to_dict() for view in self.saved_views],
            "analytics": self.analytics.to_dict()
            if self.analytics is not None
            else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosReplayBundle:
        analytics_payload = payload.get("analytics")
        return cls(
            bundle_id=_required_string(payload, "bundle_id", "replay_bundle.bundle_id"),
            schema_version=_string(
                payload.get("schema_version", "graphfakos.replay.v1"),
                "replay_bundle.schema_version",
            ),
            created_at=_string(
                payload.get("created_at", ""), "replay_bundle.created_at"
            ),
            graph=GraphFakosGraph.from_dict(
                _mapping(payload.get("graph", {}), "replay_bundle.graph")
            ),
            viewer_state=GraphFakosViewerState.from_dict(
                _mapping(payload.get("viewer_state", {}), "replay_bundle.viewer_state")
            ),
            saved_views=tuple(
                GraphFakosSavedView.from_dict(item)
                for item in _mapping_list(
                    payload.get("saved_views", []),
                    "replay_bundle.saved_views",
                )
            ),
            analytics=None
            if analytics_payload in (None, "")
            else GraphFakosGraphAnalytics.from_dict(
                _mapping(analytics_payload, "replay_bundle.analytics")
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosTheme:
    id: str = "default"
    label: str = "Default"
    node_colors: dict[str, str] = field(default_factory=dict)
    edge_colors: dict[str, str] = field(default_factory=dict)
    node_shapes: dict[str, str] = field(default_factory=dict)

    def caption(self) -> tuple[str, ...]:
        rows: list[str] = []
        for kind, color in sorted(self.node_colors.items()):
            rows.append(f"node color {kind}: {color}")
        for kind, shape in sorted(self.node_shapes.items()):
            rows.append(f"node shape {kind}: {shape}")
        for kind, color in sorted(self.edge_colors.items()):
            rows.append(f"edge color {kind}: {color}")
        return tuple(rows)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "node_colors": dict(self.node_colors),
            "edge_colors": dict(self.edge_colors),
            "node_shapes": dict(self.node_shapes),
            "caption": list(self.caption()),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosTheme:
        return cls(
            id=_required_string(payload, "id", "theme.id"),
            label=_string(payload.get("label", ""), "theme.label"),
            node_colors=_string_dict(
                payload.get("node_colors", {}), "theme.node_colors"
            ),
            edge_colors=_string_dict(
                payload.get("edge_colors", {}), "theme.edge_colors"
            ),
            node_shapes=_string_dict(
                payload.get("node_shapes", {}), "theme.node_shapes"
            ),
        )


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
            provider_id=_required_string(
                payload, "provider_id", "provenance.provider_id"
            ),
            source_type=_string(
                payload.get("source_type", ""), "provenance.source_type"
            ),
            source_label=_string(
                payload.get("source_label", ""), "provenance.source_label"
            ),
            source_uri=_string(payload.get("source_uri", ""), "provenance.source_uri"),
            excerpt=_string(payload.get("excerpt", ""), "provenance.excerpt"),
            observed_at=_string(
                payload.get("observed_at", ""), "provenance.observed_at"
            ),
            created_at=_string(payload.get("created_at", ""), "provenance.created_at"),
            updated_at=_string(payload.get("updated_at", ""), "provenance.updated_at"),
            confidence=_float_or_none(
                payload.get("confidence"), "provenance.confidence"
            ),
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
            snapshot_id=_required_string(
                payload, "snapshot_id", "snapshot.snapshot_id"
            ),
            label=_string(payload.get("label", ""), "snapshot.label"),
            created_at=_string(payload.get("created_at", ""), "snapshot.created_at"),
            source_label=_string(
                payload.get("source_label", ""), "snapshot.source_label"
            ),
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
            capabilities=_string_tuple(
                payload.get("capabilities", ()), "graph.capabilities"
            ),
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
                for item in _mapping_list(
                    payload.get("citations", []), "graph.citations"
                )
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
    preset_id: str = ""
    query: str = ""
    focus_node_id: str | None = None
    selected_node_ids: tuple[str, ...] = ()
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
    camera_x: float | None = None
    camera_y: float | None = None
    camera_zoom: float | None = None
    camera_yaw: float | None = None
    camera_pitch: float | None = None
    render_engine: str = "svg"
    theme: str = "default"
    expanded_groups: tuple[str, ...] = ()
    hidden_groups: tuple[str, ...] = ()
    saved_view_id: str = ""
    show_orphans: bool = True
    show_neighbor_links: bool = True
    edge_clutter: str = "normal"
    analytics_overlay: str = "degree"
    center_force: float = 0.012
    repel_force: float = 1.0
    link_distance: float = 1.0
    node_scale: float = 1.0
    edge_scale: float = 1.0
    edge_opacity: float = 1.0
    label_density: float = 1.0
    pinned_positions: dict[str, tuple[float, float]] = field(default_factory=dict)
    style_color_by: str = "kind"
    style_size_by: str = "score"
    style_edge_width_by: str = "kind"
    min_degree: int | None = None
    max_degree: int | None = None
    component_id: str = ""
    connected_to_node_id: str = ""
    evidence_filter: str = ""
    cluster_id: str = ""
    timeline_frame: str = ""
    timeline_playback: str = "stopped"
    pivot_node_id: str = ""
    pivot_mode: str = ""

    def with_screen(self, screen: GraphFakosScreen) -> GraphFakosRequest:
        return GraphFakosRequest(
            screen=screen,
            preset_id=self.preset_id,
            query=self.query,
            focus_node_id=self.focus_node_id,
            selected_node_ids=self.selected_node_ids,
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
            camera_x=self.camera_x,
            camera_y=self.camera_y,
            camera_zoom=self.camera_zoom,
            camera_yaw=self.camera_yaw,
            camera_pitch=self.camera_pitch,
            render_engine=self.render_engine,
            theme=self.theme,
            expanded_groups=self.expanded_groups,
            hidden_groups=self.hidden_groups,
            saved_view_id=self.saved_view_id,
            show_orphans=self.show_orphans,
            show_neighbor_links=self.show_neighbor_links,
            edge_clutter=self.edge_clutter,
            analytics_overlay=self.analytics_overlay,
            center_force=self.center_force,
            repel_force=self.repel_force,
            link_distance=self.link_distance,
            node_scale=self.node_scale,
            edge_scale=self.edge_scale,
            edge_opacity=self.edge_opacity,
            label_density=self.label_density,
            pinned_positions=dict(self.pinned_positions),
            style_color_by=self.style_color_by,
            style_size_by=self.style_size_by,
            style_edge_width_by=self.style_edge_width_by,
            min_degree=self.min_degree,
            max_degree=self.max_degree,
            component_id=self.component_id,
            connected_to_node_id=self.connected_to_node_id,
            evidence_filter=self.evidence_filter,
            cluster_id=self.cluster_id,
            timeline_frame=self.timeline_frame,
            timeline_playback=self.timeline_playback,
            pivot_node_id=self.pivot_node_id,
            pivot_mode=self.pivot_mode,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "screen": self.screen,
            "preset_id": self.preset_id,
            "query": self.query,
            "focus_node_id": self.focus_node_id,
            "selected_node_ids": list(self.selected_node_ids),
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
            "camera_x": self.camera_x,
            "camera_y": self.camera_y,
            "camera_zoom": self.camera_zoom,
            "camera_yaw": self.camera_yaw,
            "camera_pitch": self.camera_pitch,
            "render_engine": self.render_engine,
            "theme": self.theme,
            "expanded_groups": list(self.expanded_groups),
            "hidden_groups": list(self.hidden_groups),
            "saved_view_id": self.saved_view_id,
            "show_orphans": self.show_orphans,
            "show_neighbor_links": self.show_neighbor_links,
            "edge_clutter": self.edge_clutter,
            "analytics_overlay": self.analytics_overlay,
            "center_force": self.center_force,
            "repel_force": self.repel_force,
            "link_distance": self.link_distance,
            "node_scale": self.node_scale,
            "edge_scale": self.edge_scale,
            "edge_opacity": self.edge_opacity,
            "label_density": self.label_density,
            "pinned_positions": {
                node_id: [x, y]
                for node_id, (x, y) in sorted(self.pinned_positions.items())
            },
            "style_color_by": self.style_color_by,
            "style_size_by": self.style_size_by,
            "style_edge_width_by": self.style_edge_width_by,
            "min_degree": self.min_degree,
            "max_degree": self.max_degree,
            "component_id": self.component_id,
            "connected_to_node_id": self.connected_to_node_id,
            "evidence_filter": self.evidence_filter,
            "cluster_id": self.cluster_id,
            "timeline_frame": self.timeline_frame,
            "timeline_playback": self.timeline_playback,
            "pivot_node_id": self.pivot_node_id,
            "pivot_mode": self.pivot_mode,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosRequest:
        return cls(
            screen=cast(
                GraphFakosScreen,
                _string(payload.get("screen", "explore"), "request.screen"),
            ),
            preset_id=_string(payload.get("preset_id", ""), "request.preset_id"),
            query=_string(payload.get("query", ""), "request.query"),
            focus_node_id=_string_or_none(
                payload.get("focus_node_id"), "request.focus_node_id"
            ),
            selected_node_ids=_tag_tuple(
                payload.get("selected_node_ids", ()), "request.selected_node_ids"
            ),
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
            camera_x=_float_or_none(payload.get("camera_x"), "request.camera_x"),
            camera_y=_float_or_none(payload.get("camera_y"), "request.camera_y"),
            camera_zoom=_float_or_none(
                payload.get("camera_zoom"), "request.camera_zoom"
            ),
            camera_yaw=_float_or_none(payload.get("camera_yaw"), "request.camera_yaw"),
            camera_pitch=_float_or_none(
                payload.get("camera_pitch"), "request.camera_pitch"
            ),
            render_engine=_string(
                payload.get("render_engine", "svg"), "request.render_engine"
            ),
            theme=_string(payload.get("theme", "default"), "request.theme"),
            expanded_groups=_string_tuple(
                payload.get("expanded_groups", ()),
                "request.expanded_groups",
            ),
            hidden_groups=_string_tuple(
                payload.get("hidden_groups", ()),
                "request.hidden_groups",
            ),
            saved_view_id=_string(
                payload.get("saved_view_id", ""),
                "request.saved_view_id",
            ),
            show_orphans=_bool(
                payload.get("show_orphans", True),
                "request.show_orphans",
            ),
            show_neighbor_links=_bool(
                payload.get("show_neighbor_links", True),
                "request.show_neighbor_links",
            ),
            edge_clutter=_string(
                payload.get("edge_clutter", "normal"),
                "request.edge_clutter",
            ),
            analytics_overlay=_string(
                payload.get("analytics_overlay", "degree"),
                "request.analytics_overlay",
            ),
            center_force=_float(
                payload.get("center_force", 0.012), "request.center_force"
            ),
            repel_force=_float(payload.get("repel_force", 1.0), "request.repel_force"),
            link_distance=_float(
                payload.get("link_distance", 1.0), "request.link_distance"
            ),
            node_scale=_float(payload.get("node_scale", 1.0), "request.node_scale"),
            edge_scale=_float(payload.get("edge_scale", 1.0), "request.edge_scale"),
            edge_opacity=_float(
                payload.get("edge_opacity", 1.0), "request.edge_opacity"
            ),
            label_density=_float(
                payload.get("label_density", 1.0), "request.label_density"
            ),
            pinned_positions=_position_dict(
                payload.get("pinned_positions", {}), "request.pinned_positions"
            ),
            style_color_by=_string(
                payload.get("style_color_by", "kind"), "request.style_color_by"
            ),
            style_size_by=_string(
                payload.get("style_size_by", "score"), "request.style_size_by"
            ),
            style_edge_width_by=_string(
                payload.get("style_edge_width_by", "kind"),
                "request.style_edge_width_by",
            ),
            min_degree=_int_or_none(payload.get("min_degree"), "request.min_degree"),
            max_degree=_int_or_none(payload.get("max_degree"), "request.max_degree"),
            component_id=_string(
                payload.get("component_id", ""), "request.component_id"
            ),
            connected_to_node_id=_string(
                payload.get("connected_to_node_id", ""),
                "request.connected_to_node_id",
            ),
            evidence_filter=_string(
                payload.get("evidence_filter", ""), "request.evidence_filter"
            ),
            cluster_id=_string(payload.get("cluster_id", ""), "request.cluster_id"),
            timeline_frame=_string(
                payload.get("timeline_frame", ""), "request.timeline_frame"
            ),
            timeline_playback=_string(
                payload.get("timeline_playback", "stopped"),
                "request.timeline_playback",
            ),
            pivot_node_id=_string(
                payload.get("pivot_node_id", ""), "request.pivot_node_id"
            ),
            pivot_mode=_string(payload.get("pivot_mode", ""), "request.pivot_mode"),
        )


__all__ = [
    "GraphFakosCitation",
    "GraphFakosActionStatus",
    "GraphFakosDiagnostics",
    "GraphFakosEdge",
    "GraphFakosExpansionRequest",
    "GraphFakosGraph",
    "GraphFakosGraphAction",
    "GraphFakosGraphAnalytics",
    "GraphFakosKnowledgeCapture",
    "GraphFakosNode",
    "GraphFakosProvenance",
    "GraphFakosRequest",
    "GraphFakosReplayBundle",
    "GraphFakosSavedQuery",
    "GraphFakosSavedView",
    "GraphFakosScreen",
    "GraphFakosSnapshot",
    "GraphFakosTheme",
    "GraphFakosViewerCommand",
    "GraphFakosViewerEvent",
    "GraphFakosViewerState",
    "GraphFakosVisual",
]
