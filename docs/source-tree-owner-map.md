# GraphFakos Source Tree Owner Map

Status: semantic alpha

Purpose: explain the `graphfakos` source-tree owners without treating deep
imports as blanket public promises.

## Public contract

The public alpha surface is documented in:

1. `README.md`
2. `API_COMPATIBILITY.md`
3. `docs/`

The preferred entrypoint is `graphfakos`, with additional stable import roots
for adapters, contracts, models, provider, render, server, static, testing,
and `graphfakos.ui`.

## Root

- `README.md`: public identity, scope, and quick start
- `API_COMPATIBILITY.md`: stable import roots and compatibility expectations
- `RELEASING.md`: package release proof
- `CONTRIBUTING.md`: contributor workflow and PR shape
- `CODE_QUALITY.md`: package-local code-quality rules
- `SECURITY.md`: vulnerability reporting and package security boundary
- `SUPPORT.md`: public support scope
- `CODE_OF_CONDUCT.md`: contributor conduct expectations
- `LICENSE` and `NOTICE`: legal terms and notices
- `pyproject.toml`: package metadata, dependencies, and console scripts
- `MANIFEST.in`: source-distribution file policy
- `Makefile`: package-local development, lint, test, and release commands

## Docs

- `docs/README.md`: package-local docs index and integration model
- `docs/artifact-interchange.md`: portable artifact replay and review workflow
- `docs/custom-provider-example.md`: package-neutral third-party provider example
- `docs/ui-contracts.md`: shared viewer contract, wrapper responsibilities,
  and provider-adapter expectations
- `docs/accessibility.md`: WCAG 2.2 AA automated/manual viewer proof matrix
- `docs/source-tree-owner-map.md`: this source-tree owner map

## Examples

- `examples/provider_host.py`: runnable public-import-only provider showing
  host-owned truth, knowledge capture, graph action preview, and static HTML
  rendering through GraphFakos

## Source

- `src/graphfakos/models.py`: provider-neutral graph DTOs and serialized
  contract policy
- `src/graphfakos/_model_values.py`: strict shared value/coercion parsing for
  DTO deserialization
- `src/graphfakos/artifacts.py`: persisted graph artifact schema, load, and
  write helpers
- `src/graphfakos/provider.py`: provider protocol, validation helpers, and
  provider-neutral diagnostics
- `src/graphfakos/contracts.py`: public adapter/DTO contract exports
- `src/graphfakos/render.py`: public viewer rendering exports
- `src/graphfakos/static.py`: static HTML rendering entrypoints
- `src/graphfakos/server.py`: local preview server primitives
- `src/graphfakos/live.py`: structural patch, revision/cursor, replay, bounded
  reference-provider, and live diagnostics contracts
- `src/graphfakos/cli.py`: command-line parsing and execution
- `src/graphfakos/py.typed`: PEP 561 marker for typed package consumers
- `src/graphfakos/ui/app.py`: thin provider-loading and screen-composition
  entrypoint; it does not own graph algorithms, layout math, or panel details
- `src/graphfakos/ui/viewer/routing.py`: route serialization and request query
  parsing
- `src/graphfakos/ui/viewer/graph_ops.py`: provider-neutral traversal,
  components, ranking, path selection, and render-budget selection
- `src/graphfakos/ui/viewer/filtering.py`: provider-neutral query parsing and
  graph filtering
- `src/graphfakos/ui/viewer/layout.py`: deterministic coordinate and force-layout
  calculations
- `src/graphfakos/ui/viewer/canvas.py`: graph canvas, minimap, label budgets,
  inspector overlay, and visual legend
- `src/graphfakos/ui/viewer/controls.py`: graph lens, workspace, physics, and
  interaction controls
- `src/graphfakos/ui/viewer/discovery.py`: search, expansion, graph tables,
  evidence coverage, and facet discovery
- `src/graphfakos/ui/viewer/analysis.py`: readability, analytics, selection,
  styling, and investigation panels
- `src/graphfakos/ui/viewer/navigation.py`: presets, navigation maps, lenses,
  and relationship trails
- `src/graphfakos/ui/viewer/authoring.py`: provider-neutral knowledge capture
  and graph-action forms; providers still own persistence and semantic truth
- `src/graphfakos/ui/viewer/evidence.py` and `diffing.py`: evidence summaries
  and graph snapshot comparison
- `src/graphfakos/ui/viewer/html.py`, `shell.py`, `panels.py`, and `styles.py`:
  shared presentation primitives, graph-first shell placement, and stylesheet
- `src/graphfakos/assets/viewer.js`: provider-neutral state, command, history,
  fallback-SVG, and custom-element runtime
- `web/src/renderer.js`: source owner for the true WebGL 3D renderer; built to
  `src/graphfakos/assets/renderer-3d.js` for offline wheel use
- `web/tests/`: pinned real-browser interaction, responsive, fallback,
  accessibility, and scale proof
- `src/graphfakos/adapters/file.py`: file-backed provider for persisted graph
  artifacts
- `src/graphfakos/adapters/demo.py`: demo provider lifecycle, captures,
  graph actions, and public scenario dispatch
- `src/graphfakos/adapters/demo_scenarios.py`: deterministic scenario graph,
  provenance, citation, facet, and visual construction
- `src/graphfakos/adapters/fixture.py`: fake third-party provider
- `src/graphfakos/testing/assertions.py`: reusable viewer assertions

## Tests

- `tests/test_imports.py`: public import roots
- `tests/test_provider_contract.py`: provider protocol and DTO behavior
- `tests/test_render_static_html.py`: static viewer rendering
- `tests/test_local_preview_server.py`: local server route smoke
- `tests/test_live_graph.py`: patch, revision, replay, and bounded-provider proof
- `tests/test_live_server.py`: loopback SSE, origin, authorization, and client-limit proof
- `tests/test_cli.py`: CLI smoke and JSON output
- `tests/test_artifacts.py`: artifact round-trip and file-backed provider proof
- `tests/test_release_check.py`: release script shape
- `tests/test_quality_scripts.py`: package-local validator baselines and guard entrypoints
- `tests/test_fixture_adapter.py`: fake third-party provider compatibility
- `tests/test_demo_adapter.py`: generated demo provider scenarios
- `scripts/generate_benchmark_envelopes.py`: deterministic 1K, 200K, and 1M
  provider-envelope fixtures with honest omitted counts
- `scripts/validate/`: package-local complexity, structure, public-surface, and
  hygiene validators
- `scripts/baselines/`: ratchet baselines consumed by package-local validators
