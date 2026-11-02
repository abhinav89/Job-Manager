import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CV Tailor — Your open-source career workspace",
  description: "An MIT-licensed, open-source career workspace. Tailor CVs, track applications, and prepare for interviews with your AI agent, a local CLI, and an optional dashboard.",
  metadataBase: new URL("https://cvtailor.me"),
  alternates: { canonical: "/" },
  openGraph: {
    title: "CV Tailor — Your open-source career workspace",
    description: "Open source. Your agent. Your applications. One local career workspace, with an optional visual dashboard.",
    url: "https://cvtailor.me", type: "website", siteName: "CV Tailor",
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{ __html: `
    (() => {
      let saved;
      try { saved = localStorage.getItem("cv-tailor-theme"); } catch {}
      document.documentElement.dataset.theme = saved === "dark" || saved === "light"
        ? saved : window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    })();
  ` }} /></head><body>{children}</body></html>;
}
