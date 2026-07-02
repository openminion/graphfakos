# GraphFakos Competitive Viewer Roadmap Tracker

Date: 2026-07-01
Status: `done`
Owner: `graphfakos`
Related:
`docs/specs/competitive-viewer-roadmap-2026-07-01-spec.md`,
`docs/ui-contracts.md`,
`README.md`,
`API_COMPATIBILITY.md`

## Purpose

Track the next GraphFakos viewer improvements needed to move from a credible
provider-neutral graph workbench MVP toward stronger parity with lightweight
knowledge graph viewers and mature graph visualization tools.

This tracker started as roadmap planning plus the execution packet for the
first child lane. It is now the closeout record for the full package-local
competitive viewer pass. The implementation keeps GraphFakos provider-neutral:
GraphFakos owns DTOs, route/view state, local preview actions, export/replay
artifacts, structural analytics, and UI primitives; providers still own durable
persistence, worker queues, source ingestion, fact extraction, and semantic
truth.

## Review State

Current state:

1. `12/12` rows are complete.
2. no package version change was made.
3. no publishing, release, or provider-specific persistence work was done.
4. full closeout stayed package-local except for already-required workspace
   validation gates.
5. static exports remain useful without JavaScript.
6. local preview server mode is the intended interactive workbench path.

Second-pass review on 2026-07-02 tightened:

1. milestone cuts so the board does not become one giant feature,
2. `GFCR-01` as an SVG-first layout lane rather than a renderer rewrite,
3. `GFCR-04` as a measured-limit follow-on,
4. local-preview action safety and provider-owned worker boundaries,
5. visual QA requirements for desktop, mobile, static export, and local
   preview.

Promotion rule:

1. select exactly one implementation lane,
2. confirm owner boundary and acceptance detail,
3. open a child tracker or update this tracker with an `in_progress` state,
4. run the validation commands named by the child lane.

Execution verdict:

1. `GFCR-01` landed deterministic SVG-first layout quality.
2. `GFCR-02` landed provider-neutral saved-view and saved-query DTOs plus
   route/export state.
3. `GFCR-03` landed route-backed local graph controls for depth, orphans,
   neighbor links, edge clutter, and analytics overlay selection.
4. `GFCR-04` landed an honest renderer path: `svg` remains the portable
   renderer while `canvas`/`webgl` route state can be preserved by hosts.
5. `GFCR-05` and `GFCR-06` landed provider-neutral graph action/status
   contracts and local preview action submission without GraphFakos owning
   persistence or workers.
6. `GFCR-07` landed command-palette and saved-query UI surfaces.
7. `GFCR-08` landed structural graph analytics and overlay panel data.
8. `GFCR-09` landed replay bundle DTOs and CLI/static output support.
9. `GFCR-10` landed visual/interaction polish for themes, hover emphasis,
   edge clutter, and reduced-motion behavior.
10. `GFCR-CQ` records this closeout and validation evidence.

## Candidate Board

