# GoHighLevel (GHL / HighLevel)

Read the current documentation before choosing API versions, scopes, and required associations:

- Private integrations: https://marketplace.gohighlevel.com/docs/Authorization/PrivateIntegrationsToken/index.html
- Create opportunity: https://marketplace.gohighlevel.com/docs/ghl/opportunities/create-opportunity/index.html

1. Confirm the intended location/sub-account and a dedicated application opportunity pipeline. Discover the actual pipeline/stage IDs and current API availability; agency-level access is not a substitute for the required sub-account context.
2. Guide scoped private-integration or OAuth setup. Hidden personal token entry uses `python scripts/integration_env.py set CV_TAILOR_GHL_TOKEN`; OAuth uses the shared in-memory credential helper. Store location, pipeline, stage, field, and approved association IDs in nonsecret config.
3. Verify required contact associations for the selected API version and account. When a contact is required, have the user choose a real approved existing contact or explicitly approve creation with confirmed details. Never invent contact data or associate an unrelated person. Explain the data model before any write.
4. Maintain one opportunity per CV Tailor application with a stable application key and external ID. Do not assume a provider's contact-based upsert preserves this identity: several applications may share one contact, so contact-only matching can merge distinct applications. Search and reconcile by application identity and stop if safe deduplication is unavailable.
5. Map local statuses to pipeline stages separately from the provider's opportunity status enum. Do not invent accepted statuses, monetary values, or sales fields. Preserve owners, contact details, custom fields, and personal notes outside the approved mapping.
6. Check whether opportunity or contact changes activate campaigns, SMS/email, workflow enrollment, or outreach. Publish only to an approved isolated destination. Never enroll contacts, send messages, toggle automation, or trigger sales actions as a side effect of connecting a job tracker. Stop if those effects cannot be excluded.
7. Verify scoped read access before a dry run and first authorized publish. Respect rate limits, sanitize errors, and retain SQLite on failure. Archive with an approved tracker field/stage by default; do not delete opportunities or contacts.
