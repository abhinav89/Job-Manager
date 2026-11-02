# CV Tailor

A local career workspace for your AI coding agent, with an optional visual dashboard. Tailor one-page CVs, prepare cover letters and interviews, discover jobs, and track applications in a SQLite database on your machine.

Use Claude Code, Codex, OpenCode, Antigravity, or another agent that can read skills and run shell commands. CV Tailor requires no account, PostgreSQL server, or AI API key. Your chosen agent supplies its own AI access. Built-in API-powered AI is optional.

## Install

Prerequisite: Python 3.12 or newer. Clone and run the installer:

```sh
git clone https://github.com/yabswannalearn/CV-Tailor.git
cd CV-Tailor
python scripts/install.py
```

Choose **CLI only** (the default) or **CLI + dashboard**. Noninteractive installation:

```sh
python scripts/install.py --cli-only
# Or include the optional local web interface:
python scripts/install.py --with-dashboard
```

The installer creates a repository `.venv`. Activate it before running commands:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```sh
# macOS / Linux
. .venv/bin/activate
```

Without activation, run `.venv/Scripts/cv-tailor.exe` on Windows or `.venv/bin/cv-tailor` on macOS/Linux. The installer prints the exact executable path.

Open your preferred AI agent in this repository and ask:

> Use CV Tailor. Import my CV, compare this job with my profile, tailor a resume and cover letter, and save them as drafts for this application.

The entry skill loads saved workspace context on each session. Confirm extracted profile facts and skills before using them in documents.

## Optional dashboard

Node.js 22 or newer is required to install/build the dashboard. It is not required for CLI-only use or to run an already built dashboard.

```sh
cv-tailor dashboard install
cv-tailor dashboard
```