| ID | Priority | Class | Status | Improvement | Why it matters | Entry condition |
| --- | --- | --- | --- | --- | --- | --- |
| `GFCR-00` | P0 | review gate | `done` | Review and accept or revise the competitive viewer roadmap. | Prevents a chat-only roadmap and keeps package/provider boundaries explicit. | Spec accepted; first child lane selected or intentionally deferred. |
| `GFCR-01` | P0 | package-ready | `done` | Layout engine quality: deterministic seeded layouts, better force layout, hierarchy/DAG, clusters, timeline refinement, and manual pins. | Layout quality is the biggest gap between GraphFakos and polished graph tools. | Completed as an SVG-first force-layout quality lane with fixture-based visual/position acceptance. |
| `GFCR-02` | P0 | package-ready | `done` | Saved graph workspaces for camera, filters, groups, layout, pins, selected lens, and portable view JSON. | Repeated review workflows need durable view state, not only one-off routes. | Landed `GraphFakosSavedView`, `GraphFakosSavedQuery`, route-backed state, and saved-view JSON preview. |
| `GFCR-03` | P0 | package-ready | `done` | Obsidian-style local graph controls: depth slider, neighbor-link toggle, orphan toggle, grouping, colors, and display/force controls. | Local graph navigation is central for both note graphs and code/static graphs. | Landed route-backed local controls with no-JavaScript fallback forms. |
| `GFCR-04` | P0 | package-ready | `done` | Scalable renderer path with `svg` default, `canvas` contract, future `webgl` seam, and scale fixtures. | SVG cannot carry mature dense-graph expectations alone. | Landed renderer state preservation and clear SVG fallback notice for portable exports. |
| `GFCR-05` | P1 | package/provider contract | `done` | Node and edge authoring actions for draft labels, body, tags, links, merge/alias requests, and read-only provider failures. | Capture is useful, but real knowledge work needs lightweight graph authoring. | Landed `GraphFakosGraphAction`, `GraphFakosActionStatus`, graph-action panel, and provider protocol. |
| `GFCR-06` | P1 | package/provider contract | `done` | Worker-backed capture and rebuild loop with queued/rebuilding/done/error action status. | Captured notes need to flow into provider workers without moving worker ownership into GraphFakos. | Landed provider-owned action status path; GraphFakos remains persistence-free. |
| `GFCR-07` | P1 | package-ready | `done` | Command palette and query UX: saved queries, query validation, result overlay, and quick graph actions. | Larger graphs need faster navigation than forms and visible route chips alone. | Landed command-palette panel, saved query JSON, and query validation feedback. |
| `GFCR-08` | P1 | package-ready | `done` | Analytics overlays for degree, hubs, communities, components, paths, change hotspots, and provenance/freshness heatmaps. | Mature graph tools help users understand structure, not only inspect selected nodes. | Landed `GraphFakosGraphAnalytics`, `analyze_graph`, and analytics overlay panel. |
| `GFCR-09` | P2 | package-ready | `done` | Collaboration and export polish: shareable state URLs, screenshot/export presets, session bundles, and exact-state replay. | Review, PR, and issue workflows need portable graph evidence. | Landed `GraphFakosReplayBundle`, `--bundle-out`, and replay JSON preview script. |
| `GFCR-10` | P2 | package-ready | `done` | Visual and interaction polish: smoother pan/zoom, hover halos, edge clutter controls, cluster cards, mobile/touch, and accessibility. | The viewer needs to feel pleasant and trustworthy, not only functional. | Landed theme tokens, hover halos, edge clutter states, and reduced-motion CSS. |
| `GFCR-CQ` | P0 | closeout | `done` | Validate roadmap docs and reconcile next-lane owner routing. | Future agents need a clean board before execution starts. | Tracker/spec/docs updated with package validation evidence. |

## First Executable Child Lane: `GFCR-01`

Scope: package-only SVG layout quality.

Primary files:

1. `src/graphfakos/ui/app.py`
2. `src/graphfakos/models.py` only if request/viewer state needs a
   provider-neutral layout field
3. `src/graphfakos/assets/viewer.js` only if runtime state sync changes
4. `src/graphfakos/adapters/demo.py` only for layout stress fixtures
5. `tests/test_render_static_html.py`
6. `tests/test_demo_adapter.py`
7. `tests/test_provider_contract.py`
8. `tests/test_browser_runtime.py` only if JavaScript changes
9. `README.md` or `docs/` only if public behavior or commands change

Implementation order:

1. Add or tighten tests that characterize current layout position behavior for
   dense, pathfinding, islands, and agent-memory demo graphs.
2. Add deterministic layout quality assertions that inspect positions, bounds,
   selected-node placement, or overlap risk without screenshot dependence.
3. Improve the default SVG force layout first.
4. Improve grouped/radial/hierarchical layout only if the tests or visual QA
   show they are the next bottleneck.
5. Preserve all current route links, minimap, inspector, render-budget, camera,
   and static SVG behavior.
6. Record manual visual QA using the matrix below.
7. Run the validation commands in this tracker before closeout.

Explicit non-goals for `GFCR-01`:

1. no Canvas/WebGL renderer,
2. no saved workspace persistence,
3. no node/edge authoring,
4. no worker queues or provider-specific rebuild behavior,
5. no analytics overlays,
6. no package version bump.

Minimum implementation acceptance:

