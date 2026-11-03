import { expect, test } from "@playwright/test";

test("application flow uses real statuses, filters records, and includes archives on request", async ({ page, request }) => {
  const jobs = [];
  for (const [company, status, source] of [
    ["Flow Applied", "Applied", "Referral"], ["Flow Interview", "Interview", "OnlineJobs.ph"],
    ["Flow Saved", "Saved", ""], ["Flow Archive", "Rejected", "Referral"],
  ]) {
    const response = await request.post("/api/tracker", { data: { company_name: company, job_title: "Engineer", status, job_source: source } });
    expect(response.ok()).toBeTruthy();
    jobs.push(await response.json());
  }
  await request.patch(`/api/tracker/${jobs[3].id}`, { data: { revision: jobs[3].revision, is_archived: true } });
  await page.goto("/insights/");
  await expect(page.getByRole("heading", { name: "Where things stand." })).toBeVisible();
  const flow = page.getByRole("group", { name: "Application status flow" });
  const applied = flow.getByRole("button", { name: /^Applied:/ });
  await expect(applied).toBeVisible();
  await applied.click();
  const table = page.getByRole("table", { name: "Applications in the selected status" });
  await expect(table.getByText("Flow Applied", { exact: true })).toBeVisible();
  await expect(table.getByText("Flow Interview", { exact: true })).toHaveCount(0);
  await applied.press("Enter");
  await expect(table.getByText("Flow Interview", { exact: true })).toBeVisible();
  await expect(table.getByText("Flow Archive", { exact: true })).toHaveCount(0);
  await page.getByRole("checkbox", { name: "Include archived" }).check();
  await expect(table.getByText("Flow Archive", { exact: true })).toBeVisible();
  await page.getByRole("textbox", { name: "Search applications" }).fill("Flow Interview");
  await expect(table.getByRole("row")).toHaveCount(2);
  await page.getByRole("textbox", { name: "Search applications" }).clear();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download snapshot" }).click();
  expect((await download).suggestedFilename()).toMatch(/^application-insights-.*\.json$/);
  await page.locator("main").first().evaluate(element => element.scrollTo(0, 0));
  await page.screenshot({ path: "test-results/application-insights-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("heading", { name: "Where things stand." })).toBeVisible();
  await expect.poll(() => page.locator(".mobile-sidebar").evaluate(element => element.getBoundingClientRect().right)).toBeLessThanOrEqual(0);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.locator("main").first().evaluate(element => element.scrollTo(0, 0));
  await page.screenshot({ path: "test-results/application-insights-mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("button", { name: "Open Flow Interview in tracker", exact: true }).click();
  await expect(page).toHaveURL(/\/tracker\/?$/);
  await expect(page.locator(".tracker-job-card").filter({ hasText: "Flow Interview" }).getByRole("heading", { name: "Application documents" })).toBeVisible();
});

test("insights recovers from a failed request", async ({ page }) => {
  await page.route("**/api/tracker/insights?*", route => route.fulfill({ status: 503, json: { detail: "Workspace is busy. Try again." } }));
  await page.goto("/insights/");
  const error = page.getByRole("alert").filter({ hasText: "Workspace is busy" });
  await expect(error).toBeVisible();
  await page.unroute("**/api/tracker/insights?*");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Application flow", exact: true })).toBeVisible();
  await expect(error).toHaveCount(0);
});

test("an empty pipeline invites the user to add an application", async ({ page, request }) => {
  const current = await (await request.get("/api/tracker/insights")).json();
  await page.route("**/api/tracker/insights?*", route => route.fulfill({ json: {
    ...current, total: 0, awaiting_response: 0, interviewing: 0, offers: 0,
    applications: [], by_status: current.by_status.map((item: { status: string }) => ({ ...item, count: 0 })),
    follow_ups_due: [], by_source: [], archived_excluded: 0,
  } }));
  await page.goto("/insights/");
  await expect(page.getByText("Your pipeline starts with one application.")).toBeVisible();
  await expect(page.getByRole("group", { name: "Application status flow" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Open job tracker", exact: true })).toBeVisible();
});
