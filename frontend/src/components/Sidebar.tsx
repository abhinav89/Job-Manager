"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useDispatch } from "react-redux";
import {
  LayoutDashboard,
  Search,
  Kanban,
  FileText,
  User,
  Settings,
  Bot,
  BarChart3,
  MessageSquare,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  ShieldCheck,
  Wand2,
  Mail,
  LogIn,
  LogOut,
} from "lucide-react";
import { useWorkspace, useProfile, useTrackerJobs } from "@/lib/queries";
import { useAuth } from "@/lib/authContext";
import { setExpandedJob } from "@/lib/store";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useDispatch();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const { user, isAuthenticated, logout, setIsAuthModalOpen } = useAuth();
  const { data: workspace } = useWorkspace();
  const { data: profile } = useProfile();
  const { data: trackerJobs = [] } = useTrackerJobs(false);

  const userName = isAuthenticated
    ? (user?.name || (profile?.first_name ? `${profile.first_name} ${profile.last_name || ""}`.trim() : "User"))
    : "Guest";
  const userEmail = isAuthenticated
    ? (user?.email || profile?.email || workspace?.email || "")
    : "Sign in to access";
  const avatarLetter = isAuthenticated && userName ? userName[0].toUpperCase() : "G";

  const closeMobile = () => setMobileOpen(false);

  const isActive = (href: string) => {
    if (href.includes("?")) {
      const [path] = href.split("?");
      if (pathname !== path) return false;
      return true;
    }
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname === href || pathname.startsWith(href + "/");
  };

  const navItems = [
    { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard className="w-4 h-4" /> },
    { label: "Find Jobs", href: "/discover", icon: <Search className="w-4 h-4" />, badge: "24 new" },
    { label: "Job Tracker", href: "/tracker", icon: <Kanban className="w-4 h-4" />, count: trackerJobs.length },
    { label: "My Resumes", href: "/generate?tab=original", icon: <FileText className="w-4 h-4" /> },
  ];

  const toolItems = [
    { label: "Job Tailor", href: "/generate?tab=tailored", icon: <Wand2 className="w-4 h-4" /> },
    { label: "Cover Letter", href: "/generate?tab=cover_letter", icon: <Mail className="w-4 h-4" /> },
    { label: "Career Profile", href: "/profile", icon: <User className="w-4 h-4" /> },
    { label: "Interview Prep", href: "#", icon: <MessageSquare className="w-4 h-4" />, badge: "Upcoming", isFuture: true },
    { label: "Career Agent", href: "#", icon: <Bot className="w-4 h-4" />, badge: "Upcoming", isFuture: true },
    { label: "Settings", href: "/settings", icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <>
      {/* ── Mobile Top Bar ── */}
      <div className="flex md:hidden items-center justify-between h-14 px-4 bg-white border-b border-slate-200 shrink-0 z-40">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-1.5 rounded-lg text-slate-700 hover:bg-slate-100"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="w-7 h-7 rounded-xl bg-blue-600 text-white font-black flex items-center justify-center text-xs shadow-xs">
            JM
          </div>
          <span className="font-extrabold text-sm text-slate-900 tracking-tight">Job-Manager</span>
        </div>

        {isAuthenticated ? (
          <button
            type="button"
            onClick={() => logout()}
            className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs"
            title="Log Out"
          >
            {avatarLetter}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setIsAuthModalOpen(true)}
            className="px-2.5 py-1 rounded-lg bg-blue-600 text-white font-bold text-xs"
          >
            Sign In
          </button>
        )}
      </div>

      {/* ── Mobile Backdrop ── */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* ── Sidebar Desktop / Slide Drawer ── */}
      <aside
        className={`fixed md:static top-0 bottom-0 left-0 z-50 md:z-10 flex flex-col h-screen shrink-0 bg-white border-r border-slate-200 shadow-sm transition-all duration-300 ease-in-out font-sans ${
          mobileOpen ? "translate-x-0 w-64" : "-translate-x-full md:translate-x-0"
        } ${collapsed ? "md:w-16" : "md:w-60"}`}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between px-4 h-16 border-b border-slate-100 shrink-0">
          {!collapsed && (
            <Link href="/dashboard" prefetch onClick={closeMobile} className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-xl bg-blue-600 text-white font-black flex items-center justify-center text-sm shadow-xs shrink-0">
                JM
              </div>
              <div className="min-w-0">
                <span className="font-extrabold text-sm text-slate-900 tracking-tight block truncate">
                  Job-Manager
                </span>
                <span className="text-[10px] text-slate-400 font-medium block">Executive Search</span>
              </div>
            </Link>
          )}

          {collapsed && (
            <div className="w-8 h-8 rounded-xl bg-blue-600 text-white font-black flex items-center justify-center text-sm shadow-xs mx-auto">
              JM
            </div>
          )}

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation List */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {/* Main Links */}
          <div className="space-y-1">
            {!collapsed && (
              <span className="px-3 text-[10px] font-bold tracking-wider uppercase text-slate-400 block mb-2">
                Main
              </span>
            )}
            {navItems.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  prefetch
                  onClick={closeMobile}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                    active
                      ? "bg-blue-50 text-blue-700 font-bold shadow-2xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  } ${collapsed ? "justify-center" : ""}`}
                  title={collapsed ? item.label : undefined}
                >
                  <span className={`${active ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"}`}>
                    {item.icon}
                  </span>
                  {!collapsed && (
                    <span className="flex-1 truncate">{item.label}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span className="text-[10px] font-extrabold bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                  {!collapsed && item.count !== undefined && item.count > 0 && (
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-full">
                      {item.count}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Tools Links */}
          <div className="space-y-1 pt-2 border-t border-slate-100">
            {!collapsed && (
              <span className="px-3 text-[10px] font-bold tracking-wider uppercase text-slate-400 block mb-2">
                Tools
              </span>
            )}
            {toolItems.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  prefetch
                  onClick={(e) => {
                    if (item.isFuture) {
                      e.preventDefault();
                      toast.info(`${item.label} is scheduled for future release.`);
                      return;
                    }
                    closeMobile();
                  }}
                  className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all group ${
                    active
                      ? "bg-blue-50 text-blue-700 font-bold"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  } ${collapsed ? "justify-center" : ""}`}
                  title={collapsed ? item.label : undefined}
                >
                  <span className={`${active ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"}`}>
                    {item.icon}
                  </span>
                  {!collapsed && (
                    <span className="flex-1 truncate">{item.label}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span className="text-[9px] font-bold uppercase bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* User Account / Tier Footer */}
        <div className="p-3 border-t border-slate-100 shrink-0 space-y-2">
          {!collapsed ? (
            isAuthenticated ? (
              <div className="p-2 rounded-xl bg-slate-50 flex items-center justify-between gap-2.5">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-2xs">
                    {avatarLetter}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-slate-900 truncate">{userName}</div>
                    <div className="text-[10px] text-slate-500 truncate">{userEmail}</div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => logout()}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                  title="Log Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAuthModalOpen(true)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all"
              >
                <LogIn className="w-4 h-4" />
                Sign In
              </button>
            )
          ) : (
            isAuthenticated ? (
              <button
                type="button"
                onClick={() => logout()}
                className="w-full flex justify-center p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                title={`Logged in as ${userName}. Click to Log Out.`}
              >
                <LogOut className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setIsAuthModalOpen(true)}
                className="w-full flex justify-center p-1.5 rounded-lg text-blue-600 hover:bg-blue-50 transition-colors"
                title="Sign In"
              >
                <LogIn className="w-4 h-4" />
              </button>
            )
          )}
        </div>
      </aside>
    </>
  );
}
