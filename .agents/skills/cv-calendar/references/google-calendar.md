# Google Calendar

Use official APIs and verify their current requirements when generating the local adapter:

- [Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Calendar scopes](https://developers.google.com/workspace/calendar/api/auth)
- [Create events](https://developers.google.com/workspace/calendar/api/guides/create-events)
- [Event resource, IDs, reminders and private properties](https://developers.google.com/workspace/calendar/api/v3/reference/events)
- [Conditional modifications](https://developers.google.com/workspace/calendar/api/guides/version-resources)

1. Let the user choose an existing writable calendar or approve creating a dedicated CV Tailor calendar. Prefer `calendar.app.created` for app-created secondary calendars; for an existing owned calendar, consider `calendar.events.owned` and only the additional discovery scopes actually needed. Explain the access requested. Do not request Gmail or unrelated Drive access.
2. Prepare installed-app OAuth with a system browser and loopback redirect following current PKCE guidance. Use separate credential keys such as `CV_TAILOR_GOOGLE_CALENDAR_CLIENT_ID`, `CV_TAILOR_GOOGLE_CALENDAR_CLIENT_SECRET`, and `CV_TAILOR_GOOGLE_CALENDAR_REFRESH_TOKEN`. Hidden local input and `save_env_values` handle persistence; do not write downloaded credential/token JSON into the checkout. Refresh tokens at runtime with sanitized errors.
3. Save the selected calendar ID and timezone in nonsecret configuration, and verify authorized access to that specific calendar. Avoid creating a test event merely to test authorization.
4. Derive a deterministic event ID from the stable identity, using allowed base32hex characters (a lowercase SHA-256 hex digest works). Set a private extended property with the identity. On retry, read that ID and verify ownership; handle duplicate-ID responses by retrieving it instead of creating another event. Persist the last managed-field fingerprint and ETag, and use conditional updates to detect races.
5. Use `start.dateTime` / `end.dateTime` with offsets and an IANA timezone for timed events, or `start.date` / exclusive `end.date` for all-day events. Map the chosen reminders with `useDefault: false` and supported overrides, including an empty override list if reminders are disabled. Treat provider limits as validation errors rather than silently changing the choice.
6. Leave attendees empty and do not request conference creation. Publish plain text and preserve content outside a CV Tailor managed description block when updating. Use the actual returned event ID/link when reporting success.
