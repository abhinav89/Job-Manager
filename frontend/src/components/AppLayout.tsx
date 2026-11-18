"use client";
import { Suspense } from "react";
import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import AgentHandoff from "@/components/AgentHandoff";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showHandoff = pathname === "/assistant" || pathname === "/code";

  return (
    <div className="flex flex-col md:flex-row h-screen min-w-0 overflow-hidden bg-slate-50">
      <Suspense fallback={<aside className="hidden md:flex w-60 h-screen bg-white border-r border-slate-200" />}>
        <Sidebar />
      </Suspense>
      <div className="flex flex-1 min-w-0 min-h-0 flex-col">
        {showHandoff && <AgentHandoff />}
        <main className="flex-1 min-h-0 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
