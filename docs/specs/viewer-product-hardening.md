# Viewer Product Hardening

Status: done
Owner: GraphFakos
Last updated: 2026-07-28

## Purpose

Turn the completed dense-viewer and provider-workflow work into a repeatable
product-quality loop: explicit dense navigation modes, visual QA guards,
portable local run commands, richer inspect/edit proof, and maintainability
checks that keep future graph polish from re-growing large owners.

## Current State

GraphFakos already has a provider-neutral 3D workbench, dense 200K and 1M
aggregate envelopes, provider workflow conformance helpers, and a screenshot
visual-QA lane. The remaining gap is hardening: reviewers need obvious pass/fail
signals for graph surface size, theme, label pressure, mode behavior, and
large-route honesty before new visual work can safely iterate.

## Non-Goals

1. Do not add a graph database, provider persistence, source ingestion, or
   semantic truth logic.
2. Do not add new permanent panels that shrink the graph surface.
3. Do not introduce brittle pixel-perfect screenshot comparisons while the
   graph visual design is still evolving.
4. Do not hand-edit generated WebGL bundles.

## Acceptance

1. Visual QA asserts route readiness, dark-canvas state, graph-surface size,
   visible performance HUD, and bounded label pressure for dense routes.
2. Dense scene-level controls map predictably to WebGL label/detail behavior.
3. The 1M aggregate route proves omitted counts and aggregate scale without
   claiming raw million-node rendering.
4. Local run docs give copy/paste commands for 1K, 200K, 1M, browser E2E, and
   visual QA.
5. The implementation grows small owner files or docs first and avoids adding
   more policy branches to the largest viewer files.
