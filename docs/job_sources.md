# Job source helpers

The CLI, dashboard Discover page, and career agent use the same source registry.
LinkedIn, JobStreet Philippines, and Indeed Philippines/US each have a helper in
`ai-service/cv_tailor/services/job_sources/`. These are local Python collectors,
not deployed Apify Actors. No account, API key, dashboard server, or AI call is needed.

Run a bounded public search from the repository:

```powershell
.\.venv\Scripts\cv-tailor.exe --json jobs search "python automation" --sources linkedin,jobstreet,indeed-ph --limit 3
```

Use `indeed-us` for Indeed US. Include `onlinejobs` or other existing source IDs
in the comma-separated list to search them in the same run. `--limit` accepts 1–50
and limits the total returned jobs; each helper also caps its pages and detail requests.

The new helpers parse public HTML and embedded job data, preserve source IDs and
posting URLs, and enrich selected results with complete descriptions when accessible.
Missing employers, salaries, employment types, and locations remain unknown.
Preview text is separate from a complete description. Search itself does not save an
application or submit anything. The Discover page's Save action needs a known employer.

The shared transport checks robots.txt, paces requests, and reports refused access
without treating it as an empty search. It does not use sign-in cookies, stealth
browsers, proxy rotation, or challenge bypasses. Source output has a `sources` map:

| Status | Meaning |
| --- | --- |
| `ok` | Recognizable postings were collected. |
| `no_results` | The source explicitly reported an empty search. |
| `partial` | Previews/results are available but a page or selected description failed. |
| `robots_disallowed` | The source disallows the requested path for this collector. |
| `blocked` | The source returned an access refusal or verification challenge. |
| `rate_limited` | The source returned HTTP 429. |
| `layout_changed` | The response could not be recognized as postings or a genuine empty search. |
| `network_error` | A connection or other HTTP failure prevented collection. |
| `not_found` | A requested search page is unavailable. Removed detail postings are skipped. |

These statuses describe this run, not whether the website has matching jobs.
Public access can vary; fixture tests verify parsing and failure handling, not live availability.

Run parser, transport, and integration tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest ai-service/tests/test_linkedin_job_source.py ai-service/tests/test_jobstreet_job_source.py ai-service/tests/test_indeed_job_source.py ai-service/tests/test_job_source_common.py ai-service/tests/test_scraper_routes.py
```
