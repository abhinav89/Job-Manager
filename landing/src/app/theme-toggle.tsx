"use client";

import { useEffect, useRef } from "react";
import { Moon, Sun } from "lucide-react";

const STORAGE_KEY = "cv-tailor-theme";

export default function ThemeToggle() {
  const chosenThisVisit = useRef(false);

  useEffect(() => {
    const preference = window.matchMedia("(prefers-color-scheme: dark)");
    function followSystem() {
      if (chosenThisVisit.current) return;
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === "light" || saved === "dark") return;
      } catch { /* Theme switching also works when storage is unavailable. */ }
      document.documentElement.dataset.theme = preference.matches ? "dark" : "light";
    }
    preference.addEventListener("change", followSystem);
    return () => preference.removeEventListener("change", followSystem);
  }, []);

  function toggle() {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    chosenThisVisit.current = true;
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(STORAGE_KEY, theme); } catch { /* Keep the choice for this visit. */ }
  }

  return (
    <button className="theme-toggle" type="button" onClick={toggle} title="Toggle color theme">
      <Moon size={17} className="light-theme-content" aria-hidden="true" />
      <Sun size={17} className="dark-theme-content" aria-hidden="true" />
      <span className="sr-only light-theme-content">Switch to dark mode</span>
      <span className="sr-only dark-theme-content">Switch to light mode</span>
    </button>
  );
}
