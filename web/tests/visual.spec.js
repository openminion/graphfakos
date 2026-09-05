import { expect, test } from "@playwright/test";
import { testServerUrl } from "./server-routes.js";

const visualRoutes = [
  {
    name: "dense demo space",
    url: testServerUrl(
      "dense",
      "/explore",
      "theme=space&render_engine=3d&layout=grouped&render_limit=240",
    ),
    path: "test-results/visual-dense-demo-space.png",
    minimumRawNodes: 36,
    maximumLabels: 28,
    theme: "space",
  },
  {
    name: "dense demo light",
    url: testServerUrl(
      "dense",
      "/explore",
      "theme=default&render_engine=3d&layout=grouped&render_limit=240",
    ),
    path: "test-results/visual-dense-demo-light.png",
    minimumRawNodes: 36,
    maximumLabels: 28,
    theme: "default",
  },
  {
    name: "200k islands space",
    url: testServerUrl(
      "scale200k",
      "/explore",
      "theme=space&render_engine=3d&layout=islands&render_limit=240",
    ),
    path: "test-results/visual-scale-200k-space.png",
    minimumRawNodes: 200000,
    maximumLabels: 24,
    minimumRegions: 12,
    minimumAggregateLinks: 200,
    theme: "space",
    timeout: 45_000,
  },
  {
    name: "1m islands space",
    url: testServerUrl(
      "scale1m",
      "/explore",
      "theme=space&render_engine=3d&layout=islands&render_limit=240",
    ),
    path: "test-results/visual-scale-1m-space.png",
    minimumRawNodes: 1000000,
    maximumLabels: 18,
    minimumRegions: 12,
    minimumAggregateLinks: 200,
    theme: "space",
    timeout: 60_000,
  },
];

test.describe("visual QA @visual", () => {
  for (const route of visualRoutes) {
    test(`captures ${route.name}`, async ({ page }, testInfo) => {
      test.setTimeout(route.timeout || 30_000);
      await page.goto(route.url);
      const shell = page.locator(".gf-canvas-shell");
      await expect(shell).toHaveAttribute("data-webgl-ready", "true", {
        timeout: 15_000,
      });
      await expect(page.locator("body")).toHaveAttribute("data-theme", route.theme);
      await expect(page.locator("[data-gf-performance-hud]")).toBeVisible();
      await expect(shell).toHaveAttribute("data-render-engine", "3d");
      await expect(shell).toHaveAttribute("data-webgl-fallback", "false");
      await expect(shell).toHaveAttribute("data-total-nodes", String(route.minimumRawNodes));
      await expect(shell).toHaveAttribute("data-detail-mode", /overview|balanced|detail|precision/);
      await expect(shell).toHaveAttribute("data-engine-settled", "true", {
        timeout: route.timeout || 30_000,
      });

      const canvasBox = await shell.boundingBox();
      expect(canvasBox).not.toBeNull();
      expect(canvasBox.width).toBeGreaterThan(900);
      expect(canvasBox.height).toBeGreaterThan(520);
      const coverage = Number(await shell.getAttribute("data-scene-coverage"));
      const occupancy = Number(await shell.getAttribute("data-scene-occupancy"));
      const visibleMarks = Number(await shell.getAttribute("data-visible-marks"));
      expect(coverage).toBeGreaterThanOrEqual(0.5);
      expect(coverage).toBeLessThanOrEqual(0.86);
      expect(occupancy).toBeGreaterThan(0.08);
      expect(visibleMarks).toBeGreaterThanOrEqual(Math.min(24, Number(await shell.getAttribute("data-visible-nodes"))));
      const visibleLabels = await page.locator(".gf-webgl-label[data-collided='false']").count();
      expect(visibleLabels).toBeLessThanOrEqual(route.maximumLabels);
      if (route.minimumRawNodes >= 200000) {
        await expect(page.locator(".gf-scene-status")).toContainText(/trimmed|of 200,000|of 1,000,000/);
        expect(Number(await shell.getAttribute("data-visible-regions")))
          .toBeGreaterThanOrEqual(route.minimumRegions);
        expect(Number(await shell.getAttribute("data-visible-aggregate-links")))
          .toBeGreaterThanOrEqual(route.minimumAggregateLinks);
        expect(Number(await shell.getAttribute("data-visible-landmarks"))).toBeGreaterThanOrEqual(8);
      }
      await page.screenshot({ path: route.path, fullPage: false });
      await testInfo.attach("visual-route", {
        body: JSON.stringify({
          name: route.name,
          url: route.url,
          screenshot: route.path,
        }),
        contentType: "application/json",
      });
    });
  }

  test("captures focused relationship context", async ({ page }) => {
    await page.goto(testServerUrl(
      "dense",
      "/explore",
      "theme=space&render_engine=3d&layout=grouped&render_limit=240",
    ));
    const shell = page.locator(".gf-canvas-shell");
    const viewer = page.locator("graphfakos-viewer");
    await expect(shell).toHaveAttribute("data-engine-settled", "true", { timeout: 30_000 });
    await viewer.evaluate((element) => element.focusNode("provider:cluster-1"));
    await expect(page.locator(
      ".gf-webgl-label[data-node-id='provider:cluster-1'][data-selected='true']",
    )).toBeVisible();
    await expect.poll(() => page.locator(".gf-webgl-label[data-related='true']").count())
      .toBeGreaterThan(0);
    await page.waitForTimeout(600);
    await page.screenshot({
      path: "test-results/visual-dense-focus-space.png",
      fullPage: false,
    });
  });

  test("captures searchable large-graph cluster navigation", async ({ page }) => {
    test.setTimeout(45_000);
    await page.goto(testServerUrl(
      "scale200k",
      "/explore",
      "theme=space&render_engine=3d&layout=islands&render_limit=240",
    ));
    const shell = page.locator(".gf-canvas-shell");
    const navigator = page.locator("[data-gf-cluster-navigator]");
    await expect(shell).toHaveAttribute("data-engine-settled", "true", { timeout: 30_000 });
    await navigator.locator("summary").click();
    await navigator.locator("[data-gf-cluster-search]").fill("Agent Runtime");
    await expect(navigator.locator("[data-gf-cluster-search-status]")).toContainText("of 200");
    const result = navigator.locator("[data-gf-group-card]:visible").first();
    await expect(result).toContainText("Agent Runtime");
    await result.locator("[data-gf-group-focus]").click();
    await expect(page.locator(".gf-webgl-label[data-selected='true']")).toBeVisible();
    await page.waitForTimeout(600);
    await page.screenshot({
      path: "test-results/visual-scale-200k-cluster-focus-space.png",
      fullPage: false,
    });
  });

  test("captures compact mobile graph surface", async ({ page }) => {
    await page.setViewportSize({ width: 430, height: 860 });
    await page.goto(testServerUrl(
      "dense",
      "/explore",
      "theme=space&render_engine=3d&layout=grouped&render_limit=240",
    ));
    const shell = page.locator(".gf-canvas-shell");
    await expect(shell).toHaveAttribute("data-webgl-ready", "true", { timeout: 15_000 });
    await expect(shell).toHaveAttribute("data-engine-settled", "true", { timeout: 30_000 });
    const canvasBox = await shell.boundingBox();
    expect(canvasBox.y).toBeLessThan(300);
    expect(canvasBox.width).toBeGreaterThan(390);
    await expect(page.locator("body")).toHaveAttribute("data-theme", "space");
    await page.screenshot({
      path: "test-results/visual-dense-mobile-space.png",
      fullPage: false,
    });
  });
});
