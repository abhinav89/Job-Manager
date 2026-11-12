"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  SlidersHorizontal,
  Plus,
  Sparkles,
  MapPin,
  Briefcase,
  ExternalLink,
  Bookmark,
  Check,
  ChevronDown,
  Building2,
  X,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import { useRepositoryJobs, useProfile } from "@/lib/queries";
import { API_URL } from "@/lib/api";
import { JobCard } from "@/components/tracker/JobCard";
import { FilterDrawer, FilterState, defaultFilterState } from "@/components/tracker/FilterDrawer";

export default function DiscoverJobsPage() {
  const router = useRouter();
  const { data: profile } = useProfile();
  const [keyword, setKeyword] = useState("");
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  const [isAddJobModalOpen, setIsAddJobModalOpen] = useState(false);
  const [filterState, setFilterState] = useState<FilterState>(defaultFilterState);

  // Manual intake state
  const [manualUrl, setManualUrl] = useState("");
  const [manualText, setManualText] = useState("");
  const [isParsingUrl, setIsParsingUrl] = useState(false);

  // Query jobs from central repository
  const { data: repoData, isLoading, refetch } = useRepositoryJobs({
    keyword: keyword || undefined,
    location: filterState.city !== "All Cities" ? filterState.city : filterState.country !== "Global / Anywhere" ? filterState.country : undefined,
    work_model: filterState.workModel !== "all" ? filterState.workModel : undefined,
    seniority: filterState.seniority !== "all" ? filterState.seniority : undefined,
    company: filterState.companyInclude || undefined,
  });

  const jobs = repoData?.jobs || [];

  const handleSaveToTracker = async (job: any, status: "To Review" | "To Apply") => {
    try {
      const res = await fetch(`${API_URL}/scraper/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: job.company_name,
          job_title: job.job_title,
          job_url: job.job_url,
          source: job.source,
          job_description: job.job_description,
          location: job.location,
          salary_range: job.salary_range,
          job_type: job.job_type,
          status,
          priority: "Medium",
          match_score: job.match_score ? Math.round(job.match_score) : null,
          match_analysis: job.match_analysis,
        }),
      });
      if (res.ok) {
        toast.success(`Saved "${job.job_title}" to Tracker under ${status}!`);
      }
    } catch {
      toast.error("Failed to save job to tracker.");
    }
  };

  const handleTailorAndApply = (job: any) => {
    handleSaveToTracker(job, "To Apply");
    router.push(`/generate?title=${encodeURIComponent(job.job_title)}&company=${encodeURIComponent(job.company_name)}`);
  };

  const handleManualIntake = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualUrl && !manualText) {
      toast.error("Please provide either a job link or description text.");
      return;
    }
    setIsParsingUrl(true);
    try {
      const res = await fetch(`${API_URL}/scraper/parse-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: manualUrl,
          job_text: manualText,
        }),
      });
      if (!res.ok) throw new Error("Could not parse job posting.");
      const json = await res.json();
      await handleSaveToTracker(json.job, "To Review");
      setIsAddJobModalOpen(false);
      setManualUrl("");
      setManualText("");
      refetch();
    } catch (err: any) {
      toast.error(err.message || "Failed to parse job.");
    } finally {
      setIsParsingUrl(false);
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6 font-sans">
      {/* ── Top Bar with Search & Add Job ── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Search by role, company, skill (e.g. Finance Manager, Deloitte, FP&A)..."
            className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-2xl text-xs sm:text-sm focus:outline-none focus:border-blue-600 shadow-xs transition-all"
          />
        </div>

        {/* Add Job by URL or Text Button */}
        <button
          type="button"
          onClick={() => setIsAddJobModalOpen(true)}
          className="px-4 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl font-semibold text-xs shadow-xs transition-all inline-flex items-center justify-center gap-2 shrink-0"
        >
          <Plus className="w-4 h-4" />
          Add Job by URL / Paste JD
        </button>
      </div>

      {/* ── Benchmark Filter Chips Bar (NextRaise Style) ── */}
      <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
        {/* Country Quick Dropdown */}
        <select
          value={filterState.country}
          onChange={(e) => setFilterState({ ...filterState, country: e.target.value })}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium text-slate-700 hover:border-slate-300 focus:outline-none cursor-pointer"
        >
          <option value="India">🇮🇳 India</option>
          <option value="United States">🇺🇸 United States</option>
          <option value="Global / Anywhere">🌐 Global / Remote</option>
        </select>

        {/* City Quick Dropdown */}
        <select
          value={filterState.city}
          onChange={(e) => setFilterState({ ...filterState, city: e.target.value })}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium text-slate-700 hover:border-slate-300 focus:outline-none cursor-pointer"
        >
          <option value="All Cities">City: All</option>
          <option value="Bengaluru">Bengaluru</option>
          <option value="Hyderabad">Hyderabad</option>
          <option value="Mumbai">Mumbai</option>
          <option value="Delhi NCR">Delhi NCR</option>
          <option value="Pune">Pune</option>
        </select>

        {/* Work Model Quick Selector */}
        <select
          value={filterState.workModel}
          onChange={(e) => setFilterState({ ...filterState, workModel: e.target.value })}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium text-slate-700 hover:border-slate-300 focus:outline-none cursor-pointer"
        >
          <option value="all">Work model: Any</option>
          <option value="Remote">Remote</option>
          <option value="Hybrid">Hybrid</option>
          <option value="Onsite">Onsite</option>
        </select>

        {/* Seniority Selector */}
        <select
          value={filterState.seniority}
          onChange={(e) => setFilterState({ ...filterState, seniority: e.target.value })}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium text-slate-700 hover:border-slate-300 focus:outline-none cursor-pointer"
        >
          <option value="all">Level: All</option>
          <option value="Senior">Senior</option>
          <option value="Mid">Mid Level</option>
          <option value="Lead / Executive">Lead / Exec</option>
        </select>

        {/* All Filters Button */}
        <button
          type="button"
          onClick={() => setIsFilterDrawerOpen(true)}
          className="px-3.5 py-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl font-semibold hover:bg-blue-100 transition-colors inline-flex items-center gap-1.5"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          All filters
        </button>

        {/* Clear Filters */}
        {(filterState.city !== "All Cities" || filterState.workModel !== "all" || filterState.seniority !== "all") && (
          <button
            type="button"
            onClick={() => setFilterState(defaultFilterState)}
            className="text-xs text-slate-500 hover:text-slate-800 underline ml-1"
          >
            Clear all
          </button>
        )}

        <div className="ml-auto text-xs font-semibold text-slate-500">
          Showing {jobs.length} verified openings
        </div>
      </div>

      {/* ── Career Themes Quick Filters ── */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
          Themes:
        </span>
        {[
          { label: "All Roles", value: "" },
          { label: "Strategy & Transformation", value: "Strategy" },
          { label: "Finance & FP&A", value: "Finance" },
          { label: "Product", value: "Product" },
          { label: "Tech & Engineering", value: "Software" },
          { label: "Enterprise Sales", value: "Sales" },
          { label: "Business Development", value: "Partnerships" },
          { label: "Operations & BizOps", value: "Operations" },
          { label: "Supply Chain", value: "Supply Chain" },
          { label: "Marketing", value: "Marketing" },
          { label: "HR & People", value: "HR" },
        ].map((t) => {
          const isActive = keyword === t.value || (!keyword && !t.value);
          return (
            <button
              key={t.label}
              type="button"
              onClick={() => setKeyword(t.value)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                isActive
                  ? "bg-blue-600 text-white shadow-2xs"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* ── Main Content Grid: Job Cards Feed + Right Summary Rail ── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Left 3 Columns: Job Cards Feed */}
        <div className="lg:col-span-3 space-y-4">
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-sm">
              <div className="w-8 h-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin mx-auto mb-3" />
              Scanning company career pages and calculating match scores...
            </div>
          ) : jobs.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3">
              <Building2 className="w-10 h-10 text-slate-400 mx-auto" />
              <h4 className="font-bold text-slate-800 text-base">No matching jobs found</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Try broadening your filters or add a direct company posting URL using &quot;Add Job by URL&quot;.
              </p>
              <button
                type="button"
                onClick={() => {
                  setKeyword("");
                  setFilterState(defaultFilterState);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold"
              >
                Reset filters
              </button>
            </div>
          ) : (
            jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onSaveToTracker={handleSaveToTracker}
                onTailorAndApply={handleTailorAndApply}
              />
            ))
          )}
        </div>

        {/* Right 1 Column: Benchmark Info Rail (Primary Resume, ATS Check, Tracked Sources) */}
        <div className="space-y-5 lg:sticky lg:top-6">
          {/* Primary Resume Card (NextRaise benchmark right rail) */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-extrabold uppercase tracking-wider text-[10px] text-slate-400">
                PRIMARY RESUME
              </span>
              <button
                type="button"
                onClick={() => router.push("/profile")}
                className="text-blue-600 font-semibold hover:underline"
              >
                Edit
              </button>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-full border-2 border-emerald-500 flex items-center justify-center font-black text-emerald-800 text-sm bg-emerald-50 shrink-0">
                78
              </div>
              <div className="min-w-0">
                <h5 className="font-bold text-slate-900 truncate">
                  {profile?.first_name ? `${profile.first_name}_${profile.last_name || ""}_CV` : "Abhinav_Agrawal_CV"}
                </h5>
                <p className="text-[11px] text-slate-500">
                  ATS Score: 78 out of 100
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => router.push("/generate")}
              className="w-full py-2.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-xs transition-colors text-center inline-flex items-center justify-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Tailor Resume for a Job
            </button>
          </div>

          {/* Master Companies Tracked Badge */}
          <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-xs space-y-3 text-xs">
            <h5 className="font-bold flex items-center gap-2">
              <Building2 className="w-4 h-4 text-blue-400" />
              Tracked Career Portals
            </h5>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Scanning openings across Deloitte, NTT Data, McKinsey, BCG, Advance Auto Parts, Stripe, Lonza, and Workday enterprise boards.
            </p>
            <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800">
              Live link deduplication &amp; stale link removal active.
            </div>
          </div>
        </div>
      </div>

      {/* ── Slide-Over Filter Drawer ── */}
      <FilterDrawer
        isOpen={isFilterDrawerOpen}
        onClose={() => setIsFilterDrawerOpen(false)}
        filters={filterState}
        onApplyFilters={(f) => setFilterState(f)}
        onResetFilters={() => setFilterState(defaultFilterState)}
        totalMatchingJobs={jobs.length}
      />

      {/* ── Add Job by URL or JD Modal ── */}
      {isAddJobModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-7 shadow-2xl border border-slate-200 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-black text-lg text-slate-900 flex items-center gap-2">
                <Plus className="w-4 h-4 text-blue-600" />
                Add Job to Repository &amp; Tracker
              </h3>
              <button
                type="button"
                onClick={() => setIsAddJobModalOpen(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleManualIntake} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-800 mb-1">
                  Job Posting URL (LinkedIn, iimjobs, Greenhouse, Lever, Workday)
                </label>
                <input
                  type="url"
                  placeholder="https://..."
                  value={manualUrl}
                  onChange={(e) => setManualUrl(e.target.value)}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600 bg-slate-50/50"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-800 mb-1">
                  Or Paste Full Job Description Text
                </label>
                <textarea
                  rows={4}
                  placeholder="Paste the requirements, responsibilities, or role description..."
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600 bg-slate-50/50 leading-relaxed font-sans"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsAddJobModalOpen(false)}
                  className="px-4 py-2.5 rounded-xl text-slate-600 font-semibold hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isParsingUrl}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-xs disabled:opacity-50"
                >
                  {isParsingUrl ? "Analyzing Match..." : "Analyze & Save Job"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
