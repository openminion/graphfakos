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

The RC and final release must share the same base version. For example,
`0.0.4rc1` is the TestPyPI candidate for `0.0.4`; do not validate `0.0.4rc1`
and then publish a different final base version. The final step is a metadata
change from `0.0.4rc1` to `0.0.4` on the same release branch after RC proof
passes.

1. Start from a clean branch based on the intended release source.
2. Bump package metadata and public version references to an RC such as
   `0.0.4rc1`.
3. Run local proof:
   ```bash
   make dev-install
   PYTHONDONTWRITEBYTECODE=1 make check
   PYTHONDONTWRITEBYTECODE=1 make browser-test
   PYTHONDONTWRITEBYTECODE=1 make release-check
   ```
4. Push an RC tag such as `v0.0.4rc1`; the release workflow publishes to
   TestPyPI because the tag contains `rc`.
5. Install from TestPyPI in a fresh environment and run CLI smoke proof.
6. Bump package metadata and public version references to the final version,
   such as `0.0.4`.
7. Rerun the same local proof.
8. If TestPyPI should also show the current final version rather than only an
   RC, manually dispatch the release workflow from the final release branch
   with `target=testpypi` before pushing the final production tag. Then install
   that exact final version from TestPyPI and run CLI smoke proof.
9. Push the final tag, such as `v0.0.4`; the release workflow publishes to
   production PyPI because the tag does not contain `rc`.
10. Install from production PyPI in a fresh environment and run CLI smoke proof.
11. Create a GitHub Release page for the final tag with the bare version as the
    title, such as `0.0.4`, not `GraphFakos 0.0.4`. Include highlights, linked
    PRs, package links, and validation evidence in the body.
12. Merge or backfill the release commit into the default branch so GitHub's
    README and source tree match the published PyPI package.
13. Run the post-release surface audit below and record any cache lag or
    expected TestPyPI differences before calling the release complete.

Do not reuse a PyPI or TestPyPI version after upload. If a publish succeeds and
the README or metadata needs correction, release a new patch version.

## Post-Release Surface Audit

After both TestPyPI and PyPI workflows complete, verify each public surface
separately. Do not treat one stale UI element as proof that the package publish
failed.

1. Production PyPI package metadata:
   ```bash
   python3.11 - <<'PY'
   import json, urllib.request

   with urllib.request.urlopen(
       "https://pypi.org/pypi/graphfakos/json",
       timeout=20,
   ) as response:
       data = json.load(response)

   print(data["info"]["version"])
   print(sorted(data["releases"]))
   PY
   ```
2. Production PyPI version-specific metadata:
   ```bash
   python3.11 - <<'PY'
   import json, urllib.request

   version = "0.0.4"
   with urllib.request.urlopen(
       f"https://pypi.org/pypi/graphfakos/{version}/json",
       timeout=20,
   ) as response:
       data = json.load(response)

   description = data["info"].get("description") or ""
   print(data["info"]["version"])
   print([file["filename"] for file in data["urls"]])
   print("body has final version:", version in description)
   PY
   ```
3. Fresh production install:
   ```bash
   python3.11 -m venv /tmp/graphfakos-pypi-smoke
   /tmp/graphfakos-pypi-smoke/bin/python -m pip install --upgrade pip
   /tmp/graphfakos-pypi-smoke/bin/python -m pip install --no-cache-dir graphfakos==0.0.4
   /tmp/graphfakos-pypi-smoke/bin/graphfakos-smoke --json
   ```
4. TestPyPI RC install:
   ```bash
   python3.11 -m venv /tmp/graphfakos-testpypi-smoke
   /tmp/graphfakos-testpypi-smoke/bin/python -m pip install --upgrade pip
   /tmp/graphfakos-testpypi-smoke/bin/python -m pip install --no-cache-dir \
     --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     graphfakos==0.0.4rc1
   /tmp/graphfakos-testpypi-smoke/bin/graphfakos-smoke --json
   ```
5. GitHub default branch:
   ```bash
   git fetch --prune origin
   git show origin/main:README.md | rg '0\.0\.3|0\.0\.2|0\.0\.1|cacheSeconds'
   git show origin/main:RELEASING.md | rg 'RC-to-Production|invalid-publisher|PyPI stores the README'
   ```

Expected outcomes:

- Production PyPI should show the final version, such as `0.0.4`.
- The version-specific PyPI page should contain the final version in the README
  body and no older release-status text.
- If only RCs were uploaded to TestPyPI, TestPyPI may still label an older
  non-RC release, such as `0.0.1`, as its latest stable release. This is
  expected for an RC-only rehearsal. If the final version was also dispatched
  to TestPyPI, TestPyPI should show that final version as the latest stable
  release.
- The PyPI simple index and pip may lag the JSON API briefly after upload.
  Retry with `--no-cache-dir` after a short wait before assuming a publish
  failed.
- Dynamic README badges, especially `img.shields.io/pypi/v/graphfakos`, may
  lag behind PyPI metadata. For example, a `0.0.3` PyPI page can have correct
  package metadata and README body while the Shields badge still renders
  `v0.0.2`. This is badge cache, not a package publish failure.

Avoid relying on a dynamic PyPI version badge inside the README snapshot
published to PyPI. Prefer either a static release badge that is bumped with the
version or no PyPI version badge in the README body. PyPI already shows the
package version in the page header.

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
