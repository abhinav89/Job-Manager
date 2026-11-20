# DealOS Jobs — Comprehensive Test Suite & Verification Matrix

This living document catalogs all verification suites, automated test cases, architectural invariants, and manual validation procedures across the DealOS Jobs platform. It covers past implementations (Apify scheduled matching, ChatGPT P1 fixes, Google Auth, pricing isolation) and all phases of the Auto Apply agent.

---

## 1. Test Suite Summary Dashboard

| Module / Milestone | Primary Test Script / Endpoint | Tests | Coverage Scope | Status |
| :--- | :--- | :---: | :--- | :---: |
| **Apify Job Matches** | `scripts/test_apify_resumes.py` | 5 | Theme resume linking, per-person fetch limits (5 jobs/run), budget guardrails, profile isolation, server-verified allowlist | **100% Passed** |
| **ChatGPT P1 Fixes** | `scripts/test_p1_matching.py` | 4 | Dynamic JD vs CV comparison, accurate tenure calculation with overlapping interval merging, multi-workspace isolation | **100% Passed** |
| **Google Auth & Pricing** | `ai-service/tests/test_auth_routes.py` | 3 | Passwordless Google OAuth verification, logged-out plan display isolation, Career Sprint pricing restore | **100% Passed** |
| **Auto Apply Phase 1** | `scripts/test_auto_apply_phase1.py` | 6 | Setup defaults, run-level non-destructive location modes (filter vs. prioritize), deduplication, ambiguity flagging, persistent queue pause/resume/feed | **100% Passed** |
| **Auto Apply Phase 2** | `scripts/test_auto_apply_phase2.py` | 8 | 8-category Seed Answer Bank, unfamiliar required question holding, candidate answering with 4 scopes, semantic answer reuse, manual snapshot | **100% Passed** |
| **Auto Apply Phase 3** | `scripts/test_auto_apply_phase3.py` | 5 | Source branching (tailored CV vs single profile CV for Naukri/iimjobs), wording diffs, page overflow check (<=4 pages), 4 approval permutations, non-blocking queue | **100% Passed** |
| **Auto Apply Phase 4** | `scripts/test_auto_apply_phase4.py` | 6 | Greenhouse/Lever multi-step execution & confirmation IDs, ambiguous submission hold policy, Workday MFA/CAPTCHA pause/resume, Naukri handoffs & manual report, unattended limits | **100% Passed** |
| **Auto Apply Phase 5** | `scripts/test_auto_apply_phase5.py` | 6 | Multi-channel intake (WhatsApp, social/LinkedIn, Gmail alerts), intake rule qualification, email application drafting, independent email review, hiring-manager outreach flagging, tracker sync | **100% Passed** |

---

## 2. Milestone Test Details

### Milestone A: Apify Private Scheduled Job Matches
- **Implementation Commit**: `44c9610`
- **Location**: `Job-Manager/ai-service/cv_tailor/services/apify_service.py`, `routers/apify_routes.py`
- **Verification Suite**:
  1. **Server-Verified Allowlist & Ownership**: Enforces access strictly for authorized emails (`abhinava2015@email.iimcal.ac.in` and `shivangi*`). Denies unauthorized workspace requests with `403 Forbidden`.
  2. **Theme Resumes & Safe Duplication**: Allows candidates to duplicate existing resumes as theme-specific copies (e.g. FP&A vs. Strategy & CEO Office). Modifying one theme's resume never mutates another theme or the source version.
  3. **Strict 5-Posting Fetch Limit**: Hard ceiling of 5 postings per candidate per run, preventing Apify token/budget overruns regardless of the number of themes enabled.
  4. **Non-Fabrication Policy**: Scrapes search keywords only; source files and raw resume text are kept private. Edits preserve documented achievements without embellishment.

---

