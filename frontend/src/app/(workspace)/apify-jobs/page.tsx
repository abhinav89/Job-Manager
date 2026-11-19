"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  Radar,
  Briefcase,
  MapPin,
  Clock,
  DollarSign,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  RotateCw,
  SlidersHorizontal,
  ChevronRight,
  Sparkles,
  Building2,
  Globe2,
  Lock,
  Layers,
  ArrowRight,
  Info,
} from "lucide-react";

import { useAuth } from "@/lib/authContext";
import { API_URL } from "@/lib/api";
import {
  useApifyProfile,
  useApifyJobs,
  useApifyAlerts,
  queryKeys,
  type ApifyJob,
  type ApifyTheme,
} from "@/lib/queries";

export default function ApifyJobsPage() {
  const { user, isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<string>("all");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isRunningScan, setIsRunningScan] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [tokenReady, setTokenReady] = useState(false);

  // Check allowlist
  const isAllowlisted = Boolean(
    user?.email && (
      user.email.toLowerCase() === "abhinava2015@email.iimcal.ac.in" ||
      user.email.toLowerCase().includes("shivangi") ||
      user.email.toLowerCase() === "abhinav"
    )
  );

  // Auto-verify and acquire server-signed HMAC token for Apify private API
  useEffect(() => {
    if (!isAuthenticated || !isAllowlisted || !user?.email) return;

    const existingToken = localStorage.getItem("dealos_apify_token");
    if (existingToken) {
      setTokenReady(true);
      return;
    }

    setIsVerifying(true);
    fetch(`${API_URL}/apify/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: user.email }),
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Authorization refused");
        }
        const data = await res.json();
        if (data.token) {
          localStorage.setItem("dealos_apify_token", data.token);
          setTokenReady(true);
          queryClient.invalidateQueries({ queryKey: queryKeys.apifyProfile });
          queryClient.invalidateQueries({ queryKey: queryKeys.apifyJobs("all") });
        }
      })
      .catch((err) => {
        console.error("Apify server verification failed:", err);
        toast.error("Could not verify Apify private access session.");
      })
      .finally(() => setIsVerifying(false));
  }, [isAuthenticated, isAllowlisted, user?.email, queryClient]);

  const profileQuery = useApifyProfile(tokenReady);
  const jobsQuery = useApifyJobs(activeTab === "all" ? undefined : activeTab, tokenReady);
  const alertsQuery = useApifyAlerts(tokenReady);

  const profile = profileQuery.data?.profile;
  const themes: ApifyTheme[] = profile?.themes || [];
  const currentTheme = themes.find((t) => t.id === activeTab);

  // Manual test scan trigger
  const handleRunManualScan = async () => {
    setIsRunningScan(true);
    try {
      const token = localStorage.getItem("dealos_apify_token");
      const res = await fetch(`${API_URL}/apify/run-now`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.telemetry?.message || "Capped Apify scan completed successfully.");
        queryClient.invalidateQueries({ queryKey: queryKeys.apifyJobs(activeTab === "all" ? undefined : activeTab) });
        queryClient.invalidateQueries({ queryKey: queryKeys.apifyProfile });
        queryClient.invalidateQueries({ queryKey: queryKeys.apifyAlerts });
      } else {
        toast.error(data.detail || "Scan request failed.");
      }
    } catch {
      toast.error("Network error while connecting to Apify engine.");
    } finally {
      setIsRunningScan(false);
    }
  };

  // Save location preferences
  const handleSaveLocation = async (mode: "hyderabad" | "all_india" | "custom_cities") => {
    try {
      const token = localStorage.getItem("dealos_apify_token");
      const res = await fetch(`${API_URL}/apify/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ location_mode: mode }),
      });
      if (res.ok) {
        toast.success("Location filter updated.");
        setShowLocationModal(false);
        queryClient.invalidateQueries({ queryKey: queryKeys.apifyProfile });
        queryClient.invalidateQueries({ queryKey: queryKeys.apifyJobs(activeTab === "all" ? undefined : activeTab) });
      }
    } catch {
      toast.error("Could not update location preferences.");
    }
  };

  // Unauthorized screen
  if (!isAuthenticated || !isAllowlisted) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 p-8 text-center space-y-4 shadow-sm">
          <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center mx-auto border border-amber-200">
            <Lock className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Private Executive Access</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            The Apify Scheduled Match engine is an isolated executive feature provisioned exclusively for{" "}
            <strong>Abhinav Agrawal</strong> and <strong>Shivangi</strong>.
          </p>
          <div className="p-3.5 bg-slate-50 rounded-2xl text-[11px] text-slate-600 font-medium border border-slate-100">
            Please sign in with your verified executive DealOS credentials to access this workspace.
          </div>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center w-full px-4 py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 transition-colors"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const hyderabadMatches: ApifyJob[] = jobsQuery.data?.hyderabad_matches || [];
  const otherIndiaMatches: ApifyJob[] = jobsQuery.data?.other_india_matches || [];
  const allMatches: ApifyJob[] = jobsQuery.data?.all_matches || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Top Header & Executive Telemetry ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
              <Radar className="w-3.5 h-3.5 animate-pulse" />
              Private Scheduled Feeder · Apify LinkedIn Actor
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Apify Job Matches
            </h1>
            <p className="text-xs text-slate-500 max-w-2xl leading-relaxed">
              Automated twice-daily LinkedIn executive scraping matching your verified career themes. Strictly capped
              at 5 postings per run to stay 100% within the free plan.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => setShowLocationModal(true)}
              className="px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs inline-flex items-center gap-1.5 transition-colors"
            >
              <MapPin className="w-3.5 h-3.5 text-blue-600" />
              Location:{" "}
              <span className="text-slate-900 capitalize">
                {profile?.location_mode?.replace("_", " ") || "Hyderabad"}
              </span>
            </button>

            <button
              type="button"
              disabled={isRunningScan}
              onClick={handleRunManualScan}
              className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs inline-flex items-center gap-1.5 transition-all shadow-xs disabled:opacity-50"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isRunningScan ? "animate-spin" : ""}`} />
              {isRunningScan ? "Scraping (Max 5)..." : "Run Test Scan"}
            </button>
          </div>
        </div>

        {/* ── Executive Benchmark & Guardrails Banner ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-slate-100">
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
              <DollarSign className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Personal Compensation Target
              </div>
              <div className="text-xs font-black text-slate-800">
                {profile?.compensation_target || profile?.compensation_benchmark || "₹60–95 LPA"}
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Apify Free Plan Budget
              </div>
              <div className="text-xs font-black text-emerald-700">
                Safe &lt; $5.00/mo cap · 5 jobs / run
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Automated Schedule
              </div>
              <div className="text-xs font-black text-slate-800">
                Daily at 6:00 AM & 6:00 PM IST
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Theme Navigation Tabs ── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Filter Opportunities by Theme
          </div>
          <Link
            href="/generate?tab=original"
            className="text-xs font-bold text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
          >
            <FileText className="w-3.5 h-3.5" />
            Manage Resumes in My Resumes →
          </Link>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("all")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === "all"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-white text-slate-600 border border-slate-200 hover:border-slate-300"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            All Matches ({allMatches.length})
          </button>

          {themes.map((t) => {
            const isSelected = activeTab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  isSelected
                    ? "bg-blue-600 text-white shadow-xs"
                    : "bg-white text-slate-600 border border-slate-200 hover:border-slate-300"
                }`}
              >
                <span>{t.name}</span>
                {t.status === "Resume needed" ? (
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                ) : (
                  <span className="text-[10px] opacity-75 font-mono">
                    {t.active_resume_version || "v1"}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Specific Theme Header Banner (when a single theme is selected) ── */}
      {currentTheme && (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Active Theme:
              </span>
              <span className="text-sm font-black text-slate-900">{currentTheme.name}</span>
            </div>
            <div className="text-xs text-slate-500 flex flex-wrap items-center gap-3">
              <span>
                Active Resume:{" "}
                <strong className="text-slate-700">
                  {currentTheme.active_resume_filename || "None"} ({currentTheme.active_resume_version || "v1"})
                </strong>
              </span>
              <span>•</span>
              <span>
                Last Searched:{" "}
                <span className="text-slate-700 font-mono">
                  {currentTheme.last_searched || "Not searched yet"}
                </span>
              </span>
            </div>
          </div>

          <Link
            href="/generate?tab=original"
            className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 hover:border-slate-300 text-slate-700 font-bold text-xs inline-flex items-center gap-1.5 shadow-2xs shrink-0"
          >
            <FileText className="w-3.5 h-3.5 text-blue-600" />
            Switch Resume Version
          </Link>
        </div>
      )}

      {/* ── Jobs Display: Ranked Shortlists ── */}
      {activeTab === "all" ? (
        <div className="space-y-8">
          {/* Section 1: Hyderabad Ranked Shortlist (Up to 5) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <h2 className="text-base font-extrabold text-slate-900">
                  📍 Hyderabad Opportunities (Ranked Shortlist · Up to 5)
                </h2>
              </div>
              <span className="text-xs font-bold text-slate-400">
                {hyderabadMatches.length} openings found
              </span>
            </div>

            {hyderabadMatches.length === 0 ? (
              <div className="bg-white rounded-2xl border border-dashed border-slate-200 p-8 text-center text-xs text-slate-400">
                No Hyderabad matches recorded yet in current batch. They will appear here after the scheduled scrape.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {hyderabadMatches.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            )}
          </div>

          {/* Section 2: Other Selected Indian Cities & Remote (Up to 1 now, configurable to 5) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <h2 className="text-base font-extrabold text-slate-900">
                  🌐 Other Indian Cities & Remote Opportunities (Up to 1)
                </h2>
              </div>
              <span className="text-xs font-bold text-slate-400">
                {otherIndiaMatches.length} openings found
              </span>
            </div>

            {otherIndiaMatches.length === 0 ? (
              <div className="bg-white rounded-2xl border border-dashed border-slate-200 p-8 text-center text-xs text-slate-400">
                No external city or remote matches in this run.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {otherIndiaMatches.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Single Theme Filtered View */
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <h2 className="text-base font-extrabold text-slate-900">
              Matches for {currentTheme?.name}
            </h2>
            <span className="text-xs font-bold text-slate-400">
              {allMatches.length} qualified matches
            </span>
          </div>

          {allMatches.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3">
              <div className="w-12 h-12 bg-slate-50 text-slate-400 rounded-2xl flex items-center justify-center mx-auto">
                <Briefcase className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-extrabold text-slate-800">No Matching Jobs Yet</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                The crawler rotates through themes during the daily 6 AM and 6 PM runs. You can also click{" "}
                <strong>Run Test Scan</strong> above.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {allMatches.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Location Modal ── */}
      {showLocationModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-md w-full p-6 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-extrabold text-slate-900">Location Preferences</h3>
              <button
                type="button"
                onClick={() => setShowLocationModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕ Close
              </button>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Saved preferences are sent as Apify query terms and strictly re-verified against returned listings.
            </p>

            <div className="space-y-2">
              {[
                { id: "hyderabad", label: "Hyderabad only (Strict)", desc: "Excludes jobs outside Hyderabad & Telangana" },
                { id: "all_india", label: "Anywhere in India", desc: "Includes all verified metros & nationwide roles" },
                { id: "custom_cities", label: "Choose cities", desc: "Hyderabad, Bengaluru, Pune, Mumbai, Delhi NCR" },
              ].map((loc) => (
                <button
                  key={loc.id}
                  type="button"
                  onClick={() => handleSaveLocation(loc.id as any)}
                  className={`w-full p-3.5 rounded-2xl border text-left transition-all ${
                    profile?.location_mode === loc.id
                      ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/10"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="text-xs font-extrabold text-slate-800">{loc.label}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{loc.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Reusable Executive Job Card ──
function JobCard({ job }: { job: ApifyJob }) {
  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs hover:border-blue-400 transition-all flex flex-col justify-between space-y-4 group">
      <div className="space-y-3">
        {/* Badges Header */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            {job.theme_matches?.map((tm) => (
              <span
                key={tm.theme_id}
                className="px-2.5 py-0.5 rounded-lg bg-blue-50 text-blue-700 text-[10px] font-black uppercase tracking-wider border border-blue-200"
              >
                {tm.theme_name}
              </span>
            ))}
          </div>
          <span className="text-[10px] font-bold text-slate-400">
            {job.posting_date || "Recent"}
          </span>
        </div>

        {/* Title & Employer */}
        <div>
          <h3 className="text-base font-extrabold text-slate-900 group-hover:text-blue-700 transition-colors">
            {job.title}
          </h3>
          <div className="text-xs font-bold text-slate-600 flex items-center gap-1.5 mt-1">
            <Building2 className="w-3.5 h-3.5 text-slate-400" />
            <span>{job.company}</span>
          </div>
        </div>

        {/* Location & Pay Pills */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold text-slate-600">
          <span className="px-2.5 py-1 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-1">
            <MapPin className="w-3 h-3 text-slate-400" />
            {job.location}
          </span>
          <span className="px-2.5 py-1 rounded-xl bg-slate-50 border border-slate-200">
            {job.work_mode || "Onsite"}
          </span>
          <span className="px-2.5 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-500">
            Advertised Pay: <strong>{job.advertised_pay || "Undisclosed"}</strong>
          </span>
        </div>

        {/* Why it Fits Box */}
        <div className="p-3.5 rounded-2xl bg-emerald-50/60 border border-emerald-200/80 text-xs text-emerald-950 space-y-1">
          <div className="text-[10px] font-black uppercase tracking-wider text-emerald-800 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-emerald-600" />
            Why It Fits Your Profile
          </div>
          <p className="text-[11px] leading-relaxed text-emerald-900">
            {job.why_it_fits}
          </p>
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[10px] font-bold text-slate-400">
          Apify LinkedIn Scraper
        </span>
        <a
          href={job.job_url}
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-xs transition-colors"
        >
          <span>Apply on LinkedIn</span>
          <ExternalLink className="w-3.5 h-3.5 text-slate-300" />
        </a>
      </div>
    </div>
  );
}
