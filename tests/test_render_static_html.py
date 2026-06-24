from __future__ import annotations

from graphfakos import (
    FixtureGraphProvider,
    GraphFakosRequest,
    render_embeddable_html,
    render_graph_markdown_report,
    render_static_html,
)
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
    assert "Visible Graph" in html


def test_provider_status_screen_renders_capabilities() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="provider_status"),
    )

    assert "Provider Status" in html
    assert "Graph Health" in html
    assert "Integration Commands" in html
    assert "healthy" in html
    assert "static_export" in html
    assert "local_preview" in html
    assert "Capability Notes" in html
    assert "Overlay Provider" in html


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
    assert "edge hop(s) connect" in html
    assert "Route starts at provider:third-party" in html


def test_context_preview_screen_renders_ranked_context_cards() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="context_preview"),
    )

    assert "Context Assembly Preview" in html
    assert "Top 4 node(s) are ranked" in html
    assert "score 0.98" in html


def test_diff_screen_renders_snapshot_comparison() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="diff"),
    )

    assert "Snapshot Diff" in html
    assert "Fixture Baseline" in html
    assert "Added nodes" in html
    assert "Overlay Providers" in html


def test_embeddable_html_renders_fragment_only() -> None:
    html = render_embeddable_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="explore", query="kind:provider"),
    )

    assert "data-graphfakos-embed='true'" in html
    assert "<main class='gf-content gf-embed-root'" in html
    assert "<!doctype html>" not in html
    assert "Deep link:" in html


def test_markdown_report_renders_snapshot_and_comparison() -> None:
    markdown = render_graph_markdown_report(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="diff"),
    )

    assert "# GraphFakos Report" in markdown
    assert "- Screen: `diff`" in markdown
    assert "- Snapshot: `fixture-current`" in markdown
    assert "- Comparison: `Fixture Baseline`" in markdown
