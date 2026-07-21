# Custom Provider Example

GraphFakos is meant to work with packages that do not import Sophiagraph,
PragmaGraph, or OpenMinion. A custom package only needs to emit
provider-neutral DTOs and implement `GraphFakosProvider`.

## Minimal provider

```python
from graphfakos import (
    GraphFakosEdge,
    GraphFakosExpansionRequest,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvider,
    GraphFakosRequest,
)


class PackageGraphProvider(GraphFakosProvider):
    provider_id = "package_graph"
    provider_label = "Package Graph"
    graph_role = "third_party"
    capabilities = (
        "search",
        "neighborhood",
        "path",
        "provider_status",
        "static_export",
        "lazy_expansion",
    )

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        nodes = (
            GraphFakosNode(
                id="node:guide",
                label="Integration Guide",
                kind="document",
                summary="Package-specific graph documentation.",
                tags=("guide", "docs"),
                source="package_docs",
            ),
            GraphFakosNode(
                id="node:service",
                label="Graph Service",
                kind="service",
                summary="A package-local graph producer.",
                tags=("service",),
                source="package_runtime",
            ),
        )
        edges = (
            GraphFakosEdge(
                id="edge:service-docs",
                source_id="node:service",
                target_id="node:guide",
                kind="documents",
                label="documents",
            ),
        )
        return GraphFakosGraph(
            graph_id="package_graph",
            label="Package Graph",
            provider_id=self.provider_id,
            provider_label=self.provider_label,
            graph_role=self.graph_role,
            capabilities=self.capabilities,
            nodes=nodes,
            edges=edges,
            provider_payload={
                "integration_summary": (
                    "This package publishes graph DTOs directly into the "
                    "shared GraphFakos viewer."
                ),
                "integration_commands": (
                    "python -m package_graph preview --screen explore --serve",
                ),
                "perspectives": (
                    {
                        "perspective_id": "docs",
                        "label": "Documentation",
                        "summary": "Review document nodes",
                        "node_kinds": ("document",),
                    },
                ),
                "inspector_schemas": (
                    {
                        "schema_id": "service-fields",
                        "node_kind": "service",
                        "fields": (
                            {"key": "source", "label": "Source"},
                            {"key": "id", "label": "Stable id"},
                        ),
                    },
                ),
            },
        )

    def expand_graph(
        self,
        request: GraphFakosRequest,
        expansion: GraphFakosExpansionRequest,
    ) -> GraphFakosGraph | None:
        """Optional provider-owned lazy expansion hook."""
        graph = self.load_graph(request)
        if expansion.source_id not in {node.id for node in graph.nodes}:
            return None
        return graph
```

## Provider-neutral rules

- Put stable graph facts in DTO fields such as ids, labels, kinds, tags,
  scores, provenance, citations, and sources.
- Put package-specific semantics in `provider_payload`.
- Keep host/runtime policy outside GraphFakos.
- Keep package-local preview commands thin: provider construction, defaults,
  and package labels belong there; shared viewer behavior belongs in
  GraphFakos.
- Implement optional expansion only when the provider owns the source graph.
  GraphFakos validates and renders the returned slice, but it does not invent
  neighbors, ingest files, or persist expanded graph truth.
- Use typed perspectives and inspector schemas only for portable presentation.
  Provider-specific mutation, authorization, and semantic query behavior still
  requires an explicit provider-owned protocol or host integration.

## Validation loop

Use the reusable conformance helper in the provider package's own tests:

```python
from graphfakos import GraphFakosRequest
from graphfakos.testing import (
    GraphFakosProviderConformanceCase,
    assert_provider_conformance,
)


def test_package_provider_satisfies_graphfakos_contract(tmp_path):
    assert_provider_conformance(
        GraphFakosProviderConformanceCase(
            provider=PackageGraphProvider(),
            request=GraphFakosRequest(screen="explore"),
            expected_role="third_party",
            expected_provider="Package Graph",
            expected_node="Integration Guide",
            expected_edge="documents",
            required_capabilities=(
                "search",
                "neighborhood",
                "path",
                "provider_status",
                "static_export",
                "lazy_expansion",
            ),
            artifact_path=tmp_path / "package-graph.json",
        )
    )
```

Then use the same local proof shape as the fixture provider:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3.11 -m ruff check src tests scripts
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python3.11 -m pytest -q
.venv/bin/python3.11 scripts/release_check.py --skip-twine --skip-wheel-smoke
```

## Runnable host example

For a complete public-import-only example, see
`examples/provider_host.py`. It demonstrates a package-local provider that:

- returns provider-neutral nodes, edges, citations, stats, and provider payloads,
- accepts `GraphFakosKnowledgeCapture` without importing a host runtime,
- previews `GraphFakosGraphAction` while keeping persistence host-owned, and
- renders static HTML through `render_static_html`.

That shape is the preferred integration model for future Sophiagraph,
PragmaGraph, OpenMinion, and third-party graph producers: shared viewer code
lives in GraphFakos, while provider packages own truth, durability, action
policy, and rebuild behavior.
