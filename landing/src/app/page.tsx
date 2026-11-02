"use client";

import { useState, type ReactNode } from "react";
import ThemeToggle from "./theme-toggle";
import {
  ArrowRight, ArrowUpRight, Check, ChevronDown, Code2, Copy, FileText,
  FolderOpen, GitBranch, Layers, LayoutDashboard, Menu, MessageSquare,
  Search, Terminal, UserRound, X, type LucideIcon,
} from "lucide-react";

const REPO = "https://github.com/yabswannalearn/CV-Tailor";
const README = `${REPO}#readme`;
type View = "tracker" | "resume" | "interview";
type InstallMode = "cli" | "dashboard";

const skills = [
  { name: "cv-tailor", label: "Your starting point", description: "Set up your workspace and bring the whole workflow together.", prompt: "Use CV Tailor. Help me set up my profile and get ready for my next application." },
  { name: "cv-profile", label: "Profile & confirmed skills", description: "Import your CV and keep your real experience up to date.", prompt: "Import my CV into my profile. Let me review the extracted facts and confirm my skills before saving." },
  { name: "cv-jobs", label: "Job discovery", description: "Find roles and collect the details from a posting or job URL.", prompt: "Find remote roles that fit my background, then help me review the job descriptions." },
  { name: "cv-job-fit", label: "Job fit analysis", description: "See supported matches, questions, gaps, and practical constraints.", prompt: "Compare this job with my profile. Show supported matches, what needs clarification, and known gaps." },
  { name: "cv-company-research", label: "Company research", description: "Gather useful company and role context with sources.", prompt: "Research this company and role for my application. Cite the sources and distinguish facts from inference." },
  { name: "cv-resume", label: "Tailored resumes", description: "Turn confirmed experience into a tailored, one-page CV.", prompt: "Tailor my CV for this job using my confirmed experience. Save a draft, check the page count, and run the ATS check." },
  { name: "cv-resume-edit", label: "Targeted edits", description: "Rewrite one summary or selected bullets while keeping the rest.", prompt: "Make the first experience bullet more relevant to this job. Keep my facts and leave the rest of the CV unchanged." },
  { name: "cv-cover-letter", label: "Cover letters", description: "Connect your experience to the role in a letter you can review.", prompt: "Write a concise cover letter using my real experience and the company research. Save it as a draft for this application." },
  { name: "cv-tracker", label: "Application tracking", description: "Query, update, archive, and manage your application history.", prompt: "Show my applications at the interview stage, including their saved documents and next steps." },
  { name: "cv-interview", label: "Interview preparation", description: "Build prep plans, practice answers, and create cheat sheets.", prompt: "Help me prepare for this interview. Ask one practice question at a time, give feedback, and save a cheat sheet." },
  { name: "cv-code-practice", label: "Coding practice", description: "Work through Python exercises with hints, execution, and review.", prompt: "Give me a Python interview exercise for this role. Let me attempt it, offer hints when asked, and review my solution." },
];

const features: { icon: LucideIcon; title: string; description: string; detail: string }[] = [
  { icon: Search, title: "Find your next opportunity.", description: "Discover jobs, read a posting URL, and understand how a role fits your actual experience.", detail: "Job discovery · Fit analysis · Sourced research" },
  { icon: FileText, title: "Give every application its own CV.", description: "Tailor a one-page resume, refine individual bullets, and check that the PDF is readable by an ATS.", detail: "Targeted edits · PDF, LaTeX & DOCX exports" },
  { icon: MessageSquare, title: "Write with something real to say.", description: "Create cover letters that connect your experience to the role, with company research when it helps.", detail: "Confirmed facts · Reviewable drafts" },
  { icon: LayoutDashboard, title: "Keep the whole search in view.", description: "Track statuses, find past applications, and keep each role’s documents and notes together.", detail: "Search · Update · Archive · Restore" },
  { icon: UserRound, title: "Walk into interviews prepared.", description: "Build a prep plan, rehearse answers, get feedback, and keep an interview-day cheat sheet close.", detail: "Mock interviews · Saved preparation" },
  { icon: Code2, title: "Practice before the technical round.", description: "Solve Python exercises, ask for a nudge, run your code, and review correctness and complexity.", detail: "Progressive hints · Execution · Code review" },
];

