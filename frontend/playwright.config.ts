import { defineConfig } from "@playwright/test";

const externalBaseUrl = process.env.PLAYWRIGHT_BASE_URL;

export default defineConfig({
  testDir: "./tests/browser",
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 60_000 },
  use: {
    baseURL: externalBaseUrl || "http://127.0.0.1:3100",
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    launchOptions: { args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"] },
    permissions: ["camera"],
  },
  webServer: externalBaseUrl ? undefined : {
    command: "node node_modules/next/dist/bin/next dev --port 3100",
    env: { NEXT_DIST_DIR: ".next-remediation" },
    url: "http://127.0.0.1:3100",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
