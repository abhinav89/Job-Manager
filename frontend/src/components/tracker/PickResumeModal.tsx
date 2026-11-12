"use client";

import React from "react";
import { X, FileText, ArrowRight } from "lucide-react";

interface PickResumeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectResume: (resumeName: string) => void;
  resumeName?: string;
}

export function PickResumeModal({
  isOpen,
  onClose,
  onSelectResume,
  resumeName = "Master_Resume_CV",
}: PickResumeModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 relative p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-black text-slate-900 tracking-tight">Pick a resume to tailor</h3>
            <p className="text-xs text-slate-500 mt-1">
              We&apos;ll customise a copy for the job description you provide next.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3 pt-2">
          <button
            type="button"
            onClick={() => onSelectResume(resumeName)}
            className="w-full text-left p-4 rounded-2xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
                  {resumeName}
                </h4>
                <p className="text-[11px] text-slate-500">
                  Primary Master CV · Confirmed Facts
                </p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
          </button>
        </div>
      </div>
    </div>
  );
}
