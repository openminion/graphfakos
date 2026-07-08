# GraphFakos UI Contracts

Status: semantic alpha

Purpose: define the shared graph-viewer contract used by GraphFakos provider
adapters and by thin package-local UI commands such as `sophiagraph-ui` and
`pragmagraph-ui`.

## Contract Owner

GraphFakos owns the reusable viewer layer:

1. provider-neutral DTOs,
2. provider protocol validation,
3. static HTML rendering,
4. local preview serving,
5. screen routing,
6. graph canvas behavior,
7. node and edge inspectors,
8. search and filter controls,
9. provenance and citation panels,
10. provider-neutral graph diagnostics,
11. progressive camera/navigation enhancement over static SVG export,
12. framework-neutral `<graphfakos-viewer>` mounting behavior,
13. reusable viewer state, command, event, expansion, knowledge-capture, and
    theme DTOs,
14. packaged browser runtime assets,
15. reusable viewer test assertions.

Provider packages own their data semantics and adapter mapping. They should not
fork GraphFakos viewer HTML, duplicate local-server behavior, or create a
parallel test contract for the shared viewer.

## Thin Wrapper Rule

Package-local `*-ui` commands are allowed and encouraged for user convenience,
but they should stay thin.

Allowed package-local responsibilities:

1. load the package workspace or demo fixture,
2. choose sensible default screens,
3. construct the package's `GraphFakosProvider`,
4. pass command-line options through to GraphFakos rendering,
5. expose package-specific labels and integration commands.

GraphFakos-owned responsibilities:

1. shared screen names and navigation behavior,
2. provider-neutral screen metadata such as route labels and summaries,
3. static export and local preview server behavior,
4. graph filtering, selection, and inspection controls,
5. provider status and capability presentation,
6. context-preview layout,
7. camera route state, minimap orientation, group toggles, and saved-view links,
8. dynamic viewer state/event/command payloads,
9. local workbench action payload shape for provider-owned captures,
10. common smoke assertions.

## Progressive Enhancement Contract

The shared viewer must keep the static HTML export useful without JavaScript.
The baseline graph canvas is a provider-neutral SVG with route-backed node and
edge links. Client-side behavior may add pan, zoom, fit-to-selection or
fit-to-visible-graph, reset, fullscreen, drag-to-pan, drag-to-pin, Shift-drag
box selection, group toggle, minimap node focus/fitting, keyboard camera,
search, and selection shortcuts, synced minimap viewport frame,
keyboard-accessible graph-surface action menus, route-backed static action
panels for focus, neighborhood, evidence, path tracing, edge filtering, and
case-packet pivots, structural case-packet summaries for neighbors, paths,
evidence, timeline markers, and component samples, relationship-trail panels
for direct hops and shortest-path targets, route-backed component cards
with hub and case-packet links, route-backed timeline frame rails and event
cards, route-backed diff change cards for node, edge, snapshot, and case review,
route-backed interaction guides that explain search, camera, selection, local,
evidence, and authoring workflows with static fallback notes,
route-backed search/jump result panels derived from the currently visible graph,
route-backed navigation maps that expose global, local, path, evidence,
timeline, diff, status, and case-packet lanes,
route-backed command palettes that group saved queries, graph navigation,
evidence review, authoring jumps, and export shortcuts without requiring
JavaScript, plus progressive input filtering, Escape clear, Enter execution,
and live result counts when the packaged browser runtime is available,
route-backed active-lens summaries with reset links for stacked query, filter,
focus, selection, camera, and renderer state, provider-neutral expansion
planners that serialize `GraphFakosExpansionRequest` without fetching neighbors,
canvas visual legends that explain visible node kinds, edge kinds, style rules,
selection, pins, hubs, and evidence markers,
visible graph data tables that keep node metrics, selection, evidence counts,
and route-backed focus/local/case/select actions beside the canvas,
visible relationship data tables that keep edge endpoints, evidence counts,
and route-backed inspect/source/target/path/kind actions beside the canvas,
route-backed evidence coverage maps that report declared provenance and
citation presence or gaps across visible nodes and edges,
route-backed facet explorers for visible node kind, source, tag, component,
evidence, and degree buckets,
structural readability coaches for display pressure, render budget, label
density, edge opacity, and renderer fallback tuning, live selection status,
route-backed display recipes for readable review, dense scan, local focus,
evidence review, timeline review, and presentation export,
route-backed selection-set recipes for visible nodes, hubs, evidence-bearing
nodes, focus components, and clear-selection review,
selection-synced capture/action form defaults, graph-aware action-type defaults
for node versus edge contexts, and cross-panel highlight behavior, but those
enhancements must not replace the static route/export contract.
Selection, context-menu actions, and pinned node positions are viewer state or
provider-neutral action affordances only unless a provider or host explicitly
persists the saved view or accepts a graph action.

Automated package tests should cover generated HTML, route state, camera
parameters, controls, data attributes, and no-JavaScript SVG fallback. Pointer
behavior can be proven by a future browser/DOM harness or by recorded manual
preview evidence when the package validation plan explicitly allows that proof
mode.

