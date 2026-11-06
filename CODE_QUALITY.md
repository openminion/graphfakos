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

## Comment and docstring review

This rule applies to every contributor and coding agent, including tests and
scripts. Let clear names, types and direct control flow explain ordinary steps.
Review every added or changed comment and docstring in the final diff; remove
obvious restatements, decorative banners and duplicated walkthroughs. Keep one
concise explanation at the owner when a constraint is not obvious.

Preserve public API and model-facing descriptions, required notices/directives,
and useful safety, compatibility and regression-oracle rationale. Keep short
factual module explainers; move longer design/history narratives to docs.
Passing automated checks does not replace this review, and there is no comment
quota. Check current source and existing reports before filing cleanup debt;
keep unrelated cleanup out of a feature PR.

## Minimum usable code

These rules apply to maintainers, external contributors and coding agents, in
new work and cleanup of merged code. Start with actual callers, supported inputs
and concrete failure paths. Use the existing owner and a direct implementation;
add a helper or abstraction only when current callers need it.

Do not add speculative frameworks, unused modes or extension points,
pass-through wrappers, duplicate validation, silent defaults, blanket exception
handling, or retries that hide failures. Validate at the boundary that owns the
contract instead of repeatedly normalizing internal values. A retry needs a
specific transient failure, a bound and safe repeat behavior. Preserve necessary
trust-boundary checks, permissions, compatibility, persistence/replay and cleanup.

Keep provider DTO and rendering boundaries explicit. Preserve provider errors,
public display contracts and browser resource cleanup.

## Review and cleanup evidence

Review the complete final diff and every new delta for simplicity and the
[comment and docstring rules](#comment-and-docstring-review). Record the exact
reviewed head, checked callers, supported failure cases, findings and disposition
in the PR or linked review evidence. Passing automated checks does not replace
this review. Block approval or merge while a substantiated finding remains;
request the smaller existing-owner change when it satisfies the same contract.
Validate the current integration with the target branch and require all required
hosted checks on the exact head before merging. Never relax a gate to land cleanup.

For merged work, first verify that the code still exists on the current
development branch. Reuse existing findings and respect active ownership; record
obsolete findings without reopening old PRs, duplicating issues or taking over
another contributor's branch. Do not label all historical code clean from a
partial review.

A broad cleanup starts with a fresh file inventory at a recorded revision. Keep
source, tests and scripts separate, give each claimed file a trim, keep or explicit
defer disposition, and work in bounded tranches. Record callers, rationale,
validation and remaining work after each tranche; deferred files remain open.
Refresh evidence if the tree changes during validation. Record before/after LOC
for source cleanup and retain a simplification only when it reduces code and
improves readability while preserving the contract. Review the changed files
again after authoring; this is not proof of a package-wide sweep.

Preserve test assertions and negative controls. Do not introduce skips, expected
failures, extra waits or retries to conceal a regression. Preserve script output,
exit behavior and operator clarity. Run the repository's documented gates and
report local, hosted, installed-package and live-system evidence separately.
