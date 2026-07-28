# Viewer Product Hardening Tracker

Status: done
Spec: `docs/specs/viewer-product-hardening.md`
Last updated: 2026-07-28

## Goal

Make the graph viewer easier to review and safer to iterate by adding explicit
mode semantics, visual QA guards, local run commands, and large-route proof.

## Tracker

| ID | Lane | Status | Acceptance | Evidence |
|---|---|---:|---|---|
| GFPH-00 | Review gate | done | Inspect current dense/provider trackers, UI contracts, and live files before editing. | Current trackers are complete; this lane starts a new hardening pass. |
| GFPH-01 | Visual QA guards | done | Dense screenshots assert canvas size, theme, HUD, and label-pressure limits without pixel baselines. | `make visual-qa` passed, 3 visual routes. |
| GFPH-02 | Dense mode semantics | done | Overview, islands, cluster, local, and precision controls map clearly into WebGL detail behavior. | `npx playwright test tests/viewer.spec.js` passed, 39 tests. |
| GFPH-03 | 1M route honesty | done | 1M route proves aggregate scale, omitted counts, and render budget instead of raw-node claims. | `make browser-e2e` passed, including 1M provider envelope route. |
| GFPH-04 | Local run docs | done | Docs expose 1K, 200K, 1M, browser E2E, and visual QA commands in one place. | `docs/local-viewer-testing.md` added and linked from `docs/README.md`. |
| GFPH-05 | Maintainability sweep | done | Run post-authoring review on changed files and keep generated bundle rebuilt from source. | `npm run build` rebuilt `src/graphfakos/assets/renderer-3d.js`; changed-file sweep removed generated filesystem noise. |
| GFPH-06 | Validation closeout | done | Run focused browser/Python checks, WebGL build, visual QA, and package check. | `npm run build`, `npx playwright test tests/viewer.spec.js`, `make visual-qa`, `make browser-e2e`, and `make check` passed. |

## Validation Evidence Log

| Date | Command | Result |
|---|---|---|
| 2026-07-28 | `cd web && npm run build` | Passed; rebuilt packaged WebGL bundle from source. |
| 2026-07-28 | `cd web && npx playwright test tests/viewer.spec.js` | Passed; 39 browser tests. |
| 2026-07-28 | `make visual-qa` | Passed; 3 visual routes. |
| 2026-07-28 | `make browser-e2e` | Passed; 42 browser tests. |
| 2026-07-28 | `make check` | Passed; format, lint, structure validators, and 151 Python tests. |

## Change Log

| Date | Change |
|---|---|
| 2026-07-28 | Added visual QA thresholds, dense mode semantics, local run docs, and large-route proof for GraphFakos viewer hardening. |

## Review Checklist

1. Confirm visual QA screenshots are review evidence, not brittle visual
   baselines.
2. Confirm mode controls do not expand GraphFakos truth or persistence.
3. Confirm 1M docs explain aggregate envelopes and omitted counts.
4. Confirm local commands are portable and do not include machine-local paths.
5. Confirm `src/graphfakos/assets/renderer-3d.js` is rebuilt, not hand-edited.
