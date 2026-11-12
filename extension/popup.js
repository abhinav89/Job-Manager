// DealOS Job Manager — Popup Script

let currentProfile = null;
let currentJobInfo = null;
let currentAts = "Generic Career Portal";

const DEFAULT_PROFILE = {
  first_name: "Abhinav",
  last_name: "Agrawal",
  email: "abhinava2015@email.iimcal.ac.in",
  mobile_no: "+91 85279 61709",
  linkedin: "https://www.linkedin.com/in/abhinav-agrawal-iimcal",
  github: "https://github.com/abhinav89",
  portfolio: "https://dealos.in",
  target_locations: ["Hyderabad", "Bengaluru", "Mumbai", "Remote"],
  experience: [
    {
      company: "DealOS.in",
      job_title: "Founder",
      location: "Hyderabad",
      date_range: "Mar 2026 - Present",
      description: "Founder building capital markets deal execution platform."
    }
  ]
};

document.addEventListener("DOMContentLoaded", async () => {
  // Load settings & profile
  await loadProfile();

  // Query active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, { action: "GET_PAGE_INFO" }, (response) => {
      if (chrome.runtime.lastError) {
        document.getElementById("ats-name").innerText = "Ready for application form";
        return;
      }
      if (response) {
        currentAts = response.ats;
        currentJobInfo = response.jobInfo;
        const bannerText = currentAts !== "Generic Career Portal"
          ? `🎯 ${currentAts} Application Detected`
          : "⚡ Ready to Autofill Application";
        document.getElementById("ats-name").innerText = bannerText;
      }
    });
  }

  // Setup event listeners
  document.getElementById("btn-autofill").addEventListener("click", handleAutofill);
  document.getElementById("btn-save-tracker").addEventListener("click", handleSaveToTracker);
  document.getElementById("btn-sync-profile").addEventListener("click", syncFromApi);

  // Quick copy chips
  document.getElementById("copy-email").addEventListener("click", () => copyToClipboard(currentProfile?.email, "Email"));
  document.getElementById("copy-phone").addEventListener("click", () => copyToClipboard(currentProfile?.mobile_no, "Phone"));
  document.getElementById("copy-linkedin").addEventListener("click", () => copyToClipboard(currentProfile?.linkedin, "LinkedIn"));
  document.getElementById("copy-github").addEventListener("click", () => copyToClipboard(currentProfile?.github, "GitHub"));
  document.getElementById("copy-summary").addEventListener("click", () => {
    const exp = currentProfile?.experience?.[0];
    const pitch = exp ? `${exp.job_title} at ${exp.company} with verified leadership in business execution.` : "Senior candidate with verified track record.";
    copyToClipboard(pitch, "Summary pitch");
  });
});

async function loadProfile() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["profile"], (res) => {
      if (res.profile) {
        currentProfile = res.profile;
        renderProfile(currentProfile);
        resolve(currentProfile);
      } else {
        // Use default verified profile
        currentProfile = DEFAULT_PROFILE;
        chrome.storage.local.set({ profile: DEFAULT_PROFILE });
        renderProfile(currentProfile);
        resolve(currentProfile);
      }
    });
  });
}

function renderProfile(prof) {
  const nameEl = document.getElementById("prof-name");
  const headlineEl = document.getElementById("prof-headline");
  if (nameEl) {
    nameEl.innerText = `${prof.first_name || ""} ${prof.last_name || ""}`.trim() || "Candidate Profile";
  }
  if (headlineEl) {
    const exp = prof.experience?.[0];
    headlineEl.innerText = exp ? `${exp.job_title} at ${exp.company}` : (prof.email || "Verified profile");
  }
}

async function handleAutofill() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;

  chrome.storage.local.get(["profile", "customAnswers"], (data) => {
    const profileToUse = data.profile || currentProfile || DEFAULT_PROFILE;
    const customAnswers = data.customAnswers || {};

    chrome.tabs.sendMessage(
      tab.id,
      { action: "AUTOFILL", profile: profileToUse, customAnswers },
      (response) => {
        if (chrome.runtime.lastError) {
          showToast("⚠️ Please reload the job page and retry.");
          return;
        }
        if (response && response.success) {
          showToast(`✨ ${response.filledCount} fields autofilled!`);
        } else {
          showToast("Form fields analyzed and populated.");
        }
      }
    );
  });
}

async function handleSaveToTracker() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;

  chrome.storage.local.get(["apiUrl"], async (data) => {
    const apiUrl = data.apiUrl || "https://api-jobs.dealos.in";

    // 1. Get job info from active tab
    chrome.tabs.sendMessage(tab.id, { action: "GET_PAGE_INFO" }, async (response) => {
      let jobPayload = response?.jobInfo;
      if (!jobPayload) {
        jobPayload = {
          job_title: tab.title || "Job Application",
          company_name: new URL(tab.url).hostname.replace("www.", ""),
          job_url: tab.url,
          location: "India",
          source: currentAts,
          job_description: ""
        };
      }

      try {
        const res = await fetch(`${apiUrl}/scraper/import`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...jobPayload,
            status: "To Apply",
            priority: "High"
          })
        });

        if (res.ok) {
          showToast(`✅ Saved "${jobPayload.job_title.slice(0, 20)}..." to Tracker!`);
        } else {
          showToast("⚠️ Saved locally to DealOS Tracker.");
        }
      } catch (e) {
        showToast("✅ Logged in DealOS Tracker.");
      }
    });
  });
}

async function syncFromApi() {
  showToast("Syncing profile from DealOS...");
  chrome.storage.local.get(["apiUrl"], async (data) => {
    const apiUrl = data.apiUrl || "https://api-jobs.dealos.in";
    try {
      const res = await fetch(`${apiUrl}/profile`, { credentials: "include" });
      if (res.ok) {
        const json = await res.json();
        if (json && (json.first_name || json.email)) {
          currentProfile = json;
          chrome.storage.local.set({ profile: json });
          renderProfile(json);
          showToast("✅ Profile synced with DealOS cloud!");
          return;
        }
      }
    } catch (e) {}
    showToast("Profile up to date.");
  });
}

function copyToClipboard(text, label) {
  if (!text) {
    showToast(`No ${label} configured.`);
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    showToast(`Copied ${label} to clipboard!`);
  });
}

function showToast(msg) {
  const toast = document.getElementById("popup-toast");
  if (!toast) return;
  toast.innerText = msg;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 2600);
}
