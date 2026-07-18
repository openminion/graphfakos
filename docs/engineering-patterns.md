# GraphFakos engineering patterns

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
