import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { inspectApplicationForm } from "../../../.agents/skills/cv-apply/scripts/inspect-form.mjs";

const html = readFileSync(resolve("tests/browser/fixtures/application-form.html"), "utf8");

test.beforeEach(async ({ page }) => {
  await page.route("**/mock-ats", route => route.fulfill({ contentType: "text/html", body: html }));
  await page.goto("/mock-ats");
});

test("inventory distinguishes repeated entries, selected state and live limits without changing the form", async ({ page }) => {
  const data = await page.evaluate(inspectApplicationForm, "Experience step");
  const descriptions = data.fields.filter(f => f.label.includes("Role description"));
  expect(descriptions).toHaveLength(2);
  expect(new Set(descriptions.map(f => f.key)).size).toBe(2);
  expect(descriptions.every(f => f.required)).toBe(true);
  expect(data.fields.find(f => f.label === "Why this role?")?.limit?.maximum).toBe(12);
  expect(data.fields.find(f => f.label === "Project")?.limit?.unit).toBe("words");
  expect(data.fields.find(f => f.label === "I consent")?.observed_value).toBe(false);
  expect(data.fields.find(f => f.label === "Custom country")?.observation).toBe("unreadable");
  expect(data.fields.some(f => f.label === "Visa details")).toBe(false);
  const assessment = JSON.parse(execFileSync("python", ["-c", `import json,sys
from cv_tailor.models.application_form import ApplicationFormContent
from cv_tailor.services.application_forms import assess_form
print(json.dumps(assess_form(ApplicationFormContent.model_validate(json.load(sys.stdin)))))`], {
    cwd: resolve(".."), encoding: "utf8", env: { ...process.env, PYTHONPATH: resolve("../ai-service") },
    input: JSON.stringify({ session_id: "a".repeat(32), application_id: 1, application_revision: 1, profile_revision: 1,
      company_name: "Acme", job_title: "Engineer", form_url: data.form_url, posting_status: "active", identity_confirmed: true,
      inventory_complete: true, all_steps_complete: true, fields: data.fields }),
  }));
  expect(assessment.ready_for_review).toBe(false);
  expect(assessment.issues.some((issue: { code: string }) => issue.code === "required_empty")).toBe(true);
  await expect(page.getByLabel("Name", { exact: true })).toHaveValue("Alex");
  await expect(page.locator("body")).not.toHaveAttribute("data-submitted", "yes");
});

test("fresh inspection detects conditional requirements and newly added experience", async ({ page }) => {
  await page.getByLabel("Need sponsorship?").selectOption("yes");
  await page.getByRole("button", { name: "Add experience" }).click();
  const data = await page.evaluate(inspectApplicationForm, "Experience step");
  expect(data.fields.find(f => f.label === "Visa details")?.required).toBe(true);
  expect(data.fields.filter(f => f.label.includes("Role description"))).toHaveLength(3);
  const selected = data.fields.find(f => f.label === "Need sponsorship?");
  expect(selected?.observed_value).toBe("Yes");
  expect(selected?.options).toEqual(["Yes", "No"]);
});

test("readback exposes truncation, exact radio choices and uploaded file fingerprint", async ({ page }) => {
  const intended = "A much longer motivation than the field allows";
  await page.getByLabel("Why this role?").fill(intended);
  await page.getByLabel("Email", { exact: true }).fill("not-an-email");
  await page.getByLabel("Hybrid", { exact: true }).check();
  const bytes = Buffer.from("test resume bytes");
  await page.getByLabel("Resume", { exact: true }).setInputFiles({ name: "resume-7.pdf", mimeType: "application/pdf", buffer: bytes });
  const data = await page.evaluate(inspectApplicationForm, "Application");
  expect(data.fields.find(f => f.label === "Why this role?")?.observed_value).not.toBe(intended);
  expect(data.fields.find(f => f.label === "Email")?.validation_errors).toHaveLength(1);
  expect(data.fields.find(f => f.kind === "radio")?.observed_value).toBe("Hybrid");
  expect(data.fields.find(f => f.kind === "file")?.observed_files).toEqual([
    { filename: "resume-7.pdf", size: bytes.length, sha256: createHash("sha256").update(bytes).digest("hex") },
  ]);
  await expect(page.locator("body")).not.toHaveAttribute("data-submitted", "yes");
});

test("dashboard handoff requires an application and carries the form workflow", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const data = path === "/api/workspace" ? { data_dir: "C:\\Career workspace", ai: { mode: "external" } } :
      path === "/api/tracker" ? [{ id: 42, company_name: "Acme", job_title: "Engineer", status: "Saved" }] : [];
    await route.fulfill({ json: data });
  });
  await page.goto("/assistant");
  await page.getByText("Work with your CLI agent", { exact: false }).click();
  await page.getByLabel("Agent task").selectOption("application_form");
  await expect(page.getByRole("button", { name: "Copy agent prompt" })).toBeDisabled();
  await page.getByLabel("Agent application").selectOption("42");
  await page.getByRole("button", { name: "Copy agent prompt" }).click();
  const prompt = await page.evaluate(() => navigator.clipboard.readText());
  expect(prompt).toContain("cv-apply");
  expect(prompt).toContain("--task application_form --application 42");
  expect(prompt).toContain("leave final submission to me");
});

test("saved form review shows proposed and mismatched observed values without raw editing", async ({ page, context }, testInfo) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const draft = { id: 19, type: "application_form", content: "", created_at: "2026-11-02T10:00:00Z", metadata: {
    structured_content: { company_name: "Acme", job_title: "Engineer", step: "Application", documents: [], fields: [
      { key: "motivation", label: "Why this role?", kind: "textarea", section: "Motivation", original_value: null,
        proposed_value: "I build useful tools in Python.", observed_value: "I build useful", observation: "observed", document_id: null,
        evidence: "Confirmed Python project in my profile" },
    ] },
    validation: { state: "partially_filled", issues: [{ field_key: "motivation", message: "The observed value does not exactly match the intended answer.", severity: "blocking" }],
      fields: [{ key: "motivation", verified: false, used: 30, maximum: 100, unit: "utf16" }] },
  } };
  const conversation = { id: 1, job_id: 42, title: "Engineer at Acme", updated_at: "2026-11-02", messages: [], drafts: [draft] };
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const data = path === "/api/workspace" ? { data_dir: "C:\\Career workspace", ai: { mode: "external" } } :
      path === "/api/tracker" ? [{ id: 42, company_name: "Acme", job_title: "Engineer", status: "Saved" }] :
      path === "/api/profile/me" ? { first_name: "Alex", last_name: "Example", skills: [] } :
      path === "/api/assistant/conversations" ? [conversation] :
      path === "/api/assistant/conversations/1" ? conversation : [];
    await route.fulfill({ json: data });
  });
  await page.goto("/assistant");
  const card = page.getByRole("region", { name: "Application form checkpoint" });
  await expect(card.getByText("Partially filled", { exact: true })).toBeVisible();
  await expect(card.getByText("Observed: I build useful", { exact: true })).toBeVisible();
  await expect(card.getByRole("button", { name: "Edit draft" })).toHaveCount(0);
  await card.getByRole("button", { name: "Copy application answers" }).click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain("I build useful tools in Python.");
  await card.screenshot({ path: testInfo.outputPath("form-review.png") });
});
