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
10. provider-neutral graph diagnostics,
11. progressive camera/navigation enhancement over static SVG export,
12. framework-neutral `<graphfakos-viewer>` mounting behavior,
13. reusable viewer state, command, event, expansion, knowledge-capture, and
    theme DTOs,
14. packaged browser runtime assets,
15. reusable viewer test assertions.

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
2. provider-neutral screen metadata such as route labels and summaries,
3. static export and local preview server behavior,
4. graph filtering, selection, and inspection controls,
5. provider status and capability presentation,
6. context-preview layout,
7. camera route state, minimap orientation, group toggles, and saved-view links,
8. dynamic viewer state/event/command payloads,
9. local workbench action payload shape for provider-owned captures,
10. common smoke assertions.

## Progressive Enhancement Contract

The shared viewer must keep the static HTML export useful without JavaScript.
The baseline graph canvas is a provider-neutral SVG with route-backed node and
edge links. Client-side behavior may add pan, zoom, fit, reset, fullscreen,
drag, group toggle, minimap, keyboard, and cross-panel highlight behavior, but
those enhancements must not replace the static route/export contract.

Automated package tests should cover generated HTML, route state, camera
parameters, controls, data attributes, and no-JavaScript SVG fallback. Pointer
behavior can be proven by a future browser/DOM harness or by recorded manual
preview evidence when a tracker explicitly allows that proof mode.

## Dynamic Viewer Runtime Contract

GraphFakos ships a package-owned browser runtime asset for the reusable
`<graphfakos-viewer>` custom element. The element wraps the existing static
viewer markup instead of replacing it, so exported HTML remains readable when
JavaScript is unavailable.

The dynamic runtime owns only structural viewer state:

1. screen, layout, camera, selected node, selected edge, filters, groups, render
   engine, theme, and saved-view metadata,
2. provider-neutral viewer commands such as select, filter, camera, layout,
   group-toggle, expand, and export-state,
3. provider-neutral viewer events emitted as `graphfakos:<name>` custom events,
4. local fallback DOM synchronization for the SVG canvas, minimap, group
   toggles, inspector cards, and saved-view links.

Provider or host packages still own remote data loading, authorization,
mutation, persistence, semantic ranking, and product chrome. GraphFakos may
emit an expansion request event, but it must not fetch or invent
provider-specific neighbors unless a host/provider integration handles that
event explicitly.

Knowledge capture follows the same boundary. GraphFakos may render a
`Capture Knowledge` form and submit a `GraphFakosKnowledgeCapture` payload from
local preview mode, but the provider or host owns persistence, worker queues,
fact extraction, memory promotion, source ingestion, and graph rebuild policy.

The first renderer is `svg`. `canvas` and `webgl` are future
renderer-interface targets only; unsupported render engines should fail clearly
through the public renderer validation helper rather than silently changing DTO
behavior.

## Local Workbench Server Contract

Interactive viewer development should use GraphFakos' local HTTP workbench
server rather than opening generated HTML files directly. The server has two
provider-neutral response modes:

1. normal route requests return a complete HTML document for first load,
2. requests with `X-GraphFakos-Fragment: 1` return a JSON envelope containing a
   rendered `<graphfakos-viewer>` fragment for in-place client updates.

The browser runtime may intercept same-origin HTTP links and GET forms inside
`<graphfakos-viewer>` and replace the viewer from that fragment response. Static
HTML export remains a portable artifact path and must not require the server or
JavaScript to show a useful SVG baseline.

The server may also accept provider-neutral JSON action requests when a preview
host supplies an action handler:

1. `POST /api/knowledge` accepts `GraphFakosKnowledgeCapture` fields such as
   `text`, `kind`, `tags`, `source`, `link_node_id`, `link_edge_kind`, and
   `provider_payload`.
2. Providers that implement the optional capture protocol decide whether to
   persist the note, enqueue a worker, rebuild a code/static graph, or attach a
   temporary preview-only node.
3. Providers that do not implement the protocol must fail clearly; GraphFakos
   must not pretend the capture was stored.
4. Static HTML exports must treat the capture form as read-only and direct
   users back to the local preview server for mutations.

Viewer iteration can use `DemoGraphProvider` and the `--demo-scenario` CLI
switch to simulate representative graph shapes without real provider data. Demo
scenarios must remain deterministic so UI regressions are repeatable.

## Provider Adapter Shape

Adapters should implement `GraphFakosProvider` and return `GraphFakosGraph`.
The graph envelope should contain:

1. provider id, label, graph role, capabilities, and status,
2. nodes with stable ids, labels, kinds, scores, tags, sources, visual hints,
   provenance, citations, and provider payloads,
3. edges with stable ids, endpoints, kind, label, score, weight, provenance,
   citations, and provider payloads,
4. optional selected node or selected edge hints,
5. optional integration commands and short integration summaries for host
   packages or standalone previews.

Provider-only semantics belong in `provider_payload` unless the field is part
of the stable common DTO model.

Diagnostics should stay structural and provider-neutral. GraphFakos can report
orphan nodes, duplicate edge ids, unknown provenance ids, unknown citation ids,
and provider-supplied warnings. It must not decide whether a memory claim is
true, whether a source file is fresh, or whether an item should be promoted.

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
5. Hosts that want graph-side note entry can implement the optional capture
   protocol while keeping durable knowledge semantics outside GraphFakos.

The shared viewer must not infer facts, promote memories, ingest source files,
or decide durable memory policy. Those responsibilities stay with the provider
or host package.

## Compatibility Expectations

Within the `0.0.x` line, changes should preserve:

1. stable public import roots listed in `API_COMPATIBILITY.md`,
2. public DTO names,
3. `GraphFakosProvider.load_graph()` behavior,
4. console script names,
5. provider-neutral `diagnose_graph()` output keys,
6. supported screen names,
7. local preview and static-export behavior, including the no-JavaScript SVG
   baseline,
8. package adapter compatibility for Sophiagraph and PragmaGraph,
9. packaged `assets/viewer.js` availability in source, editable installs, and
   wheels,
10. same-origin local workbench fragment responses for in-place viewer
    navigation,
11. local preview JSON action behavior for `POST /api/knowledge`,
12. typed package marker availability through `graphfakos/py.typed`.

If a viewer contract change requires Sophiagraph or PragmaGraph updates, land
adapter tests in those packages with the GraphFakos change.
