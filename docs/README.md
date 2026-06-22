# GraphFakos Docs

GraphFakos is the shared graph lens package for visualizing provider-neutral
knowledge graphs.

Start with:

- [Source tree owner map](source-tree-owner-map.md)
- [UI contracts](ui-contracts.md)
- [API compatibility](../API_COMPATIBILITY.md)
- [Release process](../RELEASING.md)

## Integration Model

GraphFakos owns viewer contracts and UI primitives. Provider packages own
adapters:

- Sophiagraph maps durable memory graph records into GraphFakos DTOs.
- PragmaGraph maps observed source graph snapshots into GraphFakos DTOs.
- OpenMinion can embed or link GraphFakos through the same DTOs.
- Third-party providers can implement the provider protocol directly.

Package-local `*-ui` commands should be thin wrappers around their adapter plus
GraphFakos rendering. They may choose defaults, workspace loading, and package
labels, but shared screens, filters, static export, local preview serving, and
viewer contract tests belong here.

## Viewer Surface

The initial workbench is dependency-free static HTML with local-server routing.
It supports:

- explore, neighborhood, path, provenance, timeline, provider-status, and
  context-preview screens,
- search plus node-kind, edge-kind, tag, source, and score filters,
- clickable nodes and edges with inspector details,
- depth-aware neighborhoods,
- path source/target controls,
- provenance and citation panels, and
- provider capability/status summaries.

GraphFakos does not interpret provider-specific semantics. Adapters should put
provider-only fields in `provider_payload` unless the field belongs in a stable
common DTO.

## Provider Examples

Fake third-party provider:

```bash
graphfakos-ui --screen explore --html-out graphfakos-ui-preview.html --json
```

Sophiagraph second-brain provider:

```bash
cd ../sophiagraph
PYTHONPATH=../graphfakos/src:src \
  .venv/bin/python3.11 -m sophiagraph ui-preview \
  --screen views \
  --html-out sophiagraph-graphfakos.html \
  --json
```

PragmaGraph third-brain provider:

```bash
cd ../pragmagraph
PYTHONPATH=../graphfakos/src:src \
  .venv/bin/python3.11 -m pragmagraph ui-preview \
  --screen provider_status \
  --html-out pragmagraph-graphfakos.html \
  --json
```

OpenMinion host integration should stay provider-neutral:

```python
from graphfakos import GraphFakosRequest, render_static_html


def render_context_graph(provider):
    request = GraphFakosRequest(screen="context_preview", include_provenance=True)
    return render_static_html(provider, request)
```

Custom providers implement the same contract without importing Sophiagraph,
PragmaGraph, or OpenMinion:

```python
from graphfakos import GraphFakosGraph, GraphFakosProvider, GraphFakosRequest


class MyGraphProvider(GraphFakosProvider):
    provider_id = "my_graph"
    provider_label = "My Graph"
    graph_role = "third_party"
    capabilities = ("search", "neighborhood", "static_export")

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        ...
```
