"use client";

import React, { useState } from "react";
import {
  X,
  FileText,
  ArrowRight,
  Plus,
  UploadCloud,
  Sparkles,
  Briefcase,
  Code,
  DollarSign,
  TrendingUp,
  Cpu,
  Truck,
  Users,
  Megaphone,
  Handshake,
  Check,
  Layers,
} from "lucide-react";
import { useResumes, useThemes, type ResumeItem, type CareerTheme } from "@/lib/queries";
import { API_URL } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

interface PickResumeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectResume: (resumeName: string, resumeId?: string) => void;
  onUploadNewResume?: () => void;
  resumeName?: string;
}

const THEME_ICONS: Record<string, React.ElementType> = {
  Briefcase,
  DollarSign,
  Sparkles,
  Code,
  TrendingUp,
  Handshake,
  Cpu,
  Truck,
  Megaphone,
  Users,
};

export function PickResumeModal({
  isOpen,
  onClose,
  onSelectResume,
  onUploadNewResume,
  resumeName = "Master_Resume_CV",
}: PickResumeModalProps) {
  const queryClient = useQueryClient();
  const resumesQuery = useResumes();
  const themesQuery = useThemes();

  const [mode, setMode] = useState<"pick" | "create_theme">("pick");
  const [selectedThemeId, setSelectedThemeId] = useState<string>("strategy-transformation");
  const [newResumeName, setNewResumeName] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const resumes = resumesQuery.data?.resumes || [
    {
      id: "master-cv",
      name: resumeName,
      display_title: "Primary Master CV (All Verified Facts)",
      theme_id: "master",
      theme_name: "Master CV",
      template_id: "classic" as const,
      target_roles: ["Strategy & Leadership"],
      experience_count: 3,
      skills_count: 20,
      education_count: 2,
      last_updated: "Today",
      is_master: true,
      description: "Comprehensive source of truth with 100% verified facts.",
    },
  ];

  const themes = themesQuery.data?.themes || [];

  const handleCreateThemedResume = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanName = newResumeName.trim();
    if (!cleanName) {
      toast.error("Please enter a name for this resume");
      return;
    }

    setIsSubmitting(true);
    try {
      const chosenTheme = themes.find((t) => t.id === selectedThemeId);
      const res = await fetch(`${API_URL}/resumes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: cleanName,
          theme_id: selectedThemeId,
          template_id: chosenTheme?.recommended_template || "classic",
          target_roles: chosenTheme?.target_roles || [cleanName],
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to create theme resume");
      }

      await queryClient.invalidateQueries({ queryKey: ["workspace-data", "resumes"] });
      toast.success(`Created "${cleanName}" for ${chosenTheme?.name || "profile"}`);
      setMode("pick");
      setNewResumeName("");
      onSelectResume(cleanName);
    } catch (err: any) {
      toast.error(err?.message || "Could not create resume");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 relative p-6 sm:p-7 space-y-5">
        
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-extrabold text-[10px] uppercase tracking-wider mb-1.5">
              <Layers className="w-3 h-3" />
              Multi-Theme Resume Suite
            </div>
            <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
              {mode === "pick" ? "Pick a resume to tailor" : "Create a targeted theme resume"}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {mode === "pick"
                ? "Select an existing profile or upload/create a targeted version for this role."
                : "Generate a targeted baseline resume tailored to specific role archetypes."}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Toggle if in Pick mode */}
        {mode === "pick" ? (
          <>
            {/* Quick Actions Bar */}
            <div className="grid grid-cols-2 gap-2.5 pt-1">
              <button
                type="button"
                onClick={() => {
                  if (onUploadNewResume) {
                    onClose();
                    onUploadNewResume();
                  } else {
                    toast.info("Upload fresh CV from Career Profile or Onboarding.");
                  }
                }}
                className="p-3 rounded-2xl border border-dashed border-slate-300 hover:border-blue-500 hover:bg-blue-50/40 text-left transition-all flex items-center gap-2.5 group"
              >
                <div className="w-8 h-8 rounded-xl bg-slate-100 group-hover:bg-blue-100 text-slate-600 group-hover:text-blue-600 flex items-center justify-center shrink-0 transition-colors">
                  <UploadCloud className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800 group-hover:text-blue-700">Upload Fresh CV</div>
                  <div className="text-[10px] text-slate-400">Import new PDF / Word</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setMode("create_theme");
                  setNewResumeName("Executive_Strategy_CV");
                }}
                className="p-3 rounded-2xl border border-dashed border-slate-300 hover:border-emerald-500 hover:bg-emerald-50/40 text-left transition-all flex items-center gap-2.5 group"
              >
                <div className="w-8 h-8 rounded-xl bg-slate-100 group-hover:bg-emerald-100 text-slate-600 group-hover:text-emerald-600 flex items-center justify-center shrink-0 transition-colors">
                  <Plus className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800 group-hover:text-emerald-700">New Theme Resume</div>
                  <div className="text-[10px] text-slate-400">Sales, Tech, Product, etc.</div>
                </div>
              </button>
            </div>

            {/* List of Available Resumes */}
            <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
              <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 px-1">
                Your Available Resumes ({resumes.length})
              </div>

              {resumes.map((resume: ResumeItem) => {
                const IconComponent = resume.is_master ? FileText : Sparkles;
                return (
                  <button
                    key={resume.id}
                    type="button"
                    onClick={() => onSelectResume(resume.name, resume.id)}
                    className="w-full text-left p-4 rounded-2xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 hover:shadow-xs transition-all flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                          resume.is_master
                            ? "bg-blue-100 text-blue-700"
                            : "bg-indigo-100 text-indigo-700"
                        }`}
                      >
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-slate-900 group-hover:text-blue-700 transition-colors truncate">
                            {resume.display_title || resume.name}
                          </h4>
                          {resume.is_master ? (
                            <span className="px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 text-[9px] font-extrabold uppercase">
                              Master CV
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[9px] font-extrabold">
                              {resume.theme_name}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 truncate mt-0.5">
                          {resume.description || `${resume.experience_count} roles · ${resume.skills_count} facts · ${resume.template_id} template`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 pl-2">
                      <span className="text-[10px] text-slate-400 font-medium group-hover:text-blue-600">Select</span>
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </button>
                );
              })}
            </div>
          </>
        ) : (
          /* Mode 2: Create Themed Resume Form */
          <form onSubmit={handleCreateThemedResume} className="space-y-4 pt-1">
            <div>
              <label className="block text-xs font-bold text-slate-800 mb-1.5">
                Resume Label / File Name
              </label>
              <input
                type="text"
                value={newResumeName}
                onChange={(e) => setNewResumeName(e.target.value)}
                placeholder="e.g. Sales_Director_CV or Tech_Lead_Resume"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-800 mb-1.5">
                Select Career Theme Archetype
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[220px] overflow-y-auto pr-1">
                {themes.map((theme: CareerTheme) => {
                  const Icon = THEME_ICONS[theme.icon || "Briefcase"] || Briefcase;
                  const isSelected = selectedThemeId === theme.id;
                  return (
                    <button
                      key={theme.id}
                      type="button"
                      onClick={() => {
                        setSelectedThemeId(theme.id);
                        if (!newResumeName || newResumeName.includes("_CV")) {
                          setNewResumeName(`${theme.name.replace(/[^a-zA-Z0-9]/g, "_")}_CV`);
                        }
                      }}
                      className={`p-2.5 rounded-xl border text-left transition-all flex flex-col gap-1.5 ${
                        isSelected
                          ? "border-blue-600 bg-blue-50/70 text-blue-900 shadow-2xs"
                          : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <Icon className={`w-4 h-4 ${isSelected ? "text-blue-600" : "text-slate-500"}`} />
                        {isSelected && <Check className="w-3.5 h-3.5 text-blue-600" />}
                      </div>
                      <div className="text-[11px] font-bold leading-tight truncate">{theme.name}</div>
                      <div className="text-[9px] text-slate-500 line-clamp-1">{theme.category}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setMode("pick")}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors"
              >
                Back to List
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all flex items-center gap-2"
              >
                {isSubmitting ? "Creating..." : "Create & Tailor"}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
