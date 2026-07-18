"""Styles for graph-local display and toolbar controls."""

SURFACE_STYLE = """
.gf-canvas-tools {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-end;
}
.gf-canvas-tools > button[aria-label="Zoom in"],
.gf-canvas-tools > button[aria-label="Zoom out"] {
  font-size: 17px;
  min-width: 30px;
  padding-inline: 0;
}
.gf-canvas-tools button:disabled {
  cursor: not-allowed;
  opacity: .42;
}
.gf-tool-menu { position: relative; }
.gf-tool-menu > summary {
  align-items: center;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-muted);
  cursor: pointer;
  display: flex;
  font-weight: 900;
  height: 30px;
  justify-content: center;
  list-style: none;
  min-width: 34px;
}
.gf-tool-menu > summary::-webkit-details-marker { display: none; }
.gf-tool-menu > div {
  background: color-mix(in srgb, var(--gf-panel) 96%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  box-shadow: 0 18px 46px rgb(0 0 0 / 24%);
  display: grid;
  gap: 5px;
  min-width: 188px;
  padding: 8px;
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 16;
}
.gf-tool-menu > div button,
.gf-tool-menu > div a {
  justify-content: flex-start;
  text-align: left;
  width: 100%;
}
.gf-theme-toggle {
  background: color-mix(in srgb, var(--gf-blue-soft) 76%, transparent);
  border-color: color-mix(in srgb, var(--gf-blue) 45%, var(--gf-line));
}
.gf-display-dock {
  backdrop-filter: blur(16px);
  background: color-mix(in srgb, var(--gf-panel) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-line) 84%, transparent);
  border-radius: 12px;
  box-shadow: 0 16px 40px rgb(0 0 0 / 18%);
  left: 14px;
  position: absolute;
  top: 14px;
  width: 252px;
  z-index: 6;
}
.gf-display-dock:not([open]) { width: auto; }
.gf-display-dock > summary {
  align-items: center;
  cursor: pointer;
  display: flex;
  font-size: 12px;
  font-weight: 900;
  gap: 12px;
  justify-content: space-between;
  list-style: none;
  min-height: 34px;
  padding: 7px 10px;
  text-transform: uppercase;
}
.gf-display-dock > summary::-webkit-details-marker { display: none; }
.gf-display-dock > summary small {
  color: var(--gf-muted);
  font-size: 10px;
  letter-spacing: .08em;
}
.gf-display-dock-body {
  border-top: 1px solid var(--gf-line);
  display: grid;
  gap: 9px;
  padding: 10px;
}
.gf-display-dock-body label {
  align-items: center;
  color: var(--gf-muted);
  display: grid;
  font-size: 11px;
  font-weight: 800;
  gap: 8px;
  grid-template-columns: 48px minmax(0, 1fr);
}
.gf-display-dock-body input[type="range"] {
  accent-color: var(--gf-accent);
  min-width: 0;
  width: 100%;
}
.gf-display-dock-body p {
  color: var(--gf-muted);
  font-size: 10px;
  line-height: 1.4;
  margin: 2px 0 0;
}
.gf-scene-levels {
  display: grid;
  gap: 4px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
.gf-scene-levels button {
  background: transparent;
  border: 1px solid var(--gf-line);
  border-radius: 7px;
  color: var(--gf-muted);
  cursor: pointer;
  font: inherit;
  font-size: 10px;
  font-weight: 800;
  min-height: 28px;
  padding: 4px 3px;
}
.gf-scene-levels button[data-active="true"] {
  background: var(--gf-accent-soft);
  border-color: color-mix(in srgb, var(--gf-accent) 44%, var(--gf-line));
  color: var(--gf-accent);
}
.gf-webgl-label {
  background: color-mix(in srgb, var(--gf-canvas-bg) 78%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-accent) 22%, transparent);
  border-radius: 999px;
  color: var(--gf-ink);
  font: 750 10px/1.2 var(--gf-font-body);
  opacity: .84;
  padding: 2px 6px;
  pointer-events: none;
  white-space: nowrap;
}
.gf-webgl-label[data-priority="ambient"] { opacity: .62; }
body.gf-page[data-theme="space"] .gf-display-dock,
body.gf-page[data-theme="space"] .gf-tool-menu > div {
  background: rgba(8, 14, 35, .88);
  border-color: rgba(125, 211, 252, .2);
}
.gf-inspect-field {
  color: var(--gf-muted);
  display: grid;
  font-size: 12px;
  font-weight: 800;
  gap: 5px;
  margin-top: 8px;
}
.gf-inspect-field input,
.gf-inspect-field textarea {
  background: color-mix(in srgb, var(--gf-panel) 86%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  color: var(--gf-ink);
  font: inherit;
  padding: 8px;
}
.gf-group-controls {
  border-top: 1px solid var(--gf-line);
  display: grid;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
}
.gf-group-controls-head,
.gf-group-kind-row,
.gf-group-cluster-row {
  align-items: center;
  display: flex;
  gap: 6px;
}
.gf-group-controls-head {
  justify-content: space-between;
}
.gf-group-controls-head > span {
  color: var(--gf-muted);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.gf-group-kind-row,
.gf-group-cluster-row {
  overflow-x: auto;
  padding-bottom: 2px;
}
.gf-group-controls button,
.gf-group-fallback a,
.gf-cluster-card {
  border: 1px solid var(--gf-line);
  background: var(--gf-panel);
  color: var(--gf-muted);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
}
.gf-group-kind-row button,
.gf-group-fallback a,
.gf-group-controls [data-gf-group-show-all] {
  border-radius: 999px;
  padding: 4px 8px;
}
.gf-cluster-card {
  align-items: start;
  border-radius: 14px;
  cursor: pointer;
  display: grid;
  flex: 0 0 190px;
  gap: 2px;
  min-height: 72px;
  padding: 10px 12px;
  text-align: left;
}
.gf-cluster-card span {
  color: var(--gf-muted);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.gf-cluster-card strong {
  color: var(--gf-ink);
  font-size: 14px;
}
.gf-cluster-card small {
  color: var(--gf-muted);
  font-size: 11px;
  line-height: 1.3;
}
.gf-group-controls [data-gf-group-show-all] {
  border-color: color-mix(in srgb, var(--gf-accent) 38%, var(--gf-line));
  color: var(--gf-accent);
}
.gf-group-controls button[data-active="false"] {
  background: color-mix(in srgb, var(--gf-soft) 72%, transparent);
  color: var(--gf-muted);
  opacity: .58;
}
.gf-group-controls button[data-active="false"] strong,
.gf-group-controls button[data-active="false"] small {
  color: var(--gf-muted);
}
"""
