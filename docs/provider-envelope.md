# Provider Envelope

GraphFakos can render provider-neutral viewer envelopes produced by packages
such as PragmaGraph. This path is intended for large graph iteration where the
provider owns observed facts, clusters, content, evidence, and omitted counts,
while GraphFakos owns the visual workbench.

## Usage

Generate a PragmaGraph viewer fixture:

```bash
cd ../pragmagraph

PYTHONPATH=src .venv/bin/python3.11 -m pragmagraph.__main__ viewer-fixture \
  --scenario viewer-scale-200k \
  --out ../workspace-tmp/pragmagraph-viewer-support/viewer-scale-200k.json \
  --json
```

Open it in GraphFakos:

```bash
cd ../graphfakos

PYTHONPATH=src .venv/bin/python3.11 -m graphfakos.__main__ ui \
  --provider-envelope ../workspace-tmp/pragmagraph-viewer-support/viewer-scale-200k.json \
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

## Boundary

- Provider envelopes are JSON data contracts, not package-private imports.
- GraphFakos converts clusters, visible nodes, edge bundles, content,
  provenance, and citation payloads into `GraphFakosGraph`.
- GraphFakos does not generate canonical 200k or 1m provider fixtures.
- GraphFakos does not mutate provider truth. Edit/manage actions must be
  explicit provider-neutral commands accepted by the provider or host.
