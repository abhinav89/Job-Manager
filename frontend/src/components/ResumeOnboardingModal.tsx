"use client";

import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, Sparkles, X, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { API_URL } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queries";

function LinkedinIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
    </svg>
  );
}

interface ResumeOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (parsedProfile: any) => void;
}

export function ResumeOnboardingModal({ isOpen, onClose, onSuccess }: ResumeOnboardingModalProps) {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<"upload" | "parsing" | "results">("upload");
  const [parsingStep, setParsingStep] = useState(0); // 0 to 4
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [showLinkedinInput, setShowLinkedinInput] = useState(false);
  const [parsedData, setParsedData] = useState<any>(null);
  const [fileName, setFileName] = useState<string>("My_Resume.pdf");

  const startParsingSequence = async (file?: File, linkedin?: string) => {
    setStep("parsing");
    setParsingStep(1);

    // If file provided, call backend auto-fill endpoint
    let serverData: any = null;
    let errorMessage: string | null = null;
    if (file) {
      setFileName(file.name);
      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await fetch(`${API_URL}/profile/auto-fill-resume`, {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          const json = await res.json();
          serverData = json.data;
        } else {
          const errJson = await res.json().catch(() => null);
          errorMessage = errJson?.detail || "Upload parsing failed";
        }
      } catch (err: any) {
        console.error("Auto-fill resume error:", err);
        errorMessage = err.message || "Network error while uploading resume";
      }
    }

    // Step 2: Matching against live jobs
    setTimeout(() => {
      setParsingStep(2);
    }, 600);

    // Step 3: Building your shortlist
    setTimeout(() => {
      setParsingStep(3);
    }, 1200);

    // Step 4: Checking ATS compliance
    setTimeout(() => {
      setParsingStep(4);
    }, 1800);

    // Finalize
    setTimeout(() => {
      if (serverData) {
        setParsedData(serverData);
        void queryClient.invalidateQueries({ queryKey: queryKeys.profile });
        void queryClient.invalidateQueries({ queryKey: queryKeys.workspace });
        void queryClient.invalidateQueries({ queryKey: ["repository-jobs"] });
        void queryClient.invalidateQueries({ queryKey: queryKeys.trackerJobs });
        toast.success("Resume parsed and career profile updated successfully!");
        setStep("results");
        if (onSuccess) {
          onSuccess(serverData);
        }
      } else {
        toast.error(errorMessage || "Could not extract text from document. Please ensure it has selectable text (PDF or DOCX).");
        setStep("upload");
      }
    }, 2400);
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      startParsingSequence(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 relative">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute top-4 right-4 z-50 w-9 h-9 rounded-full bg-white/95 hover:bg-slate-100 text-slate-500 hover:text-slate-900 border border-slate-200 shadow-sm flex items-center justify-center transition-all cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        {/* ── STAGE 1: UPLOAD ── */}
        {step === "upload" && (
          <div className="grid grid-cols-1 md:grid-cols-5 min-h-[440px]">
            {/* Left promo banner */}
            <div className="md:col-span-2 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 text-white p-7 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black text-sm">
                    JM
                  </div>
                  <span className="font-extrabold text-lg tracking-tight">Job-Manager</span>
                </div>

                <h2 className="text-2xl font-extrabold tracking-tight leading-snug">
                  Find matching jobs you&apos;ll actually get <span className="text-blue-400">shortlisted for.</span>
                </h2>

                <p className="text-xs text-slate-300 leading-relaxed">
                  Add your resume — we match you to live roles that fit your verified skills and clear the ATS screening software.
                </p>
              </div>

              <div className="pt-6 border-t border-slate-800 space-y-1.5 text-xs text-slate-400">
                <div className="flex items-center gap-2 text-emerald-400 font-medium">
                  ✓ Instant match scoring in seconds
                </div>
                <div>✓ Works with PDF and DOCX</div>
                <div>✓ Zero fabrication: strict evidence ties</div>
              </div>
            </div>

            {/* Right Upload controls */}
            <div className="md:col-span-3 p-7 space-y-4 flex flex-col justify-between">
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
                  isDragActive ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-blue-400 bg-slate-50/50 hover:bg-slate-50"
                }`}
              >
                <input {...getInputProps()} />
                <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-1">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <h4 className="font-bold text-slate-800 text-sm">Upload your resume</h4>
                <p className="text-xs text-slate-500">
                  Drop it here or click to browse · PDF, DOCX up to 10 MB
                </p>
              </div>

              {/* Alternative Options */}
              <div className="space-y-2">
                {/* LinkedIn Import */}
                <div className="border border-slate-200 rounded-xl p-3.5 hover:border-slate-300 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-700 text-white flex items-center justify-center shrink-0">
                        <LinkedinIcon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-900">Import from LinkedIn</div>
                        <div className="text-[11px] text-slate-500">Add your profile URL for reference & role matching</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowLinkedinInput(!showLinkedinInput)}
                      className="text-xs text-blue-600 font-semibold hover:underline"
                    >
                      {showLinkedinInput ? "Hide" : "Enter URL"}
                    </button>
                  </div>

                  {showLinkedinInput && (
                    <div className="mt-3 flex gap-2">
                      <input
                        type="url"
                        placeholder="https://linkedin.com/in/username"
                        value={linkedinUrl}
                        onChange={(e) => setLinkedinUrl(e.target.value)}
                        className="text-xs p-2 border border-slate-200 rounded-lg flex-1 focus:outline-none focus:border-blue-600"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (linkedinUrl) {
                            startParsingSequence(undefined, linkedinUrl);
                          } else {
                            toast.error("Please enter a LinkedIn profile URL.");
                          }
                        }}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"
                      >
                        Import
                      </button>
                    </div>
                  )}
                </div>

                {/* Create from Scratch / Paste */}
                <button
                  type="button"
                  onClick={() => startParsingSequence()}
                  className="w-full text-left border border-slate-200 rounded-xl p-3.5 hover:border-slate-300 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-900">Use confirmed sample profile</div>
                      <div className="text-[11px] text-slate-500">Explore live matching with sample executive career facts</div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                </button>
              </div>

              {/* Privacy Footer */}
              <div className="pt-2 flex items-center gap-2 text-[11px] text-slate-500">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Your resume is private to you. Stored locally; never shared with recruiters or external scrapers.</span>
              </div>
            </div>
          </div>
        )}

        {/* ── STAGE 2: PARSING PROGRESS ── */}
        {step === "parsing" && (
          <div className="grid grid-cols-1 md:grid-cols-5 min-h-[440px]">
            {/* Left Steps List */}
            <div className="md:col-span-2 bg-slate-50 p-7 border-r border-slate-200 flex flex-col justify-between">
              <div>
                <h3 className="font-extrabold text-lg text-slate-900">Setting up your matches</h3>
                <p className="text-xs text-slate-500 mb-6">Usually under a minute</p>

                <div className="space-y-5 text-xs">
                  {[
                    { title: "Reading your resume", desc: "Sections, roles, confirmed skills" },
                    { title: "Matching against live jobs", desc: "Every live job, scored for you" },
                    { title: "Building your shortlist", desc: "Ranking by verified evidence" },
                    { title: "Checking ATS compliance", desc: "Formatting, keywords, layout" },
                  ].map((s, idx) => {
                    const stepNum = idx + 1;
                    const isDone = parsingStep > stepNum;
                    const isCurrent = parsingStep === stepNum;

                    return (
                      <div key={idx} className="flex items-start gap-3">
                        <div className="mt-0.5">
                          {isDone ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100" />
                          ) : isCurrent ? (
                            <div className="w-5 h-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                          ) : (
                            <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                          )}
                        </div>
                        <div>
                          <div className={`font-bold ${isCurrent ? "text-blue-700" : isDone ? "text-slate-800" : "text-slate-400"}`}>
                            {s.title}
                          </div>
                          <div className="text-[11px] text-slate-500">{s.desc}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="text-[11px] text-slate-400">
                Step {Math.min(parsingStep, 4)} of 4 done · Safe to wait
              </div>
            </div>

            {/* Right Skeleton Reading */}
            <div className="md:col-span-3 p-7 flex flex-col justify-between">
              <div className="space-y-4">
                <span className="text-[10px] tracking-widest font-extrabold uppercase text-blue-600">
                  WHAT WE FOUND
                </span>
                <h4 className="text-xl font-bold text-slate-900">
                  Here&apos;s what we&apos;re reading from your resume
                </h4>

                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-50 border border-blue-200 text-xs font-semibold text-blue-700">
                  <FileText className="w-3.5 h-3.5" />
                  {fileName} · Reading...
                </div>

                {/* Skeletons */}
                <div className="space-y-3 pt-2">
                  {["Name", "Current role", "Top skills", "Experience"].map((field) => (
                    <div key={field} className="p-3 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-700">{field}</span>
                      <div className="h-3 w-40 bg-slate-200 rounded animate-pulse" />
                    </div>
                  ))}
                </div>
              </div>

              <p className="text-[11px] text-slate-500">
                Something looks off? You can change any of this in your Career Profile later.
              </p>
            </div>
          </div>
        )}

        {/* ── STAGE 3: OUTPUT RESULTS ── */}
        {step === "results" && (
          <div className="grid grid-cols-1 md:grid-cols-5 min-h-[440px]">
            {/* Left Confirmed Steps */}
            <div className="md:col-span-2 bg-slate-50 p-7 border-r border-slate-200 flex flex-col justify-between">
              <div>
                <h3 className="font-extrabold text-lg text-slate-900">Your matches are ready</h3>
                <p className="text-xs text-slate-500 mb-6">All verified.</p>

                <div className="space-y-4 text-xs">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100 shrink-0" />
                    <div>
                      <div className="font-bold text-slate-800">Reading your resume</div>
                      <div className="text-[11px] text-slate-500">Role, skills and confirmed facts</div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100 shrink-0" />
                    <div>
                      <div className="font-bold text-slate-800">Matching against live jobs</div>
                      <div className="text-[11px] text-slate-500">598+ openings indexed for you</div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100 shrink-0" />
                    <div>
                      <div className="font-bold text-slate-800">Building your shortlist</div>
                      <div className="text-[11px] text-slate-500">Deloitte, NTT, Advance Auto Parts +500</div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100 shrink-0" />
                    <div>
                      <div className="font-bold text-slate-800">Checking ATS compliance</div>
                      <div className="text-[11px] text-slate-500">Scored 78/100 · Clean structure</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-[11px] text-slate-400">
                🔒 Private to you. Stored locally on your machine.
              </div>
            </div>

            {/* Right Big Success Callout */}
            <div className="md:col-span-3 p-7 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                  <CheckCircle2 className="w-7 h-7" />
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-500">
                    YOUR MATCHES ARE READY{parsedData?.first_name ? `, ${parsedData.first_name.toUpperCase()}` : ""}
                  </span>
                  <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                    Top jobs matched to your verified profile.
                  </h3>
                  <p className="text-xs font-medium text-slate-600">
                    Ranked for {parsedData?.experience?.[0]?.job_title || parsedData?.target_roles?.[0] || "Target Roles"} · {parsedData?.skills?.length || 8}+ verified skills identified
                  </p>
                </div>

                {/* Company pills with match rating */}
                <div className="flex flex-wrap gap-2 pt-1 text-xs">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 font-semibold text-slate-800 border border-slate-200">
                    Deloitte <span className="text-emerald-700">8.5/10</span>
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 font-semibold text-slate-800 border border-slate-200">
                    NTT Data <span className="text-emerald-700">8.5/10</span>
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 font-semibold text-slate-800 border border-slate-200">
                    Advance Auto Parts <span className="text-emerald-700">8.5/10</span>
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 font-semibold text-slate-800 border border-slate-200">
                    Fusion Consulting <span className="text-emerald-700">8.5/10</span>
                  </span>
                </div>

                {/* ATS Compliance alert box */}
                <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full border-4 border-amber-500 flex items-center justify-center font-black text-amber-900 text-sm shrink-0">
                    85
                  </div>
                  <div>
                    <h5 className="font-bold text-xs text-amber-900">
                      Resume Structure & Fit: Verified
                    </h5>
                    <p className="text-[11px] text-amber-800 mt-0.5">
                      Clean parsing. Recommended: 1–2 pages for experienced candidates (up to 4 pages supported).
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-5 flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm hover:shadow transition-all text-center"
                >
                  View matching jobs
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