const questions = [
  { title: "Is the web UI still included?", answer: "Yes. Install the optional dashboard to use the profile editor, application tracker, CV editor, interview practice, and coding practice in your browser. It runs locally and shares the same data as the CLI. You can also add it after a CLI-only installation." },
  { title: "Do I need an AI API key?", answer: "You don’t need a separate AI API key for CV Tailor’s agent workflows. Use the access you already have in your chosen CLI agent. If you want the built-in API-powered AI features, you can opt in and configure provider credentials separately." },
  { title: "Where does my work live?", answer: "Your profile, applications, and saved documents live in a local SQLite database, outside the checkout, and persist between sessions. There’s no CV Tailor account or PostgreSQL server to set up. Your chosen AI agent or provider may process the context you share with it." },
  { title: "Can I switch between agents?", answer: "Yes. Claude Code, Codex, OpenCode, and Antigravity can use the included skills and CLI commands against the same workspace. CV Tailor reloads your saved career data; each harness keeps its own chat history." },
];

function Brand() {
  return <span className="brand"><span className="brand-mark"><FileText size={20} strokeWidth={1.6} /></span><span>cv_tailor<span className="brand-dot">.</span></span></span>;
}

function ArrowLink({ children, href }: { children: ReactNode; href: string }) {
  return <a className="button button-primary" href={href}>{children}<ArrowRight size={15} /></a>;
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true); setFailed(false);
      window.setTimeout(() => setCopied(false), 2200);
    } catch { setFailed(true); }
  }
  return <div className="copy-control"><button type="button" className="copy-button" aria-label={label} onClick={() => void copy()}>{copied ? <Check size={14} /> : <Copy size={14} />}{copied ? "Copied" : "Copy"}</button><span className="sr-only" role="status">{copied ? "Copied to clipboard." : failed ? "Clipboard unavailable. Select and copy the text below." : ""}</span>{failed && <span className="copy-error">Select the text below to copy.</span>}</div>;
}

function TrackerPreview() {
  return <div className="demo-tracker">
    <div className="demo-page-heading"><div><span className="eyebrow">YOUR NEXT CHAPTER</span><h3>Job Tracker</h3></div><span className="demo-add">+ Add application</span></div>
    <div className="demo-stats"><div><strong>3</strong><span>Applications</span></div><div><strong>1</strong><span>Interview</span></div><div><strong>2</strong><span>CV drafts</span></div></div>
    <div className="demo-table-label"><span>APPLICATION</span><span>STATUS</span></div>
    <div className="demo-job"><span className="company-monogram">n</span><div><strong>Product engineer</strong><span>Northstar · Remote</span></div><span className="status status-interview">Interview</span></div>
    <div className="demo-job"><span className="company-monogram monogram-square">a</span><div><strong>Frontend developer</strong><span>Arc Studio · Remote</span></div><span className="status status-applied">Applied</span></div>
    <div className="demo-job"><span className="company-monogram">o</span><div><strong>Software engineer</strong><span>Orbit · Hybrid</span></div><span className="status status-saved">Saved</span></div>
    <div className="demo-saved-document"><FileText size={15} /><div><strong>northstar_resume_v2.pdf</strong><span>Saved to Product engineer at Northstar</span></div><span className="small-check"><Check size={13} />1 page</span></div>
  </div>;
}

function ResumePreview() {
  return <div className="demo-resume">
    <div className="demo-page-heading"><div><span className="eyebrow">TAILORED TO THE ROLE</span><h3>CV Studio</h3></div><span className="status status-ready"><Check size={11} />ATS check passed</span></div>
    <div className="resume-toolbar"><span className="active">Edit</span><span>Preview</span><span>LaTeX</span><span className="resume-page-count">1 / 1</span></div>
    <div className="resume-paper"><div className="resume-name">ALEX RIVERA</div><div className="resume-contact">Product engineer · alex@example.com</div><div className="resume-section-name">Summary</div><p>Engineer building thoughtful tools with Python, TypeScript, and a clear understanding of the people who use them.</p><div className="resume-section-name">Experience</div><div className="resume-experience"><strong>Software developer</strong><span>Studio Co.</span></div><ul><li>Built internal reporting tools that made the team’s daily work easier to follow.</li><li>Worked across product and engineering to turn user feedback into useful features.</li></ul><div className="resume-section-name">Technical skills</div><p>Python · TypeScript · React · SQL</p></div>
  </div>;
}

