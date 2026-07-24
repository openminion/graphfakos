import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { linkVisibleForDetail, shapeLinks } from "../src/link-shape.js";
import { nodeColorForKind } from "../src/visual-contrast.js";
import {
  detailLevelForCamera,
  labelBudgetForDetail,
  nodeScaleForCount,
  semanticZoom,
  zoomStableNodeScale,
} from "../src/semantic-detail.js";
import { directionalNodeId } from "../src/spatial-navigation.js";

test("maps camera distance to semantic graph detail", () => {
  expect(semanticZoom(900, 900)).toBe(1);
  expect(semanticZoom(900, 450)).toBe(2);
  expect(detailLevelForCamera({ nodeCount: 240, referenceDistance: 900, cameraDistance: 1400 }))
    .toBe("overview");
  expect(detailLevelForCamera({ nodeCount: 240, referenceDistance: 900, cameraDistance: 900 }))
    .toBe("balanced");
  expect(detailLevelForCamera({ nodeCount: 240, referenceDistance: 900, cameraDistance: 600 }))
    .toBe("detail");
  expect(detailLevelForCamera({ nodeCount: 240, referenceDistance: 900, cameraDistance: 360 }))
    .toBe("precision");
  expect(labelBudgetForDetail("overview", 1, 240)).toBe(1);
  expect(labelBudgetForDetail("detail", 1, 240)).toBe(9);
  expect(nodeScaleForCount(12)).toBeGreaterThan(nodeScaleForCount(48));
  expect(nodeScaleForCount(48)).toBeGreaterThan(nodeScaleForCount(240));
  expect(nodeScaleForCount(240)).toBeLessThan(0.5);
});

test("keeps node marks readable while camera zoom changes", () => {
  expect(zoomStableNodeScale(4)).toBeLessThan(zoomStableNodeScale(1));
  expect(zoomStableNodeScale(0.25)).toBeGreaterThan(zoomStableNodeScale(1));
  expect(zoomStableNodeScale(100)).toBeGreaterThanOrEqual(0.4);
});

test("progressive edge detail preserves aggregates and active context", () => {
  const aggregate = { id: "bundle", kind: "edge_bundle", source: "a", target: "b" };
  const selected = { id: "selected", selected: true, source: "a", target: "c" };
  const focused = { id: "focus", source: "focus-node", target: "d" };
  expect(linkVisibleForDetail(aggregate, "overview")).toBe(true);
  expect(linkVisibleForDetail(selected, "overview")).toBe(true);
  expect(linkVisibleForDetail(focused, "overview", "focus-node")).toBe(true);
  expect(linkVisibleForDetail({ id: "any", source: "a", target: "b" }, "precision")).toBe(true);
});

test("keeps dense cluster summaries brighter than generic graph items", () => {
  expect(nodeColorForKind("cluster")).toBe("#8fdaff");
  expect(nodeColorForKind("unknown")).toBe("#a8c5f2");
});

test("chooses the nearest visible node in a screen direction", () => {
  const points = [
    { id: "origin", x: 100, y: 100 },
    { id: "right-near", x: 150, y: 104 },
    { id: "right-off-axis", x: 125, y: 180 },
    { id: "right-hidden", x: 120, y: 100, hidden: true },
    { id: "left", x: 50, y: 96 },
    { id: "up", x: 102, y: 40 },
  ];

  expect(directionalNodeId(points, "origin", "right")).toBe("right-near");
  expect(directionalNodeId(points, "origin", "right", { width: 140, height: 150 })).toBe("");
  expect(directionalNodeId(points, "origin", "right", { width: 160, height: 200 })).toBe("right-near");
  expect(directionalNodeId(points, "origin", "left")).toBe("left");
  expect(directionalNodeId(points, "origin", "up")).toBe("up");
  expect(directionalNodeId(points, "origin", "unknown")).toBe("");
});

test("shapes natural curves and separates parallel links", () => {
  const nodes = [
    { id: "a", clusterId: "alpha" },
    { id: "b", clusterId: "alpha" },
    { id: "c", clusterId: "beta" },
  ];
  const links = [
    { id: "parallel:a", sourceId: "a", targetId: "b" },
    { id: "parallel:b", sourceId: "a", targetId: "b" },
    { id: "cross", sourceId: "a", targetId: "c" },
    { id: "bundle", kind: "edge_bundle", sourceId: "b", targetId: "c" },
    { id: "loop", sourceId: "a", targetId: "a" },
  ];

  const shaped = shapeLinks(nodes, links);
  const byId = new Map(shaped.map((link) => [link.id, link]));
  expect(byId.get("parallel:a").curvature).toBeLessThan(0);
  expect(byId.get("parallel:b").curvature).toBeGreaterThan(0);
  expect(byId.get("parallel:a").curveRotation).toBe(byId.get("parallel:b").curveRotation);
  expect(Math.abs(byId.get("cross").curvature)).toBeGreaterThan(0.3);
  expect(Math.abs(byId.get("bundle").curvature)).toBeGreaterThan(Math.abs(byId.get("cross").curvature));
  expect(Math.abs(byId.get("loop").curvature)).toBeGreaterThan(0.5);
  expect(shapeLinks(nodes, links)).toEqual(shaped);
});

test("mounts and navigates the packaged 3D graph", async ({ page }, testInfo) => {
  const startedAt = Date.now();
  await page.goto("/explore");
  const graph = page.locator(".gf-canvas-shell");
  await expect(graph).toBeVisible();
  await expect(graph).toHaveAttribute("data-webgl-ready", "true", { timeout: 15_000 });
  expect(Date.now() - startedAt).toBeLessThan(5_000);
  const box = await graph.boundingBox();
  expect(box.height).toBeGreaterThan(500);
  expect(box.width).toBeGreaterThan(700);
  const orientation = page.getByRole("button", { name: "Reset 3D orientation" });
  await expect(orientation).toBeVisible();
  await expect(orientation).toHaveAttribute("data-yaw", /-?\d+\.\d/);
  await orientation.click();
  await page.getByRole("button", { name: "Fit selected or visible graph" }).click();
  await page.getByRole("link", { name: "Light" }).click();
  await expect(page.locator("body")).toHaveAttribute("data-theme", "default");
  await expect(page.getByRole("link", { name: "Dark" })).toBeVisible();
  await page.screenshot({ path: "test-results/graphfakos-3d-1280x720.png", fullPage: false });
  await testInfo.attach("performance", {
    body: JSON.stringify({
      fixture: "dense",
      viewport: "1280x720",
      browser: testInfo.project.name || "chromium",
      firstSceneMs: Date.now() - startedAt,
      totalNodes: 36,
      visibleNodes: 36,
      drawnNodes: 36,
      renderer: "3d-force-graph@1.80.0",
    }),
    contentType: "application/json",
  });
});

