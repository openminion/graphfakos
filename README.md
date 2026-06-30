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
  <a href="https://pypi.org/project/graphfakos/"><img alt="PyPI" src="https://img.shields.io/pypi/v/graphfakos?color=3775A9"></a>
  <a href="https://pypi.org/project/graphfakos/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/graphfakos"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue"></a>
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

GraphFakos is a `0.0.1` semantic-alpha package. The initial public release is
intended for local package integrations, adapter development, and visual graph
inspection. The stable starting contract is the provider-neutral DTO model,
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
- provider-neutral graph diagnostics for orphan nodes, duplicate edges,
  missing provenance/citation references, and provider warnings
- dependency-free navigation for node selection, edge inspection, query search,
  node-kind, edge-kind, tag, source, and score filters plus public deep-link
  route helpers
- depth-aware neighborhood expansion and path source/target controls
- public query syntax guidance for `kind:`, `tag:`, `source:`, `edge:`,
  `id:`, `label:`, `summary:`, `has:`, quoted phrases, `score>=`, and `time>=`
  tokens
- snapshot metadata on graph envelopes plus provider-owned comparison and
  overlay workflows
- persisted graph artifact helpers plus a file-backed provider adapter for
  standalone review flows
- static HTML export for portable inspection
- embeddable HTML fragments for host package shells
- JSON and Markdown graph reports for CI proof, issue attachments, and
  package-local review flows
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

Render the built-in third-party fixture:

```bash
graphfakos-ui --screen explore --html-out graphfakos-ui-preview.html --json
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
  --json
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

Sophiagraph should expose a second-brain adapter that maps durable memories,
candidates, trust signals, structural links, and provenance into GraphFakos
DTOs. PragmaGraph should expose a third-brain adapter that maps source files,
documents, symbols, chunks, citations, freshness, and provider status into the
same DTOs.

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
see [Artifact interchange](docs/artifact-interchange.md).

## Docs and Release

- [API compatibility](API_COMPATIBILITY.md)
- [Release process](RELEASING.md)
- [Package docs](docs/README.md)
- [Artifact interchange](docs/artifact-interchange.md)
- [Custom provider example](docs/custom-provider-example.md)
- [UI contracts](docs/ui-contracts.md)
- [Source tree owner map](docs/source-tree-owner-map.md)

Run local release checks:

```bash
.venv/bin/python3.11 scripts/release_check.py --skip-twine --skip-wheel-smoke
```

## License and Brand-use Boundary

GraphFakos is distributed under the Apache License 2.0. The license covers code
use and contribution terms. It does not grant rights to imply endorsement by
OpenMinion, Sophiagraph, PragmaGraph, or related project brands.
