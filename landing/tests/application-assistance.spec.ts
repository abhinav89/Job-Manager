import { expect, test } from "@playwright/test";

test("visitors can copy the application workflow from its guide or the skills desk", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async (value: string) => { (window as Window & { copiedPrompt?: string }).copiedPrompt = value; } } });
  });
  await page.goto("/#apply");
  const section = page.locator("#apply");
  await expect(section.getByRole("heading", { name: "Less retyping. More time to review." })).toBeVisible();
  await expect(section.getByRole("listitem")).toHaveCount(3);
  await section.getByRole("button", { name: "Copy application assistance prompt" }).click();
  await expect(section.getByRole("status")).toHaveText("Copied to clipboard.");
  const prompt = await page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt);
  expect(prompt).toContain("Use cv-apply for application #42");
  expect(prompt).toContain("I'll submit it myself");
  await expect(section.getByRole("link", { name: "Read the application guide" })).toHaveAttribute("href", /docs\/application_forms\.md$/);
  const skills = page.locator("#skills");
  await skills.getByRole("button", { name: "cv-apply", exact: true }).click();
  await expect(skills.getByRole("heading", { name: "Application form assistance" })).toBeVisible();
  await skills.getByRole("button", { name: "Copy cv-apply example prompt" }).click();
  expect(await page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt)).toBe(prompt);
});

test("clipboard refusal leaves the complete application prompt selectable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 850 });
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async () => { throw new Error("denied"); } } });
  });
  await page.goto("/#apply");
  await page.getByRole("button", { name: "Copy application assistance prompt", exact: true }).click();
  const fallback = page.getByRole("textbox", { name: "Copy application assistance prompt: text to copy", exact: true });
  await expect(fallback).toBeVisible();
  await expect(fallback).toHaveValue(/Use cv-apply.*I'll submit it myself/);
  await fallback.focus();
  expect(await fallback.evaluate((field: HTMLTextAreaElement) => field.selectionEnd - field.selectionStart === field.value.length)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("application guide navigation fits mobile and desktop in both themes", async ({ page }, testInfo) => {
  for (const width of [320, 390, 900, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    if (width <= 900) {
      await page.getByRole("button", { name: "Open menu", exact: true }).click();
      await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("link", { name: "Application forms", exact: true }).click();
    } else {
      await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Apply", exact: true }).click();
    }
    await expect(page).toHaveURL(/#apply$/);
    await expect(page.locator("#apply-title")).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if (width === 390 || width === 1440) {
      await page.locator("#apply").screenshot({ path: testInfo.outputPath(`application-${width}-light.png`), animations: "disabled" });
      await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
      await page.locator("#apply").screenshot({ path: testInfo.outputPath(`application-${width}-dark.png`), animations: "disabled" });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
  }
});
