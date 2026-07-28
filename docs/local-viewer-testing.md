# Local Viewer Testing

Use these commands when reviewing graph navigation, dense layouts, inspect/edit
overlays, and visual QA.

## Interactive Routes

Open the standard package demo:

```bash
make preview
```

Open the 1K scale route:

```bash
make benchmark-fixtures
PYTHONPATH=src .venv/bin/graphfakos-ui \
  --provider-envelope web/fixtures/viewer-scale-1000.json \
  --screen explore \
  --render-engine 3d \
  --theme space \
  --layout islands \
  --render-limit 240 \
  --serve \
  --open
```

Open the 200K aggregate route:

```bash
make benchmark-fixtures
PYTHONPATH=src .venv/bin/graphfakos-ui \
  --provider-envelope web/fixtures/viewer-scale-200000.json \
  --screen explore \
  --render-engine 3d \
  --theme space \
  --layout islands \
  --render-limit 240 \
  --serve \
  --open
```

Open the 1M aggregate route:

```bash
make benchmark-fixtures
PYTHONPATH=src .venv/bin/graphfakos-ui \
  --provider-envelope web/fixtures/viewer-scale-1000000.json \
  --screen explore \
  --render-engine 3d \
  --theme space \
  --layout islands \
  --render-limit 240 \
  --serve \
  --open
```

The 200K and 1M routes render aggregate provider-envelope records, omitted
counts, bundles, and expansion cursors. They do not draw every raw node in the
browser.

## Review Gates

Run browser interaction coverage:

```bash
make browser-e2e
```

Capture visual QA screenshots and threshold checks:

```bash
make visual-qa
```

Run the package closeout gate:

```bash
make check
```

Screenshots from visual QA are written under `web/test-results/`.
