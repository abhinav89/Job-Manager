import { expect, test } from "@playwright/test";

test("visitors can learn and copy the snapshot skill from the guide or skills desk", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async (value: string) => { (window as Window & { copiedPrompt?: string }).copiedPrompt = value; } } });
  });
  await page.goto("/#snapshots");
  const section = page.locator("#snapshots");
  await expect(section.getByRole("heading", { name: "Your search at a glance." })).toBeVisible();
  await expect(section.getByRole("listitem")).toHaveCount(3);
  await expect(section.getByRole("img", { name: "Sample application snapshot" })).toBeVisible();
  await expect(section.getByText("Illustrative data", { exact: true })).toBeVisible();
  await expect(section.getByText(/include archived applications/)).toBeVisible();
  await expect(section.getByText(/snapshots folder/)).toBeVisible();
  await section.getByRole("button", { name: "Copy application snapshot prompt", exact: true }).click();
  await expect(section.getByRole("status")).toHaveText("Copied to clipboard.");
  const prompt = await page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt);
  expect(prompt).toContain("Use cv-snapshot");
  expect(prompt).toContain("my local CV Tailor database");
  expect(prompt).toContain("Leave my application records unchanged");
  await expect(section.getByRole("link", { name: "Read the skill instructions" })).toHaveAttribute("href", /\.agents\/skills\/cv-snapshot\/SKILL\.md$/);
  const skills = page.locator("#skills");
  await skills.getByRole("button", { name: "cv-snapshot", exact: true }).click();
  await expect(skills.getByRole("heading", { name: "Application snapshots" })).toBeVisible();
  await skills.getByRole("button", { name: "Copy cv-snapshot example prompt" }).click();
  expect(await page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt)).toBe(prompt);
});

test("snapshot instructions remain usable on mobile when the clipboard is unavailable", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async () => { throw new Error("denied"); } } });
  });
  await page.goto("/#snapshots");
  await page.getByRole("button", { name: "Copy application snapshot prompt", exact: true }).click();
  const fallback = page.getByRole("textbox", { name: "Copy application snapshot prompt: text to copy", exact: true });
  await expect(fallback).toBeVisible();
  await expect(fallback).toHaveValue(/Use cv-snapshot.*Leave my application records unchanged/);
  await fallback.focus();
  expect(await fallback.evaluate((field: HTMLTextAreaElement) => field.selectionEnd - field.selectionStart === field.value.length)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("snapshot preview and instructions fit both themes across screen sizes", async ({ page }, testInfo) => {
  for (const width of [320, 390, 900, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/#snapshots");
    await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
    await page.locator("#snapshots-title").scrollIntoViewIfNeeded();
    await expect(page.locator("#snapshots-title")).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if (width === 390 || width === 1440) {
      await page.locator("#snapshots").screenshot({ path: testInfo.outputPath(`snapshots-${width}-light.png`), animations: "disabled" });
      await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
      await page.locator("#snapshots").screenshot({ path: testInfo.outputPath(`snapshots-${width}-dark.png`), animations: "disabled" });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
  }
});
