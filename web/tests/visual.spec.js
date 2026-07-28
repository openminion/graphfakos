import { expect, test } from "@playwright/test";

const visualRoutes = [
  {
    name: "dense demo space",
    url: "http://127.0.0.1:8793/explore?theme=space&render_engine=3d&layout=grouped&render_limit=240",
    path: "test-results/visual-dense-demo-space.png",
  },
  {
    name: "200k islands space",
    url: "http://127.0.0.1:8794/explore?theme=space&render_engine=3d&layout=islands&render_limit=240",
    path: "test-results/visual-scale-200k-space.png",
  },
  {
    name: "1m islands space",
    url: "http://127.0.0.1:8795/explore?theme=space&render_engine=3d&layout=islands&render_limit=240",
    path: "test-results/visual-scale-1m-space.png",
  },
];

test.describe("visual QA @visual", () => {
  for (const route of visualRoutes) {
    test(`captures ${route.name}`, async ({ page }, testInfo) => {
      await page.goto(route.url);
      const shell = page.locator(".gf-canvas-shell");
      await expect(shell).toHaveAttribute("data-webgl-ready", "true", {
        timeout: 15_000,
      });
      await expect(page.locator("body")).toHaveAttribute("data-theme", "space");
      await expect(page.locator("[data-gf-performance-hud]")).toBeVisible();

      const canvasBox = await shell.boundingBox();
      expect(canvasBox).not.toBeNull();
      expect(canvasBox.width).toBeGreaterThan(900);
      expect(canvasBox.height).toBeGreaterThan(520);
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
