---
name: cv-resume
description: Tailor and render a one-page resume from confirmed profile facts and a job description. Use for new CV drafts and ATS checks.
---

# cv-resume

Run `cv-tailor --json templates list` to discover the supported visual layouts: classic, modern, minimal, serif, executive, technical, compact, and sidebar. When a user chooses a layout, save `{ "template_id": "CHOSEN_ID" }` through `applications update ID --revision CURRENT_REVISION --input template.json` before exporting application context. Do not silently fall back to another layout.

Export `cv-tailor --json context export --task resume --application ID`. Use its profile, preset, chosen visual template, job, and ResumeContent JSON schema. The AI supplies plain text in structured fields; CV Tailor builds LaTeX deterministically.
Select and reword relevant experience without inventing facts, skills, accomplishments, or numbers. Prior generated wording and job requirements are not personal evidence. Review the result against confirmed facts before saving.
Save JSON using `cv-tailor --json drafts import --kind resume --application ID --input resume.json --request-id REQUEST_ID`. Inspect returned page count and ATS warnings. If it overflows, shorten supported wording and import a revised draft with `--parent DRAFT_ID`; never silently delete user facts or fabricate tighter metrics.
Run `resume check DRAFT_ID`. Export with `drafts export DRAFT_ID --format pdf --output /absolute/path/resume.pdf`. Applying uses `drafts apply DRAFT_ID --revision APPLICATION_REVISION` after the user requests making it current. Use cv-resume-edit for targeted changes.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.

When the user supplies a new personal fact for this conversation, pass a JSON list of those explicit assertions with `--evidence facts.json` on draft import/revise, resume patch, or practice save. Never put job requirements or invented claims in evidence. It stays scoped to this conversation/application; saving it to the profile is a separate user choice.
