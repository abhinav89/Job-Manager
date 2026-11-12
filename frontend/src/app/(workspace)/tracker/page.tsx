"use client";
import { RESUME_TEMPLATES, type ResumeTemplate } from "@/lib/resumeTemplates";
import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import dynamic from "next/dynamic";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { API_URL, getApiError } from "@/lib/api";
import { queryKeys, useWorkspace, useTrackerDetails, useTrackerJobs, type JobDetails, type JobSummary, type ApplicationStatus } from "@/lib/queries";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { patchJob, prependJob, removeJob, replaceJob } from "@/lib/trackerCache";
import { setExpandedJob, setFilterStatus, setSearchQuery, setStatsOpen, type RootState } from "@/lib/store";
import { useDispatch, useSelector } from "react-redux";
import InlineQueryError from "@/components/InlineQueryError";
import ApplicationDocuments from "@/components/ApplicationDocuments";
import { KanbanBoard } from "@/components/tracker/KanbanBoard";
import { FileSpreadsheet, Download, LayoutGrid, List, Plus, Search, Lock, LogIn, Kanban } from "lucide-react";
import { useAuth } from "@/lib/authContext";

const Document = dynamic(() => import("react-pdf").then(m => m.Document), { ssr: false });
const Page = dynamic(() => import("react-pdf").then(m => m.Page), { ssr: false });

// Configure PDF.js worker - must be done on client only
if (typeof window !== "undefined") {
  import("react-pdf").then(({ pdfjs }) => {
    pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
  });
}

const API = API_URL;

// ── Types ────────────────────────────────────────────────────────
type Status = ApplicationStatus;
type Priority = "High" | "Medium" | "Low";
type TemplateId = ResumeTemplate;

type Job = JobDetails;

type JobForm = {
  company_name: string; job_title: string; job_url: string;
  short_description: string; job_description: string; status: Status;
  date_applied: string; follow_up_date: string; job_type: string;
  location: string; salary_range: string; priority: Priority; notes: string;
  template_id: TemplateId;
};

type JobPayload = {
  company_name: string;
  job_title: string;
  job_url: string | null;
  short_description: string;
  job_description: string | null;
  status: Status;
  date_applied: string | null;
  follow_up_date: string | null;
  job_type: string | null;
  location: string;
  salary_range: string;
  priority: Priority;
  notes: string;
  template_id: TemplateId;
};

// ── Constants ────────────────────────────────────────────────────
const STATUSES: Status[] = ["To Review", "To Apply", "Applied", "Interview", "Offer", "Rejected", "Saved", "Tech Test", "Ghosted"];

const SC: Record<Status, { bg: string; text: string; border: string; dot: string }> = {
  "To Review":  { bg: "#f8fafc", text: "#334155", border: "#e2e8f0", dot: "#94a3b8" },
  "To Apply":   { bg: "#eff6ff", text: "#1d4ed8", border: "#bfdbfe", dot: "#3b82f6" },
  Saved:       { bg: "#f8fafc", text: "#475569", border: "#cbd5e1", dot: "#64748b" },
  Applied:     { bg: "#eef2ff", text: "#4338ca", border: "#c7d2fe", dot: "#6366f1" },
  Interview:   { bg: "#fef3c7", text: "#b45309", border: "#fde68a", dot: "#f59e0b" },
  "Tech Test": { bg: "#f5f3ff", text: "#6d28d9", border: "#ddd6fe", dot: "#8b5cf6" },
  Offer:       { bg: "#ecfdf5", text: "#047857", border: "#a7f3d0", dot: "#10b981" },
  Rejected:    { bg: "#fff1f2", text: "#be123c", border: "#fecdd3", dot: "#f43f5e" },
  Ghosted:     { bg: "#f8fafc", text: "#64748b", border: "#e2e8f0", dot: "#94a3b8" },
};

const PC: Record<Priority, { text: string; bg: string }> = {
  High:   { text: "#b83030", bg: "#ffeaea" },
  Medium: { text: "#7a5a00", bg: "#fff8e0" },
  Low:    { text: "#4a4540", bg: "#f0ede8" },
};

const EMPTY: JobForm = {
  company_name: "", job_title: "", job_url: "", short_description: "",
  job_description: "", status: "Saved", date_applied: "", follow_up_date: "",
  job_type: "", location: "", salary_range: "", priority: "Medium", notes: "",
  template_id: "classic",
};

// ── UI helpers ───────────────────────────────────────────────────
function StatusBadge({ status }: { status: Status }) {
  const c = SC[status];
    return (
    <span className="tracker-job-badge inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[10px] font-bold tracking-[0.08em] uppercase whitespace-nowrap"
      style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}>
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: c.dot }} />{status}
    </span>
  );
}

function PriorityBadge({ priority }: { priority: Priority }) {
  const c = PC[priority];
  const arrow = priority === "High" ? "↑" : priority === "Low" ? "↓" : "–";
  return (
    <span className="tracker-job-badge inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-sm text-[9px] font-bold tracking-[0.08em] uppercase"
      style={{ background: c.bg, color: c.text }}>
      {arrow} {priority}
    </span>
  );
}

