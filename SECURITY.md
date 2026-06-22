# Security Policy

## Reporting a Vulnerability

Please do not open a public issue with exploit details.

Instead:

1. contact the project maintainers privately through the security reporting
   channel used for OpenMinion, or
2. if that channel is unavailable, open a minimal private coordination thread
   without exploit details and request a secure handoff path.

## Scope

This package's security posture follows the same general rules as OpenMinion:

1. report vulnerabilities privately first,
2. do not publish proof-of-exploit details before maintainers have had time to
   assess and respond,
3. include affected version, reproduction steps, and impact summary when
   possible.

## Package Boundary

`graphfakos` is a standalone viewer and adapter-contract package. Security
reports should say whether the issue affects:

1. the public standalone package surface (`src/graphfakos/`),
2. static HTML rendering,
3. local preview server behavior,
4. provider adapter contract validation, or
5. host/runtime behavior that belongs outside this package boundary.

## Dependency Note

If an issue depends on a host runtime, browser integration, or a provider
adapter from another package, call that out explicitly. That helps determine
whether the problem is in GraphFakos itself or in an external integration path.
