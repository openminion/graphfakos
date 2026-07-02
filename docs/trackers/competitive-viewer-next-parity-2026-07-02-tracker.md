# GraphFakos Competitive Viewer Next-Parity Tracker

Date: 2026-07-02
Status: `executed`
Owner: `graphfakos`
Related:
`docs/specs/competitive-viewer-next-parity-2026-07-02-spec.md`,
`docs/specs/competitive-viewer-roadmap-2026-07-01-spec.md`,
`docs/trackers/competitive-viewer-roadmap-2026-07-01-tracker.md`,
`docs/ui-contracts.md`,
`README.md`

## Purpose

Track the next GraphFakos improvements needed to close the remaining gap with
Obsidian, Cytoscape.js, Gephi, and Graphistry-style graph products after the
completed July 1 viewer roadmap.

This tracker was promoted for package-local implementation on 2026-07-02.
It does not authorize version bumps, publishing, provider-specific persistence,
or hosted/GPU renderer services.

## Research Summary

Source-backed product lessons:

1. Obsidian Graph View highlights graph/local graph distinction, local graph
   depth, filters, groups, display controls, force controls, and chronological
   animation: `https://obsidian.md/help/plugins/graph`.
2. Cytoscape.js highlights rich graph gestures, desktop/mobile interaction,
   events, box selection, panning, pinch zoom, and graph analysis:
   `https://js.cytoscape.org/`.
3. Gephi highlights interactive filtering by attributes/topology, ForceAtlas
   layout tuning, attribute/metric-driven styling, statistics, label controls,
   drag/pan/zoom/select tools, and export/preview workflows:
   `https://gephi.org/quickstart/` and `https://gephi.org/desktop/`.
4. Graphistry highlights GPU-accelerated visual graph analytics, pivots,
   investigation workflows, embeddable live graphs, shareable workbooks, and
   data-source exploration: `https://www.graphistry.com/`.

Implication for GraphFakos:

1. Improve control depth before renderer complexity where possible.
2. Preserve static SVG fallback and provider-neutral contracts.
3. Use demo fixtures and route/state tests instead of screenshot-only proof.
4. Treat scale claims as measured, not aspirational.

## Board

| ID | Priority | Class | Status | Improvement | Why it matters | Entry condition |
| --- | --- | --- | --- | --- | --- | --- |
| `GFNP-00` | P0 | review gate | `done` | Review and accept or revise the next-parity roadmap. | Prevents another broad viewer push from starting without scope alignment. | Spec/tracker promoted for package-local execution. |
| `GFNP-01` | P1 | renderer | `done` | Canvas renderer prototype with SVG fallback and measured limits. | Needed for denser graphs once control model is stable. | `canvas` renderer is supported behind the renderer contract with SVG fallback retained. |
| `GFNP-02` | P0 | package-ready | `done` | Physics and display control panel. | Closes Obsidian/Gephi readability-control gap fastest. | Route/state fields, controls, saved-view, and replay round-trip landed. |
| `GFNP-03` | P1 | runtime | `done` | Box select and multi-select. | Makes GraphFakos feel like an interactive graph tool rather than a link map. | Multi-select state, shift-click reducer, and selected-subgraph fallback landed. |
| `GFNP-04` | P1 | runtime/action | `done` | Node and edge context menus. | Moves common actions closer to the graph object being inspected. | Accessible node/edge action menus landed as provider-neutral action affordances. |
| `GFNP-05` | P0 | package-ready | `done` | Manual pin layout editor. | Gives users stable mental maps and durable review views. | Route pins, saved-view pins, renderer pins, and reducer pin commands landed. |
| `GFNP-06` | P1 | package-ready | `done` | Attribute-driven styling. | Makes graph meaning visually legible through kind/source/metric rules. | Color/size/edge-width state, active legends, and style-rule script metadata landed. |
| `GFNP-07` | P0 | package-ready | `done` | Advanced filters for attributes and topology. | Brings Gephi-style exploration power to static/code and knowledge graphs. | Degree, connected-to, component, evidence, and cluster filters compose with query syntax. |
| `GFNP-08` | P0 | package-ready | `done` | Community and component explorer. | Helps users understand structure and clusters beyond selected-node inspection. | Structural components and provider-declared cluster route state landed. |
| `GFNP-09` | P2 | package-ready | `done` | Time and diff animation. | Turns existing timeline/diff data into a real exploration flow. | Timeline frame/playback state and static diff-frame metadata landed. |
| `GFNP-10` | P1 | workflow | `done` | Investigation pivot workflow. | Closes Graphistry-style analyst workflow gap without owning provider truth. | Provider-neutral pivot state and replayable case-packet preview landed. |
| `GFNP-CQ` | P0 | closeout | `done` | Validate docs and lane routing. | Keeps the next execution packet clean for future agents. | Focused and full package/workspace gates passed. |

