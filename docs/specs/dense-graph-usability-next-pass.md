# Dense Graph Usability Next Pass

Status: reviewed, ready for execution
Owner: GraphFakos
Last updated: 2026-07-21

## Purpose

Make the GraphFakos graph surface feel like a serious dense graph navigator:
small readable points, natural relationship flow, reversible group controls,
space-like 3D travel, and useful inspect/edit overlays that work against
200K and 1M provider-envelope fixtures.

This pass is intentionally about the graph workbench. It should not add broad
product chrome, provider-specific semantics, storage policy, or another side
panel just because there is space.

## Product Objective

The graph is the primary product surface. A user should be able to open a large
provider-neutral graph, understand its shape at a distance, move through it like
a navigable space, inspect real node content when they arrive, and make
provider-neutral notes or graph-action drafts without losing the visual context.

## Current State

GraphFakos already has:

1. a package-owned WebGL `render_engine=3d` path with SVG fallback,
2. `space` and light themes with route-backed theme state,
3. dense 200K and 1M benchmark envelopes,
4. semantic zoom helpers for label density and node scaling,
5. cluster/island placement,
6. group chips and route-backed filters,
7. node hover and selection overlays,
8. viewer-local node and cluster drag behavior,
9. curved/bundled edge helpers, and
10. browser E2E coverage for dense envelope smoke tests.

The remaining gap is product feel: dense views still need stronger level of
detail, better relationship legibility, tighter interaction affordances, and
more useful content/edit overlays before the viewer feels competitive with
graph-first tools.

## Non-Goals

1. Do not make GraphFakos a graph database, memory store, repository ingester,
   fact extractor, or trust engine.
2. Do not persist edits unless a provider explicitly accepts a
   provider-neutral graph action or knowledge-capture payload.
3. Do not fork Sophiagraph or PragmaGraph UI semantics into GraphFakos.
4. Do not solve 1M scale by pretending the browser draws one million raw
   vertices at once. The large-fixture contract remains aggregate clusters,
   omitted counts, edge bundles, and expansion cursors.
5. Do not add large permanent panels that shrink the graph surface. Secondary
   controls should collapse, dock, or appear contextually.

## Design Principles

1. Canvas first: the largest stable visual region belongs to the graph.
2. Progressive detail: overview shows structure, mid zoom shows clusters, local
   zoom shows labels/content.
3. Reversible controls: hidden groups, dragged formations, pins, theme, and
   focus should all have visible ways back.
4. Natural links: dense edges should read as flows, bundles, arcs, or trails,
   not as a pile of straight lines.
5. Provider neutrality: edits are draft viewer actions until a provider owns
   persistence or rebuild behavior.
6. Static honesty: exported/no-JavaScript HTML stays readable even when 3D
   navigation is unavailable.

## Default Decisions For Execution

Use these defaults unless review changes them before implementation starts:

1. Dense fixture routes should default to `layout=islands` for 200K and 1M
   provider envelopes. `grouped` remains available as a mode chip.
2. Node content preview should prefer provider-declared inspector schema fields
   first, then `provider_payload.content`, then `provider_payload.summary`,
   then the node summary. GraphFakos renders these fields but does not judge
   truth or freshness.
3. Cluster drag persists as viewer-local state by default. It may be exported
   through saved-view/replay state, but it should not become provider
   persistence unless the user submits an explicit graph-action draft and the
   provider accepts it.
4. The honest usability target is both 200K and 1M aggregate routes: 200K for
   interactive product feel, 1M for envelope/budget honesty.

## Implementation Surfaces

Likely owners:

1. `web/src/semantic-detail.js`: label budget, zoom/detail thresholds, and
   dense label fallback.
2. `web/src/renderer.js`: WebGL scene setup, force profile, cluster centers,
   node scale, drag behavior, theme application, and runtime interaction.