test("keeps small 3D nodes targetable and focused content visible", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const label = page.locator(".gf-webgl-label[data-node-id='provider:cluster-1']");
  await expect(label).toBeVisible();
  await label.hover();
  await expect(label.locator("small")).toBeVisible();
  await expect(label.locator("small")).toContainText("provider");
  await expect(label.locator("small")).toContainText("links");
  await expect.poll(async () => {
    const [labelBox, surfaceBox] = await Promise.all([
      label.boundingBox(),
      page.locator(".gf-webgl-surface").boundingBox(),
    ]);
    const viewport = page.viewportSize();
    const visibleTop = Math.max(0, surfaceBox.y);
    const visibleBottom = Math.min(viewport.height, surfaceBox.y + surfaceBox.height);
    return labelBox.y >= visibleTop + 4
      && labelBox.y + labelBox.height <= visibleBottom - 4;
  }).toBe(true);
  await page.screenshot({ path: "test-results/graphfakos-3d-hover-preview.png", fullPage: false });
  await label.click();
  const inspector = page.locator("[data-gf-inspect-overlay]");
  await expect(inspector).toHaveAttribute("data-open", "true");
  await expect(inspector.locator("[data-gf-inspect-title]")).toHaveText("Provider Cluster 1");
  const relatedLabels = page.locator(".gf-webgl-label[data-related='true']");
  await expect.poll(() => relatedLabels.count()).toBeGreaterThan(2);
  expect(await relatedLabels.count()).toBeLessThanOrEqual(6);
  await expect(relatedLabels.first()).toHaveAttribute("data-selected", "false");
  expect(Number.parseFloat(await relatedLabels.first().evaluate((item) => getComputedStyle(item).opacity)))
    .toBeGreaterThan(0.8);
  await expect.poll(async () => {
    const [labelBox, inspectorBox] = await Promise.all([
      label.boundingBox(),
      inspector.boundingBox(),
    ]);
    return labelBox.x + labelBox.width <= inspectorBox.x - 12;
  }).toBe(true);

  const surface = page.locator(".gf-webgl-surface");
  const surfaceBox = await surface.boundingBox();
  await page.mouse.click(surfaceBox.x + 18, surfaceBox.y + surfaceBox.height - 18);
  await expect(inspector).toHaveAttribute("data-open", "false");
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate(
    (viewer) => viewer.getState().selected_node_id,
  )).toBeNull();
});

test("supports touch-first inspection and pinch navigation", async ({ browser }) => {
  const context = await browser.newContext({
    hasTouch: true,
    isMobile: true,
    viewport: { width: 430, height: 860 },
  });
  const page = await context.newPage();
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const viewer = page.locator("graphfakos-viewer");
  const shell = page.locator(".gf-canvas-shell");
  await expect(shell).toHaveAttribute("data-webgl-ready", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(await page.evaluate(() => document.documentElement.clientWidth));

  const guide = page.locator("[data-gf-touch-guide]");
  await expect(guide).toBeVisible();
  await expect(guide).toContainText("Tap inspect");
  await expect(guide).toContainText("Pinch zoom");

  if (browser.browserType().name() === "chromium") {
    const client = await context.newCDPSession(page);
    const surfaceBox = await page.locator(".gf-webgl-surface").boundingBox();
    const center = {
      x: surfaceBox.x + surfaceBox.width * 0.45,
      y: surfaceBox.y + surfaceBox.height * 0.55,
    };
    const before = await viewer.evaluate(
      (element) => element.exportNavigationTrail().current.camera.distance,
    );
    await client.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [
        { x: center.x - 28, y: center.y },
        { x: center.x + 28, y: center.y },
      ],
    });
    for (const spread of [44, 64, 92]) {
      await client.send("Input.dispatchTouchEvent", {
        type: "touchMove",
        touchPoints: [
          { x: center.x - spread, y: center.y },
          { x: center.x + spread, y: center.y },
        ],
      });
      await page.waitForTimeout(32);
    }
    await client.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await expect.poll(async () => {
      const distance = await viewer.evaluate(
        (element) => element.exportNavigationTrail().current.camera.distance,
      );
      return Math.abs(distance - before);
    }).toBeGreaterThan(2);
  }
  await expect(shell).toHaveAttribute("data-touch-engaged", "true");
  await expect(guide).toHaveCSS("opacity", "0");

  const label = page.locator(".gf-webgl-label").first();
  await expect(label).toBeVisible();
  const nodeId = await label.getAttribute("data-node-id");
  expect(nodeId).toBeTruthy();
  await label.evaluate((element) => {
    const box = element.getBoundingClientRect();
    const eventInit = {
      bubbles: true,
      cancelable: true,
      button: 0,
      clientX: box.left + box.width / 2,
      clientY: box.top + box.height / 2,
      pointerType: "touch",
    };
    element.dispatchEvent(new PointerEvent("pointerdown", eventInit));
    element.dispatchEvent(new PointerEvent("pointerup", eventInit));
  });
  const inspector = page.locator("[data-gf-inspect-overlay]");
  await expect(inspector).toHaveAttribute("data-open", "true");
  await expect(inspector).toHaveAttribute("data-node-id", nodeId);
  await context.close();
});

test("docks, collapses, and restores the inspector inside the graph scene", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("provider:cluster-1"));

  const shell = page.locator(".gf-canvas-shell");
  const inspector = page.locator("[data-gf-inspect-overlay]");
  const minimap = page.locator("[data-gf-minimap]");
  const orientation = page.locator("[data-gf-orientation-reset]");
  await expect(inspector).toHaveAttribute("data-open", "true");
  const contained = await Promise.all([shell.boundingBox(), inspector.boundingBox()])
    .then(([scene, dock]) => dock.x >= scene.x && dock.y >= scene.y
      && dock.x + dock.width <= scene.x + scene.width
      && dock.y + dock.height <= scene.y + scene.height);
  expect(contained).toBe(true);
  const [inspectorBox, minimapBox] = await Promise.all([
    inspector.boundingBox(),
    minimap.boundingBox(),
  ]);
  expect(minimapBox.x + minimapBox.width).toBeLessThanOrEqual(inspectorBox.x - 8);
  await expect(orientation).toBeHidden();

  const expandedHeight = (await inspector.boundingBox()).height;
  await inspector.locator("[data-gf-inspect-compact]").click();
  await expect(inspector).toHaveAttribute("data-compact", "true");
  await expect(inspector.locator("[data-gf-inspect-compact]")).toHaveText("Expand");
  const compactHeight = (await inspector.boundingBox()).height;
  expect(compactHeight).toBeLessThan(expandedHeight / 2);
  await expect(orientation).toBeVisible();

  await inspector.locator("[data-gf-inspect-compact]").click();
  await expect(inspector).toHaveAttribute("data-compact", "false");
  await expect(inspector.locator("[data-gf-inspect-compact]")).toHaveText("Collapse");
  await inspector.locator("[data-gf-inspect-close]").click();
  await expect(inspector).toHaveAttribute("data-open", "false");
  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("provider:cluster-1"));
  await expect(inspector).toHaveAttribute("data-open", "true");
});

