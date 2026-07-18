from __future__ import annotations

import json
import re

from graphfakos import (
    DemoGraphProvider,
    FixtureGraphProvider,
    GraphFakosRequest,
    render_graph_dot,
    render_embeddable_html,
    render_graph_markdown_report,
    render_static_html,
)
from graphfakos.browser import viewer_runtime_script
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
    assert "aria-label='Active graph lens'" in html
    assert "data-gf-active-lens-panel='true'" in html
    assert "data-gf-active-lens='true'" in html
    assert "data-gf-camera='zoom-in'" in html
    assert "aria-label='Fit selected or visible graph'" in html
    assert "Fit zooms to the current selection or visible graph" in html
    assert "data-gf-pin='reset'" in html
    assert "Clear pins" in html
    assert "aria-label='Graph search palette'" in html
    assert "data-gf-search-form='true'" in html
    assert "data-gf-command-search='true'" in html
    assert "aria-keyshortcuts='/ Control+K Meta+K'" in html
    assert "gf-command-shortcut" in html
    assert "/ or Ctrl+K" in html
    assert "aria-label='Graph minimap'" in html
    assert "data-gf-minimap-node='true'" in html
    assert "data-gf-minimap-viewport='true'" in html
    assert ".gf-minimap-viewport" in html
    assert "gf-minimap-node-link" in html
    assert "aria-label='Graph view lenses'" in html
    assert "Capture Knowledge" in html
    assert "data-gf-knowledge-form='true'" in html
    assert "data-gf-capture-templates='true'" in html
    assert "data-gf-capture-template='note'" in html
    assert "data-gf-capture-template='question'" in html
    assert "Code observation" in html
    assert "data-gf-capture-template='warning'" in html
    assert "Flag a risk, stale edge, or unexpected graph relationship." in html
    assert "name='viewer_context'" in html
    assert "data-gf-viewer-context-preview='true'" in html
    assert "Submission Context" in html
    assert "&quot;selected_node_ids&quot;" in html
    assert "Capture unsupported" in html
    assert "data-gf-knowledge-form='true' data-gf-capability-supported='false'" in html
    assert "Current provider does not advertise workbench knowledge capture." in html
    assert "Attach note to node" in html
    assert "Relationship kind" in html
    assert "name='link_node_id'" in html
    assert "name='link_edge_kind'" in html
    assert "gf-viewport" in html
    assert "data-layout-x=" in html
    assert "Shift-drag empty canvas to box-select nodes" in html
    assert "right-click or press Shift+F10" in html
    assert "Alt/Option-drag a node to move its cluster" in html
    assert "WASD or arrows move like a map" in html
    assert ".gf-shortcut-hint" in html
    assert "data-detail-mode=" in html
    assert "data-label-priority=" in html
    assert "data-gf-detail-mode='true'" in html
    assert '.gf-canvas-shell[data-detail-mode="overview"]' in html
    assert "Labels and edges become denser as you zoom in." in html
    assert "data-gf-live-selection='true'" in html
    assert "aria-live='polite'" in html
    assert ".gf-live-selection" in html
    assert "data-gf-graph-item='node'" in html
    assert "data-gf-graph-item='edge'" in html
    assert "<path class='gf-edge'" in html
    assert "data-source-x=" in html
    assert "data-target-x=" in html
    assert "data-z=" in html
    assert "data-layout-z=" in html
    assert "data-camera-yaw=" in html
    assert "data-camera-pitch=" in html
    assert "data-render-engine=" in html
    assert "data-cluster-id=" in html
    assert "data-content-preview=" in html
    assert "data-gf-inspect-overlay='true'" in html
    assert "data-gf-inspect-command='true'" in html
    assert "data-gf-overlay-action='draft_note'" in html
    assert "lastCommand" in viewer_runtime_script()
    assert "data-gf-inspect-content='true'" in html
    assert "data-gf-inspect-properties='true'" in html
    assert ".gf-inspect-overlay" in html
    assert '.gf-edge[data-stretched="true"]' in html
    assert '.gf-node[data-neighbor="true"]' in html
    assert "Press Shift+F10 for actions." in html
    assert ".gf-graph-item-link:focus-visible" in html
    assert "data-focus-route=" in html
    assert "data-local-route=" in html
    assert "data-evidence-route=" in html
    assert "data-pivot-route=" in html
    assert "data-inspect-route=" in html
    assert "data-path-route=" in html
    assert "data-kind-route=" in html
    assert ".gf-surface-menu" in html
    assert ".gf-selection-box" in html
    assert "data-gf-theme-toggle='true'" in html
    assert "data-gf-group-show-all='true'" in html
    assert "Show all" in html
    assert "<graphfakos-viewer" in html
    assert "data-state-json=" in html
    assert 'customElements.define("graphfakos-viewer"' in html
    assert "<script>" in html


