---
name: cv-company-research
description: Research companies and roles with cited sources for a job application. Use for company facts, interview research, and role context.
---

# cv-company-research

Run `cv-tailor --json context export --task research --application ID`. Use this harness's web-search or browser capability, prioritizing official company and job pages. Exclude personal contact data from search queries.
Separate supported company facts, dated observations, and inference. Record source titles and HTTP(S) URLs in the required research schema. Company research never establishes facts about the applicant. If web tools are unavailable, ask for source material and explain the limit rather than inventing research.
Save with `drafts import --kind research --application ID --input research.json --request-id REQUEST_ID`. Retain sources in the saved result.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.
