---
name: cv-job-fit
description: Compare a job with confirmed personal evidence and practical constraints. Use for job-fit questions without an overall numerical score.
---

# cv-job-fit

Run `cv-tailor --json context export --task job_fit --application ID`, or use supplied job text with the saved profile. Follow its output schema.
For each requirement cite the job wording and profile/user evidence. Importance is required, preferred, or unclear. Assessment is supported, needs_clarification, or known_gap. Missing profile evidence alone is not a known gap: ask a focused question. Consider location, working hours, authorization, and salary separately, keeping unknowns explicit.
Do not produce an overall match score or an automatic apply/skip verdict. Save the assessment using `drafts import --kind job_fit --application ID --input fit.json --request-id REQUEST_ID` when persistence is requested.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.
