"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  KanbanSquare,
  Search,
  MessageSquare,
  Code2,
  Sparkles,
  Terminal,
  ShieldCheck,
  GitBranch,
  Star,
  Copy,
  Check,
  ExternalLink,
  Layers,
  Cpu,
  Database,
  Lock,
  Globe,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  Sliders,
  ArrowUpRight,
} from "lucide-react";

const GITHUB_URL = "https://github.com/yabswannalearn/CV-Tailor";
const GITHUB_ISSUES_URL = "https://github.com/yabswannalearn/CV-Tailor/issues";

const GRAIN = `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`;

const C = {
  bg: "#0b0f0d",
  bgElevated: "#111714",
  card: "#141c18",
  cardHover: "#19231e",
  terminal: "#080b09",
  ink: "#f2f5f3",
  sub: "#9ca8a1",
  muted: "#68756e",
  border: "#222e28",
  borderSubtle: "#1a241f",
  mint: "#6ee7b7",
  mintDim: "rgba(110, 231, 183, 0.12)",
  mintBorder: "rgba(110, 231, 183, 0.28)",
  amber: "#fbbf24",
};

type PreviewTab = "studio" | "agent" | "tracker";
type SetupTab = "docker" | "manual";

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "Add your profile & confirm skills",
    summary:
      "Import an existing resume PDF or enter your history once. Pick a role preset (Software Developer, Virtual Assistant, Data Analyst, Customer Support, Finance, or Sales) and explicitly confirm which skills you possess.",
    detail: "Unconfirmed preset skills are never claimed as personal evidence.",
    badge: "Personal Evidence Boundary",
  },
  {
    step: "02",
    title: "Supply a job or discover remote roles",
    summary:
      "Paste a job description, extract a posting from a URL, or search across 9 remote job boards. Run an evidence-based Job Fit Analysis to inspect supported requirements, questions to clarify, and practical constraints.",
    detail: "No arbitrary match percentages or black-box ATS scores.",
    badge: "Job Intake & Fit Analysis",
  },
  {
    step: "03",
    title: "Generate, spot-edit & verify",
    summary:
      "The AI returns plain-text structured sections—never raw LaTeX. A second verification pass checks every personal claim against your confirmed profile before Python deterministically assembles the LaTeX source.",
    detail: "Highlight any lines in the PDF preview for targeted Spot Edits that preserve the 1-page budget and block invented numbers.",
    badge: "Deterministic LaTeX + Claim Guard",
  },
  {
    step: "04",
    title: "Compile via Tectonic, track & rehearse",
    summary:
      "Tectonic compiles a one-page PDF and runs a post-compile ATS check on selectable text and section order. Link the versioned CV, cover letter, and interview cheat sheet to your application tracker.",
    detail: "Practice role-specific behavioral, technical, and Python coding questions.",
    badge: "Tectonic PDF + Application CRM",
  },
];

const FEATURES = [
  {
    icon: FileText,
    tag: "Tectonic + LaTeX",
    title: "Deterministic One-Page PDFs",
    body: "AI never writes raw LaTeX markup. It outputs structured plain text that Python escapes and compiles through Tectonic with single-page auto-fit and post-compile pypdf ATS validation.",
  },
  {
    icon: Sliders,
    tag: "Block-Level Precision",
    title: "Grounded Spot Edits & 3-Mode Editor",
    body: "Switch seamlessly between structured form fields, live PDF preview, and raw LaTeX. Select text in the PDF to rewrite only that block—guarded by regex checks that reject invented metrics.",
  },
  {
    icon: Sparkles,
    tag: "Google ADK + Gemini",
    title: "Multi-Agent Career Assistant",
    body: "Persistent general and application-linked chats with live tool activity streaming, Google Search grounded company research with cited URLs, and versioned resume, cover letter, and cheat-sheet drafts.",
  },
  {
    icon: ShieldCheck,
    tag: "Evidence-Based",
    title: "No-Score Job Fit & Claim Verification",
    body: "Evaluates each job requirement as supported, needing clarification, or a known gap using only your confirmed profile and conversation evidence—never fabricating skills or fake ATS percentages.",
  },
  {
    icon: KanbanSquare,
    tag: "Local-First Workflow",
    title: "Application Tracker & 9-Source Discovery",
    body: "Manage applications from Saved to Offer with archiving, source tracking, and reviewable Career Agent tracker proposals. Discover remote roles across OnlineJobs.ph, RemoteOK, WeWorkRemotely, Arbeitnow, and more.",
  },
  {
    icon: MessageSquare,
    tag: "Preparation Suite",
    title: "Interview & Python Coding Practice",
    body: "Rehearse 10-question behavioral and technical interviews with STAR feedback and optional MediaPipe webcam delivery metrics, or solve role-tailored Python problems in a built-in Monaco workspace.",
  },
];

const DOCKER_COMMANDS = `# 1. Clone the open-source repository
git clone https://github.com/yabswannalearn/CV-Tailor.git
cd CV-Tailor

# 2. Configure your local environment & API key
cp ai-service/.env.example .env
# Edit .env and set GEMINI_API_KEY (or OPENAI_API_KEY) + SESSION_SECRET

# 3. Start PostgreSQL, FastAPI + Tectonic backend, and Next.js frontend
docker compose up --build

# App runs at http://localhost:3000 (API at http://localhost:8000)`;

