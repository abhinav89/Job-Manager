"use client";
import Sidebar from "@/components/Sidebar";
import AgentHandoff from "@/components/AgentHandoff";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col md:flex-row h-screen min-w-0 overflow-hidden" style={{ background: "#f5f2ed" }}>
      <Sidebar />
      <div className="flex flex-1 min-w-0 min-h-0 flex-col">
        <AgentHandoff />
        <main className="flex-1 min-h-0 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
