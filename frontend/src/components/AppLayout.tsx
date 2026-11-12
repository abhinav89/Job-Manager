"use client";
import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import AgentHandoff from "@/components/AgentHandoff";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showHandoff = pathname === "/assistant" || pathname === "/code";

  return (
    <div className="flex flex-col md:flex-row h-screen min-w-0 overflow-hidden bg-slate-50">
      <Sidebar />
      <div className="flex flex-1 min-w-0 min-h-0 flex-col">
        {showHandoff && <AgentHandoff />}
        <main className="flex-1 min-h-0 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
