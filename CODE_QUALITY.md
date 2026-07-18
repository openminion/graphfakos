# GraphFakos Code Quality and Hygiene

This is the public contributor version of the package's code-quality rules.

The short version:

1. keep provider-neutral contracts typed and explicit,
2. keep package boundaries honest,
3. keep runtime behavior structural rather than speculative,
4. keep comments minimal,
5. and prove the change with validation.

## 1. Prefer One Truthful Owner

Use the nearest clear owner:

1. DTOs in `models.py`,
2. provider protocol and validation in `provider.py`,
3. rendering entrypoints in `render.py`, `static.py`, and `ui/`,
4. local preview serving in `server.py`,
5. reusable test assertions in `testing/`,
6. fixture/demo providers in `adapters/`.

Avoid duplicate viewer shells, repeated magic literals, and wrappers that only
rename another helper.

## 2. Keep Runtime Behavior Structural

GraphFakos owns graph display and interaction. It does not decide whether a
memory, source item, claim, citation, or provider payload is true.

Prefer:

1. typed fields,
2. explicit provider capabilities,
3. deterministic static export,
4. clear adapter boundaries.

Avoid:

1. hidden Sophiagraph or PragmaGraph assumptions,
2. hidden OpenMinion runtime imports,
3. lossy fact extraction or semantic inference in the viewer package.

## 3. Keep Names and Layout Honest

Rules:

1. remove stale names instead of letting them linger,
2. keep files in the package area that truthfully owns them,
3. do not grow generic junk-drawer files like `utils.py`,
4. keep provider-specific mapping in provider packages or fixture adapters.

## 4. Keep Public Docs Portable

Do not add:

1. machine-local absolute paths,
2. private workstation assumptions,
3. internal tracker-state wording as public package documentation.

## 5. Keep Changes Focused

Good practice:

1. one clear purpose per PR,
2. update tests near the change,
3. avoid unrelated refactors in the same patch.

## 6. Validate Before Calling Work Done

Before closing work, run the package gates from `graphfakos/`:

```bash
make check
```

`make check` includes `make validate-patterns`, which runs the package-local
complexity, structure, broad-exception, type-ignore, duplicate-helper,
filename, and public-surface guards. Baselines under `scripts/baselines/` are
ratchets: existing debt may only shrink, and new drift must either be fixed or
added with an explicit reason.

If your change affects packaging or public release shape, also run:

```bash
make release-check
```

Use `make lint` or `make test` directly only when you need a narrower loop
while iterating.

## 7. When in Doubt, Choose Clarity

The package prefers:

1. explicit owners over convenience,
2. provider-neutral contracts over package-specific shortcuts,
3. maintainable structure over short-term shortcuts.

For a broad cleanup, simplification, or maintainability pass, follow
[docs/cleanup-workflow.md](docs/cleanup-workflow.md) so the claim is backed by a
fresh inventory, explicit per-file dispositions, and current validation.
