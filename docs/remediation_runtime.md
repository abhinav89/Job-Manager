# Remediation runtime and validation

Execution has two explicit modes. The environment example selects `EXECUTION_BACKEND=local` with `ENVIRONMENT=development`, so people can run the full project locally without Docker. Native mode uses the current Python interpreter and Tectonic (supplied by `tecto`) or an installed XeLaTeX. It runs with the developer's OS file/network permissions; it is not a security isolation boundary. Time and output limits, credential-free child environments, temporary workspaces, and disabled TeX shell escape still apply. Bind both servers to `127.0.0.1` and use only your own trusted code and LaTeX. First-use TeX package downloads require network access.

Hosted/shared deployments use `EXECUTION_BACKEND=docker` and `ENVIRONMENT=production`. If no mode is set, Docker remains the default. Native mode is rejected outside development, both at startup and execution time. There is no automatic fallback between modes. Docker mode executes Python and raw LaTeX in disposable containers and requires a Linux Docker engine with provisioned images.

For Docker mode, build the images from `ai-service/` before serving execution or compilation requests:

```powershell
docker build --target python -t cv-tailor-python:1 -f sandbox/Dockerfile .
docker build --target pdf -t cv-tailor-pdf:1 -f sandbox/Dockerfile .
```

The PDF image provisions XeLaTeX, Tectonic 0.15, both Templates' resources, and the package and format caches at build time. Its first build downloads the TeX distribution and can take several minutes. Runtime compilation has no network access and supports installed/cached packages. Rebuild the image when Templates require additional resources. The Docker build context excludes application secrets, the virtual environment, uploaded files, and logs.

In Docker mode, `CODE_SANDBOX_IMAGE` and `PDF_SANDBOX_IMAGE` can select separately provisioned images with the same fixed worker protocol. Requests never pull images. Containers use an unprivileged user, no host mounts, no network, no added capabilities, a read-only root, a 128 MiB disposable workspace, one CPU, 512 MiB memory without swap, and a 32-process limit. Container removal terminates descendants after completion or timeout. In both modes, Python has a 10-second deadline and bounded output; PDF compilation has a 120-second deadline. The API admits two executions and eight external workers per process, rejecting excess work rather than queuing it indefinitely. Native mode does not provide the container CPU, memory, process-count, filesystem or network restrictions.

Apply the database upgrade before starting the updated API against an existing database:

```powershell
python migration.py
```

`migration.py` and `AUTO_CREATE_TABLES` share `schema_changes.py`. They create the request-lifecycle table, add the conversation's active-request column, apply the existing compatibility upgrades, and seed missing Presets. Run this command against the intended deployment database using its normal migration process. Development validation uses an isolated test schema and does not migrate the configured application database.

Career Agent requests are claimed in a short transaction. Only one turn can be active per conversation. External work uses plain input snapshots and stages draft results in memory; a second short transaction saves the reply, drafts, and completion state together. Identical completed request IDs return their saved result. In-progress, failed, cancelled, or conflicting retries return controlled responses instead of repeating paid actions. Requests abandoned for more than 15 minutes release their conversation lock with an explicit failed state. Agent turns have a five-minute overall deadline. Cancelling a reply prevents late results from being saved; an already running external call may take time to finish.

Conversation Evidence is limited to the newest user-authored turns within 12,000 characters, retaining whole turns where possible and marking an oversized newest turn's truncation. Generation and verification receive the same selection. The stored transcript remains available; this window is not permanent factual memory, and earlier assistant messages or drafts cannot establish personal facts.

The job URL fetcher validates every resolved address, pins the TCP connection to a validated public address, verifies HTTPS against the original hostname, and revalidates up to three redirects. It limits DNS lookup to five seconds, individual socket operations to ten seconds, the fetch to 30 seconds, the uncompressed response to 2 MiB, and visible text to 64,000 characters. It requests identity encoding and rejects unexpectedly compressed responses. These limits apply before HTML extraction or a model call.

Run deterministic backend checks from `ai-service/`:

```powershell
python -m pip install -r requirements.txt pytest
python -m pytest tests -q
```

The real integration checks are opt-in locally and mandatory in the separate backend CI job. Set `TEST_DATABASE_URL` to a dedicated Postgres test database and `RUN_SANDBOX_TESTS=1` after building both images, then run:

```powershell
python -m pytest tests/test_remediation_integration.py -q
```

The Postgres suite creates and removes its own unique test schema. It checks migration consistency, duplicate requests, cancellation/failure atomicity, and connection-pool availability while external work waits. The sandbox suite exercises actual Python/container isolation and PDF generation across six Presets, two Templates, both optional-section states, and both compiler engines. Normal unit tests fake providers; they do not spend API credits or demonstrate OS isolation by themselves.

Run frontend checks from `frontend/`:

```powershell
npm run test:resume-draft
npm run test:tracker
npx tsc --noEmit
npx playwright install chromium
npm run test:browser
```

Browser tests start a separate frontend on port 3100 with `.next-remediation` as its build directory and fixture API responses. They do not require application accounts or live model calls. They exercise source/form synchronization, PDF Spot Edits in all three modes, page preservation, stale PDF/ATS responses, camera-track cleanup, and late completions after cancellation. Interview question requests send the selected job context in a POST body so long descriptions do not depend on URL length limits; the authenticated GET endpoint remains available.