## Dynamic Viewer Runtime Contract

GraphFakos ships a package-owned browser runtime asset for the reusable
`<graphfakos-viewer>` custom element. The element wraps the existing static
viewer markup instead of replacing it, so exported HTML remains readable when
JavaScript is unavailable.

The dynamic runtime owns only structural viewer state:

1. screen, layout, camera, selected node, selected edge, filters, groups, render
   engine, theme, and saved-view metadata,
2. provider-neutral viewer commands such as select, filter, camera, layout,
   group-toggle, expand, and export-state,
3. provider-neutral viewer events emitted as `graphfakos:<name>` custom events,
4. local fallback DOM synchronization for the SVG canvas, minimap, group
   toggles, inspector cards, and saved-view links.
5. browser-local saved-view slots for workbench convenience. These slots may
   serialize camera, filters, selection, pins, and route state into
   `localStorage`, but they are not provider persistence, collaboration, or a
   durable graph database.

Provider or host packages still own remote data loading, authorization,
mutation, persistence, semantic ranking, and product chrome. GraphFakos may
emit an expansion request event, but it must not fetch or invent
provider-specific neighbors unless a host/provider integration handles that
event explicitly.

Knowledge capture follows the same boundary. GraphFakos may render a
`Capture Knowledge` form and submit a `GraphFakosKnowledgeCapture` payload from
local preview mode, but the provider or host owns persistence, worker queues,
fact extraction, memory promotion, source ingestion, and graph rebuild policy.

The static baseline renderer is `svg`. The dynamic runtime also accepts `3d` as
a package-local projected SVG interaction mode with yaw/pitch camera state,
orbit gestures, perspective scaling, and route/export persistence. `canvas` and
WebGL-backed renderers remain future backend targets behind the same
provider-neutral state contract; unsupported render engines should fail clearly
through the public renderer validation helper rather than silently changing DTO
behavior.

## Scalable Graph Interaction Contract

The graph surface is the primary UI. Dense views should preserve a large canvas,
small readable points, progressive labels, natural curved edges, reversible
group chips, and cluster/island placement before exposing secondary panels.
Static export remains the SVG baseline when JavaScript is unavailable.

Viewer state owns theme, camera, hidden groups, selected ids, and pinned
positions. Theme may persist in browser-local storage and should be carried
across same-origin viewer route changes, but that is workbench convenience only;
it is not provider persistence.

Group controls must be reversible. Hiding a group should leave the chip visible
with an inactive state, and `Show all` must restore all hidden groups without
rebuilding provider data.

Node drag may pin one viewer-local node position. Cluster drag may move members
of the same rendered cluster together while preserving their relative offsets.
Both behaviors are viewer-local until a provider explicitly accepts a
provider-neutral action payload. `Reset`, `Layout`, or an equivalent control
must restore the canonical formation.

Edges should update live when nodes or clusters move. Dense routes should prefer
curved, bundled, alpha-scaled, or aggregate edge rendering over straight-line
clutter. Providers remain responsible for graph truth; GraphFakos only renders
the provider-neutral DTOs and emits provider-neutral commands.

`3d` navigation is a progressive enhancement over the same SVG fallback. Empty
canvas drag orbits the projected scene, Shift/Alt-drag pans, scroll zooms toward
the cursor, `W/A/S/D` moves through the scene, `Q/E` adjusts yaw, and
double-click centers a node. Saved routes and exported viewer state must carry
`camera_yaw` and `camera_pitch` in addition to `camera_x`, `camera_y`, and
`camera_zoom`. Static export may render the same graph without live orbit, but
it must remain readable and provider-neutral.

## Local Workbench Server Contract

Interactive viewer development should use GraphFakos' local HTTP workbench
server rather than opening generated HTML files directly. The server has two
provider-neutral response modes:

1. normal route requests return a complete HTML document for first load,
2. requests with `X-GraphFakos-Fragment: 1` return a JSON envelope containing a
   rendered `<graphfakos-viewer>` fragment for in-place client updates.

The browser runtime may intercept same-origin HTTP links and GET forms inside
`<graphfakos-viewer>` and replace the viewer from that fragment response. Static
HTML export remains a portable artifact path and must not require the server or
JavaScript to show a useful SVG baseline.

The server may also accept provider-neutral JSON action requests when a preview
host supplies an action handler:

1. `POST /api/knowledge` accepts `GraphFakosKnowledgeCapture` fields such as
   `text`, `kind`, `tags`, `source`, `link_node_id`, `link_edge_kind`, and
   `provider_payload`.
2. Knowledge-capture controls should expose visible graph-node attachment and
   relationship selectors where possible while preserving stable DTO field
   names for `link_node_id` and `link_edge_kind`.
3. Knowledge-capture panels may include provider-neutral templates such as
   notes, questions, code observations, and warnings. Templates may prefill
   workbench form fields and placeholders, but they must not generate note
   content, infer semantic truth, or imply durable persistence.
