# Contributing to GraphFakos

Thanks for contributing.

## Before Coding

Read these docs before coding:

1. [README.md](./README.md)
2. [API_COMPATIBILITY.md](./API_COMPATIBILITY.md)
3. [docs/README.md](./docs/README.md)
4. [docs/source-tree-owner-map.md](./docs/source-tree-owner-map.md)
5. [RELEASING.md](./RELEASING.md) when the work affects packaging or release
   behavior

Treat the package README and API compatibility policy as the stable public
contract. GraphFakos is a viewer and adapter-contract package, not a memory
store, source ingester, graph builder, or runtime policy engine.

## Quick Start

1. Fork and create a branch.
2. Make focused changes.
3. Add or update tests.
4. Open a PR with a clear summary.

## Repository Layout

```text
graphfakos/
├── src/graphfakos/             # public package shipped on PyPI
│   ├── adapters/               # fixture and example providers
│   ├── testing/                # reusable viewer assertions
│   ├── ui/                     # dependency-free graph viewer rendering
│   ├── contracts.py            # public adapter/DTO contract exports
│   ├── models.py               # provider-neutral DTOs
│   ├── provider.py             # provider protocol and validation helpers
│   ├── render.py               # public rendering exports
│   ├── server.py               # local preview server primitives
│   └── static.py               # static HTML export helpers
├── tests/                      # package tests and contract fixtures
├── docs/                       # public package-local docs
├── pyproject.toml
├── scripts/validate/           # package-local code-quality validators
├── scripts/baselines/          # ratchet baselines consumed by validators
└── scripts/release_check.py    # package release smoke
```

The public wheel is everything under `src/graphfakos/`. Tests, package docs,
and release tooling support the package but do not enlarge the runtime API
beyond `README.md`, `API_COMPATIBILITY.md`, and `docs/`.

## Setup

Requires Python 3.11+.

```bash
# 1. Clone and enter the repo
git clone https://github.com/openminion/graphfakos.git graphfakos
cd graphfakos

# 2. Create and activate a virtualenv
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode with dev extras
make dev-install

# 4. Install local hooks, including commit-message enforcement
make hooks-install
```

## Running Tests

```bash
# Full package test suite
make test

# Full local quality gate
make check

# Structure and complexity ratchets only
make validate-patterns

# Release/install smoke
make release-check
```

If you need a narrower loop while iterating, run `python3.11 -m pytest -q
tests/<target>` inside the activated virtualenv.

## Running Lint and Formatting

```bash
# Lint only
make lint

# Check formatting without rewriting files
make format-check

# Apply formatting and autofixes
make fix
```

If pre-commit, `make hooks-run`, or GitHub Actions reports formatter changes,
run `make fix`, review the diff, rerun `make check`, and recommit before
pushing again.

## Development Basics

1. Follow the existing typed, deterministic package style.
2. Keep provider-specific graph semantics outside GraphFakos core.
3. Add or update tests for any behavior change.
4. Keep static export working as the baseline viewer mode.
5. Do not add hidden imports from Sophiagraph, PragmaGraph, or OpenMinion.
6. Do not bundle unrelated refactors into the same PR.
7. Keep public docs portable and copy/paste friendly.

Commit message guidance:

1. Use commit messages in the form `<type>: <summary>` or
   `<type>(<scope>): <summary>`.
2. Approved current types are `feat`, `fix`, `docs`, `refactor`, `test`,
   `chore`, `style`, and `build`.
3. In this package, scope is optional but encouraged when it improves owner
   clarity, for example `ui`, `artifacts`, `cli`, `render`, `docs`, or
   `release`.
4. Keep the summary specific to the landed change and avoid vague messages like
   `update`.
5. Prefer the most specific truthful type; do not use `chore` when `docs`,
   `test`, `refactor`, or `build` is more accurate.
6. Do not use local shorthand or planning labels as normal commit types.

The same policy runs locally through `make hooks-install` and again in GitHub
Actions on pull requests plus `dev`/`main` pushes.

Preferred PR shape:

`Add path controls to graph viewer`

- add ...
- align ...
- polish ...

Validation
- `<command>`
- `<command>`

## Submitting a Pull Request

1. Fork and create a branch from `main`.
2. Make your change; add or update tests; run the relevant local validation.
3. Open a PR with a clear summary. In the description, include what changed,
   why, and the exact commands you ran for validation.
4. Keep PRs small and reviewable.
5. Do not bundle unrelated refactors into the same PR.

## Legal Basics

1. You keep ownership of your contributions.
2. By submitting a contribution, you license it under Apache-2.0.
3. Apache-2.0 includes a patent license for your contribution, with the standard
   patent-termination condition in the license text.
4. Only submit code or content you have the right to contribute.
5. Do not add third-party code or assets unless their license is compatible and
   clearly documented.
6. Project names and logos are not granted for endorsement use.
7. `graphfakos` is provided on an "as is" basis under the project license.
8. See [LICENSE](./LICENSE) for the full legal terms, disclaimers, and
   limitations of liability.

## Security

If you find a security issue, do not open a public issue with exploit details.
Use the project security reporting process.

## Code of Conduct

By participating, you agree to follow [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
