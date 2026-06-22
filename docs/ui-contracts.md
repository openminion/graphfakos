# GraphFakos UI Contracts

Status: semantic alpha

Purpose: define the shared graph-viewer contract used by GraphFakos provider
adapters and by thin package-local UI commands such as `sophiagraph-ui` and
`pragmagraph-ui`.

## Contract Owner

GraphFakos owns the reusable viewer layer:

1. provider-neutral DTOs,
2. provider protocol validation,
3. static HTML rendering,
4. local preview serving,
5. screen routing,
6. graph canvas behavior,
7. node and edge inspectors,
8. search and filter controls,
9. provenance and citation panels,
10. reusable viewer test assertions.

Provider packages own their data semantics and adapter mapping. They should not
fork GraphFakos viewer HTML, duplicate local-server behavior, or create a
parallel test contract for the shared viewer.

## Thin Wrapper Rule

Package-local `*-ui` commands are allowed and encouraged for user convenience,
but they should stay thin.

Allowed package-local responsibilities:

1. load the package workspace or demo fixture,
2. choose sensible default screens,
3. construct the package's `GraphFakosProvider`,
4. pass command-line options through to GraphFakos rendering,
5. expose package-specific labels and integration commands.

GraphFakos-owned responsibilities:

1. shared screen names and navigation behavior,
2. static export and local preview server behavior,
3. graph filtering, selection, and inspection controls,
4. provider status and capability presentation,
5. context-preview layout,
6. common smoke assertions.

## Provider Adapter Shape

Adapters should implement `GraphFakosProvider` and return `GraphFakosGraph`.
The graph envelope should contain:

1. provider id, label, graph role, capabilities, and status,
2. nodes with stable ids, labels, kinds, scores, tags, sources, visual hints,
   provenance, citations, and provider payloads,
3. edges with stable ids, endpoints, kind, label, score, weight, provenance,
   citations, and provider payloads,
4. optional selected node or selected edge hints,
5. optional integration commands for host packages such as OpenMinion.

Provider-only semantics belong in `provider_payload` unless the field is part
of the stable common DTO model.

## Package Alignment

Sophiagraph and PragmaGraph should line up through GraphFakos without sharing
their internal graph truth:

1. Sophiagraph maps durable memory records, candidates, trust signals,
   structural links, and memory provenance into GraphFakos DTOs.
2. PragmaGraph maps source files, documents, code symbols, chunks, citations,
   freshness, and provider status into GraphFakos DTOs.
3. OpenMinion should consume GraphFakos-compatible providers through the same
   provider-neutral result shape instead of importing package-specific viewer
   code.
4. Third-party packages can implement the same provider protocol directly.

The shared viewer must not infer facts, promote memories, ingest source files,
or decide durable memory policy. Those responsibilities stay with the provider
or host package.

## Compatibility Expectations

Within the `0.0.x` line, changes should preserve:

1. stable public import roots listed in `API_COMPATIBILITY.md`,
2. public DTO names,
3. `GraphFakosProvider.load_graph()` behavior,
4. console script names,
5. supported screen names,
6. local preview and static-export behavior,
7. package adapter compatibility for Sophiagraph and PragmaGraph,
8. typed package marker availability through `graphfakos/py.typed`.

If a viewer contract change requires Sophiagraph or PragmaGraph updates, land
adapter tests in those packages with the GraphFakos change.
