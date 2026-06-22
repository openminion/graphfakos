from __future__ import annotations

from graphfakos.adapters import FixtureGraphProvider
from graphfakos.models import GraphFakosRequest


def test_fixture_adapter_is_third_party_graph() -> None:
    graph = FixtureGraphProvider().load_graph(GraphFakosRequest())

    assert graph.graph_role == "third_party"
    assert "Third-party Provider" in {node.label for node in graph.nodes}
    assert any(edge.kind == "supports" for edge in graph.edges)
