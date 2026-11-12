"use client";

import React, { useState } from "react";
import {
  X,
  ExternalLink,
  Download,
  CheckCircle2,
  Sparkles,
  FileText,
  Building2,
  MapPin,
  Briefcase,
  Layers,
  ArrowRight,
} from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { API_URL } from "@/lib/api";
import { queryKeys, useResumes, useThemes } from "@/lib/queries";
import { JobCardData } from "./JobCard";

interface DirectApplyModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: JobCardData | null;
  onApplied?: (job: JobCardData) => void;
}

const RESUME_THEMES = [
  { id: "classic", name: "Classic Executive", desc: "Traditional serif, maximum ATS parsing accuracy (Corporate & Consulting)", file: "classic.pdf" },
  { id: "modern", name: "Modern Minimalist", desc: "Clean geometric sans, high readability (Tech, FinTech & Strategy)", file: "modern.pdf" },
  { id: "executive", name: "Executive Leadership", desc: "Prominent header, board & leadership alignment (VP, CXO & Founder)", file: "executive.pdf" },
  { id: "compact", name: "Dense 1-Page", desc: "Maximum space efficiency, 1-page condensed layout (Fast screening)", file: "compact.pdf" },
  { id: "technical", name: "Technical / Engineering", desc: "Skills-first layout, systems & tech stack prominence (AI & Tech)", file: "technical.pdf" },
  { id: "serif", name: "Academic / Formal", desc: "Refined editorial typography (Advisory, Research & Policy)", file: "serif.pdf" },
];

export function DirectApplyModal({ isOpen, onClose, job, onApplied }: DirectApplyModalProps) {
  const queryClient = useQueryClient();
  const [selectedTheme, setSelectedTheme] = useState("classic");
  const [isApplying, setIsApplying] = useState(false);

  if (!isOpen || !job) return null;

  const currentTheme = RESUME_THEMES.find(t => t.id === selectedTheme) || RESUME_THEMES[0];

  const handleDownloadThemePdf = () => {
    const link = document.createElement("a");
    link.href = `/resume-templates/${currentTheme.file}`;
    link.download = `${(job.company_name || "Application").replace(/\s+/g, "_")}_Resume_${currentTheme.name.replace(/\s+/g, "_")}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(`Downloaded resume formatted with "${currentTheme.name}" theme!`);
  };

  const handleProceedApply = async () => {
    setIsApplying(true);
    try {
      // 1. Save or update job in tracker under "Applied"
      await fetch(`${API_URL}/scraper/import`, {
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
          status: "Applied",
          priority: "High",
          match_score: job.match_score ? Math.round(job.match_score) : null,
          match_analysis: job.match_analysis,
        }),
      });

      // 2. Invalidate tracker queries so new status shows
      queryClient.invalidateQueries({ queryKey: queryKeys.tracker });

      // 3. Open official application URL in new tab
      if (job.job_url) {
        window.open(job.job_url, "_blank", "noopener,noreferrer");
      }

      toast.success(`Marked "${job.job_title}" at ${job.company_name} as Applied in Tracker!`);
      if (onApplied) onApplied(job);
      onClose();
    } catch {
      if (job.job_url) {
        window.open(job.job_url, "_blank", "noopener,noreferrer");
      }
      onClose();
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs font-sans">
      <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <span className="text-[10px] font-black tracking-widest text-blue-600 uppercase">
              DIRECT APPLICATION
            </span>
            <h2 className="text-xl font-black text-slate-900">
              Apply with Selected Resume Theme
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Target Role Card */}
          <div className="p-4 rounded-2xl bg-blue-50/60 border border-blue-100/80 flex items-center justify-between gap-4">
            <div className="space-y-1 min-w-0">
              <span className="text-xs font-bold text-blue-700">{job.company_name}</span>
              <h3 className="text-base font-extrabold text-slate-900 truncate">
                {job.job_title}
              </h3>
              <div className="flex items-center gap-3 text-xs text-slate-500">
                {job.location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    {job.location}
                  </span>
                )}
                {job.work_arrangement && (
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="w-3.5 h-3.5" />
                    {job.work_arrangement}
                  </span>
                )}
              </div>
            </div>

            {job.match_score && (
              <div className="bg-white border border-blue-200 px-3 py-2 rounded-xl text-center shrink-0">
                <span className="block text-[9px] uppercase font-bold text-slate-400">Match</span>
                <span className="text-base font-black text-blue-600">{job.match_score.toFixed(1)}</span>
              </div>
            )}
          </div>

          {/* Theme Selector */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-black uppercase tracking-wider text-slate-700">
                1. Select Resume Archetype Theme:
              </label>
              <button
                type="button"
                onClick={handleDownloadThemePdf}
                className="text-xs font-bold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
                Download PDF Preview
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {RESUME_THEMES.map((theme) => {
                const isSelected = selectedTheme === theme.id;
                return (
                  <button
                    key={theme.id}
                    type="button"
                    onClick={() => setSelectedTheme(theme.id)}
                    className={`p-3.5 rounded-2xl text-left border transition-all cursor-pointer ${
                      isSelected
                        ? "bg-blue-50/80 border-blue-600 ring-2 ring-blue-600/20 shadow-xs"
                        : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/60"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-bold ${isSelected ? "text-blue-900" : "text-slate-900"}`}>
                        {theme.name}
                      </span>
                      {isSelected && (
                        <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 leading-tight">
                      {theme.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Direct Apply Action Note */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              What happens when you click Apply:
            </span>
            <p className="leading-relaxed">
              We open the employer application page directly and automatically record this role under <strong>"Applied"</strong> in your Job Tracker pipeline for follow-up tracking.
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-5 border-t border-slate-100 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold cursor-pointer"
          >
            Cancel
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleDownloadThemePdf}
              className="px-4 py-2.5 rounded-xl border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold inline-flex items-center gap-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              Download Resume
            </button>

            <button
              type="button"
              disabled={isApplying}
              onClick={handleProceedApply}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md hover:shadow-lg transition-all inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <span>Proceed to Apply</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
