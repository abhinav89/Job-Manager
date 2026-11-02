import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  use: { baseURL: "http://127.0.0.1:3220", viewport: { width: 1440, height: 900 } },
  webServer: {
    command: "python -m http.server 3220 --bind 127.0.0.1 --directory out",
    url: "http://127.0.0.1:3220",
    reuseExistingServer: false,
  },
});
