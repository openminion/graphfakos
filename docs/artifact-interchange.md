# GraphFakos Artifact Interchange

GraphFakos artifacts are the provider-neutral handoff format for visual graph
review. They let one package export a graph once, then let GraphFakos or a
different wrapper reopen the same graph without re-running provider-specific
load logic.

## Why this exists

Use artifacts when you want:

- a stable JSON payload to attach to a PR, issue, or release proof,
- a portable HTML preview that teammates can regenerate locally,
- a replayable graph snapshot for diff, provider-status, and inspection flows,
- one shared workflow across `graphfakos`, `sophiagraph`, and `pragmagraph`.

## Export from GraphFakos

```bash
graphfakos-ui \
  --screen diff \
  --artifact-out graphfakos-artifact.json \
  --embed-out graphfakos-embed.html \
  --report-out graphfakos-report.json \
  --markdown-report-out graphfakos-report.md \
  --html-out graphfakos-view.html \
  --json
```

This writes:

- `graphfakos-artifact.json`: provider-neutral graph payload
- `graphfakos-embed.html`: embeddable fragment for package-owned shells
- `graphfakos-report.json`: machine-readable report and diagnostics
- `graphfakos-report.md`: review-friendly Markdown summary
- `graphfakos-view.html`: full standalone viewer export

## Export from Sophiagraph

```bash
cd ../sophiagraph
PYTHONPATH=../graphfakos/src:src \
  .venv/bin/python3.11 -m sophiagraph ui-preview \
  --screen views \
  --artifact-out sophiagraph-artifact.json \
  --embed-out sophiagraph-embed.html \
  --report-out sophiagraph-report.json \
  --markdown-report-out sophiagraph-report.md \
  --html-out sophiagraph-view.html \
  --json
```

## Export from PragmaGraph

```bash
cd ../pragmagraph
PYTHONPATH=../graphfakos/src:src \
  .venv/bin/python3.11 -m pragmagraph ui-preview \
  --screen provider_status \
  --artifact-out pragmagraph-artifact.json \
  --embed-out pragmagraph-embed.html \
  --report-out pragmagraph-report.json \
  --markdown-report-out pragmagraph-report.md \
  --html-out pragmagraph-view.html \
  --json
```

## Replay with GraphFakos

Once you have an artifact, reopen it with the standalone GraphFakos viewer:

```bash
graphfakos-ui \
  --graph-json pragmagraph-artifact.json \
  --screen provider_status \
  --html-out pragmagraph-replay.html \
  --json
```

For diff review, provide both the primary artifact and the comparison artifact:

```bash
graphfakos-ui \
  --graph-json current-artifact.json \
  --comparison-graph-json baseline-artifact.json \
  --screen diff \
  --html-out graph-diff.html \
  --report-out graph-diff-report.json \
  --markdown-report-out graph-diff-report.md \
  --json
```

## Suggested review bundle

For PRs, release notes, and issue triage, the most useful bundle is:

- one `*-artifact.json` file for deterministic replay,
- one `*-report.json` file for machine-readable diagnostics,
- one `*-report.md` file for quick human review,
- one `*-view.html` file when a full local export is helpful.

That keeps the visual proof provider-neutral while letting each package keep
its own storage, trust, and freshness semantics.
