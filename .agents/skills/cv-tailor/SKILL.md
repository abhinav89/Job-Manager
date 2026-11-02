---
name: cv-tailor
description: Set up and operate the local CV Tailor career workspace. Use for onboarding, multi-step career tasks, or resuming saved application work.
---

# cv-tailor

Run `cv-tailor --json status` first. If no workspace exists, run `cv-tailor init`. The default installation is CLI only; add the optional UI with `cv-tailor dashboard install` and launch it with `cv-tailor dashboard`.
Load the saved profile using `profile get`; gather missing facts through conversation and use cv-profile to save them. Use `applications list` to identify a requested existing application; pass its explicit ID to subsequent commands. Route the requested task to the focused skills below. Read only the skill you need.
- Profile: cv-profile
- Job discovery/intake: cv-jobs
- Requirement comparison: cv-job-fit
- Research: cv-company-research
- Resume creation/editing: cv-resume, cv-resume-edit
- Cover letters: cv-cover-letter
- Application management: cv-tracker
- Optional tracking connections and publishing setup: cv-connect
- Interview preparation/practice: cv-interview
- Coding exercises/review: cv-code-practice
For a multi-step request, save the application when requested, export its context, produce the requested documents, and save each as a draft. Report real command results and document IDs. Applying drafts is a separate operation. The CLI and optional dashboard use the same local SQLite data; no account or CV Tailor AI API key is required.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.

When the user supplies a new personal fact for this conversation, pass a JSON list of those explicit assertions with `--evidence facts.json` on draft import/revise, resume patch, or practice save. Never put job requirements or invented claims in evidence. It stays scoped to this conversation/application; saving it to the profile is a separate user choice.
