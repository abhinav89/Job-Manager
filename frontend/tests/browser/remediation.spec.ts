import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const latex = readFileSync(resolve("tests/browser/fixtures/resume.tex"), "utf8");
const pdf = readFileSync(resolve("tests/browser/fixtures/resume.pdf"));
const summary = "Engineer building useful tools for clients.";
const job = { id: 1, company_name: "Acme", job_title: "Engineer", job_description: "Build useful reporting tools.", has_pdf: true, status: "Saved", priority: "Medium", template_id: "classic" };

async function fixtures(page: Page) {
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user_id: 1, email: "jane@example.com", is_admin: false };
    else if (path === "/api/profile/me") data = { first_name: "Jane", last_name: "Doe", email: "jane@example.com", mobile_no: "", education: [], experience: [], projects: [], skills: [], certifications: [], preset_slug: "blank" };
    else if (path === "/api/presets") data = [];
    else if (path === "/api/tracker") data = [job];
    else if (path === "/api/tracker/1/details") data = job;
    else if (path === "/api/tracker/1/latex") data = { latex };
    else if (path === "/api/assistant/conversations") data = [{ id: 1, job_id: null, title: "General", updated_at: "2026-11-02" }];
    else if (path === "/api/assistant/conversations/1") data = { id: 1, job_id: null, title: "General", updated_at: "2026-11-02", messages: [], drafts: [] };
    else if (path.endsWith("/cancel")) data = { status: "cancelled" };
    else if (path === "/api/generate/compile-with-check") data = { pdf_b64: pdf.toString("base64"), ats: { pass: true, warnings: [] }, num_pages: 2, auto_fitted: false };
    else if (path === "/api/generate/compile-preview") {
      await route.fulfill({ contentType: "application/pdf", headers: { "X-PDF-Pages": "2" }, body: pdf });
      return;
    } else if (path === "/api/interview/questions") data = { questions: ["Describe a reporting project."] };
    await route.fulfill({ json: data });
  });
  // MediaPipe can fail to initialize without affecting camera cleanup. Keeping
  // remote model/WASM fetches out of these tests makes them deterministic.
  await page.route(/https:\/\/(?:cdn\.jsdelivr\.net|storage\.googleapis\.com)\//, route => route.abort());
}

test("source edits survive returning to the structured form", async ({ page }) => {
  await fixtures(page);
  await page.goto("/generate?job_id=1");
  await expect(page.locator("textarea").first()).toHaveValue(summary);
  await page.getByRole("button", { name: "LaTeX", exact: true }).click();
  await page.getByTitle("Switch between Monaco IDE editor and plain text area").click();
  const source = page.locator('textarea[spellcheck="false"]');
  await source.fill(latex.replace(summary, "Updated summary from the LaTeX editor."));
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  await expect(page.locator("textarea").first()).toHaveValue("Updated summary from the LaTeX editor.");
});

test("resume generation displays a useful error for a plain-text server failure", async ({ page }) => {
  await fixtures(page);
  await page.route("**/api/generate/ats-check", route => route.fulfill({ status: 500, contentType: "text/plain", body: "Internal Server Error" }));
  await page.goto("/generate");
  await page.getByPlaceholder("Paste the full job description here...").fill("Build Python reporting tools.");
  await page.getByRole("button", { name: /generate/i }).click();
  await expect(page.getByText("Something went wrong on our side. Please try again shortly.", { exact: false })).toBeVisible({ timeout: 5000 });
  await expect(page.getByText(/Unexpected token/)).toHaveCount(0);
});

test("resume generation shows the specific claims rejected by the checker", async ({ page }) => {
  await fixtures(page);
  const detail = "The generated resume still includes claims the checker couldn't support. Claims to review: Team leadership is absent from the profile.";
  await page.route("**/api/generate/ats-check", route => route.fulfill({ status: 502, json: { detail } }));
  await page.goto("/generate");
  await page.getByPlaceholder("Paste the full job description here...").fill("Build Python reporting tools.");
  await page.getByRole("button", { name: /generate/i }).click();
  await expect(page.getByText(detail, { exact: false })).toBeVisible();
});