## Recommended Execution Order

1. `GFNP-00`
2. `GFNP-02`
3. `GFNP-05`
4. `GFNP-07`
5. `GFNP-08`
6. `GFNP-03`
7. `GFNP-04`
8. `GFNP-06`
9. `GFNP-09`
10. `GFNP-10`
11. `GFNP-01`
12. `GFNP-CQ`

Reason:

1. `GFNP-02`, `GFNP-05`, `GFNP-07`, and `GFNP-08` improve the current SVG
   workbench materially without a renderer rewrite.
2. `GFNP-03`, `GFNP-04`, and `GFNP-06` deepen direct manipulation after state
   and filtering stabilize.
3. `GFNP-09`, `GFNP-10`, and `GFNP-01` are bigger workflow/scale lanes that
   benefit from the control/state model being mature first.

## Milestones

### `M1: polished small/medium graph workbench`

Rows:

1. `GFNP-02`
2. `GFNP-05`
3. `GFNP-07`
4. `GFNP-08`

Exit condition: users can tune readability, pin stable views, filter by
structure, and inspect clusters on current demo graphs without a new renderer.

### `M2: direct manipulation workbench`

Rows:

1. `GFNP-03`
2. `GFNP-04`
3. `GFNP-06`

Exit condition: users can select, inspect, style, and act on graph objects from
the graph surface with keyboard and static fallback preserved.

### `M3: investigation and scale`

Rows:

1. `GFNP-09`
2. `GFNP-10`
3. `GFNP-01`

Exit condition: users can replay time/diff changes, pivot through an
investigation, and use a measured canvas path for denser graphs.

## Lane Acceptance Detail

### `GFNP-02`

1. Add route/viewer-state fields for center force, repel force, link distance,
   node scale, edge opacity/width, and label density.
2. Preserve no-JavaScript GET-form fallback.
3. Save values in saved views and replay bundles.
4. Add focused route/state and render tests.

### `GFNP-05`

1. Add pin/unpin/reset commands.
2. Persist pinned positions in `GraphFakosSavedView`.
3. Render pins in SVG static fallback.
4. Add browser reducer tests for pin commands.

### `GFNP-07`

1. Add degree, component, connected-to, missing-provenance, warning, freshness,
   and edge-weight filter semantics.
2. Compose with existing query syntax rather than replacing it.
3. Show hidden-node/hidden-edge counts.
4. Cover dense, islands, and provenance demo fixtures.

### `GFNP-08`

1. Add component list and cluster cards.
2. Clearly label GraphFakos structural groups versus provider-declared groups.
3. Add isolate/highlight cluster routes.
4. Add tests for dense clusters and disconnected islands.

### `GFNP-03`

1. Add multi-select state field.
2. Add shift-click and box-select runtime behavior.
3. Add selected-subgraph inspector.
4. Preserve route fallback for selected IDs.

### `GFNP-04`

1. Add accessible context/action menus for nodes and edges.
2. Map all mutations to provider-neutral graph action payloads.
3. Keep unsupported-provider failures explicit.
4. Add keyboard path tests or markup assertions.

### `GFNP-06`

1. Add serializable style-rule DTO or viewer-state field.
2. Support color, size, edge width, and label rules.
3. Generate legends from active rules.
4. Keep provider-specific facts in explicit provider payload fields.

### `GFNP-09`

1. Add snapshot scrubber state.
2. Add diff-frame metadata for added/removed/changed graph items.
3. Add reduced-motion fallback summaries.
4. Add tests for timeline/diff route state and static summary output.

