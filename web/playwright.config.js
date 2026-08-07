import { defineConfig } from "@playwright/test";
import { testServers } from "./tests/server-routes.js";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  workers: 1,
  use: {
    baseURL: testServers.dense.baseURL,
    browserName: process.env.GRAPHFAKOS_BROWSER || "chromium",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    viewport: { width: 1280, height: 720 },
  },
  webServer: [
    {
      command: `PYTHONPATH=../src ../.venv/bin/python -m graphfakos ui --demo-scenario dense --screen explore --render-engine 3d --theme space --layout grouped --render-limit 240 --serve --port ${testServers.dense.port}`,
      cwd: ".",
      port: testServers.dense.port,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: `PYTHONPATH=../src ../.venv/bin/python -m graphfakos ui --provider-envelope fixtures/viewer-scale-200000.json --screen explore --render-engine 3d --theme space --layout islands --render-limit 240 --serve --port ${testServers.scale200k.port}`,
      cwd: ".",
      port: testServers.scale200k.port,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: `PYTHONPATH=../src ../.venv/bin/python -m graphfakos ui --provider-envelope fixtures/viewer-scale-1000000.json --screen explore --render-engine 3d --theme space --layout islands --render-limit 240 --serve --port ${testServers.scale1m.port}`,
      cwd: ".",
      port: testServers.scale1m.port,
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