3. `web/src/link-shape.js`: deterministic edge curve and bundling decisions.
4. `web/src/focus-readability.js`: popup/card placement around selected nodes.
5. `web/src/spatial-navigation.js`: keyboard and space-like movement helpers.
6. `web/src/visual-contrast.js`: theme-aware point/edge contrast constants.
7. `src/graphfakos/ui/app.py`: route-backed HTML composition and controls.
8. `src/graphfakos/adapters/demo.py`: demo content payloads and UX fixtures.
9. `scripts/generate_benchmark_envelopes.py`: 200K/1M deterministic envelopes.
10. `web/tests/viewer.spec.js`: browser behavior and screenshot evidence.

Maintainability guardrails:

1. `src/graphfakos/models.py`, `src/graphfakos/ui/app.py`,
   `web/src/renderer.js`, and `web/tests/viewer.spec.js` are already large
   enough that new work should prefer small existing helpers or real-owner
   extraction over adding more monolithic branches.
2. Do not split files only to create tiny abstractions; split only when the new
   file has a clear owner, such as label policy, edge policy, or input
   controls.
3. Rebuild packaged assets after changing `web/src/*`; do not edit
   `src/graphfakos/assets/renderer-3d.js` by hand.

## Execution Lanes

### GFDG-01 Scale And Label LOD

Tighten the visual ladder for dense data.

Required behavior:

1. Overview mode uses tiny points and minimal labels.
2. Cluster mode reveals cluster labels, bridge labels, and selected/focused
   context only.
3. Local mode reveals node labels around the current focus without covering the
   graph.
4. Hover and selected labels win over global label budgets.
5. Dense 200K and 1M routes visibly show more spatial structure than label
   clutter.

Acceptance:

1. `web/src/semantic-detail.js` owns label budgets.
2. `web/src/renderer.js` owns node scale and render-density decisions.
3. Browser screenshots for 200K and 1M show fewer labels at overview and
   smaller vertices than the July 3 baseline.
4. Zooming into a selected island reveals local labels without turning every
   nearby node into text.

### GFDG-02 Edge Flow And Bundling

Make relationship flow legible before adding more graph objects.

Required behavior:

1. Cross-cluster and aggregate edges curve more strongly than local edges.
2. Dense scenes alpha-scale and width-scale edges by relationship role,
   confidence, or bundle weight when available.
3. Hover/selection highlights incident links without permanently brightening
   the entire edge field.
4. Dragging a node or cluster updates connected edge geometry live.
5. Straight-line fallback remains acceptable in static SVG export.

Acceptance:

1. `web/src/link-shape.js` keeps deterministic curve calculations.
2. Tests assert aggregate/bundled edges curve more than ordinary links.
3. Dense WebGL screenshots show connection flow instead of rigid chord lines.
4. SVG fallback keeps route-backed edges readable even if it cannot reproduce
   the full WebGL edge styling.

### GFDG-03 Balanced Islands And Cluster Travel

Make large graphs use space well and support moving between islands.

Required behavior:

1. Island layout spreads cluster centers across the available field instead of
   compressing everything into the middle.
2. Cluster cards or bottom chips let users jump to, isolate, and restore
   clusters without changing theme.
3. Clicking a cluster route preserves `theme`, `render_engine`, and relevant
   camera mode.
4. Reset returns to the full graph, while focus/island controls fit the scoped
   cluster.
5. The 1M fixture remains bounded by aggregate cluster records and omitted
   counts.

Acceptance:

1. Cluster focus and reset preserve dark/light setting.
2. Browser E2E covers cluster route persistence.
3. 200K and 1M screenshots show multiple visible island groups, not one
   overlapping center mass.
4. Dense routes avoid reloading into light mode when the active theme is
   `space`.

### GFDG-04 Direct Manipulation

Make navigation and graph manipulation feel tactile.

Required behavior:

1. Empty-canvas drag orbits the 3D scene.
2. Shift or Alt drag pans the scene.
3. Scroll zooms toward the cursor.
4. Dragging a node pulls its incident edges and keeps the dropped local pin
   until reset.
5. Dragging a cluster shell moves visible members together with live edge
   stretch.
6. Layout/reset restores canonical formation.
7. Tooltip/help affordance explains the controls without consuming graph area.

Acceptance:

1. Controls are discoverable from the graph surface.
2. The route-backed static fallback still exposes fit/reset/focus links.
3. Browser E2E covers node drag, cluster drag, reset, and keyboard navigation.
4. Dragging does not leave a hidden irreversible state; reset, layout, or pin
   reset visibly restores the canonical view.

