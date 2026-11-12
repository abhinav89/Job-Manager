"use client";

import React from "react";
import Link from "next/link";
import { ExternalLink, Sparkles, FileText, MoreVertical, Clock, MapPin, Building2, ChevronRight, ArrowRight } from "lucide-react";
import type { JobDetails, ApplicationStatus } from "@/lib/queries";

interface KanbanBoardProps {
  jobs: JobDetails[];
  onStatusChange: (job: JobDetails, newStatus: ApplicationStatus) => void;
  onOpenDetails: (jobId: number) => void;
  onTailor: (job: JobDetails) => void;
  onDelete: (jobId: number) => void;
}

const COLUMNS: { id: ApplicationStatus; title: string; color: string; badge: string }[] = [
  { id: "To Review", title: "To Review", color: "border-slate-300 bg-slate-50", badge: "bg-slate-200 text-slate-800" },
  { id: "To Apply", title: "To Apply", color: "border-blue-300 bg-blue-50/40", badge: "bg-blue-100 text-blue-800" },
  { id: "Applied", title: "Applied", color: "border-teal-300 bg-teal-50/40", badge: "bg-teal-100 text-teal-800" },
  { id: "Interview", title: "Interview", color: "border-amber-300 bg-amber-50/40", badge: "bg-amber-100 text-amber-800" },
  { id: "Offer", title: "Offer", color: "border-emerald-300 bg-emerald-50/40", badge: "bg-emerald-100 text-emerald-800" },
  { id: "Rejected", title: "Rejected", color: "border-rose-200 bg-rose-50/30", badge: "bg-rose-100 text-rose-800" },
];

export function KanbanBoard({
  jobs,
  onStatusChange,
  onOpenDetails,
  onTailor,
  onDelete,
}: KanbanBoardProps) {
  // Group jobs by column status (support alias statuses like "Saved" -> "To Review", "Tech Test" -> "Interview", "Ghosted" -> "Rejected")
  const getColumnJobs = (colId: ApplicationStatus) => {
    return jobs.filter((j) => {
      if (colId === "To Review") return j.status === "To Review" || j.status === "Saved";
      if (colId === "Interview") return j.status === "Interview" || j.status === "Tech Test";
      if (colId === "Rejected") return j.status === "Rejected" || j.status === "Ghosted";
      return j.status === colId;
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 overflow-x-auto pb-6">
      {COLUMNS.map((col) => {
        const colJobs = getColumnJobs(col.id);

        return (
          <div
            key={col.id}
            className={`flex flex-col rounded-2xl border ${col.color} p-3.5 min-w-[240px] max-h-[820px] overflow-hidden`}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200/80 mb-3 shrink-0">
              <span className="font-extrabold text-xs text-slate-800 tracking-tight">
                {col.title}
              </span>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${col.badge}`}>
                {colJobs.length}
              </span>
            </div>

            {/* Cards List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {colJobs.length === 0 ? (
                <div className="text-center py-8 text-[11px] text-slate-400 font-medium">
                  No jobs in this stage
                </div>
              ) : (
                colJobs.map((job) => {
                  const companyInitials = (job.company_name || "Co")
                    .split(" ")
                    .map((w) => w[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase();

                  const score = job.match_score ?? null;

                  return (
                    <div
                      key={job.id}
                      className="bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-3.5 shadow-2xs hover:shadow-sm transition-all space-y-2.5 text-xs group"
                    >
                      {/* Top company & match score */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <div className="w-7 h-7 rounded-lg bg-slate-900 text-white font-bold flex items-center justify-center shrink-0 text-[10px]">
                            {companyInitials}
                          </div>
                          <span className="font-bold text-slate-800 truncate text-[11px]">
                            {job.company_name}
                          </span>
                        </div>

                        {score !== null && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-800 font-bold text-[10px] border border-emerald-200 shrink-0">
                            {score}/10
                          </span>
                        )}
                      </div>

                      {/* Title */}
                      <h4
                        onClick={() => onOpenDetails(job.id)}
                        className="font-bold text-slate-900 hover:text-blue-600 cursor-pointer line-clamp-2 leading-snug"
                        title={job.job_title}
                      >
                        {job.job_title}
                      </h4>

                      {/* Meta badges */}
                      <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500">
                        {job.location && (
                          <span className="truncate max-w-[120px]">📍 {job.location}</span>
                        )}
                        {job.date_applied && (
                          <span>· Applied {job.date_applied}</span>
                        )}
                        {job.follow_up_date && (
                          <span className="text-amber-700 font-medium">· Follow-up: {job.follow_up_date}</span>
                        )}
                      </div>

                      {/* Document indicator */}
                      {job.has_pdf && (
                        <div className="text-[10px] font-semibold text-emerald-700 flex items-center gap-1 bg-emerald-50/60 p-1 rounded-md">
                          <FileText className="w-3 h-3 text-emerald-600" />
                          Tailored CV Ready
                        </div>
                      )}

                      {/* Footer Actions & Stage Transition */}
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-1">
                        {/* Quick stage selector */}
                        <select
                          value={job.status}
                          onChange={(e) => onStatusChange(job, e.target.value as ApplicationStatus)}
                          className="text-[10px] bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium py-1 px-1.5 rounded-lg border border-slate-200 focus:outline-none cursor-pointer max-w-[105px]"
                          title="Move to another stage"
                        >
                          <option value="To Review">To Review</option>
                          <option value="To Apply">To Apply</option>
                          <option value="Applied">Applied</option>
                          <option value="Interview">Interview</option>
                          <option value="Offer">Offer</option>
                          <option value="Rejected">Rejected</option>
                        </select>

                        <div className="flex items-center gap-1">
                          {job.job_url && (
                            <a
                              href={job.job_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-slate-50"
                              title="Open original job link"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}

                          <button
                            type="button"
                            onClick={() => onTailor(job)}
                            className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-slate-50"
                            title="Tailor CV for this job"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
