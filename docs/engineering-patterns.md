# GraphFakos engineering patterns

Status: active
Last updated: 2026-11-01

This reference records the package-local engineering baseline for contributors
and automation working on GraphFakos.

## Boundaries

1. Keep graph DTOs, provider capabilities, and viewer commands typed and
   provider-neutral.
2. Keep provider-specific persistence, truth, and semantic interpretation in
   provider packages.
3. Keep static export usable when JavaScript or WebGL is unavailable.
4. Keep browser enhancement in the package-owned UI assets rather than copying
   viewer behavior into host integrations.

## Ownership

1. Put public graph records in the model and contract modules.
2. Put provider validation in the provider boundary.
3. Put rendering and interaction behavior under `src/graphfakos/ui/` or the
   narrow rendering entrypoints that own it.
4. Put fixture-only behavior in adapters and tests; do not promote demo
   assumptions into the public package core.
5. Extract a focused owner before a module becomes a mixed-purpose catch-all.

## Viewer composition

1. Keep `GraphFakosRequest`, graph records, provider capabilities, commands,
   events, and persisted viewer state provider-neutral and serializable.
2. Keep route parsing, graph filtering, traversal, layout, canvas composition,
   controls, discovery, analysis, navigation, authoring, and evidence behavior
   with their existing `ui/viewer/` owners; do not grow `ui/app.py` back into a
   mixed viewer implementation.
3. Keep the static SVG/HTML surface complete enough for inspection and export.
   WebGL is an enhancement, not the only representation of graph truth.
4. Edit the 3D renderer in `web/src/` and rebuild the packaged asset. Do not
   hand-edit generated `src/graphfakos/assets/renderer-3d.js` output.
5. Keep the framework-neutral custom element and packaged browser assets local;
   host packages should adapt their data instead of copying the viewer.

## Provider and side-effect rules

1. GraphFakos may validate and present knowledge-capture or graph-action
   requests, but the provider owns authorization, persistence, semantic truth,
   and final status.
2. Keep demo, fixture, file-backed, Sophiagraph, and PragmaGraph adapters behind
   the same public contracts. Do not special-case provider meaning in shared
   rendering code.
3. Preserve revision, cursor, replay, and action identifiers across local
   server and browser boundaries so retries do not silently duplicate work.
4. Treat provider errors and unavailable capabilities as typed facts; do not
   infer success from an HTTP response or optimistic browser state alone.

## Scale and accessibility truth

1. Report raw, rendered, clustered, and omitted counts separately. A 1M graph
   envelope does not mean the browser allocated or drew one million objects.
2. Keep layout and benchmark fixtures deterministic so visual and browser
   regressions are reproducible.
3. Preserve keyboard navigation, visible focus, reduced-motion behavior,
   readable labels, fallback rendering, and responsive controls when changing
   the graph surface.
4. Use real-browser checks for interaction, WebGL, responsive, accessibility,
   or scale claims; static HTML or unit tests do not prove those behaviors.

## Implementation style

1. Prefer explicit data flow and deterministic structural behavior.
2. Avoid reflection-heavy dispatch, payload-shape guessing, and wrappers that
   only rename another helper.
3. Keep comments for non-obvious constraints, not narration.
4. Preserve public compatibility or document an intentional break before
   changing an exported contract.
5. Keep public docs portable and free of machine-local paths.

## Validation

Use the narrowest useful loop while authoring, then run the package gate:

```bash
make check
```

Run `make release-check` for packaging or public-surface changes and
`make browser-e2e` for viewer behavior changes. See
[Code quality enforcement](code-quality-enforcement.md) and
[Cleanup workflow](cleanup-workflow.md) for the active ratchets and broader
sweep process.

Apply the [comment and docstring review](../CODE_QUALITY.md#comment-and-docstring-review)
to the final diff, including tests and scripts.
