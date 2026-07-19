from __future__ import annotations

import pytest

from graphfakos import (
    FixtureGraphProvider,
    build_graph_report,
    build_graph_replay_bundle,
    build_fixture_graph,
    build_viewer_route,
    GraphFakosActionStatus,
    GraphFakosCameraPose,
    GraphFakosEdge,
    GraphFakosExpansionRequest,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosGraphAnalytics,
    GraphFakosKnowledgeCapture,
    GraphFakosNode,
    GraphFakosReplayBundle,
    GraphFakosRequest,
    GraphFakosSavedQuery,
    GraphFakosSavedView,
    GraphFakosTheme,
    GraphFakosViewerCommand,
    GraphFakosViewerEvent,
    GraphFakosViewerState,
    analyze_graph,
    diagnose_graph,
    load_comparison_graph,
    load_overlay_graphs,
    load_provider_graph,
    parse_viewer_request,
    query_syntax_reference,
    render_graph_dot,
    render_static_html,
    review_preset_manifest,
    SUPPORTED_RENDER_ENGINES,
    validate_graph,
    validate_render_engine,
)
from graphfakos.testing import assert_graph_dot_contract, assert_review_preset_contract


def test_fixture_provider_satisfies_provider_contract() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())

    assert graph.provider_id == "fixture"
    assert graph.graph_role == "third_party"
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 4
    assert graph.provenance
    assert graph.citations
    assert graph.provider_details["owner"] == "OpenMinion fixture"
    assert "diff" in graph.capability_details
    assert graph.snapshot is not None
    assert graph.snapshot.snapshot_id == "fixture-current"


