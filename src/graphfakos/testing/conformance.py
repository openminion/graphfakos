"""Reusable provider conformance checks for GraphFakos consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..adapters import FileGraphProvider
from ..artifacts import write_graph_artifact
from ..models import GraphFakosGraph, GraphFakosRequest
from ..provider import (
    GraphFakosGraphActionProvider,
    GraphFakosKnowledgeCaptureProvider,
    GraphFakosProvider,
    diagnose_graph,
    load_provider_graph,
)
from ..static import build_graph_report, render_static_html
from .assertions import assert_graph_viewer_contract


@dataclass(frozen=True, slots=True)
class GraphFakosProviderConformanceCase:
    provider: GraphFakosProvider
    request: GraphFakosRequest = field(default_factory=GraphFakosRequest)
    expected_role: str = ""
    expected_provider: str = ""
    expected_node: str = ""
    expected_edge: str = ""
    required_capabilities: tuple[str, ...] = ()
    artifact_path: str | Path | None = None


@dataclass(frozen=True, slots=True)
class GraphFakosProviderConformanceResult:
    graph: GraphFakosGraph
    report: dict[str, object]
    html: str
    replay_graph: GraphFakosGraph | None = None


def assert_provider_conformance(
    case: GraphFakosProviderConformanceCase,
) -> GraphFakosProviderConformanceResult:
    graph = load_provider_graph(case.provider, case.request)
    _assert_metadata(case, graph)
    _assert_capabilities(case, graph)
    _assert_optional_protocols(case.provider, graph)

    html = render_static_html(case.provider, case.request)
    if (
        case.expected_role
        and case.expected_provider
        and case.expected_node
        and case.expected_edge
    ):
        assert_graph_viewer_contract(
            html,
            expected_role=_html_role(case.expected_role),
            expected_provider=case.expected_provider,
            expected_node=case.expected_node,
            expected_edge=case.expected_edge,
        )

    report = build_graph_report(case.provider, case.request)
    _assert_report_contract(case, graph, report)
    replay_graph = _assert_artifact_replay(case, graph)
    return GraphFakosProviderConformanceResult(
        graph=graph,
        report=report,
        html=html,
        replay_graph=replay_graph,
    )


def _assert_metadata(
    case: GraphFakosProviderConformanceCase,
    graph: GraphFakosGraph,
) -> None:
    assert graph.graph_id
    assert graph.label
    assert graph.provider_id == case.provider.provider_id
    assert graph.provider_label == case.provider.provider_label
    assert graph.graph_role == case.provider.graph_role
    if case.expected_role:
        assert graph.graph_role == case.expected_role
    if case.expected_provider:
        assert graph.provider_label == case.expected_provider
    diagnostics = diagnose_graph(graph)
    assert diagnostics.node_count == len(graph.nodes)
    assert diagnostics.edge_count == len(graph.edges)


def _assert_capabilities(
    case: GraphFakosProviderConformanceCase,
    graph: GraphFakosGraph,
) -> None:
    graph_capabilities = set(graph.capabilities)
    assert graph_capabilities
    for capability in case.required_capabilities:
        assert capability in graph_capabilities


def _assert_optional_protocols(
    provider: GraphFakosProvider,
    graph: GraphFakosGraph,
) -> None:
    capabilities = set(graph.capabilities)
    if "graph_actions" in capabilities:
        assert isinstance(provider, GraphFakosGraphActionProvider)
    if "knowledge_capture" in capabilities:
        assert isinstance(provider, GraphFakosKnowledgeCaptureProvider)


def _assert_report_contract(
    case: GraphFakosProviderConformanceCase,
    graph: GraphFakosGraph,
    report: dict[str, object],
) -> None:
    assert _mapping(report["graph"])["graph_id"] == graph.graph_id
    assert _mapping(report["request"])["screen"] == case.request.screen
    viewer_state = _mapping(report["viewer_state"])
    saved_view = _mapping(report["saved_view"])
    assert viewer_state["screen"] == case.request.screen
    assert _mapping(saved_view["state"])["screen"] == case.request.screen
    assert isinstance(report["review_presets"], list)
    assert isinstance(report["screen_manifest"], list)
    assert _mapping(report["analytics"])["node_count"] == len(graph.nodes)
    assert _mapping(report["diagnostics"])["node_count"] == len(graph.nodes)


def _assert_artifact_replay(
    case: GraphFakosProviderConformanceCase,
    graph: GraphFakosGraph,
) -> GraphFakosGraph | None:
    if case.artifact_path is None:
        return None
    artifact_path = Path(case.artifact_path)
    write_graph_artifact(graph, str(artifact_path))
    replay_provider = FileGraphProvider(str(artifact_path))
    replay_graph = load_provider_graph(replay_provider, case.request)
    assert replay_graph.to_dict() == graph.to_dict()
    replay_html = render_static_html(replay_provider, case.request)
    assert graph.label in replay_html
    return replay_graph


def _mapping(value: object) -> dict[str, Any]:
    assert isinstance(value, dict)
    return value


def _html_role(role: str) -> str:
    return role.replace("_", "-")


__all__ = [
    "GraphFakosProviderConformanceCase",
    "GraphFakosProviderConformanceResult",
    "assert_provider_conformance",
]
