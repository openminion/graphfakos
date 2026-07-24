"""Styles for compact graph operating controls."""

OPERATING_STYLE = """
.gf-operating-dock {
  display: grid;
  gap: 8px;
  grid-template-columns: minmax(180px, 1.15fr) repeat(4, minmax(140px, 1fr));
  margin-top: 10px;
}
.gf-operating-card {
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--gf-panel) 92%, transparent), color-mix(in srgb, var(--gf-panel) 76%, transparent));
  border: 1px solid color-mix(in srgb, var(--gf-line) 88%, transparent);
  border-radius: 14px;
  box-shadow: 0 12px 32px color-mix(in srgb, var(--gf-canvas-bg) 20%, transparent);
  color: var(--gf-muted);
  display: grid;
  gap: 7px;
  min-width: 0;
  padding: 9px;
}
.gf-operating-card header {
  display: grid;
  gap: 2px;
}
.gf-operating-card header span,
.gf-operating-metrics dt {
  color: color-mix(in srgb, var(--gf-accent) 78%, var(--gf-muted));
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.gf-operating-card header strong {
  color: var(--gf-ink);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gf-operating-card p {
  font-size: 10px;
  line-height: 1.35;
  margin: 0;
}
.gf-operating-row {
  display: grid;
  gap: 5px;
  grid-template-columns: minmax(0, 1fr) auto auto;
}
.gf-operating-row input,
.gf-operating-row button,
.gf-operating-row a,
.gf-operating-primary,
.gf-edge-mode-row button,
.gf-operating-fallback a {
  border: 1px solid color-mix(in srgb, var(--gf-line) 90%, transparent);
  border-radius: 999px;
  font: inherit;
  font-size: 10px;
  font-weight: 850;
  min-width: 0;
  padding: 5px 8px;
  text-decoration: none;
}
.gf-operating-row input {
  background: color-mix(in srgb, var(--gf-canvas-bg) 64%, transparent);
  color: var(--gf-ink);
}
.gf-operating-row button,
.gf-operating-row a,
.gf-operating-primary,
.gf-edge-mode-row button {
  background: color-mix(in srgb, var(--gf-accent-soft) 72%, var(--gf-panel));
  color: var(--gf-accent);
  cursor: pointer;
}
.gf-operating-primary { display: inline-flex; justify-content: center; }
.gf-operating-links,
.gf-operating-fallback,
.gf-edge-mode-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.gf-operating-links a {
  background: color-mix(in srgb, var(--gf-canvas-bg) 58%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-line) 90%, transparent);
  border-radius: 10px;
  color: var(--gf-ink);
  display: grid;
  min-width: 0;
  padding: 5px 7px;
  text-decoration: none;
}
.gf-operating-links strong,
.gf-operating-links small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gf-operating-links small { color: var(--gf-muted); font-size: 9px; }
.gf-edge-mode-row button[data-active="true"] {
  background: var(--gf-accent);
  border-color: color-mix(in srgb, var(--gf-accent) 72%, white);
  color: var(--gf-canvas-bg);
}
.gf-operating-fallback {
  font-size: 9px;
}
.gf-operating-fallback a {
  background: transparent;
  color: var(--gf-muted);
  padding-block: 3px;
}
.gf-operating-metrics {
  display: grid;
  gap: 5px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}
.gf-operating-metrics div {
  background: color-mix(in srgb, var(--gf-canvas-bg) 54%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-line) 80%, transparent);
  border-radius: 9px;
  min-width: 0;
  padding: 5px 6px;
}
.gf-operating-metrics dd {
  color: var(--gf-ink);
  font-size: 11px;
  font-weight: 850;
  margin: 1px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 1100px) {
  .gf-operating-dock { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 680px) {
  .gf-operating-dock { grid-template-columns: 1fr; }
}
"""