def test_validate_graph_rejects_unknown_edge_references() -> None:
    graph = GraphFakosGraph(
        graph_id="bad",
        label="Bad Graph",
        provider_id="bad",
        provider_label="Bad Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(GraphFakosNode(id="known", label="Known", kind="node"),),
        edges=(
            GraphFakosEdge(
                id="bad-edge",
                source_id="known",
                target_id="missing",
                kind="bad",
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown target"):
        validate_graph(graph)


def test_validate_graph_rejects_duplicate_edge_ids() -> None:
    graph = GraphFakosGraph(
        graph_id="bad",
        label="Bad Graph",
        provider_id="bad",
        provider_label="Bad Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(id="one", label="One", kind="node"),
            GraphFakosNode(id="two", label="Two", kind="node"),
        ),
        edges=(
            GraphFakosEdge(
                id="duplicate",
                source_id="one",
                target_id="two",
                kind="relates",
            ),
            GraphFakosEdge(
                id="duplicate",
                source_id="two",
                target_id="one",
                kind="relates",
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate edge ids"):
        validate_graph(graph)


def test_diagnose_graph_reports_provider_neutral_health() -> None:
    graph = GraphFakosGraph(
        graph_id="diagnostic",
        label="Diagnostic Graph",
        provider_id="diagnostic",
        provider_label="Diagnostic Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(
                id="one",
                label="One",
                kind="node",
                provenance_ids=("missing-provenance",),
            ),
            GraphFakosNode(id="two", label="Two", kind="node"),
            GraphFakosNode(
                id="orphan",
                label="Orphan",
                kind="node",
                citation_ids=("missing-citation",),
            ),
        ),
        edges=(
            GraphFakosEdge(
                id="edge",
                source_id="one",
                target_id="two",
                kind="relates",
            ),
        ),
        warnings=("provider warning",),
    )

    diagnostics = diagnose_graph(graph)

    assert diagnostics.healthy is False
    assert diagnostics.orphan_node_ids == ("orphan",)
    assert diagnostics.unknown_provenance_ids == ("missing-provenance",)
    assert diagnostics.unknown_citation_ids == ("missing-citation",)
    assert diagnostics.disconnected_node_ids == ("orphan",)
    assert diagnostics.to_dict()["warnings"] == ["provider warning"]


def test_graph_to_dict_is_provider_neutral() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    payload = graph.to_dict()

    assert payload["provider_id"] == "fixture"
    assert payload["graph_role"] == "third_party"
    assert len(payload["nodes"]) == 4
    assert len(payload["edges"]) == 4
    assert payload["available_facets"]["node_kind"] == [
        "artifact",
        "document",
        "memory",
        "provider",
    ]


def test_fixture_provider_exposes_comparison_and_overlay_graphs() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="diff")

    comparison = load_comparison_graph(provider, request)
    overlays = load_overlay_graphs(provider, request)

    assert comparison is not None
    assert comparison.provider_label == "Fixture Baseline"
    assert len(comparison.nodes) == 3
    assert overlays
    assert overlays[0].provider_label == "Overlay Provider"


def test_build_graph_report_includes_overlay_and_comparison() -> None:
    report = build_graph_report(
        FixtureGraphProvider(), GraphFakosRequest(screen="diff")
    )

    assert report["diagnostics"]["healthy"] is True
    assert report["comparison_graph"]["provider_label"] == "Fixture Baseline"
    assert report["comparison_diff"]["summary"]["changed node count"] == 0
    assert report["overlay_graphs"][0]["provider_label"] == "Overlay Provider"
    assert report["request"]["screen"] == "diff"
    assert report["viewer_state"]["screen"] == "diff"
    assert report["graph"]["snapshot"]["snapshot_id"] == "fixture-current"


def test_viewer_route_helpers_are_public_and_stable() -> None:
    request = GraphFakosRequest(
        screen="diff",
        preset_id="diff",
        query="kind:file has:provenance",
        focus_node_id="node:one",
        comparison_graph_id="baseline",
        render_limit=80,
        camera_x=11.25,
        camera_y=-3.5,
        camera_zoom=1.3,
        camera_yaw=18.0,
        camera_pitch=-9.0,
        camera_pose=GraphFakosCameraPose(
            position=(120.0, -42.5, 780.25),
            target=(18.0, 4.5, -9.0),
        ),
        center_force=0.0,
        label_density=0.0,
    )

    route = build_viewer_route(request)
    parsed = parse_viewer_request(
        "/diff",
        {
            "preset": ["diff"],
            "query": ["kind:file has:provenance"],
            "focus_node_id": ["node:one"],
            "comparison_graph_id": ["baseline"],
            "render_limit": ["80"],
            "camera_x": ["11.25"],
            "camera_y": ["-3.5"],
            "camera_zoom": ["1.3"],
            "camera_yaw": ["18"],
            "camera_pitch": ["-9"],
            "camera_pose": ["120,-42.5,780.25,18,4.5,-9"],
            "center_force": ["0"],
            "label_density": ["0"],
        },
    )

    assert route.startswith("/diff?")
    assert parsed.screen == "diff"
    assert parsed.preset_id == "diff"
    assert parsed.comparison_graph_id == "baseline"
    assert parsed.render_limit == 80
    assert parsed.camera_x == 11.25
    assert parsed.camera_y == -3.5
    assert parsed.camera_zoom == 1.3
    assert parsed.camera_yaw == 18.0
    assert parsed.camera_pitch == -9.0
    assert parsed.camera_pose == request.camera_pose
    assert parsed.center_force == 0.0
    assert parsed.label_density == 0.0
    assert "center_force=0.0" in route
    assert "label_density=0.0" in route
    assert "camera_pose=120.000000%2C-42.500000%2C780.250000" in route


@pytest.mark.parametrize(
    "value",
    (
        "nan,0,1,2,3,4",
        "0,inf,1,2,3,4",
        "0,1,2,3,4",
    ),
)
def test_camera_pose_rejects_invalid_route_values(value: str) -> None:
    with pytest.raises(ValueError):
        GraphFakosCameraPose.from_query_value(value)

    fallback = GraphFakosCameraPose(
        position=(0.0, 0.0, 720.0),
        target=(0.0, 0.0, 0.0),
    )
    parsed = parse_viewer_request(
        "/explore",
        {"camera_pose": [value]},
        base_request=GraphFakosRequest(camera_pose=fallback),
    )
    assert parsed.camera_pose == fallback


def test_camera_pose_rejects_non_finite_direct_values() -> None:
    with pytest.raises(ValueError, match="must be finite"):
        GraphFakosCameraPose(
            position=(0.0, float("nan"), 720.0),
            target=(0.0, 0.0, 0.0),
        )


def test_focused_request_normalizes_focus_as_primary_selection() -> None:
    state = GraphFakosViewerState.from_request(
        GraphFakosRequest(
            focus_node_id="provider:third-party",
            selected_node_ids=("memory:operator-preference",),
        )
    )

    assert state.selected_node_id == "provider:third-party"
    assert state.selected_node_ids == (
        "provider:third-party",
        "memory:operator-preference",
    )


def test_dynamic_viewer_contracts_round_trip() -> None:
    request = GraphFakosRequest(
        screen="explore",
        focus_node_id="provider:third-party",
        selected_edge_id="edge:provider-serves-spec",
        layout="radial",
        filters={"node_kind": "provider"},
        camera_x=4.5,
        camera_y=-2.0,
        camera_zoom=1.4,
        camera_yaw=24.0,
        camera_pitch=-16.0,
        camera_pose=GraphFakosCameraPose(
            position=(64.0, -18.0, 640.0),
            target=(12.0, 8.0, -4.0),
        ),
        selected_node_ids=("provider:third-party", "memory:operator-preference"),
        center_force=0.02,
        repel_force=1.4,
        link_distance=1.2,
        node_scale=1.15,
        edge_scale=1.25,
        edge_opacity=0.75,
        label_density=0.6,
        pinned_positions={"provider:third-party": (320.0, 180.0)},
        style_color_by="component",
        style_size_by="degree",
        style_edge_width_by="weight",
        min_degree=1,
        component_id="component:1",
        connected_to_node_id="provider:third-party",
        evidence_filter="with_provenance",
        timeline_frame="2026-06-25",
        timeline_playback="step",
        pivot_node_id="provider:third-party",
        pivot_mode="evidence_bundle",
    )

    state = GraphFakosViewerState.from_request(request)
    rebuilt_state = GraphFakosViewerState.from_dict(state.to_dict())
    command = GraphFakosViewerCommand(
        name="filter",
        target_id="node_kind",
        payload={"value": "provider"},
    )
    event = GraphFakosViewerEvent(
        name="graphfakos:filter",
        state=rebuilt_state,
        target_id="node_kind",
        payload={"value": "provider"},
    )
    expansion = GraphFakosExpansionRequest(
        source_id="provider:third-party", depth=2, cursor="expand:provider:2"
    )
    theme = GraphFakosTheme(
        id="review",
        label="Review",
        node_colors={"provider": "#0f766e"},
        edge_colors={"serves": "#64748b"},
        node_shapes={"provider": "square"},
    )

    assert rebuilt_state.selected_node_id == "provider:third-party"
    assert rebuilt_state.selected_node_ids == (
        "provider:third-party",
        "memory:operator-preference",
    )
    assert rebuilt_state.pinned_positions["provider:third-party"] == (320.0, 180.0)
    assert rebuilt_state.style_color_by == "component"
    assert rebuilt_state.camera_yaw == 24.0
    assert rebuilt_state.camera_pitch == -16.0
    assert rebuilt_state.camera_pose == request.camera_pose
    assert rebuilt_state.timeline_playback == "step"
    assert rebuilt_state.pivot_mode == "evidence_bundle"
    assert rebuilt_state.to_route_query()["node_kind"] == "provider"
    assert GraphFakosViewerCommand.from_dict(command.to_dict()).payload == {
        "value": "provider"
    }
    assert GraphFakosViewerEvent.from_dict(event.to_dict()).state.camera_zoom == 1.4
    assert GraphFakosViewerEvent.from_dict(event.to_dict()).state.camera_yaw == 24.0
    assert (
        GraphFakosViewerEvent.from_dict(event.to_dict()).state.camera_pose
        == request.camera_pose
    )
    assert GraphFakosExpansionRequest.from_dict(expansion.to_dict()).depth == 2
    assert (
        GraphFakosExpansionRequest.from_dict(expansion.to_dict()).cursor
        == "expand:provider:2"
    )
    assert "node color provider: #0f766e" in theme.caption()


def test_knowledge_capture_contract_round_trips_provider_payload() -> None:
    capture = GraphFakosKnowledgeCapture(
        text="Remember that graph navigation needs local depth controls.",
        kind="note",
        tags=("ui", "graph"),
        source="workbench",
        link_node_id="provider:third-party",
        link_edge_kind="mentions",
        provider_payload={"screen": "explore"},
    )

    rebuilt = GraphFakosKnowledgeCapture.from_dict(capture.to_dict())
    parsed_tags = GraphFakosKnowledgeCapture.from_dict(
        {
            "text": "Comma tags are accepted from lightweight clients.",
            "tags": "one, two",
        }
    )

    assert rebuilt.text.startswith("Remember")
    assert rebuilt.tags == ("ui", "graph")
    assert rebuilt.provider_payload["screen"] == "explore"
    assert parsed_tags.tags == ("one", "two")


def test_saved_view_action_analytics_and_replay_contracts_round_trip() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    request = GraphFakosRequest(
        screen="neighborhood",
        focus_node_id="provider:third-party",
        saved_view_id="ops-review",
        render_engine="canvas",
        theme="ink",
        show_orphans=False,
        show_neighbor_links=False,
        edge_clutter="reduced",
        analytics_overlay="degree",
        pinned_positions={"provider:third-party": (310.0, 220.0)},
        selected_node_ids=("provider:third-party",),
        style_color_by="source",
        style_size_by="degree",
        style_edge_width_by="weight",
    )
    saved_query = GraphFakosSavedQuery(
        query_id="hubs",
        label="Find hubs",
        query="degree>=3",
    )
    saved_view = GraphFakosSavedView.from_request(
        request,
        view_id="ops-review",
        label="Operator review",
        saved_queries=(saved_query,),
    )
    action = GraphFakosGraphAction(
        action_id="draft:one",
        action_type="merge_alias",
        target_id="provider:third-party",
        label="Merge provider aliases",
    )
    status = GraphFakosActionStatus(
        action_id=action.action_id,
        status="queued",
        message="Queued for provider review.",
    )
    analytics = analyze_graph(graph)
    bundle = GraphFakosReplayBundle(
        bundle_id="fixture:ops-review",
        graph=graph,
        viewer_state=GraphFakosViewerState.from_request(request),
        saved_views=(saved_view,),
        analytics=analytics,
    )

    rebuilt_view = GraphFakosSavedView.from_dict(saved_view.to_dict())
    assert rebuilt_view.state.theme == "ink"
    assert rebuilt_view.state.show_orphans is False
    assert rebuilt_view.pinned_positions["provider:third-party"] == (310.0, 220.0)
    assert rebuilt_view.state.selected_node_ids == ("provider:third-party",)
    assert rebuilt_view.state.style_edge_width_by == "weight"
    assert (
        GraphFakosGraphAction.from_dict(action.to_dict()).action_type == "merge_alias"
    )
    assert GraphFakosActionStatus.from_dict(status.to_dict()).status == "queued"
    assert GraphFakosGraphAnalytics.from_dict(analytics.to_dict()).node_count == 4
    rebuilt_bundle = GraphFakosReplayBundle.from_dict(bundle.to_dict())
    assert rebuilt_bundle.viewer_state.render_engine == "canvas"
    assert rebuilt_bundle.saved_views[0].saved_queries[0].query == "degree>=3"


def test_build_graph_replay_bundle_uses_provider_neutral_state() -> None:
    bundle = build_graph_replay_bundle(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            focus_node_id="provider:third-party",
            saved_view_id="route-share",
            theme="paper",
            analytics_overlay="warnings",
        ),
    )

    assert bundle.bundle_id == "fixture:explore"
    assert bundle.viewer_state.theme == "paper"
    assert bundle.saved_views[0].view_id == "route-share"
    assert bundle.analytics.hub_node_ids


def test_renderer_selection_contract_rejects_unsupported_engines() -> None:
    assert SUPPORTED_RENDER_ENGINES == ("svg", "canvas", "3d")
    assert validate_render_engine("svg") == "svg"
    assert validate_render_engine("canvas") == "canvas"
    assert validate_render_engine("3d") == "3d"

    with pytest.raises(ValueError, match="unsupported GraphFakos render engine"):
        validate_render_engine("webgl")


def test_review_preset_manifest_exposes_shared_review_flows() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="explore", focus_node_id="provider:third-party")
    graph = load_provider_graph(provider, request)
    comparison = load_comparison_graph(provider, GraphFakosRequest(screen="diff"))

    presets = review_preset_manifest(
        graph,
        request,
        comparison_graph=comparison,
    )

    assert_review_preset_contract(
        presets,
        required_ids=("overview", "focus", "evidence", "diff", "health", "context"),
    )


