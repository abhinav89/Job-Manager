import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";

test("CLI preparation can be read, edited, reopened and versioned in the tracker", async ({ page, request }) => {
  const workspace = await (await request.get("/api/workspace")).json();
  const job = await (await request.post("/api/tracker", { data: { company_name: "Document test", job_title: "Integration Engineer" } })).json();
  const originals = new Map<string, number>();
  const items = [
    ["interview_plan", "interview plan"],
    ["cheat_sheet", "quick cheat sheet"],
    ["research", "company & role research"],
  ];
  for (const [kind] of items) {
    const payload: { content: string; sources?: { title: string; url: string }[] } = { content: `# ${kind}\n\nOriginal ${kind} notes.` };
    if (kind === "research") payload.sources = [{ title: "Official role", url: "https://example.com/job" }];
    const draft = JSON.parse(execFileSync("python", ["-m", "cv_tailor", "--data-dir", workspace.data_dir, "--json",
      "drafts", "import", "--kind", kind, "--application", String(job.id), "--input", "-"], {
      input: JSON.stringify(payload), encoding: "utf8",
    }));
    originals.set(kind, draft.id);
  }

  await page.goto("/tracker/");
  const card = page.locator(".tracker-job-card").filter({ hasText: "Document test" });
  await card.getByRole("button", { name: "Documents & details" }).click();
  await expect(card.getByText("3 saved documents")).toBeVisible();

  for (const [kind, label] of items) {
    await card.getByRole("button", { name: `Open ${label}`, exact: true }).click();
    await expect(card.getByText(`Original ${kind} notes.`, { exact: true })).toBeVisible();
    await card.getByRole("button", { name: "Edit document", exact: true }).click();
    await card.getByRole("textbox", { name: "Edit document" }).fill(`# ${kind}\n\nUpdated ${kind} notes.`);
    await card.getByRole("button", { name: "Save changes", exact: true }).click();
    await expect(card.getByText(`Updated ${kind} notes.`, { exact: true })).toBeVisible();
    await expect(card.getByRole("combobox", { name: "Document version" }).locator("option")).toHaveCount(2);
    await expect(card.getByText("3 saved documents")).toBeVisible();
    const original = JSON.parse(execFileSync("python", ["-m", "cv_tailor", "--data-dir", workspace.data_dir, "--json",
      "drafts", "get", String(originals.get(kind))], { encoding: "utf8" }));
    expect(original.content).toContain(`Original ${kind} notes.`);
  }

  await expect(card.getByRole("link", { name: "Official role", exact: true })).toHaveAttribute("href", "https://example.com/job");
  await page.screenshot({ path: "test-results/application-documents-desktop.png", fullPage: true });
  await page.reload();
  await card.getByRole("button", { name: "Documents & details" }).click();
  await card.getByRole("button", { name: "Open interview plan", exact: true }).click();
  await expect(card.getByText("Updated interview_plan notes.", { exact: true })).toBeVisible();
  const versions = card.getByRole("combobox", { name: "Document version" });
  const latestId = await versions.inputValue();
  await versions.selectOption(String(originals.get("interview_plan")));
  await expect(card.getByText("Original interview_plan notes.", { exact: true })).toBeVisible();
  await expect(card.getByRole("button", { name: "Edit document", exact: true })).toHaveCount(0);
  await versions.selectOption(latestId);

  await card.getByRole("button", { name: "Edit document", exact: true }).click();
  await card.getByRole("textbox", { name: "Edit document" }).fill("Unsaved changes survive a failed request.");
  await page.route(`**/api/tracker/${job.id}/documents/*/revise`, route => route.fulfill({ status: 500, contentType: "text/plain", body: "Internal Server Error" }));
  await card.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(card.getByRole("alert")).toBeVisible();
  await expect(card.getByRole("textbox", { name: "Edit document" })).toHaveValue("Unsaved changes survive a failed request.");
  await card.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(card.getByText("Updated interview_plan notes.", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.locator(".mobile-sidebar").evaluate(element => element.getBoundingClientRect().right)).toBeLessThanOrEqual(0);
  await card.getByRole("heading", { name: "Application documents", exact: true }).scrollIntoViewIfNeeded();
  await expect(card.getByRole("button", { name: "Edit document", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/application-documents-mobile.png", fullPage: true });
});

test("document loading can be retried and applications without preparation have an empty state", async ({ page, request }) => {
  const job = await (await request.post("/api/tracker", { data: { company_name: "No preparation yet", job_title: "Engineer" } })).json();
  await page.route(`**/api/tracker/${job.id}/documents`, route => route.fulfill({ status: 500, json: { detail: "Documents temporarily unavailable." } }));
  await page.goto("/tracker/");
  const card = page.locator(".tracker-job-card").filter({ hasText: "No preparation yet" });
  await card.getByRole("button", { name: "Documents & details" }).click();
  await expect(card.getByText("Documents temporarily unavailable.", { exact: true })).toBeVisible();
  await page.unroute(`**/api/tracker/${job.id}/documents`);
  await card.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(card.getByText("Interview plans, cheat sheets, and research saved for this application will appear here.")).toBeVisible();
});
