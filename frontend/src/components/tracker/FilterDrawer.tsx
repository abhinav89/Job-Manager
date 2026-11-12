"use client";

import React, { useState } from "react";
import { X, SlidersHorizontal, Check, Search, Building2, MapPin, Briefcase } from "lucide-react";

export interface FilterState {
  workModel: string;
  jobType: string;
  seniority: string;
  datePosted: string;
  country: string;
  city: string;
  yearsExperience: number;
  roleCategory: string;
  companyInclude: string;
  companyExclude: string;
}

export const defaultFilterState: FilterState = {
  workModel: "all",
  jobType: "all",
  seniority: "all",
  datePosted: "any",
  country: "Global / Anywhere",
  city: "All Cities",
  yearsExperience: 5,
  roleCategory: "all",
  companyInclude: "",
  companyExclude: "",
};

interface FilterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  filters: FilterState;
  onApplyFilters: (filters: FilterState) => void;
  onResetFilters: () => void;
  totalMatchingJobs: number;
}

export function FilterDrawer({
  isOpen,
  onClose,
  filters,
  onApplyFilters,
  onResetFilters,
  totalMatchingJobs,
}: FilterDrawerProps) {
  const [activeTab, setActiveTab] = useState<"basic" | "location" | "experience" | "industry" | "company">("basic");
  const [draft, setDraft] = useState<FilterState>(filters);

  if (!isOpen) return null;

  const handleApply = () => {
    onApplyFilters(draft);
    onClose();
  };

  const handleReset = () => {
    setDraft(defaultFilterState);
    onResetFilters();
  };

  const citiesInIndia = [
    "All Cities", "Bengaluru", "Hyderabad", "Mumbai", "Delhi NCR", "Pune", "Chennai", "Kolkata", "Ahmedabad", "Gurugram"
  ];

  const roleCategories = [
    "Corporate Finance & FP&A", "Management & Strategy Consulting", "Technology & IT Advisory",
    "Product Management", "Data & Analytics", "Risk & M&A Advisory", "Operations & Supply Chain"
  ];

  const industries = [
    "Consulting & Advisory", "Financial Services (BFSI)", "Technology & Software",
    "Automotive & Retail", "Biotech & Pharma", "E-commerce & Logistics"
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col justify-between overflow-hidden">
        {/* Top Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between shrink-0 bg-white">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-blue-600" />
              All Filters
            </h2>
          </div>

          <button
            onClick={handleApply}
            className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
          >
            Show {totalMatchingJobs} jobs
          </button>
        </div>

        {/* Active Filter Chips */}
        <div className="px-5 py-2.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium mr-1">Active:</span>
          {draft.country && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
              {draft.country}
            </span>
          )}
          {draft.city && draft.city !== "All Cities" && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
              {draft.city}
            </span>
          )}
          {draft.workModel !== "all" && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-200 text-slate-800 font-medium">
              {draft.workModel}
            </span>
          )}
          {draft.seniority !== "all" && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-200 text-slate-800 font-medium">
              {draft.seniority} Level
            </span>
          )}
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-200 text-slate-800 font-medium">
            Up to {draft.yearsExperience} yrs exp
          </span>
        </div>

        {/* Body Split View: Left Tabs, Right Content */}
        <div className="flex-1 min-h-0 flex overflow-hidden">
          {/* Left Category Navigation */}
          <div className="w-48 sm:w-56 border-r border-slate-200 bg-slate-50 p-3 space-y-1 overflow-y-auto">
            <button
              onClick={() => setActiveTab("basic")}
              className={`w-full text-left p-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "basic" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Basic Criteria
              <div className="text-[10px] text-slate-400 font-normal mt-0.5">Work model, Type, Date</div>
            </button>

            <button
              onClick={() => setActiveTab("location")}
              className={`w-full text-left p-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "location" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Location
              <div className="text-[10px] text-slate-400 font-normal mt-0.5">Country, Cities</div>
            </button>

            <button
              onClick={() => setActiveTab("experience")}
              className={`w-full text-left p-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "experience" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Experience
              <div className="text-[10px] text-slate-400 font-normal mt-0.5">Years of experience</div>
            </button>

            <button
              onClick={() => setActiveTab("industry")}
              className={`w-full text-left p-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "industry" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Role & Industry
              <div className="text-[10px] text-slate-400 font-normal mt-0.5">Function & sector</div>
            </button>

            <button
              onClick={() => setActiveTab("company")}
              className={`w-full text-left p-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "company" ? "bg-white text-blue-700 shadow-xs border border-slate-200" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Company
              <div className="text-[10px] text-slate-400 font-normal mt-0.5">Include / Exclude</div>
            </button>
          </div>

          {/* Right Tab Content */}
          <div className="flex-1 p-5 sm:p-6 overflow-y-auto space-y-6">
            {activeTab === "basic" && (
              <div className="space-y-5">
                {/* Work Model */}
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    Work Model
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {["all", "Remote", "Hybrid", "Onsite"].map((wm) => (
                      <button
                        key={wm}
                        type="button"
                        onClick={() => setDraft({ ...draft, workModel: wm })}
                        className={`p-3 rounded-xl border text-left font-medium transition-all ${
                          draft.workModel === wm
                            ? "border-blue-600 bg-blue-50 text-blue-700 font-semibold"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {wm === "all" ? "Any Work Model" : wm}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Experience Level */}
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    Experience Level / Seniority
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {["all", "Entry", "Mid", "Senior", "Lead / Executive"].map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => setDraft({ ...draft, seniority: lvl })}
                        className={`p-3 rounded-xl border text-left font-medium transition-all ${
                          draft.seniority === lvl
                            ? "border-blue-600 bg-blue-50 text-blue-700 font-semibold"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {lvl === "all" ? "All Levels" : lvl}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Date Posted */}
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    Date Posted
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      { id: "any", label: "Any time" },
                      { id: "24h", label: "Past 24 hours" },
                      { id: "week", label: "Past week" },
                      { id: "month", label: "Past month" },
                    ].map((dp) => (
                      <button
                        key={dp.id}
                        type="button"
                        onClick={() => setDraft({ ...draft, datePosted: dp.id })}
                        className={`p-3 rounded-xl border text-left font-medium transition-all ${
                          draft.datePosted === dp.id
                            ? "border-blue-600 bg-blue-50 text-blue-700 font-semibold"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {dp.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "location" && (
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    Country
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {["India", "United States", "Global / Anywhere"].map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setDraft({ ...draft, country: c })}
                        className={`p-3 rounded-xl border text-left font-medium transition-all ${
                          draft.country === c
                            ? "border-blue-600 bg-blue-50 text-blue-700 font-semibold"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    City (in India)
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {citiesInIndia.map((city) => (
                      <button
                        key={city}
                        type="button"
                        onClick={() => setDraft({ ...draft, city })}
                        className={`p-2.5 rounded-xl border text-left font-medium transition-all ${
                          draft.city === city
                            ? "border-blue-600 bg-blue-50 text-blue-700 font-semibold"
                            : "border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {city}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "experience" && (
              <div className="space-y-5">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Years of Experience
                    </label>
                    <span className="text-sm font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full">
                      Up to {draft.yearsExperience} yrs
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={20}
                    step={1}
                    value={draft.yearsExperience}
                    onChange={(e) => setDraft({ ...draft, yearsExperience: parseInt(e.target.value, 10) })}
                    className="w-full accent-blue-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                    <span>0 yrs</span>
                    <span>5 yrs</span>
                    <span>10 yrs</span>
                    <span>15 yrs</span>
                    <span>20+ yrs</span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    Target Role Functions
                  </label>
                  <div className="space-y-2 text-xs">
                    {roleCategories.map((rc) => (
                      <label
                        key={rc}
                        className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer"
                      >
                        <input
                          type="radio"
                          name="roleCategory"
                          checked={draft.roleCategory === rc}
                          onChange={() => setDraft({ ...draft, roleCategory: rc })}
                          className="accent-blue-600"
                        />
                        <span className="font-medium text-slate-800">{rc}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "industry" && (
              <div className="space-y-4">
                <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                  Target Industries
                </label>
                <div className="space-y-2 text-xs">
                  {industries.map((ind) => (
                    <label
                      key={ind}
                      className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer"
                    >
                      <input type="checkbox" defaultChecked className="accent-blue-600 rounded" />
                      <span className="font-medium text-slate-800">{ind}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "company" && (
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Show Jobs From Specific Companies
                  </label>
                  <p className="text-xs text-slate-500 mb-2">e.g. Deloitte, McKinsey, Google, NTT</p>
                  <input
                    type="text"
                    value={draft.companyInclude}
                    onChange={(e) => setDraft({ ...draft, companyInclude: e.target.value })}
                    placeholder="Search or enter company name..."
                    className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Exclude Companies
                  </label>
                  <p className="text-xs text-slate-500 mb-2">Hide companies you do not want to see</p>
                  <input
                    type="text"
                    value={draft.companyExclude}
                    onChange={(e) => setDraft({ ...draft, companyExclude: e.target.value })}
                    placeholder="Enter companies to exclude..."
                    className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-600 bg-white"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 sm:p-5 border-t border-slate-200 bg-slate-50 flex items-center justify-between shrink-0">
          <button
            type="button"
            onClick={handleReset}
            className="text-xs font-semibold text-slate-600 hover:text-slate-900 hover:underline"
          >
            Clear all filters
          </button>

          <button
            type="button"
            onClick={handleApply}
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition-all"
          >
            Show {totalMatchingJobs} jobs
          </button>
        </div>
      </div>
    </div>
  );
}