def test_static_viewer_renders_route_backed_command_palette() -> None:
    html = render_static_html(
        DemoGraphProvider("workbench-mixed"),
        GraphFakosRequest(
            focus_node_id="agent:reviewer",
            selected_edge_id="edge:agent-links-code",
        ),
    )

    assert "data-gf-command-palette-panel='true'" in html
    assert "data-gf-command-search='true'" in html
    assert "data-gf-command-palette-search='true'" in html
    assert "data-gf-command-palette-status='true'" in html
    assert "data-gf-command-palette='true'" in html
    assert "Capture Knowledge" in html
    assert "Graph Authoring" in html
    assert "id='capture-knowledge'" in html
    assert "id='graph-authoring'" in html
    assert "#capture-knowledge" in html
    assert "#graph-authoring" in html

    palette = _json_script_payload(html, "data-gf-command-palette")
    groups = {group["id"]: group for group in palette["groups"]}
    author_actions = {action["id"]: action for action in groups["author"]["actions"]}
    review_actions = {action["id"]: action for action in groups["review"]["actions"]}
    navigate_actions = {
        action["id"]: action for action in groups["navigate"]["actions"]
    }

    assert palette["focus_node_id"] == "agent:reviewer"
    assert palette["selected_edge_id"] == "edge:agent-links-code"
    assert palette["group_count"] == 5
    assert palette["action_count"] >= 15
    assert set(groups) == {"query", "navigate", "review", "author", "export"}
    assert author_actions["capture"]["disabled"] is False
    assert author_actions["capture"]["route"].endswith("#capture-knowledge")
    assert author_actions["draft-action"]["disabled"] is False
    assert author_actions["draft-action"]["route"].endswith("#graph-authoring")
    assert "query=has%3Aprovenance" in review_actions["evidence"]["route"]
    assert "source_node_id=agent%3Areviewer" in navigate_actions["path"]["route"]
    assert palette["provider_boundary"].startswith(
        "Command palette entries change only GraphFakos route/view state"
    )


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
    assert "name='render_engine' value='canvas'" in html
    assert "name='theme' value='ink'" in html
    assert "name='saved_view_id' value='ops-review'" in html
    assert "Active lens" in html
    assert "SVG fallback" in html
    assert "Canvas renderer is enabled" in html
    assert "data-gf-canvas='true'" in html
    assert "data-gf-canvas-payload='true'" in html
    assert "data-gf-display-dock='true'" in html
    assert "data-gf-scene-control='node_scale'" in html
    assert "data-gf-scene-control='label_density'" in html
    assert "data-gf-scene-control='edge_opacity'" in html
    assert "data-gf-scene-level='overview'" in html
    assert "aria-label='More graph controls'" in html
    assert "Visual Legend" in html
    assert "data-gf-canvas-legend-panel='true'" in html
    assert "data-gf-canvas-legend='true'" in html
    assert "aria-label='Saved workspace controls'" in html
    assert "aria-label='Local graph controls'" in html
    assert "aria-label='Physics and display controls'" in html
    assert "Advanced Filters" in html
    assert "Component Explorer" in html
    assert "data-gf-component-cards='true'" in html
    assert "data-gf-component-map='true'" in html
    assert "Open component" in html
    assert "Focus hub" in html
    assert "Multi-Select Workbench" in html
    assert "Attribute Styling" in html
    assert "Timeline/Diff Animation" in html
    assert "Investigation Pivot" in html
    assert "data-gf-case-packet='true'" in html
    assert "Case Packet" in html
    assert "Nearest Neighbors" in html
    assert "Shortest Path Pivots" in html
    assert "Evidence Bundle" in html
    assert "Timeline Markers" in html
    assert "Component Sample" in html
    assert "Navigation Map" in html
    assert "data-gf-navigation-map-panel='true'" in html
    assert "data-gf-navigation-map='true'" in html
    assert "Context Menus" in html
    assert "Node Actions" in html
    assert "Edge Actions" in html
    assert "data-gf-selection-sets-panel='true'" in html
    assert "data-gf-selection-sets='true'" in html
    assert "Build case packet" in html
    assert "Trace path" in html
    assert "pivot_node_id=" in html
    assert "pivot_mode=neighbors" in html
    assert "source_node_id=" in html
    assert "Command Palette" in html
    assert "Search Results" in html
    assert "data-gf-search-results-panel='true'" in html
    assert "data-gf-search-results='true'" in html
    assert "Interaction guide" in html
    assert "data-gf-interaction-guide-panel='true'" in html
    assert "data-gf-interaction-guide='true'" in html
    assert "Graph Data Table" in html
    assert "data-gf-graph-data-table-panel='true'" in html
    assert "data-gf-graph-data-table='true'" in html
    assert "Relationship Data Table" in html
    assert "data-gf-relationship-data-table-panel='true'" in html
    assert "data-gf-relationship-data-table='true'" in html
    assert "Evidence Coverage Map" in html
    assert "data-gf-evidence-coverage-panel='true'" in html
    assert "data-gf-evidence-coverage-map='true'" in html
    assert "Facet Explorer" in html
    assert "data-gf-facet-explorer-panel='true'" in html
    assert "data-gf-facet-explorer='true'" in html
    assert "Expansion Planner" in html
    assert "data-gf-expansion-planner-panel='true'" in html
    assert "data-gf-expansion-plan='true'" in html
    assert "Readability Coach" in html
    assert "data-gf-readability-coach='true'" in html
    assert "Display Recipes" in html
    assert "data-gf-display-recipes-panel='true'" in html
    assert "data-gf-display-recipes='true'" in html
    assert "Analytics Overlay" in html
    assert "Export and Replay" in html
    assert "Graph Authoring" in html
    assert "Actions unsupported" in html
    assert "data-gf-action-form='true' data-gf-capability-supported='false'" in html
    assert "Current provider does not advertise graph authoring actions." in html
    assert "data-gf-saved-view='true'" in html
    assert "data-gf-saved-queries='true'" in html
    assert "data-gf-workbook='true'" in html
    assert "data-gf-workbook-action='save'" in html
    assert "data-gf-workbook-action='clear'" in html
    assert "JavaScript can save local browser-only slots here" in html
    assert "data-gf-replay-bundle-preview='true'" in html
    assert "data-gf-action-template='true'" in html
    assert "data-gf-action-status-text='true'" in html
    assert "name='action_id' value='draft:route'" in html
    assert "Action target node" in html
    assert "Draft edge source" in html
    assert "Draft edge target" in html
    assert "name='source_id'" in html
    assert "name='target_node_id'" in html
    assert "name='tags' placeholder='editor, review'" in html
    assert "Viewer Spec</option>" in html
    assert "data-clutter='reduced'" in html
    assert _json_script_payload(html, "data-gf-saved-view")["view_id"] == "ops-review"
    assert (
        _json_script_payload(html, "data-gf-action-template")["action_type"]
        == "draft_node"
    )
    assert _json_script_payload(html, "data-gf-action-status")["status"] == "draft"
    component_map = _json_script_payload(html, "data-gf-component-map")
    assert component_map["components"][0]["component_id"] == "component:1"
    assert component_map["components"][0]["hub_label"] == "Viewer Spec"
    assert component_map["components"][0]["node_count"] == 4
    assert component_map["components"][0]["edge_count"] == 4
    assert component_map["components"][0]["route"].startswith("/explore?")
    assert component_map["components"][0]["case_packet_route"].startswith("/explore?")
    assert (
        _json_script_payload(html, "data-gf-replay-bundle-preview")["schema_version"]
        == "graphfakos.replay.v1"
    )


