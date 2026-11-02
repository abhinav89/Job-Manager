# Using CV Tailor

This repository is a local career workspace. For user career tasks, start with `.agents/skills/cv-tailor/SKILL.md`; load focused skills as needed. Codex, OpenCode, and Antigravity discover `.agents/skills`. Claude entrypoints are in `.claude/skills`.

First setup: `python scripts/install.py --cli-only` (default) or `python scripts/install.py --with-dashboard`.
Activate `.venv` before using `cv-tailor`. Without activation use `.venv/Scripts/cv-tailor.exe` on Windows or `.venv/bin/cv-tailor` on macOS/Linux, or the environment's Python with `-m cv_tailor`.

Run `cv-tailor --json status` at the start of a session, then load the saved profile and relevant application. Storage defaults to `~/.cv-tailor`; pass `--data-dir` consistently for a different workspace. No CV Tailor account or AI API key is required. Write using CLI commands, not raw SQLite or code edits. Preserve the user's confirmed facts and distinguish drafts from current application documents.

For engineering changes read CONTEXT.md and applicable nested AGENTS.md files. Backend: `python -m pytest ai-service/tests`. Frontend: `npm --prefix frontend run build`. Never modify another agent's global configuration.
