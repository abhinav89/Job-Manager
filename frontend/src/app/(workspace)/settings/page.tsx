"use client";

import React, { useState } from "react";
import {
  Settings,
  Shield,
  Key,
  Globe,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Cpu,
  Lock,
  Layers,
} from "lucide-react";
import { useWorkspace } from "@/lib/queries";

export default function SettingsPage() {
  const { data: workspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState<"auth" | "ai" | "plans" | "domain">("auth");

  return (
    <div className="p-4 sm:p-8 max-w-5xl mx-auto space-y-8 font-sans">
      {/* ── Page Header ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2">
            <Settings className="w-3.5 h-3.5" />
            Environment &amp; Architecture
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Settings &amp; Connections
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Configure authentication, cloud project credentials, AI providers, and tier limits.
          </p>
        </div>

        <div className="px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold inline-flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Local Mode Active
        </div>
      </div>

      {/* ── Tabs Navigation ── */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto text-xs font-semibold">
        {[
          { id: "auth", label: "Authentication & Supabase", icon: <Shield className="w-4 h-4" /> },
          { id: "ai", label: "AI Provider & Engine", icon: <Cpu className="w-4 h-4" /> },
          { id: "plans", label: "Tier Quotas & Pricing", icon: <Layers className="w-4 h-4" /> },
          { id: "domain", label: "Domain & Hosting (dealos.in)", icon: <Globe className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-3 px-3.5 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        {/* Authentication & Supabase */}
        {activeTab === "auth" && (
          <div className="space-y-6 text-xs">
            <div className="border-b pb-4">
              <h3 className="text-base font-bold text-slate-900">Authentication &amp; Supabase Project</h3>
              <p className="text-slate-500 mt-1">
                Job-Manager runs in secure local mode initially. When ready for hosted multi-user deployment, connect a separate development Supabase project.
              </p>
            </div>

            {/* Strict Boundary Alert */}
            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3">
              <Lock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold">Production Project Isolation Rule</span>
                <p className="text-amber-800 leading-relaxed">
                  Your transaction advisory app at <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono">app.dealos.in</code> uses its own Supabase project. Job-Manager will NEVER connect to, alter, or reuse that project. When hosted mode is configured, a distinct Job-Manager project will be utilized.
                </p>
              </div>
            </div>

            <div className="space-y-4 pt-2">
              <h4 className="font-bold text-slate-800 text-sm">Supabase &amp; Google OAuth Environment Variables</h4>
              <p className="text-slate-500">
                To enable hosted Google sign-in, add these variables to your local <code className="bg-slate-100 px-1 py-0.5 rounded">.env</code> file (which is git-ignored):
              </p>

              <div className="p-4 rounded-xl bg-slate-900 text-slate-200 font-mono text-[11px] space-y-1 leading-relaxed">
                <div># Separate Job-Manager Supabase Project</div>
                <div>NEXT_PUBLIC_SUPABASE_URL=https://your-job-manager-project.supabase.co</div>
                <div>NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...</div>
                <div className="pt-2"># Google Cloud OAuth Credentials</div>
                <div>GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com</div>
                <div>GOOGLE_CLIENT_SECRET=GOCSPX-...</div>
              </div>

              <div className="pt-2 text-slate-500 leading-relaxed">
                <strong>Google Cloud Console Setup Steps:</strong>
                <ol className="list-decimal list-inside space-y-1 mt-1 pl-1">
                  <li>In Google Cloud Console, navigate to <em>APIs &amp; Services → Credentials</em>.</li>
                  <li>Create OAuth 2.0 Client ID (Web Application).</li>
                  <li>Set Authorized Redirect URI to: <code className="bg-slate-100 px-1 rounded">https://&lt;your-project&gt;.supabase.co/auth/v1/callback</code>.</li>
                  <li>In Supabase Dashboard, go to <em>Authentication → Providers → Google</em> and enable Google provider with the Client ID and Secret.</li>
                </ol>
              </div>
            </div>
          </div>
        )}

        {/* AI Provider */}
        {activeTab === "ai" && (
          <div className="space-y-6 text-xs">
            <div className="border-b pb-4">
              <h3 className="text-base font-bold text-slate-900">AI Intelligence Provider</h3>
              <p className="text-slate-500 mt-1">
                Controls the LLM engine for CV tailoring, spot editing, and structured profile parsing.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl border-2 border-blue-600 bg-blue-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">Google Gemini (Recommended)</span>
                  <span className="text-[10px] font-bold bg-blue-600 text-white px-2 py-0.5 rounded-full">Default</span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  Utilizes <code className="font-mono bg-blue-100 px-1 rounded">gemini-2.0-flash</code> for high-speed resume structuring, LaTeX assembly, and ATS keyword extraction.
                </p>
                <div className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1 pt-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Fast generation &amp; JSON schema support
                </div>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">OpenAI</span>
                  <span className="text-[10px] font-semibold text-slate-500">Alternative</span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  Supports <code className="font-mono bg-slate-200 px-1 rounded">gpt-4o-mini</code> or custom OpenAI-compatible base URLs.
                </p>
                <div className="text-[11px] font-semibold text-slate-600 pt-1">
                  Optional provider via OPENAI_API_KEY
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-800">Heuristic Engine Status</h4>
              <p className="text-slate-600 leading-relaxed">
                When an external AI key is omitted or undergoing rate limits, the built-in <strong>Heuristic Rule Engine</strong> automatically extracts resume sections, computes match scores, and compiles resumes with zero external dependencies.
              </p>
            </div>
          </div>
        )}

        {/* Tier Quotas & Pricing */}
        {activeTab === "plans" && (
          <div className="space-y-6 text-xs">
            <div className="border-b pb-4">
              <h3 className="text-base font-bold text-slate-900">Subscription Tiers &amp; Restrictions</h3>
              <p className="text-slate-500 mt-1">
                Standard application tiers. Prepared for future commercial capabilities.
              </p>
            </div>

            {/* Current Quota Status */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400">AI Tailored Resumes</span>
                <div className="text-xl font-black text-slate-900">1 of 1 Left</div>
                <div className="text-[10px] text-slate-500">Free tier allows 1 job-specific tailored resume</div>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400">ATS Checks</span>
                <div className="text-xl font-black text-slate-900">5 of 5 Left</div>
                <div className="text-[10px] text-slate-500">Free tier allows 5 ATS format validations</div>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400">Active Plan</span>
                <div className="text-xl font-black text-blue-600">Free Plan (₹0)</div>
                <div className="text-[10px] text-slate-500">Development / Local mode</div>
              </div>
            </div>

            {/* Benchmark Feature Table */}
            <div className="border border-slate-200 rounded-2xl overflow-hidden mt-4">
              <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200 font-bold text-slate-700">
                  <tr>
                    <th className="p-3.5">Feature</th>
                    <th className="p-3.5 w-36 text-center">Free Plan (₹0)</th>
                    <th className="p-3.5 w-36 text-center text-blue-700">Pro Plan (₹733/mo)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  <tr>
                    <td className="p-3.5 font-medium">Job discovery &amp; repository feed</td>
                    <td className="p-3.5 text-center font-bold text-emerald-700">Unlimited</td>
                    <td className="p-3.5 text-center font-bold text-emerald-700">Unlimited</td>
                  </tr>
                  <tr>
                    <td className="p-3.5 font-medium">AI job tailored resumes</td>
                    <td className="p-3.5 text-center">1 resume</td>
                    <td className="p-3.5 text-center font-bold text-blue-700">Unlimited</td>
                  </tr>
                  <tr>
                    <td className="p-3.5 font-medium">ATS score checks &amp; fixes</td>
                    <td className="p-3.5 text-center">5 checks</td>
                    <td className="p-3.5 text-center font-bold text-blue-700">Unlimited</td>
                  </tr>
                  <tr>
                    <td className="p-3.5 font-medium">Resume templates access</td>
                    <td className="p-3.5 text-center">Classic + Modern</td>
                    <td className="p-3.5 text-center font-bold text-blue-700">All 8 Templates</td>
                  </tr>
                  <tr>
                    <td className="p-3.5 font-medium">Application Master Sheet Export (Excel / CSV)</td>
                    <td className="p-3.5 text-center font-bold text-emerald-700">Included</td>
                    <td className="p-3.5 text-center font-bold text-emerald-700">Included</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Domain & Hosting (dealos.in) */}
        {activeTab === "domain" && (
          <div className="space-y-6 text-xs">
            <div className="border-b pb-4">
              <h3 className="text-base font-bold text-slate-900">Custom Domain &amp; Production Hosting</h3>
              <p className="text-slate-500 mt-1">
                Target production endpoint: <code className="font-mono bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-bold">jobs.dealos.in</code>
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
              <h4 className="font-bold text-slate-800">Deployment Staging Checklist</h4>
              <ul className="space-y-2 text-slate-600">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Frontend is Next.js 16 (production build passes cleanly, Vercel / Cloudflare ready).</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Backend is FastAPI (can be deployed on Render, Railway, or Fly.io with Tectonic).</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>DNS: Add CNAME record pointing <code className="bg-slate-200 px-1 rounded">jobs.dealos.in</code> to the frontend host.</span>
                </li>
              </ul>
            </div>

            <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-blue-900 flex items-start gap-3">
              <HelpCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Next Steps for Production Launch:</span>
                <p className="text-blue-800 mt-1 leading-relaxed">
                  As specified in your instructions, we will review the local implementation first. Before connecting custom domains, Supabase projects, or incurring any third-party hosting costs, we will discuss together.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
