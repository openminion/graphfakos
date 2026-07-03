# Releasing GraphFakos

GraphFakos follows the sibling package release pattern used by Sophiagraph,
PragmaGraph, and OpenMinion Eval.

## Local Checks

```bash
.venv/bin/python3.11 -m ruff check src tests scripts
PYTHONPATH=src .venv/bin/python3.11 -m pytest -q
.venv/bin/python3.11 scripts/release_check.py
```

For a quicker local iteration without packaging-network checks:

```bash
.venv/bin/python3.11 scripts/release_check.py --skip-twine --skip-wheel-smoke
```

## Release Proof

The release check must prove:

- public imports work
- package metadata is aligned with the semantic-alpha public surface
- the wheel includes the `py.typed` type marker
- fake third-party provider renders
- static HTML export works
- local preview server routes work
- built wheel and source distribution pass `twine check`
- installed wheel can import and run the CLI smoke path

Do not publish a release from only `src/` imports.

## Public Release Checklist

Before publishing a release:

1. confirm the canonical GitHub repository and PyPI project are owned by the
   project maintainers,
2. run `scripts/release_check.py` without skip flags,
3. inspect `dist/` only as release output, not as source-controlled content,
4. verify Sophiagraph and PragmaGraph can install the target `graphfakos`
   version from TestPyPI before production PyPI,
5. tag the release from the committed source tree.

After release validation, remove local generated artifacts such as `build/`,
`dist/`, `.venv/`, `.pytest_cache/`, and `src/*.egg-info` before preparing the
source commit.
