# GraphFakos Docs

GraphFakos is the shared graph lens package for visualizing provider-neutral
knowledge graphs.

Start with:

- [Engineering patterns](engineering-patterns.md)
- [Code quality enforcement](code-quality-enforcement.md)
- [Cleanup workflow](cleanup-workflow.md)
- [Artifact interchange](artifact-interchange.md)
- [Source tree owner map](source-tree-owner-map.md)
- [UI contracts](ui-contracts.md)
- [Viewer accessibility matrix](accessibility.md)
- [Provider envelope](provider-envelope.md)
- [Live graph sessions](live-sessions.md)
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

The workbench is portable HTML with local-server routing and package-owned
client-side enhancement. Without JavaScript, exported files still render the
static SVG graph, route links, filters, inspectors, and reports. With WebGL,
stable `render_engine=3d` mounts the bundled 3d-force-graph/Three.js scene while
retaining SVG as the structured fallback. The browser behavior is packaged in
`assets/viewer.js` and `assets/renderer-3d.js` and mounted through a framework-
neutral `<graphfakos-viewer>` custom element, so host packages can embed the
viewer without copying GraphFakos HTML or loading a CDN.

It supports:

- explore, neighborhood, path, provenance, timeline, diff, provider-status,
  and context-preview screens,
- provider-neutral screen metadata for routes, labels, and summaries,
- built-in review presets so hosts can deep-link into repeatable overview,
  focus, evidence, diff, graph-health, timeline, and context flows,
- search plus node-kind, edge-kind, tag, source, and score filters,
- public deep-link helpers for building or parsing stable viewer routes,
- camera-aware deep links through `camera_x`, `camera_y`, and `camera_zoom`,
- serializable viewer state plus provider-neutral viewer command, event,
  expansion-request, knowledge-capture, saved-view, saved-query, graph-action,
  action-status, graph-analytics, replay-bundle, and theme DTOs,
- package-owned browser runtime helpers through `viewer_runtime_script()`,
- true WebGL 3D, canvas, and SVG fallback contracts with route-preserved
  renderer/theme state for host workbenches,
- public query syntax guidance for `kind:`, `tag:`, `source:`, `edge:`,
  `id:`, `label:`, `summary:`, `has:`, quoted phrases, `score>=`, and
  `time>=` tokens,
- clickable nodes and edges with inspector details, selected-path emphasis,
  provider-neutral shapes, edge arrows, and side-panel cross-highlighting,
- pan, zoom, fit, reset, fullscreen, and drag controls layered over the static
  SVG canvas,
- minimap orientation, group toggles, and render-budget fallback links for
  larger visible graphs,
- saved workspace, local graph control, route-backed command palette with
  progressive keyboard filtering, analytics overlay, replay/export, and
  graph-authoring panels,
- hub-aware navigator panels for global, local-depth, evidence, path, status,
  and context graph lenses,
- depth-aware neighborhoods,
- path source/target controls,
- preview-server knowledge capture and graph-action forms for provider-owned
  notes, code observations, questions, memory hints, draft nodes, links, and
  merge/alias requests,
- snapshot metadata plus provider-owned comparison and overlay workflows,
- provenance and citation panels with evidence coverage summaries, and
- provider capability/status summaries.

GraphFakos also exposes:

- persisted graph artifact helpers plus a file-backed provider adapter,
- embeddable HTML fragments for package-local UI shells,
- JSON graph reports, and
- Markdown, DOT, and replay-bundle graph reports for issue attachments, review
  notes, exact-state replay, and external graph tooling.

GraphFakos does not interpret provider-specific semantics. Adapters should put
provider-only fields in `provider_payload` unless the field belongs in a stable
common DTO.

## Provider Examples

Launch the dynamic viewer locally:

```bash
make preview
```

This serves the viewer through GraphFakos' local HTTP preview server and opens a
browser. Server mode is the interactive workbench path: internal navigation and
GET forms request GraphFakos fragments and update the viewer in place. Providers
that implement the optional capture protocol can also accept notes from the
`Capture Knowledge` panel and refresh the graph. Use `Ctrl-C` to stop it.

Write a repo-local portable static export:

```bash
make preview-html
```

The generated files live under `.graphfakos-preview/`, which is intentionally
gitignored. Use this path when you need a shareable HTML export or static
fallback artifact. Static exports are view-only; run the local preview server
for note capture or provider-backed graph refreshes.

Iterate UI behavior with generated mock data:

```bash
make preview-demo
make preview-dense
make preview-timeline
make preview-warnings
make preview-path
make preview-provenance
make preview-workbench
make preview-budget
make preview-islands
```

The demo provider is deterministic and package-local. It can simulate
agent-memory, source-code, dense, timeline, warnings, pathfinding, provenance,
facets, workbench-mixed, budget, and islands graph shapes without Sophiagraph,
PragmaGraph, OpenMinion, or external data.

Core-feature scenario map:

- `pathfinding`: path screen, source/target controls, shortest-path highlight.
- `provenance`: provenance screen, citation cards, evidence coverage.
- `facets`: filter controls across node kind, edge kind, tag, and source.
- `workbench-mixed`: combined agent/session memory, code, docs, tests, human
  notes, evidence gaps, and preview-only graph actions.
- `budget`: render-limit behavior, summarized hidden nodes, show-more route.
- `islands`: provider-status diagnostics for disconnected components.
- `agent-memory`: graph-side knowledge capture beside an agent/memory graph.

Provider-envelope scale preview:

```bash
graphfakos-ui \
  --provider-envelope ../workspace-tmp/pragmagraph-viewer-support/viewer-scale-200k.json \
  --render-engine 3d \
  --theme space \
  --layout grouped \
  --render-limit 240 \
  --serve \
  --open
```

Use this path for PragmaGraph-generated 200k and 1m viewer envelopes. See
[Provider envelope](provider-envelope.md) for the boundary and exact handoff
flow.

Generate package-owned benchmark envelopes and run the real-browser matrix:

```bash
make web-install web-build
make benchmark-fixtures
make browser-e2e
```

The 1M fixture models 1,000 clusters of 1,000 nodes each. The browser receives
aggregate cluster records, omitted counts, edge bundles, and expansion cursors;
it does not allocate or claim to draw one million raw WebGL objects.

To test the capture loop, run `make preview-demo`, enter a note in
`Capture Knowledge`, and submit it. `DemoGraphProvider` stores captures in
memory for that server session and renders them back as linked graph nodes. A
real provider can persist the same `GraphFakosKnowledgeCapture` payload, enqueue
a worker, rebuild a source/code graph, or maintain a durable knowledge graph
outside GraphFakos.

Manual scenario selection:

```bash
graphfakos-ui --demo-scenario source-code --screen explore --serve --open
graphfakos-ui --demo-scenario dense --screen explore --layout grouped --render-limit 240 --serve --open
graphfakos-ui --demo-scenario timeline --screen timeline --layout timeline --serve --open
graphfakos-ui --demo-scenario pathfinding --screen path --source-node-id provider:entry --target-node-id artifact:result --serve --open
graphfakos-ui --demo-scenario workbench-mixed --screen explore --focus-node-id agent:reviewer --serve --open
```

Fake third-party provider static export:

```bash
graphfakos-ui --screen explore --html-out .graphfakos-preview/graphfakos-ui-preview.html --json
```

Camera-aware saved view:

```bash
graphfakos-ui \
  --screen explore \
  --layout radial \
  --camera-x 20 \
  --camera-y -10 \
  --camera-zoom 1.25 \
  --html-out .graphfakos-preview/graphfakos-saved-view.html \
  --json
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
  --bundle-out graphfakos-replay.json \
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
