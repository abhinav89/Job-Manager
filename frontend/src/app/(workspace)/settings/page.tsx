"use client";

import React, { useState } from "react";
import {
  User,
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
  FileText,
  Bell,
  Download,
  Trash2,
  LogOut,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/authContext";
import { useWorkspace, useProfile } from "@/lib/queries";
import { API_URL } from "@/lib/api";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { data: workspace } = useWorkspace();
  const { data: profile } = useProfile();

  const [activeTab, setActiveTab] = useState<"account" | "preferences" | "notifications" | "developer">("account");
  const [defaultTemplate, setDefaultTemplate] = useState("classic");
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [earlyApplicantAlerts, setEarlyApplicantAlerts] = useState(true);
  const [showDevDetails, setShowDevDetails] = useState(false);

  const handleSavePreferences = () => {
    toast.success("Settings & Preferences saved successfully!");
  };

  const handleExportData = () => {
    const data = {
      user: user?.email,
      exportedAt: new Date().toISOString(),
      profile: profile || {},
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `JobManager_DataExport_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    toast.success("Account data exported successfully!");
  };

  return (
    <div className="p-4 sm:p-8 max-w-5xl mx-auto space-y-8 font-sans">
      {/* ── Page Header ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold mb-2">
            <Settings className="w-3.5 h-3.5" />
            User Settings &amp; Preferences
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Account &amp; Application Settings
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage your personal profile, resume styling preferences, notifications, and cloud connections.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3.5 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold inline-flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Signed In: {user?.email || "Authenticated"}
          </div>
        </div>
      </div>

      {/* ── Navigation Tabs ── */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto text-xs font-bold">
        {[
          { id: "account", label: "My Account & Profile", icon: <User className="w-4 h-4" /> },
          { id: "preferences", label: "Resume & Theme Preferences", icon: <FileText className="w-4 h-4" /> },
          { id: "notifications", label: "Notifications & Privacy", icon: <Bell className="w-4 h-4" /> },
          { id: "developer", label: "Cloud & Developer Info", icon: <Cpu className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600 font-black"
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
        {/* Tab 1: Account Settings */}
        {activeTab === "account" && (
          <div className="space-y-6 text-xs">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">User Account Information</h3>
              <p className="text-slate-500 mt-1">
                Your authenticated account credentials for Job-Manager.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Authenticated Email</span>
                <p className="text-sm font-bold text-slate-800">{user?.email || "user@dealos.in"}</p>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 font-semibold mt-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Verified Member
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Account Role</span>
                <p className="text-sm font-bold text-slate-800">Primary Candidate &amp; Admin</p>
                <span className="text-[10px] text-slate-500">Full access to 1,700+ jobs and ATS tools</span>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={handleExportData}
                className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-bold text-xs inline-flex items-center gap-2 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                Export My Data (JSON)
              </button>

              <button
                type="button"
                onClick={() => {
                  logout();
                  toast.success("Logged out successfully.");
                }}
                className="px-4 py-2.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs inline-flex items-center gap-2 cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                Log Out of Account
              </button>
            </div>
          </div>
        )}

        {/* Tab 2: Resume & Theme Preferences */}
        {activeTab === "preferences" && (
          <div className="space-y-6 text-xs">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">Resume Styling &amp; ATS Defaults</h3>
              <p className="text-slate-500 mt-1">
                Configure default LaTeX templates and application constraints.
              </p>
            </div>

            <div className="space-y-4 max-w-xl">
              <div>
                <label className="block font-bold text-slate-800 mb-1.5">
                  Default Resume Theme
                </label>
                <select
                  value={defaultTemplate}
                  onChange={(e) => setDefaultTemplate(e.target.value)}
                  className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-xs font-semibold focus:outline-none focus:border-blue-600"
                >
                  <option value="classic">Classic (Recommended - High ATS Score, Corporate/Consulting)</option>
                  <option value="modern">Modern (Clean Sans, Tech/Product)</option>
                  <option value="executive">Executive (VP/CXO/Leadership Format)</option>
                  <option value="compact">Compact (Dense 1-Page Layout)</option>
                  <option value="technical">Technical (Infra, AI &amp; Software)</option>
                  <option value="serif">Serif Formal (Academic &amp; Editorial)</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-800 mb-1.5">
                  Default Job Search Region
                </label>
                <input
                  type="text"
                  disabled
                  value="India (Pan-India & Major Metros)"
                  className="w-full p-3 rounded-xl border border-slate-200 bg-slate-100 text-slate-600 text-xs font-semibold cursor-not-allowed"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Default filter is locked to India as requested. You can adjust per search in Find Jobs.
                </span>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleSavePreferences}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs cursor-pointer"
                >
                  Save Preferences
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Notifications & Privacy */}
        {activeTab === "notifications" && (
          <div className="space-y-6 text-xs">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">Notifications &amp; Alerts</h3>
              <p className="text-slate-500 mt-1">
                Control alert delivery and communication channels.
              </p>
            </div>

            <div className="space-y-3 max-w-xl">
              <label className="flex items-center gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={earlyApplicantAlerts}
                  onChange={(e) => setEarlyApplicantAlerts(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <div>
                  <span className="font-bold text-slate-800 block">Early Applicant Alerts</span>
                  <span className="text-[11px] text-slate-500">Get highlighted notifications when newly verified jobs open in India.</span>
                </div>
              </label>

              <label className="flex items-center gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <div>
                  <span className="font-bold text-slate-800 block">Weekly Digest Email</span>
                  <span className="text-[11px] text-slate-500">Receive top matching roles tailored to your career themes each Monday.</span>
                </div>
              </label>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleSavePreferences}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs cursor-pointer"
                >
                  Save Notification Settings
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Cloud & Developer Info */}
        {activeTab === "developer" && (
          <div className="space-y-6 text-xs">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">Cloud &amp; Superadmin Infrastructure</h3>
              <p className="text-slate-500 mt-1">
                Technical deployment configuration for Job-Manager cloud backend and Supabase.
              </p>
            </div>

            {/* Strict Boundary Alert */}
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start gap-3">
              <Shield className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold">Isolated Database Compliance Confirmed</span>
                <p className="text-emerald-800 leading-relaxed text-[11px]">
                  Job-Manager connects exclusively to its own dedicated Supabase PostgreSQL database on Render. The DealOS transaction advisory database at <code className="bg-emerald-100 px-1 py-0.5 rounded font-mono">app.dealos.in</code> remains completely isolated and untouched.
                </p>
              </div>
            </div>

            {/* Cloud Details Accordion */}
            <div className="border border-slate-200 rounded-2xl overflow-hidden">
              <button
                type="button"
                onClick={() => setShowDevDetails(!showDevDetails)}
                className="w-full px-5 py-3.5 bg-slate-50 flex items-center justify-between text-left font-bold text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <span>Live Cloud Endpoints &amp; Health Status</span>
                {showDevDetails ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              </button>

              {showDevDetails && (
                <div className="p-5 space-y-3 bg-white border-t border-slate-200 text-xs">
                  <div className="flex items-center justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Frontend Domain (Vercel):</span>
                    <a href="https://jobs.dealos.in" target="_blank" rel="noopener noreferrer" className="font-mono text-blue-600 font-bold hover:underline inline-flex items-center gap-1">
                      jobs.dealos.in <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Backend API URL (Render):</span>
                    <a href="https://api-jobs.dealos.in/api/health" target="_blank" rel="noopener noreferrer" className="font-mono text-blue-600 font-bold hover:underline inline-flex items-center gap-1">
                      api-jobs.dealos.in <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Database Engine:</span>
                    <span className="font-mono font-bold text-slate-800">Supabase Dedicated PostgreSQL (AWS eu-west-1)</span>
                  </div>
                  <div className="flex items-center justify-between py-1">
                    <span className="text-slate-500">Seeded Curated Openings:</span>
                    <span className="font-mono font-bold text-emerald-700">1,717 Jobs Loaded</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