def test_explore_screen_renders_graph_data_table_routes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="provider:third-party",
            selected_node_ids=("document:viewer-spec",),
        ),
    )

    table = _json_script_payload(html, "data-gf-graph-data-table")
    viewer_row = next(
        row for row in table["rows"] if row["id"] == "document:viewer-spec"
    )
    provider_row = next(
        row for row in table["rows"] if row["id"] == "provider:third-party"
    )

    assert "Visible graph rows keep navigation" in html
    assert table["visible_node_count"] == 4
    assert table["visible_edge_count"] == 4
    assert table["selected_node_ids"] == ["document:viewer-spec"]
    assert table["focus_node_id"] == "provider:third-party"
    assert table["provider_boundary"].startswith(
        "GraphFakos lists visible graph structure"
    )
    assert viewer_row["label"] == "Viewer Spec"
    assert viewer_row["kind"] == "document"
    assert viewer_row["degree"] == 3
    assert viewer_row["component_id"] == "component:1"
    assert viewer_row["provenance_count"] == 1
    assert viewer_row["citation_count"] == 1
    assert viewer_row["selected"] is True
    assert viewer_row["routes"]["focus"].startswith("/explore?")
    assert "focus_node_id=document%3Aviewer-spec" in viewer_row["routes"]["focus"]
    assert viewer_row["routes"]["local"].startswith("/neighborhood?")
    assert "pivot_node_id=document%3Aviewer-spec" in viewer_row["routes"]["case"]
    assert "selected_node_ids=document%3Aviewer-spec" in viewer_row["routes"]["select"]
    assert provider_row["focused"] is True


def test_explore_screen_renders_relationship_data_table_routes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="document:viewer-spec",
            selected_edge_id="edge:preference-supports-spec",
        ),
    )

    table = _json_script_payload(html, "data-gf-relationship-data-table")
    selected_row = next(
        row for row in table["rows"] if row["id"] == "edge:preference-supports-spec"
    )
    provider_row = next(
        row for row in table["rows"] if row["id"] == "edge:provider-serves-spec"
    )

    assert "Visible edge rows make relationships inspectable" in html
    assert table["visible_node_count"] == 4
    assert table["visible_edge_count"] == 4
    assert table["selected_edge_id"] == "edge:preference-supports-spec"
    assert table["provider_boundary"].startswith(
        "GraphFakos lists visible relationship structure"
    )
    assert selected_row["source_label"] == "Operator Preference"
    assert selected_row["target_label"] == "Viewer Spec"
    assert selected_row["kind"] == "supports"
    assert selected_row["confidence"] == 0.9
    assert selected_row["provenance_count"] == 1
    assert selected_row["citation_count"] == 1
    assert selected_row["selected"] is True
    assert selected_row["routes"]["inspect"].startswith("/explore?")
    assert (
        "selected_edge_id=edge%3Apreference-supports-spec"
        in selected_row["routes"]["inspect"]
    )
    assert selected_row["routes"]["source"].startswith("/explore?")
    assert (
        "focus_node_id=memory%3Aoperator-preference" in selected_row["routes"]["source"]
    )
    assert selected_row["routes"]["target"].startswith("/explore?")
    assert "focus_node_id=document%3Aviewer-spec" in selected_row["routes"]["target"]
    assert selected_row["routes"]["path"].startswith("/path?")
    assert (
        "source_node_id=memory%3Aoperator-preference" in selected_row["routes"]["path"]
    )
    assert "target_node_id=document%3Aviewer-spec" in selected_row["routes"]["path"]
    assert "edge_kind=supports" in selected_row["routes"]["kind"]
    assert provider_row["source_label"] == "Third-party Provider"


