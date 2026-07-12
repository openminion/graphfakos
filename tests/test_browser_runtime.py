from __future__ import annotations

import json
import shutil
import subprocess

from graphfakos.browser import viewer_runtime_script


def test_packaged_runtime_applies_live_patches_without_resetting_view_state() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for the browser runtime harness"
    script = (
        viewer_runtime_script()
        + """
const runtime = globalThis.GraphFakosViewerRuntime;
const graph = {
  nodes: [{ id: "a", label: "A", kind: "item" }],
  edges: [],
  provider_payload: {}
};
const state = runtime.normalizeState({
  camera_x: 12,
  camera_y: -4,
  camera_zoom: 1.5,
  filters: { kind: "item" },
  selected_node_id: "a",
  selected_node_ids: ["a"],
  live_revision: "0"
});
const patch = {
  patch_id: "patch-1",
  base_revision: { value: "0" },
  result_revision: { value: "1" },
  cursor: { value: "cursor-1" },
  operations: [
    { kind: "node_upsert", node: { id: "b", label: "B", kind: "item" } },
    { kind: "edge_upsert", edge: { id: "ab", source_id: "a", target_id: "b", kind: "related" } }
  ]
};
const result = runtime.applyGraphPatch(graph, state, patch);
const duplicate = runtime.applyGraphPatch(result.graph, result.state, patch);
console.log(JSON.stringify({ result, duplicate }));
"""
    )
    completed = subprocess.run(
        [node, "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert [node["id"] for node in payload["result"]["graph"]["nodes"]] == ["a", "b"]
    assert payload["result"]["graph"]["edges"][0]["id"] == "ab"
    assert payload["result"]["state"]["camera_x"] == 12
    assert payload["result"]["state"]["filters"] == {"kind": "item"}
    assert payload["result"]["state"]["live_revision"] == "1"
    assert payload["duplicate"]["applied"] is False


def test_packaged_viewer_runtime_reducer_runs_in_node() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for the browser runtime harness"
    assert "submitKnowledge" in viewer_runtime_script()
    assert "knowledge-saved" in viewer_runtime_script()
    assert "submitAction" in viewer_runtime_script()
    assert "action-saved" in viewer_runtime_script()
    assert "Refreshing graph..." in viewer_runtime_script()
    assert "source_id" in viewer_runtime_script()
    assert "target_node_id" in viewer_runtime_script()
    assert "splitList" in viewer_runtime_script()
    assert "pointerdown" in viewer_runtime_script()
    assert "mousedown" in viewer_runtime_script()
    assert "wheel" in viewer_runtime_script()
    assert "dblclick" in viewer_runtime_script()
    assert "data-gf-pin='reset'" in viewer_runtime_script()
    assert "gf-selection-box" in viewer_runtime_script()
    assert "nodeInspectPayload" in viewer_runtime_script()
    assert "inspect-open" in viewer_runtime_script()
    assert "edit-command" in viewer_runtime_script()
    assert "draft_note" in viewer_runtime_script()
    assert "lastCommand" in viewer_runtime_script()
    assert "contextmenu" in viewer_runtime_script()
    assert "surface-menu" in viewer_runtime_script()
    assert "Copy node ID" in viewer_runtime_script()
    assert "Trace path" in viewer_runtime_script()
    assert "Case packet" in viewer_runtime_script()
    assert "ContextMenu" in viewer_runtime_script()
    assert "F10" in viewer_runtime_script()
    assert "keyboardShortcuts" in viewer_runtime_script()
    assert "fittedCameraState" in viewer_runtime_script()
    assert "minimapViewportRect" in viewer_runtime_script()
    assert "isGraphSearchShortcut" in viewer_runtime_script()
    assert "search-focus" in viewer_runtime_script()
    assert "minimap-select" in viewer_runtime_script()
    assert "selectionStatusText" in viewer_runtime_script()
    assert "clear-selection" in viewer_runtime_script()
    assert "viewerContext" in viewer_runtime_script()
    assert "viewerContextRows" in viewer_runtime_script()
    assert "authoringDefaults" in viewer_runtime_script()
    assert "updateWorkbenchForms" in viewer_runtime_script()
    assert "captureTemplatePayload" in viewer_runtime_script()
    assert "Template selected:" in viewer_runtime_script()
    assert "workbookSlotPayload" in viewer_runtime_script()
    assert "workbook-saved" in viewer_runtime_script()
    assert "graphfakos:viewer-workbook:v1" in viewer_runtime_script()
    assert "graphfakos:viewer-theme:v1" in viewer_runtime_script()
    assert "curvedEdgePath" in viewer_runtime_script()
    assert "projectPoint3D" in viewer_runtime_script()
    assert "apply3DProjection" in viewer_runtime_script()
    assert "detailMode" in viewer_runtime_script()
    assert "applyDetailMode" in viewer_runtime_script()
    assert "camera_yaw" in viewer_runtime_script()
    assert "camera_pitch" in viewer_runtime_script()
    assert "pin-many" in viewer_runtime_script()
    assert "group-show-all" in viewer_runtime_script()
    assert "commandPaletteActionMatches" in viewer_runtime_script()
    assert "command-palette-filtered" in viewer_runtime_script()
    script = (
        viewer_runtime_script()
        + """
const runtime = globalThis.GraphFakosViewerRuntime;
let state = runtime.normalizeState({
  camera_zoom: 9,
  filters: { node_kind: "provider" },
  render_engine: "canvas",
  theme: "ink",
  show_orphans: "false",
  show_neighbor_links: "false",
  edge_clutter: "reduced",
  analytics_overlay: "degree"
});
state = runtime.reduce(state, { name: "select-node", target_id: "provider:third-party" });
state = runtime.reduce(state, { name: "select-node", target_id: "memory:operator-preference", payload: { additive: true } });
state = runtime.reduce(state, { name: "pin-node", target_id: "provider:third-party", payload: { x: 320, y: 180 } });
const pinnedState = runtime.reduce(state, { name: "pin-node", target_id: "memory:operator-preference", payload: { x: 100, y: 80 } });
const resetState = runtime.reduce(pinnedState, { name: "reset-pins" });
const clusterPinnedState = runtime.reduce(resetState, {
  name: "pin-many",
  payload: {
    positions: {
      "node:cluster-a": [11, 22],
      "node:cluster-b": [33, 44]
    }
  }
});
const restoredGroupsState = runtime.reduce(
  runtime.reduce(state, { name: "group-toggle", target_id: "memory" }),
  { name: "group-show-all" }
);
state = runtime.reduce(state, { name: "camera", payload: { x: 8, y: -2, zoom: 1.25, yaw: 16, pitch: -12 } });
state = runtime.reduce(state, { name: "group-toggle", target_id: "provider" });
state = runtime.reduce(state, { name: "filter", target_id: "node_kind", payload: { value: "memory" } });
const bounded = runtime.selectedNodeIdsInBounds(
  [
    { id: "inside:b", x: 20, y: 30 },
    { id: "outside", x: 80, y: 30 },
    { id: "inside:a", x: 10, y: 10 }
  ],
  { minX: 0, minY: 0, maxX: 40, maxY: 40 }
);
const emptyStatus = runtime.selectionStatusText(runtime.normalizeState({}), { nodes: {}, edges: {} });
const selectedStatus = runtime.selectionStatusText(
  runtime.normalizeState({
    selected_node_ids: ["node:a", "node:b", "node:c", "node:d"],
    selected_edge_id: "edge:ab"
  }),
  {
    nodes: { "node:a": "Alpha", "node:b": "Beta", "node:c": "Gamma", "node:d": "Delta" },
    edges: { "edge:ab": "connects" }
  }
);
const fittedState = runtime.fittedCameraState(
  runtime.normalizeState({ camera_x: 99, camera_y: 88, camera_zoom: 0.5 }),
  [
    { id: "node:a", x: 100, y: 100 },
    { id: "node:b", x: 300, y: 200 }
  ],
  { width: 400, height: 200, padding: 40 }
);
const emptyFitState = runtime.fittedCameraState(
  runtime.normalizeState({ camera_x: 99, camera_y: 88, camera_zoom: 0.5 }),
  [],
  { width: 400, height: 200, padding: 40 }
);
const minimapViewport = runtime.minimapViewportRect(
  runtime.normalizeState({ camera_x: 20, camera_y: -10, camera_zoom: 2 }),
  { width: 400, height: 200 },
  { width: 80, height: 40 }
);
const nodeAuthoringDefaults = runtime.authoringDefaults(runtime.normalizeState({
  selected_node_id: "node:b",
  selected_node_ids: ["node:a", "node:b"]
}));
const edgeAuthoringDefaults = runtime.authoringDefaults(
  runtime.normalizeState({ selected_edge_id: "edge:ab" }),
  [{ id: "edge:ab", source_id: "node:a", target_id: "node:b" }]
);
const viewerContext = runtime.viewerContext(runtime.normalizeState({
  screen: "neighborhood",
  query: "kind:memory",
  selected_node_id: "node:b",
  selected_node_ids: ["node:a", "node:b"],
  selected_edge_id: "edge:ab",
  camera_x: 8,
  camera_y: -2,
  camera_zoom: 1.25,
  camera_yaw: 16,
  camera_pitch: -12,
  render_engine: "canvas",
  theme: "ink",
  saved_view_id: "ops-review",
  filters: { node_kind: "memory" }
}));
const viewerContextRows = runtime.viewerContextRows(
  runtime.normalizeState({
    screen: "neighborhood",
    query: "kind:memory",
    selected_node_id: "node:b",
    selected_node_ids: ["node:a", "node:b"],
    selected_edge_id: "edge:ab",
    camera_x: 8,
    camera_y: -2,
    camera_zoom: 1.25,
    camera_yaw: 16,
    camera_pitch: -12,
    render_engine: "canvas",
    theme: "ink",
    filters: { node_kind: "memory" }
  }),
  {
    nodes: { "node:a": "Alpha", "node:b": "Beta" },
    edges: { "edge:ab": "connects" }
  }
);
const captureTemplate = runtime.captureTemplatePayload({
  dataset: {
    kind: "question",
    tags: "question, follow-up",
    source: "workbench",
    placeholder: "Ask what should be checked next in this graph context."
  },
  textContent: "Question"
});
const savedRoute = runtime.savedViewRoute(runtime.normalizeState({
  screen: "explore",
  query: "kind:memory",
  selected_node_id: "node:b",
  selected_node_ids: ["node:a", "node:b"],
  selected_edge_id: "edge:ab",
  camera_x: 8,
  camera_y: -2,
  camera_zoom: 1.25,
  camera_yaw: 16,
  camera_pitch: -12,
  render_engine: "canvas",
  theme: "ink",
  saved_view_id: "ops-review",
  hidden_groups: ["provider"],
  filters: { node_kind: "memory" },
  pinned_positions: { "node:a": [10, 20] }
}));
const workbookSlot = runtime.workbookSlotPayload(
  runtime.normalizeState({
    screen: "explore",
    query: "kind:memory",
    selected_node_id: "node:b",
    camera_x: 8,
    camera_y: -2,
    camera_zoom: 1.25,
    camera_yaw: 16,
    camera_pitch: -12,
    render_engine: "canvas",
    theme: "ink",
    filters: { node_kind: "memory" }
  }),
  "Ops Review",
  "2026-07-02T12:00:00.000Z"
);
const storage = {
  value: JSON.stringify([workbookSlot]),
  getItem: () => storage.value
};
const workbookSlots = runtime.workbookSlotsFromStorage(storage);
const commandActions = [
  { id: "local", label: "Local neighborhood", summary: "Inspect focus node", group: "navigate", route: "/neighborhood" },
  { id: "capture", label: "Capture knowledge", summary: "Jump to authoring form", group: "author", route: "/explore#capture-knowledge" },
  { id: "evidence", label: "Evidence review", summary: "Show provenance", group: "review", route: "/explore?query=has%3Aprovenance" }
];
const commandSummary = runtime.commandPaletteFilterSummary(commandActions, "author capture");
const projectedPoint = runtime.projectPoint3D(
  { x: 700, y: 360, z: 120 },
  runtime.normalizeState({ render_engine: "3d", camera_yaw: 30, camera_pitch: -15 }),
  { width: 1280, height: 720 }
);
const overviewDetailMode = runtime.detailMode(
  runtime.normalizeState({ camera_zoom: 0.5, label_density: 0.2 }),
  240
);
const precisionDetailMode = runtime.detailMode(
  runtime.normalizeState({ camera_zoom: 2.4, label_density: 0.2 }),
  240
);
const smallGraphDetailMode = runtime.detailMode(
  runtime.normalizeState({ camera_zoom: 0.5, label_density: 0.2 }),
  24
);
const inspectPayload = runtime.nodeInspectPayload({
  dataset: {
    nodeId: "node:content",
    label: "Content Node",
    kind: "note",
    summary: "Rendered summary",
    source: "demo",
    contentTitle: "Notebook entry",
    contentPreview: "Actual note text",
    provenanceIds: "prov:a prov:b",
    citationIds: "cite:a",
    focusRoute: "/explore?focus_node_id=node%3Acontent"
  }
});
process.stdout.write(JSON.stringify({
  state,
  resetState,
  clusterPinnedState,
  restoredGroupsState,
  bounded,
  emptyStatus,
  selectedStatus,
  fittedState,
  emptyFitState,
  minimapViewport,
  nodeAuthoringDefaults,
  edgeAuthoringDefaults,
  viewerContext,
  viewerContextRows,
  captureTemplate,
  savedRoute,
  workbookSlot,
  workbookSlots,
  commandSummary,
  projectedPoint,
  overviewDetailMode,
  precisionDetailMode,
  smallGraphDetailMode,
  inspectPayload,
  commandMatches: [
    runtime.commandPaletteActionMatches(commandActions[0], "local focus"),
    runtime.commandPaletteActionMatches(commandActions[1], "author capture"),
    runtime.commandPaletteActionMatches(commandActions[2], "missing")
  ],
  searchShortcuts: [
    runtime.isGraphSearchShortcut({ key: "/" }),
    runtime.isGraphSearchShortcut({ key: "k", ctrlKey: true }),
    runtime.isGraphSearchShortcut({ key: "k", metaKey: true }),
    runtime.isGraphSearchShortcut({ key: "k" })
  ],
  shortcuts: runtime.keyboardShortcuts,
  eventName: runtime.eventName("select-node")
}));
"""
    )

    result = subprocess.run(
        [node, "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["eventName"] == "graphfakos:select-node"
    assert payload["state"]["selected_node_id"] == "memory:operator-preference"
    assert payload["state"]["selected_node_ids"] == [
        "memory:operator-preference",
        "provider:third-party",
    ]
    assert payload["state"]["pinned_positions"]["provider:third-party"] == [320, 180]
    assert payload["resetState"]["pinned_positions"] == {}
    assert payload["clusterPinnedState"]["pinned_positions"] == {
        "node:cluster-a": [11, 22],
        "node:cluster-b": [33, 44],
    }
    assert payload["restoredGroupsState"]["hidden_groups"] == []
    assert payload["bounded"] == ["inside:a", "inside:b"]
    assert payload["emptyStatus"] == (
        "No selected graph items. Shift-click nodes or Shift-drag canvas to select several."
    )
    assert payload["selectedStatus"] == (
        "Selected 4 nodes: Alpha, Beta, Gamma, ... Selected edge: connects."
    )
    assert payload["fittedState"]["camera_x"] == -40
    assert payload["fittedState"]["camera_y"] == -80
    assert payload["fittedState"]["camera_zoom"] == 1.2
    assert payload["emptyFitState"]["camera_x"] == 0
    assert payload["emptyFitState"]["camera_y"] == 0
    assert payload["emptyFitState"]["camera_zoom"] == 1
    assert payload["minimapViewport"] == {
        "x": 0,
        "y": 1,
        "width": 38,
        "height": 20,
    }
    assert payload["nodeAuthoringDefaults"] == {
        "action_type": "draft_edge",
        "target_id": "node:b",
        "source_id": "node:a",
        "target_node_id": "node:b",
    }
    assert payload["edgeAuthoringDefaults"] == {
        "action_type": "draft_edge",
        "target_id": "node:a",
        "source_id": "node:a",
        "target_node_id": "node:b",
    }
    assert payload["viewerContext"] == {
        "screen": "neighborhood",
        "query": "kind:memory",
        "selected_node_id": "node:b",
        "selected_node_ids": ["node:a", "node:b"],
        "selected_edge_id": "edge:ab",
        "camera": {"x": 8, "y": -2, "zoom": 1.25, "yaw": 16, "pitch": -12},
        "layout": "force",
        "render_engine": "canvas",
        "theme": "ink",
        "saved_view_id": "ops-review",
        "filters": {"node_kind": "memory"},
    }
    assert payload["viewerContextRows"] == {
        "screen": "neighborhood: kind:memory",
        "selection": "connects",
        "camera": "x=8.0, y=-2.0, zoom=1.25, yaw=16.0, pitch=-12.0",
        "view": "force / canvas / ink",
        "filters": "node_kind=memory",
    }
    assert payload["captureTemplate"] == {
        "label": "Question",
        "kind": "question",
        "tags": "question, follow-up",
        "source": "workbench",
        "placeholder": "Ask what should be checked next in this graph context.",
    }
    assert payload["savedRoute"].startswith("/explore?")
    assert "query=kind%3Amemory" in payload["savedRoute"]
    assert "selected_node_ids=node%3Aa%2Cnode%3Ab" in payload["savedRoute"]
    assert "selected_edge_id=edge%3Aab" in payload["savedRoute"]
    assert "camera_zoom=1.25" in payload["savedRoute"]
    assert "camera_yaw=16.00" in payload["savedRoute"]
    assert "camera_pitch=-12.00" in payload["savedRoute"]
    assert "render_engine=canvas" in payload["savedRoute"]
    assert "hidden_groups=provider" in payload["savedRoute"]
    assert "pinned_positions=" in payload["savedRoute"]
    assert payload["workbookSlot"]["id"] == "ops-review:2026-07-02T12:00:00.000Z"
    assert payload["workbookSlot"]["label"] == "Ops Review"
    assert payload["workbookSlot"]["state"]["query"] == "kind:memory"
    assert payload["workbookSlot"]["route"].startswith("/explore?")
    assert payload["workbookSlots"][0]["label"] == "Ops Review"
    assert payload["commandSummary"] == {
        "query": "author capture",
        "total_count": 3,
        "visible_count": 1,
        "first_action_id": "capture",
        "first_route": "/explore#capture-knowledge",
    }
    assert payload["projectedPoint"]["x"] != 700
    assert payload["projectedPoint"]["y"] != 360
    assert payload["projectedPoint"]["scale"] > 0
    assert payload["overviewDetailMode"] == "overview"
    assert payload["precisionDetailMode"] == "precision"
    assert payload["smallGraphDetailMode"] == "detail"
    assert payload["commandMatches"] == [True, True, False]
    assert payload["inspectPayload"]["id"] == "node:content"
    assert payload["inspectPayload"]["contentTitle"] == "Notebook entry"
    assert payload["inspectPayload"]["contentPreview"] == "Actual note text"
    assert payload["inspectPayload"]["provenanceIds"] == ["prov:a", "prov:b"]
    assert payload["searchShortcuts"] == [True, True, True, False]
    assert {item["key"] for item in payload["shortcuts"]} >= {
        "/ or Ctrl/Meta+K",
        "+ / =",
        "-",
        "Arrow keys / WASD",
        "Delete / Backspace",
    }
    assert payload["state"]["camera_x"] == 8
    assert payload["state"]["camera_y"] == -2
    assert payload["state"]["camera_zoom"] == 1.25
    assert payload["state"]["camera_yaw"] == 16
    assert payload["state"]["camera_pitch"] == -12
    assert payload["state"]["render_engine"] == "canvas"
    assert payload["state"]["theme"] == "ink"
    assert payload["state"]["show_orphans"] is False
    assert payload["state"]["show_neighbor_links"] is False
    assert payload["state"]["edge_clutter"] == "reduced"
    assert payload["state"]["analytics_overlay"] == "degree"
    assert payload["state"]["filters"]["node_kind"] == "memory"
    assert payload["state"]["hidden_groups"] == ["provider"]
