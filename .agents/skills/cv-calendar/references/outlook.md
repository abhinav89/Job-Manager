# Outlook Calendar

Use Microsoft Graph for personal Outlook and compatible Microsoft 365 user calendars:

- [Register a public client](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [Desktop authorization code flow with PKCE](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)
- [Create calendar events and delegated permissions](https://learn.microsoft.com/en-us/graph/api/calendar-post-events?view=graph-rest-1.0)
- [Event properties, transactionId and reminders](https://learn.microsoft.com/en-us/graph/api/resources/event?view=graph-rest-1.0)
- [Create a stable identity property](https://learn.microsoft.com/en-us/graph/api/singlevaluelegacyextendedproperty-post-singlevalueextendedproperties?view=graph-rest-1.0)
- [Find an event by its identity property](https://learn.microsoft.com/en-us/graph/api/singlevaluelegacyextendedproperty-get?view=graph-rest-1.0)
- [Supported timezones](https://learn.microsoft.com/en-us/graph/api/outlookuser-supportedtimezones?view=graph-rest-1.0)

1. Guide registration of a public desktop client with the intended account audience and delegated `Calendars.ReadWrite`; request offline access only for token refresh. Never request mail-sending or application-wide permissions. Use the system browser and loopback/PKCE flow through a supported OAuth library. Work/school policies can require administrator consent; report that state accurately.
2. Collect values locally. Suggested names are `CV_TAILOR_OUTLOOK_CLIENT_ID`, `CV_TAILOR_OUTLOOK_TENANT_ID`, and `CV_TAILOR_OUTLOOK_TOKEN_CACHE`. A public client has no client secret. If using MSAL, persist its serialized cache directly through `save_env_values` in `.env.integrations`, never as a separate cache file. Persist refreshed cache values the same way and suppress raw authentication errors.
3. Select and verify an editable user calendar, or create a dedicated one only when requested. Save the calendar ID and supported timezone in nonsecret configuration. Use `/me/calendars/{id}/events` to target it explicitly. Group calendars are outside this workflow; their reminder behavior differs.
4. Use a deterministic `transactionId` for create retries and a fixed named single-value extended property carrying the stable CV Tailor identity. Keep the same property-set GUID/name in generated scripts. Before any create, query that property in the selected calendar (following pagination); stop on multiple matches. This lookup recovers a successful write whose local receipt was lost. `transactionId` alone is not a durable replacement for identity lookup and stored event IDs.
5. Persist the returned ID and last managed-field fingerprint, check remote changes before PATCH, and handle conditional-write conflicts without overwriting them. Update only mapped fields; preserve user notes outside a managed body block. Use a text body rather than interpreting job text as HTML.
6. Set `start` and `end` with a Graph-supported timezone, converting IANA identifiers where necessary. An all-day event uses midnight boundaries in the same timezone, `isAllDay: true`, and an exclusive end date. Use `isReminderOn` and `reminderMinutesBeforeStart`; Outlook exposes one reminder lead time, so do not promise multiple alerts. Leave attendees empty and do not enable online meetings. Report the actual returned event ID/link.
