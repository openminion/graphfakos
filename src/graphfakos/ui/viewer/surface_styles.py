"""Styles for graph-local display and toolbar controls."""

SURFACE_STYLE = """
@media (max-width: 840px) {
  .gf-shell[data-nav-collapsed="true"] { grid-template-columns: 1fr; }
  .gf-nav {
    align-self: start;
    border-bottom: 1px solid var(--gf-line);
    box-shadow: 0 8px 24px color-mix(in srgb, var(--gf-bg) 76%, transparent);
    padding: 10px 12px;
    position: sticky;
    top: 0;
    z-index: 40;
  }
  .gf-nav h1,
  .gf-shell[data-nav-collapsed="true"] .gf-nav h1 {
    font-size: 16px;
    margin: 0;
    overflow: visible;
  }
  .gf-shell[data-nav-collapsed="true"] [data-gf-nav-menu] { display: none; }
  .gf-nav-primary {
    display: grid;
    gap: 4px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-top: 10px;
  }
  .gf-nav a {
    justify-content: center;
    margin: 0;
    text-align: center;
  }
  .gf-nav-analysis { margin-top: 8px; }
}
.gf-webgl-surface {
  background: var(--gf-canvas-bg);
  border-radius: 16px;
  cursor: grab;
  inset: 0;
  min-height: clamp(520px, 76vh, 980px);
  overflow: hidden;
  overscroll-behavior: contain;
  position: absolute;
  touch-action: none;
  user-select: none;
  z-index: 2;
}
.gf-webgl-surface:active { cursor: grabbing; }
.gf-webgl-surface canvas {
  display: block;
  height: 100% !important;
  width: 100% !important;
}
.gf-touch-guide { display: none; }
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
.gf-focus-history {
  border: 1px solid var(--gf-line);
  border-radius: 9px;
  display: flex;
  overflow: hidden;
}
.gf-focus-history button {
  background: transparent;
  border: 0;
  border-radius: 0;
  min-width: 30px;
  padding-inline: 7px;
}
.gf-focus-history button + button { border-left: 1px solid var(--gf-line); }
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
.gf-command-dock > summary {
  color: var(--gf-ink);
  font-size: 12px;
  padding: 0 10px;
}
.gf-command-dock > div {
  min-width: min(520px, calc(100vw - 32px));
}
.gf-command-dock .gf-command-bar { margin: 0; }
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
  cursor: pointer;
  font: 750 10px/1.2 var(--gf-font-body);
  opacity: .84;
  padding: 2px 6px;
  pointer-events: auto;
  white-space: nowrap;
}
.gf-webgl-label[data-priority="ambient"] { opacity: .62; }
.gf-webgl-label[data-related="true"] {
  border-color: color-mix(in srgb, var(--gf-accent) 42%, var(--gf-line));
  opacity: .92;
}
.gf-edge[data-previewed="true"] {
  opacity: .92;
  stroke: var(--gf-blue);
  stroke-width: 3;
}
.gf-node[data-previewed="true"] :is(circle, rect, polygon) {
  fill: var(--gf-blue-soft);
  filter: drop-shadow(0 4px 8px rgb(0 0 0 / 18%));
  stroke: var(--gf-blue);
  stroke-width: 3;
}
.gf-canvas-shell[data-detail-mode="overview"] .gf-node[data-previewed="true"] .gf-node-label {
  opacity: .96;
}
.gf-webgl-label[data-collided="true"][data-hovered="false"][data-selected="false"][data-previewed="false"] {
  opacity: 0;
  pointer-events: none;
}
.gf-webgl-label strong { font: inherit; }
.gf-webgl-label small { display: none; }
.gf-webgl-label:hover,
.gf-webgl-label[data-hovered="true"],
.gf-webgl-label[data-previewed="true"] {
  border-color: color-mix(in srgb, var(--gf-accent) 58%, var(--gf-line));
  border-radius: 9px;
  box-shadow: 0 10px 24px color-mix(in srgb, var(--gf-canvas-bg) 42%, transparent);
  max-width: 240px;
  opacity: 1;
  padding: 6px 8px;
  white-space: normal;
}
.gf-webgl-label:hover small,
.gf-webgl-label[data-hovered="true"] small,
.gf-webgl-label[data-previewed="true"] small {
  color: var(--gf-muted);
  display: block;
  font: 650 9px/1.35 var(--gf-font-body);
  margin-top: 3px;
}
.gf-orientation-hud {
  align-items: center;
  backdrop-filter: blur(12px);
  background: color-mix(in srgb, var(--gf-canvas-bg) 82%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-line) 82%, transparent);
  border-radius: 999px;
  bottom: auto;
  color: var(--gf-ink);
  cursor: pointer;
  display: flex;
  gap: 7px;
  left: auto;
  padding: 5px 9px 5px 5px;
  position: absolute;
  right: 160px;
  top: 14px;
  z-index: 5;
}
.gf-orientation-hud > span:first-child {
  align-items: center;
  background: var(--gf-accent-soft);
  border: 1px solid color-mix(in srgb, var(--gf-accent) 50%, var(--gf-line));
  border-radius: 50%;
  color: var(--gf-accent);
  display: flex;
  font-size: 9px;
  font-weight: 950;
  height: 24px;
  justify-content: center;
  transition: transform .12s ease-out;
  width: 24px;
}
.gf-orientation-hud > span:last-child { display: grid; text-align: left; }
.gf-orientation-hud strong { font-size: 10px; line-height: 1.1; }
.gf-orientation-hud small { color: var(--gf-muted); font-size: 8px; line-height: 1.1; }
.gf-spatial-trail {
  align-items: center;
  backdrop-filter: blur(14px);
  background: color-mix(in srgb, var(--gf-canvas-bg) 84%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-line) 84%, transparent);
  border-radius: 999px;
  bottom: 14px;
  box-shadow: 0 12px 30px rgb(0 0 0 / 14%);
  display: flex;
  gap: 2px;
  left: 14px;
  max-width: calc(100% - 112px);
  overflow-x: auto;
  padding: 4px;
  position: absolute;
  scrollbar-width: none;
  z-index: 5;
}
.gf-spatial-trail[hidden] { display: none; }
.gf-spatial-trail::-webkit-scrollbar { display: none; }
.gf-spatial-trail a,
.gf-spatial-trail button {
  background: transparent;
  border: 0;
  border-radius: 999px;
  color: var(--gf-muted);
  cursor: pointer;
  flex: 0 0 auto;
  font: 850 10px/1.2 var(--gf-font-body);
  max-width: 168px;
  overflow: hidden;
  padding: 6px 9px;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gf-spatial-trail a:hover,
.gf-spatial-trail button:not(:disabled):hover { background: var(--gf-accent-soft); color: var(--gf-accent); }
.gf-spatial-items { align-items: center; display: flex; gap: 2px; min-width: 0; }
.gf-spatial-separator { color: var(--gf-muted); flex: 0 0 auto; font-size: 11px; opacity: .58; }
.gf-spatial-trail .gf-spatial-current {
  background: color-mix(in srgb, var(--gf-accent-soft) 84%, transparent);
  color: var(--gf-ink);
  cursor: default;
  opacity: 1;
}
.gf-minimap-heading {
  align-items: center;
  display: flex;
  justify-content: space-between;
}
.gf-minimap-heading > span:last-child {
  align-items: center;
  display: flex;
  gap: 4px;
  text-transform: none;
}
.gf-minimap-heading i {
  color: var(--gf-accent);
  display: inline-block;
  font-size: 13px;
  font-style: normal;
  transform-origin: center;
  transition: transform .12s ease-out;
}
.gf-minimap-heading small {
  color: var(--gf-muted);
  font-size: 9px;
  font-weight: 800;
}
.gf-minimap[data-mode="3d"] svg { cursor: grab; outline: none; touch-action: none; }
.gf-minimap[data-mode="3d"] svg[data-dragging="true"] { cursor: grabbing; }
.gf-minimap[data-mode="3d"] svg:focus-visible {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--gf-accent) 68%, transparent);
}
.gf-minimap[data-mode="3d"] .gf-minimap-viewport {
  fill: color-mix(in srgb, var(--gf-accent-soft) 18%, transparent);
  rx: 4px;
  stroke: color-mix(in srgb, var(--gf-accent) 72%, white 12%);
  stroke-dasharray: 3 2;
  stroke-width: 1.2;
  vector-effect: non-scaling-stroke;
}
.gf-minimap-camera { pointer-events: none; }
.gf-minimap-camera-heading,
.gf-minimap-camera-target,
.gf-minimap-focus-bearing,
.gf-minimap-focus-beacon { display: none; }
.gf-minimap[data-mode="3d"] .gf-minimap-camera-heading {
  display: block;
  stroke: var(--gf-accent);
  stroke-linecap: round;
  stroke-width: 1.6;
  vector-effect: non-scaling-stroke;
}
.gf-minimap[data-mode="3d"] .gf-minimap-camera-target {
  display: block;
  fill: var(--gf-canvas-bg);
  stroke: var(--gf-accent);
  stroke-width: 1.4;
  vector-effect: non-scaling-stroke;
}
.gf-minimap[data-mode="3d"][data-has-focus="true"] .gf-minimap-focus-bearing {
  display: block;
  opacity: .72;
  stroke: color-mix(in srgb, var(--gf-blue) 82%, white 18%);
  stroke-dasharray: 2 2;
  stroke-linecap: round;
  stroke-width: 1.2;
  vector-effect: non-scaling-stroke;
}
.gf-minimap[data-mode="3d"][data-has-focus="true"] .gf-minimap-focus-beacon {
  display: block;
  fill: color-mix(in srgb, var(--gf-blue-soft) 36%, transparent);
  stroke: color-mix(in srgb, var(--gf-blue) 82%, white 18%);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}
.gf-minimap[data-mode="3d"] circle[data-primary="true"] {
  fill: var(--gf-blue);
  opacity: 1;
  stroke: white;
  stroke-width: 1.5;
}
@media (min-width: 841px) {
  .gf-inspect-overlay[data-open="true"]:not([data-compact="true"]) {
    width: min(320px, calc(100% - 32px));
  }
  .gf-canvas-grid:has(.gf-inspect-overlay[data-open="true"]:not([data-compact="true"])) > .gf-minimap {
    opacity: 1;
    right: 350px;
  }
  .gf-canvas-grid:has(.gf-inspect-overlay[data-open="true"]:not([data-compact="true"])) .gf-orientation-hud {
    display: none;
  }
}
.gf-minimap [data-hidden="true"] { display: none; }
.gf-minimap circle[data-layer="far"] { opacity: .3; }
.gf-minimap circle[data-layer="middle"] { opacity: .62; }
.gf-minimap circle[data-layer="near"] { opacity: .95; }
.gf-minimap circle[data-kind="memory"] { fill: #8bd450; stroke: #b6f27e; }
.gf-minimap circle[data-kind="warning"] { fill: #ff7a72; stroke: #ffaaa4; }
.gf-minimap circle[data-kind="artifact"] { fill: #ff9f57; stroke: #ffc28e; }
.gf-minimap circle[data-kind="provider"] { fill: #56d7e8; stroke: #98f3ff; }
.gf-minimap circle[data-kind="document"] { fill: #ffd166; stroke: #ffe49c; }
body.gf-page[data-theme="space"] .gf-display-dock,
body.gf-page[data-theme="space"] .gf-tool-menu > div,
body.gf-page[data-theme="space"] .gf-spatial-trail {
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
.gf-inspect-window-actions {
  align-items: center;
  display: flex;
  gap: 5px;
}
.gf-inspect-window-actions [data-gf-inspect-close] {
  min-width: 30px;
  padding-inline: 7px;
}
.gf-inspect-overlay[data-compact="true"] {
  bottom: 16px;
  max-height: none;
  padding: 9px 10px;
  top: auto;
  width: min(310px, calc(100% - 32px));
}
.gf-inspect-overlay[data-compact="true"] > :not(.gf-inspect-overlay-bar):not(h3) {
  display: none;
}
.gf-inspect-overlay[data-compact="true"] h3 {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  max-width: 100%;
  min-width: 0;
  overflow: hidden;
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
  max-width: 100%;
  min-width: 0;
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
  align-items: center;
  border-radius: 14px;
  display: grid;
  flex: 0 0 190px;
  gap: 6px;
  grid-template-columns: minmax(0, 1fr) auto;
  min-height: 72px;
  padding: 6px;
  text-align: left;
}
.gf-cluster-focus {
  background: transparent !important;
  border: 0 !important;
  cursor: pointer;
  display: grid;
  gap: 2px;
  min-width: 0;
  padding: 5px 6px !important;
  text-align: left;
}
.gf-cluster-card span,
.gf-inspect-neighbors button span {
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
.gf-cluster-toggle {
  align-self: stretch;
  border-radius: 10px;
  cursor: pointer;
  font-size: 10px !important;
  min-width: 48px;
  padding: 5px !important;
}
.gf-cluster-card[data-active="false"] {
  background: color-mix(in srgb, var(--gf-soft) 72%, transparent);
  opacity: .62;
}
.gf-cluster-card[data-active="false"] .gf-cluster-toggle::after { content: " off"; }
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
@media (pointer: coarse) {
  .gf-touch-guide {
    align-items: center;
    backdrop-filter: blur(12px);
    background: color-mix(in srgb, var(--gf-panel) 88%, transparent);
    border: 1px solid color-mix(in srgb, var(--gf-blue) 28%, var(--gf-line));
    border-radius: 999px;
    bottom: 14px;
    box-shadow: 0 10px 30px rgb(15 23 42 / 18%);
    color: var(--gf-ink);
    display: flex;
    flex-wrap: wrap;
    font-size: 11px;
    font-weight: 800;
    gap: 5px 12px;
    justify-content: center;
    left: 50%;
    max-width: calc(100% - 28px);
    opacity: .92;
    padding: 8px 13px;
    pointer-events: none;
    position: absolute;
    transform: translateX(-50%);
    transition: opacity .18s ease, transform .18s ease;
    z-index: 7;
  }
  .gf-touch-guide span + span::before {
    color: var(--gf-muted);
    content: "\00b7";
    margin-right: 12px;
  }
  .gf-canvas-shell[data-touch-engaged="true"] .gf-touch-guide {
    opacity: 0;
    transform: translate(-50%, 8px);
  }
}
.gf-inspect-neighbors {
  border-block: 1px solid var(--gf-line);
  display: grid;
  gap: 7px;
  margin-block: 10px;
  padding-block: 9px;
}
.gf-inspect-neighbors > div:first-child {
  align-items: center;
  display: flex;
  gap: 6px;
  justify-content: space-between;
}
.gf-inspect-neighbors > div:first-child span {
  color: var(--gf-accent);
  font-size: 11px;
  font-weight: 900;
}
.gf-inspect-neighbors nav {
  display: flex;
  gap: 3px;
  margin-left: auto;
}
.gf-inspect-neighbors nav button {
  align-items: center;
  background: transparent;
  border: 1px solid var(--gf-line);
  border-radius: 7px;
  color: var(--gf-ink);
  cursor: pointer;
  display: flex;
  font: inherit;
  height: 25px;
  justify-content: center;
  padding: 0;
  width: 25px;
}
.gf-inspect-neighbors [data-gf-inspect-neighbors] {
  display: grid;
  gap: 5px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  max-height: 168px;
  overflow: auto;
  padding-right: 2px;
}
.gf-inspect-neighbors [data-gf-neighbor-node] {
  align-items: start;
  background: color-mix(in srgb, var(--gf-panel) 84%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 9px;
  color: var(--gf-ink);
  cursor: pointer;
  display: grid;
  font: inherit;
  gap: 1px;
  min-width: 0;
  padding: 7px;
  text-align: left;
}
.gf-inspect-neighbors [data-gf-neighbor-node][data-previewed="true"] {
  background: color-mix(in srgb, var(--gf-accent-soft) 78%, var(--gf-panel));
  border-color: color-mix(in srgb, var(--gf-accent) 58%, var(--gf-line));
  box-shadow: inset 3px 0 0 var(--gf-accent);
}
.gf-inspect-neighbors [data-gf-neighbor-node] strong,
.gf-inspect-neighbors [data-gf-neighbor-node] small,
.gf-inspect-neighbors [data-gf-neighbor-node] em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gf-inspect-neighbors [data-gf-neighbor-node] small {
  color: var(--gf-muted);
  font-size: 10px;
}
.gf-inspect-neighbors [data-gf-neighbor-node] em {
  color: var(--gf-accent);
  font-size: 9px;
  font-style: normal;
  font-weight: 800;
  margin-top: 2px;
}
.gf-canvas-workbench {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 10px;
}
.gf-workbench-tool {
  background: color-mix(in srgb, var(--gf-panel) 88%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  min-width: 0;
  padding: 8px 10px;
}
.gf-workbench-tool > summary {
  color: var(--gf-ink);
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
  list-style-position: outside;
}
.gf-workbench-tool > p,
.gf-workbench-tool form label {
  color: var(--gf-muted);
  font-size: 10px;
}
.gf-tool-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}
.gf-tool-row button,
.gf-workbench-tool form button,
.gf-workbench-tool form select,
.gf-workbench-tool form input {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  font: inherit;
}
.gf-tool-row button,
.gf-workbench-tool form button {
  background: color-mix(in srgb, var(--gf-accent-soft) 62%, var(--gf-panel));
  color: var(--gf-ink);
  cursor: pointer;
  font-size: 10px;
  font-weight: 800;
  padding: 5px 8px;
}
.gf-tool-row button:disabled { cursor: not-allowed; opacity: .42; }
.gf-workbench-tool form {
  display: grid;
  gap: 7px;
  margin-top: 8px;
}
.gf-workbench-tool form label { display: grid; gap: 3px; }
.gf-workbench-tool form select,
.gf-workbench-tool form input { min-width: 0; padding: 5px; }
.gf-histogram { margin-top: 8px; }
.gf-histogram > strong { display: block; font-size: 10px; margin-bottom: 3px; }
.gf-histogram > div {
  align-items: end;
  display: grid;
  gap: 2px;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  height: 44px;
}
.gf-histogram-bin {
  background: linear-gradient(to top, var(--gf-accent) var(--bar), transparent var(--bar));
  border: 1px solid color-mix(in srgb, var(--gf-accent) 36%, var(--gf-line));
  border-radius: 4px 4px 2px 2px;
  color: transparent;
  cursor: crosshair;
  height: 100%;
  min-width: 0;
  padding: 0;
}
.gf-histogram-bin:hover,
.gf-histogram-bin[data-selected="true"] {
  border-color: var(--gf-accent);
  box-shadow: 0 0 0 2px var(--gf-accent-soft);
}
.gf-perspective-list { display: grid; gap: 5px; margin-top: 8px; }
.gf-perspective-list a {
  border-left: 2px solid var(--gf-accent);
  color: var(--gf-ink);
  display: grid;
  padding-left: 7px;
  text-decoration: none;
}
.gf-perspective-list span { color: var(--gf-muted); font-size: 9px; }
[data-gf-local-perspectives] { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 7px; }
[data-gf-local-perspectives] button {
  background: transparent;
  border: 1px dashed var(--gf-line);
  border-radius: 999px;
  color: var(--gf-muted);
  cursor: pointer;
  font: inherit;
  font-size: 9px;
  padding: 3px 7px;
}
.gf-focus-locator {
  align-items: center;
  background: color-mix(in srgb, var(--gf-accent) 78%, #071128);
  border: 1px solid color-mix(in srgb, var(--gf-accent) 72%, white);
  border-radius: 999px;
  box-shadow: 0 8px 28px rgb(0 0 0 / .28);
  color: white;
  cursor: pointer;
  display: flex;
  gap: 5px;
  max-width: 160px;
  padding: 6px 9px;
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 18;
}
.gf-focus-locator[hidden] { display: none; }
.gf-focus-locator span { display: inline-block; transform: rotate(var(--bearing)); }
.gf-focus-locator strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.gf-performance-hud {
  background: color-mix(in srgb, var(--gf-panel) 82%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  bottom: 12px;
  color: var(--gf-ink);
  font-size: 9px;
  padding: 5px 7px;
  position: absolute;
  right: 12px;
  z-index: 16;
}
.gf-performance-hud summary { cursor: pointer; font-weight: 900; }
.gf-performance-hud dl { display: grid; gap: 2px; margin: 6px 0 0; min-width: 120px; }
.gf-performance-hud dl div { display: flex; justify-content: space-between; }
.gf-performance-hud dd { color: var(--gf-accent); margin: 0; }
.gf-provider-inspector {
  border-block: 1px solid var(--gf-line);
  margin-block: 10px;
  padding-block: 8px;
}
.gf-provider-inspector h3 { font-size: 10px; text-transform: uppercase; }
.gf-provider-inspector dl { display: grid; gap: 5px; }
.gf-provider-field { display: grid; grid-template-columns: minmax(76px, .7fr) 1.3fr; }
.gf-provider-field dt { color: var(--gf-muted); font-size: 10px; }
.gf-provider-field dd { margin: 0; overflow-wrap: anywhere; }
@media (max-width: 1100px) {
  .gf-canvas-workbench { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 680px) {
  .gf-canvas-workbench { grid-template-columns: 1fr; }
}
"""
