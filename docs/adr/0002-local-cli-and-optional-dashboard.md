# Local CLI with optional dashboard

Accepted 2026-11-02.

CV Tailor becomes a single-user application with SQLite storage outside the repository. It no longer operates a hosted account backend. A user may install only the Python CLI or add a static dashboard served by the same Python app. Shared services keep CLI and HTTP behavior consistent.

External coding agents use repository skills, context/schema export, and typed import commands. They handle AI reasoning and writing. Provider-specific SDKs and dashboard dependencies are optional; server-side AI requires explicit opt-in. Users can add the dashboard without moving or recreating data. The public landing page has an independent static build.

SQLite write transactions are short and serialized across processes. Application/profile revisions prevent stale updates; request receipts make identical create/import retries safe. Resumes retain deterministic assembly, page checks, and draft history. Local access checks replace account authentication. Existing hosted data is untouched and no legacy import is included in v1.
