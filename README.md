<p align="center">
  <img src="https://www.openminion.com/brand/openminion-logo.png" alt="OpenMinion logo" width="128" />
</p>

<h1 align="center">GraphFakos</h1>

<p align="center">
  <strong>Standalone provider-neutral graph lens for shared package viewers.</strong>
</p>

<p align="center">
  <a href="https://github.com/openminion/graphfakos">GitHub</a>
  · <a href="https://pypi.org/project/graphfakos/">PyPI</a>
  · <a href="https://www.openminion.com">Website</a>
  · <a href="https://x.com/OpenMinion">X</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/graphfakos/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-v0.0.5-3775A9"></a>
  <a href="https://pypi.org/project/graphfakos/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/graphfakos?cacheSeconds=300"></a>
  <a href="https://github.com/openminion/graphfakos/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue"></a>
  <img alt="Status" src="https://img.shields.io/badge/status-publish--ready%20alpha-5B8DEF">
</p>

`graphfakos` is a reusable graph lens for agent memory and source knowledge
graphs. It provides provider-neutral graph DTOs, adapter protocols, static HTML
rendering, local preview serving, and test helpers for package-owned graph
viewers.

GraphFakos exists so packages such as Sophiagraph, PragmaGraph, OpenMinion, and
third-party graph providers can share a visual graph workbench without sharing
their internal graph truth or lifecycle semantics.

The name comes from Greek `fakós` (`φακός`), meaning lens; in this package it
frames the shared graph workbench as a provider-neutral lens over nodes, edges,
provenance, citations, and package-owned graph semantics rather than as a graph
builder or memory store.

## Initial Release Status

GraphFakos is a `0.0.5` semantic-alpha release intended for local package
integrations, adapter development, and visual graph inspection.
The stable package contract is the provider-neutral DTO model,
`GraphFakosProvider`, static HTML export, local preview serving, console
scripts, and reusable viewer assertions.

## Trust and Brand Safety

- Official GitHub: `https://github.com/openminion/graphfakos`
- Official website: `https://www.openminion.com`
- Official X account: `https://x.com/OpenMinion`

`graphfakos` has no official token, coin, NFT, airdrop, staking program,
treasury product, or investment offering. Any claim otherwise is unauthorized
and should be treated as a scam.

`graphfakos` is a viewer and adapter-contract package. It does not infer facts,
extract memories, ingest repositories, enforce OpenMinion runtime policy, or
decide which graph items are true. Providers own their graph semantics and pass
explicit nodes, edges, provenance, citations, and provider payloads into
GraphFakos.

## At a Glance

- package name: `graphfakos`
- console scripts: `graphfakos`, `graphfakos-smoke`, `graphfakos-ui`
- core contract: `GraphFakosProvider`
- graph envelope: `GraphFakosGraph`
- type marker: `py.typed`
- local viewer: static HTML and local preview server
- compatibility proof: fake third-party provider plus package viewer tests

## Installation

```bash
python3.11 -m pip install graphfakos
```

For sibling-package development before the first PyPI release, install from a
local checkout:

```bash
python3.11 -m pip install -e .
```

## What the Package Provides

- provider-neutral graph DTOs for nodes, edges, provenance, citations, visual
  hints, and viewer requests
- a provider protocol that graph packages can implement without importing
  Sophiagraph, PragmaGraph, or OpenMinion
- a local graph workbench with explore, neighborhood, path, provenance,
  timeline, diff, provider-status, and context-preview screens
- a public screen manifest with provider-neutral routes, labels, and summaries
- built-in review presets for overview, focus review, evidence, diff, graph
  health, timeline, and context workflows
- provider-neutral graph diagnostics for orphan nodes, duplicate edges,
  missing provenance/citation references, and provider warnings
- dependency-free navigation for node selection, edge inspection, query
  search, common filters, and public deep-link route helpers
- progressive SVG camera controls for pan, zoom, fit, reset, fullscreen, and
  node dragging while keeping static HTML useful without JavaScript
- a framework-neutral `<graphfakos-viewer>` custom element backed by packaged
  browser runtime assets
- camera-aware saved-view routes with `camera_x`, `camera_y`, and
  `camera_zoom`
- browser-local saved-view slots for workbench iteration without implying
  provider persistence or hosted collaboration
- serializable viewer state plus provider-neutral command, event,
  expansion-request, knowledge-capture, saved-view, saved-query, graph-action,
  action-status, graph-analytics, replay-bundle, and theme DTOs for host
  integrations
