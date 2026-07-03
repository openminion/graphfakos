# GraphFakos Competitive Viewer Next-Parity Spec

Date: 2026-07-02
Status: `implemented`
Owner: `graphfakos`
Related:
`docs/trackers/competitive-viewer-next-parity-2026-07-02-tracker.md`,
`docs/specs/competitive-viewer-roadmap-2026-07-01-spec.md`,
`docs/ui-contracts.md`,
`README.md`

## Purpose

Define the next package-local work needed to move GraphFakos closer to mature
graph-viewer products after the completed July 1 competitive viewer roadmap.

This spec covered the next ten gaps against Obsidian Graph View, Cytoscape.js,
Gephi, and Graphistry-style workflows. The paired tracker was promoted for
package-local implementation on 2026-07-02.

No version bump, release, publishing, or provider-specific persistence is
approved by this spec.

## Research Baseline

Sources checked on 2026-07-02:

1. Obsidian Graph View documents global/local graph views, filters, groups,
   display settings, forces, local graph depth, and graph time-lapse behavior:
   `https://obsidian.md/help/plugins/graph`.
2. Cytoscape.js positions itself as a rich interactive graph component with
   desktop/mobile support, events, graph analysis, panning, pinch zoom, and box
   selection: `https://js.cytoscape.org/`.
3. Gephi documents interactive filtering, attribute/topology filters,
   ForceAtlas-style layouts, appearance by attributes/metrics, statistics,
   label controls, drag/pan/zoom/select tools, and SVG/PDF/PNG export:
   `https://gephi.org/quickstart/`.
4. Gephi Desktop emphasizes advanced layout algorithms, real-time adjustment,
   readability optimization, attribute styling, and image exports:
   `https://gephi.org/desktop/`.
5. Graphistry emphasizes GPU-accelerated visual graph analytics, visual pivots
   across data sources, investigation workflows, shareable workbooks, and
   embeddable live graphs: `https://www.graphistry.com/`.
6. Graphistry use-case pages emphasize investigation speed, visual querying,
   pivot/drill workflows, root-cause exploration, and saved case/workbook
   flows: `https://www.graphistry.com/use-cases/siem-optimization`.

GraphFakos should borrow product lessons, not product identity. The package
must remain a provider-neutral graph lens for code/static knowledge graphs and
human/agent knowledge graphs.

## Current GraphFakos Position

Already complete:

1. provider-neutral graph DTOs and provider protocols,
2. static SVG fallback and local preview server,
3. `<graphfakos-viewer>` runtime,
4. explore, neighborhood, path, provenance, timeline, diff, provider-status,
   and context screens,
5. deterministic SVG-first layout improvements,
6. saved views, saved queries, graph actions/statuses, analytics, and replay
   bundles,
7. knowledge capture and graph action local-preview forms,
8. route-backed local graph controls,
9. visual polish for themes, hover states, edge clutter, minimap, and reduced
   motion.

Gap list promoted by this spec:

1. true Canvas/WebGL scale,
2. richer physics/display controls,
3. box select and multi-select workflows,
4. node/edge context menus,
5. manual pin editing as a durable saved-view workflow,
6. attribute-driven styling rules,
7. advanced topology/attribute filters,
8. community/component exploration,
9. time/diff animation,
10. investigation pivot flows.

Implementation status: package-local versions of all ten lanes landed on
2026-07-02. They intentionally remain provider-neutral and do not include
version bumps, publishing, provider-specific persistence, hosted
collaboration, or production GPU services.

## Product Boundary

GraphFakos may own:

1. viewer state fields,
2. renderer contracts,
3. UI controls and static fallback,
4. provider-neutral graph action payloads,
5. structural analytics and layout metadata,
6. replay/export artifacts,
7. demo fixtures for scale and interaction testing.

Providers and hosts still own:

1. durable memory or source graph storage,
2. fact extraction and semantic truth,
3. worker queues,
4. hosted auth/collaboration,
5. provider-specific style rules unless represented as neutral metadata,
6. production-scale GPU services or remote graph engines.

## Next Ten Lanes

### GFNP-01: Canvas Renderer Prototype

Problem: SVG remains the stable portable renderer, but it cannot match
Graphistry/Gephi-scale expectations for dense interactive exploration.

Target:

1. add a `canvas` renderer path behind the existing renderer state,
2. keep SVG as fallback and static export,
3. share viewer commands across SVG and canvas,
4. add a larger deterministic demo fixture,
5. record honest render limits for SVG and canvas.

Acceptance:

1. `render_engine=canvas` renders in local preview with no provider DTO fork,
2. static export still degrades to SVG,
3. renderer choice round-trips through viewer state and replay bundle,
4. tests prove fallback behavior and command compatibility,
5. docs name measured limits instead of claiming unlimited scale.

### GFNP-02: Physics And Display Control Panel

Problem: Obsidian and Gephi make graph readability tunable through force,
display, label, and edge controls. GraphFakos currently has only coarse route
controls.

Target:

1. center/gravity force,
2. repel force,
3. link distance,
4. node-size scale,
5. edge-width/link-opacity scale,
6. label threshold and label density,
7. animate/timeline display toggles where supported.

Acceptance:

1. controls work as route-backed forms without JavaScript,
2. JavaScript-enhanced local preview updates the view without losing state,
3. saved views and replay bundles preserve control values,
4. tests cover route/state round-trip and static fallback.

### GFNP-03: Box Select And Multi-Select

Problem: Cytoscape.js and Gephi-style tools support direct selection gestures.
GraphFakos still behaves mostly as single-node/single-edge navigation.

Target:

1. box select in the enhanced runtime,
2. shift-click multi-select,
3. selected subgraph inspector,
4. bulk hide/show,
5. bulk pin/export route,
6. static fallback route for selected node IDs.

Acceptance:

1. multi-selection is represented in provider-neutral viewer state,
2. static export remains usable through route links/forms,
3. runtime tests cover selection reducer behavior,
4. visual tests cover selected-subgraph inspector output.

### GFNP-04: Node And Edge Context Menus

Problem: mature graph tools support fast node/edge actions from the graph
surface. GraphFakos currently pushes most actions into side panels.

Target:

1. node menu: focus, local graph, hide, pin, copy ID, create edge, merge/alias,
   show provenance,
2. edge menu: inspect, hide edge kind, trace path, copy ID, show evidence,
3. keyboard-accessible fallback action menu,
4. safe unsupported-provider statuses for authoring actions.

Acceptance:

1. all actions map to existing provider-neutral command/action DTOs,
2. no durable mutation happens inside GraphFakos,
3. keyboard path exists for every pointer-only menu action,
4. tests cover menu markup and action payload shape.

### GFNP-05: Manual Pin Layout Editor

Problem: users need stable mental maps. Obsidian users often want node
placement to persist; Gephi lets users move nodes directly.

Target:

1. drag-to-pin behavior,
2. pin/unpin selected nodes,
3. reset pins,
4. save pinned positions into `GraphFakosSavedView`,
5. replay pinned positions from bundle/view state.

Acceptance:

1. pinned positions round-trip through saved view and replay bundle,
2. SVG fallback renders saved pins,
3. no provider-specific storage is introduced,
4. runtime tests cover pin commands and reducer state.

### GFNP-06: Attribute-Driven Styling

Problem: Gephi-style appearance controls let users color, size, and style
nodes/edges by attributes or computed metrics. GraphFakos has fixed styling
with limited theme controls.

Target:

1. color by kind/source/freshness/component/status,
2. size by degree/score/centrality,
3. edge width by weight/confidence,
4. dashed/styled edges by freshness or warning state,
5. legends generated from active style rules.

Acceptance:

1. style rules are provider-neutral and serializable,
2. provider-declared fields stay in explicit metadata,
3. structural computed fields are clearly marked GraphFakos-computed,
4. tests cover style-rule route/state and legend output.

### GFNP-07: Advanced Filters

Problem: Gephi exposes attribute and topology filters. GraphFakos has search
and simple kind/source/tag filters, but not enough topology exploration.

Target:

1. degree range,
2. component filter,
3. source/freshness/warning filters,
4. provenance/citation missing filters,
5. connected-to selected node,
6. edge-weight/edge-kind filters,
7. saved filter sets.

Acceptance:

1. filters compose with existing query syntax,
2. no-JavaScript fallback works through forms/routes,
3. tests cover topology filters on dense/islands/provenance fixtures,
4. provider status explains hidden-node/hidden-edge counts.

### GFNP-08: Community And Component Explorer

