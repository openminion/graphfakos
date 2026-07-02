# GraphFakos Competitive Viewer Roadmap Spec

Date: 2026-07-01
Status: `done`
Owner: `graphfakos`
Related:
`docs/ui-contracts.md`,
`docs/trackers/competitive-viewer-roadmap-2026-07-01-tracker.md`,
`README.md`,
`API_COMPATIBILITY.md`

## Purpose

Define the next GraphFakos viewer roadmap required to move from a credible
provider-neutral graph workbench MVP toward a more competitive visual graph
experience for both:

1. source/code/static knowledge graphs, and
2. human/agent knowledge graphs.

This spec is planning plus the completed package-local competitive viewer
scope. It does not approve version bumps, publishing, or provider-specific
persistence work.

Execution state: `GFCR-00` through `GFCR-CQ` have been executed in GraphFakos
without changing the package version. The paired tracker records closeout
evidence and validation commands.

## External Reference Baseline

The roadmap is grounded in these current viewer patterns:

1. Obsidian Graph View: global graph, local graph, depth controls, filters,
   groups, display options, and graph forces.
   Reference: `https://obsidian.md/help/plugins/graph`
2. Graphify-style knowledge graph viewers: low-friction graph navigation over
   notes, links, relations, and existing workspace data.
   Reference: `https://www.getgraphify.com/`
3. Cytoscape.js: rich interactive graph component behavior, gestures, events,
   and multiple layout families.
   Reference: `https://js.cytoscape.org/`
4. Gephi: mature layout, filtering, topology exploration, and visual analysis
   workflows.
   Reference: `https://gephi.org/desktop/`
5. Graphistry: large-scale interactive graph investigation, pivoting, and
   analysis over bigger datasets.
   Reference: `https://www.graphistry.com/`

GraphFakos should not copy those products directly. The goal is to extract the
shared product lessons that fit a Python package-owned, provider-neutral graph
viewer.

## Competitive Milestones

This roadmap should not be treated as one giant feature. Use these milestones
to keep execution bounded:

1. `M1: usable graph workbench parity` means layout quality, saved views, local
   graph controls, and command/query navigation are good enough for daily
   package review on small and medium graphs.
2. `M2: larger graph investigation parity` means renderer scale, analytics
   overlays, and evidence/export workflows can support large provider graphs
   without misleading performance claims.
3. `M3: authoring and rebuild parity` means graph-side capture, draft
   authoring, and provider-owned worker status form a coherent loop without
   moving durable semantics into GraphFakos.

The first implementation wave should target `M1`. Do not pull `M2` or `M3`
work into the first layout lane unless it is required to preserve a public
contract.

## Current State

GraphFakos now has:

1. provider-neutral graph DTOs,
2. static export and local preview server paths,
3. framework-neutral `<graphfakos-viewer>` runtime,
4. explore, neighborhood, path, provenance, timeline, diff, provider-status,
   and context screens,
5. basic SVG camera controls, minimap, group toggles, filters, and inspectors,
6. demo scenarios for repeatable UI iteration,
7. local workbench fragment navigation, and
8. provider-owned knowledge capture through `GraphFakosKnowledgeCapture` and
   `POST /api/knowledge`.

That makes GraphFakos directionally close to lightweight Obsidian/Graphify
workbench expectations for small and medium package-review graphs. It now has
better layout quality, saved views, local graph controls, command-palette
surfaces, provider-neutral authoring/status payloads, structural analytics,
replay bundles, and visual polish. It still intentionally does not claim full
Canvas/WebGL-scale parity with large hosted graph investigation platforms.

## Product Boundary

GraphFakos owns:

1. provider-neutral graph DTOs and viewer state,
2. rendering contracts and renderer selection,
3. local preview workbench behavior,
4. graph navigation controls,
5. structural graph diagnostics,
6. provider-neutral capture payload shape,
7. reusable UI primitives and tests.

Providers and hosts own:

1. durable memory and source graph persistence,
2. fact extraction and semantic interpretation,
3. worker queues and rebuild policy,
4. trust, freshness, privacy, and promotion rules,
5. authentication and hosted collaboration semantics.

Any roadmap item that needs durable truth, semantic inference, or background
processing must define a provider-neutral contract in GraphFakos and leave the
actual behavior to providers or hosts.

## Implementation Constraints

New viewer work should follow these constraints unless a child lane explicitly
widens them:

1. keep the core viewer framework-neutral and avoid adding a frontend framework,
2. keep `svg` as the stable fallback renderer until another renderer is
   accepted through a reviewed capability contract,
3. prefer deterministic layout and state tests over screenshot-only proof,
4. keep local preview actions same-origin and local-development oriented,
5. avoid package-owned background workers, storage daemons, or hosted-service
   assumptions,
