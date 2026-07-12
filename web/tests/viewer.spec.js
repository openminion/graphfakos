import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

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
  await page.getByRole("button", { name: "Fit selected or visible graph" }).click();
  await page.getByRole("link", { name: "Light" }).click();
  await expect(page.locator("body")).toHaveAttribute("data-theme", "default");
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

test.describe("JavaScript-disabled fallback", () => {
  test.use({ javaScriptEnabled: false });

  test("keeps linked SVG and route controls available", async ({ page }) => {
    await page.goto("/explore");
    await expect(page.getByRole("img", { name: "GraphFakos graph canvas" })).toBeVisible();
    await expect(page.locator("noscript .gf-note")).toBeVisible();
    await expect(page.getByRole("link", { name: "Explore" })).toBeVisible();
  });
});
