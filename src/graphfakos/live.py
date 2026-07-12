"""Provider-neutral live graph contracts and deterministic patch application."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import json
from threading import Lock
from typing import Literal, Protocol, cast, runtime_checkable

from .models import GraphFakosEdge, GraphFakosGraph, GraphFakosNode

GraphFakosPatchOperationKind = Literal[
    "node_upsert",
    "node_delete",
    "edge_upsert",
    "edge_delete",
    "graph_metadata_merge",
    "graph_metadata_replace",
    "snapshot_reset",
]
GraphFakosLiveStatusKind = Literal[
    "connecting",
    "live",
    "heartbeat",
    "stale",
    "resync_required",
    "closed",
    "error",
]
_OPERATION_KINDS = frozenset(
    {
        "node_upsert",
        "node_delete",
        "edge_upsert",
        "edge_delete",
        "graph_metadata_merge",
        "graph_metadata_replace",
        "snapshot_reset",
    }
)
_STATUS_KINDS = frozenset(
    {
        "connecting",
        "live",
        "heartbeat",
        "stale",
        "resync_required",
        "closed",
        "error",
    }
)


@dataclass(frozen=True, slots=True)
class GraphFakosGraphRevision:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("revision value must not be empty")

    def to_dict(self) -> dict[str, object]:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosGraphRevision:
        return cls(value=_required_string(payload, "value", "revision"))


@dataclass(frozen=True, slots=True)
class GraphFakosLiveSessionCursor:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("cursor value must not be empty")

    def to_dict(self) -> dict[str, object]:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosLiveSessionCursor:
        return cls(value=_required_string(payload, "value", "cursor"))


@dataclass(frozen=True, slots=True)
class GraphFakosPatchOperation:
    kind: GraphFakosPatchOperationKind
    node: GraphFakosNode | None = None
    edge: GraphFakosEdge | None = None
    target_id: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    graph: GraphFakosGraph | None = None
    cascade: bool = False

    def __post_init__(self) -> None:
        if self.kind not in _OPERATION_KINDS:
            raise ValueError(f"unsupported patch operation kind: {self.kind!r}")
        _validate_operation_shape(self)
        _ensure_json(self.metadata, "operation.metadata")

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "node": self.node.to_dict() if self.node is not None else None,
            "edge": self.edge.to_dict() if self.edge is not None else None,
            "target_id": self.target_id,
            "metadata": dict(self.metadata),
            "graph": self.graph.to_dict() if self.graph is not None else None,
            "cascade": self.cascade,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosPatchOperation:
        node = payload.get("node")
        edge = payload.get("edge")
        graph = payload.get("graph")
        return cls(
            kind=_operation_kind(payload.get("kind")),
            node=GraphFakosNode.from_dict(_mapping(node, "operation.node"))
            if node is not None
            else None,
            edge=GraphFakosEdge.from_dict(_mapping(edge, "operation.edge"))
            if edge is not None
            else None,
            target_id=_optional_string(payload.get("target_id"), "operation.target_id"),
            metadata=_object_dict(payload.get("metadata", {}), "operation.metadata"),
            graph=GraphFakosGraph.from_dict(_mapping(graph, "operation.graph"))
            if graph is not None
            else None,
            cascade=_bool(payload.get("cascade", False), "operation.cascade"),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosGraphPatch:
    patch_id: str
    base_revision: GraphFakosGraphRevision
    result_revision: GraphFakosGraphRevision
    cursor: GraphFakosLiveSessionCursor
    operations: tuple[GraphFakosPatchOperation, ...]
    occurred_at: str = ""
    schema_version: str = "graphfakos.patch.v1"

    def __post_init__(self) -> None:
        if not self.patch_id.strip():
            raise ValueError("patch_id must not be empty")
        if not self.operations:
            raise ValueError("patch operations must not be empty")
        if self.base_revision == self.result_revision:
            raise ValueError("patch result revision must differ from base revision")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "patch_id": self.patch_id,
            "base_revision": self.base_revision.to_dict(),
            "result_revision": self.result_revision.to_dict(),
            "cursor": self.cursor.to_dict(),
            "operations": [item.to_dict() for item in self.operations],
            "occurred_at": self.occurred_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosGraphPatch:
        operations = payload.get("operations")
        if not isinstance(operations, list):
            raise TypeError("patch.operations must be a list")
        return cls(
            schema_version=_required_string(
                payload, "schema_version", "patch.schema_version"
            ),
            patch_id=_required_string(payload, "patch_id", "patch.patch_id"),
            base_revision=GraphFakosGraphRevision.from_dict(
                _mapping(payload.get("base_revision"), "patch.base_revision")
            ),
            result_revision=GraphFakosGraphRevision.from_dict(
                _mapping(payload.get("result_revision"), "patch.result_revision")
            ),
            cursor=GraphFakosLiveSessionCursor.from_dict(
                _mapping(payload.get("cursor"), "patch.cursor")
            ),
            operations=tuple(
                GraphFakosPatchOperation.from_dict(_mapping(item, "patch.operation"))
                for item in operations
            ),
            occurred_at=_optional_string(
                payload.get("occurred_at"), "patch.occurred_at"
            ),
        )


@dataclass(frozen=True, slots=True)
class GraphFakosLiveSessionRequest:
    session_id: str
    cursor: GraphFakosLiveSessionCursor | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "cursor": self.cursor.to_dict() if self.cursor is not None else None,
        }


@dataclass(frozen=True, slots=True)
class GraphFakosLiveSessionStatus:
    status: GraphFakosLiveStatusKind
    revision: GraphFakosGraphRevision
    cursor: GraphFakosLiveSessionCursor | None = None
    message: str = ""

    def __post_init__(self) -> None:
        if self.status not in _STATUS_KINDS:
            raise ValueError(f"unsupported live status: {self.status!r}")

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "revision": self.revision.to_dict(),
            "cursor": self.cursor.to_dict() if self.cursor is not None else None,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class GraphFakosLiveSessionDiagnostics:
    connection_count: int = 0
    queue_depth: int = 0
    last_revision: str = ""
    reconnect_count: int = 0
    rejected_patch_count: int = 0
    overflow_count: int = 0
    resync_count: int = 0
    authorization_rejection_count: int = 0
    origin_rejection_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True)
class GraphFakosLiveGraphState:
    graph: GraphFakosGraph
    revision: GraphFakosGraphRevision
    cursor: GraphFakosLiveSessionCursor | None = None
    applied_patch_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphFakosLiveReplayBundle:
    initial_graph: GraphFakosGraph
    initial_revision: GraphFakosGraphRevision
    patches: tuple[GraphFakosGraphPatch, ...]
    final_revision: GraphFakosGraphRevision
    schema_version: str = "graphfakos.live-replay.v1"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "initial_graph": self.initial_graph.to_dict(),
            "initial_revision": self.initial_revision.to_dict(),
            "patches": [patch.to_dict() for patch in self.patches],
            "final_revision": self.final_revision.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosLiveReplayBundle:
        patches = payload.get("patches")
        if not isinstance(patches, list):
            raise TypeError("live replay patches must be a list")
        return cls(
            schema_version=_required_string(
                payload, "schema_version", "live_replay.schema_version"
            ),
            initial_graph=GraphFakosGraph.from_dict(
                _mapping(payload.get("initial_graph"), "live_replay.initial_graph")
            ),
            initial_revision=GraphFakosGraphRevision.from_dict(
                _mapping(
                    payload.get("initial_revision"), "live_replay.initial_revision"
                )
            ),
            patches=tuple(
                GraphFakosGraphPatch.from_dict(_mapping(item, "live_replay.patch"))
                for item in patches
            ),
            final_revision=GraphFakosGraphRevision.from_dict(
                _mapping(payload.get("final_revision"), "live_replay.final_revision")
            ),
        )

    def replay(self) -> GraphFakosLiveGraphState:
        state = GraphFakosLiveGraphState(
            graph=self.initial_graph,
            revision=self.initial_revision,
        )
        for patch in self.patches:
            state = apply_graph_patch(state, patch)
        if state.revision != self.final_revision:
            raise ValueError("live replay final revision does not match bundle")
        return state


@runtime_checkable
class GraphFakosLiveProvider(Protocol):
    def open_live_session(
        self, request: GraphFakosLiveSessionRequest
    ) -> GraphFakosLiveSessionStatus: ...

    def load_patch(
        self, request: GraphFakosLiveSessionRequest
    ) -> GraphFakosGraphPatch | GraphFakosLiveSessionStatus: ...


def apply_graph_patch(
    state: GraphFakosLiveGraphState,
    patch: GraphFakosGraphPatch,
) -> GraphFakosLiveGraphState:
    """Apply one patch atomically, returning unchanged state for duplicates."""
    if patch.patch_id in state.applied_patch_ids:
        return state
    if patch.base_revision != state.revision:
        raise ValueError(
            f"patch base revision {patch.base_revision.value!r} does not match "
            f"current revision {state.revision.value!r}"
        )
    graph = state.graph
    nodes = graph.node_map()
    edges = graph.edge_map()
    provider_payload = dict(graph.provider_payload)
    for operation in patch.operations:
        if operation.kind == "snapshot_reset":
            graph = operation.graph  # shape validation guarantees non-None
            assert graph is not None
            nodes = graph.node_map()
            edges = graph.edge_map()
            provider_payload = dict(graph.provider_payload)
        elif operation.kind == "node_upsert":
            assert operation.node is not None
            nodes[operation.node.id] = operation.node
        elif operation.kind == "node_delete":
            incident = [
                edge_id
                for edge_id, edge in edges.items()
                if operation.target_id in (edge.source_id, edge.target_id)
            ]
            if incident and not operation.cascade:
                raise ValueError(
                    "node delete requires explicit incident edge deletes or cascade"
                )
            for edge_id in incident:
                edges.pop(edge_id)
            nodes.pop(operation.target_id, None)
        elif operation.kind == "edge_upsert":
            assert operation.edge is not None
            if (
                operation.edge.source_id not in nodes
                or operation.edge.target_id not in nodes
            ):
                raise ValueError("edge upsert references a missing endpoint")
            edges[operation.edge.id] = operation.edge
        elif operation.kind == "edge_delete":
            edges.pop(operation.target_id, None)
        elif operation.kind == "graph_metadata_merge":
            provider_payload.update(operation.metadata)
        elif operation.kind == "graph_metadata_replace":
            provider_payload = dict(operation.metadata)
    updated = replace(
        graph,
        nodes=tuple(nodes.values()),
        edges=tuple(edges.values()),
        provider_payload=provider_payload,
    )
    _validate_graph(updated)
    return GraphFakosLiveGraphState(
        graph=updated,
        revision=patch.result_revision,
        cursor=patch.cursor,
        applied_patch_ids=(*state.applied_patch_ids, patch.patch_id),
    )


class InMemoryGraphFakosLiveProvider:
    """Bounded reference provider for tests and local package integrations."""

    def __init__(
        self,
        *,
        revision: GraphFakosGraphRevision,
        max_queue: int = 128,
        max_operations: int = 1_000,
        max_patch_bytes: int = 1_048_576,
    ) -> None:
        if max_queue <= 0 or max_operations <= 0 or max_patch_bytes <= 0:
            raise ValueError("live-provider limits must be positive")
        self._revision = revision
        self._max_queue = max_queue
        self._max_operations = max_operations
        self._max_patch_bytes = max_patch_bytes
        self._patches: deque[GraphFakosGraphPatch] = deque()
        self._lock = Lock()
        self._reconnect_count = 0
        self._rejected_patch_count = 0
        self._overflow_count = 0
        self._resync_count = 0

    def publish_patch(self, patch: GraphFakosGraphPatch) -> None:
        encoded_size = len(json.dumps(patch.to_dict(), sort_keys=True).encode("utf-8"))
        if (
            len(patch.operations) > self._max_operations
            or encoded_size > self._max_patch_bytes
        ):
            with self._lock:
                self._rejected_patch_count += 1
            raise ValueError("patch exceeds configured operation or byte limit")
        with self._lock:
            if len(self._patches) == self._max_queue:
                self._patches.popleft()
                self._overflow_count += 1
            self._patches.append(patch)
            self._revision = patch.result_revision

    def open_live_session(
        self, request: GraphFakosLiveSessionRequest
    ) -> GraphFakosLiveSessionStatus:
        with self._lock:
            if request.cursor is not None:
                self._reconnect_count += 1
            return GraphFakosLiveSessionStatus(
                status="live",
                revision=self._revision,
                cursor=request.cursor,
            )

    def load_patch(
        self, request: GraphFakosLiveSessionRequest
    ) -> GraphFakosGraphPatch | GraphFakosLiveSessionStatus:
        with self._lock:
            if not self._patches:
                return GraphFakosLiveSessionStatus(
                    status="heartbeat", revision=self._revision, cursor=request.cursor
                )
            if request.cursor is None:
                return self._patches[0]
            cursor_values = [item.cursor.value for item in self._patches]
            if request.cursor.value not in cursor_values:
                self._resync_count += 1
                return GraphFakosLiveSessionStatus(
                    status="resync_required",
                    revision=self._revision,
                    cursor=request.cursor,
                    message="cursor is no longer available",
                )
            next_index = cursor_values.index(request.cursor.value) + 1
            if next_index < len(self._patches):
                return self._patches[next_index]
            return GraphFakosLiveSessionStatus(
                status="heartbeat", revision=self._revision, cursor=request.cursor
            )

    def diagnostics(self) -> GraphFakosLiveSessionDiagnostics:
        with self._lock:
            return GraphFakosLiveSessionDiagnostics(
                queue_depth=len(self._patches),
                last_revision=self._revision.value,
                reconnect_count=self._reconnect_count,
                rejected_patch_count=self._rejected_patch_count,
                overflow_count=self._overflow_count,
                resync_count=self._resync_count,
            )


def _validate_operation_shape(operation: GraphFakosPatchOperation) -> None:
    expected = {
        "node_upsert": operation.node is not None,
        "node_delete": bool(operation.target_id),
        "edge_upsert": operation.edge is not None,
        "edge_delete": bool(operation.target_id),
        "graph_metadata_merge": bool(operation.metadata),
        "graph_metadata_replace": True,
        "snapshot_reset": operation.graph is not None,
    }
    if not expected[operation.kind]:
        raise ValueError(f"patch operation {operation.kind!r} is missing its payload")


def _validate_graph(graph: GraphFakosGraph) -> None:
    node_ids = set(graph.node_map())
    if len(node_ids) != len(graph.nodes):
        raise ValueError("patched graph contains duplicate node ids")
    if len(graph.edge_map()) != len(graph.edges):
        raise ValueError("patched graph contains duplicate edge ids")
    for edge in graph.edges:
        if edge.source_id not in node_ids or edge.target_id not in node_ids:
            raise ValueError(f"patched edge {edge.id!r} has a missing endpoint")


def _required_string(payload: Mapping[str, object], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: object, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _object_dict(value: object, label: str) -> dict[str, object]:
    mapping = _mapping(value, label)
    result = dict(mapping)
    _ensure_json(result, label)
    return result


def _ensure_json(value: object, label: str) -> None:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be JSON-compatible") from exc


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be a boolean")
    return value


def _operation_kind(value: object) -> GraphFakosPatchOperationKind:
    if not isinstance(value, str) or value not in _OPERATION_KINDS:
        raise ValueError(f"unsupported patch operation kind: {value!r}")
    return cast(GraphFakosPatchOperationKind, value)


__all__ = [
    "apply_graph_patch",
    "GraphFakosGraphPatch",
    "GraphFakosGraphRevision",
    "GraphFakosLiveGraphState",
    "GraphFakosLiveProvider",
    "GraphFakosLiveReplayBundle",
    "GraphFakosLiveSessionCursor",
    "GraphFakosLiveSessionDiagnostics",
    "GraphFakosLiveSessionRequest",
    "GraphFakosLiveSessionStatus",
    "GraphFakosLiveStatusKind",
    "GraphFakosPatchOperation",
    "GraphFakosPatchOperationKind",
    "InMemoryGraphFakosLiveProvider",
]
