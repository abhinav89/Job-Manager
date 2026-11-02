---
name: cv-profile
description: Import and maintain the local career profile, including experience, education, projects, and confirmed skills. Use when the user provides a CV or changes personal information.
---

# cv-profile

Read `cv-tailor --json profile get` and `cv-tailor --json schema profile`. For a PDF, use `cv-tailor --json profile extract-text /absolute/path/resume.pdf`; use the harness OCR capability or ask for text when extraction is empty.
Map only supplied facts to the profile schema. Present uncertain extraction results for review. Contact email is profile data, not a login. Mark skills confirmed only when the user affirms them; preset suggestions remain unconfirmed.
Save reviewed JSON using `cv-tailor --json profile import --input /absolute/path/profile.json`. When updating, include the revision read with the profile, or pass `--revision N`. Preserve unrelated data. A conflict requires rereading and reconciling changes, not blindly retrying the old revision. Conversation-only facts become profile facts only when the user requests saving them.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.
