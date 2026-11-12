# Job-Manager Product & UX Design Note

## 1. Product Vision & Goals

**Job-Manager** is a high-performance career and job search management platform built to accelerate executive, tech, and advisory job searches (targeting `jobs.dealos.in`). It bridges job discovery, career profile management, transparent match scoring, truthful AI-assisted CV tailoring, application tracking, and document export.

### Core Principles
1. **Truthful Career Representation:** Zero invented facts, inflated metrics, or false statements. Every tailored resume bullet must tie back to confirmed user evidence.
2. **Actionable Pipeline:** Dashboards prioritize active tasks (jobs to review, applications due for follow-up, submission prep) rather than passive analytics.
3. **Evidence-Based Matching:** Match ratings (0–10 scale) transparently disclose positive alignment, missing qualifications, and uncertainty factors without false precision.
4. **Multi-Source Feeder:** Scalable architecture tracking company career pages (Workday, Greenhouse, Lever), aggregator feeds (LinkedIn, iimjobs), and manual job intake.
5. **Tier & Pricing Preparedness:** Architecture with built-in awareness of free versus pro quotas (tailor limits, ATS checks, template availability).

---

## 2. Navigation Architecture

The application adopts a clean, professional, responsive SaaS sidebar and top bar:

* **Dashboard (`/dashboard`):** 
  * Pipeline stats (To Review, To Apply, Applied, Interviewing, Offers).
  * Action items: Follow-ups due today, high-match new postings, pending tailored drafts.
* **Find Jobs (`/discover`):**
  * Natural language and keyword search bar (Role, Company, Skills).
  * Quick filter chips: Work Model (Remote, Hybrid, Onsite), Location (India, US, Global), Experience (Entry, Mid, Senior), and Recency.
  * Slide-over "All Filters" drawer (Basic Criteria, Location, Experience slider, Role taxonomy, Company include/exclude).
  * Job cards with match score gauge (e.g. `8.5 GOOD`), matched skills, gap tags, "Save for later", and "Tailor and Apply" actions.
* **Application Tracker (`/tracker`):**
  * Kanban Board and scannable List views.
  * Stages: `To Review`, `To Apply`, `Applied`, `Screening / Interview`, `Offer`, `Rejected`, `Archived`.
  * Status history timeline, interview/follow-up date reminders, contact notes.
  * One-click Application Master Sheet export (CSV and Excel `.xlsx`) with direct document links.
* **Resume Library (`/resumes` & `/generate`):**
  * Onboarding modal (Upload PDF/DOCX, LinkedIn URL, or paste text with 4-step parsing progress).
  * 3-step Tailoring Wizard:
    1. *See Your Difference:* Side-by-side comparison of job requirements vs. user qualifications.
    2. *Align Your Resume:* Block-level spot edits and template selection (Classic, Modern, Executive, Minimal, Compact).
    3. *Review Your New Resume:* In-browser PDF preview and Word (.docx) download.
  * ATS Compliance Checker with actionable fix suggestions.
* **Profile (`/profile`):**
  * Confirmed career facts record: Work Experience, Education, Projects, Skills (Confirmed vs. Preset), Certifications.
  * Search preferences: Target roles, desired locations, remote policy, salary targets, seniority level.
* **Settings (`/settings`):**
  * Account & Auth status (Local dev mode, Google OAuth connection, Supabase integration).
  * AI Provider keys (Gemini / OpenAI), tier quota status (Free vs. Pro limits).

---

## 3. Visual Design System

* **Color Palette:**
  * Backgrounds: Light slate / neutral surface (`#f8fafc`, `#ffffff`).
  * Text & Ink: High contrast slate (`#0f172a`, `#334155`, `#64748b`).
  * Primary Accent: Executive Deep Indigo / Blue (`#2563eb`, `#1d4ed8`).
  * Success / Fit: Emerald (`#059669`, `#10b981`, `#ecfdf5`).
  * Warnings / Gaps: Amber (`#d97706`, `#fef3c7`).
  * Danger: Rose (`#e11d48`, `#fff1f2`).
* **Typography:** Modern clean sans-serif (`Inter`, `system-ui`), crisp tabular figures for dates, metrics, and match scores.
* **Card & Drawer Layouts:**
  * Clean borders (`border-slate-200`), rounded corners (`rounded-xl`), subtle shadows (`shadow-sm` on hover).
  * High scannability: Company logos/monograms, bold job titles, pill badges for metadata, clear distinction between matched criteria and missing requirements.

---

## 4. Multi-Source Job Feeder Architecture

```
[Company Career Pages]       [Job Aggregators]       [Direct Manual Entry]
(Greenhouse, Lever, etc.)    (LinkedIn, Remotive...)  (Paste JD / URL)
           │                         │                        │
           └─────────────────┬───────┴────────────────────────┘
                             ▼
              [Job Ingestion & Normalizer]
                             │
                             ▼
              [Job Repository / Deduplication]
                             │
                             ▼
               [Match Engine (Heuristic + AI)]
                             │
                             ▼
              [User Feed / Application Tracker]
```

1. **Job Normalizer:** Standardizes title, company, location, work arrangement (remote/hybrid/onsite), salary, source URL, and full description text.
2. **Deduplication:** Hash-based identifier on `(normalized_company, normalized_title, location)`.
3. **Match Scoring:** 
   * Experience alignment (years & seniority).
   * Skill and keyword overlap.
   * Work arrangement / location compatibility.
   * Plain-language explanation of supported factors and missing gaps.
