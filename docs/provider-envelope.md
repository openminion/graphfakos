# Provider Envelope

GraphFakos can render provider-neutral viewer envelopes produced by packages
such as PragmaGraph. This path is intended for large graph iteration where the
provider owns observed facts, clusters, content, evidence, and omitted counts,
while GraphFakos owns the visual workbench.

## Usage

Generate a PragmaGraph viewer fixture:

```bash
cd ../pragmagraph
mkdir -p ../graphfakos/.graphfakos-preview

PYTHONPATH=src .venv/bin/python3.11 -m pragmagraph.__main__ viewer-fixture \
  --scenario viewer-scale-200k \
  --out ../graphfakos/.graphfakos-preview/viewer-scale-200k.json \
  --json
```

Open it in GraphFakos:

```bash
cd ../graphfakos

graphfakos-ui \
  --provider-envelope .graphfakos-preview/viewer-scale-200k.json \
  --render-engine 3d \
  --theme space \
  --layout grouped \
  --render-limit 240 \
  --serve \
  --open
```

Use `--html-out` instead of `--serve --open` only when you need a portable
static fallback artifact.

## Renderer And Theme

`--render-engine 3d` selects the provider-neutral 3D renderer seam. The static
export still keeps an SVG fallback so the graph remains inspectable without
browser JavaScript.

`--theme space` applies the dark graph-canvas theme to the page, canvas, nodes,
edges, chips, and overlays. Theme and renderer values are carried through the
viewer route so provider-envelope views can be reopened consistently.

## Optional Viewer Declarations

A provider envelope may add portable viewer declarations beside its graph
payload:

```json
{
  "perspectives": [
    {
      "perspective_id": "evidence",
      "label": "Evidence",
      "summary": "Review sourced nodes",
      "filters": {"evidence_filter": "with_evidence"},
      "style_color_by": "source",
      "style_size_by": "confidence"
    }
  ],
  "inspector_schemas": [
    {
      "schema_id": "document-fields",
      "node_kind": "document",
      "fields": [
        {"key": "source", "label": "Source"},
        {
          "key": "workspace",
          "label": "Workspace",
          "source": "provider_payload"
        }
      ]
    }
  ]
}
```

Perspectives contain only provider-neutral route, filter, renderer, layout, and
style fields. Inspector fields read either a stable node DTO field or a named
`provider_payload` value. These declarations control presentation only; they do
not grant mutation, persistence, or semantic-query authority.

The local workbench can also open a provider envelope or graph artifact through
the `Open data` control. Browser import is intentionally process-local and is
available only while the local preview server is running.

GraphFakos also derives a portable `GraphFakosWorkspaceManifest` from a loaded
provider envelope. Hosts can use that manifest to hand off current viewer
state, progressive cluster summaries, raw-versus-rendered budgets, saved-view
state, expansion requests, viewer-local actions, provider status, empty-state
hints, and edit/capture affordances to a web shell or desktop wrapper without
parsing rendered HTML. Provider cluster declarations may use either `id` or
`cluster_id`; expansion cursors stay provider-owned.

Viewer-local actions such as search, filtering, node inspection, neighborhood
focus, path highlighting, static export, provenance review, and citation copy
describe what the GraphFakos shell can do with the current DTOs. They are not
provider mutations. Provider-owned mutations remain limited to explicit
`supported_actions` and `supported_captures` declarations backed by host code.

When a provider returns no visible nodes, the manifest carries an `empty_state`
object. Providers may supply `provider_payload.empty_state`; otherwise
GraphFakos derives a provider-neutral code and message from graph stats and
warnings.

## Boundary

- Provider envelopes are JSON data contracts, not package-private imports.
- GraphFakos converts clusters, visible nodes, edge bundles, content,
  provenance, and citation payloads into `GraphFakosGraph`.
- GraphFakos can summarize those DTOs into a workspace manifest for viewer
  replay and integration handoff.
- GraphFakos does not generate canonical 200k or 1m provider fixtures.
- GraphFakos does not mutate provider truth. Edit/manage actions must be
  explicit provider-neutral commands accepted by the provider or host.
- Provider-owned expansion remains an optional Python protocol. A JSON envelope
  can describe an already bounded graph, but cannot make static data fetch more
  source truth by itself.
