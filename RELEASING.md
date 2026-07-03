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

## RC-to-Production Flow

Use a release candidate on TestPyPI before publishing a production PyPI
version.

1. Start from a clean branch based on the intended release source.
2. Bump package metadata and public version references to an RC such as
   `0.0.3rc1`.
3. Run local proof:
   ```bash
   make dev-install
   PYTHONDONTWRITEBYTECODE=1 make check
   PYTHONDONTWRITEBYTECODE=1 make browser-test
   PYTHONDONTWRITEBYTECODE=1 make release-check
   ```
4. Push an RC tag such as `v0.0.3rc1`; the release workflow publishes to
   TestPyPI because the tag contains `rc`.
5. Install from TestPyPI in a fresh environment and run CLI smoke proof.
6. Bump package metadata and public version references to the final version,
   such as `0.0.3`.
7. Rerun the same local proof.
8. Push the final tag, such as `v0.0.3`; the release workflow publishes to
   production PyPI because the tag does not contain `rc`.
9. Install from production PyPI in a fresh environment and run CLI smoke proof.
10. Create a GitHub Release page for the final tag with highlights, linked PRs,
    package links, and validation evidence.
11. Merge or backfill the release commit into the default branch so GitHub's
    README and source tree match the published PyPI package.

Do not reuse a PyPI or TestPyPI version after upload. If a publish succeeds and
the README or metadata needs correction, release a new patch version.

## Publishing Setup Notes

Trusted publishing must be configured separately on TestPyPI and production
PyPI.

- TestPyPI publisher:
  - repository: `openminion/graphfakos`
  - workflow: `release.yml`
  - environment: `testpypi`
- PyPI publisher:
  - repository: `openminion/graphfakos`
  - workflow: `release.yml`
  - environment: `pypi`

If publishing fails with `invalid-publisher`, the package built successfully
but PyPI did not recognize the GitHub OIDC identity. Check the owner,
repository, workflow filename, and environment name in the PyPI trusted
publisher settings.

## Dependency And README Notes

Release dependency packages before dependent packages. For example, publish a
GraphFakos version that includes new public APIs before releasing Sophiagraph
against those APIs.

PyPI stores the README included in the uploaded package. Editing GitHub's
README after a package publish does not update the already-published PyPI
description. Use absolute GitHub links for README documentation links that must
work on both GitHub and PyPI, and publish a patch version when the PyPI
description itself needs to change.