test("all modes allow PDF Spot Edits and keep the page after recompilation", async ({ page }) => {
  await fixtures(page);
  await page.goto("/generate?job_id=1");
  for (const mode of ["Edit", "Preview", "LaTeX"]) {
    await page.getByRole("button", { name: mode, exact: true }).click();
    await expect(page.locator(".react-pdf__Page__textContent").first()).toBeVisible();
    const text = page.locator(".react-pdf__Page__textContent span").filter({ hasText: summary }).first();
    await expect(text).toBeVisible();
    await text.evaluate(element => {
      const range = document.createRange();
      range.selectNodeContents(element);
      const selection = window.getSelection()!;
      selection.removeAllRanges();
      selection.addRange(range);
      element.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
    });
    await expect(page.getByText("Spot Edit · 1 Block", { exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "→", exact: true }).last().click();
    await expect(page.getByText("2/2", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Recompile", exact: true }).click();
    await expect(page.getByRole("button", { name: "Recompile", exact: true })).toBeEnabled();
    await expect(page.getByText("2/2", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "←", exact: true }).last().click();
  }
});

test("an old ATS compilation cannot replace the PDF after a newer edit", async ({ page }) => {
  await fixtures(page);
  await page.addInitScript(() => {
    const original = URL.createObjectURL.bind(URL);
    Object.assign(window, { auditPdfUrls: 0 });
    URL.createObjectURL = object => {
      if (object instanceof Blob && object.type === "application/pdf") {
        (window as unknown as { auditPdfUrls: number }).auditPdfUrls++;
      }
      return original(object);
    };
  });
  await page.goto("/generate?job_id=1");
  await expect(page.locator(".react-pdf__Page__textContent").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Recompile", exact: true })).toBeEnabled();
  const initialUrls = await page.evaluate(() => (window as unknown as { auditPdfUrls: number }).auditPdfUrls);
  let oldRequested = false;
  let newRequested = false;
  let releaseOld!: () => void;
  let releaseNew!: () => void;
  const oldGate = new Promise<void>(resolve => { releaseOld = resolve; });
  const newGate = new Promise<void>(resolve => { releaseNew = resolve; });
  await page.route("**/api/generate/compile-with-check", async route => {
    oldRequested = true;
    await oldGate;
    await route.fulfill({ json: { pdf_b64: pdf.toString("base64"), ats: { pass: false, warnings: ["Stale compilation warning"] }, num_pages: 99 } });
  });
  await page.route("**/api/generate/compile-preview", async route => {
    newRequested = true;
    await newGate;
    await route.fulfill({ contentType: "application/pdf", headers: { "X-PDF-Pages": "2" }, body: pdf });
  });
  try {
    await page.getByRole("button", { name: "Recompile", exact: true }).click();
    await expect.poll(() => oldRequested).toBe(true);
    await page.locator("textarea").first().fill("A newer summary waiting for its own preview.");
    releaseOld();
    await expect.poll(() => newRequested).toBe(true);
    expect(await page.evaluate(() => (window as unknown as { auditPdfUrls: number }).auditPdfUrls)).toBe(initialUrls);
    await expect(page.getByText("Stale compilation warning", { exact: true })).toHaveCount(0);
    await expect(page.getByText("Check suggestions", { exact: true })).toHaveCount(0);
    releaseNew();
    await expect(page.getByRole("button", { name: "Recompile", exact: true })).toBeEnabled();
    expect(await page.evaluate(() => (window as unknown as { auditPdfUrls: number }).auditPdfUrls)).toBe(initialUrls + 1);
  } finally {
    releaseOld();
    releaseNew();
  }
});

test("leaving interview practice stops every acquired camera track", async ({ page }) => {
  await fixtures(page);
  await page.addInitScript(() => {
    const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    const tracks: MediaStreamTrack[] = [];
    Object.assign(window, { auditCameraTracks: tracks });
    navigator.mediaDevices.getUserMedia = async constraints => {
      const stream = await original(constraints);
      tracks.push(...stream.getTracks());
      return stream;
    };
  });
  await page.goto("/interview?job_id=1");
  await expect(page.getByText("Ready to practice?", { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => (window as unknown as { auditCameraTracks: MediaStreamTrack[] }).auditCameraTracks.length)).toBeGreaterThan(0);
  await page.locator('a[href="/generate"]').first().click();
  await expect.poll(() => page.evaluate(() => (window as unknown as { auditCameraTracks: MediaStreamTrack[] }).auditCameraTracks.every(track => track.readyState === "ended"))).toBe(true);
});

test("cancelling an assistant reply aborts consumption and ignores late completion", async ({ page }) => {
  await fixtures(page);
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = async (input, init) => {
      if (String(input).endsWith("/messages/stream")) {
        const state = window as unknown as { auditSignal: AbortSignal; auditStream: ReadableStreamDefaultController<Uint8Array> };
        state.auditSignal = init!.signal!;
        return new Response(new ReadableStream<Uint8Array>({ start(controller) { state.auditStream = controller; } }));
      }
      return original(input, init);
    };
  });
  await page.goto("/assistant");
  await page.getByRole("textbox", { name: "Message the Career Agent" }).fill("Help me prepare.");
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await page.getByRole("button", { name: "Cancel reply", exact: true }).click();
  await expect(page.getByText("Reply cancelled. External work may still be winding down.", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { auditSignal: AbortSignal }).auditSignal.aborted)).toBe(true);
  await page.evaluate(() => {
    const state = window as unknown as { auditStream: ReadableStreamDefaultController<Uint8Array> };
    state.auditStream.enqueue(new TextEncoder().encode(JSON.stringify({ type: "complete", conversation: { id: 1, job_id: null, title: "Late", messages: [{ id: 1, role: "assistant", content: "Late completion must be ignored" }], drafts: [] } }) + "\n"));
    state.auditStream.close();
  });
  await expect(page.getByRole("button", { name: "Cancel reply", exact: true })).toHaveCount(0);
  await expect(page.getByText("Late completion must be ignored", { exact: true })).toHaveCount(0);
});