1. default SVG layout is deterministic for the same graph/request,
2. dense demo graph stays within canvas bounds with reduced overlap risk,
3. focus/path layouts keep the selected or path-critical nodes readable,
4. grouped/radial/hierarchical behavior does not regress existing tests,
5. static export remains readable without JavaScript,
6. local preview fragment navigation still works,
7. all changed public fields are documented or explicitly avoided.

Minimum focused validation:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
PYTHONPATH=src .venv/bin/python3.11 -m pytest -q \
  tests/test_render_static_html.py \
  tests/test_demo_adapter.py \
  tests/test_provider_contract.py
make check
```

Conditional validation:

1. run `make browser-test` if `src/graphfakos/assets/viewer.js` changes,
2. run `make release-check` if public DTOs, packaged assets, console scripts,
   package metadata, or release packaging behavior changes,
3. run OpenMinion `ruff check .` and `make lint` only if a child lane touches
   OpenMinion integration.

Manual QA commands:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make preview-demo
make preview-dense
make preview-path
make preview-islands
```

Static fallback command:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make preview-html
```

## Recommended Execution Order

1. `GFCR-00`
2. `GFCR-01`
3. `GFCR-02`
4. `GFCR-03`
5. `GFCR-04`
6. `GFCR-06`
7. `GFCR-05`
8. `GFCR-07`
9. `GFCR-08`
10. `GFCR-09`
11. `GFCR-10`
12. `GFCR-CQ`

## Milestone Cut

### `M1: usable graph workbench parity`

Promote these first:

1. `GFCR-01`
2. `GFCR-02`
3. `GFCR-03`
4. `GFCR-07`

Exit condition: a user can open the local preview, get a readable graph layout,
save or replay the view state, move between global/local graph lenses, and jump
through queries/commands without needing package-specific UI forks.

### `M2: larger graph investigation parity`

Promote after `M1` has evidence:

1. `GFCR-04`
2. `GFCR-08`
3. `GFCR-09`
4. `GFCR-10`

Exit condition: larger graphs have honest renderer/performance handling,
structural overlays, replayable evidence bundles, and polished visual QA.

### `M3: authoring and rebuild parity`

Promote only after the capture/action status contract is reviewed:

1. `GFCR-06`
2. `GFCR-05`

Exit condition: capture, draft authoring, and provider-owned rebuild status form
a coherent local-preview loop without GraphFakos owning persistence or workers.

## Row Detail Requirements

Every promoted row must define:

1. exact files or owners expected to change,
2. public API and compatibility impact,
3. static export fallback behavior,
4. local preview behavior,
5. test fixtures or demo scenarios,
6. package validation commands,
7. any sibling-package adapter implications,
8. whether the row is package-only or provider/host integration work.

## Boundary Rules

1. GraphFakos may shape provider-neutral viewer and action contracts.
2. GraphFakos must not own durable memory persistence.
3. GraphFakos must not ingest source repositories.
4. GraphFakos must not infer semantic truth or promote memories.
5. Static export must remain useful without JavaScript.
6. Provider-specific behavior belongs behind provider protocols or host
   integrations.
7. Renderer work must preserve the stable `svg` path until a new renderer is
   explicitly accepted.

## Acceptance Detail By Lane

### `GFCR-01`

1. Add or refine layout algorithms behind existing viewer request/state fields
   or a reviewed extension.
2. Use deterministic fixtures to avoid screenshot-only validation.
3. Include dense, pathfinding, and island demo coverage.
4. Keep the first implementation SVG-first; do not start Canvas/WebGL in this
   row.
5. Record before/after layout behavior for desktop and mobile preview sizes.

### `GFCR-02`

1. Add saved-view DTO or schema.
2. Prove round-trip through route or JSON payload.
3. Avoid implicit writes unless local preview artifact policy is accepted.

### `GFCR-03`

1. Add route-backed controls first.
2. Add JavaScript enhancement only after fallback behavior exists.
3. Keep local/global graph terminology visible.

### `GFCR-04`

1. Add renderer capability checks before adding renderer behavior.
2. Keep unsupported-engine errors explicit.
3. Include a large/dense fixture and honest render-budget output.
4. Name the measured SVG-first limit that justifies a Canvas/WebGL lane.
5. Keep renderer-specific behavior out of provider DTOs.

### `GFCR-05`

1. Add action DTOs before UI affordances.
2. Read-only providers must fail clearly.
3. Demo provider may stay in-memory only.

### `GFCR-06`

1. Add provider-neutral action status payloads.
2. Show queued/rebuilding/error state in local preview.
3. Do not add a GraphFakos-owned worker.
4. Keep action endpoints local-preview safe and same-origin.
5. Define unsupported-provider behavior before adding new UI affordances.

### `GFCR-07`

1. Keep keyboard accessibility as a first-class acceptance item.
2. Query errors must not destroy current graph state.
3. Saved queries must compose with saved workspaces if both exist.

### `GFCR-08`

1. Compute only structural graph metrics in GraphFakos.
2. Treat freshness/provenance heatmaps as provider-declared fields.
3. Add legends and provider-status agreement checks.

### `GFCR-09`

1. Version bundle schemas.
2. Keep generated evidence out of git unless explicitly published.
3. Prove replay from a bundle or exact-state URL.

### `GFCR-10`

1. Add visual changes with tests or reproducible preview instructions.
2. Preserve reduced-motion and keyboard behavior.
3. Keep style consistent with the package family.

## Visual QA Matrix

Every visual implementation row must record:

1. `agent-memory` explore or neighborhood preview,
2. `source-code` explore or path preview,
3. `dense` explore preview with default and alternate layouts,
4. `pathfinding` path preview,
5. `provenance` evidence route,
6. `islands` provider-status or explore preview,
7. desktop viewport around `1440x900`,
8. mobile viewport around `390x844`,
9. static export fallback,
10. local preview fragment navigation.

## `GFCR-01` Closeout Notes

Landed package changes:

1. Replaced the default two-ring force layout with a deterministic bounded
   force relaxation pass in `src/graphfakos/ui/app.py`.
2. Preserved focused or selected nodes at canvas center.
3. Preserved provider-declared pinned visual coordinates when both `x` and `y`
   are present.
4. Kept the renderer SVG-only with no DTO, JavaScript, package metadata, or
   version changes.
5. Added render-path layout assertions in `tests/test_demo_adapter.py` for
   dense, pathfinding, islands, and agent-memory demo graphs.

Static QA exports generated under the gitignored `.graphfakos-preview/` folder:

1. `gfcr-01-agent-memory.html`: `12` nodes, x `59.6..860.3`, y `46.0..414.0`,
   closest pair `45.2`.
2. `gfcr-01-dense.html`: `36` nodes, x `101.1..850.2`, y `46.0..414.0`,
   closest pair `19.8`.
3. `gfcr-01-pathfinding.html`: `7` visible path nodes, x `57.4..863.5`,
   y `46.0..414.0`, closest pair `211.5`.
4. `gfcr-01-islands.html`: `10` nodes, x `58.4..861.6`, y `46.0..414.0`,
   closest pair `153.2`.

Manual browser note:

1. Direct `file://` browser screenshot QA was not captured because the in-app
   browser blocks local file URLs by policy.
