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

LinkedIn's logged-out search uses ten-result pages. Philippine posting links are
normalized to the main LinkedIn hostname. The helper does not promise remote-only
results: the logged-out endpoint's work-type filter is not reliable. A bounded
research probe returned search cards and a full guest description without a login,
but the normal helper still stops because LinkedIn's robots rules disallow these
paths. See the provider inspection below for the separate Indeed API finding.

## Experimental LinkedIn Philippines guest source

Select `linkedin-guest` explicitly in CLI/agent sources or choose **LinkedIn PH guest
(experimental)** in Discover. It is excluded from default CLI and HTTP scans and
unselected by default in the dashboard.

```powershell
.\.venv\Scripts\cv-tailor.exe --json jobs search "python automation" --sources linkedin-guest --limit 3
```

This source reads public guest search and description endpoints without account
credentials or cookies. LinkedIn's robots rules disallow these paths: selecting
this experimental source makes direct requests outside the normal `linkedin`
helper's robots stop. That normal helper remains unchanged in its access policy.
Requests are sequential, spaced three seconds apart, and bounded to four search
pages of ten cards each and at most forty selected descriptions. Redirects, access
refusals and rate limits stop collection; available previews remain marked partial.

The published description is extracted when available. Undisclosed salaries stay
unknown, removed detail pages are skipped, and duplicate posting IDs are collected
once. This does not log in, submit applications, or retrieve external apply URLs.

**Keyword relevance is not guaranteed.** Live tests returned unrelated jobs even
for a nonsense term enclosed in quotes. The source preserves LinkedIn's response;
it does not invent a strict keyword filter or treat those recommendations as an
empty search. Discover shows this limitation. Remote-only filtering is unavailable,
and listings may be old. Review each posting before saving or applying.

See [the live validation](linkedin_guest_validation.md) for the tested output and
the distinction between successful extraction and unverified search relevance.

## Experimental JobStreet Philippines JSON source

An explicitly selected `jobstreet-json` source reads the website's
`https://ph.jobstreet.com/api/jobsearch/v5/search` endpoint with `siteKey=PH-Main`.
This is distinct from SEEK's documented partner API. A local unauthenticated probe
on November 5, 2026 returned HTTP 200 and PH listings, including advertised salary
text. Availability can change and is not guaranteed by a supported API contract.

```powershell
.\.venv\Scripts\cv-tailor.exe --json jobs search "python automation" --sources jobstreet-json --limit 2
```

This route must be selected explicitly in the CLI/agent sources or the Discover
page's experimental JobStreet option; it is excluded from default scans. The
website's robots rules disallow this API path for the collector. Selecting this
experimental source makes direct unauthenticated JSON requests; it does not apply
the HTML collector's robots stop. The existing `jobstreet` HTML source and its
robots checks are unchanged. No credentials, proxy rotation, challenge bypasses, or
supplied sign-in cookies are used. Requests are bounded, paginated sequentially, and spaced two
seconds apart after the first page; a refusal or rate limit stops collection.

The search API provides preview text, which stays in `short_description`;
`job_description` stays empty until a full description is available. Save to
Tracker remains available for a known employer; tailoring requires a description.
See [the provider inspection](apify_provider_inspection.md) for the public Actor
contracts inspected alongside this experiment.

Run parser, transport, and integration tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest ai-service/tests/test_linkedin_job_source.py ai-service/tests/test_linkedin_guest_source.py ai-service/tests/test_jobstreet_job_source.py ai-service/tests/test_indeed_job_source.py ai-service/tests/test_job_source_common.py ai-service/tests/test_scraper_routes.py
```
