"use client";

import React, { useState, useEffect } from "react";
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
  Loader2,
  Lock,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/authContext";
import { initiateRazorpayPayment } from "@/lib/razorpay";

export default function PricingPage() {
  const { user, isAuthenticated, setIsAuthModalOpen } = useAuth();
  const [activePlan, setActivePlan] = useState<string>("free_starter");
  const [processingPlan, setProcessingPlan] = useState<string | null>(null);

  // Sync active plan from client storage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("dealos_user_plan");
      if (stored) {
        setActivePlan(stored);
      }
    } catch {
      // ignore storage access errors
    }
  }, []);

  const handleSubscribe = async (planId: string, planName: string, amount: number) => {
    if (!isAuthenticated) {
      toast.info("Please sign in first to subscribe to a membership plan.");
      setIsAuthModalOpen(true);
      return;
    }

    setProcessingPlan(planId);
    try {
      await initiateRazorpayPayment({
        planId,
        planName,
        amount,
        user,
        onSuccess: (pId) => {
          setActivePlan(pId);
          try {
            localStorage.setItem("dealos_user_plan", pId);
          } catch {
            // ignore
          }
        },
        onError: (err) => {
          console.error("Payment failure:", err);
        },
      });
    } finally {
      setProcessingPlan(null);
    }
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
          Access over 1,700+ verified executive and engineering opportunities across India. Core search tools are 100% free; accelerate with AI automation.
        </p>

        {/* Current Active Plan Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold mt-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>
            Active Plan: {activePlan === "pro_sprint" ? "Pro Career Sprint" : activePlan === "executive_advisory" ? "Executive Advisory" : "Free Community Membership"} ({user?.email || "Guest"})
          </span>
        </div>
      </div>

      {/* ── Pricing Cards Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        {/* Tier 1: Free Starter */}
        <div className={`bg-white rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col justify-between relative overflow-hidden transition-all ${
          activePlan === "free_starter" ? "border-2 border-emerald-500" : "border border-slate-200"
        }`}>
          {activePlan === "free_starter" && (
            <div className="absolute top-4 right-4">
              <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase tracking-wider">
                ACTIVE PLAN
              </span>
            </div>
          )}

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
              disabled={activePlan === "free_starter"}
              onClick={() => {
                setActivePlan("free_starter");
                localStorage.setItem("dealos_user_plan", "free_starter");
                toast.success("Active plan set to Free Community Membership.");
              }}
              className={`w-full py-3 rounded-2xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                activePlan === "free_starter"
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200 cursor-default"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-800 cursor-pointer"
              }`}
            >
              <Check className="w-4 h-4" />
              {activePlan === "free_starter" ? "Your Current Plan" : "Switch to Free Starter"}
            </button>
          </div>
        </div>

        {/* Tier 2: Pro Career Sprint */}
        <div className={`bg-white rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col justify-between relative overflow-hidden transition-all ${
          activePlan === "pro_sprint" ? "border-2 border-blue-600 shadow-md ring-2 ring-blue-100" : "border border-slate-200 hover:border-blue-400"
        }`}>
          <div className="absolute top-4 right-4">
            {activePlan === "pro_sprint" ? (
              <span className="px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 text-[10px] font-black uppercase tracking-wider">
                ACTIVE PLAN
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-black uppercase tracking-wider">
                POPULAR
              </span>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">PRO MEMBERSHIP</span>
              <h3 className="text-2xl font-black text-slate-900 mt-1">Career Sprint</h3>
              <p className="text-xs text-slate-500 mt-1">Automated AI customizer for aggressive application runs.</p>
            </div>

            <div className="pt-2 pb-4 border-b border-slate-100 flex items-baseline gap-2">
              <span className="text-4xl font-black text-slate-900">₹1</span>
              <span className="text-xs text-amber-700 font-bold bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                Test Price (Temp ₹1)
              </span>
              <span className="text-xs text-slate-400 line-through">₹1,499</span>
            </div>

            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span><strong>Unlimited AI Resume Tailoring</strong> with zero-hallucination guarantee</span>
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

          <div className="pt-8 space-y-2">
            <button
              type="button"
              disabled={activePlan === "pro_sprint" || processingPlan === "pro_sprint"}
              onClick={() => handleSubscribe("pro_sprint", "Pro Career Sprint", 1)}
              className={`w-full py-3 rounded-2xl text-xs font-bold shadow-md transition-all flex items-center justify-center gap-2 ${
                activePlan === "pro_sprint"
                  ? "bg-blue-50 text-blue-800 border border-blue-200 cursor-default"
                  : "bg-blue-600 hover:bg-blue-700 text-white cursor-pointer hover:shadow-lg"
              }`}
            >
              {processingPlan === "pro_sprint" ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting Razorpay...
                </>
              ) : activePlan === "pro_sprint" ? (
                <>
                  <Check className="w-4 h-4 text-blue-700" />
                  Your Active Plan
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Subscribe with Razorpay (₹1 Test)
                </>
              )}
            </button>
            <p className="text-[10px] text-center text-slate-400">
              Instant UPI, GPay, PhonePe, Cards &amp; NetBanking
            </p>
          </div>
        </div>

        {/* Tier 3: Executive Advisory */}
        <div className={`bg-white rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col justify-between relative overflow-hidden transition-all ${
          activePlan === "executive_advisory" ? "border-2 border-amber-500 shadow-md" : "border border-slate-200 hover:border-amber-400"
        }`}>
          <div className="absolute top-4 right-4">
            {activePlan === "executive_advisory" ? (
              <span className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 text-[10px] font-black uppercase tracking-wider">
                ACTIVE PLAN
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-black uppercase tracking-wider">
                HIGH-TOUCH
              </span>
            )}
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
                <span><strong>Confidential Search Representation</strong> via partner fund network</span>
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

          <div className="pt-8 space-y-2">
            <button
              type="button"
              disabled={activePlan === "executive_advisory" || processingPlan === "executive_advisory"}
              onClick={() => handleSubscribe("executive_advisory", "Executive Advisory", 7999)}
              className={`w-full py-3 rounded-2xl text-xs font-bold shadow-md transition-all flex items-center justify-center gap-2 ${
                activePlan === "executive_advisory"
                  ? "bg-amber-50 text-amber-800 border border-amber-200 cursor-default"
                  : "bg-amber-600 hover:bg-amber-700 text-white cursor-pointer hover:shadow-lg"
              }`}
            >
              {processingPlan === "executive_advisory" ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting Razorpay...
                </>
              ) : activePlan === "executive_advisory" ? (
                <>
                  <Check className="w-4 h-4 text-amber-700" />
                  Your Active Plan
                </>
              ) : (
                <>
                  <Crown className="w-4 h-4" />
                  Retain Advisory (₹7,999)
                </>
              )}
            </button>
            <p className="text-[10px] text-center text-slate-400">
              Includes 1-on-1 advisor matching &amp; strategy review
            </p>
          </div>
        </div>
      </div>

      {/* ── Razorpay India Gateway Trust Banner ── */}
      <div className="p-4 sm:p-5 rounded-2xl bg-blue-50/60 border border-blue-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="space-y-0.5">
            <h4 className="text-xs font-black text-slate-900 flex items-center gap-2">
              <span>Razorpay Verified Indian Payment Gateway</span>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                ₹0 Platform Fee
              </span>
            </h4>
            <p className="text-[11px] text-slate-500">
              Zero platform setup fee. Supports UPI (Google Pay, PhonePe, Paytm), RuPay, Visa, Mastercard, and 50+ NetBanking options with 256-bit encryption.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 text-slate-600 font-bold text-[11px]">
          <span className="px-2.5 py-1 rounded-lg bg-white border border-blue-200 shadow-2xs">
            UPI Autopay Ready
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-white border border-blue-200 shadow-2xs">
            Sandbox Simulated
          </span>
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
            <span className="font-bold text-slate-800">What payment methods are supported?</span>
            <p className="text-slate-500 leading-relaxed">
              We process Indian domestic payments via Razorpay: UPI QR code, UPI ID (GPay/PhonePe), NetBanking across all major banks, and Debit/Credit cards.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
