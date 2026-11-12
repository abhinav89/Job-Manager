"use client";

import React, { useState, useEffect, useMemo } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  User,
  Briefcase,
  GraduationCap,
  Sparkles,
  Save,
  Plus,
  Trash2,
  UploadCloud,
  CheckCircle2,
  MapPin,
  DollarSign,
  Building,
  RotateCcw,
  Check,
  Layers,
  ArrowRight,
  TrendingUp,
  Tag,
  Calendar,
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { useProfile, usePresets, useThemes, queryKeys, type Profile, type CareerTheme } from "@/lib/queries";
import { ResumeOnboardingModal } from "@/components/ResumeOnboardingModal";

const THEME_SKILL_SUGGESTIONS: Record<string, string[]> = {
  "Strategy & Transformation": [
    "Corporate Strategy", "M&A Advisory", "Management Consulting", "Business Transformation",
    "Chief of Staff", "Market Sizing", "Competitive Analysis", "Executive Stakeholder Management",
    "OKRs", "P&L Management", "Financial Modeling", "Strategic Roadmapping"
  ],
  "Finance & FP&A": [
    "Corporate Finance", "FP&A", "Financial Modeling", "Variance Analysis",
    "Budgeting & Forecasting", "Valuation", "Due Diligence", "Cash Flow Modeling",
    "MS Excel", "SQL", "ERP Systems", "Cost Optimization"
  ],
  "Product Management": [
    "Product Strategy", "Product Roadmapping", "Agile & Scrum", "User Experience (UX)",
    "A/B Testing", "Feature Prioritization", "GTM Strategy", "APIs", "Data Analytics",
    "PRDs", "Wireframing", "Customer Research"
  ],
  "Tech & Engineering": [
    "Python", "TypeScript", "React", "Next.js", "Cloud Architecture", "Docker & Kubernetes",
    "Distributed Systems", "PostgreSQL", "System Design", "Microservices", "REST APIs", "CI/CD"
  ],
  "Enterprise Sales": [
    "Enterprise Sales", "B2B Sales", "SaaS Solution Selling", "Contract Negotiation",
    "Sales Pipeline Management", "Account Executive", "Quota Attainment", "CRM / Salesforce",
    "Executive Pitching", "Revenue Growth"
  ],
  "Business Development": [
    "Strategic Alliances", "Business Development", "Commercial Partnerships",
    "Channel Sales", "Market Entry", "Contract Negotiation", "Partner Enablement"
  ],
  "Operations & BizOps": [
    "Business Operations", "Process Improvement", "Operational Excellence", "Six Sigma",
    "Automation", "Workflow Optimization", "SLA Tracking", "Vendor Management", "Cost Efficiency"
  ],
  "Supply Chain & Logistics": [
    "Supply Chain Management", "Global Procurement", "Logistics", "Inventory Optimization",
    "Warehouse Management", "Freight Forwarding", "Vendor Management", "Customs Compliance"
  ],
  "Marketing & Growth": [
    "Growth Marketing", "Performance Marketing", "Brand Strategy", "Content Strategy",
    "SEO & SEM", "CAC / LTV Optimization", "Social Media Campaigns", "Demand Generation"
  ],
  "Human Resources & People": [
    "HR Business Partnering", "Talent Acquisition", "Organizational Design",
    "Performance Management", "Employee Engagement", "Executive Coaching", "HR Policies"
  ],
};

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data: initialProfile, isLoading } = useProfile();
  const { data: presets = [] } = usePresets();
  const { data: themesData } = useThemes();

  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"personal" | "experience" | "education" | "skills" | "preferences" | "themes">("personal");
  const [isSaving, setIsSaving] = useState(false);
  const [selectedSkillCategory, setSelectedSkillCategory] = useState<string>("Strategy & Transformation");

  const [formData, setFormData] = useState<Profile>({
    first_name: "",
    last_name: "",
    email: "",
    mobile_no: "",
    linkedin: "",
    github: "",
    portfolio: "",
    education: [],
    experience: [],
    projects: [],
    skills: [],
    certifications: [],
    preset_slug: "blank",
    target_roles: ["Business Analyst - Strategy Office", "Corporate Strategy"],
    target_locations: ["Bengaluru", "Hyderabad", "Mumbai", "Remote"],
    target_work_modes: ["Hybrid", "Remote"],
    target_salary: "₹25L - ₹40L/yr",
  });

  useEffect(() => {
    if (initialProfile) {
      setFormData(initialProfile);
    }
  }, [initialProfile]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch(`${API_URL}/profile/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        throw new Error("Failed to save profile.");
      }
      toast.success("Profile facts saved successfully!");
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
      queryClient.invalidateQueries({ queryKey: queryKeys.workspace });
      queryClient.invalidateQueries({ queryKey: queryKeys.resumes });
    } catch (err: any) {
      toast.error(err?.message || "Failed to save profile.");
    } finally {
      setIsSaving(false);
    }
  };

  const addExperience = () => {
    setFormData({
      ...formData,
      experience: [
        { job_title: "", company: "", location: "", description: "", date_range: "" },
        ...formData.experience,
      ],
    });
    setActiveTab("experience");
  };

  const addEducation = () => {
    setFormData({
      ...formData,
      education: [
        { school_name: "", course: "", location: "", description: "", date_range: "" },
        ...formData.education,
      ],
    });
    setActiveTab("education");
  };

  const addSkill = (skillName: string) => {
    if (!skillName.trim()) return;
    const exists = formData.skills.some((s) => s.skill_name.toLowerCase() === skillName.trim().toLowerCase());
    if (exists) {
      toast.info(`"${skillName.trim()}" is already in your skills.`);
      return;
    }
    setFormData({
      ...formData,
      skills: [...formData.skills, { skill_name: skillName.trim(), is_confirmed: true }],
    });
    toast.success(`Added "${skillName.trim()}"`);
  };

  const addMultipleSkills = (skillList: string[]) => {
    const existing = new Set(formData.skills.map((s) => s.skill_name.toLowerCase()));
    const toAdd = skillList.filter((s) => !existing.has(s.toLowerCase()));
    if (toAdd.length === 0) {
      toast.info("All selected skills are already in your profile.");
      return;
    }
    const newItems = toAdd.map((s) => ({ skill_name: s, is_confirmed: true }));
    setFormData({
      ...formData,
      skills: [...formData.skills, ...newItems],
    });
    toast.success(`Added ${toAdd.length} skills from ${selectedSkillCategory}`);
  };

  const removeSkill = (index: number) => {
    const updated = [...formData.skills];
    updated.splice(index, 1);
    setFormData({ ...formData, skills: updated });
  };

  const toggleSkillConfirmed = (index: number) => {
    const updated = [...formData.skills];
    updated[index].is_confirmed = !updated[index].is_confirmed;
    setFormData({ ...formData, skills: updated });
  };

  return (
    <div className="p-4 sm:p-8 max-w-5xl mx-auto space-y-6 font-sans">
      {/* ── Page Header ── */}
      <div className="bg-white border border-slate-200/90 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold mb-2">
            <User className="w-3.5 h-3.5" />
            Verified Career Facts
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Career Profile & Preferences
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Your single source of truth for all resumes. Zero AI hallucinations — facts, metrics, and roles extracted here govern every tailored application.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={async () => {
              if (!confirm("Are you sure you want to reset to a completely clean profile? This will clear all data so you can upload a fresh CV.")) return;
              try {
                const res = await fetch(`${API_URL}/profile/reset`, { method: "POST" });
                if (res.ok) {
                  setFormData({
                    first_name: "",
                    last_name: "",
                    mobile_no: "",
                    email: "",
                    linkedin: "",
                    github: "",
                    portfolio: "",
                    education: [],
                    experience: [],
                    projects: [],
                    skills: [],
                    certifications: [],
                    target_roles: [],
                    target_locations: [],
                    target_work_modes: ["Hybrid"],
                    target_salary: "",
                  });
                  void queryClient.invalidateQueries({ queryKey: queryKeys.profile });
                  void queryClient.invalidateQueries({ queryKey: queryKeys.workspace });
                  void queryClient.invalidateQueries({ queryKey: queryKeys.resumes });
                  toast.success("Reset to clean state. Ready for fresh CV upload!");
                }
              } catch (err) {
                toast.error("Failed to reset profile.");
              }
            }}
            className="px-3.5 py-2.5 rounded-xl border border-red-200 hover:bg-red-50 text-red-600 font-bold text-xs transition-all inline-flex items-center gap-1.5"
            title="Wipe previous data and start fresh"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Clean
          </button>

          <button
            type="button"
            onClick={() => setIsOnboardingOpen(true)}
            className="px-4 py-2.5 rounded-xl border border-blue-200 bg-blue-50/70 hover:bg-blue-100/70 text-blue-700 font-bold text-xs transition-all inline-flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4 text-blue-600" />
            Upload CV (PDF/DOCX)
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm hover:shadow transition-all inline-flex items-center gap-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* ── Navigation Tabs (Executive Segmented Pill Menu - No Top Scrollbar) ── */}
      <div className="bg-slate-200/80 p-1.5 rounded-2xl flex flex-wrap items-center gap-1.5 border border-slate-300/60 shadow-2xs">
        {[
          { id: "personal", label: "Personal & Contacts", icon: User },
          { id: "experience", label: "Experience", count: formData.experience.length, icon: Briefcase },
          { id: "education", label: "Education", count: formData.education.length, icon: GraduationCap },
          { id: "skills", label: "Skills Bank", count: formData.skills.length, icon: Sparkles },
          { id: "themes", label: "Career Themes", icon: Layers },
          { id: "preferences", label: "Target Preferences", icon: MapPin },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                isActive
                  ? "bg-white text-slate-900 shadow-sm border border-slate-200/80 font-black"
                  : "text-slate-600 hover:text-slate-900 hover:bg-white/60 font-semibold"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-blue-600" : "text-slate-500"}`} />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`text-[10px] font-extrabold px-1.5 py-0.5 rounded-full ${
                    isActive ? "bg-blue-100 text-blue-700" : "bg-slate-300/70 text-slate-700"
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Tab Content ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        
        {/* Tab 1: Personal Details */}
        {activeTab === "personal" && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">Personal & Contact Information</h3>
              <p className="text-xs text-slate-500 mt-0.5">Basic contact details rendered on the resume header.</p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1.5">First Name</label>
                <input
                  type="text"
                  value={formData.first_name || ""}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 text-xs font-medium"
                  placeholder="e.g. Abhinav"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Last Name</label>
                <input
                  type="text"
                  value={formData.last_name || ""}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 text-xs font-medium"
                  placeholder="e.g. Agrawal"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Email Address</label>
                <input
                  type="email"
                  value={formData.email || ""}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 text-xs font-medium"
                  placeholder="e.g. abhinav@example.com"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Mobile / Phone</label>
                <input
                  type="text"
                  value={formData.mobile_no || ""}
                  onChange={(e) => setFormData({ ...formData, mobile_no: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 text-xs font-medium"
                  placeholder="+91 98765 43210"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">LinkedIn Profile URL</label>
                <input
                  type="url"
                  value={formData.linkedin || ""}
                  onChange={(e) => setFormData({ ...formData, linkedin: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 text-xs font-medium"
                  placeholder="https://linkedin.com/in/username"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">GitHub / Portfolio Website</label>
                <input
                  type="url"
                  value={formData.portfolio || formData.github || ""}
                  onChange={(e) => setFormData({ ...formData, portfolio: e.target.value, github: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 text-xs font-medium"
                  placeholder="https://github.com/username or portfolio"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <label className="block font-bold text-slate-700 mb-1.5 text-xs">Primary Candidate Archetype Preset</label>
              <select
                value={formData.preset_slug || "blank"}
                onChange={(e) => setFormData({ ...formData, preset_slug: e.target.value })}
                className="w-full sm:w-1/2 p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 text-xs bg-white text-slate-900 font-medium"
              >
                <option value="blank">General / Blank Preset</option>
                {presets.map((p) => (
                  <option key={p.slug} value={p.slug}>
                    {p.display_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Tab 2: Experience Tab (Multi-Company Extraction Verified) */}
        {activeTab === "experience" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Work Experience</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Captured across all previous employers with achievements and metrics.
                </p>
              </div>
              <button
                type="button"
                onClick={addExperience}
                className="px-3.5 py-2 rounded-xl bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold inline-flex items-center gap-1.5 transition-colors"
              >
                <Plus className="w-4 h-4" /> Add Role
              </button>
            </div>

            {formData.experience.length === 0 ? (
              <div className="text-center py-12 rounded-2xl border border-dashed border-slate-200 text-slate-400 space-y-3">
                <Briefcase className="w-8 h-8 mx-auto text-slate-300" />
                <div className="text-xs font-semibold">No work experience captured yet.</div>
                <button
                  type="button"
                  onClick={() => setIsOnboardingOpen(true)}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs"
                >
                  Upload CV to Auto-Extract Companies
                </button>
              </div>
            ) : (
              <div className="space-y-5">
                {formData.experience.map((exp, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-2xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 space-y-4 relative text-xs shadow-2xs transition-all"
                  >
                    <div className="flex items-center justify-between pr-8 border-b border-slate-200/60 pb-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 font-black text-xs flex items-center justify-center shrink-0">
                          {idx + 1}
                        </div>
                        <div>
                          <div className="font-extrabold text-slate-900 text-sm">
                            {exp.job_title || "Untitled Role"}
                          </div>
                          <div className="text-xs text-slate-500 font-semibold">
                            {exp.company || "Company Name"}
                          </div>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          const updated = [...formData.experience];
                          updated.splice(idx, 1);
                          setFormData({ ...formData, experience: updated });
                        }}
                        className="text-slate-400 hover:text-rose-600 transition-colors p-1"
                        title="Remove role"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Job Title</label>
                        <input
                          type="text"
                          value={exp.job_title}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].job_title = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. Lead Business Analyst"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Company / Organization</label>
                        <input
                          type="text"
                          value={exp.company}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].company = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. Strategy Office / Deloitte"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Date Range</label>
                        <input
                          type="text"
                          value={exp.date_range || ""}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].date_range = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. Jan 2021 – Present"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Location</label>
                        <input
                          type="text"
                          value={exp.location || ""}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].location = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. Bengaluru, India"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block font-bold text-slate-700 mb-1">
                        Accomplishments & Quantified Results (Confirmed Facts)
                      </label>
                      <textarea
                        rows={3}
                        value={exp.description || ""}
                        onChange={(e) => {
                          const updated = [...formData.experience];
                          updated[idx].description = e.target.value;
                          setFormData({ ...formData, experience: updated });
                        }}
                        className="w-full p-3 rounded-xl border border-slate-300 bg-white leading-relaxed text-slate-900 font-mono text-[11px]"
                        placeholder="• Led cross-functional growth workstream boosting ARR by $1.2M&#10;• Designed financial payback models for executive stakeholders..."
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Education Tab */}
        {activeTab === "education" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Academic Background</h3>
                <p className="text-xs text-slate-500 mt-0.5">Degrees, universities, and specializations.</p>
              </div>
              <button
                type="button"
                onClick={addEducation}
                className="px-3.5 py-2 rounded-xl bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold inline-flex items-center gap-1.5 transition-colors"
              >
                <Plus className="w-4 h-4" /> Add Degree
              </button>
            </div>

            {formData.education.length === 0 ? (
              <div className="text-center py-12 rounded-2xl border border-dashed border-slate-200 text-slate-400 space-y-3">
                <GraduationCap className="w-8 h-8 mx-auto text-slate-300" />
                <div className="text-xs font-semibold">No academic credentials recorded yet.</div>
                <button
                  type="button"
                  onClick={addEducation}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs"
                >
                  Add Your Degree
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {formData.education.map((edu, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-2xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 space-y-3 relative text-xs shadow-2xs transition-all"
                  >
                    <button
                      type="button"
                      onClick={() => {
                        const updated = [...formData.education];
                        updated.splice(idx, 1);
                        setFormData({ ...formData, education: updated });
                      }}
                      className="absolute top-4 right-4 text-slate-400 hover:text-rose-600 transition-colors p-1"
                      title="Remove degree"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pr-8">
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">School / University</label>
                        <input
                          type="text"
                          value={edu.school_name}
                          onChange={(e) => {
                            const updated = [...formData.education];
                            updated[idx].school_name = e.target.value;
                            setFormData({ ...formData, education: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. Indian Institute of Management (IIM)"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Degree / Course</label>
                        <input
                          type="text"
                          value={edu.course}
                          onChange={(e) => {
                            const updated = [...formData.education];
                            updated[idx].course = e.target.value;
                            setFormData({ ...formData, education: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. MBA / PGDM in Finance & Strategy"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Date Range</label>
                        <input
                          type="text"
                          value={edu.date_range || ""}
                          onChange={(e) => {
                            const updated = [...formData.education];
                            updated[idx].date_range = e.target.value;
                            setFormData({ ...formData, education: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. 2017 – 2019"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Location</label>
                        <input
                          type="text"
                          value={edu.location || ""}
                          onChange={(e) => {
                            const updated = [...formData.education];
                            updated[idx].location = e.target.value;
                            setFormData({ ...formData, education: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 font-medium"
                          placeholder="e.g. Kolkata, India"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Skills Bank with Auto-Suggest and Domain Categories */}
        {activeTab === "skills" && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">Verified Skills Bank</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    100% verified skills used for instant match scoring against live job descriptions.
                  </p>
                </div>
                <div className="text-xs font-extrabold px-3 py-1 bg-emerald-50 text-emerald-800 rounded-full border border-emerald-200">
                  {formData.skills.length} Confirmed Skills
                </div>
              </div>
            </div>

            {/* Quick add custom skill */}
            <div className="flex gap-2">
              <input
                type="text"
                id="newSkillInput"
                placeholder="Type skill name (e.g. Financial Modeling, M&A Due Diligence, SQL, Stakeholder Management)..."
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkill(e.currentTarget.value);
                    e.currentTarget.value = "";
                  }
                }}
                className="text-xs p-3 rounded-xl border border-slate-300 flex-1 focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 text-slate-900 font-medium"
              />
              <button
                type="button"
                onClick={() => {
                  const el = document.getElementById("newSkillInput") as HTMLInputElement;
                  if (el) {
                    addSkill(el.value);
                    el.value = "";
                  }
                }}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition-all shadow-xs"
              >
                Add Skill
              </button>
            </div>

            {/* Existing Skills Pills */}
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-800">Your Current Skills</div>
              <div className="flex flex-wrap gap-2 pt-1 max-h-60 overflow-y-auto p-1">
                {formData.skills.map((s, idx) => (
                  <div
                    key={idx}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                      s.is_confirmed
                        ? "bg-emerald-50 text-emerald-900 border-emerald-300 shadow-2xs"
                        : "bg-slate-100 text-slate-700 border-slate-200"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleSkillConfirmed(idx)}
                      title={s.is_confirmed ? "Confirmed skill (used in matching)" : "Click to confirm"}
                    >
                      <CheckCircle2
                        className={`w-3.5 h-3.5 ${
                          s.is_confirmed ? "text-emerald-600 fill-emerald-100" : "text-slate-400"
                        }`}
                      />
                    </button>
                    <span>{s.skill_name}</span>
                    <button
                      type="button"
                      onClick={() => removeSkill(idx)}
                      className="ml-1 text-slate-400 hover:text-rose-600 font-bold"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Domain Skills Palette */}
            <div className="pt-5 border-t border-slate-100 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h4 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    Recommended Skills by Profile Theme
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    Click to add any industry skill relevant to your target positions.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => addMultipleSkills(THEME_SKILL_SUGGESTIONS[selectedSkillCategory] || [])}
                  className="px-3 py-1.5 rounded-lg bg-blue-100 hover:bg-blue-200 text-blue-800 text-[11px] font-bold self-start transition-colors"
                >
                  + Add All for {selectedSkillCategory}
                </button>
              </div>

              {/* Theme Selector Pills */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {Object.keys(THEME_SKILL_SUGGESTIONS).map((themeName) => (
                  <button
                    key={themeName}
                    type="button"
                    onClick={() => setSelectedSkillCategory(themeName)}
                    className={`px-3 py-1 rounded-lg text-[11px] font-bold transition-all ${
                      selectedSkillCategory === themeName
                        ? "bg-slate-900 text-white shadow-2xs"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {themeName}
                  </button>
                ))}
              </div>

              {/* Suggestions Pills */}
              <div className="flex flex-wrap gap-1.5 p-3 rounded-2xl bg-slate-50 border border-slate-200">
                {(THEME_SKILL_SUGGESTIONS[selectedSkillCategory] || []).map((sk) => {
                  const isAlreadyAdded = formData.skills.some(
                    (s) => s.skill_name.toLowerCase() === sk.toLowerCase()
                  );
                  return (
                    <button
                      key={sk}
                      type="button"
                      disabled={isAlreadyAdded}
                      onClick={() => addSkill(sk)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all inline-flex items-center gap-1 ${
                        isAlreadyAdded
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200 opacity-60 cursor-default"
                          : "bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-300 cursor-pointer"
                      }`}
                    >
                      {isAlreadyAdded ? <Check className="w-3 h-3 text-emerald-600" /> : <Plus className="w-3 h-3 text-slate-400" />}
                      {sk}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Career Themes / Archetypes */}
        {activeTab === "themes" && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">Career Themes & Archetypes</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Maintain specialized resumes tailored to distinct functions: Sales, BD, Product, Tech, Finance, Operations, SCM, HR, Strategy.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {(themesData?.themes || []).map((theme: CareerTheme) => (
                <div
                  key={theme.id}
                  className="p-4 rounded-2xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 space-y-2 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{theme.name}</span>
                    <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-blue-100 text-blue-800">
                      {theme.recommended_template} template
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 line-clamp-2">{theme.description}</p>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {theme.target_roles.slice(0, 3).map((r, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 bg-white border border-slate-200 rounded-md text-slate-600 font-medium">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 6: Target Preferences */}
        {activeTab === "preferences" && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <h3 className="text-base font-extrabold text-slate-900">Job Discovery Preferences</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Governs automatic relevance scoring and role recommendations in Find Jobs.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Target Roles</label>
                <input
                  type="text"
                  value={formData.target_roles?.join(", ") || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      target_roles: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    })
                  }
                  placeholder="e.g. Strategy Manager, Chief of Staff, Business Analyst"
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Preferred Locations</label>
                <input
                  type="text"
                  value={formData.target_locations?.join(", ") || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      target_locations: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    })
                  }
                  placeholder="e.g. Bengaluru, Hyderabad, Mumbai, Remote"
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Target Salary Expectation</label>
                <input
                  type="text"
                  value={formData.target_salary || ""}
                  onChange={(e) => setFormData({ ...formData, target_salary: e.target.value })}
                  placeholder="e.g. ₹25L - ₹40L/yr"
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1.5">Preferred Work Model</label>
                <select
                  value={formData.target_work_modes?.[0] || "Hybrid"}
                  onChange={(e) => setFormData({ ...formData, target_work_modes: [e.target.value] })}
                  className="w-full p-3 rounded-xl border border-slate-300 focus:outline-none focus:border-blue-600 bg-white text-slate-900 font-medium"
                >
                  <option value="Hybrid">Hybrid</option>
                  <option value="Remote">Remote Only</option>
                  <option value="Onsite">Onsite Only</option>
                  <option value="Any">Any Arrangement</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── CV Upload & Auto-Extraction Onboarding Modal ── */}
      <ResumeOnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        onSuccess={async (parsed) => {
          if (parsed) {
            const updated: Profile = {
              ...formData,
              first_name: parsed.first_name || formData.first_name,
              last_name: parsed.last_name || formData.last_name,
              email: parsed.email || formData.email,
              mobile_no: parsed.mobile_no || formData.mobile_no,
              skills: parsed.skills?.length ? parsed.skills : formData.skills,
              experience: parsed.experience?.length ? parsed.experience : formData.experience,
              education: parsed.education?.length ? parsed.education : formData.education,
            };
            setFormData(updated);

            // Immediately auto-save to backend so facts are persisted
            try {
              await fetch(`${API_URL}/profile/save`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(updated),
              });
              queryClient.invalidateQueries({ queryKey: queryKeys.profile });
              queryClient.invalidateQueries({ queryKey: queryKeys.resumes });
              toast.success(
                `Successfully extracted ${updated.experience.length} companies, ${updated.education.length} degrees, and ${updated.skills.length} skills!`
              );
            } catch (err) {
              toast.info("Extracted into form. Click 'Save Changes' to commit.");
            }
          }
        }}
      />
    </div>
  );
}