function InputField({ label, value, onChange, type = "text", placeholder = "", required = false }: {
  label: string; value: string; onChange: (v: string) => void;
  type?: string; placeholder?: string; required?: boolean;
}) {
  return (
    <div>
      <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
        {label}{required && <span className="text-rose-500"> *</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 outline-none transition-colors focus:border-blue-600 focus:bg-white font-sans"
      />
    </div>
  );
}

function SelectField({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void; options: string[];
}) {
  return (
    <div>
      <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">{label}</label>
      <select
        aria-label={label}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 outline-none transition-colors focus:border-blue-600 focus:bg-white font-sans"
      >
        {options.map(o => <option key={o} value={o}>{o || "— Select —"}</option>)}
      </select>
    </div>
  );
}

function IconBtn({ onClick, title, children, danger = false, green = false }: {
  onClick: () => void; title: string; children: React.ReactNode; danger?: boolean; green?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`w-8 h-8 flex items-center justify-center rounded-xl transition-all shrink-0 cursor-pointer ${
        danger
          ? "text-slate-400 hover:text-rose-600 hover:bg-rose-50"
          : green
          ? "text-slate-400 hover:text-emerald-600 hover:bg-emerald-50"
          : "text-slate-400 hover:text-slate-800 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}

// ── PDF Preview Modal ────────────────────────────────────────────
function PdfModal({ jobId, companyName, onClose }: { jobId: number; companyName: string; onClose: () => void }) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [page, setPage] = useState(1);
  const pdfUrlRef = useRef<string | null>(null);
  const onLoad = useCallback(({ numPages }: { numPages: number }) => setNumPages(numPages), []);

  useEffect(() => {
    fetch(`${API}/tracker/${jobId}/pdf`, { credentials: "include" })
      .then(res => res.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        pdfUrlRef.current = url;
        setPdfUrl(url);
      });

    return () => {
      if (pdfUrlRef.current) {
        URL.revokeObjectURL(pdfUrlRef.current);
        pdfUrlRef.current = null;
      }
    };
  }, [jobId]);
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 font-sans bg-slate-900/60 backdrop-blur-xs"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="flex w-[calc(100vw-2rem)] max-w-[680px] flex-col rounded-3xl bg-white shadow-2xl border border-slate-200 overflow-hidden" style={{ maxHeight: "90vh" }}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 shrink-0 bg-slate-50 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
            <span className="text-xs font-bold text-slate-900">
              {companyName} — Tailored Resume
            </span>
          </div>
          <div className="flex items-center gap-3">
            {numPages > 1 && (
              <div className="flex items-center gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
                  className="text-xs font-bold text-slate-500 hover:text-slate-800 disabled:opacity-20 cursor-pointer">←</button>
                <span className="text-xs text-slate-400 font-medium">{page}/{numPages}</span>
                <button onClick={() => setPage(p => Math.min(numPages, p + 1))} disabled={page >= numPages}
                  className="text-xs font-bold text-slate-500 hover:text-slate-800 disabled:opacity-20 cursor-pointer">→</button>
              </div>
            )}
            <a href={`${API}/tracker/${jobId}/pdf`} target="_blank" rel="noopener noreferrer"
              className="text-xs px-3 py-1.5 rounded-xl font-bold bg-slate-900 hover:bg-blue-600 text-white transition-colors">
              ↓ Download
            </a>
            <button onClick={onClose} className="p-1 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer">✕</button>
          </div>
        </div>

        {/* PDF */}
        <div className="flex-1 overflow-auto flex items-start justify-center py-6 px-4 bg-slate-100/70">
          {!pdfUrl ? (
            <div className="flex items-center justify-center h-40 gap-2">
              {[0,150,300].map(d => <span key={d} className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: `${d}ms` }} />)}
            </div>
          ) : (
            <div className="shadow-lg">
              <Document file={pdfUrl} onLoadSuccess={onLoad}
                loading={<div className="flex items-center justify-center h-40 text-xs text-slate-400 font-bold">Loading PDF...</div>}>
                <Page pageNumber={page} renderTextLayer={true} renderAnnotationLayer={true} width={Math.min(620, window.innerWidth - 56)} />
              </Document>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Cover Letter Modal ───────────────────────────────────────────
function CoverLetterModal({ job, onClose, onSave }: { job: Job; onClose: () => void; onSave: (id: number, text: string) => void }) {
  const [text, setText] = useState(job.cover_letter || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave(job.id, text);
    setSaving(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 font-sans bg-slate-900/60 backdrop-blur-xs"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="flex w-[calc(100vw-2rem)] max-w-[680px] flex-col rounded-3xl bg-white shadow-2xl border border-slate-200 overflow-hidden" style={{ maxHeight: "90vh" }}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 shrink-0 bg-slate-50 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
            <span className="text-xs font-bold text-slate-900">
              {job.company_name} — Cover Letter
            </span>
          </div>
          <button onClick={onClose} className="p-1 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer">✕</button>
        </div>

        {/* Text Area */}
        <div className="flex-1 overflow-auto flex flex-col p-6">
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            className="w-full flex-1 p-4 text-xs rounded-2xl border border-slate-200 bg-slate-50 text-slate-800 outline-none resize-none font-sans leading-relaxed focus:border-blue-600 focus:bg-white"
            style={{ minHeight: "380px" }}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 shrink-0 bg-slate-50 border-t border-slate-100">
          <button onClick={onClose} className="px-4 py-2.5 text-xs font-bold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 cursor-pointer">
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="px-5 py-2.5 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs cursor-pointer disabled:opacity-50">
            {saving ? "Saving..." : "Save Cover Letter"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────
export default function TrackerPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated, setIsAuthModalOpen } = useAuth();
  const dispatch = useDispatch();
  const trackerUi = useSelector((state: RootState) => state.trackerUi);
  const workspaceQuery = useWorkspace();
  const userError = workspaceQuery.isError;
  const jobsQuery = useTrackerJobs(!userError);
  const expandedJob = trackerUi.expandedJob;
  const detailsQuery = useTrackerDetails(expandedJob);
  const jobs = useMemo(() => (jobsQuery.data || []) as Job[], [jobsQuery.data]);
  const [showModal, setShowModal] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [form, setForm] = useState<JobForm>(EMPTY);
  const [generatingFor, setGeneratingFor] = useState<number | null>(null);
  const [generatingClFor, setGeneratingClFor] = useState<number | null>(null);
  const [viewingPdfFor, setViewingPdfFor] = useState<Job | null>(null);
  const [viewingClFor, setViewingClFor] = useState<Job | null>(null);
  const [generateError, setGenerateError] = useState<{ id: number; msg: string } | null>(null);
  const [autoFilling, setAutoFilling] = useState(false);
  const [jobDescriptionOpen, setJobDescriptionOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"kanban" | "list">("kanban");

  const handleExport = (format: "csv" | "xlsx") => {
    window.open(`${API}/tracker/export/${format}`, "_blank");
    toast.success(`Exporting Application Master Sheet (${format.toUpperCase()})...`);
  };

  const loading = jobsQuery.isLoading;
  const stats = useMemo(() => ({
    total: jobs.length,
    by_status: jobs.reduce<Record<string, number>>((counts, job) => {
      counts[job.status] = (counts[job.status] || 0) + 1;
      return counts;
    }, {}),
  }), [jobs]);
  const filterStatus = trackerUi.filterStatus as Status | "All";
  const searchQuery = trackerUi.searchQuery;

  useEffect(() => {
    if (userError) console.error("Local workspace is unavailable");
  }, [userError, router]);

  const handleAutoFill = async () => {
    if (!form.job_url.trim()) return;
    setAutoFilling(true);
    try {
      const res = await fetch(`${API}/tracker/fetch-job-details`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ url: form.job_url })
      });
      if (res.ok) {
        const json = await res.json();
        if (json.data) {
          setForm(f => ({
            ...f,
            company_name: json.data.company_name || f.company_name,
            job_title: json.data.job_title || f.job_title,
            job_description: json.data.job_description || f.job_description
          }));
        }
      } else {
        toast.error("Failed to auto-fill job details.");
      }
    } catch {
      toast.error("Error auto-filling job details.");
    } finally {
      setAutoFilling(false);
    }
  };

  type SaveVariables = { id: number | null; body: JobPayload; optimistic: JobSummary };
  type MutationSnapshot = { previousJobs?: JobSummary[]; previousDetails?: JobDetails };

  const saveMutation = useMutation<JobDetails, Error, SaveVariables, MutationSnapshot & { optimisticId: number }>({
    mutationFn: async ({ id, body }) => {
      const response = await fetch(id === null ? `${API}/tracker` : `${API}/tracker/${id}`, {
        method: id === null ? "POST" : "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ ...body, revision: editingJob?.revision }),
      });
      if (!response.ok) throw new Error(await getApiError(response, "Unable to save this application."));
      return response.json();
    },
    onMutate: async ({ id, body, optimistic }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.trackerJobs });
      const previousJobs = queryClient.getQueryData<JobSummary[]>(queryKeys.trackerJobs);
      const previousDetails = id === null ? undefined : queryClient.getQueryData<JobDetails>(queryKeys.trackerDetails(id));
      const optimisticId = id ?? optimistic.id;
      queryClient.setQueryData<JobSummary[]>(
        queryKeys.trackerJobs,
        current => id === null ? prependJob(current, optimistic) : patchJob(current, id, optimistic),
      );
      if (id !== null && previousDetails) {
        queryClient.setQueryData(queryKeys.trackerDetails(id), {
          ...previousDetails,
          ...optimistic,
          job_description: body.job_description || undefined,
          notes: body.notes || undefined,
        });
      }
      setShowModal(false);
      return { previousJobs, previousDetails, optimisticId };
    },
    onError: (error, variables, context) => {
      queryClient.setQueryData(queryKeys.trackerJobs, context?.previousJobs);
      if (variables.id !== null && context?.previousDetails) {
        queryClient.setQueryData(queryKeys.trackerDetails(variables.id), context.previousDetails);
      }
      setShowModal(true);
      toast.error(error.message);
    },
    onSuccess: (saved, variables, context) => {
      queryClient.setQueryData<JobSummary[]>(queryKeys.trackerJobs, current =>
        replaceJob(current, context.optimisticId, saved),
      );
      queryClient.setQueryData(queryKeys.trackerDetails(saved.id), saved);
      setEditingJob(null);
      toast.success(variables.id === null ? "Application added." : "Application updated.");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.trackerJobs });
      void queryClient.invalidateQueries({ queryKey: queryKeys.trackerStats });
    },
  });

  const deleteMutation = useMutation<{ status: string }, Error, { id: number; revision?: number }, MutationSnapshot & { wasExpanded: boolean }>({
    mutationFn: async ({id, revision}) => {
      const response = await fetch(`${API}/tracker/${id}?revision=${revision}`, { method: "DELETE", credentials: "include" });
      if (!response.ok) throw new Error(await getApiError(response, "Unable to delete this application."));
      return response.json();
    },
    onMutate: async ({id}) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.trackerJobs });
      const previousJobs = queryClient.getQueryData<JobSummary[]>(queryKeys.trackerJobs);
      const previousDetails = queryClient.getQueryData<JobDetails>(queryKeys.trackerDetails(id));
      queryClient.setQueryData<JobSummary[]>(queryKeys.trackerJobs, current => removeJob(current, id));
      queryClient.removeQueries({ queryKey: queryKeys.trackerDetails(id), exact: true });
      const wasExpanded = expandedJob === id;
      if (wasExpanded) dispatch(setExpandedJob(null));
      return { previousJobs, previousDetails, wasExpanded };
    },
    onError: (error, {id}, context) => {
      queryClient.setQueryData(queryKeys.trackerJobs, context?.previousJobs);
      if (context?.previousDetails) queryClient.setQueryData(queryKeys.trackerDetails(id), context.previousDetails);
      if (context?.wasExpanded) dispatch(setExpandedJob(id));
      toast.error(error.message);
    },
    onSuccess: (_, {id}) => {
      queryClient.removeQueries({ queryKey: queryKeys.trackerDetails(id), exact: true });
      toast.success("Application deleted.");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.trackerJobs });
      void queryClient.invalidateQueries({ queryKey: queryKeys.trackerStats });
    },
  });

  const statusMutation = useMutation<JobDetails, Error, { job: Job; status: Status }, MutationSnapshot>({
    mutationFn: async ({ job, status }) => {
      const response = await fetch(`${API}/tracker/${job.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status, revision: job.revision }),
      });
      if (!response.ok) throw new Error(await getApiError(response, "Unable to update application status."));
      return response.json();
    },
    onMutate: async ({ job, status }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.trackerJobs });
      const previousJobs = queryClient.getQueryData<JobSummary[]>(queryKeys.trackerJobs);
      const previousDetails = queryClient.getQueryData<JobDetails>(queryKeys.trackerDetails(job.id));
      queryClient.setQueryData<JobSummary[]>(queryKeys.trackerJobs, current => patchJob(current, job.id, { status }));
      if (previousDetails) queryClient.setQueryData(queryKeys.trackerDetails(job.id), { ...previousDetails, status });
      return { previousJobs, previousDetails };
    },
    onError: (error, { job }, context) => {
      queryClient.setQueryData(queryKeys.trackerJobs, context?.previousJobs);
      if (context?.previousDetails) queryClient.setQueryData(queryKeys.trackerDetails(job.id), context.previousDetails);
      toast.error(error.message);
    },
    onSuccess: saved => {
      queryClient.setQueryData<JobSummary[]>(queryKeys.trackerJobs, current => replaceJob(current, saved.id, saved));
      queryClient.setQueryData(queryKeys.trackerDetails(saved.id), saved);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.trackerJobs });
      void queryClient.invalidateQueries({ queryKey: queryKeys.trackerStats });
    },
  });

  const openCreate = () => { setEditingJob(null); setForm({ ...EMPTY, template_id: workspaceQuery.data?.preferences?.resume_template || "classic" }); setJobDescriptionOpen(false); setShowModal(true); };
  const openEdit = (job: Job) => {
    const editableJob = detailsQuery.data?.id === job.id ? { ...job, ...detailsQuery.data } : job;
    setEditingJob(editableJob);
    setForm({
      company_name: editableJob.company_name, job_title: editableJob.job_title,
      job_url: editableJob.job_url || "", short_description: editableJob.short_description || "",
      job_description: editableJob.job_description || "", status: editableJob.status,
      date_applied: editableJob.date_applied || "", follow_up_date: editableJob.follow_up_date || "",
      job_type: editableJob.job_type || "", location: editableJob.location || "",
      salary_range: editableJob.salary_range || "", priority: editableJob.priority, notes: editableJob.notes || "",
      template_id: editableJob.template_id || "classic",
    });
    setJobDescriptionOpen(true);
    setShowModal(true);
  };

  const handleSave = () => {
    if (!form.company_name.trim() || !form.job_title.trim()) return;
    const body: JobPayload = {
      ...form,
      date_applied: form.date_applied || null,
      follow_up_date: form.follow_up_date || null,
      job_url: form.job_url || null,
      job_type: form.job_type || null,
      job_description: form.job_description || null,
    };
    const optimistic: JobSummary = {
      id: editingJob?.id ?? -Date.now(),
      company_name: form.company_name,
      job_title: form.job_title,
      job_url: form.job_url || undefined,
      short_description: form.short_description || undefined,
      has_pdf: editingJob?.has_pdf ?? false,
      pdf_generated_at: editingJob?.pdf_generated_at,
      status: form.status,
      date_applied: form.date_applied || undefined,
      follow_up_date: form.follow_up_date || undefined,
      job_type: form.job_type || undefined,
      location: form.location || undefined,
      salary_range: form.salary_range || undefined,
      priority: form.priority,
      template_id: form.template_id,
    };
    saveMutation.mutate({ id: editingJob?.id ?? null, body, optimistic });
  };

  const handleDelete = (id: number) => {
    if (!confirm("Delete this job application?")) return;
    deleteMutation.mutate({ id: id, revision: jobs.find(item => item.id === id)?.revision });
  };

  const handleStatusChange = (job: Job, newStatus: Status) => {
    statusMutation.mutate({ job, status: newStatus });
  };

  const handleGeneratePdf = async (job: Job) => {
    if (!job.job_description?.trim()) {
      setGenerateError({ id: job.id, msg: "Add a job description first" });
      setTimeout(() => setGenerateError(null), 3000);
      return;
    }
    setGeneratingFor(job.id);
    setGenerateError(null);
    try {
      const res = await fetch(`${API}/tracker/${job.id}/generate-pdf`, {
        method: "POST", credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json();
        setGenerateError({ id: job.id, msg: err.detail || "Generation failed" });
        setTimeout(() => setGenerateError(null), 4000);
      } else {
        const pdfGeneratedAt = new Date().toISOString();
        queryClient.setQueryData<JobSummary[]>(queryKeys.trackerJobs, current => patchJob(current, job.id, { has_pdf: true, pdf_generated_at: pdfGeneratedAt }));
        const details = queryClient.getQueryData<JobDetails>(queryKeys.trackerDetails(job.id));
        if (details) queryClient.setQueryData(queryKeys.trackerDetails(job.id), { ...details, has_pdf: true, pdf_generated_at: pdfGeneratedAt });
        void queryClient.invalidateQueries({ queryKey: queryKeys.trackerJobs });
        router.push(`/generate?job_id=${job.id}`);
      }
    } catch {
      setGenerateError({ id: job.id, msg: "Connection error" });
      setTimeout(() => setGenerateError(null), 3000);
    } finally { setGeneratingFor(null); }
  };

  const handleGenerateCoverLetter = async (job: Job) => {
    if (!job.job_description?.trim()) {
      setGenerateError({ id: job.id, msg: "Add a job description first" });
      setTimeout(() => setGenerateError(null), 3000);
      return;
    }
    setGeneratingClFor(job.id);
    setGenerateError(null);
    try {
      const res = await fetch(`${API}/tracker/${job.id}/generate-cover-letter`, {
        method: "POST", credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json();
        setGenerateError({ id: job.id, msg: err.detail || "Generation failed" });
        setTimeout(() => setGenerateError(null), 4000);
      } else {
        const data = await res.json();
        const updatedJob = { ...job, cover_letter: data.cover_letter };
        queryClient.setQueryData(queryKeys.trackerDetails(job.id), updatedJob);
        setViewingClFor(updatedJob);
      }
    } catch {
      setGenerateError({ id: job.id, msg: "Connection error" });
      setTimeout(() => setGenerateError(null), 3000);
    } finally { setGeneratingClFor(null); }
  };

  const handleSaveCoverLetter = async (id: number, text: string) => {
    try {
      const res = await fetch(`${API}/tracker/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ cover_letter: text, revision: jobs.find(job => job.id === id)?.revision })
      });
      if (res.ok) {
        const data: JobDetails = await res.json();
        queryClient.setQueryData<JobSummary[]>(queryKeys.trackerJobs, current => replaceJob(current, id, data));
        queryClient.setQueryData(queryKeys.trackerDetails(id), data);
        void queryClient.invalidateQueries({ queryKey: queryKeys.trackerJobs });
      }
    } catch {
      console.error("Failed to save cover letter");
    }
  };

  const setField = (k: keyof JobForm, v: string) => setForm(f => ({ ...f, [k]: v }));

  const filtered = jobs.filter(j => {
    const matchStatus = filterStatus === "All" || j.status === filterStatus;
    const q = searchQuery.toLowerCase();
    const matchSearch = !q || j.company_name.toLowerCase().includes(q) || j.job_title.toLowerCase().includes(q) || (j.location || "").toLowerCase().includes(q);
    return matchStatus && matchSearch && Boolean(j.is_archived) === showArchived;
  });

  if (!isAuthenticated) {
    return (
      <div className="p-4 sm:p-8 max-w-4xl mx-auto space-y-6 text-center py-20 font-sans">
        <div className="w-16 h-16 rounded-3xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-xs border border-blue-100">
          <Lock className="w-8 h-8" />
        </div>
        <div className="space-y-2 max-w-md mx-auto">
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Private Application Tracker</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            Your applied roles, interview schedules, notes, and application documents are private to your authenticated account. Please sign in to access your tracker.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsAuthModalOpen(true)}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
        >
          <LogIn className="w-4 h-4" />
          Sign In to Access Tracker
        </button>
      </div>
    );
  }

  return (
    <>
    <div className="h-full overflow-auto font-sans bg-slate-50/50 text-slate-900">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10">

          {/* Header */}
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-[10px] tracking-[0.2em] uppercase font-bold text-blue-600 mb-1">
                APPLICATION PIPELINE
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight font-sans">
                Job Tracker
              </h1>
              <p className="text-xs text-slate-500 mt-0.5 font-sans">
                {stats.total} application{stats.total !== 1 ? "s" : ""} · {jobs.filter(j => j.has_pdf).length} tailored resume versions saved
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              {/* View Switcher */}
              <div className="flex items-center rounded-xl border border-slate-200 bg-white p-1 shadow-2xs">
                <button
                  type="button"
                  onClick={() => setViewMode("kanban")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "kanban" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  Kanban
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("list")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "list" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <List className="w-3.5 h-3.5" />
                  List
                </button>
              </div>

              {/* Export Master Sheet */}
              <button
                type="button"
                onClick={() => handleExport("xlsx")}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-all shadow-2xs"
                title="Download complete pipeline formatted for Excel"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                Excel
              </button>

              <button
                type="button"
                onClick={() => handleExport("csv")}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-all shadow-2xs"
                title="Download CSV"
              >
                <Download className="w-3.5 h-3.5 text-slate-500" />
                CSV
              </button>

              <button
                type="button"
                onClick={() => setShowArchived(value => !value)}
                className="rounded-xl border border-slate-200 bg-white hover:bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700"
              >
                {showArchived ? "Active" : "Archived"}
              </button>

              <button
                onClick={openCreate}
                disabled={workspaceQuery.isPending || workspaceQuery.isError}
                className="flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all shadow-sm"
              >
                <Plus className="w-4 h-4" />
                Add Application
              </button>
            </div>
          </div>

          {/* Stats Overview */}
          <section className="mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xs">
            <button
              type="button"
              onClick={() => dispatch(setStatsOpen(!trackerUi.statsOpen))}
              className="flex w-full items-center justify-between gap-4 px-5 py-3.5 text-left hover:bg-slate-50/50 transition-colors cursor-pointer"
              aria-expanded={trackerUi.statsOpen}
            >
              <div>
                <span className="block text-[10px] uppercase tracking-wider font-extrabold text-blue-600">Application Pipeline Overview</span>
                <span className="mt-0.5 block text-xs font-semibold text-slate-500">
                  {stats.total} total application{stats.total !== 1 ? "s" : ""} · {filterStatus === "All" ? "All statuses" : `${filterStatus} selected`}
                </span>
              </div>
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-700 font-bold text-xs">
                {trackerUi.statsOpen ? "−" : "+"}
              </span>
            </button>
            {trackerUi.statsOpen && (
              <div className="grid grid-cols-2 gap-2 border-t border-slate-100 p-4 sm:grid-cols-4 lg:grid-cols-9 bg-slate-50/30">
                {STATUSES.map(s => {
                  const c = SC[s];
                  const count = stats.by_status[s] || 0;
                  const active = filterStatus === s;
                  return (
                    <button
                      key={s}
                      onClick={() => dispatch(setFilterStatus(active ? "All" : s))}
                      className={`rounded-xl p-3 text-center transition-all cursor-pointer ${
                        active
                          ? "ring-2 ring-blue-600 shadow-2xs"
                          : "hover:bg-slate-100/80"
                      }`}
                      style={{ background: c.bg, border: `1px solid ${c.border}` }}
                    >
                      <div className="text-lg font-black text-slate-900">{count}</div>
                      <div className="mt-0.5 text-[10px] uppercase font-bold tracking-tight text-slate-600 truncate">{s}</div>
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          {/* Search & Filter Bar */}
          <div className="mb-6 flex flex-wrap items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                value={searchQuery}
                onChange={e => dispatch(setSearchQuery(e.target.value))}
                placeholder="Search company, job title, location..."
                className="w-full pl-10 pr-4 py-2.5 text-xs outline-none rounded-xl bg-white border border-slate-200 focus:border-blue-600 text-slate-800 transition-colors shadow-2xs font-sans"
              />
            </div>
            {filterStatus !== "All" && (
              <button
                onClick={() => dispatch(setFilterStatus("All"))}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 cursor-pointer"
              >
                ✕ Clear {filterStatus}
              </button>
            )}
            <span className="text-xs font-semibold ml-auto text-slate-400">{filtered.length} application{filtered.length !== 1 ? "s" : ""}</span>
          </div>

          {/* Applications Content */}
          {loading ? (
            <div className="flex items-center justify-center py-20 gap-2">
              {[0, 150, 300].map(d => (
                <span
                  key={d}
                  className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-bounce"
                  style={{ animationDelay: `${d}ms` }}
                />
              ))}
            </div>
          ) : jobsQuery.isError && jobs.length === 0 ? (
            <InlineQueryError
              message={jobsQuery.error instanceof Error ? jobsQuery.error.message : "We couldn’t load your applications."}
              onRetry={() => { void jobsQuery.refetch(); }}
            />
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 gap-3 bg-white border border-slate-200 rounded-3xl text-center shadow-xs">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Kanban className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-bold text-slate-900">
                  {searchQuery || filterStatus !== "All" ? "No applications match your filter" : "No applications tracked yet"}
                </h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  Save roles directly from &quot;Find Jobs&quot; or manually log an application to track your interview progress.
                </p>
              </div>
              {!searchQuery && filterStatus === "All" && (
                <button
                  onClick={openCreate}
                  disabled={workspaceQuery.isPending || workspaceQuery.isError}
                  className="mt-2 text-xs font-bold px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs cursor-pointer inline-flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add your first application
                </button>
              )}
            </div>
          ) : viewMode === "kanban" ? (
            <KanbanBoard
              jobs={filtered}
              onStatusChange={(j, st) => handleStatusChange(j, st as Status)}
              onOpenDetails={(id) => dispatch(setExpandedJob(id))}
              onTailor={(job) => {
                if (job.has_pdf) {
                  router.push(`/generate?job_id=${job.id}`);
                } else {
                  handleGeneratePdf(job);
                }
              }}
              onDelete={handleDelete}
            />
          ) : (
            <div className="space-y-2">
              {filtered.map(job => {
                const expanded = expandedJob === job.id;
                const detailJob: Job = detailsQuery.data?.id === job.id ? { ...job, ...detailsQuery.data } : job;
                const isGenerating = generatingFor === job.id;
                const err = generateError?.id === job.id ? generateError.msg : null;
                return (
                  <div key={job.id} className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs hover:border-slate-300 transition-all font-sans">

                    {/* Main row */}
                    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: SC[job.status].dot }} />

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-bold text-slate-900">{job.company_name}</span>
                          <span className="text-xs text-slate-300">·</span>
                          <span className="text-sm font-medium text-slate-600">{job.job_title}</span>
                        </div>
                        {expanded && <div className="flex items-center gap-3 mt-1.5 flex-wrap text-xs text-slate-500">
                          {job.location && <span className="inline-flex items-center gap-1">📍 {job.location}</span>}
                          {job.job_source && <span>via {job.job_source}</span>}
                          {job.job_type && <span>{job.job_type}</span>}
                          {job.salary_range && <span>💰 {job.salary_range}</span>}
                          {job.date_applied && <span>Applied {job.date_applied}</span>}
                          {job.has_pdf && job.pdf_generated_at && (
                            <span className="text-emerald-700 font-semibold">
                              ✓ CV generated {new Date(job.pdf_generated_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>}
                      </div>

                      {/* Right controls */}
                      {expanded && <div className="tracker-job-actions flex w-full flex-wrap items-center justify-start gap-2 sm:order-last sm:basis-full">
                        <button type="button" onClick={async () => {
                          try {
                            const response = await fetch(`${API}/tracker/${job.id}`, { method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_archived: !job.is_archived }) });
                            if (!response.ok) throw new Error(await getApiError(response, "Unable to update archive."));
                            void queryClient.invalidateQueries({ queryKey: queryKeys.tracker });
                          } catch (err) { toast.error(err instanceof Error ? err.message : "Unable to update archive."); }
                        }} className="rounded-xl border border-slate-200 bg-white hover:bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 cursor-pointer">{job.is_archived ? "Restore" : "Archive"}</button>
                        <button type="button" onClick={async () => {
                          try {
                            const response = await fetch(`${API}/assistant/conversations`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_id: job.id }) });
                            if (!response.ok) throw new Error(await getApiError(response, "Unable to open the assistant."));
                            const conversation = await response.json();
                            sessionStorage.setItem("career-assistant-active", String(conversation.id));
                            sessionStorage.setItem("career-assistant-fit-prompt", String(conversation.id));
                            router.push("/assistant");
                          } catch (err) { toast.error(err instanceof Error ? err.message : "Unable to open the assistant."); }
                        }} className="rounded-xl border border-slate-200 bg-white hover:bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 cursor-pointer">Analyze fit</button>
                        <PriorityBadge priority={job.priority} />
                        <StatusBadge status={job.status} />

                        {/* Quick status */}
                        <select value={job.status} onChange={e => handleStatusChange(job, e.target.value as Status)}
                          className="text-xs px-2.5 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 font-medium outline-none cursor-pointer"
                          title="Change status">
                          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>

                        <div className="hidden h-5 w-px shrink-0 sm:block bg-slate-200" />

                        {/* Generate CV / Open Editor */}
                        <button
                          onClick={() => job.has_pdf ? router.push(`/generate?job_id=${job.id}`) : handleGeneratePdf(detailJob)}
                          disabled={isGenerating}
                          title={job.has_pdf ? "Open CV in editor" : job.job_description ? "Generate tailored CV for this job" : "Add job description first"}
                          className="flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition-all shadow-xs disabled:opacity-50 cursor-pointer bg-blue-600 hover:bg-blue-700 text-white">
                          {isGenerating ? (
                            <span className="flex items-center gap-2">
                              Tailoring CV...
                            </span>
                          ) : (
                            <span className="flex items-center gap-2">
                              <span>{job.has_pdf ? "Open Tailored CV" : "Tailor Resume"}</span>
                            </span>
                          )}
                        </button>

                        {/* Generate Cover Letter */}
                        <button
                          onClick={() => handleGenerateCoverLetter(detailJob)}
                          disabled={generatingClFor === job.id}
                          title={job.job_description ? "Generate cover letter for this job" : "Add job description first"}
                          className="flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition-all shadow-xs disabled:opacity-50 cursor-pointer border border-slate-200 bg-white hover:bg-slate-50 text-slate-800">
                          {generatingClFor === job.id ? (
                            <span>Writing letter...</span>
                          ) : (
                            <span>{job.cover_letter ? "Regenerate Cover Letter" : "Generate Cover Letter"}</span>
                          )}
                        </button>

                        {/* View Cover Letter */}
                        {job.cover_letter && (
                          <button
                            onClick={() => setViewingClFor(detailJob)}
                            title="View and Edit Cover Letter"
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 cursor-pointer transition-all">
                            Edit Cover Letter
                          </button>
                        )}

                        <div className="hidden h-5 w-px shrink-0 sm:block" style={{ background: "#d4cfc7" }} />

                        {/* Edit */}
                        <IconBtn onClick={() => openEdit(detailJob)} title="Edit" green>
                          <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                            <path d="M7.5 1.5l2 2L3 10H1V8L7.5 1.5z" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/>
                          </svg>
                        </IconBtn>

                        {/* Delete */}
                        <IconBtn onClick={() => handleDelete(job.id)} title="Delete" danger>
                          <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                            <path d="M1.5 3h8M4 3V2h3v1M3.5 3v6h4V3h-4z" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </IconBtn>
                      </div>}
                      <button type="button" onClick={() => dispatch(setExpandedJob(expanded ? null : job.id))}
                        title={expanded ? "Collapse details" : "Show details"} aria-expanded={expanded} aria-controls={`application-details-${job.id}`}
                        className="col-span-2 inline-flex shrink-0 items-center justify-center gap-2 justify-self-end rounded-sm border border-[#d4cfc7] bg-[#f5f2ed] px-3 py-2 text-[10px] font-semibold text-[#3d6600] hover:border-[#8ab030] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5a8a00]">
                        Documents & details
                        <svg width="11" height="11" viewBox="0 0 11 11" fill="none"
                          style={{ transform: expanded ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}>
                          <path d="M2 4L5.5 7L9 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>

                    {/* Error toast */}
                    {err && (
                      <div className="px-4 pb-2">
                        <div className="px-3 py-2 text-[10px] rounded-sm" style={{ background: "#ffeaea", color: "#b83030", border: "1px solid #f8b8b8" }}>
                          ✗ {err}
                        </div>
                      </div>
                    )}

                    {/* Expanded */}
                    {expanded && (
                      <div id={`application-details-${job.id}`} className="px-4 pb-4 pt-4" style={{ borderTop: "1px solid #d4cfc7" }}>
                        <ApplicationDocuments key={job.id} applicationId={job.id} />
                        {detailsQuery.isPending ? (
                          <div role="status" className="grid grid-cols-1 gap-3 md:grid-cols-2">
                            <span className="h-20 animate-pulse rounded-sm bg-[#ddd8d0]" />
                            <span className="h-20 animate-pulse rounded-sm bg-[#ddd8d0]" />
                            <span className="sr-only">Loading application details…</span>
                          </div>
                        ) : detailsQuery.isError ? (
                          <InlineQueryError
                            message={detailsQuery.error instanceof Error ? detailsQuery.error.message : "We couldn’t load this application."}
                            onRetry={() => { void detailsQuery.refetch(); }}
                          />
                        ) : (
                        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                          <div className="space-y-3">
                            {job.short_description && (
                              <div>
                                <div className="text-[9px] tracking-[0.2em] uppercase mb-1" style={{ color: "#a8a39c" }}>Description</div>
                                <p className="text-xs leading-relaxed" style={{ color: "#4a4540" }}>{job.short_description}</p>
                              </div>
                            )}
                            {detailJob.job_description && (
                              <div>
                                <div className="text-[9px] tracking-[0.2em] uppercase mb-1" style={{ color: "#a8a39c" }}>Job Description</div>
                                <p className="text-xs leading-relaxed line-clamp-4" style={{ color: "#7a7570" }}>{detailJob.job_description}</p>
                              </div>
                            )}
                            {job.job_url && (
                              <div>
                                <div className="text-[9px] tracking-[0.2em] uppercase mb-1" style={{ color: "#a8a39c" }}>Job URL</div>
                                <a href={job.job_url} target="_blank" rel="noopener noreferrer"
                                  className="text-xs underline truncate block" style={{ color: "#3d6600" }}>
                                  {job.job_url}
                                </a>
                              </div>
                            )}
                          </div>
                          <div className="space-y-3">
                            {job.follow_up_date && (
                              <div>
                                <div className="text-[9px] tracking-[0.2em] uppercase mb-1" style={{ color: "#a8a39c" }}>Follow-up Date</div>
                                <p className="text-xs" style={{ color: "#4a4540" }}>📅 {job.follow_up_date}</p>
                              </div>
                            )}
                            {detailJob.notes && (
                              <div>
                                <div className="text-[9px] tracking-[0.2em] uppercase mb-1" style={{ color: "#a8a39c" }}>Notes</div>
                                <p className="text-xs leading-relaxed" style={{ color: "#4a4540" }}>{detailJob.notes}</p>
                              </div>
                            )}
                            {job.has_pdf && (
                              <div>
                                <div className="text-[9px] tracking-[0.2em] uppercase mb-1" style={{ color: "#a8a39c" }}>CV Status</div>
                                <p className="text-xs" style={{ color: "#5a8a00" }}>
                                  ✓ Tailored CV saved · Generated {job.pdf_generated_at ? new Date(job.pdf_generated_at).toLocaleString() : ""}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── Add/Edit Application Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs font-sans"
          onClick={e => { if (e.target === e.currentTarget) setShowModal(false); }}>
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-white shadow-2xl border border-slate-200">

            <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 bg-slate-50 border-b border-slate-100">
              <h2 className="text-sm font-black tracking-tight text-slate-900">
                {editingJob ? "Edit Job Application" : "Track New Job Application"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer">✕</button>
            </div>

            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <InputField label="Company Name" value={form.company_name} onChange={v => setField("company_name", v)} placeholder="Zepto, Rubrik, Snowflake..." required />
                <InputField label="Job Title" value={form.job_title} onChange={v => setField("job_title", v)} placeholder="Engineering Manager, Strategy Lead..." required />
              </div>
              
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <div className="flex-1">
                  <InputField label="Job URL" value={form.job_url} onChange={v => setField("job_url", v)} placeholder="https://..." />
                </div>
                <button 
                  onClick={handleAutoFill} 
                  disabled={autoFilling || !form.job_url.trim()}
                  className="h-[42px] px-4 text-xs font-bold rounded-xl bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
                  {autoFilling ? "Extracting..." : "Auto-Fill from URL"}
                </button>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">Short Summary</label>
                <textarea value={form.short_description} onChange={e => setField("short_description", e.target.value)}
                  placeholder="Brief overview of the role..." rows={2}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 outline-none resize-none font-sans focus:border-blue-600 focus:bg-white" />
              </div>

              {/* Job description */}
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50/50">
                <button
                  type="button"
                  onClick={() => setJobDescriptionOpen(open => !open)}
                  className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left transition-colors hover:bg-slate-100/50 cursor-pointer"
                  aria-expanded={jobDescriptionOpen}
                >
                  <span className="min-w-0">
                    <span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">Job Description</span>
                    <span className="mt-0.5 block truncate text-xs text-slate-500">
                      {form.job_description ? form.job_description.replace(/\s+/g, " ").slice(0, 110) : "Paste full job description for ATS match & tailoring"}
                    </span>
                  </span>
                  <span className="text-xs font-bold text-blue-600 shrink-0">
                    {jobDescriptionOpen ? "Close ▲" : "Expand ▼"}
                  </span>
                </button>
                {jobDescriptionOpen && (
                  <div className="border-t border-slate-200 p-4 bg-white">
                    <textarea value={form.job_description} onChange={e => setField("job_description", e.target.value)}
                      placeholder="Paste the full job description here..." rows={10}
                      className="w-full min-h-[220px] text-xs leading-relaxed p-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 outline-none resize-y font-sans focus:border-blue-600 focus:bg-white" />
                    <div className="mt-1.5 flex justify-between text-[11px] text-slate-400">
                      <span>Full JD text</span>
                      <span>{form.job_description.length} characters</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <SelectField label="Status" value={form.status} onChange={v => setField("status", v)} options={STATUSES} />
                <SelectField label="Priority" value={form.priority} onChange={v => setField("priority", v)} options={["High", "Medium", "Low"]} />
                <SelectField label="Job Type" value={form.job_type} onChange={v => setField("job_type", v)} options={["", "Remote", "Hybrid", "On-site"]} />
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <SelectField label="Resume Template" value={form.template_id} onChange={v => setField("template_id", v as TemplateId)} options={RESUME_TEMPLATES.map(template => template.id)} />
                <div className="flex items-end pb-2 text-xs text-slate-500">
                  Used when generating or tailoring a CV for this role.
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <InputField label="Location" value={form.location} onChange={v => setField("location", v)} placeholder="Bengaluru / Remote / India..." />
                <InputField label="Salary Range" value={form.salary_range} onChange={v => setField("salary_range", v)} placeholder="₹25L–₹40L / yr..." />
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <InputField label="Date Applied" value={form.date_applied} onChange={v => setField("date_applied", v)} type="date" />
                <InputField label="Follow-up Date" value={form.follow_up_date} onChange={v => setField("follow_up_date", v)} type="date" />
              </div>
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">Interview &amp; Pipeline Notes</label>
                <textarea value={form.notes} onChange={e => setField("notes", e.target.value)}
                  placeholder="Referral contact, recruiter notes, discussion points..." rows={3}
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 outline-none resize-none font-sans focus:border-blue-600 focus:bg-white" />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3 px-6 py-4 bg-slate-50 border-t border-slate-100">
              <button onClick={() => setShowModal(false)}
                className="px-4 py-2.5 text-xs font-bold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 cursor-pointer">
                Cancel
              </button>
              <button onClick={handleSave} disabled={saveMutation.isPending || !form.company_name.trim() || !form.job_title.trim()}
                className="px-5 py-2.5 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs cursor-pointer disabled:opacity-50">
                {saveMutation.isPending ? "Saving..." : editingJob ? "Save Changes" : "Add Application"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── PDF Preview Modal ── */}
      {viewingPdfFor && (
        <PdfModal
          jobId={viewingPdfFor.id}
          companyName={viewingPdfFor.company_name}
          onClose={() => setViewingPdfFor(null)}
        />
      )}

      {/* ── Cover Letter Modal ── */}
      {viewingClFor && (
        <CoverLetterModal
          job={viewingClFor}
          onClose={() => setViewingClFor(null)}
          onSave={handleSaveCoverLetter}
        />
      )}
    </>
  );
}
 