test("unwinds menu, inspector, and graph focus with layered Escape", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const viewer = page.locator("graphfakos-viewer");
  const shell = page.locator(".gf-canvas-shell");
  const inspector = page.locator("[data-gf-inspect-overlay]");
  await expect(shell).toHaveAttribute("data-webgl-ready", "true");
  await viewer.evaluate((element) => element.focusNode("provider:cluster-1"));
  await expect(inspector).toHaveAttribute("data-open", "true");

  await shell.press("j");
  await expect(inspector.locator("[data-gf-neighbor-node][data-previewed='true']")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(inspector.locator("[data-gf-neighbor-node][data-previewed='true']")).toHaveCount(0);
  await expect(inspector).toHaveAttribute("data-open", "true");
  expect(await viewer.evaluate((element) => element.getState().selected_node_id))
    .toBe("provider:cluster-1");

  const structuredNode = page.locator(".gf-node[data-node-id='provider:cluster-1']");
  await structuredNode.dispatchEvent("keydown", { key: "F10", shiftKey: true, bubbles: true });
  await expect(page.locator(".gf-surface-menu")).toBeVisible();
  await inspector.locator("[data-gf-overlay-action='center']").focus();
  await page.keyboard.press("Escape");
  await expect(page.locator(".gf-surface-menu")).toHaveCount(0);
  await expect(inspector).toHaveAttribute("data-open", "true");

  await page.keyboard.press("Escape");
  await expect(inspector).toHaveAttribute("data-open", "false");
  await expect(shell).toBeFocused();
  expect(await viewer.evaluate((element) => element.getState().selected_node_id))
    .toBe("provider:cluster-1");

  await page.keyboard.press("Escape");
  const cleared = await viewer.evaluate((element) => element.getState());
  expect(cleared.selected_node_id).toBeNull();
  expect(cleared.selected_node_ids).toEqual([]);
  await expect(page.locator(".gf-webgl-label[data-related='true']")).toHaveCount(0);
  await expect(page.locator("[data-gf-focus-history='back']")).toBeEnabled();
});

test("declutters local 3D labels in screen space", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.dispatch({
    name: "scene-level",
    payload: { value: "local" },
  }));
  const labels = page.locator(".gf-webgl-label[data-collided='false']");
  await expect.poll(() => labels.count()).toBeGreaterThan(2);
  const overlaps = await labels.evaluateAll((elements) => {
    const boxes = elements
      .filter((element) => Number.parseFloat(getComputedStyle(element).opacity) > 0.05)
      .map((element) => ({ id: element.dataset.nodeId, box: element.getBoundingClientRect() }));
    const collisions = [];
    boxes.forEach((left, index) => {
      boxes.slice(index + 1).forEach((right) => {
        if (
          left.box.left < right.box.right
          && left.box.right > right.box.left
          && left.box.top < right.box.bottom
          && left.box.bottom > right.box.top
        ) collisions.push([left.id, right.id]);
      });
    });
    return collisions;
  });
  expect(overlaps).toEqual([]);
});

test("uses the overview map as a live 3D camera navigator", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const viewer = page.locator("graphfakos-viewer");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const minimap = page.locator("[data-gf-minimap]");
  const map = minimap.locator("[data-gf-minimap-map]");
  const footprint = minimap.locator("[data-gf-minimap-viewport]");
  const cameraTarget = minimap.locator("[data-gf-minimap-camera-target]");
  const cameraHeading = minimap.locator("[data-gf-minimap-camera-heading]");
  const focusBearing = minimap.locator("[data-gf-minimap-focus-bearing]");
  const focusBeacon = minimap.locator("[data-gf-minimap-focus-beacon]");
  await expect(minimap).toHaveAttribute("data-mode", "3d");
  await expect(minimap).toHaveAttribute("aria-label", /outlined footprint shows camera coverage.*Drag, click empty space, or use arrow keys/);
  await expect(minimap.locator("[data-gf-minimap-orientation]")).toHaveText(/-?\d+\u00b0 \u00b7 -?\d+\u00b0/);
  await expect.poll(() => map.locator("circle[data-layer]").count()).toBeGreaterThan(0);
  await expect(footprint).toBeVisible();
  await expect(cameraTarget).toBeVisible();
  expect(Number(await cameraHeading.getAttribute("y1")))
    .not.toBe(Number(await cameraHeading.getAttribute("y2")));
  await expect(focusBearing).toBeHidden();
  await expect(focusBeacon).toBeHidden();

  const minimapNode = map.locator("circle[data-layer]").first();
  const minimapNodeId = await minimapNode.getAttribute("data-minimap-node-id");
  await viewer.evaluate((element, nodeId) => {
    element.dispatch({ name: "select-node", target_id: nodeId });
  }, minimapNodeId);
  await expect(minimap).toHaveAttribute("data-has-focus", "true");
  await expect(minimapNode).toHaveAttribute("data-primary", "true");
  await expect(minimapNode).toHaveAttribute("data-selected", "true");
  await expect(focusBearing).toBeVisible();
  await expect(focusBeacon).toBeVisible();
  await expect(minimap).toHaveAttribute("aria-label", /focus beacon marks/);
  await expect.poll(async () => Math.hypot(
    Number(await focusBeacon.getAttribute("cx")) - Number(await minimapNode.getAttribute("cx")),
    Number(await focusBeacon.getAttribute("cy")) - Number(await minimapNode.getAttribute("cy")),
  )).toBeLessThan(0.2);
  const bearingStart = await focusBearing.evaluate((line) => ({
    x: Number(line.getAttribute("x1")),
    y: Number(line.getAttribute("y1")),
  }));
  await map.evaluate((svg) => {
    const rect = svg.getBoundingClientRect();
    svg.dispatchEvent(new MouseEvent("click", {
      bubbles: true,
      clientX: rect.right - 3,
      clientY: rect.top + 3,
    }));
  });
  await expect.poll(async () => Math.hypot(
    Number(await focusBearing.getAttribute("x1")) - bearingStart.x,
    Number(await focusBearing.getAttribute("y1")) - bearingStart.y,
  )).toBeGreaterThan(4);
  await expect(focusBeacon).toBeVisible();
  await viewer.evaluate((element) => element.dispatch({ name: "clear-selection" }));
  await expect(minimap).toHaveAttribute("data-has-focus", "false");
  await expect(focusBearing).toBeHidden();
  await expect(focusBeacon).toBeHidden();

  const targetBeforeMapMove = await cameraTarget.evaluate((node) => ({
    x: Number(node.getAttribute("cx")),
    y: Number(node.getAttribute("cy")),
  }));

  const before = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await map.evaluate((svg) => {
    const rect = svg.getBoundingClientRect();
    svg.dispatchEvent(new MouseEvent("click", {
      bubbles: true,
      clientX: rect.left + 2,
      clientY: rect.bottom - 2,
    }));
  });
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return Math.hypot(
      camera.target.x - before.target.x,
      camera.target.y - before.target.y,
      camera.target.z - before.target.z,
    );
  }).toBeGreaterThan(10);
  await expect.poll(async () => {
    const next = await cameraTarget.evaluate((node) => ({
      x: Number(node.getAttribute("cx")),
      y: Number(node.getAttribute("cy")),
    }));
    return Math.hypot(next.x - targetBeforeMapMove.x, next.y - targetBeforeMapMove.y);
  }).toBeGreaterThan(4);
  const beforeDistance = Math.hypot(...["x", "y", "z"].map((axis) => (
    before.position[axis] - before.target[axis]
  )));
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    const distance = Math.hypot(...["x", "y", "z"].map((axis) => (
      camera.position[axis] - camera.target[axis]
    )));
    return Math.abs(distance - beforeDistance);
  }).toBeLessThan(1);
  const after = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  const afterOffset = ["x", "y", "z"].map((axis) => after.position[axis] - after.target[axis]);
  expect(Math.hypot(...afterOffset)).toBeCloseTo(beforeDistance, 0);

  const mapBox = await map.boundingBox();
  const beforeDrag = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await page.mouse.move(mapBox.x + mapBox.width * 0.25, mapBox.y + mapBox.height * 0.25);
  await page.mouse.down();
  await page.mouse.move(mapBox.x + mapBox.width * 0.75, mapBox.y + mapBox.height * 0.72, { steps: 8 });
  await page.mouse.up();
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return Math.hypot(...["x", "y", "z"].map((axis) => camera.target[axis] - beforeDrag.target[axis]));
  }).toBeGreaterThan(10);
  await expect(map).toHaveAttribute("data-dragging", "false");

  await map.focus();
  const beforeKeyboard = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await map.press("ArrowRight");
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return Math.abs(camera.target.x - beforeKeyboard.target.x);
  }).toBeGreaterThan(5);
  const afterFirstKeyboard = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await map.press("ArrowRight");
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return Math.abs(camera.target.x - afterFirstKeyboard.target.x);
  }).toBeGreaterThan(5);

  const footprintWidth = Number(await footprint.getAttribute("width"));
  const zoomIn = page.getByRole("button", { name: "Zoom in" });
  for (let index = 0; index < 4; index += 1) await zoomIn.click();
  await expect.poll(async () => Number(await footprint.getAttribute("width")))
    .toBeLessThan(footprintWidth - 2);

  const surface = page.locator(".gf-webgl-surface canvas");
  const surfaceBox = await surface.boundingBox();
  const headingBeforeOrbit = await cameraHeading.getAttribute("x2");
  await page.mouse.move(surfaceBox.x + surfaceBox.width * 0.5, surfaceBox.y + surfaceBox.height * 0.5);
  await page.mouse.down();
  await page.mouse.move(surfaceBox.x + surfaceBox.width * 0.62, surfaceBox.y + surfaceBox.height * 0.44, { steps: 8 });
  await page.mouse.up();
  await expect.poll(() => minimap.locator("[data-gf-minimap-orientation]").textContent())
    .not.toBe("0\u00b0 \u00b7 0\u00b0");
  await expect.poll(() => cameraHeading.getAttribute("x2")).not.toBe(headingBeforeOrbit);
});

