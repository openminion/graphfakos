# Provider Workflow Gap Closure Tracker

Status: completed
Spec: `docs/specs/provider-workflow-gap-closure.md`
Last updated: 2026-07-25

## Goal

Fill the provider-backed workflow gaps around GraphFakos without expanding its
truth boundary: provider smoke, expansion visibility, action lifecycle clarity,
edge explanation, portable saved workspaces, and large-graph wrapper proof.

## Tracker

| ID | Lane | Status | Acceptance | Evidence |
|---|---|---:|---|---|
| GFWG-00 | Review gate | done | Inspect current viewer/server/tests and confirm this is not a UI rewrite lane. | Existing local server, desktop backend, minimap, performance HUD, provider envelope, capture/action, and dense-fixture surfaces are present. |
| GFWG-01 | Provider smoke | done | Optional umbrella smoke proves PragmaGraph envelope and Sophiagraph adapter handoff while standalone GraphFakos remains provider-free. | Added `tests/test_sibling_provider_smoke.py`; focused pytest passed with provider-envelope and desktop-backend coverage. |
| GFWG-02 | Progressive expansion | done | Expansion affordances stay selected-node, omitted-count, and provider-owned. | Existing `/api/expand` behavior remains covered by browser E2E; operating dock preserves provider-owned expansion affordances. |
| GFWG-03 | Action lifecycle | done | Authoring UI shows draft, queued/previewed, applied, unsupported/rejected states honestly. | Static HTML tests now assert explicit lifecycle copy and state names. |
| GFWG-04 | Search and edge explanation | done | Ranked search and selected-edge explanation are graph-adjacent and static-readable. | Operating dock now renders selected-edge explanation from the context graph while ranked search stays scoped to the visible graph. |
| GFWG-05 | Portable workspace | done | Browser saved slots can export/import portable JSON with visible success/error status. | Runtime helpers and browser E2E now cover JSON export/import round trip. |
| GFWG-06 | Performance, minimap, and desktop boundary | done | Dense envelope counts, HUD, minimap, and desktop token backend are covered in focused tests/docs. | Existing desktop-backend and browser E2E gates passed alongside package check. |
| GFWG-07 | Validation and cleanup | done | Focused Python tests, browser build/E2E, package check, and diff whitespace pass. | `55 passed`, `npm --prefix web run build`, `make browser-e2e` with `39 passed`, and `make check` with `149 passed`. |

## Review Checklist

1. Confirm no production GraphFakos code imports provider packages.
2. Confirm saved workspace import/export is browser-local and provider-neutral.
3. Confirm action lifecycle wording does not imply GraphFakos persistence.
4. Confirm selected-edge explanation includes endpoints and evidence counts.
5. Confirm sibling provider smoke skips outside the umbrella checkout.
6. Confirm desktop wrapper guidance points at the existing backend route.

## Closeout Commands

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
