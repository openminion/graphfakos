"""Mutable provider session used only by the local interactive preview server."""

from __future__ import annotations

from collections.abc import Mapping

from .adapters.provider_envelope import graph_from_provider_envelope
from .models import (
    GraphFakosActionStatus,
    GraphFakosExpansionRequest,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosKnowledgeCapture,
    GraphFakosRequest,
)
from .provider import (
    GraphFakosComparisonProvider,
    GraphFakosGraphActionProvider,
    GraphFakosKnowledgeCaptureProvider,
    GraphFakosOverlayProvider,
    GraphFakosProvider,
    load_expanded_graph,
    validate_graph,
)


class LocalPreviewProviderSession:
    """Keep imports and drill-down results alive across local viewer routes."""

    def __init__(self, provider: GraphFakosProvider) -> None:
        self._provider = provider
        self._imported_graph: GraphFakosGraph | None = None
        self._graph_override: GraphFakosGraph | None = None

    @property
    def provider_id(self) -> str:
        return self._provider.provider_id

    @property
    def provider_label(self) -> str:
        return self._provider.provider_label

    @property
    def graph_role(self) -> str:
        return self._provider.graph_role

    @property
    def capabilities(self) -> tuple[str, ...]:
        return tuple(self._provider.capabilities)

    @property
    def supports_graph_actions(self) -> bool:
        return isinstance(self._provider, GraphFakosGraphActionProvider)

    @property
    def supports_knowledge_capture(self) -> bool:
        return isinstance(self._provider, GraphFakosKnowledgeCaptureProvider)

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        return (
            self._graph_override
            or self._imported_graph
            or self._provider.load_graph(request)
        )

    def load_comparison_graph(
        self, request: GraphFakosRequest
    ) -> GraphFakosGraph | None:
        if not isinstance(self._provider, GraphFakosComparisonProvider):
            return None
        return self._provider.load_comparison_graph(request)

    def load_overlay_graphs(
        self, request: GraphFakosRequest
    ) -> tuple[GraphFakosGraph, ...]:
        if not isinstance(self._provider, GraphFakosOverlayProvider):
            return ()
        return self._provider.load_overlay_graphs(request)

    def expand_graph(
        self,
        request: GraphFakosRequest,
        expansion: GraphFakosExpansionRequest,
    ) -> GraphFakosGraph | None:
        graph = load_expanded_graph(self._provider, request, expansion)
        if graph is not None:
            self._graph_override = graph
        return graph

    def reset_graph(self) -> GraphFakosGraph:
        self._graph_override = None
        return self._imported_graph or self._provider.load_graph(GraphFakosRequest())

    def import_payload(
        self,
        payload_format: str,
        payload: Mapping[str, object],
    ) -> GraphFakosGraph:
        if payload_format == "provider_envelope":
            graph = graph_from_provider_envelope(payload, source_path="browser import")
        elif payload_format == "graph_artifact":
            graph = GraphFakosGraph.from_dict(payload)
        else:
            raise ValueError("format must be provider_envelope or graph_artifact")
        validate_graph(graph)
        self._imported_graph = graph
        self._graph_override = None
        return graph

    def capture_knowledge(self, capture: GraphFakosKnowledgeCapture) -> object:
        if not isinstance(self._provider, GraphFakosKnowledgeCaptureProvider):
            return None
        result = self._provider.capture_knowledge(capture)
        if isinstance(result, GraphFakosGraph):
            self._graph_override = result
        return result

    def submit_graph_action(
        self, action: GraphFakosGraphAction
    ) -> GraphFakosActionStatus | Mapping[str, object] | None:
        if not isinstance(self._provider, GraphFakosGraphActionProvider):
            return None
        result = self._provider.submit_graph_action(action)
        if isinstance(result, GraphFakosGraph):
            self._graph_override = result
        return result


__all__ = ["LocalPreviewProviderSession"]