def test_explore_screen_renders_navigation_map_lanes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="document:viewer-spec",
            selected_edge_id="edge:provider-serves-spec",
        ),
    )

    navigation_map = _json_script_payload(html, "data-gf-navigation-map")
    lanes = {lane["id"]: lane for lane in navigation_map["lanes"]}

    assert "Route-backed workbench lanes make screen changes" in html
    assert navigation_map["screen"] == "explore"
    assert navigation_map["focus_node_id"] == "document:viewer-spec"
    assert navigation_map["selected_edge_id"] == "edge:provider-serves-spec"
    assert navigation_map["visible_node_count"] == 4
    assert navigation_map["visible_edge_count"] == 4
    assert navigation_map["lane_count"] == 8
    assert navigation_map["provider_boundary"].startswith(
        "GraphFakos exposes route-backed navigation lanes"
    )
    assert lanes["global"]["route"].startswith("/explore?")
    assert "focus_node_id=" not in lanes["global"]["route"]
    assert lanes["local"]["route"].startswith("/neighborhood?")
    assert "focus_node_id=document%3Aviewer-spec" in lanes["local"]["route"]
    assert lanes["path"]["route"].startswith("/path?")
    assert "source_node_id=provider%3Athird-party" in lanes["path"]["route"]
    assert "target_node_id=document%3Aviewer-spec" in lanes["path"]["route"]
    assert "selected_edge_id=edge%3Aprovider-serves-spec" in lanes["path"]["route"]
    assert lanes["evidence"]["route"].startswith("/explore?")
    assert "query=has%3Aprovenance" in lanes["evidence"]["route"]
    assert "analytics_overlay=provenance" in lanes["evidence"]["route"]
    assert lanes["timeline"]["route"].startswith("/timeline?")
    assert "timeline_playback=step" in lanes["timeline"]["route"]
    assert lanes["case"]["route"].startswith("/explore?")
    assert "pivot_node_id=document%3Aviewer-spec" in lanes["case"]["route"]
    assert "pivot_mode=neighbors" in lanes["case"]["route"]
    assert lanes["path"]["shortcut_hint"] == "p"


def test_explore_screen_renders_interaction_guide_steps() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="document:viewer-spec",
            selected_edge_id="edge:provider-serves-spec",
            selected_node_ids=("provider:third-party",),
            camera_x=8,
            camera_y=-3,
            camera_zoom=1.25,
        ),
    )

    guide = _json_script_payload(html, "data-gf-interaction-guide")
    steps = {step["id"]: step for step in guide["steps"]}

    assert "Explore, select, and edit without losing the static fallback." in html
    assert guide["provider_id"] == "fixture"
    assert guide["screen"] == "explore"
    assert guide["focus_node_id"] == "document:viewer-spec"
    assert guide["selected_edge_id"] == "edge:provider-serves-spec"
    assert guide["visible_node_count"] == 4
    assert guide["visible_edge_count"] == 4
    assert guide["step_count"] == 6
    assert guide["fallback"]["static_svg"].startswith("Route links and GET forms")
    assert guide["fallback"]["local_preview"].startswith("JavaScript enhances")
    assert guide["provider_boundary"].startswith(
        "GraphFakos teaches viewer interactions"
    )
    assert steps["search"]["shortcut"] == "/ or Ctrl+K"
    assert steps["search"]["route"].startswith("/explore?")
    assert steps["camera"]["route"].startswith("/explore?")
    assert "camera_x=8" not in steps["camera"]["route"]
    assert steps["select"]["shortcut"] == "Shift-click / box"
    assert "selected_node_ids=provider%3Athird-party" in steps["select"]["route"]
    assert "selected_edge_id=edge%3Aprovider-serves-spec" in steps["select"]["route"]
    assert steps["local"]["route"].startswith("/neighborhood?")
    assert "focus_node_id=document%3Aviewer-spec" in steps["local"]["route"]
    assert "query=has%3Aprovenance" in steps["evidence"]["route"]
    assert "analytics_overlay=provenance" in steps["evidence"]["route"]
    assert steps["author"]["summary"].startswith("Use local preview forms")


def test_canvas_legend_explains_visible_styles_and_markers() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="document:viewer-spec",
            selected_node_ids=("provider:third-party",),
            selected_edge_id="edge:provider-serves-spec",
            style_color_by="component",
            style_size_by="degree",
            style_edge_width_by="confidence",
        ),
    )

    legend = _json_script_payload(html, "data-gf-canvas-legend")
    node_kinds = {item["value"]: item for item in legend["node_kinds"]}
    edge_kinds = {item["value"]: item for item in legend["edge_kinds"]}
    markers = {item["id"]: item for item in legend["markers"]}

    assert "Shapes, styles, and evidence markers" in html
    assert legend["visible_node_count"] == 4
    assert legend["visible_edge_count"] == 4
    assert legend["provider_boundary"].startswith(
        "GraphFakos explains visible structural styling"
    )
    assert node_kinds["document"]["count"] == 1
    assert node_kinds["document"]["route"].startswith("/explore?")
    assert "node_kind=document" in node_kinds["document"]["route"]
    assert edge_kinds["serves"]["count"] == 2
    assert edge_kinds["serves"]["route"].startswith("/explore?")
    assert "edge_kind=serves" in edge_kinds["serves"]["route"]
    assert markers["selected"]["count"] == 2
    assert markers["hub"]["count"] == 1
    assert markers["evidence"]["count"] == 3
    assert markers["pinned"]["meaning"].startswith("Dashed node outlines")
    assert legend["style_rules"] == {
        "color_by": "component",
        "edge_width_by": "confidence",
        "size_by": "degree",
    }


