"use client";

import React, { useState } from "react";
import {
  Check,
  Sparkles,
  Zap,
  Crown,
  ShieldCheck,
  CreditCard,
  ArrowRight,
  Clock,
  Briefcase,
  HelpCircle,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/authContext";

export default function PricingPage() {
  const { user } = useAuth();
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">("annual");

  const handleWaitlist = (planName: string) => {
    toast.success(`You are added to the VIP waitlist for ${planName}! We'll notify you when it launches.`);
  };

  return (
    <div className="p-4 sm:p-8 max-w-6xl mx-auto space-y-10 font-sans">
      {/* ── Page Header ── */}
      <div className="text-center space-y-3 max-w-2xl mx-auto pt-4">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold">
          <CreditCard className="w-3.5 h-3.5" />
          Transparent Plans &amp; Membership
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
          Supercharge Your Career Search
        </h1>
        <p className="text-sm text-slate-500 leading-relaxed">
          Access over 1,700+ verified executive and engineering opportunities. All current core tools are included in your complimentary Free plan.
        </p>

        {/* Current Active Plan Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold mt-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Active Plan: Free Community Membership ({user?.email || "Signed In"})</span>
        </div>
      </div>

      {/* ── Pricing Cards Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        {/* Tier 1: Free Starter */}
        <div className="bg-white border-2 border-emerald-500 rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-4 right-4">
            <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase tracking-wider">
              ACTIVE PLAN
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">STARTER</span>
              <h3 className="text-2xl font-black text-slate-900 mt-1">Free Forever</h3>
              <p className="text-xs text-slate-500 mt-1">Essential tools for active job discovery and tracking.</p>
            </div>

            <div className="pt-2 pb-4 border-b border-slate-100">
              <span className="text-4xl font-black text-slate-900">₹0</span>
              <span className="text-xs text-slate-400 font-medium"> / lifetime</span>
            </div>

            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start gap-2.5">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>1,700+ Verified Openings</strong> across India &amp; Global</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>10 ATS-Proof Themes</strong> with direct PDF downloads</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Match Score &amp; Evidence</strong> breakdown for every job</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Direct Apply</strong> using chosen resume theme</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Private Kanban Tracker</strong> for all applications</span>
              </li>
            </ul>
          </div>

          <div className="pt-8">
            <button
              type="button"
              disabled
              className="w-full py-3 rounded-2xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold cursor-default flex items-center justify-center gap-1.5"
            >
              <Check className="w-4 h-4" />
              Your Current Plan
            </button>
          </div>
        </div>

        {/* Tier 2: Pro Career Sprint */}
        <div className="bg-white border border-slate-200 hover:border-blue-400 rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col justify-between relative overflow-hidden transition-all">
          <div className="absolute top-4 right-4">
            <span className="px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-black uppercase tracking-wider">
              UPCOMING
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">PRO MEMBERSHIP</span>
              <h3 className="text-2xl font-black text-slate-900 mt-1">Career Sprint</h3>
              <p className="text-xs text-slate-500 mt-1">Automated AI customizer for aggressive application runs.</p>
            </div>

            <div className="pt-2 pb-4 border-b border-slate-100">
              <span className="text-4xl font-black text-slate-900">₹1,499</span>
              <span className="text-xs text-slate-400 font-medium"> / month</span>
            </div>

            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span><strong>Unlimited AI Resume Tailoring</strong> with strict zero-hallucination guarantee</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span><strong>Executive Cover Letter Generation</strong> matching company voice</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span><strong>Instant WhatsApp &amp; Telegram Alerts</strong> for early applicant edge</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span><strong>AI Interview Question Generator</strong> based on target JD</span>
              </li>
            </ul>
          </div>

          <div className="pt-8">
            <button
              type="button"
              onClick={() => handleWaitlist("Pro Career Sprint")}
              className="w-full py-3 rounded-2xl bg-slate-900 hover:bg-blue-600 text-white text-xs font-bold shadow-md transition-all cursor-pointer flex items-center justify-center gap-1.5"
            >
              <Zap className="w-4 h-4" />
              Join Pro Waitlist
            </button>
          </div>
        </div>

        {/* Tier 3: Executive Concierge */}
        <div className="bg-white border border-slate-200 hover:border-amber-400 rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col justify-between relative overflow-hidden transition-all">
          <div className="absolute top-4 right-4">
            <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-black uppercase tracking-wider">
              UPCOMING
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600">HIGH-TOUCH ADVISORY</span>
              <h3 className="text-2xl font-black text-slate-900 mt-1">Executive Advisory</h3>
              <p className="text-xs text-slate-500 mt-1">White-glove positioning for CXO, VP, and Director candidates.</p>
            </div>

            <div className="pt-2 pb-4 border-b border-slate-100">
              <span className="text-4xl font-black text-slate-900">₹7,999</span>
              <span className="text-xs text-slate-400 font-medium"> / quarter</span>
            </div>

            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start gap-2.5">
                <Crown className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span><strong>1-on-1 Executive Pitch Deck</strong> &amp; Board Profile Formulation</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Crown className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span><strong>Confidential Search Representation</strong> via DealOS partner fund network</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Crown className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span><strong>Senior Recruiter Direct Introductions</strong> for unadvertised roles</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Crown className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span><strong>Dedicated Human Coach Review</strong> before submitting critical bids</span>
              </li>
            </ul>
          </div>

          <div className="pt-8">
            <button
              type="button"
              onClick={() => handleWaitlist("Executive Advisory")}
              className="w-full py-3 rounded-2xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-md transition-all cursor-pointer flex items-center justify-center gap-1.5"
            >
              <Crown className="w-4 h-4" />
              Join Executive Waitlist
            </button>
          </div>
        </div>
      </div>

      {/* ── FAQ Section ── */}
      <div className="bg-slate-50 border border-slate-200 rounded-3xl p-6 sm:p-8 space-y-4">
        <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-blue-600" />
          Frequently Asked Questions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1">
            <span className="font-bold text-slate-800">Is the Free plan truly free?</span>
            <p className="text-slate-500 leading-relaxed">
              Yes, all current core functionality—including search across all 1,700+ openings, LaTeX theme downloads, and application pipeline tracking—is completely free.
            </p>
          </div>
          <div className="space-y-1">
            <span className="font-bold text-slate-800">When will paid plans launch?</span>
            <p className="text-slate-500 leading-relaxed">
              Paid automation tiers are in private beta. Joining the waitlist grants you priority onboarding and a launch-week discount.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
