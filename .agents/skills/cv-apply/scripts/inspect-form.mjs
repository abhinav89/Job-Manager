/** Read-only DOM helper. Pass this self-contained function to a supported
 * browser evaluation API; never import it as an automatic page content script. */
export async function inspectApplicationForm(step = "Application") {
  const visible = el => !!el && !!el.getClientRects().length && getComputedStyle(el).visibility !== "hidden";
  // Do not read any field values on a credential/verification step. Passwords
  // must never become a text field in an application checkpoint.
  const credential = el => el.type === "password" ||
    /current-password|new-password|one-time-code|webauthn|username/i.test(el.autocomplete || "") ||
    /password|passwd|one.?time|otp|2fa|mfa|authenticator|api.?key|access.?token|secret|security.?code|verification.?code/i
      .test([el.name, el.id, el.getAttribute("aria-label"), ...Array.from(el.labels || []).map(l => l.textContent)].join(" "));
  if (/(?:^|\/)(?:login|log-in|signin|sign-in|oauth|password|mfa|2fa|verify)(?:\/|$)/i.test(location.pathname) ||
      Array.from(document.querySelectorAll("input, textarea")).some(el => visible(el) && credential(el))) {
    return {form_url: location.origin + location.pathname, login_required: true, fields: []};
  }
  const clean = text => (text || "").replace(/\s+/g, " ").trim();
  const labelText = node => {
    const copy = node.cloneNode(true);
    copy.querySelectorAll("input, select, textarea, button, script, style").forEach(child => child.remove());
    return copy.textContent;
  };
  const described = el => clean((el.getAttribute("aria-describedby") || "").split(/\s+/)
    .map(id => document.getElementById(id)?.textContent || "").join(" "));
  const label = el => clean(el.getAttribute("aria-label") ||
    (el.getAttribute("aria-labelledby") || "").split(/\s+/).map(id => document.getElementById(id)?.textContent || "").join(" ") ||
    Array.from(el.labels || []).map(labelText).join(" ") || el.getAttribute("placeholder") || el.name || el.id);
  const fieldsets = Array.from(document.querySelectorAll("fieldset"));
  const section = el => {
    const parents = [];
    for (let p = el.parentElement; p; p = p.parentElement) {
      if (p.tagName !== "FIELDSET") continue;
      const title = clean(p.querySelector(":scope > legend")?.textContent) || "Entry";
      const peers = fieldsets.filter(f => (clean(f.querySelector(":scope > legend")?.textContent) || "Entry") === title);
      parents.unshift(`${title}${peers.length > 1 ? ` ${peers.indexOf(p) + 1}` : ""}`);
    }
    return parents.join(" / ");
  };
  const fields = [];
  const occurrences = new Map();
  const seenRadio = new Set();
  for (const el of document.querySelectorAll("input, textarea, select, [role=combobox]")) {
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || "text").toLowerCase();
    if (el.disabled || credential(el) || ["hidden", "button", "submit", "reset", "image"].includes(type)) continue;
    if (!visible(el) && !Array.from(el.labels || []).some(visible)) continue;
    const groupSection = section(el);
    let kind = tag === "select" ? "select" : tag === "textarea" ? "textarea" :
      ["email", "tel", "url", "number", "date", "checkbox", "radio", "file"].includes(type) ? type : "text";
    // Custom widgets require an accessible snapshot: typed search text is not
    // evidence that the application accepted a selection.
    if (el.getAttribute("role") === "combobox") kind = "unknown";
    let title = label(el) || "Unlabelled control";
    let options = [];
    let value = el.value ?? null;
    let required = !!el.required || el.getAttribute("aria-required") === "true" || /\*/.test(title);
    if (kind === "radio") {
      const group = el.name ? Array.from(document.querySelectorAll('input[type="radio"]')).filter(r =>
        r.name === el.name && r.form === el.form && section(r) === groupSection) : [el];
      if (seenRadio.has(group[0])) continue;
      seenRadio.add(group[0]);
      options = group.map(label);
      const checked = group.find(r => r.checked);
      value = checked ? label(checked) : null;
      title = clean(el.closest("fieldset")?.querySelector(":scope > legend")?.textContent) || el.name || title;
      required ||= group.some(r => r.required || r.getAttribute("aria-required") === "true");
    } else if (kind === "select") {
      options = Array.from(el.options).filter(o => o.value && !o.disabled).map(o => clean(o.textContent));
      const selected = Array.from(el.selectedOptions).filter(o => o.value).map(o => clean(o.textContent));
      value = el.multiple ? selected : selected[0] ?? null;
    } else if (kind === "checkbox") value = !!el.checked;
    else if (kind === "file" || kind === "unknown") value = null;
    const base = `${step}/${groupSection}/${kind}/${title}`.slice(0, 450);
    const occurrence = (occurrences.get(base) || 0) + 1;
    occurrences.set(base, occurrence);
    const help = described(el);
    let limit = null;
    const ml = el.getAttribute("maxlength");
    if (ml !== null && /^\d+$/.test(ml)) limit = { maximum: Number(ml), unit: "utf16", source: "Rendered control maxlength" };
    const words = help.match(/(?:maximum|max|up to|limit:?)[\s:]+(\d+)\s+words\b/i);
    if (!limit && words) limit = { maximum: Number(words[1]), unit: "words", source: help };
    const files = [];
    for (const file of kind === "file" ? Array.from(el.files || []) : []) {
      let hash = null;
      try {
        const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
        hash = Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, "0")).join("");
      } catch { /* No reliable file hash: report it unknown. */ }
      files.push({ filename: file.name, size: file.size, sha256: hash });
    }
    if (kind === "file" && files.length) value = files.map(file => file.filename);
    fields.push({ key: `${base}/${occurrence}`, label: title, section: groupSection, kind, required,
      options, limit, original_value: value, proposed_value: null, observed_value: value,
      observation: kind === "unknown" ? "unreadable" : "observed", observed_at: new Date().toISOString(),
      original_files: files, observed_files: files, source: value !== null && value !== "" && value !== false ? "user_existing" : "none",
      evidence: value !== null && value !== "" && value !== false ? `Existing value in ${title}` : "",
      validation_errors: el.getAttribute("aria-invalid") === "true" ? [help || "The portal marked this field invalid"] :
        el.willValidate && !el.validity.valid ? [el.validationMessage || "The field failed native browser validation"] : [],
    });
  }
  return { form_url: location.href, title: document.title, fields };
}