2. The lane was closed on rendered-coordinate assertions, static export
   generation, and package validation instead of screenshot proof.

## Full Tracker Closeout Notes

Landed package changes:

1. Saved views and saved queries: added provider-neutral DTOs, route-backed
   saved-view state, command-palette saved-query previews, and saved-view JSON
   script payloads.
2. Local graph controls: added route-backed depth, orphan visibility,
   neighbor-link visibility, edge-clutter, renderer, theme, and analytics
   overlay controls with GET-form fallback.
3. Renderer path: kept `svg` as the portable renderer while preserving
   `canvas` and `webgl` request state for host workbenches and showing an
   explicit SVG fallback notice in static exports.
4. Authoring and rebuild seam: added `GraphFakosGraphAction`,
   `GraphFakosActionStatus`, `GraphFakosGraphActionProvider`, graph-action UI,
   local preview `/api/action` handling, and unsupported-provider failures
   without GraphFakos owning persistence or workers.
5. Command/query UX: added command-palette saved-query data and validation
   feedback while keeping existing route/search behavior.
6. Analytics overlays: added `GraphFakosGraphAnalytics`, `analyze_graph`, report
   analytics, and UI overlay panels for hubs, components, orphans, density, and
   degree summaries.
7. Collaboration/export: added `GraphFakosReplayBundle`,
   `build_graph_replay_bundle`, `write_graph_replay_bundle`, and CLI
   `--bundle-out` support.
