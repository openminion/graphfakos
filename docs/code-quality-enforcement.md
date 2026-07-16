# GraphFakos code quality enforcement

GraphFakos uses the same local, hook, and CI quality sequence so contributors
can reproduce failures before opening a pull request.

## Local gates

```bash
make format-check
make lint
make validate-patterns
make test
make check
```

`make check` is the normal closeout gate. It combines formatting, Ruff,
structural ratchets, and the package tests.

## Structural ratchets

`scripts/validate_quality_patterns.py` and `scripts/baselines/` guard:

1. file and function size,
2. duplicate private helpers,
3. path and filename drift,
4. broad exception handlers,
5. bare `# type: ignore` comments, and
6. hidden sibling-package imports across the public package boundary.

Baselines preserve known debt; they are not targets. Fix new drift rather than
raising a baseline unless a reviewed compatibility constraint requires it.

## Hooks and CI

Install hooks once with:

```bash
make hooks-install
```

Run the complete hook set manually with `make hooks-run`. GitHub Actions repeats
the same formatter, lint, ratchet, test, and build checks for pull requests and
protected branch pushes.

## Additional gates

Run `make release-check` when package metadata, exports, docs required by the
wheel, or release behavior changes. Run `make browser-e2e` when the dynamic
viewer, renderer, routes, or interaction contracts change.

For a broad cleanup or maintainability pass, follow
[Cleanup workflow](cleanup-workflow.md) rather than treating a hand-picked file
set as a package-wide review.