### GFDG-05 Inspector, Content, And Edit Overlay

Make click/inspect useful enough for real notes, memory, and code graph items.

Required behavior:

1. Click or tap opens a contextual card near the selected node.
2. The card shows a concise title, kind, source, relationship count, evidence
   count, and provider-declared preview content when available.
3. The card can expand into a docked detail view without covering the graph
   permanently.
4. The detail view supports provider-neutral note/capture and graph-action
   draft forms.
5. Tags/groups can be toggled or drafted for provider handling; unsupported
   providers show clear unsupported status.
6. Escape or empty-canvas click dismisses transient overlays.

Acceptance:

1. GraphFakos renders provider-declared inspector fields without interpreting
   provider truth.
2. Demo data includes note/content payloads for UX iteration.
3. Browser E2E covers open, expand, edit draft, unsupported action, and dismiss.
4. The overlay does not permanently steal canvas width; expanded detail is
   dismissible, dockable, or route-backed.

### GFDG-06 Theme Toggle And Visual Contrast

Make light/dark switching obvious and durable.

Required behavior:

1. The top canvas controls include the visible opposite theme action, such as
   `Light` while in space theme and `Dark` while in light theme.
2. Theme choice persists through route changes, cluster focus, reloads, and
   local saved-view slots.
3. The graph canvas itself changes theme, not only the surrounding chrome.
4. Space theme uses bright enough points and edges to keep small vertices
   visible.
5. Light theme remains usable for static export and screenshots.

Acceptance:

1. Theme persistence is covered by browser E2E.
2. Dense screenshots show small vertices with enough contrast in both themes.
3. No provider-specific state is required to remember the viewer theme.
4. The visible toggle label always names the action that will happen, not the
   current theme.

### GFDG-07 Large Fixture Proof

Keep scale claims honest and repeatable.

Required behavior:

1. 200K and 1M fixture generation remains deterministic.
2. Every generated large fixture has at least 100 nodes per cluster before
   aggregation.
3. Large routes expose aggregate clusters, omitted counts, bundles, and
   expansion cursors.
4. Browser tests open 200K and 1M routes without crashing or allocating the
   full raw graph.
5. Screenshots are generated for visual review.

Acceptance:

1. `make benchmark-fixtures` produces the scale envelopes.
2. `make browser-e2e` validates dense smoke routes.
3. The README/docs include a copy-paste local command for opening the 1M route.
4. Evidence distinguishes raw graph size from rendered aggregate count.

## Review Questions

These are no longer blockers because the execution defaults above answer them,
but reviewers should revisit them if implementation evidence points elsewhere:

1. Should any non-fixture dense provider route still default to `grouped`
   instead of `islands`?
2. Should provider-declared preview content become a stable DTO field after
   more adapter experience?
3. Should cluster drag export as a provider-neutral action draft in the first
   pass, or wait until edit overlays are stronger?
4. What visual evidence threshold should make 1M "usable enough" rather than
   merely "honestly bounded"?

## Failure Smells

Stop and rework if a pass creates any of these outcomes:

1. The graph canvas shrinks because a panel became more important than the
   graph.
2. Labels dominate the screen at overview zoom.
3. Dark/light mode is visible in chrome but not on the graph itself.
4. Hidden groups cannot be restored without a page reload.
5. Cluster focus drops theme or render-engine route state.
6. Dense edges are mostly straight high-contrast lines through the center.
7. A note/edit affordance implies provider persistence when the provider did
   not accept the action.
8. A large-fixture test claims one million rendered objects instead of the
   aggregate envelope contract.

## Validation Plan

Use focused validation during implementation:

1. `npm --prefix web run build`
2. `make browser-e2e`
3. `make check`
4. `git diff --check`

When UI behavior changes materially, capture and inspect:

1. `web/test-results/graphfakos-200k-overview.png`
2. `web/test-results/graphfakos-1m-overview.png`

Do not claim the lane is visually complete from unit tests alone. The dense
viewer must be opened in a browser and visually checked against the product
objective above.
