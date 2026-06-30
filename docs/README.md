# GraphFakos Docs

GraphFakos is the shared graph lens package for visualizing provider-neutral
knowledge graphs.

Start with:

- [Artifact interchange](artifact-interchange.md)
- [Source tree owner map](source-tree-owner-map.md)
- [UI contracts](ui-contracts.md)
- [Custom provider example](custom-provider-example.md)
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

- explore, neighborhood, path, provenance, timeline, diff, provider-status,
  and context-preview screens,
- provider-neutral screen metadata for routes, labels, and summaries,
- built-in review presets so hosts can deep-link into repeatable overview,
  focus, evidence, diff, graph-health, timeline, and context flows,
- search plus node-kind, edge-kind, tag, source, and score filters,
- public deep-link helpers for building or parsing stable viewer routes,
- public query syntax guidance for `kind:`, `tag:`, `source:`, `edge:`,
  `id:`, `label:`, `summary:`, `has:`, quoted phrases, `score>=`, and
  `time>=` tokens,
- clickable nodes and edges with inspector details,
- hub-aware navigator panels for larger graphs,
- depth-aware neighborhoods,
- path source/target controls,
- snapshot metadata plus provider-owned comparison and overlay workflows,
- provenance and citation panels with evidence coverage summaries, and
- provider capability/status summaries.

GraphFakos also exposes:

- persisted graph artifact helpers plus a file-backed provider adapter,
- embeddable HTML fragments for package-local UI shells,
- JSON graph reports, and
- Markdown and DOT graph reports for issue attachments, review notes, and
  external graph tooling.

GraphFakos does not interpret provider-specific semantics. Adapters should put
provider-only fields in `provider_payload` unless the field belongs in a stable
common DTO.

## Provider Examples

Fake third-party provider:

```bash
graphfakos-ui --screen explore --html-out graphfakos-ui-preview.html --json
```

Diff plus embed/report example:

```bash
graphfakos-ui \
  --screen diff \
  --comparison-graph-id fixture-baseline \
  --artifact-out graphfakos-artifact.json \
  --embed-out graphfakos-embed.html \
  --report-out graphfakos-report.json \
  --markdown-report-out graphfakos-report.md \
  --dot-out graphfakos-report.dot \
  --json
```

Artifact-backed standalone replay:

```bash
graphfakos-ui \
  --graph-json graphfakos-artifact.json \
  --comparison-graph-json graphfakos-baseline.json \
  --screen diff \
  --html-out graphfakos-artifact-view.html \
  --json
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
  --artifact-out pragmagraph-graph.json \
  --report-out pragmagraph-graph-report.json \
  --embed-out pragmagraph-graph-embed.html \
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

For a fuller third-party example, see
[Custom provider example](custom-provider-example.md).

## Public route and query helpers

GraphFakos exposes package-level helpers for shareable routes:

```python
from graphfakos import GraphFakosRequest, build_viewer_route, parse_viewer_request

request = GraphFakosRequest(
    screen="diff",
    query="kind:file has:provenance",
    comparison_graph_id="structural_baseline",
)
route = build_viewer_route(request)
parsed = parse_viewer_request("/diff", {"query": ["kind:file has:provenance"]})
```

The public `query_syntax_reference()` helper returns the documented token set
that package-local UIs can surface in their own help or docs.

## Persisted graph artifacts

GraphFakos now exposes a provider-neutral artifact surface for portable review
workflows:

```python
from graphfakos import (
    FixtureGraphProvider,
    GraphFakosRequest,
    load_graph_artifact,
    load_provider_graph,
    write_graph_artifact,
)

graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
write_graph_artifact(graph, "graphfakos-artifact.json")
reloaded = load_graph_artifact("graphfakos-artifact.json")
```

The public `graph_artifact_schema()` helper returns the package-owned JSON
schema description for that artifact shape, and `FileGraphProvider` lets the
standalone CLI reopen those artifacts without custom code.

For end-to-end package handoff and replay examples, see
[Artifact interchange](artifact-interchange.md).
