# GraphFakos API Compatibility

GraphFakos is a `0.0.1` semantic-alpha package. Public APIs are intentionally
small and centered on provider-neutral graph viewing.

## Stable Import Roots

- `graphfakos`
- `graphfakos.adapters`
- `graphfakos.contracts`
- `graphfakos.models`
- `graphfakos.provider`
- `graphfakos.render`
- `graphfakos.server`
- `graphfakos.static`
- `graphfakos.testing`
- `graphfakos.ui`

## Compatibility Promise

GraphFakos keeps the following surfaces stable within the `0.0.x` line unless a
release note says otherwise:

- DTO class names
- provider protocol method names
- optional `GraphFakosSnapshot` field names and top-level graph snapshot keys
- provider-neutral `diagnose_graph()` output shape
- `screen_manifest()` keys for `screen`, `label`, `route`, and `summary`
- `build_viewer_route()`, `parse_viewer_request()`, and
  `query_syntax_reference()` helper names
- report helper names in `graphfakos.static` / `graphfakos.render`
- console script names
- local preview server helper names
- screen manifest helper names
- testing assertion helper names
- PEP 561 type marker presence through `graphfakos/py.typed`

Provider-specific semantics are not part of GraphFakos core compatibility.
Sophiagraph, PragmaGraph, OpenMinion, and third-party providers own their own
semantic compatibility promises.