def test_render_graph_dot_exports_provider_neutral_edges() -> None:
    graph = build_fixture_graph()

    dot = render_graph_dot(graph)

    assert_graph_dot_contract(
        dot,
        expected_node_ids=("provider:third-party", "artifact:static-export"),
        expected_edge_ids=("serves", "supports"),
    )


def test_query_syntax_reference_documents_tokens() -> None:
    syntax = query_syntax_reference()

    assert any(item["token"] == "kind:<value>" for item in syntax)
    assert any(item["token"] == "has:provenance" for item in syntax)
    assert any(item["token"] == "score>=0.8" for item in syntax)
    assert any(item["token"] == '"quoted phrase"' for item in syntax)


def test_custom_provider_can_render_all_shared_screens() -> None:
    class CustomProvider:
        provider_id = "custom"
        provider_label = "Custom Provider"
        graph_role = "third_party"
        capabilities = (
            "search",
            "neighborhood",
            "path",
            "provenance",
            "timeline",
            "provider_status",
            "context_preview",
            "static_export",
        )

        def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
            return GraphFakosGraph(
                graph_id="custom",
                label="Custom Graph",
                provider_id=self.provider_id,
                provider_label=self.provider_label,
                graph_role=self.graph_role,
                capabilities=self.capabilities,
                nodes=(
                    GraphFakosNode(
                        id="one",
                        label="One",
                        kind="record",
                        summary="First custom node.",
                        score=0.9,
                        source="custom",
                    ),
                    GraphFakosNode(
                        id="two",
                        label="Two",
                        kind="record",
                        summary="Second custom node.",
                        score=0.8,
                        source="custom",
                    ),
                ),
                edges=(
                    GraphFakosEdge(
                        id="one-two",
                        source_id="one",
                        target_id="two",
                        kind="connects",
                        label="connects",
                    ),
                ),
                provider_payload={
                    "integration_summary": "Custom provider preview.",
                    "integration_commands": ("python -m custom_graph preview --serve",),
                },
            )

    for screen in (
        "explore",
        "neighborhood",
        "path",
        "provenance",
        "timeline",
        "diff",
        "provider_status",
        "context_preview",
    ):
        html = render_static_html(CustomProvider(), GraphFakosRequest(screen=screen))
        assert "Custom Provider" in html
        assert "Integration Commands" in html
