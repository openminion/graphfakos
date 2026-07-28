# Visual QA

GraphFakos has automated browser E2E coverage for viewer behavior and a
separate visual QA lane for dense graph review screenshots.

Use visual QA when changing:

1. WebGL graph layout, labels, node scale, edges, minimap, or theme contrast,
2. dense 200K or 1M provider-envelope rendering,
3. graph surface spacing, controls, or inspector placement, or
4. screenshot-ready product presentation.

Run:

```bash
cd graphfakos
make visual-qa
```

The command regenerates benchmark fixtures, starts the same local preview
servers used by browser E2E, verifies that each route reaches WebGL-ready
state, checks graph-surface size, theme, performance HUD, and label-pressure
thresholds, and writes current screenshots under `web/test-results/`.

Current visual routes:

1. dense demo in space theme,
2. 200K aggregate provider envelope in islands layout,
3. 1M aggregate provider envelope in islands layout.

This is a review lane, not a provider-truth test. GraphFakos still renders
provider-neutral DTOs; providers own graph truth, semantic search, persistence,
and rebuild policy.

Keep `make browser-e2e` for interaction regressions and `make visual-qa` for
visual review evidence. Do not replace focused behavior assertions with pixel
expectations unless a route is stable enough for intentional baseline
maintenance.
