/**
 * DealOS Job Manager — ATS Form Autofill & Copilot Content Script
 * 
 * Accurately detects and autofills application inputs across Greenhouse, Lever,
 * Ashby, Workday, LinkedIn, SmartRecruiters, BambooHR, and all corporate ATS portals.
 */

(function () {
  if (window.__DEALOS_AUTOFILL_INJECTED__) return;
  window.__DEALOS_AUTOFILL_INJECTED__ = true;

  // ── 1. ATS Platform Detection ──────────────────────────────────────
  function detectATS() {
    const host = window.location.hostname.toLowerCase();
    const url = window.location.href.toLowerCase();

    if (host.includes("greenhouse.io") || document.querySelector("#job_application_answers_attributes_0_boolean_value, #first_name, form[action*='greenhouse']")) {
      return "Greenhouse";
    }
    if (host.includes("lever.co") || document.querySelector(".application-form, form[action*='lever.co']")) {
      return "Lever";
    }
    if (host.includes("ashbyhq.com") || document.querySelector("input[name*='_systemfield_']")) {
      return "Ashby";
    }
    if (host.includes("myworkdayjobs.com") || host.includes("workday.com") || document.querySelector("[data-automation-id*='legalNameSection_']")) {
      return "Workday";
    }
    if (host.includes("smartrecruiters.com") || document.querySelector("oc-one-click-apply, [data-test-id*='smartrecruiters']")) {
      return "SmartRecruiters";
    }
    if (host.includes("bamboohr.com")) {
      return "BambooHR";
    }
    if (host.includes("linkedin.com") && document.querySelector(".jobs-easy-apply-modal, .jobs-apply-button")) {
      return "LinkedIn Easy Apply";
    }
    return "Generic Career Portal";
  }

  // ── 2. Native Value Setter (React / Angular / Vue compatible) ──────
  function setNativeValue(element, value) {
    if (!element || value === undefined || value === null) return false;

    try {
      const tag = element.tagName.toLowerCase();
      let valueSetter;

      if (tag === "input") {
        valueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
      } else if (tag === "textarea") {
        valueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
      } else if (tag === "select") {
        valueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value")?.set;
      }

      if (valueSetter) {
        valueSetter.call(element, value);
      } else {
        element.value = value;
      }

      // Dispatch comprehensive event chain for modern frontend frameworks
      element.dispatchEvent(new Event("focus", { bubbles: true }));
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
      element.dispatchEvent(new Event("blur", { bubbles: true }));

      // Visual highlight
      element.style.transition = "all 0.3s ease";
      element.style.boxShadow = "0 0 0 2px #10b981";
      element.style.borderColor = "#10b981";

      return true;
    } catch (e) {
      console.warn("[DealOS] Failed setting native value:", e);
      element.value = value;
      return true;
    }
  }

  // ── 3. Field Identification Heuristics ─────────────────────────────
  function getFieldContext(el) {
    const id = (el.id || "").toLowerCase();
    const name = (el.name || "").toLowerCase();
    const placeholder = (el.placeholder || "").toLowerCase();
    const aria = (el.getAttribute("aria-label") || "").toLowerCase();
    const autoId = (el.getAttribute("data-automation-id") || "").toLowerCase();
    const autocomplete = (el.autocomplete || "").toLowerCase();

    // Look for associated label text
    let labelText = "";
    if (el.id) {
      const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (labelEl) labelText = labelEl.innerText.toLowerCase();
    }
    if (!labelText) {
      const parentLabel = el.closest("label");
      if (parentLabel) labelText = parentLabel.innerText.toLowerCase();
    }
    if (!labelText && el.parentElement) {
      const prevEl = el.previousElementSibling;
      if (prevEl && (prevEl.tagName === "LABEL" || prevEl.tagName === "SPAN" || prevEl.tagName === "P")) {
        labelText = prevEl.innerText.toLowerCase();
      }
    }

    return `${id} ${name} ${placeholder} ${aria} ${autoId} ${autocomplete} ${labelText}`.trim();
  }

  // ── 4. Main Autofill Engine ────────────────────────────────────────
  function autofillForm(profile, customAnswers = {}) {
    if (!profile) return { success: false, filledCount: 0 };

    let filledCount = 0;
    const inputs = Array.from(document.querySelectorAll("input, textarea, select"));

    const firstName = profile.first_name || (profile.name ? profile.name.split(" ")[0] : "");
    const lastName = profile.last_name || (profile.name ? profile.name.split(" ").slice(1).join(" ") : "");
    const fullName = `${firstName} ${lastName}`.trim();
    const email = profile.email || "";
    const phone = profile.mobile_no || profile.phone || "";
    const linkedin = profile.linkedin || "";
    const github = profile.github || "";
    const portfolio = profile.portfolio || profile.website || "";
    const location = (profile.target_locations && profile.target_locations[0]) || "India";

    // Work Experience
    const currentExp = (profile.experience && profile.experience[0]) || {};
    const currentCompany = currentExp.company || "";
    const currentTitle = currentExp.job_title || "";
    const totalExpYears = profile.experience ? Math.min(25, Math.max(3, profile.experience.length * 2)) : 5;

    // Summary / Pitch
    const summary = currentExp.description
      ? `Accomplished ${currentTitle} with verified track record across ${currentCompany}. Experienced in strategy, execution, and driving cross-functional outcomes.`
      : "Experienced professional with proven track record in strategy, execution, and high-impact delivery.";

    inputs.forEach((el) => {
      // Skip hidden, disabled, or read-only elements
      if (el.type === "hidden" || el.disabled || el.readOnly || el.offsetParent === null) return;

      const ctx = getFieldContext(el);
      const tag = el.tagName.toLowerCase();

      // 1. First Name
      if (
        (ctx.includes("first") && (ctx.includes("name") || ctx.includes("given") || ctx.includes("fname"))) ||
        ctx.includes("legalnamesection_firstname")
      ) {
        if (firstName && !el.value) {
          if (setNativeValue(el, firstName)) filledCount++;
        }
        return;
      }

      // 2. Last Name
      if (
        (ctx.includes("last") && (ctx.includes("name") || ctx.includes("family") || ctx.includes("surname") || ctx.includes("lname"))) ||
        ctx.includes("legalnamesection_lastname")
      ) {
        if (lastName && !el.value) {
          if (setNativeValue(el, lastName)) filledCount++;
        }
        return;
      }

      // 3. Full Name (only if not a separate first/last name field)
      if (
        (ctx.includes("full_name") || ctx.includes("fullname") || (ctx.includes("name") && !ctx.includes("company") && !ctx.includes("first") && !ctx.includes("last") && !ctx.includes("user"))) &&
        tag === "input" && el.type === "text"
      ) {
        if (fullName && !el.value) {
          if (setNativeValue(el, fullName)) filledCount++;
        }
        return;
      }

      // 4. Email
      if (
        ctx.includes("email") ||
        ctx.includes("e-mail") ||
        el.type === "email"
      ) {
        if (email && !el.value) {
          if (setNativeValue(el, email)) filledCount++;
        }
        return;
      }

      // 5. Phone / Mobile
      if (
        ctx.includes("phone") ||
        ctx.includes("mobile") ||
        ctx.includes("cell") ||
        ctx.includes("contact_number") ||
        ctx.includes("phonenumber") ||
        el.type === "tel"
      ) {
        if (phone && !el.value) {
          if (setNativeValue(el, phone)) filledCount++;
        }
        return;
      }

      // 6. LinkedIn URL
      if (ctx.includes("linkedin") && !ctx.includes("how did you hear")) {
        if (linkedin && !el.value) {
          if (setNativeValue(el, linkedin)) filledCount++;
        }
        return;
      }

      // 7. GitHub URL
      if (ctx.includes("github")) {
        if (github && !el.value) {
          if (setNativeValue(el, github)) filledCount++;
        }
        return;
      }

      // 8. Website / Portfolio URL
      if (ctx.includes("website") || ctx.includes("portfolio") || ctx.includes("personal url") || ctx.includes("blog")) {
        if ((portfolio || linkedin) && !el.value) {
          if (setNativeValue(el, portfolio || linkedin)) filledCount++;
        }
        return;
      }

      // 9. Location / City / Address
      if (ctx.includes("city") || ctx.includes("location") || ctx.includes("addresssection_city") || ctx.includes("residence")) {
        if (location && !el.value) {
          if (setNativeValue(el, location)) filledCount++;
        }
        return;
      }

      // 10. Current Company / Employer
      if (
        (ctx.includes("company") || ctx.includes("employer") || ctx.includes("organization") || ctx.includes("org")) &&
        !ctx.includes("how did you hear")
      ) {
        if (currentCompany && !el.value) {
          if (setNativeValue(el, currentCompany)) filledCount++;
        }
        return;
      }

      // 11. Current Job Title / Headline
      if (ctx.includes("current title") || ctx.includes("job title") || ctx.includes("current role") || ctx.includes("headline")) {
        if (currentTitle && !el.value) {
          if (setNativeValue(el, currentTitle)) filledCount++;
        }
        return;
      }

      // 12. Years of Experience
      if (ctx.includes("years") && (ctx.includes("experience") || ctx.includes("exp"))) {
        if (!el.value) {
          if (setNativeValue(el, String(totalExpYears))) filledCount++;
        }
        return;
      }

      // 13. Work Authorization ("Yes")
      if (
        ctx.includes("authorized") ||
        ctx.includes("legally authorized") ||
        ctx.includes("right to work") ||
        ctx.includes("work eligibility")
      ) {
        const val = customAnswers.authorizedToWork || "Yes";
        if (tag === "select") {
          selectMatchingOption(el, ["yes", "authorized", "eligible"]);
          filledCount++;
        } else if (el.type === "radio" || el.type === "checkbox") {
          if (ctx.includes("yes")) {
            el.checked = true;
            el.dispatchEvent(new Event("change", { bubbles: true }));
            filledCount++;
          }
        } else if (el.type === "text" && !el.value) {
          if (setNativeValue(el, val)) filledCount++;
        }
        return;
      }

      // 14. Visa Sponsorship ("No")
      if (
        ctx.includes("sponsorship") ||
        ctx.includes("require sponsorship") ||
        ctx.includes("visa")
      ) {
        const val = customAnswers.requiresSponsorship || "No";
        if (tag === "select") {
          selectMatchingOption(el, ["no", "will not", "do not require"]);
          filledCount++;
        } else if (el.type === "radio" || el.type === "checkbox") {
          if (ctx.includes("no")) {
            el.checked = true;
            el.dispatchEvent(new Event("change", { bubbles: true }));
            filledCount++;
          }
        } else if (el.type === "text" && !el.value) {
          if (setNativeValue(el, val)) filledCount++;
        }
        return;
      }

      // 15. Notice Period
      if (ctx.includes("notice") || ctx.includes("availability") || ctx.includes("how soon can you start")) {
        const val = customAnswers.noticePeriod || "30 Days";
        if (tag === "select") {
          selectMatchingOption(el, ["30", "1 month", "immediate", "less than"]);
          filledCount++;
        } else if (tag === "input" && !el.value) {
          if (setNativeValue(el, val)) filledCount++;
        }
        return;
      }

      // 16. Salary Expectations
      if (ctx.includes("salary") || ctx.includes("compensation") || ctx.includes("expected ctc") || ctx.includes("desired salary")) {
        const val = customAnswers.preferredSalary || "Competitive / Market standard";
        if (tag === "input" && !el.value) {
          if (setNativeValue(el, val)) filledCount++;
        }
        return;
      }

      // 17. Summary / Pitch / Additional Info
      if (
        (ctx.includes("summary") || ctx.includes("cover letter") || ctx.includes("additional information") || ctx.includes("comments") || ctx.includes("pitch")) &&
        tag === "textarea"
      ) {
        if (!el.value) {
          if (setNativeValue(el, summary)) filledCount++;
        }
        return;
      }
    });

    // Show floating on-page toast notification
    showFeedbackBadge(filledCount);
    return { success: true, filledCount };
  }

  function selectMatchingOption(selectEl, keywords) {
    for (let opt of selectEl.options) {
      const optText = opt.text.toLowerCase();
      const optVal = opt.value.toLowerCase();
      for (let kw of keywords) {
        if (optText.includes(kw) || optVal.includes(kw)) {
          selectEl.value = opt.value;
          selectEl.dispatchEvent(new Event("change", { bubbles: true }));
          selectEl.style.boxShadow = "0 0 0 2px #10b981";
          return true;
        }
      }
    }
    return false;
  }

  function showFeedbackBadge(count) {
    const existing = document.getElementById("dealos-autofill-badge");
    if (existing) existing.remove();

    const badge = document.createElement("div");
    badge.id = "dealos-autofill-badge";
    badge.style.position = "fixed";
    badge.style.bottom = "24px";
    badge.style.right = "24px";
    badge.style.zIndex = "999999";
    badge.style.background = "#0f172a";
    badge.style.color = "#ffffff";
    badge.style.border = "1px solid #10b981";
    badge.style.borderRadius = "9999px";
    badge.style.padding = "10px 18px";
    badge.style.fontSize = "13px";
    badge.style.fontWeight = "600";
    badge.style.boxShadow = "0 10px 25px rgba(0,0,0,0.3)";
    badge.style.display = "flex";
    badge.style.alignItems = "center";
    badge.style.gap = "8px";
    badge.style.fontFamily = "system-ui, -apple-system, sans-serif";
    badge.style.animation = "dealosFadeIn 0.3s ease-out";

    badge.innerHTML = `
      <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;"></span>
      <span>${count > 0 ? `✨ DealOS: ${count} fields autofilled!` : "⚡ DealOS: Ready to autofill"}</span>
    `;

    document.body.appendChild(badge);

    setTimeout(() => {
      if (badge) {
        badge.style.opacity = "0";
        badge.style.transition = "opacity 0.4s ease";
        setTimeout(() => badge.remove(), 400);
      }
    }, 4000);
  }

  // ── 5. Page Job Scraper (for 1-click tracker save) ──────────────────
  function scrapePageJob() {
    let jobTitle = "";
    let companyName = "";
    let location = "";
    let description = "";

    // Specific ATS selectors
    const ats = detectATS();

    if (ats === "Greenhouse") {
      jobTitle = document.querySelector(".app-title, h1.header, .job-title")?.innerText || "";
      companyName = document.querySelector(".company-name, .header-tagline")?.innerText || "";
      location = document.querySelector(".location")?.innerText || "";
      description = document.querySelector("#content, .body")?.innerText || "";
    } else if (ats === "Lever") {
      jobTitle = document.querySelector(".posting-headline h2, h2")?.innerText || "";
      companyName = document.querySelector(".main-header-logo, .posting-headline")?.innerText || "";
      location = document.querySelector(".posting-categories .location")?.innerText || "";
      description = document.querySelector(".section-wrapper.page-full-width")?.innerText || "";
    } else if (ats === "Ashby") {
      jobTitle = document.querySelector("h1")?.innerText || "";
      description = document.querySelector("[class*='jobDescription']")?.innerText || "";
    }

    // Generic fallbacks
    if (!jobTitle) {
      jobTitle = document.querySelector("h1, h2.title, [class*='job-title'], [class*='jobTitle']")?.innerText || document.title;
    }
    if (!companyName) {
      companyName = document.querySelector("[class*='company-name'], [class*='companyName']")?.innerText || window.location.hostname.replace("www.", "").split(".")[0];
    }
    if (!description) {
      description = document.querySelector("article, main, #job-description, .job-description, [class*='description']")?.innerText || "";
    }

    return {
      job_title: (jobTitle || "Job Opportunity").trim().slice(0, 150),
      company_name: (companyName || "Target Company").trim().slice(0, 100),
      location: (location || "India").trim().slice(0, 100),
      job_url: window.location.href,
      source: ats,
      job_description: description.trim().slice(0, 4000)
    };
  }

  // ── 6. Message Listener from Extension Popup ───────────────────────
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "GET_PAGE_INFO") {
      const ats = detectATS();
      const jobInfo = scrapePageJob();
      sendResponse({ ats, jobInfo });
      return true;
    }

    if (request.action === "AUTOFILL") {
      const result = autofillForm(request.profile, request.customAnswers);
      sendResponse(result);
      return true;
    }

    if (request.action === "TRIGGER_AUTOFILL") {
      // Fetch profile from storage and autofill
      chrome.storage.local.get(["profile", "customAnswers"], (data) => {
        if (data.profile) {
          autofillForm(data.profile, data.customAnswers);
        }
      });
      sendResponse({ status: "triggered" });
      return true;
    }
  });

})();