test("keeps 3D camera markers out of the SVG overview map", async ({ page }) => {
  await page.goto("/explore?render_engine=svg");
  const minimap = page.locator("[data-gf-minimap]");
  await expect(minimap).not.toHaveAttribute("data-mode", "3d");
  await expect(minimap.locator("[data-gf-minimap-viewport]")).toBeVisible();
  await expect(minimap.locator("[data-gf-minimap-camera-heading]")).toBeHidden();
  await expect(minimap.locator("[data-gf-minimap-camera-target]")).toBeHidden();
  await expect(minimap.locator("[data-gf-minimap-focus-bearing]")).toBeHidden();
  await expect(minimap.locator("[data-gf-minimap-focus-beacon]")).toBeHidden();
});

test("falls back to the structured SVG scene when WebGL is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function patched(type, ...args) {
      if (String(type).startsWith("webgl")) return null;
      return original.call(this, type, ...args);
    };
  });
  await page.goto("/explore");
  const graph = page.locator(".gf-canvas-shell");
  await expect(graph).toHaveAttribute("data-webgl-fallback", "true");
  await expect(page.locator(".gf-canvas")).toBeVisible();
  await expect(page.getByRole("img", { name: "GraphFakos graph canvas" })).toBeVisible();
});

test("preserves selection and reversible scene changes", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const state = await page.locator("graphfakos-viewer").evaluate((viewer) => {
    viewer.dispatch({ name: "select-node", target_id: "provider:cluster-1" });
    viewer.dispatch({ name: "pin-node", target_id: "provider:cluster-1", payload: { x: 120, y: 80 } });
    viewer.dispatch({ name: "undo" });
    const undone = viewer.getState();
    viewer.dispatch({ name: "redo" });
    return { undone, redone: viewer.getState() };
  });
  expect(state.undone.selected_node_id).toBe("provider:cluster-1");
  expect(state.undone.pinned_positions["provider:cluster-1"]).toBeUndefined();
  expect(state.redone.pinned_positions["provider:cluster-1"]).toEqual([120, 80]);
  const layout = page.getByRole("button", { name: "Reset graph formation" });
  await expect(layout).toBeEnabled();
  await layout.click();
  await page.locator(".gf-canvas-shell").press("ControlOrMeta+z");
});

test("keeps Obsidian-style display controls on the graph surface", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const display = page.locator("[data-gf-display-dock]");
  await expect(display).toBeVisible();
  await display.locator(":scope > summary").click();

  const nodeScale = display.locator("[data-gf-scene-control='node_scale']");
  await nodeScale.press("ArrowLeft");
  await display.locator("[data-gf-scene-level='cluster']").click();

  const state = await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState());
  expect(state.node_scale).toBeLessThan(1);
  expect(state.scene_level).toBe("cluster");
  await expect(display.locator("[data-gf-scene-level='cluster']")).toHaveAttribute("data-active", "true");
});

test("runs graph operating dock controls without leaving the canvas", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await expect(page.locator("[data-gf-operating-dock]")).toBeVisible();

  const viewer = page.locator("graphfakos-viewer");
  await page.locator("[data-gf-edge-mode='focus']").click();
  await expect.poll(() => viewer.evaluate((element) => element.getState().edge_clutter))
    .toBe("focus");
  await expect(page.locator("[data-gf-edge-mode='focus']")).toHaveAttribute("data-active", "true");

  await page.locator("[data-gf-workbook-name]").first().fill("Focus pass");
  await page.locator("[data-gf-workbook-action='save']").first().click();
  await expect(page.locator("[data-gf-workbook-status]").first()).toContainText("Saved local slot");
  await expect(page.locator("[data-gf-workbook-list]").first()).toContainText("Focus pass");

  const localRoute = await page.locator("[data-gf-expand-neighborhood]").first().getAttribute("href");
  expect(localRoute).toContain("/neighborhood?");
  expect(localRoute).toContain("max_depth=1");
  expect(await page.locator("[data-gf-search-jump]").count()).toBeGreaterThan(0);
});

