# Provider Workflow Gap Closure

Status: completed
Owner: GraphFakos
Last updated: 2026-07-28

## Purpose

Close the remaining workflow gaps around the dense graph viewer without moving
provider truth into GraphFakos. The viewer should make provider-backed graph
inspection, expansion, editing drafts, saved workspaces, and large-graph
diagnostics visible and testable from one canvas-first surface.

## Current State

GraphFakos already owns the reusable viewer shell, static SVG fallback, WebGL
3D renderer, local preview server, provider envelope loader, desktop backend
token boundary, minimap, performance HUD, capture/action forms, and dense
benchmark envelopes. Sophiagraph and PragmaGraph already expose GraphFakos
adapter or envelope surfaces in sibling packages.

The gap is not another UI rewrite. The gap is making these seams behave like a
coherent product loop:

1. real provider smoke proof for Sophiagraph and PragmaGraph handoffs,
2. visible progressive expansion and omitted-count workflows,
3. graph action lifecycle states users can understand,
4. selected-edge explanations close to the graph surface,
5. portable saved workspace export/import,
6. search and selection overlays that keep context on-canvas,
7. minimap, performance, and render-budget proof for large envelopes, and
8. a desktop wrapper boundary that reuses the same local server.

The follow-up contract is now a portable `GraphFakosWorkspaceManifest`, which
packages viewer state, progressive clusters, raw-versus-rendered budgets,
saved-view replay state, expansion requests, edit/capture affordances, and the
local backend route without moving provider truth into GraphFakos.

## Non-Goals

1. Do not import Sophiagraph or PragmaGraph from production GraphFakos code.
2. Do not make GraphFakos persist provider edits, accept truth, or rebuild
   provider graphs.
3. Do not add a permanent right-side workbench that steals graph width.
4. Do not claim to render 200K or 1M raw browser vertices at once. Large routes
   stay aggregate-envelope plus expansion-cursor flows.
5. Do not fork desktop-specific viewer code. Desktop wrappers launch the same
   backend and viewer routes with a private token.

## Acceptance Lanes

### GFWG-01 Provider Smoke

GraphFakos test coverage should prove that provider-owned data can arrive from:

1. a PragmaGraph viewer envelope,
2. a Sophiagraph GraphFakos adapter, and
3. a third-party host provider.

Sibling package tests must be optional and skip when the sibling source tree is
not present, but they should run in the umbrella checkout.

### GFWG-02 Progressive Expansion

The graph surface must keep expansion visible and provider-owned:

1. selected nodes can request bounded details through `/api/expand`,
2. omitted counts stay visible when raw nodes/edges are not rendered,
3. expansion status reports success or unsupported provider behavior, and
4. static exports show honest route-backed expansion links.

### GFWG-03 Action Lifecycle

Action authoring must describe the lifecycle clearly:

1. `draft`: GraphFakos has built a provider-neutral payload,
2. `queued` or `previewed`: a local preview or provider has received it,
3. `applied`: the provider accepted and refreshed graph state, and
4. `unsupported` or `rejected`: the provider refused or does not implement it.

The viewer must never imply durable persistence until the provider returns an
accepted/applied status.

### GFWG-04 Search And Edge Explanation

Search and selected-edge explanation should stay near the graph surface:

1. ranked search jumps expose matching nodes without replacing the graph,
2. selected edges show "why connected" summary, endpoints, confidence,
   provenance, citations, and path/filter actions,
3. the same data round-trips through investigation-session DTOs, and
4. selected-edge UI must be usable in static HTML.

### GFWG-05 Portable Workspace

Saved workspaces must leave local browser storage:

1. save local camera/theme/selection/filter slots,
2. export all local slots as a portable JSON workspace,
3. import that JSON back into the browser,
4. reject malformed workspace files with a visible error, and
5. keep all of this viewer-local unless a provider explicitly persists a saved
   view.

### GFWG-06 Performance, Minimap, And Desktop Boundary

Large-graph proof must remain visible and wrapper-ready:

1. performance HUD reports live rendered nodes, links, frame, and detail mode,
2. minimap remains available for 3D orientation,
3. 200K and 1M benchmark envelopes expose raw/visible/omitted counts, and
4. desktop wrappers use `graphfakos desktop-backend` with tokenized local
   routes instead of a copied viewer implementation.

## Validation

Focused closeout should run:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_provider_envelope.py \
  tests/test_sibling_provider_smoke.py \
  tests/test_render_static_html.py \
  tests/test_browser_runtime.py \
  tests/test_desktop_backend.py -q
npm --prefix web run build
make browser-e2e
make check
git diff --check
```