function InterviewPreview() {
  return <div className="demo-interview">
    <div className="demo-page-heading"><div><span className="eyebrow">PRODUCT ENGINEER · NORTHSTAR</span><h3>A little practice goes a long way.</h3></div></div>
    <div className="practice-question"><span className="eyebrow">PRACTICE QUESTION</span><p>Tell me about a tool you built that made someone else’s work easier.</p><span className="practice-cursor" /></div>
    <div className="prep-checklist"><span><Check size={13} />Company research saved</span><span><Check size={13} />Your experience, in context</span><span><Check size={13} />Interview-day cheat sheet</span></div>
    <div className="demo-saved-document"><FileText size={15} /><div><strong>northstar_interview_prep</strong><span>Ready to pick up next session</span></div><span className="status status-ready">Saved</span></div>
  </div>;
}

function WorkspacePreview() {
  const [view, setView] = useState<View>("tracker");
  const views: { value: View; label: string; icon: LucideIcon }[] = [{ value: "tracker", label: "Job tracker", icon: LayoutDashboard }, { value: "resume", label: "CV studio", icon: FileText }, { value: "interview", label: "Interview prep", icon: MessageSquare }];
  return <figure className="workspace-preview">
    <div className="window-bar"><span className="window-dots"><i /><i /><i /></span><span>cv_tailor / local workspace</span><span className="window-local"><span />On your machine</span></div>
    <div className="demo-workspace"><aside className="demo-sidebar"><span className="demo-brand"><FileText size={16} />cv_tailor</span><span className="demo-nav-label">WORKSPACE</span><div className="demo-nav" aria-label="Workspace preview views">{views.map(({ value, label, icon: Icon }) => <button type="button" key={value} aria-pressed={view === value} onClick={() => setView(value)}><Icon size={14} /><span>{label}</span></button>)}</div><div className="demo-profile"><span>AR</span><div>Alex Rivera<small>Local profile</small></div></div></aside><div className="demo-main" aria-live="polite">{view === "tracker" ? <TrackerPreview /> : view === "resume" ? <ResumePreview /> : <InterviewPreview />}</div></div>
    <div className="agent-receipt"><span className="receipt-icon"><Terminal size={16} /></span><div><span className="eyebrow">FROM YOUR AGENT, TO YOUR WORKSPACE</span><p>{view === "tracker" ? "Application saved. Everything is right where you left it." : view === "resume" ? "CV draft saved. Ready for your review." : "Preparation saved. Your next session starts here."}</p></div><Check size={16} className="receipt-check" /></div>
    <figcaption><span className="sample-dot" />Interactive preview · Sample data</figcaption>
  </figure>;
}

function SkillDesk() {
  const [selected, setSelected] = useState("cv-resume");
  const skill = skills.find(item => item.name === selected)!;
  return <div className="skill-desk"><div className="skill-list" aria-label="Included skills">{skills.map(item => <button key={item.name} type="button" onClick={() => setSelected(item.name)} aria-pressed={selected === item.name}><span>{item.name}</span><ArrowUpRight size={13} /></button>)}</div><div className="skill-detail" aria-live="polite"><span className="eyebrow">{skill.name}</span><h3>{skill.label}</h3><p>{skill.description}</p><div className="prompt-window"><div className="prompt-window-header"><span><Terminal size={13} />Try asking your agent</span><CopyButton key={skill.name} text={skill.prompt} label={`Copy ${skill.name} example prompt`} /></div><blockquote><span aria-hidden="true">›</span>{skill.prompt}</blockquote><div className="prompt-result"><Check size={13} />Saved work is available in your local workspace.</div></div><p className="skill-note">Use a skill by name or ask naturally. Your agent reads the instructions and uses CV Tailor’s commands to save the result.</p></div></div>;
}

