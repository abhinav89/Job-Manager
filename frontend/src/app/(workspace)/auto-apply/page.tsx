"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  Play,
  Pause,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  MapPin,
  Briefcase,
  Layers,
  Settings2,
  SlidersHorizontal,
  ChevronRight,
  ShieldCheck,
  Check,
  X,
  ExternalLink,
  MessageSquare,
  Sparkles,
  Info,
  Clock,
  ArrowRight,
  ListFilter,
  Eye,
  FileText,
} from "lucide-react";

import { API_URL } from "@/lib/api";
import {
  useAutoApplySetup,
  useAutoApplyQueue,
  queryKeys,
  type AutoApplyPreviewJob,
  type AutoApplyPreviewResponse,
  type AutoApplyQueueItem,
} from "@/lib/queries";

export default function AutoApplyPage() {
  const queryClient = useQueryClient();

  // Queries
  const setupQuery = useAutoApplySetup();
  const queueQuery = useAutoApplyQueue();

  // Run-level location adjustments (Independent from saved defaults!)
  const [locationMode, setLocationMode] = useState<"prioritize" | "filter">("prioritize");
  const [selectedLocations, setSelectedLocations] = useState<string[]>(["Hyderabad"]);
  const [unattendedLowerRanked, setUnattendedLowerRanked] = useState<boolean>(false);

  // Setup modal state
  const [isEditingSetup, setIsEditingSetup] = useState(false);
  const [editThemes, setEditThemes] = useState<string[]>([]);
  const [newThemeInput, setNewThemeInput] = useState("");
  const [editMinExp, setEditMinExp] = useState(4);
  const [editMaxExp, setEditMaxExp] = useState(10);
  const [isSavingSetup, setIsSavingSetup] = useState(false);

  // Preview state
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [previewData, setPreviewData] = useState<AutoApplyPreviewResponse | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<Set<string>>(new Set());
  const [saveAsRule, setSaveAsRule] = useState(false);
  const [isQueueing, setIsQueueing] = useState(false);

  // Queue tab filter
  const [queueTab, setQueueTab] = useState<"all" | "active" | "needs_input">("all");

  // Sync initial setup values
  useEffect(() => {
    if (setupQuery.data?.defaults) {
      const defs = setupQuery.data.defaults;
      setEditThemes(defs.role_themes || []);
      setEditMinExp(defs.min_experience_years || 4);
      setEditMaxExp(defs.max_experience_years || 10);
      if (selectedLocations.length === 0 || selectedLocations[0] === "Hyderabad") {
        setSelectedLocations(defs.preferred_locations || ["Hyderabad"]);
      }
      setLocationMode(defs.location_mode || "prioritize");
      setUnattendedLowerRanked(defs.unattended_include_lower_ranked || false);
    }
  }, [setupQuery.data]);

  // Load preview function
  const handleFetchPreview = async (overrideLocs?: string[], overrideMode?: "prioritize" | "filter") => {
    setIsLoadingPreview(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          locations: overrideLocs || selectedLocations,
          location_mode: overrideMode || locationMode,
          unattended_include_lower_ranked: unattendedLowerRanked,
        }),
      });
      const data: AutoApplyPreviewResponse = await res.json();
      if (res.ok) {
        setPreviewData(data);
        // Pre-select all eligible unflagged jobs by default
        const eligibleIds = new Set(
          data.jobs.filter((j) => j.eligible_for_auto_queue).map((j) => j.job_id)
        );
        setSelectedJobIds(eligibleIds);
      } else {
        toast.error("Could not generate job preview.");
      }
    } catch {
      toast.error("Network error while generating preview.");
    } finally {
      setIsLoadingPreview(false);
    }
  };

  // Run preview on initial mount once setup is ready
  useEffect(() => {
    if (setupQuery.data && !previewData) {
      handleFetchPreview();
    }
  }, [setupQuery.data]);

  // Save editable defaults
  const handleSaveDefaults = async () => {
    if (editThemes.length === 0) {
      toast.error("Please add at least one role theme.");
      return;
    }
    if (editMinExp < 0 || editMaxExp < editMinExp) {
      toast.error("Please specify a valid experience range.");
      return;
    }

    setIsSavingSetup(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/setup`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role_themes: editThemes,
          min_experience_years: editMinExp,
          max_experience_years: editMaxExp,
          preferred_locations: selectedLocations,
          location_mode: locationMode,
          unattended_include_lower_ranked: unattendedLowerRanked,
        }),
      });
      if (res.ok) {
        toast.success("Saved role themes & experience range defaults!");
        setIsEditingSetup(false);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplySetup });
        handleFetchPreview();
      } else {
        toast.error("Failed to save defaults.");
      }
    } catch {
      toast.error("Network error saving defaults.");
    } finally {
      setIsSavingSetup(false);
    }
  };

  // Prepopulate suggestions from profile
  const handlePrepopulate = () => {
    if (setupQuery.data?.profile_suggestions) {
      const sug = setupQuery.data.profile_suggestions;
      setEditThemes(sug.suggested_themes);
      setEditMinExp(sug.suggested_min_experience);
      setEditMaxExp(sug.suggested_max_experience);
      toast.info("Prepopulated suggestions from your verified profile tenure.");
    }
  };

  // Queue selected jobs
  const handleQueueSelected = async () => {
    if (!previewData || selectedJobIds.size === 0) {
      toast.error("Please select at least one job to queue.");
      return;
    }

    const toQueue = previewData.jobs.filter((j) => selectedJobIds.has(j.job_id));
    setIsQueueing(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selected_jobs: toQueue,
          save_rule: saveAsRule,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Queued ${data.added_count} job application(s)!`);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not queue jobs.");
      }
    } catch {
      toast.error("Network error queueing jobs.");
    } finally {
      setIsQueueing(false);
    }
  };

  // Pause / Resume queue
  const handleToggleQueuePause = async () => {
    const isPaused = queueQuery.data?.queue?.queue_status === "paused";
    const endpoint = isPaused ? "/auto-apply/queue/resume" : "/auto-apply/queue/pause";
    try {
      const res = await fetch(`${API_URL}${endpoint}`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      }
    } catch {
      toast.error("Could not update queue pause state.");
    }
  };

  // Resolve Needs Input item
  const handleResolveNeedsInput = async (itemId: string, action: "approve" | "dismiss") => {
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      }
    } catch {
      toast.error("Could not resolve queue item.");
    }
  };

  const queue = queueQuery.data?.queue;
  const queueItems: AutoApplyQueueItem[] = queue?.queue_items || [];
  const activityFeed = queue?.activity_feed || [];
  const isQueuePaused = queue?.queue_status === "paused";

  const filteredQueueItems = queueItems.filter((item) => {
    if (queueTab === "active") return item.status === "queued" || item.status === "in_progress";
    if (queueTab === "needs_input") return item.status === "needs_input";
    return true;
  });

  const needsInputCount = queueItems.filter((i) => i.status === "needs_input").length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Top Header ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold border border-blue-200">
              <Bot className="w-3.5 h-3.5" />
              Phase 1 · Job Filtering, Selection &amp; Run Queue
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Auto Apply Setup &amp; Application Queue
            </h1>
            <p className="text-xs text-slate-500 max-w-2xl leading-relaxed">
              Define your role themes and target experience range. Select eligible jobs to populate a persistent
              application queue with step-by-step activity tracking, pause/resume controls, and review flags.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleToggleQueuePause}
              className={`px-4 py-2.5 rounded-xl font-bold text-xs inline-flex items-center gap-2 shadow-xs transition-all ${
                isQueuePaused
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                  : "bg-amber-500 hover:bg-amber-600 text-white"
              }`}
            >
              {isQueuePaused ? (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Resume Queue
                </>
              ) : (
                <>
                  <Pause className="w-4 h-4 fill-current" />
                  Pause Queue
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── Setup Defaults Bar (Reused Across Runs) ── */}
        <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                Saved Candidate Defaults (Reused Across Runs)
              </span>
              <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded-full">
                Persistent
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-bold text-slate-700">Target Themes:</span>
              {(setupQuery.data?.defaults?.role_themes || ["Strategy Consulting", "Corporate Strategy"]).map((t) => (
                <span key={t} className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-800 font-bold text-xs">
                  {t}
                </span>
              ))}

              <span className="text-slate-300">|</span>

              <span className="font-bold text-slate-700">Experience Range:</span>
              <span className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-blue-700 font-mono font-bold text-xs">
                {setupQuery.data?.defaults?.min_experience_years || 4}–{setupQuery.data?.defaults?.max_experience_years || 10} years
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsEditingSetup(true)}
            className="px-4 py-2 rounded-xl bg-white border border-slate-200 hover:border-slate-300 text-slate-700 font-bold text-xs inline-flex items-center gap-1.5 shadow-2xs shrink-0 transition-colors"
          >
            <Settings2 className="w-3.5 h-3.5 text-blue-600" />
            Edit Themes &amp; Experience Range
          </button>
        </div>
      </div>

      {/* ── Run Configuration: Adjustable Location for Each Run ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-blue-600" />
              Adjust Location for This Run
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Adjusting location for this run leaves your saved themes and experience range defaults completely intact.
            </p>
          </div>

          <button
            type="button"
            disabled={isLoadingPreview}
            onClick={() => handleFetchPreview()}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-xs transition-all disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoadingPreview ? "animate-spin" : ""}`} />
            Refresh Preview
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Mode Selector */}
          <div className="space-y-3">
            <label className="text-xs font-extrabold uppercase tracking-wider text-slate-400 block">
              Location Mode
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  setLocationMode("prioritize");
                  handleFetchPreview(undefined, "prioritize");
                }}
                className={`p-3.5 rounded-2xl border text-left transition-all ${
                  locationMode === "prioritize"
                    ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/10"
                    : "border-slate-200 hover:border-slate-300 bg-white"
                }`}
              >
                <div className="text-xs font-extrabold">Prioritize by Location</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Preferred locations first; other eligible locations shown below.
                </div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setLocationMode("filter");
                  handleFetchPreview(undefined, "filter");
                }}
                className={`p-3.5 rounded-2xl border text-left transition-all ${
                  locationMode === "filter"
                    ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/10"
                    : "border-slate-200 hover:border-slate-300 bg-white"
                }`}
              >
                <div className="text-xs font-extrabold">Filter by Location</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Includes only jobs strictly matching selected locations.
                </div>
              </button>
            </div>
          </div>

          {/* Location Selection Pills */}
          <div className="space-y-3">
            <label className="text-xs font-extrabold uppercase tracking-wider text-slate-400 block">
              Preferred Cities for this Run
            </label>
            <div className="flex flex-wrap gap-1.5">
              {["Hyderabad", "Bengaluru", "Mumbai", "Pune", "Delhi NCR", "Chennai", "Remote (India)"].map((city) => {
                const isSelected = selectedLocations.includes(city);
                return (
                  <button
                    key={city}
                    type="button"
                    onClick={() => {
                      const next = isSelected
                        ? selectedLocations.filter((c) => c !== city)
                        : [...selectedLocations, city];
                      if (next.length === 0) return;
                      setSelectedLocations(next);
                      handleFetchPreview(next, locationMode);
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-slate-900 text-white shadow-2xs"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    <MapPin className="w-3 h-3" />
                    <span>{city}</span>
                    {isSelected && <Check className="w-3 h-3 text-emerald-400" />}
                  </button>
                );
              })}
            </div>

            {/* Unattended run setting */}
            <div className="pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600 font-medium">
                <input
                  type="checkbox"
                  checked={unattendedLowerRanked}
                  onChange={(e) => setUnattendedLowerRanked(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
                <span>For unattended runs: Allow lower-ranked eligible locations (otherwise preferred only).</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* ── Preview Table & Selection ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Eye className="w-4 h-4 text-blue-600" />
              Eligible Job Matches Preview
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Review matching openings, check cross-posting deduplication, and inspect why each job qualified.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => {
                if (!previewData) return;
                const allIds = new Set(previewData.jobs.map((j) => j.job_id));
                setSelectedJobIds(selectedJobIds.size === allIds.size ? new Set() : allIds);
              }}
              className="px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs"
            >
              {previewData && selectedJobIds.size === previewData.jobs.length ? "Deselect All" : "Select All Eligible"}
            </button>

            <button
              type="button"
              disabled={isQueueing || selectedJobIds.size === 0}
              onClick={handleQueueSelected}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-xs transition-all disabled:opacity-50"
            >
              <Bot className="w-3.5 h-3.5" />
              {isQueueing ? "Queuing..." : `Queue Selected Jobs (${selectedJobIds.size})`}
            </button>
          </div>
        </div>

        {/* Telemetry Pills */}
        {previewData && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Matches</div>
              <div className="text-lg font-black text-slate-900">{previewData.total_preview_jobs}</div>
            </div>
            <div className="p-3 bg-emerald-50/60 rounded-2xl border border-emerald-100 text-center">
              <div className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">Preferred Location</div>
              <div className="text-lg font-black text-emerald-800">{previewData.preferred_location_count}</div>
            </div>
            <div className="p-3 bg-indigo-50/60 rounded-2xl border border-indigo-100 text-center">
              <div className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider">Tracker Excluded</div>
              <div className="text-lg font-black text-indigo-800">{previewData.previously_applied_excluded_count}</div>
            </div>
            <div className="p-3 bg-amber-50/60 rounded-2xl border border-amber-100 text-center">
              <div className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Flagged for Review</div>
              <div className="text-lg font-black text-amber-800">{previewData.ambiguous_flagged_count}</div>
            </div>
          </div>
        )}

        {/* Rule checkbox */}
        <div className="p-3 bg-blue-50/50 rounded-2xl border border-blue-200/60 flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer text-xs text-blue-900 font-semibold">
            <input
              type="checkbox"
              checked={saveAsRule}
              onChange={(e) => setSaveAsRule(e.target.checked)}
              className="rounded border-blue-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
            />
            <span>Save this selection rule to automatically queue future crawler matches.</span>
          </label>
        </div>

        {/* Jobs List */}
        {isLoadingPreview ? (
          <div className="py-12 text-center text-xs text-slate-400 space-y-2">
            <RotateCw className="w-5 h-5 animate-spin mx-auto text-blue-600" />
            <div>Scanning feeds and evaluating qualification rules...</div>
          </div>
        ) : !previewData || previewData.jobs.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No matching jobs found with the current location and theme settings.
          </div>
        ) : (
          <div className="space-y-3">
            {previewData.jobs.map((job) => {
              const isSelected = selectedJobIds.has(job.job_id);
              return (
                <div
                  key={job.job_id}
                  className={`p-4 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    isSelected
                      ? "border-blue-400 bg-blue-50/20"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => {
                        const next = new Set(selectedJobIds);
                        if (e.target.checked) next.add(job.job_id);
                        else next.delete(job.job_id);
                        setSelectedJobIds(next);
                      }}
                      className="mt-1 rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                    />

                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-extrabold text-sm text-slate-900">{job.job_title}</span>
                        <span className="text-xs font-semibold text-slate-500">at {job.company_name}</span>
                        <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">
                          {job.matched_theme}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md">
                          {job.source}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-600">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {job.location} ({job.work_arrangement})
                        </span>
                        <span>•</span>
                        <span>Experience: <strong className="font-mono text-slate-700">{job.advertised_experience_range}</strong></span>
                      </div>

                      {/* Why it qualified */}
                      <div className="text-[11px] text-emerald-800 bg-emerald-50/60 border border-emerald-100 px-2.5 py-1 rounded-xl">
                        ✓ <strong>Why it qualified:</strong> {job.why_it_qualified}
                      </div>

                      {/* Ambiguity Flag */}
                      {job.has_ambiguity && (
                        <div className="text-[11px] text-amber-800 bg-amber-50/80 border border-amber-200 px-2.5 py-1 rounded-xl flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          <span>Flagged: {job.ambiguity_flags.join("; ")}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {job.job_url && (
                      <a
                        href={job.job_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold inline-flex items-center gap-1"
                      >
                        <span>View</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Persistent Queue & Chat-Style Activity Feed ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Queue Items */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <h2 className="text-base font-extrabold text-slate-900">
                Application Run Queue
              </h2>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                isQueuePaused
                  ? "bg-amber-100 text-amber-800"
                  : "bg-emerald-100 text-emerald-800"
              }`}>
                {isQueuePaused ? "Paused" : "Active"}
              </span>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-bold">
              <button
                type="button"
                onClick={() => setQueueTab("all")}
                className={`px-3 py-1 rounded-lg transition-all ${
                  queueTab === "all" ? "bg-white text-slate-900 shadow-2xs" : "text-slate-600"
                }`}
              >
                All ({queueItems.length})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("needs_input")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "needs_input" ? "bg-white text-amber-700 shadow-2xs font-extrabold" : "text-slate-600"
                }`}
              >
                Needs Input ({needsInputCount})
              </button>
            </div>
          </div>

          {filteredQueueItems.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              No jobs currently in this queue view. Select eligible jobs in the preview above to populate.
            </div>
          ) : (
            <div className="space-y-3">
              {filteredQueueItems.map((item) => (
                <div
                  key={item.queue_item_id}
                  className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    item.status === "needs_input"
                      ? "border-amber-300 bg-amber-50/40"
                      : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-sm text-slate-900">{item.job_title}</span>
                      <span className="text-xs text-slate-500">· {item.company_name}</span>
                    </div>
                    <div className="text-xs text-slate-600 flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] font-bold">
                        {item.matched_theme}
                      </span>
                      <span>{item.location}</span>
                    </div>
                    {item.has_ambiguity && (
                      <div className="text-[11px] text-amber-800">
                        ⚠️ <strong>Action needed:</strong> {item.ambiguity_flags.join("; ")}
                      </div>
                    )}
                  </div>

                  {item.status === "needs_input" ? (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleResolveNeedsInput(item.queue_item_id, "approve")}
                        className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs"
                      >
                        Approve for Queue
                      </button>
                      <button
                        type="button"
                        onClick={() => handleResolveNeedsInput(item.queue_item_id, "dismiss")}
                        className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold text-xs"
                      >
                        Dismiss
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] font-bold px-2 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wider">
                        Queued
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Chat-Style Activity Feed */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-blue-600" />
                <h3 className="text-base font-extrabold text-slate-900">Queue Activity Feed</h3>
              </div>
              <span className="text-[10px] font-bold text-slate-400 font-mono">Live Sync</span>
            </div>

            <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
              {activityFeed.slice(-15).map((act) => (
                <div key={act.id} className="p-3 rounded-2xl bg-slate-50 border border-slate-100 space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-extrabold text-blue-700 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-blue-500" />
                      Auto Apply Agent
                    </span>
                    <span className="text-slate-400 font-mono">
                      {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed font-medium">
                    {act.message}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Edit Setup Defaults Modal ── */}
      {isEditingSetup && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-extrabold text-slate-900">Edit Auto Apply Defaults</h3>
              <button
                type="button"
                onClick={() => setIsEditingSetup(false)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Role themes */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-extrabold text-slate-700">Role Themes</label>
                  <button
                    type="button"
                    onClick={handlePrepopulate}
                    className="text-[11px] font-bold text-blue-600 hover:underline"
                  >
                    Prepopulate from Profile
                  </button>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {editThemes.map((th) => (
                    <span key={th} className="px-2.5 py-1 rounded-xl bg-slate-100 text-slate-800 text-xs font-bold flex items-center gap-1.5">
                      {th}
                      <button
                        type="button"
                        onClick={() => setEditThemes(editThemes.filter((t) => t !== th))}
                        className="text-slate-400 hover:text-rose-600 font-bold"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={newThemeInput}
                    onChange={(e) => setNewThemeInput(e.target.value)}
                    placeholder="Add theme (e.g. Commercial Due Diligence)"
                    className="flex-1 px-3.5 py-2 rounded-xl border border-slate-200 text-xs outline-none focus:border-blue-600"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newThemeInput.trim()) {
                        e.preventDefault();
                        if (!editThemes.includes(newThemeInput.trim())) {
                          setEditThemes([...editThemes, newThemeInput.trim()]);
                        }
                        setNewThemeInput("");
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      if (newThemeInput.trim() && !editThemes.includes(newThemeInput.trim())) {
                        setEditThemes([...editThemes, newThemeInput.trim()]);
                        setNewThemeInput("");
                      }
                    }}
                    className="px-3.5 py-2 rounded-xl bg-slate-900 text-white font-bold text-xs"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Experience Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-extrabold text-slate-700 block mb-1">Min Experience (Years)</label>
                  <input
                    type="number"
                    min={0}
                    max={30}
                    value={editMinExp}
                    onChange={(e) => setEditMinExp(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none focus:border-blue-600"
                  />
                </div>
                <div>
                  <label className="text-xs font-extrabold text-slate-700 block mb-1">Max Experience (Years)</label>
                  <input
                    type="number"
                    min={0}
                    max={40}
                    value={editMaxExp}
                    onChange={(e) => setEditMaxExp(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none focus:border-blue-600"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsEditingSetup(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSavingSetup}
                onClick={handleSaveDefaults}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs"
              >
                {isSavingSetup ? "Saving..." : "Save Defaults"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