Problem: mature graph tools help users understand clusters, communities, and
components instead of only inspecting selected nodes.

Target:

1. component list,
2. simple community grouping,
3. cluster cards,
4. isolate/highlight cluster,
5. cluster legend,
6. compare cluster changes across snapshots.

Acceptance:

1. GraphFakos computes only structural clusters unless provider metadata
   declares semantic clusters,
2. cluster routes and replay state are stable,
3. tests cover islands and dense cluster fixtures,
4. UI distinguishes component, community, and provider-declared group.

### GFNP-09: Time And Diff Animation

Problem: Obsidian supports chronological graph animation, and GraphFakos
already has timeline/diff data but no animated inspection flow.

Target:

1. snapshot scrubber,
2. added/removed/changed animation,
3. freshness heatmap,
4. play/pause/step controls,
5. reduced-motion fallback,
6. static diff summary fallback.

Acceptance:

1. animation never becomes required for static export readability,
2. reduced-motion users get non-animated summaries,
3. snapshot/diff state is replayable,
4. tests cover timeline route state and generated diff frames metadata.

### GFNP-10: Investigation Pivot Workflow

Problem: Graphistry-style products help analysts pivot from one entity to
neighbors, shared context, timelines, root cause, and case evidence. GraphFakos
has pieces of this but not a cohesive investigation flow.

Target:

1. pivot from node to neighbors,
2. shared-neighbor path,
3. shortest-path-to-selected,
4. timeline around selected,
5. evidence/provenance bundle,
6. saved investigation route,
7. replayable case packet.

Acceptance:

1. investigation state is provider-neutral,
2. replay bundle records selected pivots and evidence routes,
3. GraphFakos does not infer root cause or truth,
4. providers may enrich the case packet through explicit payload fields.

## Recommended Execution Order

1. `GFNP-02`: physics/display controls
2. `GFNP-05`: manual pin layout editor
3. `GFNP-07`: advanced filters
4. `GFNP-08`: community/component explorer
5. `GFNP-03`: box select and multi-select
6. `GFNP-04`: node and edge context menus
7. `GFNP-06`: attribute-driven styling
8. `GFNP-09`: time/diff animation
9. `GFNP-10`: investigation pivot workflow
10. `GFNP-01`: canvas renderer prototype

Reason: improve SVG/local-preview usefulness first, then direct interaction,
then investigation workflows, and only then invest in the renderer once the
control model is stable. `GFNP-01` can move earlier if SVG performance becomes
the measured blocker for the selected lane.

## Milestones

### M1: Polished Small/Medium Graph Workbench

Rows: `GFNP-02`, `GFNP-05`, `GFNP-07`, `GFNP-08`.

Exit condition: a user can tune readability, pin a stable mental map, filter
by structure, and inspect clusters on current demo graphs without needing a new
renderer.

### M2: Direct Manipulation Workbench

Rows: `GFNP-03`, `GFNP-04`, `GFNP-06`.

Exit condition: users can select, inspect, style, and act on graph objects from
the graph surface while preserving keyboard and static fallback behavior.

### M3: Investigation And Scale

Rows: `GFNP-09`, `GFNP-10`, `GFNP-01`.

Exit condition: users can replay time/diff changes, pivot through an
investigation, and use a measured canvas renderer path for denser graphs.

## Validation Expectations

Every promoted lane should include:

1. focused tests for DTO/viewer-state behavior,
2. static render fallback tests,
3. browser runtime tests when JavaScript behavior changes,
4. local preview server tests when routes/actions change,
5. `make check`,
6. `make browser-test` when `assets/viewer.js` changes,
7. `make release-check` when public DTOs, package exports, CLI outputs, or
   packaged assets change,
8. OpenMinion `ruff check .` and `make lint` only when workspace closeout or
   OpenMinion integration is part of the promoted lane.

## Review Questions

1. Should `GFNP-01` move earlier, or should the package keep improving the SVG
   control model before starting Canvas?
2. Should manual pins be local-viewer-only state, or should providers be able
   to declare initial pin suggestions?
3. Which style-rule fields should become stable DTOs versus provider payload?
4. Which graph size should be the first honest canvas acceptance target?
5. Should the first investigation workflow optimize for code/static graphs,
   human knowledge graphs, or provider-neutral demo parity?
