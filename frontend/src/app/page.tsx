"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Immediate programmatic redirect to /dashboard
    router.replace("/dashboard");
  }, [router]);

  return (
    <>
      <head>
        <meta httpEquiv="refresh" content="0; url=/dashboard" />
      </head>
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900 font-sans">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-slate-700 text-white font-black flex items-center justify-center text-lg shadow-xl tracking-tight">
            <span>D</span><span className="text-blue-400 text-base leading-none -ml-0.5">•</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-center gap-2">
              <span className="text-lg font-black text-white tracking-tight">DealOS</span>
              <span className="text-[10px] font-extrabold bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full uppercase tracking-wider">
                Jobs
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Loading Career Operating System...</p>
          </div>
          <div className="w-24 h-1 bg-slate-800 rounded-full overflow-hidden mt-2">
            <div className="w-full h-full bg-blue-500 rounded-full animate-pulse" />
          </div>
        </div>
      </div>
    </>
  );
}
