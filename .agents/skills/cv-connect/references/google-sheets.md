# Google Sheets

Use the official API for publishing. Computer use can help navigate setup, but routine spreadsheet updates should not depend on browser clicks.

- Desktop OAuth: https://developers.google.com/identity/protocols/oauth2/native-app
- Scopes: https://developers.google.com/workspace/sheets/api/scopes
- Sheets API: https://developers.google.com/workspace/sheets/api/guides/concepts

1. Choose a spreadsheet and dedicated tracker tab, or create one with the user's approval. Map existing headers instead of overwriting the file.
2. Generate a human-run local OAuth setup script following current installed-app guidance. Use the system browser and appropriate loopback/PKCE flow; never collect the Google password or authorization code in chat. Explain the requested scopes, preferring file-scoped access where supported by the chosen creation/selection flow.
3. Capture client credentials locally and store any client secret and returned refresh token using `save_env_values` from `scripts/integration_env.py`. Suggested keys are `CV_TAILOR_GOOGLE_CLIENT_ID`, `CV_TAILOR_GOOGLE_CLIENT_SECRET`, and `CV_TAILOR_GOOGLE_REFRESH_TOKEN`. Do not persist a separate credential/token JSON in the checkout or print token responses. The spreadsheet ID belongs in the nonsecret config.
4. Generate the publishing adapter with runtime token refresh and sanitized errors. Avoid requesting unrelated Drive or Gmail access.
5. Keep a stable CV Tailor ID column and find rows by that ID every run, so sorting does not change the target. Update only mapped columns; retain custom columns, formulas, and user notes.
6. Send imported text using `valueInputOption=RAW` so job text cannot become a spreadsheet formula. Handle retryable failures without duplicating rows or disturbing SQLite.
7. Verify authorized spreadsheet access, then preview field mapping and proposed writes before the first publish. Repeated syncs must update the same rows.
