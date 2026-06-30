# GraphFakos Source Tree Owner Map

Status: semantic alpha

Purpose: explain the `graphfakos` source-tree owners without treating deep
imports as blanket public promises.

## Public contract

The public alpha surface is documented in:

1. `README.md`
2. `API_COMPATIBILITY.md`
3. `docs/`

The preferred entrypoint is `graphfakos`, with additional stable import roots
for adapters, contracts, models, provider, render, server, static, testing,
and `graphfakos.ui`.

## Root

- `README.md`: public identity, scope, and quick start
- `API_COMPATIBILITY.md`: stable import roots and compatibility expectations
- `RELEASING.md`: package release proof
- `CONTRIBUTING.md`: contributor workflow and PR shape
- `CODE_QUALITY.md`: package-local code-quality rules
- `SECURITY.md`: vulnerability reporting and package security boundary
- `SUPPORT.md`: public support scope
- `CODE_OF_CONDUCT.md`: contributor conduct expectations
- `LICENSE` and `NOTICE`: legal terms and notices
- `pyproject.toml`: package metadata, dependencies, and console scripts
- `MANIFEST.in`: source-distribution file policy
- `Makefile`: package-local development, lint, test, and release commands

## Docs

- `docs/README.md`: package-local docs index and integration model
- `docs/artifact-interchange.md`: portable artifact replay and review workflow
- `docs/custom-provider-example.md`: package-neutral third-party provider example
- `docs/ui-contracts.md`: shared viewer contract, wrapper responsibilities,
  and provider-adapter expectations
- `docs/source-tree-owner-map.md`: this source-tree owner map

## Source

- `src/graphfakos/models.py`: provider-neutral graph DTOs
- `src/graphfakos/artifacts.py`: persisted graph artifact schema, load, and
  write helpers
- `src/graphfakos/provider.py`: provider protocol, validation helpers, and
  provider-neutral diagnostics
- `src/graphfakos/contracts.py`: public adapter/DTO contract exports
- `src/graphfakos/render.py`: public viewer rendering exports
- `src/graphfakos/static.py`: static HTML rendering entrypoints
- `src/graphfakos/server.py`: local preview server primitives
- `src/graphfakos/cli.py`: command-line parsing and execution
- `src/graphfakos/py.typed`: PEP 561 marker for typed package consumers
- `src/graphfakos/ui/`: viewer rendering primitives, screen manifest,
  filter controls, graph canvas, node/edge inspectors, guidance panels, and
  screen layouts
- `src/graphfakos/adapters/file.py`: file-backed provider for persisted graph
  artifacts
- `src/graphfakos/adapters/fixture.py`: fake third-party provider
- `src/graphfakos/testing/assertions.py`: reusable viewer assertions

## Tests

- `tests/test_imports.py`: public import roots
- `tests/test_provider_contract.py`: provider protocol and DTO behavior
- `tests/test_render_static_html.py`: static viewer rendering
- `tests/test_local_preview_server.py`: local server route smoke
- `tests/test_cli.py`: CLI smoke and JSON output
- `tests/test_artifacts.py`: artifact round-trip and file-backed provider proof
- `tests/test_release_check.py`: release script shape
- `tests/test_fixture_adapter.py`: fake third-party provider compatibility