### `GFNP-10`

1. Add investigation pivot state.
2. Add routes for neighbors, shared-neighbor path, selected timeline, and
   evidence bundle.
3. Add replayable case packet metadata.
4. Keep root-cause/truth language provider-owned.

### `GFNP-01`

1. Add a `canvas` renderer behind the existing renderer contract.
2. Keep SVG static export as fallback.
3. Share commands/state across renderers.
4. Add large demo fixture and measured acceptance target.
5. Run `make browser-test` and `make release-check`.

## First Recommended Child Lane

Recommended next implementation lane: `GFNP-02`.

Why:

1. It is the fastest competitor-visible improvement after the July 1 closeout.
2. It strengthens saved views, replay bundles, and future renderer inputs.
3. It avoids starting Canvas before the control/state model is mature.
4. It is package-owned and should not require Sophiagraph, PragmaGraph, or
   OpenMinion changes.

Initial `GFNP-02` scope:

1. route/viewer-state fields for force/display controls,
2. local preview controls and static fallback form,
3. saved-view/replay round-trip,
4. tests in `tests/test_provider_contract.py`, `tests/test_render_static_html.py`,
   and `tests/test_browser_runtime.py` if runtime state changes.

Explicit non-goals for `GFNP-02`:

1. no Canvas/WebGL renderer,
2. no provider-specific style persistence,
3. no graph action/persistence behavior,
4. no hosted collaboration,
5. no version bump.

## Validation Commands

Docs-only review:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make check
```

Implementation lane baseline:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make fix
make check
```

Conditional:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make browser-test
make release-check
```

Workspace closeout when required:

```bash
cd /Users/j/repos/base/agent-frameworks/openminion
.venv/bin/python3.11 -m ruff check .
make lint
```

## Execution Closeout

Implemented package-local surfaces:

1. `GraphFakosRequest` and `GraphFakosViewerState` now carry physics/display,
   multi-select, pinned positions, styling, advanced filters, timeline, and
   investigation pivot state.
2. Routes and CLI arguments round-trip the same provider-neutral viewer state.
3. Static and local-preview UI now include physics controls, advanced filters,
   component explorer, multi-select workbench, attribute styling, timeline
   scrubber, investigation pivot controls, context menus, and canvas renderer
   metadata.
4. The SVG renderer remains the static fallback; `canvas` is now a supported
   progressive renderer contract with a lightweight browser draw path.
5. Saved views and replay bundles preserve route pins and new viewer state.

Validation evidence:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
.venv/bin/python3.11 -m py_compile src/graphfakos/models.py src/graphfakos/ui/app.py src/graphfakos/cli.py
make fix
.venv/bin/python3.11 -m pytest tests/test_provider_contract.py tests/test_render_static_html.py tests/test_browser_runtime.py tests/test_cli.py
```

Focused result: `44 passed`.

Pending final closeout gates:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make check
make browser-test
make release-check
```

Final result:

1. `make check`: `67 passed`.
2. `make browser-test`: `1 passed`.
3. `make release-check`: `67 passed`, build succeeded, `twine check` passed,
   wheel install smoke passed, CLI preview smoke passed.
4. `cd /Users/j/repos/base/agent-frameworks/openminion && .venv/bin/python3.11 -m ruff check .`:
   all checks passed.
5. `cd /Users/j/repos/base/agent-frameworks/openminion && make lint`: all
   checks passed.

## Review Checklist

1. Are the competitor lessons correctly translated into GraphFakos-owned
   package work?
2. Is the renderer lane sequenced correctly, or should `GFNP-01` move earlier?
3. Does `GFNP-02` have enough acceptance detail to execute first?
4. Are static export and keyboard fallback requirements explicit enough?
5. Does each provider-touching item preserve provider ownership of persistence
   and semantics?

## Validation Evidence Log

| Date | Scope | Evidence | Result | Owner |
| --- | --- | --- | --- | --- |
| 2026-07-02 | docs authoring | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make check` | passed; Ruff format check, Ruff lint, and `67 passed` | codex |

## Change Log

| Date | Change | Owner |
| --- | --- | --- |
| 2026-07-02 | Added research-backed next-parity board and recommended `GFNP-02` as first child lane. | codex |
