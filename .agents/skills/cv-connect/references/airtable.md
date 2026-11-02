# Airtable

Read the current official API and account limits during setup:

- Personal access tokens: https://support.airtable.com/docs/creating-personal-access-tokens
- Web API: https://airtable.com/developers/web/api/introduction
- Scopes: https://airtable.com/developers/web/api/scopes

1. Choose a base and editable application table. A read-only synced table cannot be a publishing destination. Discover actual field IDs and types; reuse approved mappings rather than replacing the schema.
2. Guide scoped personal-token or OAuth setup. Limit access to the chosen base and required operations. Store a personal token through `python scripts/integration_env.py set CV_TAILOR_AIRTABLE_TOKEN`. Keep base/table IDs and field mappings in nonsecret config.
3. Generate a local adapter using current API pagination, batch/rate limits, and retry guidance. Read and update only mapped fields; preserve formulas, linked records, views, and personal fields. Create fields only with approval and the required schema permission.
4. Use a dedicated stable CV Tailor ID field, not company/title, to resolve repeat publishes. Check for duplicate IDs and conflicts before writing. Respect table automations: do not publish into a destination with unapproved side effects.
5. Verify read access first, then dry-run fictional or selected applications before the first authorized publish. Archive using an approved field; do not delete records by default.
