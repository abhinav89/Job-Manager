import { defineConfig } from "@playwright/test";

const externalBaseUrl = process.env.PLAYWRIGHT_BASE_URL;

export default defineConfig({
  testDir: "./tests/browser",
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 60_000 },
  use: {
    baseURL: externalBaseUrl || "http://127.0.0.1:3218",
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    launchOptions: { args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"] },
    permissions: ["camera"],
  },
  webServer: externalBaseUrl ? undefined : {
    command: "python tests/browser/server.py",
    url: "http://127.0.0.1:3218",
    reuseExistingServer: false,
    timeout: 180_000,
  },
});
