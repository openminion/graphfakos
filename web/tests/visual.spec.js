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
      await expect(page.locator("body")).toHaveAttribute("data-theme", "space");
      await expect(page.locator("[data-gf-performance-hud]")).toBeVisible();
      await expect(shell).toHaveAttribute("data-render-engine", "3d");
      await expect(shell).toHaveAttribute("data-webgl-fallback", "false");
      await expect(shell).toHaveAttribute("data-total-nodes", String(route.minimumRawNodes));
      await expect(shell).toHaveAttribute("data-detail-mode", /overview|balanced|detail|precision/);

      const canvasBox = await shell.boundingBox();
      expect(canvasBox).not.toBeNull();
      expect(canvasBox.width).toBeGreaterThan(900);
      expect(canvasBox.height).toBeGreaterThan(520);
      const visibleLabels = await page.locator(".gf-webgl-label[data-collided='false']").count();
      expect(visibleLabels).toBeLessThanOrEqual(route.maximumLabels);
      if (route.minimumRawNodes >= 200000) {
        await expect(page.locator(".gf-scene-status")).toContainText(/trimmed|of 200,000|of 1,000,000/);
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
});
