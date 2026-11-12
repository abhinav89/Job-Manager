// DealOS Job Manager — Background Service Worker

const DEFAULT_SETTINGS = {
  apiUrl: "https://api-jobs.dealos.in",
  webUrl: "https://jobs.dealos.in",
  authorizedToWork: "Yes",
  requiresSponsorship: "No",
  noticePeriod: "30 Days",
  preferredSalary: "Competitive / Market standard"
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(Object.keys(DEFAULT_SETTINGS), (result) => {
    const toStore = {};
    for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
      if (result[key] === undefined) {
        toStore[key] = value;
      }
    }
    if (Object.keys(toStore).length > 0) {
      chrome.storage.local.set(toStore);
    }
  });

  // Create context menu for quick autofill
  chrome.contextMenus.create({
    id: "dealos-autofill",
    title: "⚡ DealOS: Autofill Application",
    contexts: ["page", "editable"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "dealos-autofill" && tab?.id) {
    chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" }, () => {
      if (chrome.runtime.lastError) {
        // Content script might not be loaded yet, inject it
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"]
        }, () => {
          chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" });
        });
      }
    });
  }
});