test("runs selection, distribution, perspective, and import workflows", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.evaluate(() => localStorage.removeItem("graphfakos:viewer-perspectives:v1"));
  const viewer = page.locator("graphfakos-viewer");
  await viewer.evaluate((element) => element.dispatch({
    name: "select-node",
    target_id: "provider:cluster-1",
  }));

  await page.locator("[data-gf-selection-action='outgoing']").click();
  await expect.poll(() => viewer.evaluate(
    (element) => element.getState().selected_node_ids.length,
  )).toBeGreaterThan(1);

  await page.locator(".gf-workbench-tool").filter({ hasText: "Distributions" }).locator("summary").click();
  await page.locator("[data-gf-histogram='degree'] button:not([title^='0 '])").first().click();
  await expect.poll(() => viewer.evaluate(
    (element) => element.getState().selected_node_ids.length,
  )).toBeGreaterThan(0);
  await page.locator("[data-gf-selection-action='only']").click();
  await expect.poll(() => viewer.evaluate((element) => (
    element.graph.nodes.filter((node) => node.provider_payload?.viewer_hidden).length
  ))).toBeGreaterThan(0);

  await page.locator(".gf-workbench-tool").filter({ hasText: "Perspectives" }).locator("summary").click();
  await page.locator("[data-gf-perspective-save]").click();
  await expect(page.locator("[data-gf-local-perspectives] button")).toHaveText("View 1");
  await page.reload();
  await page.locator(".gf-workbench-tool").filter({ hasText: "Perspectives" }).locator("summary").click();
  await expect(page.locator("[data-gf-local-perspectives] button")).toHaveText("View 1");

  await page.locator(".gf-workbench-tool").filter({ hasText: "Open data" }).locator("summary").click();
  const importResponse = page.waitForResponse((response) => response.url().endsWith("/api/import"));
  await page.locator("[data-gf-import-form] input[type='file']").setInputFiles(
    "fixtures/viewer-scale-1000.json",
  );
  await page.locator("[data-gf-import-form] button[type='submit']").click();
  const response = await importResponse;
  expect(response.ok()).toBe(true);
  expect((await response.json()).ok).toBe(true);
  await expect(page).toHaveURL(/\/explore/);
});

test("loads provider-backed details and reports live rendering performance", async ({ page }) => {
  await page.goto("/explore");
  const viewer = page.locator("graphfakos-viewer");
  await expect(viewer.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await viewer.evaluate((element) => element.dispatch({
    name: "select-node",
    target_id: "provider:cluster-1",
  }));

  const expansionResponse = page.waitForResponse((response) => response.url().endsWith("/api/expand"));
  await page.locator("[data-gf-selection-action='expand']").click();
  const response = await expansionResponse;
  expect(response.ok()).toBe(true);
  expect((await response.json()).ok).toBe(true);

  const performance = page.locator("[data-gf-performance-hud]");
  await performance.locator("summary").click();
  await expect.poll(async () => performance.locator("[data-gf-perf-fps]").textContent())
    .not.toBe("--");
  await expect(performance.locator("[data-gf-perf-detail]")).toHaveText(
    /overview|balanced|detail|precision/,
  );
});

test("preserves theme and group visibility across viewer routes", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const before = await page.locator("graphfakos-viewer").evaluate(async (viewer) => {
    viewer.dispatch({ name: "group-toggle", target_id: "provider" });
    viewer.focusNode("memory:c1-1");
    await new Promise((resolve) => window.setTimeout(resolve, 700));
    const trail = viewer.exportNavigationTrail();
    await viewer.navigate("/explore?layout=grouped&focus_node_id=artifact%3Ac1-3");
    return { camera: trail.current.camera, hiddenGroups: viewer.getState().hidden_groups };
  });
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.waitForTimeout(500);
  const after = await page.locator("graphfakos-viewer").evaluate((viewer) => ({
    state: viewer.getState(),
    camera: viewer.exportNavigationTrail().current.camera,
  }));

  expect(after.state.theme).toBe("space");
  expect(before.hiddenGroups).toContain("provider");
  expect(after.state.hidden_groups).toContain("provider");
  expect(after.state.selected_node_id).toBe("artifact:c1-3");
  expect(after.camera.mode).toBe("3d");
  expect(Math.abs(after.camera.position.x - before.camera.position.x)).toBeLessThan(1);
  expect(Math.abs(after.camera.position.y - before.camera.position.y)).toBeLessThan(1);
  expect(Math.abs(after.camera.position.z - before.camera.position.z)).toBeLessThan(1);
  await expect(page.locator("[data-gf-focus-history='back']")).toBeEnabled();
  await page.locator("[data-gf-focus-history='back']").click();
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState().selected_node_id))
    .toBe("memory:c1-1");
  await expect(page.locator("body")).toHaveAttribute("data-theme", "space");
});

test("restores exact graph scenes through browser back and forward", async ({ page }) => {
  await page.goto(
    "/explore?theme=space&render_engine=3d&layout=grouped"
      + "&focus_node_id=memory%3Ac1-1",
  );
  const viewer = page.locator("graphfakos-viewer");
  await expect(viewer.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await expect.poll(() => viewer.evaluate((element) => element.getState().selected_node_id))
    .toBe("memory:c1-1");
  await page.evaluate(() => { window.__graphfakosRouteMarker = "kept"; });

  await viewer.evaluate((element) => element.navigate(
    "/neighborhood?theme=space&render_engine=3d&layout=grouped"
      + "&focus_node_id=provider%3Acluster-1",
  ));
  await expect(page).toHaveURL(/\/neighborhood\?/);
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate(
    (element) => element.getState().selected_node_id,
  )).toBe("provider:cluster-1");

  await page.evaluate(() => window.history.back());
  await expect(page).toHaveURL(/\/explore\?/);
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate(
    (element) => element.getState().selected_node_id,
  )).toBe("memory:c1-1");
  expect(await page.evaluate(() => window.__graphfakosRouteMarker)).toBe("kept");

  await page.evaluate(() => window.history.forward());
  await expect(page).toHaveURL(/\/neighborhood\?/);
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate(
    (element) => element.getState().selected_node_id,
  )).toBe("provider:cluster-1");
  expect(await page.evaluate(() => window.__graphfakosRouteMarker)).toBe("kept");
});

test("keeps the newest scene when route responses arrive out of order", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const viewer = page.locator("graphfakos-viewer");
  await expect(viewer.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");

  await page.evaluate(() => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = (input, options) => {
      if (!String(input).includes("/neighborhood?")) return nativeFetch(input, options);
      return new Promise((resolve, reject) => {
        window.setTimeout(() => nativeFetch(input, options).then(resolve, reject), 350);
      });
    };
  });

  const results = await viewer.evaluate(async (element) => Promise.all([
    element.navigate(
      "/neighborhood?theme=space&render_engine=3d&focus_node_id=memory%3Ac1-1",
    ),
    element.navigate(
      "/path?theme=space&render_engine=3d&from_node_id=memory%3Ac1-1"
        + "&to_node_id=provider%3Acluster-1",
    ),
  ]));

  expect(results).toEqual([false, true]);
  await expect(page).toHaveURL(/\/path\?/);
  await expect(page.locator("[aria-label='Path controls']")).toBeVisible();
  await page.waitForTimeout(450);
  await expect(page).toHaveURL(/\/path\?/);
  await expect(page.locator("[aria-label='Path controls']")).toBeVisible();
});

test("restores an exact 3D camera pose from a durable route", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("memory:c1-1"));
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate((viewer) => (
    viewer.getState().camera_pose?.position?.z || null
  ))).not.toBeNull();
  await page.waitForTimeout(500);

  const saved = await page.locator("graphfakos-viewer").evaluate((viewer) => ({
    route: window.GraphFakosViewerRuntime.savedViewRoute(viewer.getState()),
    camera: viewer.exportNavigationTrail().current.camera,
  }));
  expect(saved.route).toContain("camera_pose=");

  await page.goto(saved.route);
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.waitForTimeout(600);
  const restored = await page.locator("graphfakos-viewer").evaluate((viewer) => ({
    state: viewer.getState(),
    camera: viewer.exportNavigationTrail().current.camera,
  }));

  expect(restored.camera.mode).toBe("3d");
  for (const axis of ["x", "y", "z"]) {
    expect(Math.abs(restored.camera.position[axis] - saved.camera.position[axis])).toBeLessThan(1);
    expect(Math.abs(restored.camera.target[axis] - saved.camera.target[axis])).toBeLessThan(1);
  }
  expect(restored.state.camera_pose).not.toBeNull();
  expect(restored.state.theme).toBe("space");
});