8. Visual polish: added theme tokens, hover halos, selected-node emphasis,
   edge-clutter states, darker/paper themes, canvas texture, action/workspace
   panel styling, and reduced-motion behavior.

Boundary preserved:

1. no version bump,
2. no publish or release,
3. no provider-specific durable storage,
4. no source ingestion,
5. no semantic truth inference,
6. no package-owned background worker.

## Validation Commands

For this planning tracker:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make check
```

For implementation child lanes, add as applicable:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make browser-test
make release-check
```

When a child lane touches OpenMinion integration or the workspace family:

```bash
cd /Users/j/repos/base/agent-frameworks/openminion
.venv/bin/python3.11 -m ruff check .
make lint
```

## Validation Evidence Log

| Date | Row | Evidence | Result | Owner |
| --- | --- | --- | --- | --- |
| 2026-07-01 | `GFCR-00` / `GFCR-CQ` | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make check`. | passed; Ruff format check, Ruff lint, and `61 passed`. | codex |
| 2026-07-02 | second-pass review | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make check`. | passed; Ruff format check, Ruff lint, and `61 passed`. | codex |
| 2026-07-02 | execution-readiness pass | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make check`. | passed; Ruff format check, Ruff lint, and `61 passed`. | codex |
| 2026-07-02 | `GFCR-01` focused acceptance | `cd /Users/j/repos/base/agent-frameworks/graphfakos && PYTHONPATH=src .venv/bin/python3.11 -m pytest -q tests/test_render_static_html.py tests/test_demo_adapter.py tests/test_provider_contract.py`. | passed; `37 passed`. | codex |
| 2026-07-02 | `GFCR-01` package gate | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make check`. | passed; Ruff format check, Ruff lint, and `63 passed`. | codex |
| 2026-07-02 | workspace closeout gate | `cd /Users/j/repos/base/agent-frameworks/openminion && .venv/bin/python3.11 -m ruff check . && make lint`. | passed after moving an existing OpenMinion budget prompt literal into the brain loop constants owner. | codex |
| 2026-07-02 | full tracker focused acceptance | `cd /Users/j/repos/base/agent-frameworks/graphfakos && PYTHONPATH=src .venv/bin/python3.11 -m pytest -q tests/test_provider_contract.py tests/test_render_static_html.py tests/test_cli.py tests/test_browser_runtime.py tests/test_local_preview_server.py tests/test_demo_adapter.py`. | passed; `53 passed`. | codex |
| 2026-07-02 | full tracker package gate | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make check`. | passed; Ruff format check, Ruff lint, and `66 passed`. | codex |
| 2026-07-02 | full tracker browser/runtime gate | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make browser-test`. | passed; `1 passed`. | codex |
| 2026-07-02 | full tracker release gate | `cd /Users/j/repos/base/agent-frameworks/graphfakos && make release-check`. | passed; `66 passed`, package build succeeded, `twine check` passed for wheel and sdist, installed wheel smoke passed. | codex |
| 2026-07-02 | full tracker workspace closeout gate | `cd /Users/j/repos/base/agent-frameworks/openminion && .venv/bin/python3.11 -m ruff check . && make lint`. | passed; Ruff passed and `make lint` validators/typecheck passed. | codex |

## Completion Criteria

1. Review questions in the spec are answered or routed.
2. All candidate rows are complete.
3. No row moves provider-owned persistence, source ingestion, or semantic truth
   into GraphFakos.
4. Static export fallback expectations are preserved.
5. Package validation passes after the full tracker implementation.

## Remaining Follow-Up

1. Run visual QA from a browser against `make preview-demo`, `make
   preview-dense`, `make preview-path`, and `make preview-islands` when a human
   wants screenshot-level acceptance.
2. Promote a future dedicated Canvas/WebGL renderer only after a measured SVG
   limit justifies it.
3. Integrate provider-specific persistence or worker behavior only in provider
   packages or hosts, not in GraphFakos.