6. require every visual claim to name the demo scenario and viewport used for
   review.

## Roadmap Lanes

### GFCR-01: Layout Engine Quality

Problem: the current layouts are useful but not competitive with graph-native
tools for medium/dense graphs.

Target:

1. deterministic seeded layout state,
2. better force layout,
3. hierarchy/DAG layout,
4. cluster-aware layout,
5. timeline layout refinement,
6. manual pin positions that can round-trip through viewer state.

Acceptance:

1. static SVG fallback still renders,
2. layout choice is represented in route/viewer state,
3. deterministic tests prove stable node positions for seeded fixtures,
4. dense demo graph is visibly navigable without arbitrary overlap explosion,
5. no Canvas/WebGL renderer is required for the first layout improvement.

### GFCR-02: Saved Graph Workspaces

Problem: users need repeatable graph views, not only route links.

Target:

1. named saved views,
2. camera, filter, layout, group, pinned-node, and selected-lens state,
3. portable JSON export/import for saved views,
4. static-export compatibility.

Acceptance:

1. saved view DTO round-trips,
2. saved view can be applied from CLI or local preview,
3. no provider-specific storage assumption is introduced,
4. docs distinguish local preview, static export, and host-owned persistence.

### GFCR-03: Obsidian-Style Local Graph Controls

Problem: local graph navigation needs controls users already understand.

Target:

1. depth slider,
2. neighbor-link toggle,
3. orphan toggle,
4. tag/source/kind grouping,
5. group color/display controls,
6. force/display sliders where supported by the active renderer.

Acceptance:

1. controls degrade to route-backed GET forms without JavaScript,
2. local graph depth is visible in both UI and route state,
3. tests cover depth and neighbor-link behavior,
4. screen remains readable on mobile.

### GFCR-04: Scalable Renderer Path

Problem: SVG is clear and portable but will not support large graph parity.

This lane should not start until `GFCR-01` proves the best SVG-first layout
quality that is reasonable for the package. Renderer scale should solve a real
measured limit, not bypass a weak layout algorithm.

Target:

1. keep `svg` as the stable default,
2. define a `canvas` renderer contract,
3. reserve a future `webgl` renderer seam,
4. keep shared viewer commands independent of renderer internals,
5. add scale fixtures and honest render limits.

Acceptance:

1. unsupported render engines still fail clearly,
2. Canvas/WebGL work cannot break SVG static export,
3. renderer capability checks are typed and tested,
4. large demo fixture has a documented proof path,
5. renderer-specific behavior does not leak into provider DTOs.

### GFCR-05: Node And Edge Authoring

Problem: capture creates notes, but real knowledge work needs lightweight graph
authoring.

Target:

1. edit draft node label/body/tags,
2. create draft links between nodes,
3. mark draft/confirmed/provider-owned posture,
4. merge or alias nodes only through provider-owned actions,
5. expose clear unsupported-action errors for read-only providers.

Acceptance:

1. GraphFakos only shapes provider-neutral action payloads,
2. demo provider can exercise draft authoring in memory,
3. read-only providers show safe failures,
4. no durable memory policy enters GraphFakos.

### GFCR-06: Worker-Backed Capture And Rebuild Loop

Problem: captured notes should be consumable by source/knowledge graph workers,
but GraphFakos must not own those workers.

Target:

1. provider-neutral action result schema,
2. optional queued/rebuilding/done/error status payloads,
3. refresh route or event after provider rebuild,
4. demo worker simulation for local UI iteration,
5. docs for Sophiagraph, PragmaGraph, and OpenMinion host integration.

Acceptance:

1. action status DTOs are provider-neutral,
2. local preview can show queued/rebuilding/error states,
3. tests cover provider support and unsupported-provider behavior,
4. semantics remain provider-owned,
5. action endpoints stay local-preview safe and do not imply hosted auth.

### GFCR-07: Command Palette And Query UX

Problem: filter inputs are functional but not yet a polished graph-navigation
surface.

Target:

1. command palette,
2. saved queries,
3. query syntax validation,
4. search result overlay,
5. quick actions for focus, path, evidence, timeline, and export.

Acceptance:

1. keyboard access works,
2. no-JavaScript fallback remains usable,
3. query parser errors are shown without losing current graph state,
4. docs include common query recipes.

### GFCR-08: Analytics Overlays

Problem: competitive graph tools help users understand structure, not only
inspect nodes one by one.

Target:

1. degree and hub overlays,
2. centrality/community summaries where provider or GraphFakos diagnostics can
   compute them structurally,
3. disconnected component overlays,
4. shortest-path and change-hotspot overlays,
5. provenance/freshness heatmaps based on explicit provider fields.

Acceptance:

1. overlays are structural or provider-declared only,
2. no semantic truth inference is introduced,
3. provider-status and graph canvas agree on counts,
4. visual legend explains every overlay.