### Milestone B: ChatGPT P1 Architectural Resolution
- **Implementation Commit**: `5aad4a8`
- **Location**: `Job-Manager/ai-service/cv_tailor/services/job_repository_service.py`, `routers/scraper_routes.py`, `workspace.py`
- **Verification Suite**:
  1. **Dynamic Resume & JD Gap Analysis**: Replaced static 7.5 demo scores and hardcoded qualifications with dynamic semantic comparison between the candidate's selected resume and the actual job description.
  2. **Accurate Tenure Calculation**: Replaced the arbitrary `roles × 2.2` multiplier with exact date-parsed tenure calculation. Implemented overlapping interval merging for concurrent roles.
  3. **Multi-Workspace Profile Resolution**: Removed hardcoded `workspace_id == 1` fallback, dynamically resolving the profile from the authenticated workspace and verifying isolated ranking per candidate.

---

### Milestone C: Authentication & Plan Isolation
- **Implementation Commit**: `fd69ef2`, `53e12b7`
- **Location**: `Job-Manager/ai-service/cv_tailor/routers/auth_routes.py`, `frontend/src/lib/authContext.tsx`
- **Verification Suite**:
  1. **Passwordless Google Auth**: Supports Google credential tokens with email verification, eliminating mandatory password requirements for verified Google sign-ins.
  2. **Logged-Out Plan Display Isolation**: Prevents logged-out guests from seeing active subscription tiers (e.g., Career Sprint active badge) by keying subscription status strictly to authenticated user context.
  3. **Role-Based Superadmin Gating**: Restricts superadmin navigation and metrics strictly to users with `role === "owner"`.

---

### Milestone D: Auto Apply Phase 1 — Filtering, Selection & Run Queue
- **Implementation Commit**: `fbc25c1`
- **Test File**: `Job-Manager/scripts/test_auto_apply_phase1.py`
- **Verification Cases**:
  - `Test 1`: Setup defaults initialization & profile suggestions (calculates tenure, target experience range 4–7 yrs, suggests role themes).
  - `Test 2`: Non-destructive run adjustments: changing location or arrangements for a single run preserves saved candidate defaults 100% intact.
  - `Test 3`: Location Modes: Filter Mode strictly includes preferred locations; Prioritize Mode ranks preferred locations first and retains other eligible locations below.
  - `Test 4`: Cross-posting deduplication: consolidates identical company/title listings into unique opportunities.
  - `Test 5`: Ambiguity flagging: flags listings with undisclosed compensation or unstated location for review.
  - `Test 6`: Persistent queue pause/resume and chat activity feed audit trail.

---

### Milestone E: Auto Apply Phase 2 — Form Filling & Answer Bank
- **Implementation Commit**: `a89a84d`
- **Test File**: `Job-Manager/scripts/test_auto_apply_phase2.py`
- **Verification Cases**:
  - `Test 1`: Seed Answer Bank initialization with 8 core categories (notice period, availability, work authorization, sponsorship, relocation, compensation, travel, experience).
  - `Test 2`: Candidate editing and customization of Answer Bank entries.
  - `Test 3 & 4`: Unfamiliar required question handling: Job 1 pauses waiting for candidate input while Job 2 continues in background.
  - `Test 5`: Answering in chat/modal with scopes (`save_as_default`, `save_for_rule`, `use_once`, `ask_every_time`).
  - `Test 6`: Answer reuse: Job 3 automatically reuses the saved answer for the same semantic question without pausing.
  - `Test 7`: Form review snapshot generation and manual review mode.
  - `Test 8`: Chat feed logging of answering events.

---

