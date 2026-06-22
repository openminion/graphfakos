from __future__ import annotations

from graphfakos import FixtureGraphProvider, GraphFakosRequest, render_static_html
from graphfakos.testing import assert_graph_viewer_contract


def test_static_viewer_renders_graph_canvas_and_inspector() -> None:
    html = render_static_html(FixtureGraphProvider(), GraphFakosRequest())

    assert_graph_viewer_contract(
        html,
        expected_role="third-party",
        expected_provider="Fixture Provider",
        expected_node="Operator Preference",
        expected_edge="supports",
    )
    assert "Neighborhood" in html
    assert "Provider Status" in html


def test_provider_status_screen_renders_capabilities() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="provider_status"),
    )

    assert "Provider Status" in html
    assert "static_export" in html
    assert "local_preview" in html


def test_explore_screen_renders_filter_controls_and_edge_inspector() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            query="provider",
            selected_edge_id="edge:provider-serves-spec",
            filters={"node_kind": "provider", "edge_kind": "serves"},
        ),
    )

    assert "aria-label='Graph filters'" in html
    assert "Node kind" in html
    assert "Edge kind" in html
    assert "selected" in html
    assert "Selected Edge" in html
    assert "edge:provider-serves-spec" in html
    assert "Third-party Provider" in html


def test_neighborhood_screen_uses_depth_controls() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="neighborhood",
            focus_node_id="provider:third-party",
            max_depth=2,
        ),
    )

    assert "aria-label='Neighborhood controls'" in html
    assert "Depth 2 neighborhood" in html
    assert "Static Export" in html


def test_path_screen_renders_source_target_controls() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="path",
            source_node_id="provider:third-party",
            target_node_id="artifact:static-export",
        ),
    )

    assert "aria-label='Path controls'" in html
    assert "Source node" in html
    assert "Target node" in html
    assert "provider:third-party -&gt; artifact:static-export" in html
