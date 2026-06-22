# Support

## What Is Supported Today

Current public standalone support is limited to:

1. the provider-neutral package surface documented in `README.md`,
   `API_COMPATIBILITY.md`, and `docs/`,
2. graph DTOs, provider protocol validation, static HTML export, local preview
   server helpers, fixture provider, and reusable viewer assertions, and
3. the release/install smoke and package-local test workflow needed to validate
   the published package.

## Not Covered by the Standalone Public Support Promise

The following surfaces are outside the current standalone package support
promise:

1. hosted or browser runtime behavior owned by OpenMinion,
2. Sophiagraph memory semantics,
3. PragmaGraph source-ingestion semantics,
4. provider wiring or transport layers outside this package,
5. monorepo planning docs and tracker execution artifacts, and
6. third-party services or host-specific deployment wiring.

## Getting Help

For usage questions or bug reports:

1. include the package version,
2. include the exact import path or command you ran,
3. state whether the issue affects the public standalone surface, a provider
   adapter, or an out-of-package runtime/integration surface,
4. include traceback or reproduction steps when available.

If the issue only reproduces inside a larger host runtime, call that out
explicitly; that usually means the problem is on an integration-owned path
rather than the standalone package contract.
