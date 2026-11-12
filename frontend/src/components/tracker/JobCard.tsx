"use client";

import React, { useState } from "react";
import { Bookmark, ExternalLink, Sparkles, ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Building2, MapPin, Briefcase, Clock, DollarSign } from "lucide-react";

export interface JobCardData {
  id?: string | number;
  company_name: string;
  job_title: string;
  job_url?: string;
  source?: string;
  location?: string;
  work_arrangement?: string;
  job_type?: string;
  seniority?: string;
  salary_range?: string;
  date_posted?: string;
  is_early_applicant?: boolean;
  match_score?: number;
  match_label?: string;
  match_analysis?: {
    score: number;
    label: string;
    summary: string;
    pros: string[];
    cons: string[];
    matched_skills: string[];
    missing_skills: string[];
    experience_fit?: string;
    location_fit?: string;
  };
  job_description?: string;
}

interface JobCardProps {
  job: JobCardData;
  onSaveToTracker?: (job: JobCardData, status: "To Review" | "To Apply") => void;
  onTailorAndApply?: (job: JobCardData) => void;
  isSaved?: boolean;
}

export function JobCard({ job, onSaveToTracker, onTailorAndApply, isSaved = false }: JobCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [saved, setSaved] = useState(isSaved);

  const score = job.match_score ?? 7.5;
  const label = job.match_label || (score >= 8.5 ? "STRONG" : score >= 7.0 ? "GOOD" : score >= 5.5 ? "FAIR" : "PARTIAL");

  // Determine score color
  const getScoreColor = () => {
    if (score >= 8.5) return { ring: "border-emerald-500", text: "text-emerald-400", badge: "bg-emerald-950 text-emerald-300 border-emerald-800" };
    if (score >= 7.0) return { ring: "border-teal-500", text: "text-teal-400", badge: "bg-teal-950 text-teal-300 border-teal-800" };
    if (score >= 5.5) return { ring: "border-amber-500", text: "text-amber-400", badge: "bg-amber-950 text-amber-300 border-amber-800" };
    return { ring: "border-rose-500", text: "text-rose-400", badge: "bg-rose-950 text-rose-300 border-rose-800" };
  };

  const scoreStyle = getScoreColor();

  const handleSave = () => {
    setSaved(!saved);
    if (onSaveToTracker) {
      onSaveToTracker(job, "To Review");
    }
  };

  // Company monogram letters
  const companyInitials = (job.company_name || "Co")
    .split(" ")
    .map(w => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
      <div className="p-5 sm:p-6 flex flex-col lg:flex-row items-start justify-between gap-5">
        {/* Left: Company & Details */}
        <div className="flex items-start gap-4 flex-1 min-w-0">
          {/* Company Monogram/Logo */}
          <div className="w-12 h-12 rounded-xl bg-slate-900 text-white font-bold flex items-center justify-center shrink-0 text-base shadow-sm">
            {companyInitials}
          </div>

          <div className="space-y-2 flex-1 min-w-0">
            {/* Title & Posted Badge */}
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900 tracking-tight leading-snug truncate">
                {job.job_title}
              </h3>
              {job.is_early_applicant && (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full">
                  ⚡ Early applicant
                </span>
              )}
            </div>

            {/* Company & Meta info */}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-medium text-slate-600">
              <span className="font-semibold text-slate-800">{job.company_name}</span>
              {job.source && (
                <span className="text-slate-400 font-normal">via {job.source}</span>
              )}
              {job.date_posted && (
                <span className="text-xs text-slate-400">· {job.date_posted}</span>
              )}
            </div>

            {/* Tags row */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-600">
              {job.location && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-700">
                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                  {job.location}
                </span>
              )}
              {job.work_arrangement && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 font-medium border border-blue-100">
                  <Briefcase className="w-3.5 h-3.5 text-blue-600" />
                  {job.work_arrangement}
                </span>
              )}
              {job.seniority && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-700">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {job.seniority}
                </span>
              )}
              {job.salary_range && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 font-semibold border border-emerald-100">
                  <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
                  {job.salary_range}
                </span>
              )}
            </div>

            {/* Expand details link */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setExpanded(!expanded)}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1 transition-colors"
              >
                {expanded ? "Hide fit analysis" : "View match evidence & details"}
                {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Relevance Widget & Primary Actions */}
        <div className="flex flex-row lg:flex-col items-center lg:items-end justify-between w-full lg:w-auto gap-3 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100">
          {/* Circular Profile Relevance Widget (NextRaise Benchmark Style) */}
          <div className="bg-slate-950 text-white rounded-xl p-3 flex flex-col items-center justify-center min-w-[100px] shadow-sm">
            <span className="text-[9px] tracking-wider uppercase font-semibold text-slate-400 mb-1">
              PROFILE FIT
            </span>
            <div className={`w-11 h-11 rounded-full border-2 ${scoreStyle.ring} flex items-center justify-center font-extrabold text-base ${scoreStyle.text}`}>
              {score.toFixed(1)}
            </div>
            <span className="text-[10px] font-bold tracking-wide uppercase text-slate-300 mt-1">
              {label}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSave}
              className={`p-2.5 rounded-xl border text-xs font-medium transition-all ${
                saved
                  ? "bg-slate-100 text-slate-800 border-slate-300"
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900"
              }`}
              title={saved ? "Saved in Tracker" : "Save for later"}
            >
              <Bookmark className={`w-4 h-4 ${saved ? "fill-slate-800 text-slate-800" : ""}`} />
            </button>

            {job.job_url && (
              <a
                href={job.job_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-slate-900 text-xs font-medium transition-all"
                title="Open employer job posting"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}

            <button
              type="button"
              onClick={() => onTailorAndApply ? onTailorAndApply(job) : null}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm hover:shadow transition-all inline-flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Tailor & Apply
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Match Evidence & Gaps Drawer */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50/80 p-5 space-y-4 text-xs animate-in fade-in duration-150">
          {/* Fit Summary */}
          {job.match_analysis && (
            <div className="space-y-2">
              <p className="font-medium text-slate-800">
                <span className="font-bold text-slate-900">Match Summary: </span>
                {job.match_analysis.summary}
              </p>

              {/* Supported Points */}
              {job.match_analysis.pros && job.match_analysis.pros.length > 0 && (
                <div className="space-y-1 pt-1">
                  <div className="font-semibold text-emerald-800 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Confirmed Evidence Supporting Match:
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-600 pl-2">
                    {job.match_analysis.pros.map((pro, idx) => (
                      <li key={idx}>{pro}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Gaps / Questions */}
              {job.match_analysis.cons && job.match_analysis.cons.length > 0 && (
                <div className="space-y-1 pt-1">
                  <div className="font-semibold text-amber-800 flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                    Potential Gaps / Detail to Confirm:
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-600 pl-2">
                    {job.match_analysis.cons.map((con, idx) => (
                      <li key={idx}>{con}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Description Snippet */}
          {job.job_description && (
            <div className="pt-2 border-t border-slate-200/60">
              <p className="font-semibold text-slate-800 mb-1">Job Description Excerpt:</p>
              <p className="text-slate-600 whitespace-pre-line line-clamp-4 leading-relaxed font-sans">
                {job.job_description}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