def test_explore_screen_renders_evidence_coverage_map() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(focus_node_id="document:viewer-spec"),
    )

    coverage = _json_script_payload(html, "data-gf-evidence-coverage-map")
    rows = {row["id"]: row for row in coverage["coverage_rows"]}

    assert "Visible provenance and citation coverage stays structural" in html
    assert coverage["visible_node_count"] == 4
    assert coverage["visible_edge_count"] == 4
    assert coverage["node_coverage"] == {
        "missing_any": 2,
        "missing_citation": 2,
        "missing_provenance": 2,
        "total": 4,
        "with_any": 2,
        "with_citation": 2,
        "with_provenance": 2,
    }
    assert coverage["edge_coverage"] == {
        "missing_any": 3,
        "missing_citation": 3,
        "missing_provenance": 3,
        "total": 4,
        "with_any": 1,
        "with_citation": 1,
        "with_provenance": 1,
    }
    assert coverage["gap_count"] == 5
    assert coverage["provider_boundary"].startswith(
        "GraphFakos reports declared evidence coverage only"
    )
    assert rows["nodes-with-provenance"]["count"] == 2
    assert rows["nodes-with-provenance"]["percent"] == 50
    assert "evidence_filter=with_provenance" in rows["nodes-with-provenance"]["route"]
    assert rows["nodes-missing-citation"]["count"] == 2
    assert "evidence_filter=missing_citation" in rows["nodes-missing-citation"]["route"]
    assert rows["edges-with-evidence"]["count"] == 1
    assert "query=has%3Aprovenance" in rows["edges-with-evidence"]["route"]
    assert "analytics_overlay=provenance" in rows["edges-with-evidence"]["route"]
    assert rows["edges-missing-evidence"]["route"].startswith("/provenance?")


def test_explore_screen_renders_selection_set_routes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="document:viewer-spec",
            selected_node_ids=("provider:third-party",),
            selected_edge_id="edge:provider-serves-spec",
        ),
    )

    payload = _json_script_payload(html, "data-gf-selection-sets")
    sets = {item["id"]: item for item in payload["sets"]}

    assert "Select visible" in html
    assert "Select focus component" in html
    assert payload["selected_node_ids"] == ["provider:third-party"]
    assert payload["visible_node_count"] == 4
    assert payload["visible_edge_count"] == 4
    assert payload["provider_boundary"].startswith(
        "Selection sets are GraphFakos viewer state only"
    )
    assert sets["visible"]["count"] == 4
    assert "selected_node_ids=memory%3Aoperator-preference" in sets["visible"]["route"]
    assert sets["hubs"]["node_ids"] == ["document:viewer-spec"]
    assert "selected_node_ids=document%3Aviewer-spec" in sets["hubs"]["route"]
    assert sets["evidence"]["count"] == 2
    assert "selected_node_ids=memory%3Aoperator-preference" in sets["evidence"]["route"]
    assert sets["focus-component"]["count"] == 4
    assert sets["focus-component"]["case_route"].startswith("/explore?")
    assert "pivot_mode=neighbors" in sets["focus-component"]["case_route"]
    assert "selected_node_ids=" not in sets["clear"]["route"]
    assert "selected_edge_id=" not in sets["clear"]["route"]


def test_explore_screen_renders_faceted_filter_routes() -> None:
    html = render_static_html(FixtureGraphProvider(), GraphFakosRequest())

    facets = _json_script_payload(html, "data-gf-facet-explorer")
    by_id = {facet["id"]: facet for facet in facets["facets"]}
    node_kind_items = {item["value"]: item for item in by_id["node_kind"]["items"]}
    evidence_items = {item["value"]: item for item in by_id["evidence_filter"]["items"]}
    degree_items = {item["value"]: item for item in by_id["degree"]["items"]}

    assert "Route-backed facets expose structural" in html
    assert facets["visible_node_count"] == 4
    assert facets["visible_edge_count"] == 4
    assert facets["provider_boundary"].startswith(
        "GraphFakos counts visible structural fields"
    )
    assert node_kind_items["document"]["count"] == 1
    assert node_kind_items["document"]["route"].startswith("/explore?")
    assert "node_kind=document" in node_kind_items["document"]["route"]
    assert by_id["source"]["items"][0]["value"] == "fixture"
    assert by_id["source"]["items"][0]["count"] == 4
    assert by_id["component_id"]["items"][0]["value"] == "component:1"
    assert by_id["component_id"]["items"][0]["count"] == 4
    assert evidence_items["with_provenance"]["count"] == 2
    assert (
        "evidence_filter=with_provenance" in evidence_items["with_provenance"]["route"]
    )
    assert degree_items["degree 1-2"]["count"] == 3
    assert degree_items["degree 3+"]["count"] == 1
    assert "min_degree=3" in degree_items["degree 3+"]["route"]


