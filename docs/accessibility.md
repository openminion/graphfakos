# Viewer Accessibility Matrix

Status: semantic alpha

GraphFakos treats WebGL as visual enhancement. The linked SVG, route-backed
controls, graph data tables, and contextual panels remain the structured
alternative when WebGL or JavaScript is unavailable.

| WCAG 2.2 AA area | Automated proof | Manual proof |
| --- | --- | --- |
| Keyboard (2.1.1, 2.1.2) | Playwright keyboard/control smoke | Tab through graph controls; use Fit, Reset, Layout, Clear Pins, Undo, and Redo without drag |
| Focus visible (2.4.7, 2.4.11) | Browser focus semantics and package CSS | Confirm focus ring is not obscured at desktop and narrow widths |
| Pointer alternatives (2.5.1, 2.5.7) | Named non-drag toolbar controls | Verify every node/cluster drag result can be cleared or restored with Layout, Clear Pins, Undo, or Redo |
| Target size (2.5.8) | Responsive Playwright viewport | Confirm toolbar and drawer targets remain at least 24 by 24 CSS pixels |
| Name, role, value (4.1.2) | axe critical scan, semantic role assertions | Screen-reader pass over graph application, SVG links, drawer, and live selection status |
| Reflow (1.4.10) | 768 by 1024 browser screenshot | Confirm graph remains primary and tools become a bottom sheet |
| Contrast (1.4.3, 1.4.11) | theme screenshot and axe scan | Inspect light, space, increased-contrast, and forced-colors modes |
| Reduced motion (2.3.3) | CSS and renderer media-query behavior | Confirm force settling is skipped and transitions are disabled |
| Text alternative (1.1.1) | SVG role/name assertions | Confirm full node content remains available through linked SVG/table/inspector paths |

Automated checks are necessary but are not a claim that every assistive-
technology combination has been certified. Release review records the named
manual checks when the viewer interaction model changes.