### GFCR-09: Collaboration And Export Polish

Problem: review workflows need shareable states and portable evidence.

Target:

1. shareable view URLs,
2. screenshot/export presets,
3. JSON session bundle export,
4. exact-state replay,
5. issue/PR-friendly graph evidence bundles.

Acceptance:

1. exported state can be replayed in static or local preview mode,
2. bundle schemas are versioned,
3. docs explain what is and is not included,
4. generated artifacts remain gitignored unless explicitly published.

### GFCR-10: Visual And Interaction Polish

Problem: the current UI is credible but still feels utilitarian compared with
polished graph products.

Target:

1. smoother pan/zoom and transitions,
2. hover halos and connected-edge emphasis,
3. edge bundling or reduced clutter modes,
4. cluster cards,
5. stronger empty/loading/error states,
6. touch/mobile behavior,
7. accessibility pass for keyboard and screen-reader flows.

Acceptance:

1. visual changes do not reduce static fallback readability,
2. keyboard navigation is tested,
3. mobile viewport smoke covers core screens,
4. design remains aligned with GraphFakos/Sophiagraph/PragmaGraph family style.

## Execution Strategy

Recommended order:

1. GFCR-01 layout engine quality,
2. GFCR-02 saved graph workspaces,
3. GFCR-03 local graph controls,
4. GFCR-04 scalable renderer path,
5. GFCR-06 worker-backed capture loop,
6. GFCR-05 node/edge authoring,
7. GFCR-07 command palette and query UX,
8. GFCR-08 analytics overlays,
9. GFCR-09 collaboration/export polish,
10. GFCR-10 visual and interaction polish.

Reason: layout, saved state, and local controls are the foundation. Renderer
scale and action/rebuild status must be designed before deeper authoring and
analytics work. Visual polish should happen continuously, but the dedicated
visual lane is most valuable after the interaction model stabilizes.

## Historical First Lane Recommendation

`GFCR-01` was promoted and completed as an SVG-first layout quality lane.

Recommended scope:

1. add deterministic seeded positions,
2. improve force/radial/grouped placement in the current SVG renderer,
3. add a lightweight layout quality fixture set for `dense`, `pathfinding`,
   `islands`, and `agent-memory`,
4. define manual pinned-position state if it can round-trip without new
   storage,
5. defer Canvas/WebGL until the improved SVG path hits a measured limit.

The first lane did not include saved workspaces, node authoring, worker status,
or analytics. Those surfaces were completed later in the full package-local
tracker pass.

## Final Decisions For Execution

The executed tracker used these final decisions:

1. Renderer target: keep `svg` as the stable renderer and preserve
   `canvas`/`webgl` as route/viewer state plus a clear static-export fallback
   notice.
2. Saved view persistence: use provider-neutral JSON/route state and replay
   bundles, not implicit local writes.
3. Worker-backed capture integration: add provider-neutral graph action/status
   contracts and local preview submission, but leave workers to providers.
4. Scale target: improve SVG-first quality for current demo fixtures and keep
   larger Canvas/WebGL scale as a future measured lane.
5. Node/edge authoring: expose draft graph-action payloads and unsupported
   provider failures without GraphFakos owning durable graph edits.

## Historical `GFCR-01` Execution Packet

The first implementation lane should be package-only and should touch only the
viewer/layout/demo/test surfaces needed for SVG-first layout quality.

Primary candidate files:

1. `src/graphfakos/ui/app.py` for `_layout_positions()` and layout-specific
   helpers,
2. `src/graphfakos/models.py` only if layout state needs a provider-neutral
   request/viewer-state field,
3. `src/graphfakos/assets/viewer.js` only if pinned positions or layout state
   need runtime synchronization,
4. `src/graphfakos/adapters/demo.py` for layout stress fixtures only,
5. `tests/test_render_static_html.py`,
6. `tests/test_provider_contract.py`,
7. `tests/test_demo_adapter.py`,
8. `tests/test_browser_runtime.py` only if JavaScript behavior changes,
9. package docs if public behavior or commands change.

Execution steps:

1. Freeze the current layout behavior with focused tests around dense,
   pathfinding, islands, and agent-memory demo graphs.
2. Add deterministic layout scoring or position assertions that do not rely on
   screenshots.
3. Improve one layout family at a time, starting with the default force layout
   and grouped/radial placement if needed for visible parity.
4. Preserve all existing route-backed links, inspector behavior, minimap,
   render-limit behavior, and static SVG fallback.
5. Add manual QA notes for desktop and mobile preview commands.
6. Run package validation before declaring the lane ready for PR.

Out of scope for `GFCR-01`:

1. Canvas/WebGL renderer work,
2. saved-workspace persistence,
3. graph authoring actions,
4. worker queues,
5. analytics overlays,
6. provider-specific adapter behavior outside demo fixtures.

Minimum validation for `GFCR-01`:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
PYTHONPATH=src .venv/bin/python3.11 -m pytest -q \
  tests/test_render_static_html.py \
  tests/test_demo_adapter.py \
  tests/test_provider_contract.py
make check
```

Add `make browser-test` if `assets/viewer.js` changes. Add
`make release-check` if public DTOs, package metadata, entrypoints, assets, or
release packaging behavior changes.

## Full Implementation Closeout

The executed scope completed the tracker rows as follows:

1. `GFCR-01`: deterministic SVG-first force-layout quality, selected-node
   centering, pinned-position preservation, and demo layout assertions.
2. `GFCR-02`: `GraphFakosSavedView`, `GraphFakosSavedQuery`, route-backed
   saved state, and saved-view JSON previews.
3. `GFCR-03`: local graph controls for depth, orphans, neighbor links, edge
   clutter, renderer, theme, and analytics overlay.
4. `GFCR-04`: renderer state preservation with honest SVG fallback for static
   exports.
5. `GFCR-05`: graph-action DTOs, provider protocol, authoring panel, and
   unsupported-provider failures.
6. `GFCR-06`: graph-action status contract and local preview action endpoint
   without GraphFakos-owned workers.
7. `GFCR-07`: command palette, saved queries, and query validation feedback.
8. `GFCR-08`: structural analytics DTOs, report analytics, and overlay panel.
9. `GFCR-09`: replay bundle DTOs, replay JSON helper, and `--bundle-out`.
10. `GFCR-10`: theme tokens, hover halos, edge clutter states, panel polish,
    and reduced-motion CSS.
11. `GFCR-CQ`: tracker/spec/docs closeout with validation evidence.

Package boundaries stayed unchanged: providers own persistence, worker queues,
source ingestion, semantic interpretation, trust, freshness, and promotion
policy.

## Visual QA Matrix

Every visual child lane should record at least this matrix:

1. `agent-memory` on explore and neighborhood screens,
2. `source-code` on explore and path screens,
3. `dense` on explore with default and grouped/radial layouts,
4. `pathfinding` on path screen,
5. `provenance` on provenance and explore/evidence routes,
6. `islands` on provider-status and explore screens,
7. desktop viewport around `1440x900`,
8. mobile viewport around `390x844`,
9. static export open without JavaScript assumptions,
10. local preview route/fragment navigation.

Screenshots or manual notes are useful, but they are not enough by themselves;
child lanes should also keep deterministic tests for route/state/DTO behavior.

## Risk Register

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Layout lane becomes renderer rewrite | It delays visible improvement and risks the stable SVG fallback. | Keep `GFCR-01` SVG-first; require a measured limit before `GFCR-04`. |
| GraphFakos starts owning semantics | It would blur Sophiagraph, PragmaGraph, and host responsibilities. | Keep action/status payloads provider-neutral and persistence-free. |
| Screenshot-only proof | Pretty output can hide broken routes, filters, or static fallback. | Require deterministic state/route tests plus visual QA notes. |
| Dependency creep | A heavy frontend stack would weaken package simplicity and embed use. | Keep framework-neutral by default and require explicit dependency review. |
| Cross-package viewer drift | Sibling packages may fork panels or actions. | Keep shared UI in GraphFakos and sibling packages adapter-only. |

## Non-Goals

1. Do not make GraphFakos a durable memory store.
2. Do not make GraphFakos ingest source repositories.
3. Do not add semantic/fact inference to the viewer runtime.
4. Do not require JavaScript for static export readability.
5. Do not bump package version from this planning doc.
6. Do not introduce a framework dependency for the core viewer.

## Review Questions

Default answers for first execution:

1. Layout quality should stay SVG-only for `GFCR-01`; `canvas` is deferred to
   `GFCR-04`.
2. Saved views should be provider-neutral JSON/route state first; local preview
   file writes need `GFCR-02` artifact-policy acceptance.
3. Which provider should be the first real worker-backed capture integration:
   no real provider for `GFCR-01`; decide this in `GFCR-06`.
4. Which graph size should define the next honest scale target: 500 visible
   nodes for SVG-first layout proof; 2,000 and 10,000 are renderer-scale
   follow-ons.
5. Node/edge authoring actions are too early before saved views and worker
   status exist, except for minimal compatibility hooks.

## Validation Expectations

Each child lane should include:

1. focused unit tests for DTO/state behavior,
2. static render tests for no-JavaScript fallback,
3. local preview server tests for interactive behavior,
4. browser runtime tests where JavaScript behavior changes,
5. `make check`,
6. `make browser-test` when runtime code changes,
7. `make release-check` when public/package surfaces change.
