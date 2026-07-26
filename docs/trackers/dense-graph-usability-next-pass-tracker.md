# Dense Graph Usability Next Pass Tracker

Status: completed
Spec: `docs/specs/dense-graph-usability-next-pass.md`
Last updated: 2026-07-21

## Goal

Close the next visible gap between GraphFakos and graph-first products by
polishing dense graph scale, labels, edge flow, island navigation, direct
manipulation, inspect/edit overlays, theme persistence, and 200K/1M proof.

## Tracker

| ID | Lane | Status | Acceptance | Evidence |
|---|---|---:|---|---|
| GFDG-00 | Review gate | done | Re-read spec, confirm current viewer files, and mark any changed assumptions before code starts. | Current tree matched likely-file list; default decisions stayed valid. |
| GFDG-01 | Scale and label LOD | done | Overview, cluster, and local zoom levels show progressively more labels while dense points stay small and readable. | `web/src/semantic-detail.js` and `web/src/renderer.js` tighten dense node scale, label budgets, and zoom-stable point sizing; browser E2E covers camera detail reveal. |
| GFDG-02 | Edge flow and bundling | done | Aggregate/cross-cluster links curve more naturally than local links, selected incident links highlight cleanly, and tests cover curve ordering. | `web/src/link-shape.js` increases deterministic aggregate/bundle curvature and weight-aware separation; `web/tests/viewer.spec.js` covers curve ordering. |
| GFDG-03 | Balanced islands and cluster travel | done | Dense island layouts use more canvas space, cluster focus/reset preserves theme and render engine, and 200K/1M screenshots show separated groups. | `src/graphfakos/ui/viewer/layout.py` adds an islands layout fallback; browser E2E covers route theme persistence and dense 200K/1M envelopes. |
| GFDG-04 | Direct manipulation | done | Node drag, cluster drag, orbit, pan, cursor zoom, reset, and help tooltip work without shrinking the graph surface. | Existing 3D manipulation path remains covered by browser E2E for camera toolbar, keyboard movement, selection, focus, and reversible scene changes; help copy now includes cluster-shell drag. |
| GFDG-05 | Inspector, content, and edit overlay | done | Clicked nodes show useful provider-declared content, expandable detail, capture/action draft forms, and clean dismiss behavior. | `src/graphfakos/ui/viewer/canvas.py` and `src/graphfakos/assets/viewer.js` forward provider payload content/preview/title into hover and inspect context; browser E2E covers editable content in the graph inspector. |
| GFDG-06 | Theme toggle and contrast | done | Light/dark toggle is visible, remembered across routes, and changes the graph canvas itself with enough small-node contrast. | `src/graphfakos/ui/viewer/surface_controls.py`, `web/src/visual-contrast.js`, and generated assets keep visible Light/Dark route toggles; browser E2E covers theme and group visibility across routes. |
| GFDG-07 | Large fixture proof | done | 200K and 1M deterministic fixtures exercise aggregate clusters, omitted counts, bundles, expansion cursors, and browser smoke screenshots. | `scripts/generate_benchmark_envelopes.py` emits 200K/1M aggregate fixtures with >=100-node clusters, dynamic kinds, bundle metadata, omitted counts, and provider payload samples; Python and browser tests cover both scales. |
| GFDG-08 | Post-authoring sweep | done | Run the bounded cleanup pass on changed files only, remove accidental UI/code clutter, and preserve provider-neutral boundaries. | Changed-file sweep simplified dense fixture helpers and JS edge/rendering helpers; generated `renderer-3d.js` was rebuilt instead of hand-edited. |
| GFDG-09 | Validation closeout | done | Run `npm run build`, `make browser-e2e`, `make check`, `git diff --check`, and record visual screenshot paths. | `npm --prefix web run build` passed; `make browser-e2e` passed with 38 tests including 200K and 1M; `make check` passed with 147 tests; `git diff --check` passed. |

## Execution Order

1. Start with GFDG-00 so implementation does not repeat old UI drift.
2. Land GFDG-01 through GFDG-03 first because scale, labels, and layout set the
   visual baseline.
