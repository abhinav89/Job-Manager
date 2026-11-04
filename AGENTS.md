# Using CV Tailor

## Development workflow

Make engineering changes on the long-lived `dev` branch. Fetch origin and switch to `dev` before editing; create it from `origin/main` only if it does not exist. Preserve uncommitted work and existing branch history. Never reset or force-push a branch to synchronize it.

Enable the repository's branch guards once per clone with `python scripts/setup_git_hooks.py`. Do not overwrite an existing custom hooks setup; integrate the guards with it instead. The guards block commits on `main` and direct pushes to `main`.

Commit and push changes to `dev`, then open a PR from `dev` to `main`. Merge through the PR after required checks pass when the user has authorized the merge. Never commit or push directly to `main`, bypass its required checks, or delete `dev` after merging. After a merge, fetch origin, fast-forward `dev` to `origin/main` when possible, and leave the checkout on `dev`. If branches have diverged, preserve the existing work and merge normally rather than resetting.

## Career workspace

This repository is a local career workspace. For user career tasks, start with `.agents/skills/cv-tailor/SKILL.md`; load focused skills as needed. Codex, OpenCode, and Antigravity discover `.agents/skills`. Claude entrypoints are in `.claude/skills`.

First setup: `python scripts/install.py --cli-only` (default) or `python scripts/install.py --with-dashboard`.
Activate `.venv` before using `cv-tailor`. Without activation use `.venv/Scripts/cv-tailor.exe` on Windows or `.venv/bin/cv-tailor` on macOS/Linux, or the environment's Python with `-m cv_tailor`.

Run `cv-tailor --json status` at the start of a session, then load the saved profile and relevant application. Storage defaults to `~/.cv-tailor`; pass `--data-dir` consistently for a different workspace. No CV Tailor account or AI API key is required. Write using CLI commands, not raw SQLite or code edits. Preserve the user's confirmed facts and distinguish drafts from current application documents.

Status includes saved SQLite preferences. Use `preferences get` to load the default resume template and preferred tracking connection; reuse them unless the user changes them. Save explicit preference choices with `preferences set --revision N --input preferences.json`. Application-specific template choices override the default. Credentials stay in the Git-ignored environment file, never preferences or SQLite.

For engineering changes read CONTEXT.md and applicable nested AGENTS.md files. Backend: `python -m pytest ai-service/tests`. Frontend: `npm --prefix frontend run build`. Never modify another agent's global configuration.