def test_explore_screen_renders_active_lens_reset_routes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            query="provider",
            focus_node_id="provider:third-party",
            selected_node_ids=("provider:third-party", "document:viewer-spec"),
            selected_edge_id="edge:provider-serves-spec",
            filters={"node_kind": "provider", "min_score": "0.8"},
            render_engine="canvas",
            theme="ink",
            camera_x=24,
            camera_y=-12,
            camera_zoom=1.4,
            min_degree=1,
            evidence_filter="with_provenance",
        ),
    )

    active_lens = _json_script_payload(html, "data-gf-active-lens")
    routes = active_lens["routes"]

    assert active_lens["screen"] == "explore"
    assert active_lens["query"] == "provider"
    assert active_lens["filters"]["node_kind"] == "provider"
    assert active_lens["focus_node_id"] == "provider:third-party"
    assert active_lens["selected_node_ids"] == [
        "provider:third-party",
        "document:viewer-spec",
    ]
    assert active_lens["selected_edge_id"] == "edge:provider-serves-spec"
    assert active_lens["render_engine"] == "canvas"
    assert active_lens["theme"] == "ink"
    assert active_lens["advanced_filters"] == {
        "evidence_filter": "with_provenance",
        "min_degree": 1,
    }
    assert routes["Clear query"].startswith("/explore?")
    assert "query=provider" not in routes["Clear query"]
    assert "node_kind=provider" not in routes["Clear filters"]
    assert "min_score=0.8" not in routes["Clear filters"]
    assert "evidence_filter=with_provenance" not in routes["Clear filters"]
    assert "focus_node_id=provider%3Athird-party" not in routes["Clear focus"]
    assert "selected_node_ids=" not in routes["Clear selection"]
    assert (
        "selected_edge_id=edge%3Aprovider-serves-spec" not in routes["Clear selection"]
    )
    assert "camera_x=24" not in routes["Reset camera"]
    assert routes["SVG fallback"].startswith("/explore?")
    assert "render_engine=svg" in routes["SVG fallback"]


def test_explore_screen_renders_display_recipe_routes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            preset_id="display-readable",
            focus_node_id="document:viewer-spec",
            render_limit=80,
        ),
    )

    payload = _json_script_payload(html, "data-gf-display-recipes")
    recipes = {recipe["id"]: recipe for recipe in payload["recipes"]}

    assert "Quick view recipes tune layout" in html
    assert payload["active_recipe_id"] == "display-readable"
    assert payload["visible_node_count"] == 4
    assert payload["visible_edge_count"] == 4
    assert payload["provider_boundary"].startswith(
        "Display recipes only change GraphFakos viewer state"
    )
    assert recipes["display-readable"]["active"] is True
    assert "edge_clutter=reduced" in recipes["display-readable"]["route"]
    assert "label_density=0.65" in recipes["display-readable"]["route"]
    assert recipes["display-dense"]["route"].startswith("/explore?")
    assert "render_engine=canvas" in recipes["display-dense"]["route"]
    assert "render_limit=240" in recipes["display-dense"]["route"]
    assert recipes["display-local"]["route"].startswith("/neighborhood?")
    assert "focus_node_id=document%3Aviewer-spec" in recipes["display-local"]["route"]
    assert "max_depth=1" in recipes["display-local"]["route"]
    assert "query=has%3Aprovenance" in recipes["display-evidence"]["route"]
    assert "analytics_overlay=provenance" in recipes["display-evidence"]["route"]
    assert recipes["display-timeline"]["route"].startswith("/timeline?")
    assert "timeline_playback=step" in recipes["display-timeline"]["route"]
    assert "theme=paper" in recipes["display-export"]["route"]
    assert "render_engine=svg" in recipes["display-export"]["route"]


def test_explore_screen_renders_provider_neutral_expansion_plan() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            focus_node_id="provider:third-party",
            max_depth=2,
            filters={"edge_kind": "serves", "node_kind": "provider"},
        ),
    )

    expansion_plan = _json_script_payload(html, "data-gf-expansion-plan")

    assert "Expansion Planner" in html
    assert "Preview Local Expansion" in html
    assert "providers or hosts own fetching" in html
    assert expansion_plan["status"] == "planned"
    assert expansion_plan["source_id"] == "provider:third-party"
    assert expansion_plan["source_label"] == "Third-party Provider"
    assert expansion_plan["depth"] == 2
    assert expansion_plan["edge_kind"] == "serves"
    assert expansion_plan["node_kind"] == "provider"
    assert expansion_plan["request"] == {
        "depth": 2,
        "edge_kind": "serves",
        "node_kind": "provider",
        "source_id": "provider:third-party",
    }
    assert expansion_plan["provider_boundary"].startswith(
        "GraphFakos plans the expansion request"
    )
    assert expansion_plan["suggestions"][0]["id"] == "provider:third-party"
    assert expansion_plan["suggestions"][0]["request"]["source_id"] == (
        "provider:third-party"
    )
    assert expansion_plan["suggestions"][0]["local_route"].startswith("/neighborhood?")
    assert expansion_plan["suggestions"][0]["deeper_route"].startswith("/neighborhood?")
    assert expansion_plan["suggestions"][0]["case_route"].startswith("/explore?")