Structured schemas validate output shape; claim verification separately checks factual support. Model-assisted claim verification reduces unsupported output but is not a proof of truth. Provider availability and production deployment configuration still need normal release verification.

## Local verification record — 2026-11-02

- Original backend baseline: `python -m unittest discover -s tests` — 83 passed.
- Deterministic backend suite: `venv\Scripts\python.exe -m pytest tests -q` — 123 passed, 9 skipped, and 18 subtests passed in 24 seconds. The nine infrastructure tests are skipped unless explicitly enabled and passed in the provisioned run below.
- Final focused backend rerun after small matching/error-status fixes: 64 passed, with 13 subtests passed. FastAPI app import and `/health` smoke checks also passed with automatic schema creation disabled.
- Provisioned integration suite: 9 passed, with 48 PDF matrix subtests passed in 281 seconds. These exercised both engines, both Templates, all six Presets, optional sections present/absent, host-file/network isolation, timeout cleanup, and Postgres request atomicity.
- Postgres checks were rerun after the final conversation locking changes: 5 passed. Three conversations held fake external calls with a pool of two connections; no connection remained checked out during the wait. Duplicate and conflicting turns, provider failure, database-write failure, coroutine cancellation, explicit cancellation, and late results were covered.
- Frontend: 23 resume parser tests, 4 tracker tests, TypeScript checks, all 5 browser tests, and the production Next.js build passed. The build generated all 16 routes. Browser fixtures intentionally block remote Monaco/MediaPipe downloads; their unavailable-resource console messages do not change the tested cleanup behavior.
- Both sandbox images were built locally. The first PDF build exposed missing font resources; package provisioning and offline prewarming now compile both Templates with both engines before an image can finish building.

The initial remediation validation used no paid model calls and did not change the configured application database or `.env`. Starting the app afterward applied its enabled migration to the local development database. The temporary Postgres integration container was separate from application data and has been removed.

### Follow-up: resume generation schema compatibility

Live use exposed a Gemini HTTP 400: the SDK serialized strict Pydantic models through the older `response_schema` field, which rejected `additional_properties`. The shared helper now sends `model_json_schema()` through `response_json_schema`, as shown in [Google's structured output example](https://ai.google.dev/gemini-api/docs/generate-content/structured-output). Strict validation, including nested extra-field rejection, remains enabled.

The real SDK serializer is covered by an HTTP-transport fixture that reproduced the rejection before the fix. Resume routes return controlled JSON errors for provider failures, and the resume page uses the shared error parser so plain-text HTTP failures cannot become `Unexpected token` errors.

A live check using a synthetic profile, an in-memory database, real Gemini generation and verification, and the isolated compiler returned HTTP 200 with a one-page PDF that passed ATS validation. This follow-up used live provider calls; normal CI continues to use deterministic fixtures.

Follow-up validation: 125 backend tests passed (9 opt-in infrastructure tests skipped), all 6 browser tests passed against the updated production preview, and the production build and frontend/backend health checks passed.

To run browser checks against an existing preview instead of starting a development server, set `PLAYWRIGHT_BASE_URL` to that preview's URL before running `npm run test:browser`.

### Follow-up: explaining rejected personal claims

If both generation attempts fail factual verification, resume routes now include the checker's specific findings in the error shown to the user. A rejection is a model judgment to review, not proof that the profile is wrong. Generated claims continue to be blocked while unsupported.

The generation prompt no longer demands minimum skill counts, lengthy bullets, or filling empty space. Evidence takes priority over Preset length guidance. The bounded repair attempt receives the rejected draft as explicitly untrusted phrasing alongside the findings, while verification continues to receive only the original personal evidence. Regression fixtures cover rejection details reaching the UI and keep failed drafts from reaching compilation.

Validation: 127 deterministic backend tests passed, with the 9 infrastructure checks left opt-in. The local preview uses the existing production frontend with the updated backend.

### Follow-up: Docker-free local development

At the user's request, the environment example and local setup now select native execution explicitly. The running local preview was restarted with `EXECUTION_BACKEND=local`; its backend startup log confirms the mode, and frontend/backend health checks pass. The actual `.env` was not modified.

Validation: 132 deterministic backend tests passed (9 opt-in infrastructure tests skipped). Native Python fixtures cover stdin, exclusion of application secrets, timeout/output bounds, missing compiler behavior and production rejection. Actual native compilation produced one-page PDFs for both Templates with both XeLaTeX and Tectonic, with Docker lookup forbidden by the test harness. These checks establish Docker-free operation, not OS isolation.

Before deployment:

- [ ] Build and provision the sandbox images in the intended runtime environment; run its isolation checks.
- [ ] Apply `python migration.py` to the intended database through the deployment migration process.
- [ ] Run the hosted CI workflows after pushing the changes. The backend workflow now runs deterministic tests and a separate provisioned Postgres/sandbox integration job on pushes and pull requests.
- [ ] Verify provider credentials and normal application smoke checks in the deployment environment.