test("focuses hidden groups as navigable scene regions", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const result = await page.locator("graphfakos-viewer").evaluate((viewer) => {
    viewer.dispatch({ name: "group-toggle", target_id: "provider" });
    const hiddenBeforeFocus = viewer.getState().hidden_groups.includes("provider");
    const state = viewer.focusGroup("provider");
    const selectedKinds = state.selected_node_ids.map((nodeId) => (
      viewer.querySelector(`.gf-node[data-node-id="${CSS.escape(nodeId)}"]`)?.dataset.kind || ""
    ));
    return {
      hiddenBeforeFocus,
      hiddenAfterFocus: state.hidden_groups.includes("provider"),
      selectedNodeId: state.selected_node_id,
      selectedCount: state.selected_node_ids.length,
      selectedKinds,
      overlayOpen: viewer.querySelector("[data-gf-inspect-overlay]")?.dataset.open,
      theme: state.theme,
    };
  });

  expect(result.hiddenBeforeFocus).toBe(true);
  expect(result.hiddenAfterFocus).toBe(false);
  expect(result.selectedCount).toBeGreaterThan(0);
  expect(result.selectedNodeId).toBeTruthy();
  expect(result.selectedKinds.every((kind) => kind === "provider")).toBe(true);
  expect(result.overlayOpen).toBe("true");
  expect(result.theme).toBe("space");
});

test("exposes cluster focus and connected-node navigation", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");

  const card = page.locator("[data-gf-group-card='provider']");
  await expect(card).toBeVisible();
  await card.locator("[data-gf-group='provider']").click();
  await expect(card).toHaveAttribute("data-active", "false");
  await card.locator("[data-gf-group-focus='provider']").click();
  await expect(card).toHaveAttribute("data-active", "true");
  await expect(page.locator("[data-gf-inspect-overlay]")).toHaveAttribute("data-open", "true");

  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("provider:cluster-1"));
  const inspector = page.locator("[data-gf-inspect-overlay]");
  const contentSection = inspector.locator("[data-gf-inspect-content-section]");
  await expect(contentSection).not.toHaveAttribute("open", "");
  await expect(contentSection).toBeInViewport({ ratio: 0.5 });
  await expect(inspector.locator("[data-gf-inspect-neighbor-count]")).not.toHaveText("0");
  await expect(inspector.locator("[data-gf-neighbor-node]").first()).toBeVisible();
  await expect(inspector.locator("[data-gf-neighbor-node] em").first())
    .toContainText(/incoming|outgoing|both directions/);
  const stableRoute = (value) => {
    const url = new URL(value);
    ["camera_pose", "camera_yaw", "camera_pitch"].forEach((key) => url.searchParams.delete(key));
    return `${url.pathname}?${url.searchParams.toString()}`;
  };
  const routeBeforeCenter = stableRoute(page.url());
  await inspector.locator("[data-gf-overlay-action='center']").click();
  await expect(inspector).toHaveAttribute("data-open", "true");
  await expect(inspector).toHaveAttribute("data-last-command", "center");
  expect(stableRoute(page.url())).toBe(routeBeforeCenter);
  await expect.poll(async () => {
    const camera = await page.locator("graphfakos-viewer")
      .evaluate((viewer) => viewer.exportNavigationTrail().current.camera);
    return Math.hypot(
      camera.position.x - camera.target.x,
      camera.position.y - camera.target.y,
      camera.position.z - camera.target.z,
    );
  }).toBeGreaterThan(300);
  await page.locator(".gf-canvas-shell").press("j");
  const keyboardNeighbor = await page.evaluate(() => document.activeElement?.getAttribute("data-gf-neighbor-node"));
  expect(keyboardNeighbor).toBeTruthy();
  await expect(inspector.locator(`[data-gf-neighbor-node='${keyboardNeighbor}']`))
    .toHaveAttribute("data-previewed", "true");
  await expect(page.locator(`.gf-node[data-node-id='${keyboardNeighbor}']`))
    .toHaveAttribute("data-previewed", "true");
  await expect(page.locator(`.gf-webgl-label[data-node-id='${keyboardNeighbor}']`))
    .toHaveAttribute("data-previewed", "true");
  await expect.poll(() => page.locator(".gf-edge[data-previewed='true']").count()).toBeGreaterThan(0);
  expect(await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState().selected_node_id))
    .toBe("provider:cluster-1");

  await page.keyboard.press("j");
  const nextKeyboardNeighbor = await page.evaluate(() => document.activeElement?.getAttribute("data-gf-neighbor-node"));
  expect(nextKeyboardNeighbor).toBeTruthy();
  expect(nextKeyboardNeighbor).not.toBe(keyboardNeighbor);
  await page.keyboard.press("k");
  expect(await page.evaluate(() => document.activeElement?.getAttribute("data-gf-neighbor-node")))
    .toBe(keyboardNeighbor);
  await page.keyboard.press("Enter");
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState().selected_node_id))
    .toBe(keyboardNeighbor);
  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("provider:cluster-1"));
  await page.locator("[data-gf-inspect-overlay]").evaluate((overlay) => { overlay.scrollTop = 200; });
  const neighbor = page.locator("[data-gf-neighbor-node='memory:c1-1']");
  await expect(neighbor).toBeVisible();
  await neighbor.click();
  const state = await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState());
  expect(state.selected_node_id).toBe("memory:c1-1");
  await expect(page.locator("[data-gf-inspect-overlay]")).toHaveAttribute("data-node-id", "memory:c1-1");
  expect(await page.locator("[data-gf-inspect-overlay]").evaluate((overlay) => overlay.scrollTop)).toBe(0);
  const fitState = await page.locator("graphfakos-viewer").evaluate((viewer) => {
    viewer.fitVisible();
    return viewer.getState();
  });
  expect(fitState.selected_node_id).toBe("memory:c1-1");

  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("provider:cluster-1"));
  await expect(page.locator("[data-gf-focus-history='back']")).toBeEnabled();
  await page.locator("[data-gf-focus-history='back']").click();
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState().selected_node_id))
    .toBe("memory:c1-1");
  await expect(page.locator("[data-gf-focus-history='forward']")).toBeEnabled();
  await page.locator(".gf-canvas-shell").press("]");
  await expect.poll(() => page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState().selected_node_id))
    .toBe("provider:cluster-1");
});

