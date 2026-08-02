<p align="center">
  <img src="https://www.openminion.com/brand/openminion-logo.png" alt="GraphFakos logo" width="128" />
</p>

<h1 align="center">GraphFakos</h1>

<p align="center">
  <strong>Provider-neutral graph lens for local exploration, review, and package viewers.</strong>
</p>

<p align="center">
  <a href="https://github.com/OpenMinion/graphfakos">GitHub</a>
  · <a href="https://pypi.org/project/graphfakos/">PyPI</a>
  · <a href="https://www.openminion.com">Website</a>
  · <a href="docs/README.md">Docs</a>
  · <a href="https://x.com/OpenMinion">X</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/graphfakos/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-v0.0.8rc1-3775A9"></a>
  <a href="https://pypi.org/project/graphfakos/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/graphfakos?cacheSeconds=300"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue"></a>
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-6B7280">
</p>

GraphFakos `v0.0.8rc1` is a public alpha graph viewer package. It gives graph
providers one shared set of DTOs, adapter contracts, static rendering, local
preview tools, and interaction payloads without taking ownership of the graph
itself.

## Read This First

1. Read [At a Glance](#at-a-glance) to confirm that GraphFakos is a viewer, not
   a graph database or fact engine.
2. Follow [Install](#install) and [Quick Start](#quick-start) to open the local
   workbench.
3. Read [Provider Contract](#provider-contract) before adapting another graph.
4. Use the [package docs](docs/README.md) for live sessions, interchange,
   accessibility, and UI contracts.
5. Read [Development](#development) before changing the package.

## Trust and Brand Safety

- Official GitHub: <https://github.com/OpenMinion/graphfakos>
- Official website: <https://www.openminion.com>
- Official X account: <https://x.com/OpenMinion>

GraphFakos has no official token, coin, NFT, airdrop, staking program, treasury
product, or investment offering. Any claim otherwise is unauthorized and
should be treated as a scam.

## At a Glance

| | |
| --- | --- |
| Package | `graphfakos` |
| Current line | `v0.0.8rc1` public alpha |
| Python | 3.11+ |
| Best fit | Shared local graph viewing across independent providers |
| Core contract | `GraphFakosProvider` |
| Main outputs | Static HTML, embeddable fragments, local preview, and portable artifacts |
| Not the claim | Graph truth, persistence, indexing, memory, or fact extraction |

## Common Commands

```bash
python3.11 -m pip install graphfakos
graphfakos-smoke
graphfakos-ui --serve --open
```

For a static artifact:

```bash
graphfakos-ui --html-out graph.html
```

## Install

Install from PyPI:

```bash
python3.11 -m pip install graphfakos
```

For a source checkout:

```bash
python3.11 -m pip install -e ".[dev]"
```

## Quick Start

Open the packaged demo workbench:

```bash
graphfakos-ui --serve --open
```

Render a provider-neutral graph from Python:

```python
from graphfakos import (
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvider,
    GraphFakosRequest,
    render_static_html,
)


class DemoProvider(GraphFakosProvider):
    provider_id = "demo"
    provider_label = "Demo Provider"
    graph_role = "example"
    capabilities = ("search",)

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        return GraphFakosGraph(
            graph_id="demo",
            label="Demo Graph",
            provider_id=self.provider_id,
            provider_label=self.provider_label,
            graph_role=self.graph_role,
            capabilities=self.capabilities,
            nodes=(
                GraphFakosNode(
                    id="node:1",
                    label="First node",
                    kind="example",
                    summary="Provider-owned graph content.",
                ),
            ),
            edges=(),
        )


html = render_static_html(DemoProvider(), GraphFakosRequest(screen="explore"))
open("graph.html", "w", encoding="utf-8").write(html)
```

For a complete host adapter with actions and knowledge capture, run:

```bash
python3.11 examples/provider_host.py
```

## What GraphFakos Provides

- provider-neutral node, edge, citation, provenance, request, and graph DTOs
- a typed provider protocol and reusable provider assertions
- explore, neighborhood, path, provenance, timeline, diff, status, and context
  views
- static HTML, embeddable fragments, JSON, Markdown, DOT, and replay artifacts
- local preview serving and same-origin interaction endpoints
- search, filters, saved views, perspectives, diagnostics, and camera state
- typed capture, graph-action, expansion, live-patch, and replay contracts
- a framework-neutral browser custom element and packaged viewer assets
- fixtures and helpers for adapter, accessibility, and browser validation

## What GraphFakos Does Not Provide

- durable graph or memory persistence
- source ingestion, parsing, or fact extraction
- truth, trust, freshness, lifecycle, or ranking semantics
- OpenMinion runtime policy or agent orchestration
- SophiaGraph memory behavior
- PragmaGraph indexing behavior
- a hosted multi-user graph service

GraphFakos displays explicit provider data. Providers decide what nodes and
edges mean, where data is stored, which actions are valid, and whether a write
is accepted.

## Provider Contract

A provider owns graph truth and implements `GraphFakosProvider`:

```python
from graphfakos import GraphFakosGraph, GraphFakosProvider, GraphFakosRequest


class MyProvider(GraphFakosProvider):
    provider_id = "my-provider"
    provider_label = "My Provider"
    graph_role = "third-party"
    capabilities = ("search", "neighborhood", "path")

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph: ...
```

Optional protocols add bounded expansion, knowledge capture, graph actions,
live updates, or provider-specific inspector fields. Keep persistence and
semantic decisions in the provider rather than hiding them in viewer code.

## How It Fits

| Package | Responsibility |
| --- | --- |
| SophiaGraph | Durable memory semantics and memory graph projections |
| PragmaGraph | Observed-fact semantics and source graph projections |
| OpenMinion | Runtime and operator-facing graph integration |
| GraphFakos | Shared viewer, interaction DTOs, and local rendering |

Package-specific `sophiagraph-ui` and `pragmagraph-ui` commands should remain
thin adapters: they map package-owned data into GraphFakos DTOs and delegate
the viewer behavior to GraphFakos.

## Development

```bash
make dev-install
make hooks-install
make check
```

Run `make browser-test` when changing browser behavior and `make release-check`
before publishing or changing the documented public surface.

## Docs and Release

- [`docs/README.md`](docs/README.md): package documentation map
- [`docs/ui-contracts.md`](docs/ui-contracts.md): viewer and interaction
  contracts
- [`docs/live-sessions.md`](docs/live-sessions.md): patches, cursors, and replay
- [`docs/artifact-interchange.md`](docs/artifact-interchange.md): portable
  artifacts
- [`docs/custom-provider-example.md`](docs/custom-provider-example.md): adapter
  walkthrough
- [`docs/accessibility.md`](docs/accessibility.md): keyboard and accessibility
  behavior
- [`docs/source-tree-owner-map.md`](docs/source-tree-owner-map.md): code owners
  and package layout
- [`API_COMPATIBILITY.md`](API_COMPATIBILITY.md): supported import roots
- [`RELEASING.md`](RELEASING.md): release and publish flow

## License and Brand-use Boundary

- Source code license: Apache-2.0
- Brand/trademark grant: none

The license grants rights to use, modify, and redistribute the code. It does
not grant rights to present a fork, clone, token, website, or social account as
the official GraphFakos or OpenMinion project or imply affiliation or
endorsement.
