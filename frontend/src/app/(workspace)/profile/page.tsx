"use client";

import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  User,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Award,
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
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { useProfile, usePresets, queryKeys, type Profile } from "@/lib/queries";
import { ResumeOnboardingModal } from "@/components/ResumeOnboardingModal";

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data: initialProfile, isLoading } = useProfile();
  const { data: presets = [] } = usePresets();

  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"personal" | "experience" | "education" | "skills" | "preferences">("personal");
  const [isSaving, setIsSaving] = useState(false);

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
      toast.info("Skill already exists in your profile.");
      return;
    }
    setFormData({
      ...formData,
      skills: [...formData.skills, { skill_name: skillName.trim(), is_confirmed: true }],
    });
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
    <div className="p-4 sm:p-8 max-w-5xl mx-auto space-y-8 font-sans">
      {/* ── Page Header ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2">
            <User className="w-3.5 h-3.5" />
            Confirmed Career Record
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Career Profile & Preferences
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Your verified career facts are the single source of truth for all tailored resumes. No AI hallucinations.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={async () => {
              if (!confirm("Are you sure you want to reset to a completely clean, fresh profile? This will clear all entered facts so you can start fresh.")) return;
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
                  toast.success("Reset to clean state. Ready for your fresh CV!");
                }
              } catch (err) {
                toast.error("Failed to reset profile.");
              }
            }}
            className="px-3.5 py-2.5 rounded-xl border border-red-200 hover:bg-red-50 text-red-600 font-semibold text-xs transition-all inline-flex items-center gap-1.5"
            title="Wipe previous data and start fresh"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Clean
          </button>

          <button
            type="button"
            onClick={() => setIsOnboardingOpen(true)}
            className="px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-all inline-flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4 text-blue-600" />
            Upload CV (PDF/DOCX)
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm hover:shadow transition-all inline-flex items-center gap-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* ── Navigation Tabs ── */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto text-xs font-semibold">
        {[
          { id: "personal", label: "Personal & Contacts", icon: <User className="w-4 h-4" /> },
          { id: "experience", label: `Experience (${formData.experience.length})`, icon: <Briefcase className="w-4 h-4" /> },
          { id: "education", label: `Education (${formData.education.length})`, icon: <GraduationCap className="w-4 h-4" /> },
          { id: "skills", label: `Skills (${formData.skills.length})`, icon: <Sparkles className="w-4 h-4" /> },
          { id: "preferences", label: "Target Preferences", icon: <MapPin className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-3 px-3.5 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        {/* Personal Details */}
        {activeTab === "personal" && (
          <div className="space-y-6">
            <h3 className="text-base font-bold text-slate-900 border-b pb-3">Contact & Identification</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">First Name</label>
                <input
                  type="text"
                  value={formData.first_name || ""}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                  placeholder="e.g. Abhinav"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Last Name</label>
                <input
                  type="text"
                  value={formData.last_name || ""}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                  placeholder="e.g. Agrawal"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={formData.email || ""}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                  placeholder="e.g. abhinav@example.com"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Mobile / Phone</label>
                <input
                  type="text"
                  value={formData.mobile_no || ""}
                  onChange={(e) => setFormData({ ...formData, mobile_no: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                  placeholder="+91 98765 43210"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">LinkedIn Profile URL</label>
                <input
                  type="url"
                  value={formData.linkedin || ""}
                  onChange={(e) => setFormData({ ...formData, linkedin: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                  placeholder="https://linkedin.com/in/username"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">GitHub / Portfolio</label>
                <input
                  type="url"
                  value={formData.portfolio || formData.github || ""}
                  onChange={(e) => setFormData({ ...formData, portfolio: e.target.value, github: e.target.value })}
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                  placeholder="https://github.com/username"
                />
              </div>
            </div>

            <div className="pt-4 border-t">
              <label className="block font-semibold text-slate-700 mb-1 text-xs">Primary Role Preset</label>
              <select
                value={formData.preset_slug || "blank"}
                onChange={(e) => setFormData({ ...formData, preset_slug: e.target.value })}
                className="w-full sm:w-1/2 p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600 text-xs bg-white"
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

        {/* Experience Tab */}
        {activeTab === "experience" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">Work Experience</h3>
              <button
                type="button"
                onClick={addExperience}
                className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold inline-flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add Role
              </button>
            </div>

            {formData.experience.length === 0 ? (
              <div className="text-center py-10 text-slate-400 text-xs">
                No work experience added yet. Click &quot;Add Role&quot; or import from CV.
              </div>
            ) : (
              <div className="space-y-4">
                {formData.experience.map((exp, idx) => (
                  <div key={idx} className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-3 relative text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        const updated = [...formData.experience];
                        updated.splice(idx, 1);
                        setFormData({ ...formData, experience: updated });
                      }}
                      className="absolute top-4 right-4 text-slate-400 hover:text-rose-600 transition-colors"
                      title="Remove experience"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pr-8">
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Job Title</label>
                        <input
                          type="text"
                          value={exp.job_title}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].job_title = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-200 bg-white"
                          placeholder="e.g. Business Analyst"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Company</label>
                        <input
                          type="text"
                          value={exp.company}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].company = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-200 bg-white"
                          placeholder="e.g. Strategy Office"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Date Range</label>
                        <input
                          type="text"
                          value={exp.date_range || ""}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].date_range = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-200 bg-white"
                          placeholder="e.g. 2021 - Present"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">Location</label>
                        <input
                          type="text"
                          value={exp.location || ""}
                          onChange={(e) => {
                            const updated = [...formData.experience];
                            updated[idx].location = e.target.value;
                            setFormData({ ...formData, experience: updated });
                          }}
                          className="w-full p-2.5 rounded-xl border border-slate-200 bg-white"
                          placeholder="e.g. Bengaluru, India"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Accomplishments & Responsibilities (Confirmed Evidence)
                      </label>
                      <textarea
                        rows={3}
                        value={exp.description || ""}
                        onChange={(e) => {
                          const updated = [...formData.experience];
                          updated[idx].description = e.target.value;
                          setFormData({ ...formData, experience: updated });
                        }}
                        className="w-full p-2.5 rounded-xl border border-slate-200 bg-white leading-relaxed"
                        placeholder="Bullet points of verified achievements, metrics, and leadership duties..."
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Education Tab */}
        {activeTab === "education" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">Academic Background</h3>
              <button
                type="button"
                onClick={addEducation}
                className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold inline-flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add Degree
              </button>
            </div>

            <div className="space-y-4">
              {formData.education.map((edu, idx) => (
                <div key={idx} className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-3 relative text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      const updated = [...formData.education];
                      updated.splice(idx, 1);
                      setFormData({ ...formData, education: updated });
                    }}
                    className="absolute top-4 right-4 text-slate-400 hover:text-rose-600 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pr-8">
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">School / University</label>
                      <input
                        type="text"
                        value={edu.school_name}
                        onChange={(e) => {
                          const updated = [...formData.education];
                          updated[idx].school_name = e.target.value;
                          setFormData({ ...formData, education: updated });
                        }}
                        className="w-full p-2.5 rounded-xl border border-slate-200 bg-white"
                        placeholder="e.g. IIM Calcutta"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">Course / Degree</label>
                      <input
                        type="text"
                        value={edu.course}
                        onChange={(e) => {
                          const updated = [...formData.education];
                          updated[idx].course = e.target.value;
                          setFormData({ ...formData, education: updated });
                        }}
                        className="w-full p-2.5 rounded-xl border border-slate-200 bg-white"
                        placeholder="e.g. MBA / PGDM in Finance"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === "skills" && (
          <div className="space-y-6">
            <div className="border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">Skills Bank</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Confirmed skills are used to calculate match relevance scores against live job descriptions.
              </p>
            </div>

            {/* Quick add */}
            <div className="flex gap-2">
              <input
                type="text"
                id="newSkillInput"
                placeholder="Add skill (e.g. Financial Modeling, M&A Due Diligence, SQL)..."
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkill(e.currentTarget.value);
                    e.currentTarget.value = "";
                  }
                }}
                className="text-xs p-3 rounded-xl border border-slate-200 flex-1 focus:outline-none focus:border-blue-600"
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
                className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-all"
              >
                Add Skill
              </button>
            </div>

            {/* Skills Pills */}
            <div className="flex flex-wrap gap-2 pt-2">
              {formData.skills.map((s, idx) => (
                <div
                  key={idx}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    s.is_confirmed
                      ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                      : "bg-slate-100 text-slate-700 border-slate-200"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => toggleSkillConfirmed(idx)}
                    title={s.is_confirmed ? "Confirmed skill" : "Click to confirm"}
                  >
                    <CheckCircle2 className={`w-3.5 h-3.5 ${s.is_confirmed ? "text-emerald-600 fill-emerald-100" : "text-slate-400"}`} />
                  </button>
                  <span>{s.skill_name}</span>
                  <button
                    type="button"
                    onClick={() => removeSkill(idx)}
                    className="ml-1 text-slate-400 hover:text-rose-600"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Target Preferences Tab */}
        {activeTab === "preferences" && (
          <div className="space-y-6">
            <div className="border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">Job Search Preferences</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Steers recommendation and match calculation across job sources.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Roles</label>
                <input
                  type="text"
                  defaultValue="Finance Manager, Strategy Lead, Consulting Manager, FP&A Lead"
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Preferred Locations</label>
                <input
                  type="text"
                  defaultValue="Bengaluru, Hyderabad, Mumbai, Delhi NCR, Remote"
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Work Arrangement</label>
                <select className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600 bg-white">
                  <option>Remote & Hybrid</option>
                  <option>Remote Only</option>
                  <option>Hybrid Only</option>
                  <option>Any (including Onsite)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Salary Range</label>
                <input
                  type="text"
                  defaultValue="₹25L - ₹40L/yr"
                  className="w-full p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <ResumeOnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        onSuccess={(parsed) => {
          if (parsed) {
            setFormData((prev) => ({
              ...prev,
              first_name: parsed.first_name || prev.first_name,
              last_name: parsed.last_name || prev.last_name,
              email: parsed.email || prev.email,
              mobile_no: parsed.mobile_no || prev.mobile_no,
              skills: parsed.skills?.length ? parsed.skills : prev.skills,
              experience: parsed.experience?.length ? parsed.experience : prev.experience,
              education: parsed.education?.length ? parsed.education : prev.education,
            }));
          }
        }}
      />
    </div>
  );
}
