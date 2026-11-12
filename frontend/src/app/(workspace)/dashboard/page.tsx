"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  CheckCircle2,
  Clock,
  Download,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  Plus,
  Search,
  Sparkles,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  BookmarkCheck,
} from "lucide-react";
import { usePipelineSummary, useRepositoryJobs, useProfile } from "@/lib/queries";
import { API_URL } from "@/lib/api";
import { ResumeOnboardingModal } from "@/components/ResumeOnboardingModal";
import { JobCard } from "@/components/tracker/JobCard";
import { toast } from "sonner";

export default function DashboardPage() {
  const router = useRouter();
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const { data: profile } = useProfile();
  const { data: pipeline, isLoading: isPipelineLoading } = usePipelineSummary();
  const { data: repoData, isLoading: isJobsLoading } = useRepositoryJobs();

  const userName = profile?.first_name || "Abhinav";
  const recommendedJobs = repoData?.jobs?.slice(0, 3) || [];

  const handleExport = (format: "csv" | "xlsx") => {
    const url = `${API_URL}/tracker/export/${format}`;
    window.open(url, "_blank");
    toast.success(`Exporting Application Master Sheet as ${format.toUpperCase()}...`);
  };

  const handleTailorJob = (job: any) => {
    // Save to tracker if not already saved, then navigate to tailoring
    router.push(`/generate?title=${encodeURIComponent(job.job_title)}&company=${encodeURIComponent(job.company_name)}`);
  };

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* ── Top Header & Quick Actions ── */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            Executive Career Pipeline
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Welcome back, {userName}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Track openings across 100+ company career pages, align resumes truthfully, and drive applications.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={() => setIsOnboardingOpen(true)}
            className="px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-all inline-flex items-center gap-2"
          >
            <FileText className="w-4 h-4 text-slate-500" />
            Update CV
          </button>

          <button
            type="button"
            onClick={() => handleExport("xlsx")}
            className="px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-all inline-flex items-center gap-2"
            title="Export complete pipeline to Excel"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            Export Master Sheet
          </button>

          <Link
            href="/discover"
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm hover:shadow transition-all inline-flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Find Jobs
          </Link>
        </div>
      </div>

      {/* ── Follow-ups Due Alert (if any) ── */}
      {pipeline && pipeline.follow_ups_due_count > 0 && (
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 border border-amber-200 flex items-start gap-4 animate-in fade-in duration-200">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
            <Clock className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-sm text-amber-900">
              {pipeline.follow_ups_due_count} Follow-up{pipeline.follow_ups_due_count > 1 ? "s" : ""} Due Today
            </h4>
            <p className="text-xs text-amber-800 mt-0.5">
              Consistent recruiter outreach increases response rates. Review your scheduled follow-ups in the application tracker.
            </p>
          </div>
          <Link
            href="/tracker"
            className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shrink-0"
          >
            Review Pipeline
          </Link>
        </div>
      )}

      {/* ── 4 Primary Action Pipeline Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* To Review */}
        <Link
          href="/tracker"
          className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 shadow-xs hover:shadow transition-all space-y-3 group"
        >
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">Jobs To Review</span>
            <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
              <BookmarkCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-slate-900">
            {pipeline?.to_review_count ?? 0}
          </div>
          <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
            New jobs saved for fit review <ArrowRight className="w-3 h-3 text-slate-400" />
          </p>
        </Link>

        {/* To Apply */}
        <Link
          href="/tracker"
          className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 shadow-xs hover:shadow transition-all space-y-3 group"
        >
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700">Jobs To Apply</span>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-blue-700">
            {pipeline?.to_apply_count ?? 0}
          </div>
          <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
            High fit · Ready for tailored submission <ArrowRight className="w-3 h-3 text-slate-400" />
          </p>
        </Link>

        {/* In Progress / Applied */}
        <Link
          href="/tracker"
          className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 shadow-xs hover:shadow transition-all space-y-3 group"
        >
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-700">Applications In Progress</span>
            <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center group-hover:bg-teal-100 transition-colors">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-teal-800">
            {pipeline?.applied_count ?? 0}
          </div>
          <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
            Submitted & awaiting feedback <ArrowRight className="w-3 h-3 text-slate-400" />
          </p>
        </Link>

        {/* Interviews & Offers */}
        <Link
          href="/tracker"
          className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 shadow-xs hover:shadow transition-all space-y-3 group"
        >
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">Interviews & Offers</span>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-emerald-700">
            {(pipeline?.interviewing_count ?? 0) + (pipeline?.offers_count ?? 0)}
          </div>
          <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
            {pipeline?.interviewing_count ?? 0} active stage, {pipeline?.offers_count ?? 0} offers <ArrowRight className="w-3 h-3 text-slate-400" />
          </p>
        </Link>
      </div>

      {/* ── Top Recommended Openings Feed (NextRaise Style) ── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Top Matching Openings For You
            </h2>
            <p className="text-xs text-slate-500">
              Curated from tracked company career portals & verified against your confirmed career facts.
            </p>
          </div>
          <Link
            href="/discover"
            className="text-xs font-bold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
          >
            Explore all openings <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="space-y-4">
          {recommendedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onTailorAndApply={() => handleTailorJob(job)}
              onSaveToTracker={() => toast.success(`Saved ${job.job_title} at ${job.company_name} to Tracker!`)}
            />
          ))}
        </div>
      </div>

      {/* ── Pipeline Master Sheet Callout ── */}
      <div className="bg-slate-950 text-white rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
        <div className="space-y-1">
          <h3 className="text-lg font-bold">Application Master Sheet & Audit Trail</h3>
          <p className="text-xs text-slate-400 max-w-xl">
            Download your full tracking dataset formatted for Excel or CSV, with timestamps, follow-up dates, recruiter contacts, and links to exact tailored resume copies.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => handleExport("csv")}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-all inline-flex items-center gap-2"
          >
            <Download className="w-4 h-4 text-slate-300" />
            Download CSV
          </button>
          <button
            type="button"
            onClick={() => handleExport("xlsx")}
            className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-all inline-flex items-center gap-2 shadow-sm"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Download Excel (.xlsx)
          </button>
        </div>
      </div>

      {/* Onboarding Modal */}
      <ResumeOnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
      />
    </div>
  );
}