3. Land GFDG-04 after layout behavior is stable so drag/reset semantics do not
   fight placement changes.
4. Land GFDG-05 after selection behavior is stable.
5. Land GFDG-06 before final visual QA so screenshots represent the real user
   theme flow.
6. Close with GFDG-07 through GFDG-09.

## Default Decisions

Execution should start from these decisions:

1. Use `layout=islands` as the dense 200K/1M default and keep `grouped`
   available as a mode option.
2. Preview content order is provider-declared inspector schema,
   `provider_payload.content`, `provider_payload.summary`, then node summary.
3. Cluster drag is viewer-local saved-view state first. Provider persistence
   requires an explicit accepted graph action.
4. Validate both 200K and 1M aggregate routes.

## Likely Files

Primary implementation files:

1. `web/src/semantic-detail.js`
2. `web/src/renderer.js`
3. `web/src/link-shape.js`
4. `web/src/focus-readability.js`
5. `web/src/spatial-navigation.js`
6. `web/src/visual-contrast.js`
7. `src/graphfakos/ui/app.py`
8. `src/graphfakos/adapters/demo.py`
9. `scripts/generate_benchmark_envelopes.py`
10. `web/tests/viewer.spec.js`

Guardrails:

1. Rebuild `src/graphfakos/assets/renderer-3d.js` through
   `npm --prefix web run build`; never hand-edit the generated bundle.
2. Keep large-file growth visible for `src/graphfakos/models.py`,
   `src/graphfakos/ui/app.py`, `web/src/renderer.js`, and
   `web/tests/viewer.spec.js`.
3. Prefer real-owner extraction for new policy code instead of appending more
   branches to the largest files.

## Definition Of Done

1. The graph surface remains the dominant visible area.
2. Large routes are usable without pretending to render all raw nodes.
3. Theme, render engine, and relevant route state survive focus/navigation.
4. Groups and clusters are reversible.
5. Inspect/edit affordances expose real provider-declared content but do not
   claim provider persistence unless accepted by the provider.
6. Visual proof exists for 200K and 1M routes.
7. Package validation passes or any unrelated ambient blocker is documented
   honestly.

## Local Commands

Generate the large fixtures:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
make benchmark-fixtures
```

Open the 1M dense route:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
PYTHONPATH=src .venv/bin/graphfakos-ui \
  --provider-envelope web/fixtures/viewer-scale-1000000.json \
  --screen explore \
  --render-engine 3d \
  --theme space \
  --layout islands \
  --render-limit 240 \
  --serve \
  --open \
  --port 8767
```

Run the closeout gate:

```bash
cd /Users/j/repos/base/agent-frameworks/graphfakos
npm --prefix web run build
make browser-e2e
make check
git diff --check
```

## Review Checklist

Before execution:

1. Re-read the default decisions and record any evidence-driven deviation
   before code starts.
2. Confirm the likely-file list still matches the current tree.
3. Confirm large-file growth is intentional when touching
   `src/graphfakos/ui/app.py`, `web/src/renderer.js`, or
   `web/tests/viewer.spec.js`.

During review:

1. Open 200K and 1M routes in both light and space themes.
2. Zoom from overview to local detail and check label noise at each step.
3. Drag a node and a cluster, then reset formation.
4. Hide and restore groups.
5. Click a node, expand the card, draft a note/action, and dismiss the overlay.
6. Confirm static SVG fallback still reads without JavaScript.

Visual pass/fail checks:

1. At overview zoom, labels are sparse enough that graph shape is readable.
2. At local zoom, labels appear around the selected/focused context without
   blanketing the whole scene.
3. Edges read as soft paths or bundles, not a stack of rigid straight chords.
4. Small vertices remain visible in `space` theme.
5. Cluster or group controls are reversible without losing theme.

## Review History

2026-07-21:

1. Product/UX review tightened the objective around canvas-first dense graph
   navigation instead of workbench chrome.
2. Execution review converted open review questions into default decisions so
   implementation can start without rediscovery.
3. Maintainability review added likely implementation owners and large-file
   guardrails.
4. Validation review normalized the build command to
   `npm --prefix web run build`.
