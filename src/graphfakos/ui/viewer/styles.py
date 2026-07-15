"""Package-owned viewer stylesheet."""

from __future__ import annotations

from graphfakos.ui.viewer.surface_styles import SURFACE_STYLE

_STYLE = """
<style>
:root {
  color-scheme: light;
  --gf-bg: #f6f7f3;
  --gf-ink: #17211d;
  --gf-muted: #66716c;
  --gf-line: #d8ded7;
  --gf-panel: #ffffff;
  --gf-soft: #eef2ee;
  --gf-accent: #246c5c;
  --gf-accent-soft: #ddf0eb;
  --gf-blue: #345c8c;
  --gf-blue-soft: #e2eaf6;
  --gf-canvas-bg: #eef4f2;
  --gf-font-body: "Avenir Next", "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body.gf-page {
  margin: 0;
  background: var(--gf-bg);
  color: var(--gf-ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  line-height: 1.45;
}
body.gf-page[data-theme="ink"] {
  --gf-bg: #111612;
  --gf-ink: #eef4ec;
  --gf-muted: #b5c1b7;
  --gf-line: #334039;
  --gf-panel: #171f1a;
  --gf-soft: #202a24;
  --gf-accent: #7ad4ba;
  --gf-accent-soft: #17382f;
  --gf-blue: #9ec4ff;
  --gf-blue-soft: #172b46;
  --gf-canvas-bg: #101713;
  color-scheme: dark;
}
body.gf-page[data-theme="space"] {
  --gf-bg: #060b1c;
  --gf-ink: #eef5ff;
  --gf-muted: #aebbe0;
  --gf-line: #263458;
  --gf-panel: #0b1229;
  --gf-soft: #101a36;
  --gf-accent: #64d9f3;
  --gf-accent-soft: #0b3444;
  --gf-blue: #a998ff;
  --gf-blue-soft: #201a50;
  --gf-canvas-bg: #070d24;
  color-scheme: dark;
}
body.gf-page[data-theme="paper"] {
  --gf-bg: #fbf3df;
  --gf-ink: #30251b;
  --gf-muted: #7d6d5e;
  --gf-line: #eadbc1;
  --gf-panel: #fffaf0;
  --gf-soft: #f5ead3;
  --gf-accent: #9a5f2c;
  --gf-accent-soft: #f1ddbf;
  --gf-blue: #596f95;
  --gf-blue-soft: #dee5f1;
  --gf-canvas-bg: #fffaf0;
}
.gf-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 188px minmax(0, 1fr);
}
.gf-shell[data-nav-collapsed="true"] {
  grid-template-columns: 58px minmax(0, 1fr);
}
.gf-nav {
  border-right: 1px solid var(--gf-line);
  background: var(--gf-panel);
  padding: 20px 14px;
}
.gf-nav-heading {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}
.gf-nav h1 {
  margin: 0 0 18px;
  font-size: 18px;
}
.gf-nav-heading button {
  background: transparent;
  border: 1px solid var(--gf-line);
  border-radius: 9px;
  color: var(--gf-muted);
  cursor: pointer;
  min-height: 32px;
  min-width: 32px;
}
.gf-shell[data-nav-collapsed="true"] .gf-nav h1,
.gf-shell[data-nav-collapsed="true"] .gf-nav a,
.gf-shell[data-nav-collapsed="true"] .gf-nav-analysis {
  font-size: 0;
  overflow: hidden;
  padding-inline: 0;
  text-align: center;
}
.gf-shell[data-nav-collapsed="true"] .gf-nav a::before {
  content: "•";
  font-size: 18px;
  margin: auto;
}
.gf-nav-analysis {
  border-top: 1px solid var(--gf-line);
  margin-top: 12px;
  padding-top: 10px;
}
.gf-nav-analysis summary {
  color: var(--gf-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
  padding: 8px 10px;
  text-transform: uppercase;
}
.gf-nav a {
  display: flex;
  align-items: center;
  min-height: 36px;
  margin: 4px 0;
  padding: 8px 10px;
  border-radius: 8px;
  color: var(--gf-muted);
  text-decoration: none;
  font-size: 14px;
}
.gf-nav a[aria-current="page"] {
  background: var(--gf-accent-soft);
  color: var(--gf-accent);
  font-weight: 700;
}
.gf-content {
  min-width: 0;
  padding: 10px 12px 18px;
}
.gf-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
  margin-bottom: 18px;
}
.gf-eyebrow {
  margin: 0 0 4px;
  color: var(--gf-muted);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}
.gf-header h2 {
  margin: 0;
  font-size: 30px;
  line-height: 1.1;
}
.gf-header p {
  margin: 8px 0 0;
  color: var(--gf-muted);
}
.gf-summary,
.gf-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.gf-summary { justify-content: flex-end; }
.gf-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, .8fr);
  gap: 16px;
  align-items: start;
}
.gf-layout-graph-first {
  display: block;
  min-height: 0;
  position: relative;
}
.gf-graph-primary {
  min-width: 0;
}
.gf-context-drawer {
  background: color-mix(in srgb, var(--gf-panel) 97%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 14px 0 0 14px;
  box-shadow: -18px 0 48px rgb(5 14 30 / 18%);
  bottom: 18px;
  max-height: calc(100dvh - 86px);
  overflow: hidden;
  position: fixed;
  right: 0;
  width: min(390px, calc(100vw - 24px));
  z-index: 20;
}
.gf-context-drawer:not([open]) {
  border-radius: 999px;
  right: 18px;
  width: auto;
}
.gf-context-drawer > summary {
  align-items: center;
  cursor: pointer;
  display: flex;
  gap: 10px;
  justify-content: space-between;
  list-style: none;
  padding: 10px 14px;
}
.gf-context-drawer > summary::-webkit-details-marker { display: none; }
.gf-context-drawer > summary span { font-weight: 900; }
.gf-context-drawer > summary small { color: var(--gf-muted); }
.gf-context-drawer:not([open]) > summary small { display: none; }
.gf-context-drawer:not([open]) > summary {
  min-height: 42px;
  padding: 8px 14px;
}
.gf-context-scroll {
  border-top: 1px solid var(--gf-line);
  max-height: calc(100dvh - 136px);
  overflow: auto;
  padding: 10px;
}
.gf-developer-tools {
  margin-top: 12px;
}
.gf-developer-tools > summary {
  color: var(--gf-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
  padding: 8px 2px;
}
.gf-embed-root[data-graphfakos-screen="explore"] .gf-header {
  align-items: center;
  margin-bottom: 8px;
}
.gf-embed-root[data-graphfakos-screen="explore"] .gf-header .gf-eyebrow,
.gf-embed-root[data-graphfakos-screen="explore"] .gf-header > div:first-child > p:not(:first-child) {
  display: none;
}
.gf-embed-root[data-graphfakos-screen="explore"] .gf-header h2 {
  font-size: 22px;
}
.gf-embed-root[data-graphfakos-screen="explore"] .gf-canvas-panel {
  margin-bottom: 8px;
  padding: 8px;
}
.gf-embed-root[data-graphfakos-screen="explore"] .gf-canvas {
  height: calc(100dvh - 190px);
  min-height: 520px;
}
.gf-integration {
  display: grid;
  grid-template-columns: minmax(220px, .7fr) minmax(0, 1.3fr);
  gap: 12px;
  align-items: start;
}
.gf-panel {
  background: var(--gf-panel);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  padding: 12px;
  margin-bottom: 12px;
}
.gf-panel h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.gf-preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}
.gf-preset-card {
  display: grid;
  gap: 5px;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 10px;
  background: var(--gf-panel);
  color: var(--gf-ink);
}
.gf-preset-card span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-preset-card[data-active="true"] {
  border-color: var(--gf-accent);
  background: var(--gf-accent-soft);
}
.gf-subpanel {
  border-top: 1px solid var(--gf-line);
  margin-top: 12px;
  padding-top: 12px;
}
.gf-subpanel h4 {
  margin: 0 0 10px;
  font-size: 14px;
}
.gf-mini-label {
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}
.gf-note {
  margin: 0 0 12px;
  color: var(--gf-muted);
}
.gf-toolbar { margin-bottom: 16px; }
.gf-toolbar form {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) repeat(6, minmax(110px, .45fr)) auto auto;
  gap: 8px;
}
.gf-toolbar input,
.gf-toolbar select {
  min-width: 0;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
}
.gf-toolbar button {
  border: 1px solid var(--gf-accent);
  border-radius: 8px;
  background: var(--gf-accent);
  color: white;
  padding: 10px 14px;
  font: inherit;
  font-weight: 700;
}
.gf-panel-form {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}
.gf-panel-form input,
.gf-panel-form select {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-ink);
  font: inherit;
  min-width: 0;
  padding: 9px 10px;
}
.gf-panel-form button {
  border: 1px solid var(--gf-accent);
  border-radius: 8px;
  background: var(--gf-accent);
  color: white;
  font: inherit;
  font-weight: 700;
  padding: 9px 10px;
}
.gf-panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.gf-command-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto auto;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.gf-command-bar input {
  min-width: 0;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 8px 10px;
  font: inherit;
}
.gf-command-bar button,
.gf-canvas-tools button {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background: var(--gf-panel);
  color: var(--gf-ink);
  font: inherit;
  font-weight: 700;
  min-height: 30px;
  padding: 4px 9px;
}
.gf-command-bar button {
  border-color: var(--gf-accent);
  background: var(--gf-accent);
  color: #fff;
}
.gf-command-shortcut {
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 800;
  padding: 6px 9px;
  white-space: nowrap;
}
.gf-tool-link,
.gf-inline-link,
.gf-route-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 5px 9px;
  background: var(--gf-panel);
  font-size: 13px;
  font-weight: 700;
}
.gf-lens-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 12px;
}
.gf-active-lens {
  align-items: flex-start;
  background: linear-gradient(135deg, rgba(36, 108, 92, 0.09), rgba(52, 92, 140, 0.08));
  border: 1px solid var(--gf-line);
  border-radius: 18px;
  box-shadow: 0 12px 28px rgba(20, 35, 30, 0.08);
  display: flex;
  gap: 14px;
  justify-content: space-between;
  margin: 12px 0;
  padding: 14px;
}
.gf-active-lens-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.gf-route-chip {
  background: var(--gf-soft);
  color: var(--gf-ink);
}
.gf-interaction-guide {
  background:
    radial-gradient(circle at 12% 18%, color-mix(in srgb, var(--gf-blue-soft) 74%, transparent), transparent 34%),
    linear-gradient(135deg, white, color-mix(in srgb, var(--gf-soft) 82%, white));
  border: 1px solid color-mix(in srgb, var(--gf-blue) 22%, var(--gf-line));
  border-radius: 22px;
  box-shadow: var(--gf-shadow);
  display: grid;
  gap: 14px;
  margin: 12px 0 16px;
  padding: 18px;
}
.gf-guide-copy h3,
.gf-guide-copy p {
  margin: 0;
}
.gf-guide-copy h3 {
  font-size: 20px;
  letter-spacing: -.02em;
}
.gf-guide-copy p {
  color: var(--gf-muted);
  line-height: 1.55;
  margin-top: 6px;
}
.gf-guide-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
.gf-guide-card {
  background: rgba(255, 255, 255, .78);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  color: var(--gf-ink);
  display: grid;
  gap: 5px;
  padding: 10px;
  text-decoration: none;
}
.gf-guide-card span {
  color: var(--gf-blue);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.gf-guide-card p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.45;
  margin: 0;
}
.gf-route-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
.gf-command-palette {
  display: grid;
  gap: 12px;
}
.gf-command-search {
  color: var(--gf-muted);
  display: grid;
  gap: 6px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.gf-command-search input {
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  color: var(--gf-ink);
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0;
  padding: 10px 11px;
  text-transform: none;
}
.gf-command-group {
  display: grid;
  gap: 8px;
}
.gf-command-group h4 {
  font-size: 13px;
  letter-spacing: .04em;
  margin: 0;
  text-transform: uppercase;
}
.gf-command-row {
  align-items: center;
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  padding: 9px 10px;
}
.gf-command-row[data-disabled="true"] {
  opacity: .56;
}
.gf-trail-row {
  align-items: center;
}
.gf-trail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.gf-inline-note {
  color: var(--gf-muted);
  display: block;
  font-size: 12px;
  margin-top: 2px;
}
.gf-facet-explorer {
  display: grid;
  gap: 10px;
}
.gf-facet-group {
  background: color-mix(in srgb, var(--gf-soft) 70%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px;
}
.gf-facet-group h4 {
  flex: 1 0 100%;
  margin: 0 0 2px;
}
.gf-facet-pill {
  align-items: center;
  background: white;
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-ink);
  display: inline-flex;
  gap: 7px;
  padding: 5px 8px;
  text-decoration: none;
}
.gf-facet-pill[aria-current="true"] {
  background: var(--gf-accent-soft);
  border-color: color-mix(in srgb, var(--gf-accent) 35%, var(--gf-line));
}
.gf-facet-pill strong {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-navigation-map {
  display: grid;
  gap: 8px;
}
.gf-navigation-lane {
  background: color-mix(in srgb, var(--gf-blue-soft) 46%, white);
  border-left: 4px solid color-mix(in srgb, var(--gf-blue) 45%, var(--gf-line));
  display: grid;
  gap: 7px;
}
.gf-navigation-lane h4,
.gf-navigation-lane p {
  margin: 0;
}
.gf-navigation-lane p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.45;
}
.gf-display-recipes {
  display: grid;
  gap: 8px;
}
.gf-recipe-card {
  background: color-mix(in srgb, var(--gf-soft) 76%, white);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  color: var(--gf-ink);
  display: grid;
  gap: 4px;
  padding: 10px;
  text-decoration: none;
}
.gf-recipe-card[data-active="true"] {
  background: var(--gf-accent-soft);
  border-color: color-mix(in srgb, var(--gf-accent) 35%, var(--gf-line));
}
.gf-recipe-card span {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.4;
}
.gf-selection-sets {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}
.gf-selection-set-card {
  background: color-mix(in srgb, var(--gf-blue-soft) 54%, white);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 18%, var(--gf-line));
  border-radius: 14px;
  display: grid;
  gap: 7px;
  padding: 10px;
}
.gf-selection-set-card h4,
.gf-selection-set-card p {
  margin: 0;
}
.gf-relationship-table {
  display: grid;
  gap: 8px;
}
.gf-relationship-row {
  border-left: 4px solid color-mix(in srgb, var(--gf-blue) 42%, var(--gf-line));
}
.gf-relationship-row h4 {
  font-size: 14px;
  line-height: 1.35;
}
.gf-evidence-coverage {
  display: grid;
  gap: 8px;
}
.gf-evidence-coverage-row {
  background: color-mix(in srgb, var(--gf-soft) 76%, white);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  display: grid;
  gap: 8px;
  padding: 10px;
}
.gf-evidence-coverage-row h4,
.gf-evidence-coverage-row p {
  margin: 0;
}
.gf-evidence-coverage-row p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.4;
}
.gf-evidence-meter {
  background: white;
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  height: 9px;
  overflow: hidden;
}
.gf-evidence-meter span {
  background: linear-gradient(90deg, var(--gf-accent), var(--gf-blue));
  display: block;
  height: 100%;
}
.gf-capture-panel {
  border-color: #c8d8d0;
}
.gf-action-panel,
.gf-workspace-controls,
.gf-local-controls,
.gf-physics-controls {
  border-color: color-mix(in srgb, var(--gf-accent) 24%, var(--gf-line));
}
.gf-workbook {
  background: color-mix(in srgb, var(--gf-soft) 76%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  display: grid;
  gap: 8px;
  padding: 10px;
}
.gf-workbook-row,
.gf-workbook-slot {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.gf-workbook input {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-ink);
  flex: 1 1 160px;
  font: inherit;
  min-height: 34px;
  padding: 7px 9px;
}
.gf-workbook button,
.gf-workbook a {
  border: 1px solid color-mix(in srgb, var(--gf-accent) 30%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-ink);
  font-size: 12px;
  font-weight: 800;
  padding: 6px 10px;
  text-decoration: none;
}
.gf-workbook button {
  background: white;
  cursor: pointer;
  font-family: inherit;
}
.gf-workbook-list {
  display: grid;
  gap: 6px;
}
.gf-workbook-slot {
  justify-content: space-between;
}
.gf-workbook-slot span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-capture-form {
  display: grid;
  gap: 10px;
}
.gf-capture-templates {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.gf-capture-templates span {
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  margin-right: 2px;
  text-transform: uppercase;
}
.gf-capture-form .gf-capture-templates button {
  background: color-mix(in srgb, var(--gf-accent) 9%, white);
  border: 1px solid color-mix(in srgb, var(--gf-accent) 28%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-ink);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  min-height: 30px;
  padding: 6px 10px;
}
.gf-capture-form label {
  color: var(--gf-muted);
  display: grid;
  gap: 5px;
  font-size: 13px;
  font-weight: 700;
}
.gf-capture-form input,
.gf-capture-form select,
.gf-capture-form textarea {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-ink);
  font: inherit;
  min-width: 0;
  padding: 9px 10px;
}
.gf-capture-form textarea {
  resize: vertical;
}
.gf-viewer-context-preview {
  background: color-mix(in srgb, var(--gf-soft) 72%, white);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  display: grid;
  gap: 8px;
  padding: 10px 12px;
}
.gf-viewer-context-preview b {
  color: var(--gf-ink);
  font-size: 13px;
}
.gf-viewer-context-preview ul {
  display: grid;
  gap: 6px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.gf-viewer-context-preview li {
  align-items: baseline;
  display: flex;
  gap: 10px;
  justify-content: space-between;
}
.gf-viewer-context-preview span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-viewer-context-preview strong {
  color: var(--gf-ink);
  font-size: 12px;
  font-weight: 700;
  text-align: right;
}
.gf-capture-form button {
  border: 1px solid var(--gf-accent);
  border-radius: 8px;
  background: var(--gf-accent);
  color: white;
  font: inherit;
  font-weight: 700;
  min-height: 36px;
  padding: 8px 10px;
}
.gf-capture-status {
  color: var(--gf-muted);
  font-size: 13px;
  margin: 0;
  min-height: 18px;
}
.gf-capture-status[data-state="error"] {
  color: #b42318;
}
.gf-capture-status[data-state="saved"] {
  color: var(--gf-accent);
}
.gf-context-menu {
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  margin-bottom: 10px;
  padding: 8px 10px;
}
.gf-context-menu summary {
  cursor: pointer;
  font-weight: 800;
}
.gf-case-packet {
  background: color-mix(in srgb, var(--gf-soft) 72%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  display: grid;
  gap: 8px;
  margin: 12px 0;
  padding: 10px;
}
.gf-case-packet h4,
.gf-case-packet h5 {
  margin: 0;
}
.gf-surface-menu {
  background: color-mix(in srgb, var(--gf-panel) 94%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  box-shadow: 0 18px 42px rgb(20 29 44 / 20%);
  display: grid;
  gap: 6px;
  min-width: 170px;
  padding: 10px;
  position: fixed;
  z-index: 20;
}
.gf-surface-menu strong {
  color: var(--gf-ink);
  font-size: 12px;
  overflow: hidden;
  padding: 2px 4px 5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gf-surface-menu a,
.gf-surface-menu button {
  background: transparent;
  border: 0;
  border-radius: 8px;
  color: var(--gf-ink);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 7px 8px;
  text-align: left;
  text-decoration: none;
}
.gf-surface-menu a:hover,
.gf-surface-menu button:hover,
.gf-surface-menu a:focus-visible,
.gf-surface-menu button:focus-visible {
  background: var(--gf-accent-soft);
  outline: none;
}
.gf-canvas-grid {
  display: block;
  position: relative;
}
.gf-canvas-shell {
  min-width: 0;
  outline: none;
  position: relative;
}
.gf-webgl-surface {
  background: var(--gf-canvas-bg);
  border-radius: 16px;
  inset: 0;
  min-height: clamp(520px, 76vh, 980px);
  overflow: hidden;
  position: absolute;
  z-index: 2;
}
.gf-webgl-surface canvas {
  display: block;
  height: 100% !important;
  width: 100% !important;
}
.gf-canvas-shell[data-webgl-ready="true"] > .gf-canvas {
  opacity: 0;
  pointer-events: none;
}
.gf-canvas-shell[data-webgl-fallback="true"] > .gf-webgl-surface {
  display: none;
}
.gf-canvas-shell:focus-visible {
  box-shadow: 0 0 0 3px var(--gf-accent-soft);
}
.gf-shortcut-hint {
  color: var(--gf-muted);
  font-size: 12px;
  margin: -4px 0 10px;
}
.gf-scene-status {
  align-items: center;
  color: var(--gf-muted);
  display: flex;
  flex-wrap: wrap;
  font-size: 11px;
  gap: 8px 14px;
  justify-content: space-between;
  margin: 3px 2px 6px;
}
.gf-canvas-help {
  color: var(--gf-muted);
  font-size: 12px;
  margin: 0 0 6px;
}
.gf-canvas-help summary {
  cursor: pointer;
  font-weight: 800;
  width: max-content;
}
.gf-canvas-help[open] {
  background: var(--gf-soft);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  padding: 8px 10px;
}
.gf-detail-status {
  align-items: center;
  color: var(--gf-muted);
  display: inline-flex;
  font-size: 12px;
  gap: 8px;
  margin: 0;
}
.gf-detail-status strong {
  background: color-mix(in srgb, var(--gf-accent-soft) 70%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-accent) 24%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-accent);
  font-weight: 900;
  padding: 4px 8px;
}
.gf-live-selection {
  align-items: center;
  background: color-mix(in srgb, var(--gf-blue-soft) 58%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 24%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-ink);
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  margin: 7px 0 0;
  max-width: 100%;
  padding: 6px 10px;
}
.gf-live-selection[data-selected-count="0"][data-edge-selected="false"] {
  background: var(--gf-soft);
  color: var(--gf-muted);
  font-weight: 700;
}
.gf-canvas {
  width: 100%;
  height: calc(100dvh - 188px);
  max-height: 960px;
  min-height: 600px;
  border: 1px solid var(--gf-line);
  border-radius: 18px;
  background:
    radial-gradient(circle at 20px 20px, color-mix(in srgb, var(--gf-line) 34%, transparent) 1px, transparent 1px),
    var(--gf-panel);
  background-size: 28px 28px;
  cursor: grab;
  touch-action: none;
}
body.gf-page[data-theme="space"] .gf-canvas {
  background:
    radial-gradient(circle at 16% 24%, rgba(100, 217, 243, .12), transparent 25%),
    radial-gradient(circle at 78% 18%, rgba(169, 152, 255, .12), transparent 24%),
    radial-gradient(circle at 50% 80%, rgba(72, 255, 190, .08), transparent 24%),
    radial-gradient(circle at 18px 18px, rgba(238, 245, 255, .16) 1px, transparent 1px),
    linear-gradient(135deg, #030816, #070a1c 48%, #0e1234);
  background-size: auto, auto, auto, 64px 64px, auto;
  box-shadow: inset 0 0 130px rgba(100, 217, 243, .08), 0 20px 80px rgba(0, 0, 0, .22);
}
body.gf-page[data-theme="space"] .gf-edge {
  stroke: rgba(198, 224, 255, .44);
}
body.gf-page[data-theme="space"] .gf-node circle,
body.gf-page[data-theme="space"] .gf-node rect,
body.gf-page[data-theme="space"] .gf-node polygon {
  filter: drop-shadow(0 0 8px rgba(100, 217, 243, .24));
}
body.gf-page[data-theme="space"] .gf-node[data-kind="provider"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="provider"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="provider"] polygon {
  fill: #7dd3fc;
  stroke: #d8f4ff;
}
body.gf-page[data-theme="space"] .gf-node[data-kind="memory"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="memory"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="memory"] polygon {
  fill: #9ee66f;
  stroke: #e5ffd1;
}
body.gf-page[data-theme="space"] .gf-node[data-kind="artifact"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="artifact"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="artifact"] polygon {
  fill: #ffb86b;
  stroke: #ffe2b8;
}
body.gf-page[data-theme="space"] .gf-node[data-kind="document"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="document"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="document"] polygon {
  fill: #d9e7ff;
  stroke: #ffffff;
}
.gf-canvas-renderer {
  background: color-mix(in srgb, var(--gf-panel) 92%, var(--gf-blue));
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  display: block;
  height: auto;
  margin-bottom: 10px;
  width: 100%;
}
.gf-canvas:active { cursor: grabbing; }
.gf-inspect-overlay {
  backdrop-filter: blur(14px);
  background: color-mix(in srgb, var(--gf-panel) 94%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 24%, var(--gf-line));
  border-radius: 18px;
  box-shadow: 0 18px 46px rgb(20 29 44 / 18%);
  display: none;
  gap: 10px;
  max-height: min(70dvh, 680px);
  max-width: min(360px, calc(100% - 32px));
  overflow: auto;
  padding: 12px;
  position: absolute;
  right: 18px;
  bottom: 110px;
  z-index: 8;
}
.gf-inspect-overlay[data-open="true"] {
  display: grid;
}
.gf-inspect-overlay-bar,
.gf-inspect-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: space-between;
}
.gf-inspect-overlay-bar span {
  color: var(--gf-blue);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.gf-inspect-overlay h3 {
  font-size: 18px;
  letter-spacing: -.02em;
  margin: 0;
}
.gf-inspect-overlay p {
  color: var(--gf-muted);
  margin: 0;
}
.gf-inspect-section {
  background: color-mix(in srgb, var(--gf-soft) 62%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  padding: 8px 10px;
}
.gf-inspect-section summary {
  cursor: pointer;
  font-weight: 900;
}
.gf-inspect-command {
  display: grid;
  gap: 8px;
}
.gf-inspect-command label {
  color: var(--gf-muted);
  display: grid;
  font-size: 12px;
  gap: 5px;
}
.gf-inspect-command textarea {
  background: color-mix(in srgb, var(--gf-panel) 86%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  color: var(--gf-ink);
  font: inherit;
  min-height: 76px;
  padding: 8px;
  resize: vertical;
}
.gf-inspect-overlay button {
  background: var(--gf-blue-soft);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 28%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-blue);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  padding: 6px 10px;
}
body.gf-page[data-theme="space"] .gf-inspect-overlay {
  background: rgba(8, 13, 35, .88);
  border-color: rgba(125, 211, 252, .32);
  box-shadow: 0 24px 70px rgba(0, 0, 0, .38), inset 0 0 0 1px rgba(255, 255, 255, .04);
}
body.gf-page[data-theme="space"] .gf-inspect-section,
body.gf-page[data-theme="space"] .gf-inspect-command textarea {
  background: rgba(17, 24, 48, .68);
  border-color: rgba(161, 182, 255, .22);
}
.gf-canvas defs path {
  fill: #768078;
}
.gf-edge {
  fill: none;
  stroke: #9ea9a2;
  stroke-width: 1.5;
  transition: stroke .16s ease, stroke-width .16s ease, opacity .16s ease;
}
.gf-edge[data-selected="true"] {
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-edge[data-stretched="true"] {
  opacity: .9;
  stroke: var(--gf-blue);
  stroke-width: 3;
}
.gf-edge[data-path="true"] {
  stroke: var(--gf-accent);
  stroke-width: 3;
}
.gf-edge[data-clutter="reduced"] {
  opacity: .42;
  stroke-width: 1;
}
.gf-edge[data-clutter="hidden"] {
  opacity: .08;
}
.gf-canvas-shell[data-detail-mode="overview"] .gf-edge:not([data-selected="true"]):not([data-stretched="true"]):not([data-path="true"]) {
  opacity: .18;
  stroke-width: .8;
}
.gf-canvas-shell[data-detail-mode="balanced"] .gf-edge:not([data-selected="true"]):not([data-stretched="true"]):not([data-path="true"]) {
  opacity: .34;
}
.gf-canvas-shell[data-detail-mode="precision"] .gf-edge:not([data-selected="true"]):not([data-stretched="true"]):not([data-path="true"]) {
  opacity: .46;
}
.gf-edge:hover {
  stroke: var(--gf-accent);
  stroke-width: 3;
}
.gf-graph-item-link:focus-visible {
  outline: none;
}
.gf-graph-item-link:focus-visible .gf-edge {
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-graph-item-link:focus-visible .gf-node circle,
.gf-graph-item-link:focus-visible .gf-node rect,
.gf-graph-item-link:focus-visible .gf-node polygon {
  filter: drop-shadow(0 0 0.45rem var(--gf-blue-soft));
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-selection-box {
  fill: color-mix(in srgb, var(--gf-blue-soft) 62%, transparent);
  pointer-events: none;
  stroke: var(--gf-blue);
  stroke-dasharray: 6 4;
  stroke-width: 2;
}
.gf-node circle,
.gf-node rect,
.gf-node polygon {
  fill: var(--gf-accent-soft);
  stroke: var(--gf-accent);
  stroke-width: 2;
  transition: fill .16s ease, stroke .16s ease, stroke-width .16s ease, opacity .16s ease;
}
.gf-node[data-kind="artifact"] circle,
.gf-node[data-kind="artifact"] rect,
.gf-node[data-kind="artifact"] polygon {
  fill: #fff3d6;
  stroke: #9b6b17;
}
.gf-node[data-kind="document"] circle,
.gf-node[data-kind="document"] rect,
.gf-node[data-kind="document"] polygon {
  fill: #e8edf7;
  stroke: var(--gf-blue);
}
.gf-node[data-kind="memory"] circle,
.gf-node[data-kind="memory"] rect,
.gf-node[data-kind="memory"] polygon {
  fill: #e8f1dd;
  stroke: #587a2e;
}
.gf-node[data-selected="true"] circle,
.gf-node[data-selected="true"] rect,
.gf-node[data-selected="true"] polygon,
.gf-node[data-neighbor="true"] circle,
.gf-node[data-neighbor="true"] rect,
.gf-node[data-neighbor="true"] polygon,
.gf-node:hover circle,
.gf-node:hover rect,
.gf-node:hover polygon,
.gf-node[data-highlight="true"] circle,
.gf-node[data-highlight="true"] rect,
.gf-node[data-highlight="true"] polygon {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 3;
  filter: drop-shadow(0 4px 8px rgb(0 0 0 / 18%));
}
.gf-node[data-pinned="true"] circle,
.gf-node[data-pinned="true"] rect,
.gf-node[data-pinned="true"] polygon {
  stroke-dasharray: 5 3;
}
.gf-node[data-hidden="true"],
.gf-edge[data-hidden="true"] {
  opacity: .16;
}
.gf-node text {
  fill: var(--gf-ink);
  font-size: 10px;
  font-weight: 700;
  opacity: .88;
  paint-order: stroke;
  stroke: #fbfcfa;
  stroke-width: 5px;
  stroke-linejoin: round;
  transition: font-size .16s ease, opacity .16s ease;
  pointer-events: none;
}
.gf-canvas-shell[data-detail-mode="overview"] .gf-node-label {
  opacity: 0;
}
.gf-canvas-shell[data-detail-mode="overview"] .gf-node[data-label-priority="focus"] .gf-node-label,
.gf-canvas-shell[data-detail-mode="overview"] .gf-node[data-label-priority="hub"] .gf-node-label,
.gf-canvas-shell[data-detail-mode="overview"] .gf-node[data-selected="true"] .gf-node-label,
.gf-canvas-shell[data-detail-mode="overview"] .gf-node[data-neighbor="true"] .gf-node-label,
.gf-canvas-shell[data-detail-mode="overview"] .gf-node:hover .gf-node-label {
  opacity: .96;
}
.gf-canvas-shell[data-detail-mode="balanced"] .gf-node[data-label-priority="ambient"] .gf-node-label,
.gf-canvas-shell[data-detail-mode="balanced"] .gf-node[data-label-priority="landmark"] .gf-node-label {
  opacity: .28;
}
.gf-canvas-shell[data-detail-mode="detail"] .gf-node[data-label-priority="ambient"] .gf-node-label {
  opacity: .52;
}
.gf-canvas-shell[data-detail-mode="precision"] .gf-node-label {
  font-size: 9px;
  opacity: .94;
}
body.gf-page[data-theme="space"] .gf-node text {
  fill: #f4f8ff;
  stroke: #050817;
  stroke-width: 4px;
}
.gf-canvas-legend {
  background: color-mix(in srgb, var(--gf-soft) 74%, white);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  display: grid;
  gap: 10px;
  margin-top: 10px;
  padding: 12px;
}
.gf-canvas-legend-heading {
  display: grid;
  gap: 2px;
}
.gf-canvas-legend-heading span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-canvas-legend-group {
  display: grid;
  gap: 6px;
}
.gf-canvas-legend-group h4 {
  font-size: 12px;
  letter-spacing: .04em;
  margin: 0;
  text-transform: uppercase;
}
.gf-canvas-legend-group div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.gf-legend-pill {
  align-items: center;
  background: white;
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-ink);
  display: inline-flex;
  gap: 6px;
  padding: 4px 7px;
  text-decoration: none;
}
.gf-legend-pill strong {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-canvas-legend-markers {
  display: grid;
  gap: 7px;
}
.gf-legend-marker {
  display: grid;
  gap: 8px;
  grid-template-columns: 18px minmax(0, 1fr);
}
.gf-legend-marker > span {
  align-self: start;
  border: 2px solid var(--gf-accent);
  border-radius: 999px;
  height: 14px;
  margin-top: 2px;
  width: 14px;
}
.gf-legend-marker > span[data-marker="selected"] {
  background: var(--gf-blue-soft);
  border-color: var(--gf-blue);
}
.gf-legend-marker > span[data-marker="pinned"] {
  border-style: dashed;
}
.gf-legend-marker > span[data-marker="hub"] {
  background: var(--gf-accent-soft);
}
.gf-legend-marker > span[data-marker="evidence"] {
  background: #fff3d6;
  border-color: #9b6b17;
}
.gf-legend-marker strong {
  font-size: 12px;
}
.gf-legend-marker p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.35;
  margin: 0;
}
.gf-minimap {
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  background: color-mix(in srgb, var(--gf-panel) 80%, transparent);
  box-shadow: 0 16px 42px rgba(0, 0, 0, .18);
  padding: 8px;
  position: absolute;
  right: 14px;
  top: 14px;
  opacity: .72;
  transition: opacity .18s ease;
  width: 132px;
  z-index: 3;
}
.gf-minimap:hover { opacity: 1; }
.gf-minimap-heading {
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.gf-minimap svg {
  display: block;
  width: 100%;
  border: 1px solid var(--gf-line);
  border-radius: 6px;
  background: var(--gf-panel);
}
.gf-minimap circle {
  fill: var(--gf-accent-soft);
  stroke: var(--gf-accent);
}
.gf-minimap-viewport {
  fill: color-mix(in srgb, var(--gf-blue-soft) 28%, transparent);
  pointer-events: none;
  stroke: var(--gf-blue);
  stroke-dasharray: 5 3;
  stroke-width: 1.5;
}
.gf-minimap-node-link {
  cursor: pointer;
}
.gf-minimap-node-link:focus-visible {
  outline: none;
}
.gf-minimap-node-link:focus-visible circle,
.gf-minimap-node-link:hover circle {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 2;
}
.gf-minimap circle[data-selected="true"] {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 2;
}
.gf-group-controls {
  align-items: center;
  border-top: 1px solid var(--gf-line);
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  padding-top: 8px;
  flex-wrap: wrap;
}
.gf-group-controls button,
.gf-group-fallback a {
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  background: var(--gf-panel);
  color: var(--gf-muted);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  margin: 0 4px 4px 0;
  padding: 4px 8px;
}
.gf-group-controls [data-gf-group-show-all] {
  border-color: color-mix(in srgb, var(--gf-accent) 38%, var(--gf-line));
  color: var(--gf-accent);
}
.gf-group-controls button[data-active="false"] {
  background: var(--gf-soft);
  color: var(--gf-muted);
  text-decoration: line-through;
}
.gf-card[data-highlight="true"],
.gf-list li[data-highlight="true"] {
  border-color: var(--gf-blue);
  box-shadow: 0 0 0 2px var(--gf-blue-soft);
}
.gf-card {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 12px;
  background: var(--gf-panel);
  margin-bottom: 10px;
  overflow-wrap: anywhere;
}
.gf-card h4 {
  margin: 8px 0;
  font-size: 15px;
}
.gf-card p { margin: 8px 0; }
.gf-component-grid {
  display: grid;
  gap: 10px;
}
.gf-component-card {
  border-color: color-mix(in srgb, var(--gf-blue) 24%, var(--gf-line));
}
.gf-timeline-rail {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0;
}
.gf-timeline-grid {
  display: grid;
  gap: 10px;
}
.gf-timeline-card {
  border-color: color-mix(in srgb, var(--gf-accent) 24%, var(--gf-line));
}
.gf-diff-workbench {
  border-top: 1px solid var(--gf-line);
  margin-top: 12px;
  padding-top: 12px;
}
.gf-diff-grid {
  display: grid;
  gap: 10px;
}
.gf-diff-card {
  border-color: color-mix(in srgb, var(--gf-accent) 30%, var(--gf-line));
}
.gf-badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--gf-soft);
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 700;
}
.gf-badge[data-tone="accent"] {
  background: var(--gf-accent-soft);
  color: var(--gf-accent);
}
.gf-badge[data-tone="blue"] {
  background: var(--gf-blue-soft);
  color: var(--gf-blue);
}
.gf-list {
  display: grid;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.gf-list li {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 9px 10px;
  background: var(--gf-panel);
  overflow-wrap: anywhere;
}
.gf-kv {
  display: grid;
  grid-template-columns: minmax(100px, .45fr) minmax(0, 1fr);
  gap: 8px 12px;
  margin: 0;
}
.gf-kv dt {
  color: var(--gf-muted);
  font-size: 13px;
}
.gf-kv dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.gf-empty {
  margin: 0;
  color: var(--gf-muted);
}
.gf-code-list {
  display: grid;
  gap: 8px;
  margin: 0;
}
.gf-code-list code {
  display: block;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background: var(--gf-soft);
  padding: 9px 10px;
  color: var(--gf-ink);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  overflow-wrap: anywhere;
}
a {
  color: var(--gf-accent);
  text-decoration: none;
}
@media (max-width: 840px) {
  .gf-shell { grid-template-columns: 1fr; }
  .gf-nav { border-right: 0; border-bottom: 1px solid var(--gf-line); }
  .gf-layout,
  .gf-canvas-grid,
  .gf-integration,
  .gf-header,
  .gf-command-bar,
  .gf-toolbar form { grid-template-columns: 1fr; }
  .gf-summary { justify-content: flex-start; }
  .gf-context-drawer {
    border-radius: 18px 18px 0 0;
    bottom: 0;
    max-height: min(70dvh, 620px);
    top: auto;
    width: 100%;
  }
  .gf-context-drawer:not([open]) {
    border-radius: 999px 999px 0 0;
    width: auto;
  }
  .gf-context-scroll { max-height: calc(min(70dvh, 620px) - 54px); }
  .gf-embed-root[data-graphfakos-screen="explore"] .gf-canvas {
    height: calc(100dvh - 250px);
    min-height: 440px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .gf-edge,
  .gf-node circle,
  .gf-node rect,
  .gf-node polygon {
    transition: none;
  }
}
@media (prefers-contrast: more) {
  .gf-edge { opacity: .72 !important; }
  .gf-node circle,
  .gf-node rect,
  .gf-node polygon { stroke-width: 3px; }
  button,
  .gf-tool-link,
  .gf-context-drawer { border-width: 2px; }
}
@media (forced-colors: active) {
  .gf-webgl-surface { display: none; }
  .gf-canvas-shell > .gf-canvas { opacity: 1 !important; pointer-events: auto !important; }
  .gf-node circle,
  .gf-node rect,
  .gf-node polygon { fill: Canvas; stroke: CanvasText; }
  .gf-edge { stroke: CanvasText; }
}
</style>
"""


def viewer_styles() -> str:
    """Return the complete self-contained viewer stylesheet."""
    return _STYLE.replace("</style>", f"{SURFACE_STYLE}</style>")


__all__ = ["viewer_styles"]