Open [the local dashboard](http://127.0.0.1:8000). One Python process serves the static dashboard and its `/api` endpoints. The CLI works even when this server is stopped. Both interfaces use the same SQLite workspace.

Without provider credentials, use **Work with your CLI agent → Copy agent prompt**. Paste the prompt into your agent in this checkout. Results saved through the CLI appear in the dashboard. Review a draft before making it the current application document.

## Data and sessions

Data defaults to `~/.cv-tailor/cv-tailor.sqlite3`, outside the checkout, and survives restarts and repository updates. Each workspace has one local profile; profile email is contact information, not a login. Multiple clones share this default workspace.

Use a separate workspace with:

```sh
cv-tailor --data-dir /absolute/path/career-workspace init
cv-tailor --data-dir /absolute/path/career-workspace dashboard
```

`CV_TAILOR_HOME` is the equivalent environment setting. Pass the same workspace to every command. Existing hosted PostgreSQL databases are never read or changed; importing an old account is outside this release. Storage is local; your chosen AI agent/provider may process the context you give it. Harness chat histories remain in that harness.

## Commands

```sh
cv-tailor --json status
cv-tailor doctor
cv-tailor schema profile
cv-tailor profile extract-text /absolute/path/cv.pdf
cv-tailor profile import --input profile.json
cv-tailor applications add --input job.json --request-id unique-create-id
cv-tailor applications list --status Interview
cv-tailor applications get 1
cv-tailor context export --task resume --application 1
cv-tailor drafts import --kind resume --application 1 --input resume.json --request-id unique-draft-id
cv-tailor drafts list --application 1
cv-tailor resume blocks 1
cv-tailor resume check 1
cv-tailor drafts export 1 --format pdf --output resume.pdf
cv-tailor drafts apply 1 --revision 1
```

Commands accept `--json` anywhere and file/stdin JSON (`--input -`). Errors return a nonzero exit code and structured JSON in JSON mode. Run `cv-tailor GROUP --help` for subcommands and `schema KIND` for accepted content.

Updates, archive/restore, deletion, and applying documents require the current application revision; profile updates require the saved profile revision. On conflict, reread and reconcile changes. Use the same request ID for an identical create/import retry to prevent duplicates; a different payload requires a new ID.

New personal facts supplied in a conversation can be passed as a JSON list with `--evidence facts.json` on draft import/revise, resume patch, or practice save. They remain scoped to that conversation/application and are included in later context exports; they do not silently change the profile. Job requirements and generated text are not personal evidence.

Resumes are assembled from structured plain-text content, compiled with Tectonic, and checked for ATS warnings. Overflow drafts remain reviewable, but applying or exporting a resume PDF requires exactly one page. First PDF use may download TeX packages. Native execution is the default and runs with your OS permissions and bounded time/output; Docker execution remains an explicit option.

## Included skills

`cv-tailor`, `cv-profile`, `cv-jobs`, `cv-job-fit`, `cv-company-research`, `cv-resume`, `cv-resume-edit`, `cv-cover-letter`, `cv-tracker`, `cv-interview`, `cv-code-practice`, `cv-connect`.

Canonical skills live in `.agents/skills`, with Claude entrypoints in `.claude/skills`. They share the same CLI and output schemas. Company research uses the harness's browsing tools, or user-provided sources when browsing is unavailable. Factual grounding guidance and deterministic checks help catch unsupported claims; review generated documents.

## Optional built-in AI

```sh
python -m pip install -e "ai-service[ai]"
```

Put provider settings in `~/.cv-tailor/.env` (or your selected data directory), not the repository:

```env
AI_MODE=api
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
# Alternatively, standalone generation supports:
# AI_PROVIDER=openai
# OPENAI_API_KEY=your-key
# Optional job-search ranking:
# JEV_API_KEY=your-key
```

The default is `AI_MODE=external`. Merely setting a key does not enable server-side AI. The existing built-in Career Agent and Google Search grounding require Gemini; standalone generation supports Gemini or OpenAI. Restart the dashboard after changing settings. API secrets are excluded from native code/PDF subprocess environments.

Browser-backed job sources are optional: `python -m pip install -e "ai-service[browser]"`. Unavailable sources report diagnostics; URL intake and pasted job descriptions remain available.

## Development and verification

```sh
python -m pip install -e "ai-service[test,ai]"
python -m pytest ai-service/tests
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix frontend run test:tracker
npm --prefix frontend run test:resume-draft
npm --prefix frontend run test:browser
```

The backend is packaged under `ai-service/cv_tailor`. CLI and HTTP adapters share workspace services. Tests use disposable SQLite files, including real concurrent CLI processes; optional Docker integration tests use `RUN_SANDBOX_TESTS=1`.

The public domain serves only the separately built static landing page:

```sh
npm --prefix landing ci
npm --prefix landing run build
# Publish landing/out with your static hosting provider.
```

The local dashboard build is `frontend/out`; `cv-tailor dashboard install` packages it with the Python app. Never deploy the login-free local API as a public backend.

## License

CV Tailor is open source under the [MIT license](LICENSE).

## Resume formats

Eight visual formats are available through the CLI and optional dashboard: Classic, Modern, Minimal, Serif, Executive, Technical, Compact, and Sidebar. Run `cv-tailor --json templates list` to see their IDs. Save the chosen `template_id` on an application before importing its resume draft.

The landing page gallery uses actual one-page PDFs with fictional sample data. Its cards provide Copy prompt and an enlarged PDF modal. Rebuild both applications' sample assets and generated template catalogs with `python scripts/build_resume_gallery.py` (backend dependencies, Tectonic, and Poppler required). This does not invoke an AI provider.

## Guided tracking connections

Copy an Obsidian, Notion, Google Sheets, Markdown, Airtable, HubSpot, or GoHighLevel (GHL) connection prompt from the landing page into your coding agent in this checkout. The `cv-connect` skill guides setup and prepares reusable local setup/publishing scripts; these are agent-configured connections, not a preconfigured background sync service. SQLite remains primary, publishing is one-way and manual, and personal notes/custom fields are preserved. CRM setup verifies account capabilities, maps pipeline stages, and avoids unintended outreach or sales automations.

Any needed credentials are entered in your own terminal and saved in the Git-ignored `.env.integrations` file. Do not paste credentials into agent chat. For example, run `python scripts/integration_env.py set CV_TAILOR_NOTION_TOKEN` yourself for hidden token entry; `python scripts/integration_env.py status` reports configured key names only. OAuth setup scripts can call `save_env_values` from that helper directly in memory. The helper refuses to write a tracked or unignored environment file. Load values with `dotenv_values(path, interpolate=False)`.

Nonsecret configuration and generated scripts live under the Git-ignored `.cv-tailor-integrations/`. Review a dry run before your first publish. Provider authorization may be required for cloud tools; Obsidian/Markdown folder publishing needs no provider token. Most integration logos are from Simple Icons under CC0; the unmodified HighLevel logo comes from its official brand kit. Notices accompany the assets.
