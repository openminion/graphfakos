# GraphFakos API Compatibility

GraphFakos is a `0.0.6` semantic-alpha release. Public APIs are
intentionally small and centered on provider-neutral graph viewing.

## Stable Import Roots

- `graphfakos`
- `graphfakos.adapters`
- `graphfakos.browser`
- `graphfakos.contracts`
- `graphfakos.models`
- `graphfakos.provider`
- `graphfakos.render`
- `graphfakos.renderers`
- `graphfakos.server`
- `graphfakos.live`
- `graphfakos.static`
- `graphfakos.testing`
- `graphfakos.ui`

## Compatibility Promise

GraphFakos keeps the following surfaces stable within the `0.0.x` line unless a
release note says otherwise:

- DTO class names
- dynamic viewer DTO names for state, command, event, expansion request, and
  knowledge-capture/theme payloads
- investigation-session and connection-explanation DTO names and top-level
  report keys
- optional expansion provider protocol and `load_expanded_graph()` helper name
- typed `GraphFakosPerspective`, `GraphFakosInspectorField`, and
  `GraphFakosInspectorSchema` declaration names
- provider declaration reader names `graph_perspectives()`,
  `inspector_schema_for()`, and `inspector_values()`
- deterministic demo scenario names and `DemoGraphProvider` for viewer
  iteration
- `viewer_runtime_script()` helper name and packaged `assets/viewer.js`
  availability
- `SUPPORTED_RENDER_ENGINES` and `validate_render_engine()` helper names
- provider protocol method names
- optional knowledge-capture provider protocol and `GraphFakosKnowledgeCapture`
  field names
- optional `GraphFakosSnapshot` field names and top-level graph snapshot keys
- persisted graph artifact field names and the `graphfakos.artifacts` helper
  names
- provider-neutral `diagnose_graph()` output shape
- `screen_manifest()` keys for `screen`, `label`, `route`, and `summary`
- `build_viewer_route()`, `parse_viewer_request()`, and
  `query_syntax_reference()` helper names
- report helper names in `graphfakos.static` / `graphfakos.render`
- console script names
- local preview server helper names and same-origin fragment response behavior
- typed live patch/revision/cursor/status/replay contracts and atomic patch
  application helpers
- local preview action handler helper shape and `POST /api/knowledge` JSON
  behavior
- local preview `POST /api/import`, `POST /api/expand`, and `POST /api/reset`
  endpoint purposes and top-level `ok`, `graph`, and `error` response keys
- screen manifest helper names
- testing assertion helper names
- PEP 561 type marker presence through `graphfakos/py.typed`

Provider-specific semantics are not part of GraphFakos core compatibility.
Sophiagraph, PragmaGraph, OpenMinion, and third-party providers own their own
semantic compatibility promises.
