// Fixed code owned by CV Tailor. The model cannot supply JavaScript or selectors.
async () => {
  const visible = el => !!el.getClientRects().length && getComputedStyle(el).visibility !== "hidden";
  const clean = text => (text || "").replace(/\s+/g, " ").trim();
  const label = el => clean(el.getAttribute("aria-label") ||
    Array.from(el.labels || []).map(l => {
      const clone = l.cloneNode(true);
      clone.querySelectorAll("input, textarea, select, script, style").forEach(c => c.remove());
      return clone.textContent;
    }).join(" ") || el.getAttribute("placeholder") || el.name || el.id || el.textContent);
  const sensitive = el => el.type === "password" ||
    /current-password|new-password|one-time-code|webauthn|username/i.test(el.autocomplete || "") ||
    /password|passwd|one.?time|\botp\b|\bpin\b|2fa|mfa|authenticator|api.?key|access.?token|secret|security.?code|verification.?code/i
      .test([el.name, el.id, el.getAttribute("aria-label"), label(el)].join(" "));
  const controls = Array.from(document.querySelectorAll("input, textarea, select, button, a[href], [role=combobox]"));
  const authForm = Array.from(document.forms).some(form => visible(form) &&
    /(?:^|\/)(?:login|log-in|signin|sign-in|oauth|password|verify)(?:\/|$)/i.test(new URL(form.action, location.href).pathname));
  if (authForm || controls.some(el => visible(el) && sensitive(el))) return {blocked: true};
  const fields = [];
  for (const [index, el] of controls.entries()) {
    if (!visible(el) || el.disabled || el.type === "hidden" || sensitive(el)) continue;
    const tag = el.tagName.toLowerCase();
    const kind = tag === "a" ? "link" : tag === "button" || ["submit", "button", "reset", "image"].includes(el.type) ? "button" :
      el.getAttribute("role") === "combobox" ? "unknown" : tag === "select" ? "select" : tag === "textarea" ? "textarea" : el.type;
    let value = null;
    let options = [];
    if (kind === "select") {
      options = Array.from(el.options).filter(o => o.value && !o.disabled).map(o => clean(o.textContent));
      value = Array.from(el.selectedOptions).filter(o => o.value).map(o => clean(o.textContent));
    } else if (["checkbox", "radio"].includes(kind)) value = el.checked;
    else if (!["button", "link", "file", "unknown"].includes(kind)) value = el.value;
    const files = [];
    if (kind === "file") {
      for (const file of el.files || []) {
        let sha256 = null;
        try {
          sha256 = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", await file.arrayBuffer())))
            .map(b => b.toString(16).padStart(2, "0")).join("");
        } catch { /* Leave unverified if hashing is not available. */ }
        files.push({filename: file.name, size: file.size, sha256});
      }
      value = files.map(f => f.filename);
    }
    fields.push({index, label: label(el), kind, required: !!el.required || el.getAttribute("aria-required") === "true",
      value, options, files, maxlength: el.hasAttribute("maxlength") ? el.maxLength : null,
      section: clean(el.closest("fieldset")?.querySelector(":scope > legend")?.textContent),
      validation_error: el.willValidate && !el.validity.valid ? el.validationMessage : null});
  }
  if (controls.some(el => visible(el) && sensitive(el))) return {blocked: true};
  return {blocked: false, fields, headings: Array.from(document.querySelectorAll("h1, h2")).filter(visible).map(el => clean(el.textContent))};
}
