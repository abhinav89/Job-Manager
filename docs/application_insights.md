# Application insights

Open **Insights** in the sidebar, or **Application flow** in the Job Tracker. This optional view reads the same local workspace as the tracker and CLI. It does not change applications or require an AI key.

The Sankey-style chart sends each tracked job to its **current recorded status**. Branch widths represent counts. Selecting a branch filters the searchable application list; selecting it again clears that status filter. Active applications can be opened in the existing tracker.

Archived applications are excluded from the chart by default. **Include archived** adds them to the chart and list. The workspace inventory always includes all records, archived jobs, and all saved draft versions. Follow-ups due include unarchived applications with a scheduled date on or before the viewer's local date, excluding Rejected and Ghosted.

The database does not currently store status-transition history, individual interview rounds, withdrawals, or offer acceptance. The visualization does not infer those events or treat an Offer as an accepted offer. Submission dates are used only when explicitly recorded.

Refresh reloads current data; the page also refreshes every 30 seconds while open. **Download snapshot** saves the displayed data as a local JSON file. It contains application details and workspace counts, so share it deliberately.

For a ready-to-view artifact, ask the agent **“Create a snapshot of my job applications.”** The `cv-snapshot` skill generates an SVG chart, offline HTML report, and source JSON from the selected workspace. It saves new files under the workspace's `snapshots/` directory without changing applications. Agents with a suitable renderer can also provide a PNG.

Agents can retrieve the source data without the dashboard:

```sh
cv-tailor --json applications insights
cv-tailor --json applications insights --include-archived --as-of 2026-11-03
```

Pass `--data-dir` consistently when using a nondefault workspace. The HTTP adapter exposes the same data at `GET /api/tracker/insights`, with optional `include_archived` and `as_of` parameters. No schema changes or status changes are needed.
