"""Typed provider declarations consumed by the GraphFakos viewer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .models import GraphFakosGraph, GraphFakosNode


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


__all__ = [
    "GraphFakosInspectorField",
    "GraphFakosInspectorSchema",
    "GraphFakosPerspective",
    "graph_perspectives",
    "inspector_schema_for",
    "inspector_values",
]
