"use client";

import React, { useState } from "react";
import { X, Sparkles, Link as LinkIcon, Loader2 } from "lucide-react";
import { API_URL } from "@/lib/api";
import { toast } from "sonner";

interface TailorInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; company: string; jd: string; url?: string }) => void;
  initialJobTitle?: string;
  initialCompany?: string;
}

export function TailorInputModal({
  isOpen,
  onClose,
  onSubmit,
  initialJobTitle = "",
  initialCompany = "",
}: TailorInputModalProps) {
  const [url, setUrl] = useState("");
  const [jobTitle, setJobTitle] = useState(initialJobTitle);
  const [company, setCompany] = useState(initialCompany);
  const [jobDescription, setJobDescription] = useState("");
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);

  if (!isOpen) return null;

  const handleFetchUrl = async () => {
    if (!url.trim()) {
      toast.error("Please enter a valid job link first.");
      return;
    }
    setIsFetchingUrl(true);
    try {
      const res = await fetch(`${API_URL}/scraper/parse-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      if (res.ok) {
        const json = await res.json();
        const parsed = json.job || {};
        if (parsed.job_title) setJobTitle(parsed.job_title);
        if (parsed.company_name) setCompany(parsed.company_name);
        if (parsed.job_description) setJobDescription(parsed.job_description);
        toast.success(`Fetched details for ${parsed.job_title || "job"}!`);
      } else {
        toast.info("Could not auto-extract from link. Please paste the job description below.");
      }
    } catch (err) {
      toast.info("Could not fetch link directly. Please paste the job description below.");
    } finally {
      setIsFetchingUrl(false);
    }
  };

  const isValid = jobTitle.trim().length > 0 && jobDescription.trim().length >= 50;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobTitle.trim()) {
      toast.error("Please provide a job title.");
      return;
    }
    if (jobDescription.trim().length < 50) {
      toast.error("Please paste at least 50 characters of job description.");
      return;
    }
    onSubmit({
      title: jobTitle.trim(),
      company: company.trim(),
      jd: jobDescription.trim(),
      url: url.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 relative">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h3 className="text-lg font-black text-slate-900 tracking-tight">Tailor your resume</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Section 1: Import from job link */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-800">
              Import from job link <span className="font-normal text-slate-500">(optional - fills the fields below)</span>
            </label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <LinkIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste a Greenhouse, Lever, Workday, or careers link"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
              <button
                type="button"
                onClick={handleFetchUrl}
                disabled={isFetchingUrl || !url.trim()}
                className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shrink-0 disabled:opacity-50"
              >
                {isFetchingUrl ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Fetch details
                  </>
                )}
              </button>
            </div>
            <p className="text-[11px] text-slate-400">
              LinkedIn links can&apos;t be imported directly - use company career links for best results.
            </p>
          </div>

          {/* Divider */}
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase font-bold tracking-widest text-slate-400">
              <span className="bg-white px-3">or enter manually</span>
            </div>
          </div>

          {/* Title & Company */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold tracking-wider text-slate-600">
                Job Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Product Manager"
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold tracking-wider text-slate-600">
                Company <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Stripe"
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          {/* Job Description */}
          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold tracking-wider text-slate-600">
              Job Description <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={6}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the full job description - responsibilities, requirements, keywords. More context = sharper match."
              className="w-full p-3 rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 transition-colors resize-none leading-relaxed"
            />
            <div className="flex justify-end text-[10px] text-slate-400">
              {jobDescription.length} / 100 min chars
            </div>
          </div>

          {/* Footer */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-100">
            <span className="text-xs text-slate-500">
              {isValid ? "Ready to tailor your CV" : "Fill title & paste JD to continue"}
            </span>
            <button
              type="submit"
              disabled={!isValid}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm hover:shadow transition-all inline-flex items-center gap-1.5 disabled:opacity-50"
            >
              Tailor my resume →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
