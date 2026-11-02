# HubSpot

Verify current account capabilities, authentication, and supported API versions:

- Developer documentation: https://developers.hubspot.com/docs
- Deals API: https://developers.hubspot.com/docs/api-reference/crm-deals-v3/guide
- Object availability: https://knowledge.hubspot.com/records/understand-objects

1. Prefer an approved, dedicated job-application deal pipeline when available. Custom objects depend on subscription and permission; never assume access, require a purchase, or repurpose an existing sales pipeline without agreement. Offer another destination if the account cannot represent the tracker safely.
2. Guide the supported private-app or OAuth authorization flow with only required object read/write access. Use `python scripts/integration_env.py set CV_TAILOR_HUBSPOT_TOKEN` for human-entered tokens; OAuth credentials use the shared in-memory helper. Account, pipeline, stage, and property IDs belong in nonsecret config.
3. Inspect actual stage IDs and property types. Map local statuses explicitly; do not invent CRM enum values, contact details, sales amounts, or close dates. Company/contact associations are optional, separate choices.
4. Preserve a stable CV Tailor application key in an approved property and persist the external record ID. Check existing records and conflicts before creating. A delayed search result after a write must not cause another create; use stored IDs and reconcile uncertain results before retrying.
5. Update only approved tracker properties. Preserve sales records, personal notes, owners, and associations. CRM writes may activate workflows: verify the dedicated destination is excluded from unapproved outreach, marketing, notifications, and revenue workflows. Stop if this cannot be established; do not silently change existing automations.
6. Test read access and mapping, then dry-run the first publish. Follow current rate limits and sanitize errors. Use a mapped archive state by default; never move or delete unrelated deals.
