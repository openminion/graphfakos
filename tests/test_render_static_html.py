from __future__ import annotations

import json
import re

from graphfakos import (
    FixtureGraphProvider,
    GraphFakosRequest,
    render_graph_dot,
    render_embeddable_html,
    render_graph_markdown_report,
    render_static_html,
)
from graphfakos.testing import assert_graph_dot_contract, assert_graph_viewer_contract


def _json_script_payload(html: str, data_attribute: str) -> object:
    pattern = (
        rf"<script type='application/json' {re.escape(data_attribute)}='true'>"
        r"(.*?)</script>"
    )
    match = re.search(pattern, html)
    assert match is not None
    return json.loads(match.group(1))


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
    assert "data-gf-camera='zoom-in'" in html
    assert "aria-label='Graph search palette'" in html
    assert "aria-label='Graph minimap'" in html
    assert "aria-label='Graph view lenses'" in html
    assert "Capture Knowledge" in html
    assert "data-gf-knowledge-form='true'" in html
    assert "gf-viewport" in html
    assert "<graphfakos-viewer" in html
    assert "data-state-json=" in html
    assert 'customElements.define("graphfakos-viewer"' in html
    assert "<script>" in html


def test_static_viewer_renders_competitive_workbench_controls() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            render_engine="canvas",
            theme="ink",
            saved_view_id="ops-review",
            show_orphans=False,
            show_neighbor_links=False,
            edge_clutter="reduced",
            analytics_overlay="degree",
        ),
    )

    assert "data-theme='ink'" in html
    assert "render-engine='canvas'" in html
    assert "Canvas renderer is enabled" in html
    assert "data-gf-canvas='true'" in html
    assert "data-gf-canvas-payload='true'" in html
    assert "aria-label='Saved workspace controls'" in html
    assert "aria-label='Local graph controls'" in html
    assert "aria-label='Physics and display controls'" in html
    assert "Advanced Filters" in html
    assert "Component Explorer" in html
    assert "Multi-Select Workbench" in html
    assert "Attribute Styling" in html
    assert "Timeline/Diff Animation" in html
    assert "Investigation Pivot" in html
    assert "Context Menus" in html
    assert "Node Actions" in html
    assert "Edge Actions" in html
    assert "Command Palette" in html
    assert "Analytics Overlay" in html
    assert "Export and Replay" in html
    assert "Graph Authoring" in html
    assert "data-gf-saved-view='true'" in html
    assert "data-gf-saved-queries='true'" in html
    assert "data-gf-replay-bundle-preview='true'" in html
    assert "data-gf-action-template='true'" in html
    assert "data-gf-action-status-text='true'" in html
    assert "data-clutter='reduced'" in html
    assert _json_script_payload(html, "data-gf-saved-view")["view_id"] == "ops-review"
    assert (
        _json_script_payload(html, "data-gf-action-template")["action_type"]
        == "draft_node"
    )
    assert _json_script_payload(html, "data-gf-action-status")["status"] == "draft"
    assert (
        _json_script_payload(html, "data-gf-replay-bundle-preview")["schema_version"]
        == "graphfakos.replay.v1"
    )


def test_static_viewer_minimap_marks_nodes_for_navigation() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(focus_node_id="provider:third-party"),
    )

    assert "aria-label='Graph minimap'" in html
    assert "data-minimap-node-id='provider:third-party'" in html
    assert "data-node-ref='provider:third-party'" in html
    assert "<title>Third-party Provider</title>" in html
    assert "data-selected='true'" in html


def test_static_viewer_keeps_no_javascript_svg_fallback() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(camera_x=12.5, camera_y=-4.0, camera_zoom=1.4),
    )

    assert "data-camera-x='12.50'" in html
    assert "data-camera-y='-4.00'" in html
    assert "data-camera-zoom='1.40'" in html
    assert "transform='translate(12.50 -4.00) scale(1.40)'" in html
    assert "Saved view" in html
    assert "camera_zoom=1.4" in html


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
    assert "Workflow" in html
    assert "Navigator" in html


def test_explore_screen_supports_quoted_score_and_time_queries() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            query='"Operator Preference" score>=0.9 time>=2026-06-20',
        ),
    )

    assert "Operator Preference" in html
    assert "Third-party Provider" not in html


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
    assert "data-path='true'" in html
    assert "Capture Knowledge" in html


def test_explore_screen_renders_new_layout_and_group_controls() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="explore", layout="radial"),
    )

    assert "Radial layout" in html
    assert "data-gf-group='artifact'" in html
    assert "data-kind='document'" in html
    assert "marker-end='url(#gf-arrow)'" in html


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
    assert "Changed nodes" in html
    assert "Change Hotspots" in html
    assert "Snapshot changes" in html
    assert "Overlay Providers" in html


def test_embeddable_html_renders_fragment_only() -> None:
    html = render_embeddable_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="explore", query="kind:provider"),
    )

    assert "data-graphfakos-embed='true'" in html
    assert "data-graphfakos-screen='explore'" in html
    assert "<main class='gf-content gf-embed-root'" in html
    assert "<graphfakos-viewer" in html
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
    assert "## Diff Summary" in markdown
    assert "### Change Hotspots" in markdown


def test_provenance_screen_renders_evidence_coverage() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="provenance"),
    )

    assert "Evidence Coverage" in html
    assert "Provider Coverage" in html
    assert "Citation Locations" in html


def test_graph_dot_render_is_public_for_static_exports() -> None:
    dot = render_graph_dot(FixtureGraphProvider().load_graph(GraphFakosRequest()))

    assert_graph_dot_contract(
        dot,
        expected_node_ids=("provider:third-party", "memory:operator-preference"),
        expected_edge_ids=("supports",),
    )