test("previews and commits screen-direction node travel", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const viewer = page.locator("graphfakos-viewer");
  const shell = page.locator(".gf-canvas-shell");
  await expect(shell).toHaveAttribute("data-webgl-ready", "true");
  await viewer.evaluate((element) => element.focusNode("provider:cluster-1"));
  await shell.focus();

  const candidate = await viewer.evaluate((element) => {
    for (const direction of ["right", "left", "down", "up"]) {
      const nodeId = element.stepSpatialNode(direction);
      if (nodeId) return { direction, nodeId };
    }
    return null;
  });
  expect(candidate).not.toBeNull();
  await shell.press("Escape");
  const key = `Alt+Arrow${candidate.direction[0].toUpperCase()}${candidate.direction.slice(1)}`;
  await shell.press(key);

  await expect(page.locator(`.gf-webgl-label[data-node-id='${candidate.nodeId}']`))
    .toHaveAttribute("data-previewed", "true");
  await expect(page.locator(`.gf-node[data-node-id='${candidate.nodeId}']`))
    .toHaveAttribute("data-previewed", "true");
  await expect(page.locator("[data-gf-live-selection]"))
    .toContainText("Enter to focus; Escape to cancel");
  await expect.poll(() => page.locator(".gf-edge[data-previewed='true']").count()).toBeGreaterThan(0);
  expect(await viewer.evaluate((element) => element.getState().selected_node_id)).toBe("provider:cluster-1");

  await shell.press("Enter");
  await expect.poll(() => viewer.evaluate((element) => element.getState().selected_node_id))
    .toBe(candidate.nodeId);
  await expect(page.locator("[data-gf-live-selection]"))
    .not.toHaveAttribute("data-previewed-node-id");
});

test("moves the live 3D camera from keyboard and toolbar controls", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const viewer = page.locator("graphfakos-viewer");
  const shell = page.locator(".gf-canvas-shell");
  await expect(shell).toHaveAttribute("data-webgl-ready", "true");
  await shell.focus();

  const before = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await shell.press("d");
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return Math.hypot(
      camera.target.x - before.target.x,
      camera.target.y - before.target.y,
      camera.target.z - before.target.z,
    );
  }).toBeGreaterThan(1);

  const beforeOrbit = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await shell.press("q");
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return Math.abs(camera.yaw - beforeOrbit.yaw);
  }).toBeGreaterThan(4);

  const beforeZoom = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
  await page.getByRole("button", { name: "Zoom in" }).click();
  await expect.poll(async () => {
    const camera = await viewer.evaluate((element) => element.exportNavigationTrail().current.camera);
    return beforeZoom.distance - camera.distance;
  }).toBeGreaterThan(1);
  await expect.poll(() => viewer.evaluate((element) => element.getState().camera_pose)).not.toBeNull();
  await expect.poll(() => page.url()).toContain("camera_pose=");
});

test("keeps focus and fits a fresh camera when entering a local lens", async ({ page }) => {
  await page.goto(
    "/explore?theme=space&render_engine=3d&layout=grouped"
      + "&camera_pose=0%2C0%2C10000%2C0%2C0%2C0",
  );
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.focusNode("provider:cluster-1"));

  const inspector = page.locator("[data-gf-inspect-overlay]");
  const local = inspector.locator("[data-gf-overlay-action='local']");
  await expect(local).toHaveAttribute("data-route", /camera_scope=fresh/);
  await local.click();

  await expect(page).toHaveURL(/\/neighborhood\?/);
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await expect(inspector).toHaveAttribute("data-open", "true");
  await expect(inspector).toHaveAttribute("data-node-id", "provider:cluster-1");
  const state = await page.locator("graphfakos-viewer").evaluate((viewer) => viewer.getState());
  expect(state.selected_node_id).toBe("provider:cluster-1");
  expect(state.selected_node_ids).toContain("provider:cluster-1");
  expect(page.url()).not.toContain("camera_scope=");
  expect(Math.abs(state.camera_pose.position.z - 10000)).toBeGreaterThan(100);

  const canvasBox = await page.locator(".gf-canvas-shell").boundingBox();
  expect(canvasBox.y).toBeLessThan(180);
  await expect(page.locator("[data-gf-context-drawer]")).not.toHaveAttribute("open", "");
  const searchDock = page.locator("[data-gf-command-dock]");
  await expect(searchDock).not.toHaveAttribute("open", "");
  await page.locator(".gf-canvas-shell").press("/");
  await expect(searchDock).toHaveAttribute("open", "");
  await expect(page.locator("[data-gf-command-search]")).toBeFocused();
});

test("keeps recent graph locations visible and directly navigable", async ({ page }) => {
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");

  const viewer = page.locator("graphfakos-viewer");
  const trail = page.locator("[data-gf-spatial-trail]");
  await expect(trail).toBeHidden();
  await viewer.evaluate((element) => element.focusNode("memory:c1-1"));
  await viewer.evaluate((element) => element.focusNode("provider:cluster-1"));

  await expect(trail).toBeVisible();
  await expect(trail.locator("[aria-current='location']")).toContainText("Provider Cluster 1");
  await expect(page.locator("[data-gf-focus-history='back']"))
    .toHaveAttribute("title", "Previous focus: Memory C1.1");
  await trail.locator("[data-gf-spatial-index]:not([aria-current])").last().click();
  await expect.poll(() => viewer.evaluate((element) => element.getState().selected_node_id))
    .toBe("memory:c1-1");

  await trail.locator("[data-gf-spatial-root]").click();
  await expect.poll(() => viewer.evaluate((element) => element.getState().selected_node_id))
    .toBeNull();
  await expect(trail).toBeHidden();
  await expect(page.locator("[data-gf-focus-history='forward']"))
    .toHaveAttribute("title", "Next focus: Memory C1.1");
});

test("opens editable content in the graph inspector", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  await page.locator("graphfakos-viewer").evaluate((viewer) => {
    const node = viewer.querySelector(".gf-node");
    viewer.dispatch({ name: "select-node", target_id: node.dataset.nodeId });
    window.GraphFakosViewerRuntime.openInspectOverlay(viewer, node);
  });

  const overlay = page.locator("[data-gf-inspect-overlay]");
  await expect(overlay).toHaveAttribute("data-open", "true");
  await overlay.locator("[data-gf-inspect-content-section] summary").click();
  await expect(overlay.locator("[data-gf-inspect-content-section]")).toHaveAttribute("open", "");
  await expect(overlay.locator("[data-gf-inspect-title-input]")).toBeVisible();
  await expect(overlay.locator("[data-gf-inspect-title-input]")).toHaveValue(/.+/);
  await expect(overlay.locator("[data-gf-inspect-content-input]")).toHaveValue(/.+/);
});

test("applies live patches without replacing viewer state", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const result = await page.locator("graphfakos-viewer").evaluate((viewer) => {
    viewer.state = {
      ...viewer.getState(),
      camera_x: 18,
      camera_y: -6,
      camera_zoom: 1.4,
      filters: { kind: "provider" },
      live_revision: "0",
    };
    const sourceId = viewer.graph.nodes[0].id;
    const applied = viewer.applyLivePatch({
      patch_id: "browser-patch-1",
      base_revision: { value: "0" },
      result_revision: { value: "1" },
      cursor: { value: "browser-cursor-1" },
      operations: [
        { kind: "node_upsert", node: { id: "live:new", label: "Live node", kind: "provider" } },
        { kind: "edge_upsert", edge: { id: "live:edge", source_id: sourceId, target_id: "live:new", kind: "updated" } },
      ],
    });
    return {
      applied: applied.applied,
      nodeIds: viewer.graph.nodes.map((node) => node.id),
      edgeIds: viewer.graph.edges.map((edge) => edge.id),
      state: viewer.getState(),
      liveStatus: viewer.dataset.liveStatus,
    };
  });

  expect(result.applied).toBe(true);
  expect(result.nodeIds).toContain("live:new");
  expect(result.edgeIds).toContain("live:edge");
  expect(result.state.camera_x).toBe(18);
  expect(result.state.filters).toEqual({ kind: "provider" });
  expect(result.state.live_revision).toBe("1");
  expect(result.liveStatus).toBe("live");
  await expect(page.locator("[data-gf-live-status]")).toContainText("Live graph is current");
});

