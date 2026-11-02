# CV Tailor

A free, open-source CV tailoring app. Paste your profile and a job description, get back an ATS-safe, one-page resume PDF built from your real experience — plus a matching cover letter.

**Live app:** [cvtailor.me](https://cvtailor.me)

## How it works

- **AI-powered tailoring** — the backend sends your profile + job description to Google's Gemini models (with OpenAI as a one-line backup via `AI_PROVIDER`), which select, rewrite, and keyword-align your bullets.
- **LaTeX-quality PDFs** — the AI returns plain text only; a deterministic LaTeX assembler builds every document, so an AI rewrite can never break compilation. Compiled with Tectonic.
- **ATS Check** — every generated PDF is validated post-compile: section order, selectable text, ATS-conventional headings.
- **Spot Edit** — select any text in the PDF preview and describe a change ("make this more metric-heavy"). Only those lines are rewritten; a grounding pass blocks invented facts and numbers.
- **Roles & Presets** — pick a role (e.g. Virtual Assistant, Data Analyst) to steer summary style, skills bank, and section emphasis.
- **Application Tracker, Cover Letters, Interview Practice, Coding Practice** — all powered by the same AI layer.
- **Career Agent** — a Google ADK and Gemini assistant with persistent application or general chats, sourced company research, tailored CV and cover-letter drafts, interview preparation, and downloadable interview cheat sheets. Drafts can be reviewed and versioned before being applied to a tracked application.
- **Job fit and tracker management** — request an evidence-based fit analysis without a numerical score, and review Career Agent proposals to add, update, archive, restore, or delete tracked applications. Archived applications keep their status and documents.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (TypeScript), react-pdf preview |
| Backend | FastAPI (Python) |
| AI | Google Gemini API (default) · OpenAI Chat Completions (backup) |
| Database | PostgreSQL |
| PDF | Tectonic (LaTeX), pypdf-based ATS validation |

## Running locally

Docker is optional for trusted, single-user development. The example configuration uses native Python and Tectonic (`EXECUTION_BACKEND=local`, `ENVIRONMENT=development`). `tecto` in the Python requirements supplies the Tectonic executable; it downloads TeX packages on first use. Alternatively, install XeLaTeX and set `PDF_LATEX_ENGINE=xelatex`.

```bash
# 1. Backend
cd ai-service
pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL, GEMINI_API_KEY (or OPENAI_API_KEY)
python migration.py         # create tables
uvicorn main:app --reload --host 127.0.0.1

# 2. Frontend (new terminal, from the repository root)
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1
```

Use native mode only for your own local code and LaTeX. It runs tools with your OS account's file and network access, with time/output limits and an environment that excludes application credentials. Keep both servers bound to `127.0.0.1`. PostgreSQL, Node.js, Python and provider credentials are still required.

For hosted or shared deployments, set `ENVIRONMENT=production` and `EXECUTION_BACKEND=docker`, and provision the isolated execution images described in [the runtime guide](docs/remediation_runtime.md). Native mode is rejected outside development; Docker failures never switch to native execution automatically.

## Configuration

All AI traffic goes through one dispatcher (`ai-service/services/llm_service.py`). Switch providers with env vars:

```env
AI_PROVIDER=gemini          # or "openai"
GEMINI_API_KEY=...          # required for the default provider
GEMINI_MODEL=gemini-3.1-flash-lite-preview
OPENAI_API_KEY=sk-...       # only needed if AI_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
```

The Career Agent uses Gemini for conversations and tools, even if the standalone AI provider is set to OpenAI. Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY` for ADK) and use a Gemini model that supports Google Search grounding for company research. Existing skills need confirmation in the profile before the agent can use them as personal evidence. Run `python migration.py` when upgrading an existing database to add the conversation, skill confirmation, job source, and archive fields.

The app does not use a credit system. AI evidence checks help catch unsupported claims, but users should review drafts before applying them.
