import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/Providers";

export const metadata: Metadata = {
  title: "DealOS Job Manager — Intelligent Career Copilot & ATS Tracker",
  description: "Search 1,700+ verified opportunities, customize resumes with zero hallucinations, track applications, and accelerate your career.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