test("keeps the graph primary on the narrow responsive shell", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/explore");
  const graph = page.locator(".gf-canvas-shell");
  await expect(graph).toBeVisible();
  const box = await graph.boundingBox();
  expect(box.width).toBeGreaterThan(700);
  expect(box.height).toBeGreaterThan(500);
  const targets = await page.locator(".gf-canvas-tools").evaluate((root) => {
    const items = [...root.querySelectorAll("button, a")];
    return items.map((item) => {
      const rect = item.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    });
  });
  expect(targets.every((target) => target.width >= 24 && target.height >= 24)).toBe(true);
  await page.screenshot({ path: "test-results/graphfakos-3d-768x1024.png", fullPage: false });
});

test("keeps mobile navigation compact until requested", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 860 });
  await page.goto("/explore?theme=space&render_engine=3d&layout=grouped");
  const shell = page.locator(".gf-shell");
  const nav = page.locator(".gf-nav");
  const toggle = page.getByRole("button", { name: "Toggle navigation" });
  const menu = page.locator("[data-gf-nav-menu]");
  await expect(shell).toHaveAttribute("data-nav-collapsed", "true");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(menu).toBeHidden();
  expect((await nav.boundingBox()).height).toBeLessThan(64);
  expect((await page.locator(".gf-canvas-shell").boundingBox()).y).toBeLessThan(450);
  expect(await page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(await page.evaluate(() => document.documentElement.clientWidth));

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(menu).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 500));
  expect((await nav.boundingBox()).y).toBeLessThanOrEqual(1);
  await toggle.press("Escape");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(toggle).toBeFocused();

  await page.setViewportSize({ width: 1024, height: 860 });
  await expect(shell).toHaveAttribute("data-nav-collapsed", "false");
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(menu).toBeVisible();
});

test("has no critical automated accessibility violations", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.locator(".gf-canvas-shell")).toHaveAttribute("data-webgl-ready", "true");
  const results = await new AxeBuilder({ page }).analyze();
  const critical = results.violations.filter((violation) => violation.impact === "critical");
  expect(critical).toEqual([]);
});

for (const fixture of [
  {
    label: "200K",
    url: "http://127.0.0.1:8794/explore",
    total: "200000",
    maxFirstSceneMs: 12_000,
  },
  {
    label: "1M",
    url: "http://127.0.0.1:8795/explore",
    total: "1000000",
    maxFirstSceneMs: 15_000,
  },
]) {
  test(`renders the ${fixture.label} provider envelope honestly`, async ({ page }, testInfo) => {
    const startedAt = Date.now();
    await page.goto(fixture.url);
    const graph = page.locator(".gf-canvas-shell");
    await expect(graph).toHaveAttribute("data-webgl-ready", "true", { timeout: 15_000 });
    await expect(graph).toHaveAttribute("data-total-nodes", fixture.total);
    const visible = Number(await graph.getAttribute("data-visible-nodes"));
    const firstSceneMs = Date.now() - startedAt;
    expect(visible).toBeLessThanOrEqual(240);
    expect(firstSceneMs).toBeLessThan(fixture.maxFirstSceneMs);
    const labels = await page.locator(".gf-webgl-label").count();
    expect(labels).toBeLessThanOrEqual(8);
    if (fixture.label === "1M") {
      await expect.poll(async () => Number(await graph.getAttribute("data-reference-distance")))
        .toBeGreaterThan(0);
      const referenceDistance = Number(await graph.getAttribute("data-reference-distance"));
      const zoomIn = page.getByRole("button", { name: "Zoom in" });
      await zoomIn.click();
      await zoomIn.click();
      await expect(graph).toHaveAttribute("data-detail-mode", "detail");
      expect(Number(await graph.getAttribute("data-reference-distance")))
        .toBeCloseTo(referenceDistance, 1);
      expect(await page.locator(".gf-webgl-label").count()).toBeGreaterThan(labels);
    }
    await testInfo.attach("performance", {
      body: JSON.stringify({
        fixture: fixture.label,
        viewport: "1280x720",
        firstSceneMs,
        totalNodes: Number(fixture.total),
        visibleNodes: visible,
        drawnNodes: visible,
        renderer: "3d-force-graph@1.80.0",
      }),
      contentType: "application/json",
    });
    await page.screenshot({
      path: `test-results/graphfakos-${fixture.label.toLowerCase()}-overview.png`,
      fullPage: false,
    });
  });
}

test("reveals more dense-scene context as the 3D camera approaches", async ({ page }) => {
  await page.goto("http://127.0.0.1:8794/explore");
  const graph = page.locator(".gf-canvas-shell");
  const viewer = page.locator("graphfakos-viewer");
  await expect(graph).toHaveAttribute("data-webgl-ready", "true", { timeout: 15_000 });
  await expect(graph).toHaveAttribute("data-detail-mode", "balanced");
  await expect.poll(async () => Number(await graph.getAttribute("data-reference-distance")))
    .toBeGreaterThan(0);
  const initialLabels = await page.locator(".gf-webgl-label").count();
  const initialDistance = await viewer.evaluate(
    (element) => element.exportNavigationTrail().current.camera.distance,
  );
  const referenceDistance = Number(await graph.getAttribute("data-reference-distance"));
  expect(initialLabels).toBeLessThanOrEqual(8);

  const zoomIn = page.getByRole("button", { name: "Zoom in" });
  await zoomIn.click();
  await zoomIn.click();
  await expect(graph).toHaveAttribute("data-detail-mode", "detail");
  await expect.poll(() => viewer.evaluate(
    (element) => element.exportNavigationTrail().current.camera.distance,
  )).toBeLessThan(initialDistance * 0.8);
  expect(await page.locator(".gf-webgl-label").count()).toBeGreaterThan(initialLabels);
  expect(Number(await graph.getAttribute("data-semantic-zoom"))).toBeGreaterThan(1.3);
  expect(Number(await graph.getAttribute("data-camera-distance")))
    .toBeLessThan(Number(await graph.getAttribute("data-reference-distance")) * 0.8);
  await page.waitForTimeout(900);
  await expect(graph).toHaveAttribute("data-detail-mode", "detail");
  expect(Number(await graph.getAttribute("data-reference-distance"))).toBeCloseTo(referenceDistance, 1);
  expect(Number(await graph.getAttribute("data-semantic-zoom"))).toBeGreaterThan(1.3);
  expect(await page.locator(".gf-webgl-label").count()).toBeGreaterThan(initialLabels);
});

test.describe("JavaScript-disabled fallback", () => {
  test.use({ javaScriptEnabled: false });

  test("keeps linked SVG and route controls available", async ({ page }) => {
    await page.goto("/explore");
    await expect(page.getByRole("img", { name: "GraphFakos graph canvas" })).toBeVisible();
    await expect(page.locator("noscript .gf-note")).toBeVisible();
    await expect(page.getByRole("link", { name: "Explore" })).toBeVisible();
  });
});
