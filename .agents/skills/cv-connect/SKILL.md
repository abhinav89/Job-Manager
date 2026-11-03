---
name: cv-connect
description: Guide optional application-tracking publishing to notes, spreadsheets, Airtable, HubSpot, GoHighLevel (GHL), or another chosen tool. Use when connecting a tracker or CRM, exporting to notes, or configuring integration credentials.
---

# cv-connect

Create a guided, local setup and publishing workflow for the user's chosen tool. SQLite remains the source of truth. This skill supplies the setup process; it does not imply a preconfigured connection or a built-in background sync service.

For Google Calendar or Outlook event publishing, use [cv-calendar](../cv-calendar/SKILL.md). Calendar connections are saved separately and can coexist with the tracking connection.

## Scope and resume

1. Read the root AGENTS.md. Run `cv-tailor --json status` and retain its actual `data_dir`; pass that same `--data-dir` on every subsequent CLI call.
2. Load `cv-tailor --json --data-dir PATH preferences get`. Reuse its `tracking_connection` unless the user chooses another tool. A named provider in the prompt overrides this run's destination. Remember the chosen connection after setup unless the user requests a one-off connection. Ask only for missing destination and field choices.
3. Inspect the saved nonsecret `tracking_connection.config_path` when present; otherwise use the Git-ignored `.cv-tailor-integrations/` directory. Reuse matching scripts and mappings. If a path moved or belongs to another workspace, report it and repair only with the user's chosen destination; do not silently create another external tracker. Credential presence can be checked with `python scripts/integration_env.py status`; never read or print the credential file into model context.
4. Read only the relevant provider reference: [local Markdown / Obsidian](references/markdown.md), [Notion](references/notion.md), [Google Sheets](references/google-sheets.md), [Airtable](references/airtable.md), [HubSpot](references/hubspot.md), or [GoHighLevel / GHL](references/gohighlevel.md). For another tool, verify its current official documentation and capabilities before designing a connector.

## Guided setup

- Explain the short ordered stages, then prepare a cross-platform Python setup script in `.cv-tailor-integrations/`. Reuse the repository's CLI and available Python libraries; add a provider dependency only when needed. No CV Tailor AI API key is required.
- The user runs interactive credential entry in their own terminal. Open official setup URLs before asking them to obtain values. Computer use may guide navigation; credential entry and account authorization stay with the user. Never ask them to paste a token, secret, password, OAuth code, or credential JSON into agent chat.
- Use `python scripts/integration_env.py set CV_TAILOR_PROVIDER_TOKEN` with the actual variable names. Only key names go on the command line. The helper captures values through hidden terminal input and refuses tracked or unignored environment files.
- For OAuth, the human-run local authorization script must pass returned credentials directly in memory to `save_env_values` from `scripts/integration_env.py`. Never print authorization codes, provider token responses, headers, or exception payloads. Persist credentials in `.env.integrations`, not another token file.
- Scripts load `.env.integrations` explicitly with `dotenv_values(path, interpolate=False)`. Keep credentials out of URLs, notes, spreadsheets, exported JSON, generated prompts, logs, and Git. Do not move existing platform-managed credentials into this file.
- Keep nonsecret destination, field mapping, and explicit data directory in a connection-specific JSON file under `.cv-tailor-integrations/`. New connections use the SQLite preference's stable `workspace_uuid`; existing connections retain their saved UUID to avoid duplicating published records. After setup, save `{ "tracking_connection": { "provider": "PROVIDER_ID", "config_path": "ABSOLUTE_JSON_PATH" } }` with `preferences set --revision N --input preferences.json --data-dir PATH` unless the user requested a one-off connection. Use `schema preferences` for provider IDs. Preserve their resume default. Never put credentials in SQLite, preference input, or config JSON. Reuse saved stages without exposing secret values.
- For CRMs, verify the account's object, pipeline, property, and API capabilities before selecting a schema. Use a dedicated approved tracker destination. Explain any automation triggered by writes; stop if isolation from messaging, campaigns, or sales workflows cannot be verified. Never enable, disable, or run unrelated CRM automations to make tracking work.

## Publishing contract

- Obtain application records through `cv-tailor --json --data-dir PATH applications list` / `applications get ID`; never access SQLite directly or replace it with an external store.
- Start with tracking metadata: application ID, company, role, URL, status, dates, and archive state. Notes are an explicit opt-in; profile facts, conversations, credentials, and document contents are not published by default.
- Build a stable external key from the saved workspace UUID and application ID. Upsert that record on retries, including after external row reordering. Preserve unowned fields, personal notes, and records from other tools.
- Generate a dry-run mode showing destinations, fields, and proposed changes without sending application data. Confirm the first publish scope unless the user has already approved it. Existing approved configurations can be reused for later requested publishes.
- Treat unavailable destinations as a retryable publish failure; local applications remain saved and usable. Stop on conflicting edits to managed fields. Do not silently overwrite external edits or implement two-way imports.
- Archive rather than delete external entries by default. Disconnecting removes only the connection, leaving SQLite and external records intact.
- To clear the remembered connection, save `{ "tracking_connection": null }` through the preferences CLI. This does not delete external data, revoke provider credentials, or remove local applications.

## Validate and hand back

Test generated scripts against fictional fixtures, including repeat publishes and preservation of personal notes. Compile/check the scripts without capturing credentials. Perform only the authorized live connection test and publish. Report the saved script path, safe status, and exact rerun command, distinguishing verified actions from steps still awaiting the user. Never claim a connection or publish succeeded without an actual successful result.
