---
name: cv-tracker
description: Query and manage local job applications, statuses, archives, and documents. Use for application tracking and pipeline questions.
---

# cv-tracker

Use `cv-tailor --json applications list`, with optional `--status`, `--company`, and `--archived yes|no|all`. Use `applications get ID` for details and `applications stats` for counts. Answer broader questions by reasoning over the returned records; do not edit SQLite directly.
Read `schema application` or `schema application_update` for allowed fields. Add with `applications add --input job.json --request-id UNIQUE_ID`. Update with `applications update ID --revision N --input changes.json`. Archive/restore with `applications archive ID --revision N` and `applications restore ID --revision N`; archiving preserves status and documents.
Delete only when the user's request authorizes deletion, identifying the exact application; it also removes linked conversations and drafts. Use `applications delete ID --revision N`. For any conflict reread and reconcile. Never claim a write succeeded unless the command succeeded. Do not contact employers or submit applications as part of tracker maintenance.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.
