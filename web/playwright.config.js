import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:8793",
    browserName: process.env.GRAPHFAKOS_BROWSER || "chromium",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    viewport: { width: 1280, height: 720 },
  },
  webServer: [
    {
      command: "PYTHONPATH=../src ../.venv/bin/python -m graphfakos ui --demo-scenario dense --screen explore --render-engine 3d --theme space --layout grouped --render-limit 240 --serve --port 8793",
      cwd: ".",
      port: 8793,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "PYTHONPATH=../src ../.venv/bin/python -m graphfakos ui --provider-envelope fixtures/viewer-scale-200000.json --screen explore --render-engine 3d --theme space --layout islands --render-limit 240 --serve --port 8794",
      cwd: ".",
      port: 8794,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "PYTHONPATH=../src ../.venv/bin/python -m graphfakos ui --provider-envelope fixtures/viewer-scale-1000000.json --screen explore --render-engine 3d --theme space --layout islands --render-limit 240 --serve --port 8795",
      cwd: ".",
      port: 8795,
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