const MANUAL_COMMANDS = `# 1. Clone the repository
git clone https://github.com/yabswannalearn/CV-Tailor.git
cd CV-Tailor

# 2. Start the FastAPI + Tectonic backend
cd ai-service
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL, SESSION_SECRET, and GEMINI_API_KEY in .env
python migration.py
uvicorn main:app --reload --port 8000

# 3. In a second terminal, start the Next.js frontend
cd ../frontend
npm install
npm run dev`;

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-60px" }}
      variants={fadeUp}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function OpenSourceHomepage() {
  const [scrolled, setScrolled] = useState(false);
  const [previewTab, setPreviewTab] = useState<PreviewTab>("studio");
  const [setupTab, setSetupTab] = useState<SetupTab>("docker");
  const [copiedClone, setCopiedClone] = useState(false);
  const [copiedSetup, setCopiedSetup] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollTo = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const copyText = async (text: string, which: "clone" | "setup") => {
    try {
      await navigator.clipboard.writeText(text);
      if (which === "clone") {
        setCopiedClone(true);
        setTimeout(() => setCopiedClone(false), 2000);
      } else {
        setCopiedSetup(true);
        setTimeout(() => setCopiedSetup(false), 2000);
      }
    } catch {
      // ignore clipboard errors in non-secure contexts
    }
  };

  return (
    <main
      className="relative min-h-screen overflow-x-hidden font-mono selection:bg-[#6ee7b7]/20 selection:text-[#6ee7b7]"
      style={{ background: C.bg, color: C.ink }}
    >
      {/* Subtle grain texture */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.035]"
        style={{ backgroundImage: GRAIN, backgroundRepeat: "repeat", backgroundSize: "128px" }}
      />

      {/* Ambient top glow */}
      <div
        className="pointer-events-none absolute top-0 left-1/2 z-0 h-[460px] w-[900px] -translate-x-1/2 rounded-full blur-[140px]"
        style={{ background: "radial-gradient(circle, rgba(110,231,183,0.12) 0%, rgba(11,15,13,0) 70%)" }}
      />

      {/* ── Navigation ── */}
      <header
        className="fixed top-0 right-0 left-0 z-50 transition-all duration-300"
        style={{
          background: scrolled ? "rgba(11, 15, 13, 0.86)" : "transparent",
          backdropFilter: scrolled ? "blur(12px)" : "none",
          borderBottom: scrolled ? `1px solid ${C.border}` : "1px solid transparent",
        }}
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <a href="#" className="flex items-center gap-2.5">
              <div
                className="flex h-6 w-6 items-center justify-center rounded-sm border"
                style={{ background: C.mintDim, borderColor: C.mintBorder }}
              >
                <FileText size={13} style={{ color: C.mint }} />
              </div>
              <span className="text-xs font-bold tracking-[0.18em] uppercase" style={{ color: C.ink }}>
                cv_tailor
              </span>
            </a>
            <span
              className="hidden rounded-full border px-2 py-0.5 text-[10px] tracking-wider uppercase sm:inline-block"
              style={{ borderColor: C.mintBorder, background: C.mintDim, color: C.mint }}
            >
              Open Source · Self-Hosted
            </span>
          </div>

          <nav className="hidden items-center gap-7 text-[11px] tracking-[0.14em] uppercase md:flex" style={{ color: C.sub }}>
            <a href="#how-it-works" onClick={scrollTo("how-it-works")} className="transition-colors hover:text-white">
              How it works
            </a>
            <a href="#preview" onClick={scrollTo("preview")} className="transition-colors hover:text-white">
              Product preview
            </a>
            <a href="#features" onClick={scrollTo("features")} className="transition-colors hover:text-white">
              Features
            </a>
            <a href="#self-host" onClick={scrollTo("self-host")} className="transition-colors hover:text-white">
              Run it yourself
            </a>
            <a href="#open-source" onClick={scrollTo("open-source")} className="transition-colors hover:text-white">
              Open source
            </a>
          </nav>

          <div className="flex items-center gap-2.5">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-md border px-3.5 py-2 text-[11px] font-bold tracking-[0.12em] uppercase transition-all hover:border-[#6ee7b7]/60 hover:bg-[#19231e]"
              style={{ borderColor: C.border, background: C.bgElevated, color: C.ink }}
            >
              <Star size={13} style={{ color: C.amber }} fill={C.amber} />
              <span>Star on GitHub</span>
              <ArrowUpRight size={13} style={{ color: C.sub }} />
            </a>
            <a
              href="#self-host"
              onClick={scrollTo("self-host")}
              className="hidden rounded-md px-3.5 py-2 text-[11px] font-bold tracking-[0.12em] uppercase transition-opacity hover:opacity-90 sm:inline-flex"
              style={{ background: C.mint, color: "#08120d" }}
            >
              Self-Host
            </a>
          </div>
        </div>
      </header>

      {/* ── 1. Hero Section ── */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pt-32 pb-16 sm:px-8 sm:pt-40 sm:pb-24">
        <div className="mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="mb-6 inline-flex items-center gap-2.5 rounded-full border px-3.5 py-1.5"
            style={{ borderColor: C.mintBorder, background: C.mintDim }}
          >
            <GitBranch size={12} style={{ color: C.mint }} />
            <span className="text-[11px] tracking-[0.18em] uppercase" style={{ color: C.mint }}>
              Open-Source AI Resume Studio & Career Agent
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.08 }}
            className="text-4xl leading-[1.08] font-bold tracking-tight sm:text-6xl"
            style={{ fontFamily: "'Georgia', serif" }}
          >
            Tailor grounded, one-page LaTeX resumes{" "}
            <span style={{ color: C.mint }}>on your own machine.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.16 }}
            className="mx-auto mt-6 max-w-2xl text-sm leading-relaxed sm:text-base"
            style={{ color: C.sub }}
          >
            CV Tailor pairs a deterministic Tectonic PDF compiler with a Google ADK &amp; Gemini Career Agent.
            Paste a job description, verify your fit against confirmed personal evidence, compile an ATS-checked
            one-page resume, and track every application—using your own API keys and local PostgreSQL database.
          </motion.p>

          {/* Primary CTAs: Star on GitHub + Setup Instructions */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.24 }}
            className="mt-9 flex flex-col items-center justify-center gap-3.5 sm:flex-row"
          >
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex w-full items-center justify-center gap-2.5 rounded-md px-6 py-3.5 text-xs font-bold tracking-[0.14em] uppercase transition-all hover:opacity-95 sm:w-auto"
              style={{ background: C.mint, color: "#07120d" }}
            >
              <Star size={15} fill="#07120d" />
              <span>Star on GitHub</span>
              <span className="rounded bg-black/15 px-2 py-0.5 font-mono text-[10px] tracking-normal">
                yabswannalearn/CV-Tailor
              </span>
              <ExternalLink size={13} className="transition-transform group-hover:translate-x-0.5" />
            </a>

            <a
              href="#self-host"
              onClick={scrollTo("self-host")}
              className="flex w-full items-center justify-center gap-2 rounded-md border px-6 py-3.5 text-xs font-bold tracking-[0.14em] uppercase transition-colors hover:border-[#6ee7b7]/50 hover:bg-[#141c18] sm:w-auto"
              style={{ borderColor: C.border, background: C.bgElevated, color: C.ink }}
            >
              <Terminal size={14} style={{ color: C.mint }} />
              <span>Self-Host Setup</span>
            </a>

            <a
              href="#how-it-works"
              onClick={scrollTo("how-it-works")}
              className="flex w-full items-center justify-center gap-2 rounded-md border px-5 py-3.5 text-xs font-bold tracking-[0.14em] uppercase transition-colors hover:text-white sm:w-auto"
              style={{ borderColor: "transparent", color: C.sub }}
            >
              <span>How It Works ↓</span>
            </a>
          </motion.div>

          {/* Quick git clone pill */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.55, delay: 0.32 }}
            className="mx-auto mt-6 flex max-w-xl items-center justify-between gap-3 rounded-lg border px-4 py-2.5 text-left text-xs"
            style={{ borderColor: C.border, background: C.terminal }}
          >
            <div className="flex min-w-0 items-center gap-2.5 overflow-x-auto whitespace-nowrap">
              <span style={{ color: C.mint }}>$</span>
              <code className="text-[11px] sm:text-xs" style={{ color: C.sub }}>
                git clone https://github.com/yabswannalearn/CV-Tailor.git
              </code>
            </div>
            <button
              type="button"
              onClick={() => void copyText("git clone https://github.com/yabswannalearn/CV-Tailor.git", "clone")}
              className="inline-flex shrink-0 items-center gap-1.5 rounded border px-2.5 py-1 text-[10px] uppercase tracking-wider transition-colors hover:border-[#6ee7b7]/50"
              style={{ borderColor: C.border, background: C.bgElevated, color: C.ink }}
              aria-label="Copy git clone command"
            >
              {copiedClone ? <Check size={12} style={{ color: C.mint }} /> : <Copy size={12} />}
              <span>{copiedClone ? "Copied" : "Copy"}</span>
            </button>
          </motion.div>
        </div>

        {/* ── 2. Interactive Product Preview (Example Data Only) ── */}
        <motion.div
          id="preview"
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, delay: 0.3 }}
          className="mt-14 scroll-mt-24 rounded-xl border shadow-2xl overflow-hidden"
          style={{ borderColor: C.border, background: C.bgElevated }}
        >
          {/* Browser / App Window Header */}
          <div
            className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3 sm:px-6"
            style={{ borderColor: C.border, background: C.terminal }}
          >
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#ef4444]/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#10b981]/70" />
              <span className="ml-2 text-[11px]" style={{ color: C.muted }}>
                localhost:3000 — Interactive Product Preview (Example Data)
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              {(
                [
                  { id: "studio", label: "1. Resume Studio & Spot Edit" },
                  { id: "agent", label: "2. ADK Career Agent & Fit Analysis" },
                  { id: "tracker", label: "3. Application Tracker & Prep" },
                ] as { id: PreviewTab; label: string }[]
              ).map(tab => {
                const active = previewTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setPreviewTab(tab.id)}
                    className="rounded-md px-3 py-1.5 text-[11px] font-bold tracking-wider uppercase transition-all"
                    style={{
                      background: active ? C.mintDim : "transparent",
                      color: active ? C.mint : C.sub,
                      border: active ? `1px solid ${C.mintBorder}` : "1px solid transparent",
                    }}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab 1: Resume Studio & Spot Edit */}
          {previewTab === "studio" && (
            <div className="grid grid-cols-1 lg:grid-cols-12">
              {/* Left pane: Editor + Spot Edit */}
              <div className="border-b p-5 sm:p-6 lg:col-span-5 lg:border-r lg:border-b-0" style={{ borderColor: C.border }}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] tracking-[0.2em] uppercase" style={{ color: C.mint }}>
                    Three-Mode Editor · Spot Edit
                  </span>
                  <div className="flex items-center gap-1 rounded border p-0.5 text-[10px]" style={{ borderColor: C.border, background: C.terminal }}>
                    <span className="rounded px-2 py-0.5" style={{ background: C.card, color: C.ink }}>Form</span>
                    <span className="px-2 py-0.5" style={{ color: C.muted }}>PDF</span>
                    <span className="px-2 py-0.5" style={{ color: C.muted }}>LaTeX</span>
                  </div>
                </div>

                <div className="mt-4 rounded-lg border p-3.5" style={{ borderColor: C.borderSubtle, background: C.terminal }}>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold" style={{ color: C.ink }}>Target Role Preset</span>
                    <span className="rounded px-2 py-0.5 text-[10px]" style={{ background: C.mintDim, color: C.mint }}>
                      software-developer · modern
                    </span>
                  </div>
                  <p className="mt-1.5 text-[11px] leading-relaxed" style={{ color: C.sub }}>
                    Job: Senior Backend Engineer at Acme Cloud (Python, FastAPI, PostgreSQL, Distributed Systems)
                  </p>
                </div>

                <div className="mt-4 rounded-lg border p-4" style={{ borderColor: C.mintBorder, background: C.card }}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold tracking-wider uppercase" style={{ color: C.mint }}>
                      Selected PDF Block · Experience Bullet #2
                    </span>
                    <span className="text-[10px]" style={{ color: C.muted }}>Budget: 118 / 135 chars</span>
                  </div>
                  <p className="mt-2 rounded border p-2.5 text-xs leading-relaxed" style={{ borderColor: C.border, background: C.terminal, color: C.sub }}>
                    &ldquo;Built internal deployment tooling and migrated services to PostgreSQL with zero downtime.&rdquo;
                  </p>
                  <div className="mt-3">
                    <div className="text-[10px] uppercase tracking-wider" style={{ color: C.sub }}>
                      Spot-Edit Instruction
                    </div>
                    <div className="mt-1 flex items-center justify-between rounded border px-3 py-2 text-xs" style={{ borderColor: C.border, background: C.terminal, color: C.ink }}>
                      <span>Emphasize FastAPI service reliability using confirmed profile metrics only.</span>
                    </div>
                  </div>
                  <div className="mt-3 flex items-start gap-2 rounded border p-2.5 text-[11px]" style={{ borderColor: C.mintBorder, background: C.mintDim, color: C.ink }}>
                    <ShieldCheck size={15} className="mt-0.5 shrink-0" style={{ color: C.mint }} />
                    <div>
                      <strong style={{ color: C.mint }}>Grounded Rewrite Ready:</strong> Uses confirmed profile fact (14 microservices, 99.95% uptime). No unverified numbers introduced.
                    </div>
                  </div>
                </div>
              </div>

              {/* Right pane: Deterministic Tectonic PDF Output */}
              <div className="p-5 sm:p-6 lg:col-span-7" style={{ background: C.terminal }}>
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold" style={{ color: C.ink }}>alex_rivera_resume.pdf</span>
                    <span className="rounded border px-2 py-0.5 text-[10px]" style={{ borderColor: C.border, color: C.sub }}>
                      1 / 1 Page (Auto-Fit Verified)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase"
                      style={{ borderColor: C.mintBorder, background: C.mintDim, color: C.mint }}
                    >
                      <CheckCircle2 size={11} />
                      ATS Check: PASS (Selectable · Section Order)
                    </span>
                  </div>
                </div>

                {/* Simulated crisp 1-page LaTeX document */}
                <div className="rounded-lg border bg-[#fcfbf9] p-5 text-[#18181b] shadow-inner sm:p-6" style={{ borderColor: C.border }}>
                  <div className="border-b border-zinc-300 pb-3">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <h3 className="font-serif text-lg font-bold tracking-tight text-zinc-900">ALEX RIVERA</h3>
                      <span className="font-mono text-[10px] text-zinc-600">
                        alex.rivera@example.com · github.com/arivera-dev · Remote
                      </span>
                    </div>
                    <p className="mt-1.5 text-[11px] leading-relaxed text-zinc-700">
                      Backend Engineer with 4+ years building Python and FastAPI microservices, relational data pipelines in PostgreSQL, and automated CI/CD workflows.
                    </p>
                  </div>

                  <div className="mt-3">
                    <div className="text-[10px] font-bold tracking-[0.15em] text-zinc-800 uppercase">Experience</div>
                    <div className="mt-1 flex justify-between text-[11px] font-bold text-zinc-900">
                      <span>Platform Engineer · Northwind Systems</span>
                      <span className="font-mono text-[10px] font-normal text-zinc-600">2023 — Present</span>
                    </div>
                    <ul className="mt-1 list-disc space-y-1 pl-4 text-[11px] leading-snug text-zinc-700">
                      <li>Designed async FastAPI ingestion endpoints handling 1,200 req/sec backed by PostgreSQL connection pooling.</li>
                      <li className="rounded bg-emerald-100/90 px-1.5 py-0.5 text-zinc-900 ring-1 ring-emerald-500/40">
                        Standardized deployment pipelines across 14 FastAPI and PostgreSQL microservices, maintaining 99.95% uptime during schema migrations.
                      </li>
                      <li>Cut p95 query latency by 38% by indexing high-cardinality audit tables and eliminating N+1 ORM lookups.</li>
                    </ul>
                  </div>

                  <div className="mt-3">
                    <div className="text-[10px] font-bold tracking-[0.15em] text-zinc-800 uppercase">Confirmed Technical Skills</div>
                    <p className="mt-1 text-[11px] text-zinc-700">
                      <span className="font-semibold text-zinc-900">Languages &amp; Frameworks:</span> Python, FastAPI, SQL, TypeScript, React ·{" "}
                      <span className="font-semibold text-zinc-900">Infrastructure:</span> PostgreSQL, Docker, Linux, GitHub Actions
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Google ADK Career Agent & Evidence-Based Job Fit */}
          {previewTab === "agent" && (
            <div className="grid grid-cols-1 lg:grid-cols-12">
              <div className="border-b p-5 sm:p-6 lg:col-span-5 lg:border-r lg:border-b-0" style={{ borderColor: C.border }}>
                <span className="text-[10px] tracking-[0.2em] uppercase" style={{ color: C.mint }}>
                  Google ADK · Application Conversation
                </span>
                <h3 className="mt-2 text-sm font-bold" style={{ color: C.ink }}>
                  Senior Backend Engineer · Acme Cloud
                </h3>
                <p className="mt-1 text-xs leading-relaxed" style={{ color: C.sub }}>
                  The Career Agent streams live tool activity, grounds company research with Google Search citations, and never applies tracker or document changes without your confirmation.
                </p>

                <div className="mt-4 space-y-2 rounded-lg border p-3.5 text-[11px]" style={{ borderColor: C.border, background: C.terminal }}>
                  <div className="font-bold uppercase tracking-wider" style={{ color: C.sub }}>
                    Live Agent Activity Stream (NDJSON)
                  </div>
                  <div className="flex items-center gap-2" style={{ color: C.mint }}>
                    <CheckCircle2 size={13} />
                    <span>research_company · 4 web sources verified via Google Search</span>
                  </div>
                  <div className="flex items-center gap-2" style={{ color: C.mint }}>
                    <CheckCircle2 size={13} />
                    <span>analyze_job_fit · Compared JD against Confirmed Skills</span>
                  </div>
                  <div className="flex items-center gap-2" style={{ color: C.mint }}>
                    <CheckCircle2 size={13} />
                    <span>propose_application_change · Saved reviewable tracker proposal</span>
                  </div>
                </div>

                <div className="mt-4 rounded-lg border p-3.5 text-xs" style={{ borderColor: C.mintBorder, background: C.mintDim }}>
                  <div className="font-bold" style={{ color: C.mint }}>Tracker Proposal (Awaiting Confirmation)</div>
                  <p className="mt-1 text-[11px]" style={{ color: C.ink }}>
                    Update status for <strong>Senior Backend Engineer at Acme Cloud</strong> to <code>Interview</code> and record source as <code>Arbeitnow</code>.
                  </p>
                  <div className="mt-2.5 flex gap-2">
                    <span className="rounded px-2.5 py-1 text-[10px] font-bold uppercase" style={{ background: C.mint, color: "#07120d" }}>
                      Confirm tracker change
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-5 sm:p-6 lg:col-span-7" style={{ background: C.terminal }}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider" style={{ color: C.ink }}>
                    Evidence-Based Job Fit Analysis (No Numerical Score)
                  </span>
                  <span className="rounded border px-2 py-0.5 text-[10px]" style={{ borderColor: C.border, color: C.sub }}>
                    Draft v1 · Saved to Conversation
                  </span>
                </div>

                <div className="mt-3 space-y-3">
                  <div className="rounded-lg border p-3.5" style={{ borderColor: C.border, background: C.card }}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold" style={{ color: C.ink }}>
                        &ldquo;4+ years production Python &amp; FastAPI experience&rdquo;
                      </span>
                      <span className="rounded px-2 py-0.5 text-[10px] font-bold uppercase" style={{ background: C.mintDim, color: C.mint }}>
                        Required · Supported
                      </span>
                    </div>
                    <p className="mt-1.5 text-[11px]" style={{ color: C.sub }}>
                      <strong>Personal Evidence:</strong> Confirmed profile lists 4+ years building Python &amp; FastAPI services at Northwind Systems (1,200 req/sec ingestion API).
                    </p>
                  </div>

                  <div className="rounded-lg border p-3.5" style={{ borderColor: C.border, background: C.card }}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold" style={{ color: C.ink }}>
                        &ldquo;Experience operating Kafka event streams&rdquo;
                      </span>
                      <span className="rounded bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold text-amber-300 uppercase">
                        Preferred · Needs Clarification
                      </span>
                    </div>
                    <p className="mt-1.5 text-[11px]" style={{ color: C.sub }}>
                      <strong>Assessment:</strong> Missing from saved profile is not assumed to be a gap. Have you worked with Kafka or similar message brokers in any role or project?
                    </p>
                  </div>

                  <div className="rounded-lg border p-3.5" style={{ borderColor: C.border, background: C.card }}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold" style={{ color: C.ink }}>
                        Practical Constraints (Location, Hours &amp; Compensation)
                      </span>
                      <span className="rounded border px-2 py-0.5 text-[10px]" style={{ borderColor: C.border, color: C.sub }}>
                        Separately Evaluated
                      </span>
                    </div>
                    <p className="mt-1.5 text-[11px]" style={{ color: C.sub }}>
                      Remote (UTC-5 to UTC+1 overlap required). Salary listed at $130k–$150k; compatible with saved remote preference.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Application Tracker & Interview Prep */}
          {previewTab === "tracker" && (
            <div className="grid grid-cols-1 gap-4 p-5 sm:p-6 lg:grid-cols-3" style={{ background: C.terminal }}>
              {[
                {
                  status: "Saved",
                  role: "Data Engineer",
                  company: "Vanguard Analytics",
                  source: "Found via WeWorkRemotely",
                  badges: ["Job Fit Analyzed", "Remote"],
                },
                {
                  status: "Interview",
                  role: "Senior Backend Engineer",
                  company: "Acme Cloud",
                  source: "Found via Arbeitnow",
                  badges: ["1-Page PDF Attached", "Cover Letter v2", "Cheat Sheet PDF"],
                },
                {
                  status: "Offer",
                  role: "Full-Stack Python Developer",
                  company: "Helios Labs",
                  source: "Found via Direct Referral",
                  badges: ["Offer-Linked Evidence Source", "STAR Practice Complete"],
                },
              ].map(card => (
                <div key={card.company} className="rounded-lg border p-4" style={{ borderColor: C.border, background: C.card }}>
                  <div className="flex items-center justify-between">
                    <span className="rounded px-2 py-0.5 text-[10px] font-bold uppercase" style={{ background: C.mintDim, color: C.mint }}>
                      {card.status}
                    </span>
                    <span className="text-[10px]" style={{ color: C.muted }}>{card.source}</span>
                  </div>
                  <h4 className="mt-3 text-sm font-bold" style={{ color: C.ink }}>{card.role}</h4>
                  <p className="text-xs" style={{ color: C.sub }}>{card.company}</p>
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {card.badges.map(b => (
                      <span
                        key={b}
                        className="rounded border px-2 py-0.5 text-[10px]"
                        style={{ borderColor: C.border, background: C.terminal, color: C.sub }}
                      >
                        {b}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </section>

      {/* ── 3. How It Works (Workflow + Architecture Pipeline) ── */}
      <section id="how-it-works" className="relative z-10 mx-auto max-w-6xl scroll-mt-20 px-5 py-20 sm:px-8 sm:py-28">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-[11px] tracking-[0.25em] uppercase" style={{ color: C.mint }}>
            How It Works
          </span>
          <h2
            className="mt-3 text-3xl font-bold sm:text-4xl"
            style={{ fontFamily: "'Georgia', serif", letterSpacing: "-0.02em" }}
          >
            From raw profile to verified one-page PDF—without hallucinated claims.
          </h2>
          <p className="mt-4 text-sm leading-relaxed" style={{ color: C.sub }}>
            Most AI resume builders let LLMs invent metrics or break formatting. CV Tailor separates personal evidence
            verification from deterministic LaTeX compilation.
          </p>
        </Reveal>

        {/* 4-Step Workflow Grid */}
        <div className="mt-14 grid grid-cols-1 gap-5 md:grid-cols-2">
          {WORKFLOW_STEPS.map((item, idx) => (
            <Reveal key={item.step} delay={idx * 0.08}>
              <div
                className="flex h-full flex-col justify-between rounded-xl border p-6 transition-colors hover:border-[#6ee7b7]/40"
                style={{ borderColor: C.border, background: C.card }}
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold" style={{ color: C.mint }}>
                      STEP {item.step}
                    </span>
                    <span
                      className="rounded-full border px-2.5 py-0.5 text-[10px] uppercase tracking-wider"
                      style={{ borderColor: C.mintBorder, background: C.mintDim, color: C.mint }}
                    >
                      {item.badge}
                    </span>
                  </div>
                  <h3 className="mt-3 text-base font-bold" style={{ color: C.ink }}>
                    {item.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed" style={{ color: C.sub }}>
                    {item.summary}
                  </p>
                </div>
                <div
                  className="mt-4 border-t pt-3 text-[11px]"
                  style={{ borderColor: C.borderSubtle, color: C.muted }}
                >
                  ↳ {item.detail}
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        {/* Under-the-Hood Architecture Pipeline */}
        <Reveal className="mt-10">
          <div className="rounded-xl border p-6 sm:p-8" style={{ borderColor: C.border, background: C.bgElevated }}>
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
              <div>
                <span className="text-[10px] tracking-[0.2em] uppercase" style={{ color: C.mint }}>
                  System Architecture
                </span>
                <h3 className="mt-1 text-lg font-bold" style={{ color: C.ink }}>
                  Under the hood: How the local pipeline executes
                </h3>
              </div>
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs underline-offset-4 hover:underline"
                style={{ color: C.mint }}
              >
                <span>Browse architecture in repo</span>
                <ArrowUpRight size={14} />
              </a>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  icon: Database,
                  title: "1. Profile & Evidence Store",
                  code: "models/database_models.py",
                  desc: "PostgreSQL stores your profile, explicitly confirmed skills, application conversations, and versioned drafts.",
                },
                {
                  icon: Cpu,
                  title: "2. LLM Dispatcher & ADK Agent",
                  code: "services/career_agent.py",
                  desc: "Gemini (or OpenAI for standalone tailoring) selects relevant experience and runs a second pass to strip unsupported claims.",
                },
                {
                  icon: Layers,
                  title: "3. Deterministic LaTeX Assembler",
                  code: "services/latex_assembly.py",
                  desc: "Plain-text JSON is escaped and slotted into Classic or Modern LaTeX templates—AI never touches raw LaTeX syntax.",
                },
                {
                  icon: FileText,
                  title: "4. Tectonic & ATS Validator",
                  code: "services/pdf_service.py",
                  desc: "Tectonic compiles the 1-page PDF locally and pypdf verifies selectable text, section order, and conventional headings.",
                },
              ].map(node => {
                const Icon = node.icon;
                return (
                  <div
                    key={node.title}
                    className="rounded-lg border p-4"
                    style={{ borderColor: C.border, background: C.terminal }}
                  >
                    <div className="flex items-center gap-2">
                      <Icon size={15} style={{ color: C.mint }} />
                      <span className="text-xs font-bold" style={{ color: C.ink }}>{node.title}</span>
                    </div>
                    <code className="mt-1.5 block text-[10px]" style={{ color: C.mint }}>
                      {node.code}
                    </code>
                    <p className="mt-2 text-[11px] leading-relaxed" style={{ color: C.sub }}>
                      {node.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </Reveal>
      </section>

      {/* ── 4. Verified Features Grid ── */}
      <section id="features" className="relative z-10 mx-auto max-w-6xl scroll-mt-20 px-5 py-20 sm:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-[11px] tracking-[0.25em] uppercase" style={{ color: C.mint }}>
            Verified Capabilities
          </span>
          <h2
            className="mt-3 text-3xl font-bold sm:text-4xl"
            style={{ fontFamily: "'Georgia', serif", letterSpacing: "-0.02em" }}
          >
            Built for the entire job search lifecycle.
          </h2>
          <p className="mt-4 text-sm leading-relaxed" style={{ color: C.sub }}>
            Every module included in the open-source repository—no paywalled tiers or credit systems.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <Reveal key={f.title} delay={(i % 3) * 0.07}>
                <div
                  className="flex h-full flex-col justify-between rounded-xl border p-6 transition-all hover:-translate-y-0.5 hover:border-[#6ee7b7]/40"
                  style={{ borderColor: C.border, background: C.card }}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <div
                        className="flex h-9 w-9 items-center justify-center rounded-md border"
                        style={{ borderColor: C.mintBorder, background: C.mintDim }}
                      >
                        <Icon size={17} style={{ color: C.mint }} />
                      </div>
                      <span className="text-[10px] tracking-wider uppercase" style={{ color: C.muted }}>
                        {f.tag}
                      </span>
                    </div>
                    <h3 className="mt-4 text-sm font-bold tracking-wide uppercase" style={{ color: C.ink }}>
                      {f.title}
                    </h3>
                    <p className="mt-2.5 text-xs leading-relaxed" style={{ color: C.sub }}>
                      {f.body}
                    </p>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* ── 5. Run It Yourself (Self-Hosting & Prerequisites) ── */}
      <section id="self-host" className="relative z-10 mx-auto max-w-6xl scroll-mt-20 px-5 py-20 sm:px-8 sm:py-28">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-[11px] tracking-[0.25em] uppercase" style={{ color: C.mint }}>
            Run It Yourself
          </span>
          <h2
            className="mt-3 text-3xl font-bold sm:text-4xl"
            style={{ fontFamily: "'Georgia', serif", letterSpacing: "-0.02em" }}
          >
            Self-host on your machine with your own AI key.
          </h2>
          <p className="mt-4 text-sm leading-relaxed" style={{ color: C.sub }}>
            Run CV Tailor locally via Docker Compose or standard Python + Node.js tooling. Bring your own
            Google Gemini or OpenAI API key—no subscription or credit system required.
          </p>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Terminal Box */}
          <Reveal className="lg:col-span-7">
            <div className="overflow-hidden rounded-xl border" style={{ borderColor: C.border, background: C.terminal }}>
              <div
                className="flex flex-wrap items-center justify-between gap-2 border-b px-4 py-3"
                style={{ borderColor: C.border, background: C.bgElevated }}
              >
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setSetupTab("docker")}
                    className="rounded px-3 py-1 text-[11px] font-bold uppercase transition-colors"
                    style={{
                      background: setupTab === "docker" ? C.mintDim : "transparent",
                      color: setupTab === "docker" ? C.mint : C.sub,
                      border: setupTab === "docker" ? `1px solid ${C.mintBorder}` : "1px solid transparent",
                    }}
                  >
                    Docker Compose
                  </button>
                  <button
                    type="button"
                    onClick={() => setSetupTab("manual")}
                    className="rounded px-3 py-1 text-[11px] font-bold uppercase transition-colors"
                    style={{
                      background: setupTab === "manual" ? C.mintDim : "transparent",
                      color: setupTab === "manual" ? C.mint : C.sub,
                      border: setupTab === "manual" ? `1px solid ${C.mintBorder}` : "1px solid transparent",
                    }}
                  >
                    Manual (FastAPI + Next.js)
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    void copyText(setupTab === "docker" ? DOCKER_COMMANDS : MANUAL_COMMANDS, "setup")
                  }
                  className="inline-flex items-center gap-1.5 rounded border px-2.5 py-1 text-[10px] uppercase tracking-wider hover:border-[#6ee7b7]/50"
                  style={{ borderColor: C.border, background: C.card, color: C.ink }}
                >
                  {copiedSetup ? <Check size={12} style={{ color: C.mint }} /> : <Copy size={12} />}
                  <span>{copiedSetup ? "Copied" : "Copy commands"}</span>
                </button>
              </div>

              <pre className="overflow-x-auto p-5 text-xs leading-6" style={{ color: C.ink }}>
                <code>{setupTab === "docker" ? DOCKER_COMMANDS : MANUAL_COMMANDS}</code>
              </pre>
            </div>
          </Reveal>

          {/* Prerequisites & AI Provider Configuration */}
          <Reveal delay={0.1} className="lg:col-span-5">
            <div className="flex h-full flex-col justify-between rounded-xl border p-6" style={{ borderColor: C.border, background: C.card }}>
              <div>
                <h3 className="text-sm font-bold tracking-wider uppercase" style={{ color: C.ink }}>
                  Prerequisites &amp; Provider Requirements
                </h3>
                <ul className="mt-4 space-y-3 text-xs leading-relaxed" style={{ color: C.sub }}>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 size={15} className="mt-0.5 shrink-0" style={{ color: C.mint }} />
                    <span>
                      <strong style={{ color: C.ink }}>AI API Key:</strong> Set <code>GEMINI_API_KEY</code> (default) or{" "}
                      <code>AI_PROVIDER=openai</code> with <code>OPENAI_API_KEY</code> for the main tailoring dispatcher.
                    </span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <AlertCircle size={15} className="mt-0.5 shrink-0" style={{ color: C.amber }} />
                    <span>
                      <strong style={{ color: C.ink }}>Career Agent &amp; Grounded Search:</strong> The multi-agent Career Assistant (<code>google-adk</code>) and live Google Search company research specifically require a Gemini API key.
                    </span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 size={15} className="mt-0.5 shrink-0" style={{ color: C.mint }} />
                    <span>
                      <strong style={{ color: C.ink }}>Database &amp; PDF Engine:</strong> PostgreSQL 15+ and Tectonic for LaTeX compilation (automatically fetched by <code>pdf_service.py</code> on Linux if not pre-installed).
                    </span>
                  </li>
                </ul>
              </div>

              <div className="mt-6 rounded-lg border p-4 text-[11px] leading-relaxed" style={{ borderColor: C.borderSubtle, background: C.terminal, color: C.sub }}>
                <strong style={{ color: C.ink }}>Cost transparency:</strong> CV Tailor itself is free and open-source. Running AI tailoring, Spot Edits, or Career Agent research calls your configured Gemini or OpenAI account directly and may incur standard API token usage costs from your provider.
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── 6. Open Source, Privacy & GitHub CTA ── */}
      <section id="open-source" className="relative z-10 mx-auto max-w-6xl scroll-mt-20 px-5 pb-24 sm:px-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Privacy & Data Flow Transparency */}
          <Reveal>
            <div className="h-full rounded-xl border p-6 sm:p-8" style={{ borderColor: C.border, background: C.card }}>
              <div className="flex items-center gap-2">
                <Lock size={16} style={{ color: C.mint }} />
                <span className="text-[11px] font-bold tracking-[0.2em] uppercase" style={{ color: C.mint }}>
                  Privacy &amp; Data Flow
                </span>
              </div>
              <h3 className="mt-3 text-xl font-bold" style={{ fontFamily: "'Georgia', serif", color: C.ink }}>
                Know what stays on your machine—and what goes to your AI provider.
              </h3>
              <div className="mt-5 space-y-4 text-xs leading-relaxed" style={{ color: C.sub }}>
                <div>
                  <strong className="block" style={{ color: C.ink }}>✓ Stored &amp; Executed Locally</strong>
                  Your PostgreSQL database, saved profile, confirmed skills, tracked applications, versioned drafts, and Tectonic LaTeX-to-PDF compilation all run on your own computer.
                </div>
                <div>
                  <strong className="block" style={{ color: C.ink }}>↗ Sent to External Services When Invoked</strong>
                  When you generate or spot-edit a CV, draft a cover letter, run Job Fit Analysis, or chat with the Career Agent, relevant profile facts and job descriptions are sent to your configured AI provider (Google Gemini or OpenAI). Company research uses Google Search grounding via Gemini.
                </div>
                <div>
                  <strong className="block" style={{ color: C.ink }}>↗ Optional Integrations</strong>
                  Job Discovery queries public remote job boards using role keywords only. Optional TypeSafe Jev ranking sends work-related skill evidence (excluding your name, email, phone, and links). Email verification uses Resend if configured.
                </div>
              </div>
            </div>
          </Reveal>

          {/* Open Source Stack & Star on GitHub CTA */}
          <Reveal delay={0.1}>
            <div
              className="flex h-full flex-col justify-between rounded-xl border p-6 sm:p-8"
              style={{ borderColor: C.mintBorder, background: "linear-gradient(180deg, #141c18 0%, #0e1512 100%)" }}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold tracking-[0.2em] uppercase" style={{ color: C.mint }}>
                    Open-Source Repository
                  </span>
                  <span className="rounded border px-2.5 py-0.5 text-[10px]" style={{ borderColor: C.border, color: C.sub }}>
                    Next.js 16 · FastAPI · ADK · Tectonic · PostgreSQL
                  </span>
                </div>

                <h3 className="mt-3 text-2xl font-bold" style={{ fontFamily: "'Georgia', serif", color: C.ink }}>
                  Inspect the code, star the repo, or contribute.
                </h3>
                <p className="mt-3 text-xs leading-relaxed" style={{ color: C.sub }}>
                  CV Tailor is developed in the open at{" "}
                  <a
                    href={GITHUB_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline underline-offset-4"
                    style={{ color: C.mint }}
                  >
                    github.com/yabswannalearn/CV-Tailor
                  </a>
                  . Explore the deterministic LaTeX assembler, personal evidence verification passes, and Google ADK multi-agent tools—or open an issue to suggest improvements.
                </p>

                <div className="mt-6 grid grid-cols-2 gap-3 text-[11px]">
                  <div className="rounded-lg border p-3" style={{ borderColor: C.border, background: C.terminal }}>
                    <div className="font-bold" style={{ color: C.ink }}>Frontend</div>
                    <div className="mt-1" style={{ color: C.sub }}>Next.js 16, React 19, Tailwind v4, Monaco, react-pdf</div>
                  </div>
                  <div className="rounded-lg border p-3" style={{ borderColor: C.border, background: C.terminal }}>
                    <div className="font-bold" style={{ color: C.ink }}>Backend &amp; AI</div>
                    <div className="mt-1" style={{ color: C.sub }}>FastAPI, SQLAlchemy, Google ADK, Gemini / OpenAI, Tectonic</div>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex flex-1 items-center justify-center gap-2 rounded-md px-5 py-3.5 text-xs font-bold tracking-[0.14em] uppercase transition-opacity hover:opacity-95"
                  style={{ background: C.mint, color: "#07120d" }}
                >
                  <Star size={15} fill="#07120d" />
                  <span>Star yabswannalearn/CV-Tailor</span>
                  <ExternalLink size={13} />
                </a>
                <a
                  href={GITHUB_ISSUES_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 rounded-md border px-5 py-3.5 text-xs font-bold tracking-[0.14em] uppercase transition-colors hover:border-[#6ee7b7]/50"
                  style={{ borderColor: C.border, background: C.terminal, color: C.ink }}
                >
                  <BookOpen size={14} style={{ color: C.mint }} />
                  <span>Issues &amp; Contributing</span>
                </a>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="relative z-10 border-t px-5 py-10 sm:px-8" style={{ borderColor: C.border }}>
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <div
              className="flex h-5 w-5 items-center justify-center rounded-sm border"
              style={{ background: C.mintDim, borderColor: C.mintBorder }}
            >
              <FileText size={11} style={{ color: C.mint }} />
            </div>
            <span className="text-xs font-bold tracking-[0.15em] uppercase" style={{ color: C.ink }}>
              cv_tailor
            </span>
            <span className="text-[11px]" style={{ color: C.muted }}>
              · Open-Source AI Resume &amp; Career Toolkit
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs" style={{ color: C.sub }}>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 transition-colors hover:text-white"
            >
              <Globe size={13} style={{ color: C.mint }} />
              <span>GitHub Repository</span>
            </a>
            <a href="#self-host" onClick={scrollTo("self-host")} className="transition-colors hover:text-white">
              Self-Hosting Guide
            </a>
            <a href="#open-source" onClick={scrollTo("open-source")} className="transition-colors hover:text-white">
              Privacy &amp; Stack
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
