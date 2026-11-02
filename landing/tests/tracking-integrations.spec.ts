import { test, expect } from "@playwright/test";

test("each destination copies its setup wizard and local credential instructions", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async (value: string) => { (window as Window & { copiedPrompt?: string }).copiedPrompt = value; } } });
  });
  await page.goto("/#integrations");
  const section = page.locator("#integrations");
  await expect(section.getByRole("heading", { name: "Connect it anywhere." })).toBeVisible();
  await expect(section.locator("article")).toHaveCount(7);
  for (const name of ["Obsidian", "Notion", "Google Sheets", "Markdown", "Airtable", "HubSpot", "GoHighLevel"]) {
    const card = section.getByRole("article").filter({ has: page.getByRole("heading", { name, exact: true }) });
    await expect(card.getByRole("img", { name: `${name} logo` })).toBeVisible();
    expect(await card.locator("img").evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
    await card.getByRole("button", { name: `Copy ${name} connection prompt`, exact: true }).click();
    await expect(card.getByRole("status")).toHaveText("Copied to clipboard.");
    const prompt = await page.evaluate(() => (window as Window & { copiedPrompt?: string }).copiedPrompt);
    expect(prompt).toContain(name);
    expect(prompt).toContain("cv-connect");
    expect(prompt).toContain("SQLite as my primary");
    expect(prompt).toContain(".env.integrations");
    expect(prompt).toContain("untracked and ignored");
    expect(prompt).toContain("Never ask me to paste credentials into agent chat");
    expect(prompt).toContain("dry run before the first publish");
    if (name === "HubSpot") {
      expect(prompt).toContain("supported objects and API access");
      expect(prompt).toContain("Do not assume paid custom objects");
    }
    if (name === "GoHighLevel") {
      expect(prompt).toContain("GoHighLevel (GHL)");
      expect(prompt).toContain("Never invent contacts, merge applications that share a contact");
    }
  }
});

test("clipboard refusal leaves a selectable complete prompt", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: async () => { throw new Error("denied"); } } });
  });
  await page.goto("/#integrations");
  await page.getByRole("button", { name: "Copy Notion connection prompt", exact: true }).click();
  const fallback = page.getByRole("textbox", { name: "Copy Notion connection prompt: text to copy", exact: true });
  await expect(fallback).toBeVisible();
  await expect(fallback).toHaveValue(/Use the cv-connect skill.*Notion.*\.env.integrations/);
  await fallback.focus();
  expect(await fallback.evaluate((field: HTMLTextAreaElement) => field.selectionEnd - field.selectionStart === field.value.length)).toBe(true);
});

test("connection cards and navigation fit mobile, tablet, and desktop", async ({ page }) => {
  for (const width of [320, 390, 768, 900, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    if (width <= 900) {
      await page.getByRole("button", { name: "Open menu", exact: true }).click();
      await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("link", { name: "Connect your tools" }).click();
      await expect(page.getByRole("button", { name: "Open menu", exact: true })).toBeVisible();
    } else {
      await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Connect", exact: true }).click();
    }
    await expect(page).toHaveURL(/#integrations$/);
    await expect(page.getByRole("heading", { name: "Connect it anywhere." })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.locator(".integration-card .copy-button")).toHaveCount(7);
  }
});
