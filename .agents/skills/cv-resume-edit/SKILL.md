---
name: cv-resume-edit
description: Revise specific blocks of an existing CV while preserving unrelated content. Use for summary-only edits and targeted resume bullet changes.
---

# cv-resume-edit

Identify the application and draft with `drafts list --application ID`, then run `cv-tailor --json resume blocks DRAFT_ID`. Ask which block if the requested target is ambiguous. Read `schema resume_edit` for replacement JSON. A patch covers at most six contiguous blocks within one section; split other selections into separate patches.
Rewrite only the selected blocks using confirmed profile facts. Return plain text, not LaTeX. Do not turn a missing number or requested claim into evidence; ask for real information when needed.
Use `resume patch DRAFT_ID --input patches.json --request-id UNIQUE_ID`. The command creates a new draft, escapes text, and preserves the other source spans. Inspect page count and run `resume check NEW_DRAFT_ID`. Earlier drafts remain available. Do not regenerate the whole CV as a fallback for a targeted edit.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.

When the user supplies a new personal fact for this conversation, pass a JSON list of those explicit assertions with `--evidence facts.json` on draft import/revise, resume patch, or practice save. Never put job requirements or invented claims in evidence. It stays scoped to this conversation/application; saving it to the profile is a separate user choice.