### Milestone F: Auto Apply Phase 3 — CV Tailoring & Independent Approvals
- **Implementation Commit**: `36a20b9`
- **Test File**: `Job-Manager/scripts/test_auto_apply_phase3.py`
- **Verification Cases**:
  - `Test 1`: Source branching: Portals/LinkedIn/Email generate tailored CV with verified facts; Naukri/iimjobs bypass tailoring and attach single profile CV as-is.
  - `Test 2`: Testing all four approval permutations:
    - `(review_tailored_cv=True, review_before_portal_submission=True)`: Pauses at CV review, then pauses at submission review.
    - `(review_tailored_cv=True, review_before_portal_submission=False)`: Pauses at CV review, then auto-advances.
    - `(review_tailored_cv=False, review_before_portal_submission=True)`: Auto-advances CV, pauses at submission review.
    - `(review_tailored_cv=False, review_before_portal_submission=False)`: Auto-advances through both checkpoints directly to ready.
  - `Test 3`: Non-blocking multi-job queue execution (Job A waits for CV review while Job B continues).
  - `Test 4`: CV preview, wording diff inspection, and page overflow checks (<=4 pages).
  - `Test 5`: Activity feed audit logging.

---

### Milestone G: Auto Apply Phase 4 — Portal Automation & Workday Accounts
- **Implementation Commit**: `abf7aee`
- **Test File**: `Job-Manager/scripts/test_auto_apply_phase4.py`
- **Verification Cases**:
  - `Test 1`: Greenhouse multi-step form execution, file upload, and confirmation ID capture (`GH-CONF-...`).
  - `Test 2`: Ambiguous response policy: Holds unclear submissions at `submission_unclear` and requires verification check before retry.
  - `Test 3`: Workday adapter: account creation opt-in check, session reuse, and human checkpoint pausing (`paused_for_human_checkpoint`) for interactive MFA/CAPTCHA with explicit resumption.
  - `Test 4`: Naukri & iimjobs adapters: clear handoff package generation, custom pitch preview, and candidate manual report sync to tracker.
  - `Test 5`: LinkedIn adapter: external routing vs. manual Easy Apply handoff.
  - `Test 6`: Unattended automated submission limits enforcement (`allow_unattended_submission`, `daily_submission_limit`).

---

### Milestone H: Auto Apply Phase 5 — Hiring Alerts & Email Applications
- **Implementation State**: Completed & Verified
- **Test File**: `Job-Manager/scripts/test_auto_apply_phase5.py`
- **Verification Cases (100% Passed)**:
  - `Test 1`: Gmail OAuth onboarding & isolated scopes (`gmail.send`, `gmail.compose` by default, isolated `gmail.readonly` for inbox intake / Workday verification).
  - `Test 2`: Multi-channel intake parser: Extracts role, company, recipient email, location, experience from WhatsApp messages, LinkedIn posts, and Gmail alerts.
  - `Test 3`: Intake rule qualification & ambiguity routing: Incomplete/ambiguous intake messages routed to `needs_input` with ambiguity flags.
  - `Test 4`: Email application drafting: Generates tailored pitch and attaches job-specific tailored PDF with page budget overflow guardrail (<= 4 pages).
  - `Test 5`: Independent email review setting (`review_before_email_send=True` pauses at `waiting_email_review`; `False` auto-sends to careers inbox) & Hiring-manager outreach check: Mandatory review for individual work emails.
  - `Test 6`: Candidate approval & strict tracker sync: Confirmed sends transition to `Applied` with confirmation reference `EML-...` in SQLite `JobApplication`.

---

## 3. How to Run All Verification Suites

Execute all suites sequentially via PowerShell:
```powershell
cd "C:\Users\Abhinav Agrawal\Documents\Job-Manager\Job-Manager"

# Auto Apply Phase 1
& "ai-service/venv/Scripts/python.exe" "scripts/test_auto_apply_phase1.py"

# Auto Apply Phase 2
& "ai-service/venv/Scripts/python.exe" "scripts/test_auto_apply_phase2.py"

# Auto Apply Phase 3
& "ai-service/venv/Scripts/python.exe" "scripts/test_auto_apply_phase3.py"

# Auto Apply Phase 4
& "ai-service/venv/Scripts/python.exe" "scripts/test_auto_apply_phase4.py"

# Auto Apply Phase 5
& "ai-service/venv/Scripts/python.exe" "scripts/test_auto_apply_phase5.py"
```
