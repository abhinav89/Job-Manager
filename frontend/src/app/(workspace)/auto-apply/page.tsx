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
  BookOpen,
  Zap,
  HelpCircle,
  BookmarkCheck,
  Split,
  FileCheck2,
  SendHorizontal,
} from "lucide-react";

import { API_URL } from "@/lib/api";
import {
  useAutoApplySetup,
  useAutoApplyQueue,
  useAnswerBank,
  queryKeys,
  type AutoApplyPreviewJob,
  type AutoApplyPreviewResponse,
  type AutoApplyQueueItem,
  type AnswerBankItem,
  type WordingChange,
} from "@/lib/queries";

export default function AutoApplyPage() {
  const queryClient = useQueryClient();

  // Queries
  const setupQuery = useAutoApplySetup();
  const queueQuery = useAutoApplyQueue();
  const answerBankQuery = useAnswerBank();

  // Run-level location adjustments (Independent from saved defaults!)
  const [locationMode, setLocationMode] = useState<"prioritize" | "filter">("prioritize");
  const [selectedLocations, setSelectedLocations] = useState<string[]>(["Hyderabad"]);
  const [unattendedLowerRanked, setUnattendedLowerRanked] = useState<boolean>(false);

  // Phase 3 & 4: Approval & Portal Automation Settings
  const [reviewTailoredCv, setReviewTailoredCv] = useState<boolean>(true);
  const [reviewBeforeSubmission, setReviewBeforeSubmission] = useState<boolean>(true);
  const [allowUnattendedSubmission, setAllowUnattendedSubmission] = useState<boolean>(false);
  const [dailySubmissionLimit, setDailySubmissionLimit] = useState<number>(5);
  const [allowWorkdayAccountCreation, setAllowWorkdayAccountCreation] = useState<boolean>(false);

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

  // Queue state & tabs
  const [queueTab, setQueueTab] = useState<
    | "all"
    | "approved_for_submission"
    | "paused_for_human_checkpoint"
    | "submission_unclear"
    | "handoff_ready"
    | "applied"
    | "waiting_cv_review"
    | "waiting_submission_review"
    | "needs_answer"
    | "queued"
    | "needs_input"
  >("all");
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);

  // Phase 2: Answer Bank Modal State
  const [isAnswerBankOpen, setIsAnswerBankOpen] = useState(false);
  const [editableAnswers, setEditableAnswers] = useState<AnswerBankItem[]>([]);
  const [isSavingBank, setIsSavingBank] = useState(false);

  // Phase 2: Answering Unfamiliar Question Modal State
  const [answeringItem, setAnsweringItem] = useState<AutoApplyQueueItem | null>(null);
  const [answerTextInput, setAnswerTextInput] = useState("");
  const [selectedOptionInput, setSelectedOptionInput] = useState("");
  const [scopeInput, setScopeInput] = useState<"save_as_default" | "save_for_rule" | "use_once" | "ask_every_time">("save_as_default");
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false);

  // Phase 3: CV Review Diff Modal State
  const [reviewingCvItem, setReviewingCvItem] = useState<AutoApplyQueueItem | null>(null);

  // Phase 3: Submission Review Modal State
  const [reviewingItem, setReviewingItem] = useState<AutoApplyQueueItem | null>(null);

  // Phase 4: Report Manual Submission Modal State
  const [reportModalItem, setReportModalItem] = useState<AutoApplyQueueItem | null>(null);
  const [reportConfirmationRef, setReportConfirmationRef] = useState("");
  const [reportNotes, setReportNotes] = useState("");
  const [isSubmittingReport, setIsSubmittingReport] = useState(false);

  // Phase 4: Action In-Flight States
  const [resumingCheckpointId, setResumingCheckpointId] = useState<string | null>(null);
  const [verifyingUnclearId, setVerifyingUnclearId] = useState<string | null>(null);
  const [submittingPortalId, setSubmittingPortalId] = useState<string | null>(null);

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
      setReviewTailoredCv(defs.review_tailored_cv ?? true);
      setReviewBeforeSubmission(defs.review_before_portal_submission ?? true);
      setAllowUnattendedSubmission(defs.allow_unattended_submission ?? false);
      setDailySubmissionLimit(defs.daily_submission_limit ?? 5);
      setAllowWorkdayAccountCreation(defs.allow_workday_account_creation ?? false);
    }
  }, [setupQuery.data]);

  // Sync Answer Bank editable list
  useEffect(() => {
    if (answerBankQuery.data?.answer_bank?.answers) {
      setEditableAnswers(answerBankQuery.data.answer_bank.answers);
    }
  }, [answerBankQuery.data]);

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
          review_tailored_cv: reviewTailoredCv,
          review_before_portal_submission: reviewBeforeSubmission,
          allow_unattended_submission: allowUnattendedSubmission,
          daily_submission_limit: dailySubmissionLimit,
          allow_workday_account_creation: allowWorkdayAccountCreation,
        }),
      });
      if (res.ok) {
        toast.success("Saved role themes, limits & portal automation settings!");
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

  // Phase 3: Run Queue Engine with independent approvals
  const handleRunQueueProcessor = async () => {
    setIsProcessingQueue(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rule_overrides: {
            review_tailored_cv: reviewTailoredCv,
            review_before_portal_submission: reviewBeforeSubmission,
          },
        }),
      });
      const data = await res.json();
      if (res.ok) {
        if (data.status === "queue_paused") {
          toast.info(data.message);
        } else {
          toast.success(
            `Processed: ${data.waiting_cv_review_count} waiting CV review, ${data.waiting_submission_review_count} waiting submission review, ${data.approved_for_submission_count} approved for submit.`
          );
        }
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error("Failed to run queue worker.");
      }
    } catch {
      toast.error("Network error running queue worker.");
    } finally {
      setIsProcessingQueue(false);
    }
  };

  // Phase 3: Approve Tailored CV
  const handleApproveCv = async (itemId: string) => {
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/approve-cv`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Tailored CV approved! Advancing to application package.");
        setReviewingCvItem(null);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not approve CV.");
      }
    } catch {
      toast.error("Network error approving CV.");
    }
  };

  // Phase 3: Approve Final Submission
  const handleApproveSubmission = async (itemId: string) => {
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/approve-submission`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Final submission package approved!");
        setReviewingItem(null);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not approve submission.");
      }
    } catch {
      toast.error("Network error approving submission.");
    }
  };

  // Phase 4: Submit to Company Portal
  const handleSubmitToPortal = async (itemId: string) => {
    setSubmittingPortalId(itemId);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/submit-portal`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        if (data.status === "applied") {
          toast.success(`Submission confirmed! Ref: ${data.confirmation_ref}`);
        } else if (data.status === "paused_for_human_checkpoint") {
          toast.warning(`Interactive action needed (${data.checkpoint_type}). Please check instructions.`);
        } else if (data.status === "submission_unclear") {
          toast.warning(`Submission outcome unclear. Awaiting verification.`);
        } else {
          toast.info(data.message || "Submitted to portal.");
        }
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Portal submission failed.");
      }
    } catch {
      toast.error("Network error during portal submission.");
    } finally {
      setSubmittingPortalId(null);
    }
  };

  // Phase 4: Resume Human Checkpoint (Workday MFA/CAPTCHA)
  const handleResumeCheckpoint = async (itemId: string) => {
    setResumingCheckpointId(itemId);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/resume-checkpoint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checkpoint_resolved: true }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Checkpoint resolved! Confirmed applied: ${data.confirmation_ref}`);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not resume checkpoint.");
      }
    } catch {
      toast.error("Network error resuming checkpoint.");
    } finally {
      setResumingCheckpointId(null);
    }
  };

  // Phase 4: Verify Ambiguous/Unclear Submission
  const handleVerifyUnclear = async (itemId: string, confirmed: boolean) => {
    setVerifyingUnclearId(itemId);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/verify-unclear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not verify unclear submission.");
      }
    } catch {
      toast.error("Network error verifying submission.");
    } finally {
      setVerifyingUnclearId(null);
    }
  };

  // Phase 4: Prepare Portal Handoff Package (Naukri / iimjobs / LinkedIn)
  const handlePrepareHandoff = async (itemId: string) => {
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${itemId}/handoff`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Handoff package prepared for ${data.portal}!`);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not prepare handoff package.");
      }
    } catch {
      toast.error("Network error preparing handoff package.");
    }
  };

  // Phase 4: Open Report Applied Modal
  const handleOpenReportModal = (item: AutoApplyQueueItem) => {
    setReportModalItem(item);
    setReportConfirmationRef("");
    setReportNotes("");
  };

  // Phase 4: Report Candidate Manual Submission
  const handleReportApplied = async () => {
    if (!reportModalItem) return;
    setIsSubmittingReport(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${reportModalItem.queue_item_id}/report-applied`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirmation_ref: reportConfirmationRef.trim() || undefined,
          notes: reportNotes.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || "Manual application recorded and synced to tracker!");
        setReportModalItem(null);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
      } else {
        toast.error(data.detail || "Could not report applied.");
      }
    } catch {
      toast.error("Network error reporting application.");
    } finally {
      setIsSubmittingReport(false);
    }
  };

  // Phase 2: Save Answer Bank Updates
  const handleSaveAnswerBank = async () => {
    setIsSavingBank(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/answer-bank`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: editableAnswers }),
      });
      if (res.ok) {
        toast.success("Answer Bank updated successfully!");
        setIsAnswerBankOpen(false);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyAnswerBank });
      } else {
        toast.error("Failed to update Answer Bank.");
      }
    } catch {
      toast.error("Network error updating Answer Bank.");
    } finally {
      setIsSavingBank(false);
    }
  };

  // Phase 2: Open Answering Card/Modal
  const handleOpenAnswering = (item: AutoApplyQueueItem) => {
    setAnsweringItem(item);
    setSelectedOptionInput(item.pending_question?.options?.[0] || "");
    setAnswerTextInput("");
    setScopeInput("save_as_default");
  };

  // Phase 2: Submit Answer for Paused Job
  const handleSubmitAnswer = async () => {
    if (!answeringItem || !answeringItem.pending_question) return;
    const finalAnswer = selectedOptionInput || answerTextInput;
    if (!finalAnswer.trim()) {
      toast.error("Please provide an answer.");
      return;
    }

    setIsSubmittingAnswer(true);
    try {
      const res = await fetch(`${API_URL}/auto-apply/queue/${answeringItem.queue_item_id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer_text: finalAnswer,
          scope: scopeInput,
          selected_option: selectedOptionInput || undefined,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || "Answer saved! Job resumed.");
        setAnsweringItem(null);
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyQueue });
        queryClient.invalidateQueries({ queryKey: queryKeys.autoApplyAnswerBank });
      } else {
        toast.error(data.detail || "Failed to submit answer.");
      }
    } catch {
      toast.error("Network error submitting answer.");
    } finally {
      setIsSubmittingAnswer(false);
    }
  };

  const queue = queueQuery.data?.queue;
  const queueItems: AutoApplyQueueItem[] = queue?.queue_items || [];
  const activityFeed = queue?.activity_feed || [];
  const isQueuePaused = queue?.queue_status === "paused";

  const queuedCount = queueItems.filter((i) => i.status === "queued").length;
  const waitingCvCount = queueItems.filter((i) => i.status === "waiting_cv_review").length;
  const needsAnswerCount = queueItems.filter((i) => i.status === "needs_answer").length;
  const waitingSubCount = queueItems.filter((i) => i.status === "waiting_submission_review").length;
  const approvedCount = queueItems.filter((i) => i.status === "approved_for_submission" || i.status === "ready_for_review").length;
  const checkpointCount = queueItems.filter((i) => i.status === "paused_for_human_checkpoint").length;
  const unclearCount = queueItems.filter((i) => i.status === "submission_unclear").length;
  const handoffCount = queueItems.filter((i) => i.status === "handoff_ready").length;
  const appliedCount = queueItems.filter((i) => i.status === "applied").length;
  const needsInputCount = queueItems.filter((i) => i.status === "needs_input").length;

  const filteredQueueItems = queueItems.filter((item) => {
    if (queueTab === "queued") return item.status === "queued" || item.status === "in_progress";
    if (queueTab === "waiting_cv_review") return item.status === "waiting_cv_review";
    if (queueTab === "needs_answer") return item.status === "needs_answer";
    if (queueTab === "waiting_submission_review") return item.status === "waiting_submission_review";
    if (queueTab === "approved_for_submission") return item.status === "approved_for_submission" || item.status === "ready_for_review";
    if (queueTab === "paused_for_human_checkpoint") return item.status === "paused_for_human_checkpoint";
    if (queueTab === "submission_unclear") return item.status === "submission_unclear";
    if (queueTab === "handoff_ready") return item.status === "handoff_ready";
    if (queueTab === "applied") return item.status === "applied";
    if (queueTab === "needs_input") return item.status === "needs_input";
    return true;
  });

  const answerBank = answerBankQuery.data?.answer_bank;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Top Header ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold border border-blue-200">
              <Bot className="w-3.5 h-3.5" />
              Phase 4 · Portal Automation, Workday Accounts &amp; Adapter Handoffs
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Auto Apply Agent &amp; Application Queue
            </h1>
            <p className="text-xs text-slate-500 max-w-2xl leading-relaxed">
              Automates multi-step company portal submissions (Greenhouse, Lever, Workday) with confirmation tracking,
              pauses for interactive human checkpoints (MFA/CAPTCHA), prepares dedicated handoff packages for Naukri &amp; iimjobs,
              and strictly records confirmed applications in your Job Tracker.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Answer Bank Button */}
            <button
              type="button"
              onClick={() => setIsAnswerBankOpen(true)}
              className="px-4 py-2.5 rounded-xl border border-slate-200 hover:border-blue-400 bg-white hover:bg-blue-50/40 text-slate-700 font-extrabold text-xs inline-flex items-center gap-2 shadow-2xs transition-all"
            >
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span>Answer Bank ({answerBank?.answers?.length || 8})</span>
              <span className="px-1.5 py-0.5 rounded-md bg-slate-100 text-[10px] font-mono text-slate-600">
                v{answerBank?.version || 1}
              </span>
            </button>

            {/* Run Queue Worker */}
            <button
              type="button"
              disabled={isProcessingQueue}
              onClick={handleRunQueueProcessor}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs inline-flex items-center gap-2 shadow-xs transition-all disabled:opacity-50"
            >
              <Zap className={`w-4 h-4 ${isProcessingQueue ? "animate-spin" : "fill-current"}`} />
              <span>{isProcessingQueue ? "Running Queue Worker..." : "Run Queue Worker"}</span>
            </button>

            {/* Pause / Resume Queue */}
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

        {/* ── Saved Defaults & Independent Approval Settings Strip ── */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
              Active Candidate Defaults &amp; Review Policy
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-0.5 text-xs">
              <span className="font-bold text-slate-700">Themes:</span>
              {(setupQuery.data?.defaults?.role_themes || []).map((th) => (
                <span
                  key={th}
                  className="px-2.5 py-0.5 rounded-lg bg-white border border-slate-200 text-xs font-bold text-slate-800 shadow-2xs"
                >
                  {th}
                </span>
              ))}
              <span className="text-slate-300">|</span>
              <span className="font-bold text-slate-700">Target Range:</span>
              <span className="px-2 py-0.5 rounded-lg bg-blue-50 border border-blue-200 text-xs font-black text-blue-700">
                {setupQuery.data?.defaults?.min_experience_years || 4}–{setupQuery.data?.defaults?.max_experience_years || 7} yrs
              </span>
              <span className="text-slate-300">|</span>

              {/* Independent Review Pills */}
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold border ${
                  reviewTailoredCv
                    ? "bg-violet-50 text-violet-700 border-violet-200"
                    : "bg-slate-100 text-slate-500 border-slate-200"
                }`}>
                  CV Review: <strong>{reviewTailoredCv ? "ON (Waits)" : "OFF (Auto)"}</strong>
                </span>
                <span className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold border ${
                  reviewBeforeSubmission
                    ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                    : "bg-slate-100 text-slate-500 border-slate-200"
                }`}>
                  Submit Review: <strong>{reviewBeforeSubmission ? "ON (Waits)" : "OFF (Auto)"}</strong>
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsEditingSetup(true)}
            className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-extrabold text-xs inline-flex items-center gap-1.5 shadow-2xs shrink-0 self-start md:self-auto"
          >
            <Settings2 className="w-3.5 h-3.5 text-slate-500" />
            <span>Edit Settings</span>
          </button>
        </div>
      </div>

      {/* ── Run Configuration & Filter Controls ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-blue-600" />
            <h2 className="text-base font-extrabold text-slate-900">
              Run Configuration &amp; Review Policy
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Configure run location and independent approval gates.
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Location Mode */}
          <div className="space-y-2">
            <label className="text-xs font-extrabold text-slate-700 block">Location Mode</label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-2xl text-xs font-bold">
              <button
                type="button"
                onClick={() => {
                  setLocationMode("prioritize");
                  handleFetchPreview(selectedLocations, "prioritize");
                }}
                className={`py-2 px-3 rounded-xl transition-all ${
                  locationMode === "prioritize"
                    ? "bg-white text-blue-700 shadow-2xs font-black"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Prioritize
              </button>
              <button
                type="button"
                onClick={() => {
                  setLocationMode("filter");
                  handleFetchPreview(selectedLocations, "filter");
                }}
                className={`py-2 px-3 rounded-xl transition-all ${
                  locationMode === "filter"
                    ? "bg-white text-blue-700 shadow-2xs font-black"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Filter Strict
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              {locationMode === "prioritize"
                ? "Preferred locations listed first; other eligible openings appear below."
                : "Restricts results strictly to selected locations and work arrangements."}
            </p>
          </div>

          {/* Target Cities */}
          <div className="space-y-2">
            <label className="text-xs font-extrabold text-slate-700 block">Preferred Target Cities</label>
            <div className="flex flex-wrap items-center gap-1.5">
              {["Hyderabad", "Bengaluru", "Mumbai", "Delhi NCR", "Pune", "Remote"].map((city) => {
                const isSelected = selectedLocations.includes(city);
                return (
                  <button
                    key={city}
                    type="button"
                    onClick={() => {
                      const next = isSelected
                        ? selectedLocations.filter((c) => c !== city)
                        : [...selectedLocations, city];
                      if (next.length === 0) {
                        toast.error("Please keep at least one target location.");
                        return;
                      }
                      setSelectedLocations(next);
                      handleFetchPreview(next, locationMode);
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                      isSelected
                        ? "bg-blue-600 border-blue-600 text-white shadow-2xs"
                        : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {city} {isSelected ? "✓" : "+"}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Phase 3: Independent Approvals Checkboxes */}
          <div className="space-y-3 p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-extrabold text-slate-900 flex items-center gap-1.5">
              <Split className="w-4 h-4 text-blue-600" />
              Independent Approval Checkpoints
            </div>

            <div className="space-y-2">
              <label className="flex items-start gap-2 cursor-pointer text-xs text-slate-700 font-medium">
                <input
                  type="checkbox"
                  checked={reviewTailoredCv}
                  onChange={(e) => setReviewTailoredCv(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 mt-0.5"
                />
                <div>
                  <strong className="block text-slate-900">Review tailored CV</strong>
                  <span className="text-[11px] text-slate-500">Waits before attachment. Check diff &amp; PDF preview.</span>
                </div>
              </label>

              <label className="flex items-start gap-2 cursor-pointer text-xs text-slate-700 font-medium">
                <input
                  type="checkbox"
                  checked={reviewBeforeSubmission}
                  onChange={(e) => setReviewBeforeSubmission(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 mt-0.5"
                />
                <div>
                  <strong className="block text-slate-900">Review before portal submission</strong>
                  <span className="text-[11px] text-slate-500">Waits after form and CV attachment are ready.</span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* ── Preview & Selection Section ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-blue-600" />
            <h2 className="text-base font-extrabold text-slate-900">
              Matches Preview &amp; Selection
            </h2>
            {previewData && (
              <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-bold font-mono">
                {previewData.jobs.length} roles
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                if (previewData) {
                  const allIds = new Set(previewData.jobs.map((j) => j.job_id));
                  setSelectedJobIds(allIds);
                }
              }}
              className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={() => setSelectedJobIds(new Set())}
              className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold"
            >
              Clear
            </button>
            <button
              type="button"
              disabled={isQueueing || selectedJobIds.size === 0}
              onClick={handleQueueSelected}
              className="px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-extrabold shadow-xs transition-all disabled:opacity-50"
            >
              {isQueueing ? "Queueing..." : `Add Selected to Queue (${selectedJobIds.size})`}
            </button>
          </div>
        </div>

        {/* Stats strip */}
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
              const isNaukriOrIimjobs = (job.source || "").toLowerCase().includes("naukri") || (job.source || "").toLowerCase().includes("iimjobs");

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
                        {isNaukriOrIimjobs ? (
                          <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[10px] font-mono">
                            Single Profile CV
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-md bg-violet-50 text-violet-700 border border-violet-200 text-[10px] font-bold">
                            Tailors Job-Specific CV
                          </span>
                        )}
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
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
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
            <div className="flex flex-wrap items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-bold">
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
                onClick={() => setQueueTab("approved_for_submission")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "approved_for_submission"
                    ? "bg-white text-emerald-700 shadow-2xs font-extrabold"
                    : approvedCount > 0
                    ? "text-emerald-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Ready ({approvedCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("paused_for_human_checkpoint")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "paused_for_human_checkpoint"
                    ? "bg-white text-amber-700 shadow-2xs font-extrabold"
                    : checkpointCount > 0
                    ? "text-amber-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Checkpoints ({checkpointCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("submission_unclear")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "submission_unclear"
                    ? "bg-white text-orange-700 shadow-2xs font-extrabold"
                    : unclearCount > 0
                    ? "text-orange-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Unclear ({unclearCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("handoff_ready")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "handoff_ready"
                    ? "bg-white text-blue-700 shadow-2xs font-extrabold"
                    : handoffCount > 0
                    ? "text-blue-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Handoffs ({handoffCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("applied")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "applied"
                    ? "bg-white text-emerald-700 shadow-2xs font-extrabold"
                    : appliedCount > 0
                    ? "text-emerald-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Applied ({appliedCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("waiting_cv_review")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "waiting_cv_review"
                    ? "bg-white text-violet-700 shadow-2xs font-extrabold"
                    : waitingCvCount > 0
                    ? "text-violet-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                CV Review ({waitingCvCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("waiting_submission_review")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "waiting_submission_review"
                    ? "bg-white text-indigo-700 shadow-2xs font-extrabold"
                    : waitingSubCount > 0
                    ? "text-indigo-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Submit Review ({waitingSubCount})
              </button>
              <button
                type="button"
                onClick={() => setQueueTab("needs_answer")}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  queueTab === "needs_answer"
                    ? "bg-white text-rose-700 shadow-2xs font-extrabold"
                    : needsAnswerCount > 0
                    ? "text-rose-600 font-extrabold"
                    : "text-slate-600"
                }`}
              >
                Needs Answer ({needsAnswerCount})
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
              No jobs currently in this queue view. Click 'Run Queue Worker' or add jobs from preview.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredQueueItems.map((item) => {
                const isWaitingCv = item.status === "waiting_cv_review";
                const isWaitingSub = item.status === "waiting_submission_review";
                const isApprovedSub = item.status === "approved_for_submission" || item.status === "ready_for_review";
                const isCheckpoint = item.status === "paused_for_human_checkpoint";
                const isUnclear = item.status === "submission_unclear";
                const isHandoff = item.status === "handoff_ready";
                const isApplied = item.status === "applied";
                const isNeedsAnswer = item.status === "needs_answer";
                const isNeedsInput = item.status === "needs_input";

                return (
                  <div
                    key={item.queue_item_id}
                    className={`p-4 sm:p-5 rounded-2xl border transition-all space-y-3 ${
                      isApplied
                        ? "border-emerald-300 bg-emerald-50/20"
                        : isCheckpoint
                        ? "border-amber-400 bg-amber-50/30"
                        : isUnclear
                        ? "border-orange-400 bg-orange-50/30"
                        : isHandoff
                        ? "border-blue-400 bg-blue-50/30"
                        : isWaitingCv
                        ? "border-violet-300 bg-violet-50/30"
                        : isWaitingSub
                        ? "border-indigo-300 bg-indigo-50/30"
                        : isApprovedSub
                        ? "border-emerald-300 bg-emerald-50/20"
                        : isNeedsAnswer
                        ? "border-rose-300 bg-rose-50/30"
                        : isNeedsInput
                        ? "border-amber-300 bg-amber-50/40"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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
                          <span>•</span>
                          <span className="text-[10px] text-slate-400 font-mono">{item.source}</span>
                          {item.tailored_cv?.skipped && (
                            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                              Single Profile CV
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Status Badges & Quick Action Controls */}
                      <div className="flex items-center gap-2 shrink-0">
                        {isApplied ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-emerald-100 text-emerald-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              Applied
                            </span>
                            <Link
                              href="/tracker"
                              className="px-3 py-1.5 rounded-xl border border-emerald-200 bg-white hover:bg-emerald-50 text-emerald-700 font-extrabold text-xs shadow-2xs inline-flex items-center gap-1"
                            >
                              <span>Tracker</span>
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                          </div>
                        ) : isCheckpoint ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-amber-100 text-amber-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                              Human Checkpoint
                            </span>
                            {item.job_url && (
                              <a
                                href={item.job_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-3 py-1.5 rounded-xl border border-amber-300 bg-white hover:bg-amber-50 text-amber-800 font-extrabold text-xs shadow-2xs inline-flex items-center gap-1"
                              >
                                <span>Open Portal</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                            <button
                              type="button"
                              disabled={resumingCheckpointId === item.queue_item_id}
                              onClick={() => handleResumeCheckpoint(item.queue_item_id)}
                              className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-extrabold text-xs shadow-2xs inline-flex items-center gap-1.5"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>{resumingCheckpointId === item.queue_item_id ? "Resuming..." : "Resume Checkpoint"}</span>
                            </button>
                          </div>
                        ) : isUnclear ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-orange-100 text-orange-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
                              Status Unclear
                            </span>
                            <button
                              type="button"
                              disabled={verifyingUnclearId === item.queue_item_id}
                              onClick={() => handleVerifyUnclear(item.queue_item_id, true)}
                              className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs shadow-2xs"
                            >
                              Verify Acknowledged
                            </button>
                            <button
                              type="button"
                              disabled={verifyingUnclearId === item.queue_item_id}
                              onClick={() => handleVerifyUnclear(item.queue_item_id, false)}
                              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-extrabold text-xs shadow-2xs"
                            >
                              Reset for Retry
                            </button>
                          </div>
                        ) : isHandoff ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-blue-100 text-blue-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <Bot className="w-3.5 h-3.5 text-blue-600" />
                              Handoff Ready
                            </span>
                            {item.job_url && (
                              <a
                                href={item.job_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs shadow-2xs inline-flex items-center gap-1"
                              >
                                <span>Open {item.handoff_package?.portal || item.source}</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                            <button
                              type="button"
                              onClick={() => handleOpenReportModal(item)}
                              className="px-3.5 py-1.5 rounded-xl border border-blue-200 bg-white hover:bg-blue-50 text-blue-700 font-extrabold text-xs shadow-2xs"
                            >
                              Report Applied
                            </button>
                          </div>
                        ) : isWaitingCv ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-violet-100 text-violet-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <FileCheck2 className="w-3.5 h-3.5" />
                              CV Review
                            </span>
                            <button
                              type="button"
                              onClick={() => setReviewingCvItem(item)}
                              className="px-3 py-1.5 rounded-xl border border-violet-200 bg-white hover:bg-violet-50 text-violet-700 font-extrabold text-xs shadow-2xs"
                            >
                              Inspect Diff
                            </button>
                            <button
                              type="button"
                              onClick={() => handleApproveCv(item.queue_item_id)}
                              className="px-3.5 py-1.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-extrabold text-xs shadow-2xs"
                            >
                              Approve CV
                            </button>
                          </div>
                        ) : isWaitingSub ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-indigo-100 text-indigo-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <SendHorizontal className="w-3.5 h-3.5" />
                              Submit Review
                            </span>
                            <button
                              type="button"
                              onClick={() => setReviewingItem(item)}
                              className="px-3 py-1.5 rounded-xl border border-indigo-200 bg-white hover:bg-indigo-50 text-indigo-700 font-extrabold text-xs shadow-2xs"
                            >
                              Review Package
                            </button>
                            <button
                              type="button"
                              onClick={() => handleApproveSubmission(item.queue_item_id)}
                              className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs shadow-2xs"
                            >
                              Approve Submit
                            </button>
                          </div>
                        ) : isApprovedSub ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-emerald-100 text-emerald-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              Ready to Submit
                            </span>
                            {((item.source || "").toLowerCase().includes("naukri") || (item.source || "").toLowerCase().includes("iimjobs")) ? (
                              <button
                                type="button"
                                onClick={() => handlePrepareHandoff(item.queue_item_id)}
                                className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs shadow-2xs"
                              >
                                Prepare Handoff
                              </button>
                            ) : (
                              <button
                                type="button"
                                disabled={submittingPortalId === item.queue_item_id}
                                onClick={() => handleSubmitToPortal(item.queue_item_id)}
                                className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs shadow-2xs inline-flex items-center gap-1.5"
                              >
                                <SendHorizontal className="w-3.5 h-3.5" />
                                <span>{submittingPortalId === item.queue_item_id ? "Submitting..." : "Submit to Portal"}</span>
                              </button>
                            )}
                            {item.job_url && (
                              <a
                                href={item.job_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold shadow-2xs inline-flex items-center gap-1"
                              >
                                <span>Portal</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                        ) : isNeedsAnswer ? (
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-1 rounded-xl bg-rose-100 text-rose-800 text-xs font-black uppercase tracking-wider flex items-center gap-1">
                              <HelpCircle className="w-3.5 h-3.5" />
                              Needs Answer
                            </span>
                            <button
                              type="button"
                              onClick={() => handleOpenAnswering(item)}
                              className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs shadow-2xs"
                            >
                              Answer
                            </button>
                          </div>
                        ) : isNeedsInput ? (
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleResolveNeedsInput(item.queue_item_id, "approve")}
                              className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs"
                            >
                              Approve
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
                          <span className="text-[10px] font-bold px-2 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wider">
                            Queued
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Applied Details Snippet */}
                    {isApplied && (
                      <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2 text-emerald-900 font-bold">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>Confirmation ID: <strong className="font-mono text-emerald-800">{item.confirmation_ref || "Recorded"}</strong></span>
                          {item.date_applied && <span className="text-[11px] text-emerald-600 font-normal">· Date Applied: {item.date_applied}</span>}
                        </div>
                        <span className="text-[10px] font-mono font-bold bg-white px-2 py-0.5 rounded-md border border-emerald-200 text-emerald-800">
                          Synced to DealOS Job Tracker
                        </span>
                      </div>
                    )}

                    {/* Human Checkpoint Alert Snippet */}
                    {isCheckpoint && (
                      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs space-y-2">
                        <div className="flex items-center gap-2 font-black text-amber-900 uppercase text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                          Checkpoint Type: {item.checkpoint_type || "Interactive MFA / CAPTCHA"}
                        </div>
                        <p className="text-amber-800 text-xs leading-relaxed font-medium">
                          {item.checkpoint_instructions || "Action required in portal browser. Complete the check, then click 'Resume Checkpoint'."}
                        </p>
                      </div>
                    )}

                    {/* Ambiguous Submission Alert Snippet */}
                    {isUnclear && (
                      <div className="p-3.5 rounded-xl bg-orange-50 border border-orange-200 text-xs space-y-2">
                        <div className="flex items-center gap-2 font-black text-orange-900 text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
                          Submission Policy Hold
                        </div>
                        <p className="text-orange-800 text-xs leading-relaxed font-medium">
                          {item.unclear_reason || "Portal response timed out or returned ambiguous acknowledgment. Verify receipt before retrying."}
                        </p>
                      </div>
                    )}

                    {/* Handoff Package Details Snippet */}
                    {isHandoff && item.handoff_package && (
                      <div className="p-3.5 rounded-xl bg-blue-50/80 border border-blue-200 text-xs space-y-2">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-extrabold text-blue-900 uppercase">
                            {item.handoff_package.portal?.toUpperCase()} Handoff Package
                          </span>
                          <span className="text-blue-700 font-bold">
                            CV: {item.handoff_package.attached_cv_type || "Single Profile CV"}
                          </span>
                        </div>
                        <p className="text-blue-800 text-xs leading-relaxed font-medium">
                          {item.handoff_package.portal_instructions}
                        </p>
                        {item.handoff_package.prepared_pitch && (
                          <div className="p-2 rounded-lg bg-white border border-blue-100 text-slate-700 text-xs italic">
                            "{item.handoff_package.prepared_pitch}"
                          </div>
                        )}
                      </div>
                    )}

                    {/* Wording Diff Snippet (If waiting CV review) */}
                    {isWaitingCv && item.tailored_cv?.wording_changes && item.tailored_cv.wording_changes.length > 0 && (
                      <div className="p-3.5 rounded-xl bg-white border border-violet-200 shadow-2xs space-y-2">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-extrabold text-violet-800">
                            Wording Changes ({item.tailored_cv.wording_changes.length} sections tailored)
                          </span>
                          <span className="text-[10px] font-mono text-slate-500">
                            Page Budget: {item.tailored_cv.page_count} pages · {item.tailored_cv.overflow_status}
                          </span>
                        </div>
                        <div className="text-xs text-slate-700 line-clamp-2 italic bg-slate-50 p-2 rounded-lg border border-slate-100">
                          "{item.tailored_cv.wording_changes[0].tailored}"
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
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

            <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
              {activityFeed.slice(-25).map((act) => (
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
                  {act.badge && (
                    <div className="pt-1">
                      <span className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[9px] font-bold text-slate-500">
                        {act.badge}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Phase 3: Tailored CV Review & Diff Modal ── */}
      {reviewingCvItem && reviewingCvItem.tailored_cv && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-3xl w-full p-6 sm:p-8 space-y-5 shadow-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-violet-50 text-violet-700 text-[10px] font-black uppercase">
                  Checkpoint 1: Review Tailored CV
                </div>
                <h3 className="text-base font-extrabold text-slate-900 pt-1">
                  {reviewingCvItem.job_title} · {reviewingCvItem.company_name}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setReviewingCvItem(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto pr-1 flex-1">
              {/* Overflow Check Strip */}
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                <div>
                  <span className="font-extrabold text-slate-700">Estimated Page Count:</span>{" "}
                  <strong className="text-slate-900">{reviewingCvItem.tailored_cv.page_count} Pages</strong> (Recommended: 1–2 for senior; Max ceiling: 4)
                </div>
                <span className="px-2.5 py-1 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 font-extrabold text-[11px]">
                  ✓ Overflow: Passed
                </span>
              </div>

              {/* Wording Changes Diff List */}
              <div className="space-y-3">
                <div className="text-xs font-black uppercase text-slate-400 tracking-wider">
                  Wording Changes &amp; Section Tailoring
                </div>
                {reviewingCvItem.tailored_cv.wording_changes.map((wc, idx) => (
                  <div key={idx} className="p-4 rounded-2xl border border-slate-200 space-y-2 bg-white shadow-2xs">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-extrabold text-blue-700">{wc.section}</span>
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 font-mono font-bold text-slate-500 text-[10px]">
                        {wc.change_type}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-500">
                        <strong className="block text-[10px] text-slate-400 uppercase font-black mb-1">Original Wording</strong>
                        <p>{wc.original}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-violet-50/70 border border-violet-200 text-violet-950">
                        <strong className="block text-[10px] text-violet-600 uppercase font-black mb-1">Tailored for Opening</strong>
                        <p className="font-semibold">{wc.tailored}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <span className="text-[11px] text-slate-400 font-mono">
                Version: {reviewingCvItem.tailored_cv.version_id}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setReviewingCvItem(null)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => handleApproveCv(reviewingCvItem.queue_item_id)}
                  className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-extrabold text-xs shadow-xs"
                >
                  Approve CV &amp; Advance
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Phase 3: Final Submission Review Modal ── */}
      {reviewingItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-2xl w-full p-6 sm:p-8 space-y-5 shadow-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-indigo-50 text-indigo-700 text-[10px] font-black uppercase">
                  Checkpoint 2: Final Submission Review
                </div>
                <h3 className="text-base font-extrabold text-slate-900 pt-1">
                  {reviewingItem.job_title} · {reviewingItem.company_name}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setReviewingItem(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto pr-1 flex-1">
              <div className="p-3.5 rounded-2xl bg-indigo-50/60 border border-indigo-200 text-xs text-indigo-900 leading-relaxed font-medium">
                🛡️ <strong>Application Package Ready:</strong> Form fields filled from Answer Bank and CV attached.
                Review before approving for portal submission.
              </div>

              {reviewingItem.answers_snapshot?.fields ? (
                <div className="space-y-3">
                  {Object.values(reviewingItem.answers_snapshot.fields).map((f) => (
                    <div key={f.question_id} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-extrabold text-slate-700">{f.exact_question_text}</span>
                        <span className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[10px] font-mono font-bold text-slate-500">
                          {f.source_scope}
                        </span>
                      </div>
                      <div className="text-xs font-black text-slate-900 pt-0.5">
                        {f.answer_value || "(Blank / Skipped optional field)"}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-slate-400">
                  Standard application package ready with profile answers.
                </div>
              )}
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <span className="text-[11px] text-slate-400 font-mono">
                CV: {reviewingItem.tailored_cv?.version_id || "Profile CV"}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setReviewingItem(null)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => handleApproveSubmission(reviewingItem.queue_item_id)}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs shadow-xs"
                >
                  Approve for Portal Submission
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Phase 2: Answer Bank Management Modal ── */}
      {isAnswerBankOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-2xl w-full p-6 sm:p-8 space-y-5 shadow-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                  Answer Bank (8 Core Categories)
                </h3>
                <p className="text-xs text-slate-500">
                  Reusable answers for notice period, availability, work authorization, sponsorship, relocation, compensation, travel, and experience.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsAnswerBankOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto pr-2 flex-1">
              {editableAnswers.map((item, idx) => (
                <div key={item.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-slate-900">{item.canonical_question}</span>
                    <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600">
                      {item.category}
                    </span>
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-slate-500 block mb-1">Your Default Answer:</label>
                    <input
                      type="text"
                      value={item.answer_text}
                      onChange={(e) => {
                        const updated = [...editableAnswers];
                        updated[idx].answer_text = e.target.value;
                        setEditableAnswers(updated);
                      }}
                      className="w-full px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs font-medium outline-none focus:border-blue-600"
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                    <span>Patterns: {item.matched_patterns?.slice(0, 3).join(", ")}</span>
                    <label className="flex items-center gap-1.5 cursor-pointer text-slate-600 font-bold">
                      <input
                        type="checkbox"
                        checked={item.ask_every_time}
                        onChange={(e) => {
                          const updated = [...editableAnswers];
                          updated[idx].ask_every_time = e.target.checked;
                          setEditableAnswers(updated);
                        }}
                        className="rounded border-slate-300 text-blue-600 w-3.5 h-3.5"
                      />
                      <span>Ask every time</span>
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsAnswerBankOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSavingBank}
                onClick={handleSaveAnswerBank}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs shadow-xs"
              >
                {isSavingBank ? "Saving..." : "Save Answer Bank"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Phase 2: Answering Unfamiliar Question Modal ── */}
      {answeringItem && answeringItem.pending_question && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Answer Application Question</h3>
                <p className="text-xs text-slate-500">
                  {answeringItem.job_title} at {answeringItem.company_name}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAnsweringItem(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-3.5 rounded-2xl bg-rose-50/70 border border-rose-200 space-y-1">
                <span className="text-[10px] font-black text-rose-800 uppercase tracking-wider">Exact Question Text</span>
                <p className="text-xs font-extrabold text-slate-900">
                  "{answeringItem.pending_question.exact_question_text}"
                </p>
              </div>

              {answeringItem.pending_question.options && answeringItem.pending_question.options.length > 0 ? (
                <div className="space-y-1.5">
                  <label className="text-xs font-extrabold text-slate-700 block">Select Compatible Option:</label>
                  <div className="flex flex-wrap gap-2">
                    {answeringItem.pending_question.options.map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => setSelectedOptionInput(opt)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                          selectedOptionInput === opt
                            ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                            : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <label className="text-xs font-extrabold text-slate-700 block">Your Answer:</label>
                  <textarea
                    rows={3}
                    value={answerTextInput}
                    onChange={(e) => setAnswerTextInput(e.target.value)}
                    placeholder="Enter your response..."
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none focus:border-blue-600"
                  />
                </div>
              )}

              {/* 4 Scope Selector */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <label className="text-xs font-extrabold text-slate-700 block">Persistence Scope:</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 p-2 rounded-xl border border-slate-200 cursor-pointer text-xs font-medium hover:bg-slate-50">
                    <input
                      type="radio"
                      name="scope"
                      value="save_as_default"
                      checked={scopeInput === "save_as_default"}
                      onChange={() => setScopeInput("save_as_default")}
                      className="text-blue-600"
                    />
                    <div>
                      <strong className="text-slate-900 block">Save as Default (Recommended)</strong>
                      <span className="text-[11px] text-slate-500">Universal reuse across all future job applications.</span>
                    </div>
                  </label>

                  <label className="flex items-center gap-2 p-2 rounded-xl border border-slate-200 cursor-pointer text-xs font-medium hover:bg-slate-50">
                    <input
                      type="radio"
                      name="scope"
                      value="save_for_rule"
                      checked={scopeInput === "save_for_rule"}
                      onChange={() => setScopeInput("save_for_rule")}
                      className="text-blue-600"
                    />
                    <div>
                      <strong className="text-slate-900 block">Save for this Rule</strong>
                      <span className="text-[11px] text-slate-500">Reused only for '{answeringItem.matched_theme}' roles.</span>
                    </div>
                  </label>

                  <label className="flex items-center gap-2 p-2 rounded-xl border border-slate-200 cursor-pointer text-xs font-medium hover:bg-slate-50">
                    <input
                      type="radio"
                      name="scope"
                      value="use_once"
                      checked={scopeInput === "use_once"}
                      onChange={() => setScopeInput("use_once")}
                      className="text-blue-600"
                    />
                    <div>
                      <strong className="text-slate-900 block">Use Once</strong>
                      <span className="text-[11px] text-slate-500">Applied solely to this specific application.</span>
                    </div>
                  </label>

                  <label className="flex items-center gap-2 p-2 rounded-xl border border-slate-200 cursor-pointer text-xs font-medium hover:bg-slate-50">
                    <input
                      type="radio"
                      name="scope"
                      value="ask_every_time"
                      checked={scopeInput === "ask_every_time"}
                      onChange={() => setScopeInput("ask_every_time")}
                      className="text-blue-600"
                    />
                    <div>
                      <strong className="text-slate-900 block">Ask Every Time</strong>
                      <span className="text-[11px] text-slate-500">Always pause and request confirmation when this question appears.</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setAnsweringItem(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingAnswer}
                onClick={handleSubmitAnswer}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs shadow-xs"
              >
                {isSubmittingAnswer ? "Saving..." : "Save Answer & Resume Job"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Phase 4: Report Manual Submission Modal ── */}
      {reportModalItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Report Manual Application</h3>
                <p className="text-xs text-slate-500">
                  {reportModalItem.job_title} at {reportModalItem.company_name}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setReportModalItem(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 leading-relaxed font-medium">
                Enter your confirmation reference or application notes. Submitting this will record your application as strictly <strong>Applied</strong> in your persistent Job Tracker.
              </div>

              <div>
                <label className="text-xs font-extrabold text-slate-700 block mb-1">Confirmation Reference / Application ID</label>
                <input
                  type="text"
                  value={reportConfirmationRef}
                  onChange={(e) => setReportConfirmationRef(e.target.value)}
                  placeholder="e.g. NK-APP-88412 or GH-CONF-1234"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none focus:border-blue-600 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-extrabold text-slate-700 block mb-1">Notes (Optional)</label>
                <textarea
                  value={reportNotes}
                  onChange={(e) => setReportNotes(e.target.value)}
                  placeholder="e.g. Applied via Naukri quick-apply using profile CV."
                  rows={2}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs outline-none focus:border-blue-600 resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setReportModalItem(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingReport}
                onClick={handleReportApplied}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs shadow-xs"
              >
                {isSubmittingReport ? "Recording..." : "Confirm & Sync to Tracker"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Edit Setup Defaults Modal ── */}
      {isEditingSetup && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full p-6 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-extrabold text-slate-900">Edit Auto Apply Settings</h3>
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

              {/* Phase 3 Approval Checkboxes */}
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <label className="text-xs font-extrabold text-slate-900 block">Default Review Policy:</label>
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={reviewTailoredCv}
                    onChange={(e) => setReviewTailoredCv(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 w-4 h-4"
                  />
                  <span>Review tailored CV before attachment</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={reviewBeforeSubmission}
                    onChange={(e) => setReviewBeforeSubmission(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 w-4 h-4"
                  />
                  <span>Review final package before portal submission</span>
                </label>
              </div>

              {/* Phase 4 Automation & Limits */}
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                <label className="text-xs font-extrabold text-slate-900 block">Portal Automation &amp; Limits:</label>
                
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={allowWorkdayAccountCreation}
                    onChange={(e) => setAllowWorkdayAccountCreation(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 w-4 h-4"
                  />
                  <span>Allow automated Workday account creation if not existing</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={allowUnattendedSubmission}
                    onChange={(e) => setAllowUnattendedSubmission(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 w-4 h-4"
                  />
                  <span>Allow unattended automated submission under daily limit</span>
                </label>

                {allowUnattendedSubmission && (
                  <div className="pl-6 pt-1">
                    <label className="text-[11px] font-bold text-slate-600 block mb-1">Daily Automated Submission Limit:</label>
                    <input
                      type="number"
                      min={1}
                      max={50}
                      value={dailySubmissionLimit}
                      onChange={(e) => setDailySubmissionLimit(Number(e.target.value))}
                      className="w-24 px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-mono outline-none focus:border-blue-600"
                    />
                  </div>
                )}
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
                {isSavingSetup ? "Saving..." : "Save Settings"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