def test_explore_screen_renders_readability_coach_suggestions() -> None:
    html = render_static_html(
        DemoGraphProvider("dense"),
        GraphFakosRequest(
            screen="explore",
            render_limit=20,
            edge_clutter="normal",
            label_density=1,
            edge_opacity=1,
            render_engine="svg",
        ),
    )

    coach = _json_script_payload(html, "data-gf-readability-coach")
    suggestion_ids = {item["id"] for item in coach["suggestions"]}

    assert "Readability Coach" in html
    assert "Structural display checks suggest route-backed tuning" in html
    assert coach["status"] == "needs_tuning"
    assert coach["visible_node_count"] == 20
    assert coach["metrics"]["hidden_nodes"] == 16
    assert coach["metrics"]["edge_clutter"] == "normal"
    assert "increase-render-budget" in suggestion_ids
    assert "reduce-edge-clutter" in suggestion_ids
    assert "lower-label-density" in suggestion_ids
    assert "soften-edges" in suggestion_ids
    assert any(
        suggestion["route"].startswith("/explore?")
        and "edge_clutter=reduced" in suggestion["route"]
        for suggestion in coach["suggestions"]
    )


def test_demo_viewer_marks_workbench_editor_capabilities_supported() -> None:
    html = render_static_html(
        DemoGraphProvider(),
        GraphFakosRequest(screen="explore", focus_node_id="agent:codex"),
    )

    assert "Capture supported" in html
    assert "Actions supported" in html
    assert "data-gf-knowledge-form='true' data-gf-capability-supported='true'" in html
    assert "data-gf-action-form='true' data-gf-capability-supported='true'" in html
    assert "Current provider does not advertise" not in html
    assert "<button type='submit'>Add to graph</button>" in html
    assert "<button type='submit'>Queue action</button>" in html


def test_graph_authoring_defaults_follow_selected_nodes() -> None:
    html = render_static_html(
        DemoGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            selected_node_ids=(
                "agent:codex",
                "document:dynamic-viewer-spec",
            ),
        ),
    )

    assert "data-gf-action-form='true' data-gf-capability-supported='true'" in html
    assert "name='viewer_context'" in html
    assert "Submission Context" in html
    assert (
        "&quot;selected_node_ids&quot;:[&quot;agent:codex&quot;,&quot;document:dynamic-viewer-spec&quot;]"
        in html
    )
    assert "<option value='draft_edge' selected>Draft edge</option>" in html
    assert "<option value='agent:codex' selected>Codex Agent</option>" in html
    assert (
        "<option value='document:dynamic-viewer-spec' selected>Dynamic Viewer Spec</option>"
        in html
    )
    action = _json_script_payload(html, "data-gf-action-template")
    assert action["action_type"] == "draft_edge"
    assert action["target_id"] == "agent:codex"
    assert action["source_id"] == "agent:codex"
    assert action["target_node_id"] == "document:dynamic-viewer-spec"


def test_graph_authoring_context_preview_reflects_filtered_route_state() -> None:
    html = render_static_html(
        DemoGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            query="kind:document",
            filters={"node_kind": "document"},
            camera_x=12.0,
            camera_y=-4.0,
            camera_zoom=1.4,
            selected_node_ids=(
                "agent:codex",
                "document:dynamic-viewer-spec",
            ),
        ),
    )

    assert "data-gf-viewer-context-preview='true'" in html
    assert "explore: kind:document" in html
    assert "agent:codex, Dynamic Viewer Spec" in html
    assert "x=12.0, y=-4.0, zoom=1.40" in html
    assert "force / svg / default" in html
    assert "node_kind=document" in html


def test_graph_authoring_defaults_follow_selected_edge() -> None:
    html = render_static_html(
        DemoGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            selected_edge_id="edge:agent-observes-session",
        ),
    )

    assert "<option value='agent:codex' selected>Codex Agent</option>" in html
    assert (
        "<option value='session:design-review' selected>Design Review Session</option>"
        in html
    )
    assert "<option value='draft_edge' selected>Draft edge</option>" in html
    action = _json_script_payload(html, "data-gf-action-template")
    assert action["action_type"] == "draft_edge"
    assert action["source_id"] == "agent:codex"
    assert action["target_node_id"] == "session:design-review"


def test_static_viewer_renders_structural_case_packet_payload() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            pivot_node_id="document:viewer-spec",
            pivot_mode="paths",
        ),
    )

    payload = _json_script_payload(html, "data-gf-investigation-case")

    assert "Viewer Spec" in html
    assert "updated_at: 2026-06-21T09:30:00+00:00" in html
    assert payload["status"] == "ready"
    assert payload["pivot_node_id"] == "document:viewer-spec"
    assert payload["pivot_label"] == "Viewer Spec"
    assert payload["pivot_kind"] == "document"
    assert payload["pivot_mode"] == "paths"
    assert payload["metrics"]["degree"] == 3
    assert payload["metrics"]["neighbors"] == 3
    assert payload["metrics"]["timeline_events"] == 1
    assert payload["neighbors"][0]["route"].startswith("/explore?")
    assert payload["path_targets"][0]["route"].startswith("/path?")
    assert payload["evidence_bundle"]["provenance_ids"] == ["prov:fixture"]
    assert payload["evidence_bundle"]["citation_ids"] == ["cite:provider-doc"]
    assert payload["timeline_events"] == [
        {"field": "updated_at", "value": "2026-06-21T09:30:00+00:00"}
    ]


