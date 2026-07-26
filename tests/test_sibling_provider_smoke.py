from __future__ import annotations

import sys
from pathlib import Path

import pytest

from graphfakos import GraphFakosRequest, render_static_html
from graphfakos.adapters.provider_envelope import graph_from_provider_envelope
from graphfakos.provider import load_provider_graph
from graphfakos.testing.conformance import (
    GraphFakosProviderConformanceCase,
    assert_provider_conformance,
)


def _add_sibling_src(package: str) -> None:
    package_src = Path(__file__).resolve().parents[1].parent / package / "src"
    if not package_src.exists():
        pytest.skip(f"{package} source tree is not available")
    sys.path.insert(0, str(package_src))


def test_pragmagraph_viewer_envelope_smokes_through_graphfakos() -> None:
    _add_sibling_src("pragmagraph")
    viewer = pytest.importorskip("pragmagraph.viewer")

    envelope = viewer.build_viewer_fixture_envelope("viewer-scale-200k").to_dict()
    graph = graph_from_provider_envelope(envelope, source_path="pragmagraph fixture")

    assert graph.provider_id == "pragmagraph"
    assert graph.stats["provider_envelope"] is True
    assert graph.stats["hidden_nodes"] > 0
    assert graph.stats["level_of_detail"] in {"cluster", "meta"}
    assert any(node.kind == "cluster" for node in graph.nodes)
    assert any(edge.kind == "edge_bundle" for edge in graph.edges)


def test_sophiagraph_adapter_smokes_through_graphfakos_conformance() -> None:
    _add_sibling_src("sophiagraph")
    models = pytest.importorskip("sophiagraph.models")
    storage = pytest.importorskip("sophiagraph.storage")
    adapter = pytest.importorskip("sophiagraph.ui.graphfakos_adapter")

    namespace = models.MemoryNamespace(agent_id="codex", graph_id="main")
    store = storage.SophiaGraphMemoryStore()
    store.put_record(
        models.MemoryRecord(
            id="auth",
            scope="agent:codex",
            type="fact",
            key="auth",
            title="Auth Decision",
            content={"text": "Use JWT auth for the operator console."},
            namespace=namespace,
            source="validated",
            confidence=0.91,
            created_at="2026-06-22T00:00:00+00:00",
            updated_at="2026-06-22T00:00:00+00:00",
        )
    )
    store.put_record(
        models.MemoryRecord(
            id="refresh",
            scope="agent:codex",
            type="fact",
            key="refresh",
            title="Refresh Plan",
            content={"text": "Refresh GraphFakos previews after sync."},
            namespace=namespace,
            created_at="2026-06-22T00:00:00+00:00",
            updated_at="2026-06-22T00:00:00+00:00",
        )
    )
    store.put_link(
        models.StructuralLink(
            link_id="link-auth-refresh",
            source_record_id="auth",
            target_record_id="refresh",
            raw_target="Refresh Plan",
            link_kind="wikilink",
            resolution_status="resolved",
            namespace=namespace,
            relation_type="supports",
            created_at="2026-06-22T00:00:00+00:00",
        )
    )
    provider = adapter.SophiagraphViewerProvider(
        store=store,
        scope="agent:codex",
        namespace=namespace,
    )

    result = assert_provider_conformance(
        GraphFakosProviderConformanceCase(
            provider=provider,
            request=GraphFakosRequest(),
            expected_role="memory",
            expected_provider="Sophiagraph",
            expected_node="Auth Decision",
            expected_edge="supports",
            required_capabilities=("search", "neighborhood", "path"),
        )
    )
    html = render_static_html(provider, GraphFakosRequest(screen="explore"))
    graph = load_provider_graph(provider, GraphFakosRequest())

    assert result.graph.provider_id == "sophiagraph"
    assert graph.provider_label == "Sophiagraph"
    assert "Auth Decision" in html
    assert "supports" in html
