---
name: cv-interview
description: Prepare and practice for an interview using a local profile and job. Use for preparation plans, mock questions, answer feedback, and cheat sheets.
---

# cv-interview

Select the application and export `context export --task interview_plan --application ID`. Ask about interview date or available preparation time when useful; allow skipping. Prepare likely questions and talking points grounded in real experience. Personal stories must come from the user, not the job posting.
For mock practice ask one question at a time, let the user answer, then give feedback. Use `schema interview_feedback` when saving structured feedback; do not infer webcam/delivery observations you did not receive. A cheat sheet uses `schema cheat_sheet` and may include sourced company facts, supported talking points, and questions to ask.
Save through `practice save --kind interview_plan|interview_feedback|cheat_sheet --application ID --input file.json --request-id UNIQUE_ID`. Reuse saved preparation when resuming. Cheat-sheet PDF export uses `drafts export ID --format pdf --output /absolute/path/cheat-sheet.pdf`.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.

When the user supplies a new personal fact for this conversation, pass a JSON list of those explicit assertions with `--evidence facts.json` on draft import/revise, resume patch, or practice save. Never put job requirements or invented claims in evidence. It stays scoped to this conversation/application; saving it to the profile is a separate user choice.
