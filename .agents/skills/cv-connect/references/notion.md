# Notion

Read the current official documentation when setting up; do not guess API versions, dashboard clicks, database/data-source identifiers, or permission requirements.

- Authorization: https://developers.notion.com/guides/get-started/authorization
- API: https://developers.notion.com/reference/intro

1. Ask for the chosen workspace and tracking destination. Prefer a dedicated tracker and explicitly mapped properties. Access is limited to the user-selected pages/data source.
2. Guide the user through the appropriate internal connection or OAuth flow. For a personal token-based connection, hidden entry can use `python scripts/integration_env.py set CV_TAILOR_NOTION_TOKEN`. The user runs this command; the agent does not collect its input. Keep destination IDs in the nonsecret config.
3. Generate a local Python adapter that loads the token at runtime from `.env.integrations`, sends it in an authorization header, and reports sanitized errors. Pin the verified API version in that adapter.
4. Use a stable CV Tailor ID property to find and update the same application page. Handle pagination and provider retry instructions; never match only on company/title or treat a rate limit as a missing record.
5. Change only mapped tracker properties or an explicitly managed content block. Preserve personal page content, custom properties, and user edits; archive only under the publishing contract.
6. Test property discovery/read access first. Dry-run the selected application fields before the first authorized publish. Report the actual tracker URL and verified result without printing tokens or raw token responses.
