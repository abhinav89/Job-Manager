---
name: cv-jobs
description: Discover jobs and gather accurate posting details from URLs or pasted descriptions. Use for job search and job intake before saving an application.
---

# cv-jobs

Use `cv-tailor --json jobs search "search terms"` for built-in sources; optionally provide `--sources name1,name2`. Source diagnostics distinguish unavailable sources from empty results. Research and relevance reasoning are performed by this harness, without CV Tailor AI calls.
For a supplied URL use `cv-tailor --json jobs fetch "URL"`, or use your available browser tools. A blocked or inaccessible posting requires pasted details; do not invent missing information. Gather company, title, description, and source. Job Source is distinct from URL and may be unknown.
Use cv-job-fit for a requirement comparison. When the user requests saving, inspect `schema application` and use `applications add --input file.json --request-id UNIQUE_ID`. Retain the same request ID if retrying the identical create operation.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.
