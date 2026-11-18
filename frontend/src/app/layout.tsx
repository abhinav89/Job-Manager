import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/Providers";

export const metadata: Metadata = {
  title: "DealOS Jobs — Executive Career Platform & ATS Tracker",
  description: "Access 1,700+ verified executive & engineering openings, customize ATS-proof resumes with zero hallucinations, and track applications on DealOS Jobs.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
