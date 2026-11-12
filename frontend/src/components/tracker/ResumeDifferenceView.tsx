"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, ThumbsUp, Sparkles, ArrowRight, ShieldCheck } from "lucide-react";

interface ResumeDifferenceProps {
  jobTitle: string;
  companyName: string;
  userTitle?: string;
  userExperienceYears?: number;
  jobExperienceYears?: number;
  matchScore?: number;
  onProceedToAlign: () => void;
  onBack?: () => void;
}

export function ResumeDifferenceView({
  jobTitle,
  companyName,
  userTitle = "Business Analyst - CEO Strategy Office",
  userExperienceYears = 12.8,
  jobExperienceYears = 5,
  matchScore = 6.5,
  onProceedToAlign,
  onBack,
}: ResumeDifferenceProps) {
  const scoreLabel = matchScore >= 8.5 ? "Strong" : matchScore >= 7.0 ? "Good" : matchScore >= 5.5 ? "Fair" : "Partial";

  // Pre-configured comparison tags matching NextRaise benchmark (tailor cv p1.png)
  const requiredQualifications = [
    "5+ years", "Coordinating deliverables", "Developing", "Developing presentations",
    "Managing operational processes", "Performing quality checks", "Microsoft Excel", "Business degree"
  ];

  const matchedResponsibilities = [
    "Improve", "Business processes supporting", "Donations", "Recurring financial"
  ];
  const missingResponsibilities = ["Materials for executive"];

  const matchedAtsKeywords = [
    "Analytics", "Automation", "Business Operations", "Communication",
    "Financial Reporting", "Process Improvement", "Project Management"
  ];
  const missingAtsKeywords = [
    "Data Governance", "MS Excel", "Presentation Skills", "Problem-solving", "Risk Management"
  ];

  const matchedRelatedTerms = [
    "Business professional", "Clients, Strategy & Growth", "Financial investment planning",
    "Leadership decisions", "Office of the COO", "Operational excellence", "Operational performance metrics",
    "Senior stakeholders"
  ];
  const missingRelatedTerms = ["Executive audiences"];

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm space-y-8 font-sans max-w-5xl mx-auto">
      {/* ── Top Header & Wizard Progress ── */}
      <div className="space-y-4">
        {onBack && (
          <div>
            <button
              type="button"
              onClick={onBack}
              className="text-xs font-bold text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-1.5"
            >
              ← Back to My Resumes
            </button>
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-slate-900 text-sm sm:text-base">
              Tailoring resume for <span className="text-blue-700">{jobTitle}</span> at <span className="text-slate-900">{companyName}</span>
            </span>
            <span className="text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-full">
              1 tailored resume left
            </span>
          </div>

          {/* 3 Step Breadcrumb */}
          <div className="flex items-center gap-2 text-xs font-semibold">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-600 text-white shadow-2xs">
              <span className="w-4 h-4 rounded-full bg-white text-blue-600 flex items-center justify-center text-[10px] font-black">1</span>
              See Your Difference
            </span>
            <span className="text-slate-300">→</span>
            <span className="text-slate-400">2. Align Your Resume</span>
            <span className="text-slate-300">→</span>
            <span className="text-slate-400">3. Review New Resume</span>
          </div>
        </div>

        {/* Hero Match Gauge & Headline */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
          <div className="space-y-1.5">
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Your Resume is a {scoreLabel} Match — Let&apos;s Make It Great
            </h2>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-amber-50 text-amber-900 border border-amber-200 text-xs font-medium">
              <span>ℹ️ You&apos;re on the right track, but some target keywords and achievements need alignment.</span>
            </div>
          </div>

          {/* Match Score Radial Indicator */}
          <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-2xl p-3 shrink-0">
            <div className="w-14 h-14 rounded-full border-4 border-amber-500 flex items-center justify-center font-black text-slate-900 text-lg bg-white shadow-2xs">
              {matchScore}
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider font-extrabold text-slate-400">MATCH RATING</div>
              <div className="text-xs font-bold text-amber-900">{scoreLabel} Fit</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Side-by-Side Comparison Table (Benchmark: tailor cv p1.png) ── */}
      <div className="border border-slate-200 rounded-2xl overflow-hidden shadow-2xs">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
              <th className="p-4 w-44">Feature</th>
              <th className="p-4 w-12 text-center">Status</th>
              <th className="p-4 font-bold text-slate-900">{companyName} Requirements</th>
              <th className="p-4 font-bold text-slate-900">Your Confirmed Resume Facts</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {/* Job Title */}
            <tr className="hover:bg-slate-50/50 transition-colors">
              <td className="p-4 font-bold text-slate-700">Job Title</td>
              <td className="p-4 text-center">
                <XCircle className="w-4 h-4 text-rose-500 mx-auto" />
              </td>
              <td className="p-4 font-semibold text-slate-800">{jobTitle}</td>
              <td className="p-4 text-slate-600 font-medium">{userTitle}</td>
            </tr>

            {/* Years of Experience */}
            <tr className="hover:bg-slate-50/50 transition-colors">
              <td className="p-4 font-bold text-slate-700">Years of experience</td>
              <td className="p-4 text-center">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mx-auto" />
              </td>
              <td className="p-4 font-semibold text-slate-800">{jobExperienceYears}+ years</td>
              <td className="p-4 text-emerald-800 font-semibold">{userExperienceYears} years on your resume</td>
            </tr>

            {/* Required Qualifications */}
            <tr className="hover:bg-slate-50/50 transition-colors">
              <td className="p-4 font-bold text-slate-700">Required qualifications</td>
              <td className="p-4 text-center">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mx-auto" />
              </td>
              <td colSpan={2} className="p-4">
                <div className="flex flex-wrap gap-1.5">
                  {requiredQualifications.map((q) => (
                    <span key={q} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-200 font-medium text-[11px]">
                      <ThumbsUp className="w-3 h-3 text-emerald-600" />
                      {q}
                    </span>
                  ))}
                </div>
              </td>
            </tr>

            {/* Core Responsibilities */}
            <tr className="hover:bg-slate-50/50 transition-colors">
              <td className="p-4 font-bold text-slate-700">Core responsibilities</td>
              <td className="p-4 text-center">
                <AlertTriangle className="w-4 h-4 text-amber-500 mx-auto" />
              </td>
              <td colSpan={2} className="p-4 space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  {matchedResponsibilities.map((r) => (
                    <span key={r} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-200 font-medium text-[11px]">
                      <ThumbsUp className="w-3 h-3 text-emerald-600" />
                      {r}
                    </span>
                  ))}
                  {missingResponsibilities.map((r) => (
                    <span key={r} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-medium text-[11px]">
                      {r}
                    </span>
                  ))}
                </div>
              </td>
            </tr>

            {/* ATS Keywords */}
            <tr className="hover:bg-slate-50/50 transition-colors">
              <td className="p-4 font-bold text-slate-700">
                ATS Job Keywords ({matchedAtsKeywords.length}/{matchedAtsKeywords.length + missingAtsKeywords.length})
              </td>
              <td className="p-4 text-center">
                <AlertTriangle className="w-4 h-4 text-amber-500 mx-auto" />
              </td>
              <td colSpan={2} className="p-4 space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  {matchedAtsKeywords.map((k) => (
                    <span key={k} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-200 font-medium text-[11px]">
                      <ThumbsUp className="w-3 h-3 text-emerald-600" />
                      {k}
                    </span>
                  ))}
                  {missingAtsKeywords.map((k) => (
                    <span key={k} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-medium text-[11px]">
                      {k}
                    </span>
                  ))}
                </div>
              </td>
            </tr>

            {/* Related Terms */}
            <tr className="hover:bg-slate-50/50 transition-colors">
              <td className="p-4 font-bold text-slate-700">Related terms</td>
              <td className="p-4 text-center">
                <AlertTriangle className="w-4 h-4 text-amber-500 mx-auto" />
              </td>
              <td colSpan={2} className="p-4">
                <div className="flex flex-wrap gap-1.5">
                  {matchedRelatedTerms.map((t) => (
                    <span key={t} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-200 font-medium text-[11px]">
                      <ThumbsUp className="w-3 h-3 text-emerald-600" />
                      {t}
                    </span>
                  ))}
                  {missingRelatedTerms.map((t) => (
                    <span key={t} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-medium text-[11px]">
                      {t}
                    </span>
                  ))}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── Bottom Primary CTA ── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Zero hallucination guarantee: every tailored bullet links strictly to your confirmed facts.
        </div>

        <button
          type="button"
          onClick={onProceedToAlign}
          className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-sm shadow-md hover:shadow-lg transition-all inline-flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          Improve My Resume for This Job
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