function Installation() {
  const [mode, setMode] = useState<InstallMode>("cli");
  const commands = `git clone ${REPO}.git\ncd CV-Tailor\npython scripts/install.py --${mode === "cli" ? "cli-only" : "with-dashboard"}`;
  return <section className="install-section section" id="install" aria-labelledby="install-title"><div className="install-copy"><span className="eyebrow">MAKE IT YOUR WORKSPACE</span><h2 id="install-title">Start with your agent.<br />Add the dashboard anytime.</h2><p>A small setup, then it’s yours. Choose how you want to work; your profile and applications stay together either way.</p><div className="install-requirements"><span><Check size={14} />Python 3.12 or newer</span><span><Check size={14} />{mode === "cli" ? "No Node.js needed for CLI-only use" : "Node.js 22+ to install the dashboard"}</span><span><Check size={14} />No CV Tailor account or PostgreSQL server</span></div><a className="text-link" href={README} target="_blank" rel="noreferrer">Read the full installation guide<ArrowUpRight size={14} /></a></div><div className="install-panel"><div className="install-options" aria-label="Installation options"><button type="button" aria-pressed={mode === "cli"} onClick={() => setMode("cli")}><Terminal size={16} /><span>CLI only<small>The default</small></span></button><button type="button" aria-pressed={mode === "dashboard"} onClick={() => setMode("dashboard")}><LayoutDashboard size={16} /><span>CLI + dashboard<small>The visual workspace, too</small></span></button></div><div className="install-code"><div className="code-header"><span>YOUR TERMINAL</span><CopyButton key={mode} text={commands} label="Copy installation commands" /></div><pre><code>{commands}</code></pre><div className="install-code-note"><Check size={13} />{mode === "cli" ? "Skills, CLI commands, and your local database." : "Everything in the CLI, plus the local web interface."}</div></div><div className="after-install"><span className="eyebrow">THEN YOU’RE READY</span><p>The installer creates <code>.venv</code> and prints your CLI path. Activate it, open your AI agent in the repo, and ask it to use CV Tailor.</p>{mode === "dashboard" && <div className="launch-command"><code>cv-tailor dashboard</code><span>Launch the local UI <ArrowUpRight size={12} /></span></div>}{mode === "cli" && <div className="launch-command"><code>cv-tailor dashboard install</code><span>Add the UI later <ArrowUpRight size={12} /></span></div>}</div></div></section>;
}

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header"><div className="header-inner"><a href="#" aria-label="CV Tailor home"><Brand /></a><nav className="desktop-nav" aria-label="Main navigation"><a href="#workflow">How it works</a><a href="#features">Features</a><a href="#skills">The skills</a></nav><div className="header-actions"><ThemeToggle /><a className="github-link" href={REPO} target="_blank" rel="noreferrer">GitHub<ArrowUpRight size={13} /></a><a href="#install" className="header-install">Get started<ArrowRight size={13} /></a><button className="menu-toggle" type="button" aria-label={menuOpen ? "Close menu" : "Open menu"} aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={20} /> : <Menu size={20} />}</button></div></div><nav hidden={!menuOpen} id="mobile-navigation" className="mobile-nav" aria-label="Mobile navigation">{[["#workflow", "How it works"], ["#features", "Features"], ["#skills", "The skills"], ["#install", "Get started"]].map(([href, label]) => <a key={href} href={href} onClick={() => setMenuOpen(false)}>{label}<ArrowUpRight size={15} /></a>)}</nav></header>
    <main id="main">
      <section className="hero section" aria-labelledby="hero-title"><div className="hero-copy"><span className="hero-eyebrow"><span />OPEN SOURCE. YOUR WORKSPACE.</span><h1 id="hero-title">Your career workspace,<br /><em>at your command.</em></h1><p className="hero-description">Work with the AI agent you already use. Turn your experience into tailored applications, and keep the whole job search together on your machine.</p><div className="hero-actions"><ArrowLink href="#install">Set up your workspace</ArrowLink><a href="#features" className="hero-explore">Take a look around<ArrowRight size={14} /></a></div><div className="hero-note"><Check size={13} /><span>CLI only by default. Local dashboard when you want it.</span></div></div><WorkspacePreview /></section>
      <div className="agent-strip section"><span>AT HOME IN YOUR AGENT</span><div><span><Terminal size={15} />Claude Code</span><span><Terminal size={15} />Codex</span><span><Terminal size={15} />OpenCode</span><span><Terminal size={15} />Antigravity</span></div><p>Your agent. Your choice.</p></div>
      <section className="workflow-section section" id="workflow" aria-labelledby="workflow-title"><div className="section-heading"><div><span className="eyebrow">A WORKFLOW THAT STAYS WITH YOU</span><h2 id="workflow-title">From “this looks interesting”<br />to “I’m ready for the interview.”</h2></div><p>Start with what you’ve done. Give your agent a role to work toward. Pick up your progress in the terminal or the dashboard.</p></div><div className="workflow-steps">{[
        ["01", "Make it yours", "Import your CV, review your profile, and confirm the skills you actually have."],
        ["02", "Bring a role", "Paste a job description or URL. Explore the fit and gather useful company context."],
        ["03", "Shape the application", "Tailor your CV and cover letter. Review drafts, refine a bullet, and export."],
        ["04", "Keep moving", "Track the application, prepare for interviews, and return with your work intact."],
      ].map(([number, title, text]) => <article key={number}><span className="step-number">{number}</span><h3>{title}</h3><p>{text}</p></article>)}</div></section>
      <section className="features-section section" id="features" aria-labelledby="features-title"><div className="section-heading"><div><span className="eyebrow">THE TOOLS FOR YOUR NEXT STEP</span><h2 id="features-title">A place for every part<br />of the application.</h2></div><p>The writing, research, documents, and preparation all connect to the same profile and application history.</p></div><div className="feature-grid">{features.map(({ icon: Icon, title, description, detail }) => <article className="feature-card" key={title}><span className="feature-icon"><Icon size={20} strokeWidth={1.5} /></span><h3>{title}</h3><p>{description}</p><span className="feature-detail">{detail}</span></article>)}</div><div className="workspace-foundation"><div><UserRound size={19} /><span><strong>One reusable profile</strong><small>Your experience and confirmed skills.</small></span></div><div><Layers size={19} /><span><strong>Room to revise</strong><small>Keep drafts and earlier document versions.</small></span></div><div><FolderOpen size={19} /><span><strong>Local, lasting storage</strong><small>SQLite data that stays between sessions.</small></span></div></div></section>
      <section className="skills-section section" id="skills" aria-labelledby="skills-title"><div className="section-heading"><div><span className="eyebrow">11 SKILLS. ONE SHARED WORKSPACE.</span><h2 id="skills-title">Tell your agent<br />what you need.</h2></div><p>Each skill teaches your agent a CV Tailor workflow. It handles the reasoning and writing; CV Tailor gives the result a place to live.</p></div><SkillDesk /><div className="skills-footnote"><GitBranch size={15} /><p>Switch agents and keep your saved work. Enable built-in API-powered AI separately when you want it.</p><a href={`${REPO}#included-skills`} target="_blank" rel="noreferrer">Explore the skills<ArrowUpRight size={13} /></a></div></section>
      <Installation />
      <section className="faq-section section" aria-labelledby="faq-title"><div><span className="eyebrow">A FEW THINGS TO KNOW</span><h2 id="faq-title">Before you<br />make yourself at home.</h2><p>CLI-friendly. Dashboard-ready.<br />Built around your own workspace.</p></div><div className="faq-list">{questions.map(question => <details key={question.title}><summary>{question.title}<ChevronDown size={16} /></summary><p>{question.answer}</p></details>)}</div></section>
      <section className="closing-section section"><div className="closing-mark"><FileText size={26} strokeWidth={1.4} /></div><span className="eyebrow">YOUR EXPERIENCE. YOUR NEXT CHAPTER.</span><h2>A workspace to<br />make your next move.</h2><p>Start with your profile. Bring a role. Let’s put it together.</p><ArrowLink href="#install">Get started with CV Tailor</ArrowLink></section>
    </main>
    <footer className="site-footer section"><a href="#" aria-label="CV Tailor home"><Brand /></a><p>A local workspace for your next chapter.</p><nav aria-label="Footer navigation"><a href={README} target="_blank" rel="noreferrer">Documentation<ArrowUpRight size={12} /></a><a href={REPO} target="_blank" rel="noreferrer">GitHub<ArrowUpRight size={12} /></a><a href={`${REPO}/issues`} target="_blank" rel="noreferrer">Feedback<ArrowUpRight size={12} /></a></nav></footer>
  </>;
}
