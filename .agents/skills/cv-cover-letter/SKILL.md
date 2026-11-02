---
name: cv-cover-letter
description: Write or revise an application cover letter grounded in the local profile and job. Use for tailored cover letters.
---

# cv-cover-letter

Run `cv-tailor --json context export --task cover_letter --application ID`. Use the profile, explicit user statements, job, and available sourced research. Previous drafts guide wording but do not establish new facts.
Write a concise letter connecting actual experience to specific requirements. Avoid invented stories, portfolio claims, numbers, and generic company praise. Ask for missing evidence or omit the unsupported claim.
Save `{"content":"letter text"}` using `drafts import --kind cover_letter --application ID --input letter.json --request-id REQUEST_ID`. For a revision include `--parent OLD_DRAFT_ID`. Save as a reviewable draft; use `drafts apply DRAFT_ID --revision APPLICATION_REVISION` only when making it current is requested.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.

When the user supplies a new personal fact for this conversation, pass a JSON list of those explicit assertions with `--evidence facts.json` on draft import/revise, resume patch, or practice save. Never put job requirements or invented claims in evidence. It stays scoped to this conversation/application; saving it to the profile is a separate user choice.
