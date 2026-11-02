import { test, expect } from "@playwright/test";

test("saved defaults survive reload and a scoped application keeps its own template", async ({ page, request }) => {
  const profile = { first_name: "Alex", last_name: "Example", mobile_no: "", email: "alex@example.com", education: [], experience: [], projects: [], skills: [], certifications: [], preset_slug: "blank" };
  const existing = await request.get("/api/profile/me");
  const currentProfile = existing.ok() ? await existing.json() : {};
  expect((await request.post("/api/profile/save", { data: { ...profile, revision: currentProfile.revision } })).ok()).toBe(true);
  const initial = await (await request.get("/api/preferences")).json();
  expect((await request.patch("/api/preferences", { data: { revision: initial.revision, resume_template: "modern", tracking_connection: { provider: "notion", config_path: null } } })).ok()).toBe(true);
  const job = await (await request.post("/api/tracker", { data: { company_name: "Preference Example", job_title: "Engineer", template_id: "compact" } })).json();

  await page.goto("/generate");
  await expect(page.getByRole("button", { name: "Modern resume preview Modern", exact: false })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Minimal resume preview Minimal", exact: false }).click();
  await page.getByRole("button", { name: "Save as my default", exact: true }).click();
  await expect(page.getByText("Default: Minimal", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Minimal resume preview Minimal", exact: false })).toHaveAttribute("aria-pressed", "true");
  const saved = await (await request.get("/api/preferences")).json();
  expect(saved.tracking_connection.provider).toBe("notion");
  await page.goto(`/generate?job_id=${job.id}`);
  await expect(page.getByRole("button", { name: "Compact resume preview Compact", exact: false })).toHaveAttribute("aria-pressed", "true");
  expect((await (await request.get(`/api/tracker/${job.id}/details`)).json()).template_id).toBe("compact");
  await page.goto("/tracker");
  await page.getByRole("button", { name: "Add Application", exact: true }).first().click();
  await expect(page.getByLabel("Resume Template", { exact: true })).toHaveValue("minimal");
});
