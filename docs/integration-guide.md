# GraphFakos Integration Guide

Status: public alpha guidance

Purpose: give Sophiagraph, PragmaGraph, OpenMinion, and third-party packages one
small path for embedding the shared graph viewer without copying UI code or
inventing package-local graph contracts.

## Boundary

GraphFakos owns the viewer lens:

- provider-neutral graph DTOs,
- static and local-preview rendering,
- routes, filters, saved views, camera state, and viewer actions,
- workspace manifests for host handoff, and
- reusable provider conformance checks.

The provider package owns graph truth:

- storage, indexing, ingestion, and refresh,
- authorization and tenancy,
- semantic ranking and domain-specific query behavior,
- mutation, promotion, deletion, and persistence, and
- product chrome around the embedded viewer.

Package-local commands such as `sophiagraph-ui`, `pragmagraph-ui`, or an
OpenMinion graph viewer should stay thin. They should load the package's native
graph, adapt it into `GraphFakosGraph`, then call GraphFakos render and testing
helpers.

## Minimal Provider

```python
from graphfakos import (
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvider,
    GraphFakosRequest,
)


class PackageGraphProvider(GraphFakosProvider):
    provider_id = "package"
    provider_label = "Package Graph"
    graph_role = "third_party"
    capabilities = ("search", "neighborhood", "path", "provider_status")

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        return GraphFakosGraph(
            graph_id="package:default",
            label="Package Graph",
            provider_id=self.provider_id,
            provider_label=self.provider_label,
            graph_role=self.graph_role,
            capabilities=self.capabilities,
            nodes=(
                GraphFakosNode(
                    id="doc:integration",
                    label="Integration Guide",
                    kind="document",
                    summary="Provider-owned graph content.",
                ),
            ),
            edges=(),
        )
```

## Viewer Embedding

Use the same provider with whichever output the host needs:

```python
from graphfakos import (
    GraphFakosRequest,
    render_embeddable_html,
    render_static_html,
    workspace_manifest_for_graph,
)
from graphfakos.provider import load_provider_graph

provider = PackageGraphProvider()
request = GraphFakosRequest(screen="explore")

html_page = render_static_html(provider, request)
html_fragment = render_embeddable_html(provider, request)
graph = load_provider_graph(provider, request)
manifest = workspace_manifest_for_graph(graph, request)
```

Use `html_page` for a complete static export, `html_fragment` inside host-owned
chrome, and `manifest` when a desktop shell or web app needs the current viewer
state without parsing rendered HTML.

## Optional Workflows

Only advertise optional capabilities when the provider implements the matching
protocol:

- `lazy_expansion` for provider-owned neighborhood slices,
- `knowledge_capture` for provider-owned note or observation capture,
- `graph_action` for provider-owned draft nodes, edges, tags, merges, or
  review actions,
- `provider_status` for status, warnings, facets, and provider details.

GraphFakos can render the controls and validate the returned DTOs. It does not
persist captures, invent expansion neighbors, or apply graph actions unless the
provider implements those workflows.

Current OpenMinion-family provider behavior:

| Provider package | GraphFakos role | Capture/edit behavior |
| --- | --- | --- |
| Sophiagraph | durable second-brain memory lens | provider-backed captures and candidate graph actions |
| PragmaGraph | observed source/document graph lens | read-oriented viewer envelope and live patches; no durable memory writes |
| OpenMinion | orchestration shell over configured brains | second-brain visual lens is read-only from the viewer; use OpenMinion memory commands for durable writes |

## Workspace Manifest

`workspace_manifest_for_graph(graph, request)` is the host handoff contract. It
contains:

- current route, camera, filters, renderer, and selected ids,
- visible clusters and expansion cursors,
- rendered-versus-source graph budget,
- saved-view replay state,
- default expansion requests,
- viewer-local actions,
- provider-backed action and capture affordances,
- provider status, facets, warnings, and empty-state hints, and
- the local preview route for the same screen.

The Explore screen also renders this contract as the `Provider Readiness` panel,
so users integrating Sophiagraph, PragmaGraph, OpenMinion, or a third-party
provider can quickly see what the viewer believes is available.

## Test Contract

Provider packages should add a small conformance test:

```python
from graphfakos import GraphFakosRequest
from graphfakos.testing import (
    GraphFakosProviderConformanceCase,
    assert_provider_conformance,
)


def test_package_provider_satisfies_graphfakos_contract(tmp_path):
    result = assert_provider_conformance(
        GraphFakosProviderConformanceCase(
            provider=PackageGraphProvider(),
            request=GraphFakosRequest(screen="explore"),
            expected_role="third_party",
            expected_provider="Package Graph",
            expected_node="Integration Guide",
            required_capabilities=(
                "search",
                "neighborhood",
                "path",
                "provider_status",
            ),
            artifact_path=tmp_path / "package-graph.json",
        )
    )

    assert result.workspace_manifest.provider_id == "package"
```

When the provider supports optional workflows, pass `expansion_request`,
`capture`, `action`, and `expected_action_status` into the same conformance
case. Keep those tests in the provider package so they run against the native
adapter and real package defaults.

## Local Sibling Matrix

When GraphFakos, Sophiagraph, PragmaGraph, and OpenMinion are checked out under
the same `agent-frameworks/` workspace, run the source-level integration matrix
from `graphfakos/`:

```bash
make integration-check
```

That command exercises:

1. GraphFakos consuming Sophiagraph and PragmaGraph provider projections,
2. Sophiagraph's GraphFakos adapter, workbench, and compatibility contracts,
3. PragmaGraph's GraphFakos adapter, viewer envelope, and UI contracts,
4. OpenMinion's GraphFakos-backed graph viewer, and
5. OpenMinion's PragmaGraph provider co-enable paths.

Use the wheelhouse variant before coordinated package releases or when changing
dependency lower bounds:

```bash
make integration-wheel-check
```

It builds local wheels for the sibling packages and installs them together in a
fresh virtual environment, so the check catches package metadata and dependency
resolution drift that source-path tests can miss.

## Wrapper Checklist

Use this checklist before shipping a package-local `*-ui` wrapper:

- The wrapper imports GraphFakos public roots only.
- The wrapper converts native records into `GraphFakosGraph` and leaves
  provider-specific fields in `provider_payload`.
- The wrapper calls `render_static_html`, `render_embeddable_html`, or the local
  preview server instead of copying viewer HTML.
- The package has a conformance test using
  `GraphFakosProviderConformanceCase`.
- The rendered Explore screen shows `Provider Readiness` with useful
  capabilities, actions, facets, warnings, or empty-state hints.
- Any mutation, capture, refresh, or expansion path is explicitly implemented
  by the provider package.
- Provider docs say whether editing/capture is `supported`, `read-only`, or
  `unsupported`; GraphFakos only renders controls that the provider advertises.