4. `POST /api/action` accepts `GraphFakosGraphAction` fields such as
   `action_id`, `action_type`, `target_id`, `source_id`, `target_node_id`,
   `label`, `body`, `tags`, and `provider_payload`.
5. Providers that implement the optional capture protocol decide whether to
   persist the note, enqueue a worker, rebuild a code/static graph, or attach a
   temporary preview-only node.
6. Providers that implement the optional graph-action protocol decide whether
   to queue, reject, preview, or apply the edit. GraphFakos only shapes the
   provider-neutral action payload and displays the returned status.
7. Providers that do not implement either protocol must fail clearly;
   GraphFakos must not pretend the capture or action was stored.
8. Graph-action authoring controls should use visible graph-node selectors
   where possible while preserving stable DTO field names for `target_id`,
   `source_id`, and `target_node_id`.
9. Static HTML exports must treat capture and graph-action forms as read-only
   and direct users back to the local preview server for mutations.
10. In local preview mode, accepted captures and graph actions should refresh
   the current route-backed viewer fragment so preview-only graph items become
   visible without a manual browser reload.
11. The local server should accept both JavaScript-submitted JSON payloads and
    ordinary `application/x-www-form-urlencoded` browser form submissions for
    preview actions, so the editor remains useful when JavaScript enhancement is
    unavailable or a host submits forms directly.
12. Successful browser form submissions should redirect back to the current
    viewer route, while JavaScript/API submissions that request JSON should keep
    receiving JSON action results for in-place fragment refresh.
13. Capture and action submissions may include
    `provider_payload.viewer_context` with route, selection, camera, renderer,
    theme, saved-view, query, and filter state so providers can understand the
    user's workbench context without GraphFakos assigning semantic truth.
14. Editor panels should show a compact submission-context preview beside the
    hidden payload field, so users can see which route, selection, camera, and
    filters will accompany a provider-owned capture or graph action.

Viewer iteration can use `DemoGraphProvider` and the `--demo-scenario` CLI
switch to simulate representative graph shapes without real provider data. Demo
scenarios must remain deterministic so UI regressions are repeatable. Demo
knowledge captures and graph actions are preview-only graph items; they are
there so viewer/editor behavior can be tested without implying durable storage
or semantic truth.

## Provider Adapter Shape

Adapters should implement `GraphFakosProvider` and return `GraphFakosGraph`.
The graph envelope should contain:

1. provider id, label, graph role, capabilities, and status,
2. nodes with stable ids, labels, kinds, scores, tags, sources, visual hints,
   provenance, citations, and provider payloads,
3. edges with stable ids, endpoints, kind, label, score, weight, provenance,
   citations, and provider payloads,
4. optional selected node or selected edge hints,
5. optional integration commands and short integration summaries for host
   packages or standalone previews.

Provider-only semantics belong in `provider_payload` unless the field is part
of the stable common DTO model.

Diagnostics should stay structural and provider-neutral. GraphFakos can report
orphan nodes, duplicate edge ids, unknown provenance ids, unknown citation ids,
and provider-supplied warnings. It must not decide whether a memory claim is
true, whether a source file is fresh, or whether an item should be promoted.

## Package Alignment

Sophiagraph and PragmaGraph should line up through GraphFakos without sharing
their internal graph truth:

1. Sophiagraph maps durable memory records, candidates, trust signals,
   structural links, and memory provenance into GraphFakos DTOs.
2. PragmaGraph maps source files, documents, code symbols, chunks, citations,
   freshness, and provider status into GraphFakos DTOs.
3. OpenMinion should consume GraphFakos-compatible providers through the same
   provider-neutral result shape instead of importing package-specific viewer
   code.
4. Third-party packages can implement the same provider protocol directly.
5. Hosts that want graph-side note entry can implement the optional capture
   protocol while keeping durable knowledge semantics outside GraphFakos.

The shared viewer must not infer facts, promote memories, ingest source files,
or decide durable memory policy. Those responsibilities stay with the provider
or host package.

## Compatibility Expectations

Within the `0.0.x` line, changes should preserve:

1. stable public import roots listed in `API_COMPATIBILITY.md`,
2. public DTO names,
3. `GraphFakosProvider.load_graph()` behavior,
4. console script names,
5. provider-neutral `diagnose_graph()` output keys,
6. supported screen names,
7. local preview and static-export behavior, including the no-JavaScript SVG
   baseline,
8. package adapter compatibility for Sophiagraph and PragmaGraph,
9. packaged `assets/viewer.js` availability in source, editable installs, and
   wheels,
10. same-origin local workbench fragment responses for in-place viewer
    navigation,
11. local preview JSON action behavior for `POST /api/knowledge`,
12. typed package marker availability through `graphfakos/py.typed`.

If a viewer contract change requires Sophiagraph or PragmaGraph updates, land
adapter tests in those packages with the GraphFakos change.