def test_static_viewer_minimap_marks_nodes_for_navigation() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(focus_node_id="provider:third-party"),
    )

    assert "aria-label='Graph minimap'" in html
    assert "aria-label='Focus minimap node Third-party Provider'" in html
    assert "data-minimap-node-id='provider:third-party'" in html
    assert "data-node-ref='provider:third-party'" in html
    assert "data-focus-route=" in html
    assert ".gf-minimap-node-link:focus-visible" in html
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
    assert "class='gf-minimap-viewport'" in html
    assert "data-camera-x='12.50' data-camera-y='-4.00' data-camera-zoom='1.40'" in html
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
    assert "Relationship Trail" in html
    assert "data-gf-relationship-trail='true'" in html
    assert "Nearest Hops" in html
    assert "Path Targets" in html
    assert "Search Results" in html
    search_results = _json_script_payload(html, "data-gf-search-results")
    assert search_results["query"] == "provider"
    assert search_results["mode"] == "query_matches"
    assert search_results["visible_node_count"] == 1
    assert search_results["results"][0]["id"] == "provider:third-party"
    assert search_results["results"][0]["focus_route"].startswith("/explore?")
    assert search_results["results"][0]["local_route"].startswith("/neighborhood?")
    assert search_results["results"][0]["evidence_route"].startswith("/provenance?")


def test_explore_screen_renders_relationship_trail_routes() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(focus_node_id="provider:third-party"),
    )

    assert "Relationship Trail" in html
    assert ">Focus</a>" in html
    assert ">Local</a>" in html
    assert ">Path</a>" in html
    trail = _json_script_payload(html, "data-gf-relationship-trail")
    assert trail["focus_id"] == "provider:third-party"
    assert trail["neighbors"][0]["path_route"].startswith("/path?")
    assert trail["path_targets"][0]["hop_count"] >= 1


def test_explore_screen_renders_search_result_path_routes_from_visible_graph() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            query="Viewer",
            focus_node_id="provider:third-party",
        ),
    )

    search_results = _json_script_payload(html, "data-gf-search-results")

    assert search_results["focus_id"] == "provider:third-party"
    assert search_results["visible_node_count"] == 1
    assert search_results["results"][0]["id"] == "document:viewer-spec"
    assert search_results["results"][0]["path_route"] is None


def test_explore_screen_renders_search_result_path_routes_when_focus_is_visible() -> (
    None
):
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(focus_node_id="provider:third-party"),
    )

    search_results = _json_script_payload(html, "data-gf-search-results")
    path_routes = [
        result["path_route"]
        for result in search_results["results"]
        if result["id"] != "provider:third-party"
    ]

    assert any(route and route.startswith("/path?") for route in path_routes)


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


def test_timeline_screen_renders_route_backed_event_workbench() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="timeline",
            timeline_frame="2026-06-21T09:30:00+00:00",
            timeline_playback="step",
        ),
    )

    payload = _json_script_payload(html, "data-gf-timeline-events")

    assert "Timeline and Freshness" in html
    assert "data-gf-timeline-rail='true'" in html
    assert "data-gf-timeline-cards='true'" in html
    assert "Open frame" in html
    assert "Timeline case packet" in html
    assert payload["selected_frame"] == "2026-06-21T09:30:00+00:00"
    assert payload["playback"] == "step"
    assert len(payload["events"]) == 1
    event = payload["events"][0]
    assert event["field"] == "updated_at"
    assert event["kind"] == "document"
    assert event["label"] == "Viewer Spec"
    assert event["node_id"] == "document:viewer-spec"
    assert event["value"] == "2026-06-21T09:30:00+00:00"
    assert event["route"].startswith("/timeline?")
    assert "timeline_frame=2026-06-21T09%3A30%3A00%2B00%3A00" in event["route"]
    assert event["focus_route"].startswith("/explore?")
    assert "focus_node_id=document%3Aviewer-spec" in event["focus_route"]
    assert event["case_packet_route"].startswith("/explore?")
    assert "pivot_node_id=document%3Aviewer-spec" in event["case_packet_route"]
    assert "pivot_mode=timeline" in event["case_packet_route"]


def test_diff_screen_renders_snapshot_comparison() -> None:
    html = render_static_html(
        FixtureGraphProvider(),
        GraphFakosRequest(screen="diff"),
    )
    payload = _json_script_payload(html, "data-gf-diff-workbench")

    assert "Snapshot Diff" in html
    assert "Fixture Baseline" in html
    assert "Added nodes" in html
    assert "Changed nodes" in html
    assert "Change Hotspots" in html
    assert "Snapshot changes" in html
    assert "Overlay Providers" in html
    assert "data-gf-diff-workbench='true'" in html
    assert "data-gf-diff-cards='true'" in html
    assert "Diff Review Workbench" in html
    assert "Review change" in html
    assert "Case packet" in html
    assert payload["current_graph_id"] == "fixture"
    assert payload["comparison_graph_id"] == "fixture-baseline"
    assert any(change["change_type"] == "added_node" for change in payload["changes"])
    assert any(change["change_type"] == "added_edge" for change in payload["changes"])
    assert any(change["change_type"] == "snapshot" for change in payload["changes"])
    added_node = next(
        change for change in payload["changes"] if change["change_type"] == "added_node"
    )
    assert added_node["id"] == "artifact:static-export"
    assert added_node["route"].startswith("/explore?")
    assert added_node["case_packet_route"].startswith("/explore?")


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
