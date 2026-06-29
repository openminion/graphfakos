"""File-backed provider adapter for persisted GraphFakos artifacts."""

from __future__ import annotations

from ..artifacts import load_graph_artifact
from ..models import GraphFakosGraph, GraphFakosRequest


class FileGraphProvider:
    """Load one current graph plus optional comparison/overlay artifacts."""

    def __init__(
        self,
        graph_path: str,
        *,
        comparison_graph_path: str = "",
        overlay_graph_paths: tuple[str, ...] = (),
    ) -> None:
        self._graph = load_graph_artifact(graph_path)
        self._comparison_graph = (
            load_graph_artifact(comparison_graph_path)
            if comparison_graph_path
            else None
        )
        self._overlay_graphs = tuple(
            load_graph_artifact(path) for path in overlay_graph_paths
        )
        self.provider_id = self._graph.provider_id
        self.provider_label = self._graph.provider_label
        self.graph_role = self._graph.graph_role
        self.capabilities = self._graph.capabilities

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        return self._graph

    def load_comparison_graph(self, request: GraphFakosRequest) -> GraphFakosGraph | None:
        if self._comparison_graph is None:
            return None
        requested_id = request.comparison_graph_id or ""
        snapshot = self._graph.snapshot
        if not requested_id:
            return self._comparison_graph
        if snapshot is not None and requested_id in snapshot.comparison_ids:
            return self._comparison_graph
        comparison_snapshot = self._comparison_graph.snapshot
        if comparison_snapshot is not None and requested_id == comparison_snapshot.snapshot_id:
            return self._comparison_graph
        if requested_id == self._comparison_graph.graph_id:
            return self._comparison_graph
        return None

    def load_overlay_graphs(
        self,
        request: GraphFakosRequest,
    ) -> tuple[GraphFakosGraph, ...]:
        return self._overlay_graphs


__all__ = ["FileGraphProvider"]
