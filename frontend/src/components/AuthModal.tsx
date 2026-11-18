"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/authContext";
import { Mail, Key, ShieldCheck, X, ArrowRight } from "lucide-react";

export function AuthModal() {
  const { isAuthModalOpen, setIsAuthModalOpen, login, loginWithGoogle } = useAuth();
  const [authMode, setAuthMode] = useState<"default" | "google_verify">("default");
  const [email, setEmail] = useState("");
  const [googleEmail, setGoogleEmail] = useState("");
  const [passcode, setPasscode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      const res = await login(email, passcode);
      if (!res.success) {
        setErrorMsg(res.error || "Login failed");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleVerify = async (targetEmail: string) => {
    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      const res = await loginWithGoogle(targetEmail);
      if (!res.success) {
        setErrorMsg(res.error || "Google authentication failed");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const triggerGoogleFlow = () => {
    setErrorMsg(null);
    const candidateEmail = (googleEmail || email).trim();
    if (candidateEmail && candidateEmail.includes("@")) {
      handleGoogleVerify(candidateEmail);
    } else {
      setGoogleEmail(candidateEmail);
      setAuthMode("google_verify");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl relative space-y-6">
        {/* Close Button */}
        <button
          onClick={() => {
            setIsAuthModalOpen(false);
            setAuthMode("default");
            setErrorMsg(null);
          }}
          className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="space-y-2 text-center">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 text-white font-black flex items-center justify-center text-base mx-auto shadow-md tracking-tight">
            <span>D</span><span className="text-blue-400 text-sm leading-none -ml-0.5">•</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              Sign In to DealOS
            </h2>
            <span className="text-[10px] font-extrabold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full uppercase tracking-wider">
              Jobs
            </span>
          </div>
          <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
            Executive Career Platform &amp; ATS Tracker. Sign in to access your private profile, tailored resumes, and application pipeline.
          </p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs font-semibold">
            {errorMsg}
          </div>
        )}

        {authMode === "google_verify" ? (
          /* Google Email Verification Flow (Passwordless) */
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-100 text-left space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-900">
                <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Google Account Email Verification</span>
              </div>
              <p className="text-[11px] text-blue-700/90 leading-relaxed">
                Confirm your Google email to authenticate directly. No password required.
              </p>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleGoogleVerify(googleEmail);
              }}
              className="space-y-3"
            >
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Your Google Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    autoFocus
                    value={googleEmail}
                    onChange={(e) => setGoogleEmail(e.target.value)}
                    placeholder="name@gmail.com or workspace email"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md hover:shadow-lg transition-all disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? "Verifying..." : "Verify & Sign In with Google"}
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode("default");
                  setErrorMsg(null);
                }}
                className="w-full py-2 text-center text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
              >
                ← Back to standard password login
              </button>
            </form>
          </div>
        ) : (
          /* Default Mode with Google Button and Password Fallback */
          <div className="space-y-4">
            {/* Primary Google Auth Button */}
            <button
              type="button"
              onClick={triggerGoogleFlow}
              className="w-full py-3 px-4 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs shadow-xs hover:shadow-sm transition-all flex items-center justify-center gap-3 cursor-pointer group"
            >
              <svg className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Sign in with Google</span>
              <span className="text-[10px] font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full ml-auto">
                No Password
              </span>
            </button>

            {/* Divider */}
            <div className="relative flex items-center py-1">
              <div className="flex-grow border-t border-slate-200"></div>
              <span className="flex-shrink mx-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                or sign in with password
              </span>
              <div className="flex-grow border-t border-slate-200"></div>
            </div>

            {/* Email & Passcode Form */}
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setGoogleEmail(e.target.value);
                    }}
                    placeholder="name@dealos.in"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                    Password
                  </label>
                  <span className="text-[10px] text-slate-400">Min 6 characters</span>
                </div>
                <div className="relative">
                  <Key className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={passcode}
                    onChange={(e) => setPasscode(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md hover:shadow-lg transition-all disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? "Signing in..." : "Sign In with Password"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>
        )}

        {/* Security Assurance */}
        <div className="pt-2 border-t border-slate-100 flex items-center justify-center gap-2 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Encrypted Session · Isolated Dedicated Database</span>
        </div>
      </div>
    </div>
  );
}