- an explicit SVG renderer contract with clear unsupported-engine failures for
  future Canvas/WebGL seams
- route-preserved renderer/theme state so host workbenches can experiment with
  Canvas/WebGL while static exports honestly fall back to SVG
- provider-neutral visual hierarchy with node shapes, edge arrows, selected
  path emphasis, minimap orientation, group toggles, and side-panel
  cross-highlighting
- depth-aware neighborhood expansion, orphan visibility, neighbor-link
  visibility, edge-clutter controls, analytics overlays, and path source/target
  controls
- route-backed command palette with saved queries, navigation, evidence review,
  authoring jumps, export-state shortcuts, and progressive keyboard filtering
  for faster graph workbench flow
- hub-aware navigation panels that recommend global, local-depth, evidence,
  path, status, and context routes for larger graphs
- preview-server knowledge capture forms so host providers or workers can
  consume operator notes, code observations, questions, or memory hints and
  rebuild the graph
- preview-server graph action forms so providers can accept draft nodes, links,
  merge/alias requests, or return clear unsupported-action statuses
- public query syntax guidance for graph filters such as `kind:`, `tag:`,
  `source:`, `edge:`, `id:`, `label:`, `summary:`, `has:`, quoted phrases,
  `score>=`, and `time>=`
- snapshot metadata on graph envelopes plus provider-owned comparison and
  overlay workflows
- richer diff and provenance review surfaces with change hotspots, evidence
  coverage, and citation location summaries
- persisted graph artifact helpers plus a file-backed provider adapter for
  standalone review flows
- static HTML export for portable inspection
- embeddable HTML fragments for host package shells
- JSON, Markdown, DOT, and replay-bundle exports for CI proof, issue
  attachments, exact-state replay, and package-local review flows
- a local HTTP preview server for interactive package development
- a fake fixture provider for tests and third-party adapter examples
- shared test assertions for graph viewer contracts

## What the Package Does Not Provide

- durable memory persistence
- source ingestion
- fact extraction
- graph construction
- OpenMinion runtime policy
- Sophiagraph trust semantics
- PragmaGraph freshness or source semantics

## Provider Adapter Contract

Providers implement `GraphFakosProvider`:

```python
from graphfakos import GraphFakosProvider, GraphFakosRequest, GraphFakosGraph


class MyProvider:
    provider_id = "my_provider"
    provider_label = "My Provider"
    graph_role = "third_party"
    capabilities = ("search", "neighborhood", "path", "provenance")

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        ...
```

GraphFakos understands how to display graph-shaped data. Providers own what
their data means.

## Package UI Wrappers

GraphFakos is the shared viewer implementation. Package-local `*-ui` commands
should stay thin:

- `sophiagraph-ui` maps durable second-brain memory records into
  GraphFakos DTOs through Sophiagraph's adapter, then calls the shared viewer.
- `pragmagraph-ui` maps source/document/code graph snapshots into
  GraphFakos DTOs through PragmaGraph's adapter, then calls the shared viewer.
- future packages should implement a `GraphFakosProvider` adapter instead of
  copying viewer HTML, local-server behavior, navigation screens, or tests.

This keeps the visual workbench consistent while preserving each package's own
storage, trust, freshness, and lifecycle semantics.

## Examples

Launch the reusable dynamic viewer in a browser:

```bash
make preview
```

`make preview` serves the viewer at a local HTTP URL and opens the browser. It
does not require a generated HTML file. In server mode, GraphFakos serves a
live workbench: internal links and filter forms update the viewer in place
through server-rendered fragments. The side panel can also submit notes or
observations to providers that support the workbench capture protocol. Stop the
server with `Ctrl-C`.

Write a portable static export under the gitignored repo-local preview folder:

```bash
make preview-html
```

The static export lands in `.graphfakos-preview/graphfakos-viewer.html` and is
useful for sharing or no-JavaScript fallback checks. Treat it as an export, not
the main dynamic viewer workflow. Static exports are view-only; run the preview
server when you want note capture or provider-backed graph refreshes.

Iterate the viewer against generated mock graphs:

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

These commands use deterministic demo scenarios instead of real provider data,
which makes UI work easier to repeat. The available scenarios are
`agent-memory`, `source-code`, `dense`, `timeline`, `warnings`, `pathfinding`,
`provenance`, `facets`, `workbench-mixed`, `budget`, and `islands`.

Use the scenarios as a core-feature plus UI matrix:

- `pathfinding`: path screen, source/target controls, shortest-path highlight.
- `provenance`: provenance screen, citation cards, evidence coverage.
- `facets`: filter controls across node kind, edge kind, tag, and source.
- `workbench-mixed`: combined agent/session memory, code, docs, tests, human
  notes, evidence gaps, and preview-only graph actions.
- `budget`: render-limit behavior, summarized hidden nodes, show-more route.
- `islands`: provider-status diagnostics for disconnected components.
- `agent-memory`: knowledge capture workflow beside a focused agent/memory
  graph.

To test the capture loop, run `make preview-demo`, choose or keep a focused
node, write a note in `Capture Knowledge`, and submit it. The demo provider
stores captures in memory for that server session and renders them back as
linked graph nodes. Real providers can implement the same action to persist the
payload, enqueue a worker, rebuild a code/static graph, or maintain a durable
knowledge graph outside GraphFakos.

You can also choose a scenario manually:

```bash
graphfakos-ui --demo-scenario source-code --screen explore --serve --open
graphfakos-ui --demo-scenario dense --screen explore --layout grouped --render-limit 240 --serve --open
graphfakos-ui --demo-scenario timeline --screen timeline --layout timeline --serve --open
graphfakos-ui --demo-scenario pathfinding --screen path --source-node-id provider:entry --target-node-id artifact:result --serve --open
graphfakos-ui --demo-scenario workbench-mixed --screen explore --focus-node-id agent:reviewer --serve --open
```

Render the built-in third-party fixture manually:

```bash
graphfakos-ui --screen explore --html-out .graphfakos-preview/graphfakos-ui-preview.html --json
```

Render a diff view plus export machine-readable and Markdown reports:

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

Jump straight into a built-in review flow:

```bash
graphfakos-ui --preset focus --focus-node-id provider:third-party --html-out graphfakos-focus.html --json
```

Serve the local viewer:

```bash
graphfakos-ui --screen neighborhood --serve --open
```

Filter a graph and inspect an edge:

```bash
graphfakos-ui \
  --screen explore \
  --node-kind provider \
  --edge-kind serves \
  --selected-edge-id edge:provider-serves-spec \
  --html-out graphfakos-filtered.html \
  --json
```

Build or parse a shareable viewer route from Python:

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

Render from a persisted GraphFakos artifact instead of the built-in fixture:

```bash
graphfakos-ui \
  --graph-json graphfakos-artifact.json \
  --comparison-graph-json graphfakos-baseline.json \
  --screen diff \
  --html-out graphfakos-from-artifact.html \
  --json
```

Render from a real provider module:

```bash
graphfakos-ui \
  --provider-module my_package.graph_provider \
  --provider-class MyGraphProvider \
  --provider-config-json '{"workspace": ".graph-workspace"}' \
  --screen provider_status \
  --html-out graphfakos-provider.html \
  --json
```

Package adapters stay responsible for their own semantics:

- Sophiagraph maps durable memories, candidates, trust signals, structural
  links, and provenance into GraphFakos DTOs.
- PragmaGraph maps source files, documents, symbols, chunks, citations,
  freshness, and provider status into the same DTOs.

Persist and reload one provider-neutral graph artifact from Python:

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

For package-to-package replay flows, CI attachments, and issue-review examples,
see [Artifact interchange](https://github.com/openminion/graphfakos/blob/main/docs/artifact-interchange.md).

## Docs and Release

- [API compatibility](https://github.com/openminion/graphfakos/blob/main/API_COMPATIBILITY.md)
- [Release process](https://github.com/openminion/graphfakos/blob/main/RELEASING.md)
- [Package docs](https://github.com/openminion/graphfakos/blob/main/docs/README.md)
- [Artifact interchange](https://github.com/openminion/graphfakos/blob/main/docs/artifact-interchange.md)
- [Custom provider example](https://github.com/openminion/graphfakos/blob/main/docs/custom-provider-example.md)
- [UI contracts](https://github.com/openminion/graphfakos/blob/main/docs/ui-contracts.md)
- [Source tree owner map](https://github.com/openminion/graphfakos/blob/main/docs/source-tree-owner-map.md)

Run local release checks:

```bash
.venv/bin/python3.11 scripts/release_check.py --skip-twine --skip-wheel-smoke
```

## License and Brand-use Boundary

GraphFakos is distributed under the Apache License 2.0. The license covers code
use and contribution terms. It does not grant rights to imply endorsement by
OpenMinion, Sophiagraph, PragmaGraph, or related project brands.
