# Third-Party Browser Assets

GraphFakos packages a deterministic browser bundle built from these pinned
dependencies. Node.js is required only when rebuilding the asset, not when
installing or running the Python package.

| Package | Version | License | Purpose |
| --- | --- | --- | --- |
| `3d-force-graph` | 1.80.0 | MIT | Interactive force-directed WebGL scene |
| `three` | 0.185.1 | MIT | WebGL renderer and scene primitives |

The source bundle is built by `npm run build` in `web/`. The generated
`src/graphfakos/assets/renderer-3d.js` is included in the wheel and served
locally without a CDN.
