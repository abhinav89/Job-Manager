// DealOS Extension Options Script

document.addEventListener("DOMContentLoaded", () => {
  const fields = ["apiUrl", "authorizedToWork", "requiresSponsorship", "noticePeriod", "preferredSalary"];

  chrome.storage.local.get(fields, (items) => {
    if (items.apiUrl) document.getElementById("apiUrl").value = items.apiUrl;
    if (items.authorizedToWork) document.getElementById("authorizedToWork").value = items.authorizedToWork;
    if (items.requiresSponsorship) document.getElementById("requiresSponsorship").value = items.requiresSponsorship;
    if (items.noticePeriod) document.getElementById("noticePeriod").value = items.noticePeriod;
    if (items.preferredSalary) document.getElementById("preferredSalary").value = items.preferredSalary;
  });

  document.getElementById("save-btn").addEventListener("click", () => {
    const toSave = {
      apiUrl: document.getElementById("apiUrl").value.trim() || "https://api-jobs.dealos.in",
      authorizedToWork: document.getElementById("authorizedToWork").value,
      requiresSponsorship: document.getElementById("requiresSponsorship").value,
      noticePeriod: document.getElementById("noticePeriod").value.trim() || "30 Days",
      preferredSalary: document.getElementById("preferredSalary").value.trim() || "Competitive / Market standard",
      customAnswers: {
        authorizedToWork: document.getElementById("authorizedToWork").value,
        requiresSponsorship: document.getElementById("requiresSponsorship").value,
        noticePeriod: document.getElementById("noticePeriod").value.trim(),
        preferredSalary: document.getElementById("preferredSalary").value.trim()
      }
    };

    chrome.storage.local.set(toSave, () => {
      const toast = document.getElementById("toast");
      toast.style.display = "block";
      setTimeout(() => {
        toast.style.display = "none";
      }, 3000);
    });
  });
});
