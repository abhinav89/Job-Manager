import { test, expect } from "@playwright/test";

test("gallery opens the actual PDF, renders its text, and restores focus on Escape", async ({ page }) => {
  await page.goto("/#templates");
  await expect(page.locator(".resume-template-card")).toHaveCount(8);
  await expect(page.locator(".resume-template-card p")).toHaveCount(0);
  const trigger = page.getByRole("button", { name: "Preview Minimal PDF", exact: true });
  await trigger.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Minimal", exact: true })).toBeVisible();
  await expect(dialog.locator("canvas")).toBeVisible({ timeout: 20000 });
  await expect(dialog.locator(".textLayer")).toContainText("ALEX MORGAN");
  await expect(dialog.locator(".textLayer")).toContainText("Northstar Studio");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
});

test("mobile cards copy the chosen template prompt and render the Sidebar PDF", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async (value: string) => { (window as Window & { copiedPrompt?: string }).copiedPrompt = value; } } });
  });
  await page.goto("/#templates");
  await page.getByRole("button", { name: "Copy Sidebar resume prompt", exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt)).toContain("template_id: sidebar");
  await expect.poll(() => page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt)).toContain("Remember this as my default resume format");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Preview Sidebar PDF", exact: true }).click();
  await expect(page.getByRole("dialog").locator("canvas")).toBeVisible({ timeout: 20000 });
  await expect(page.getByRole("dialog").locator(".textLayer")).toContainText(/Coastal State\s*University/);
  await page.getByRole("button", { name: "Close PDF preview", exact: true }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
