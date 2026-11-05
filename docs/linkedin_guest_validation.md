# LinkedIn guest validation — November 5, 2026

A bounded live test used ordinary HTTP, the collector's truthful user agent, no
account session, and three-second request spacing. This tests technical access and
record extraction; it does not establish site permission or sustained availability.

| Check | Observed result |
| --- | --- |
| Normal CLI `linkedin` source | No endpoint collection; `robots_disallowed`. |
| Guest search: `python automation`, Philippines | HTTP 200, ten parsed cards. |
| Second page: offset ten | HTTP 200, ten additional IDs, no overlap with the first page. |
| Three selected guest descriptions | HTTP 200; description, employer, location and employment type extracted. Detail headings matched all three search titles. |
| Opt-in CLI `linkedin-guest` source, limit three | Source status `ok`; returned the same three postings with their published descriptions. |
| Second query: `AI automation` | HTTP 200, ten cards with different results. |
| Nonsense query, both plain and quoted | HTTP 200 with unrelated jobs. Strict keyword matching and true empty-search behavior are not verified. |

The first three selected postings were:

| Posting | Employer | Location | Employment type | Salary | Description characters |
| --- | --- | --- | --- | --- | --- |
| [Automation Developer](https://www.linkedin.com/jobs/view/4483082352/) | Convene | Pasig, Philippines | Full-time | Undisclosed | 2,205 |
| [Automation Engineer: AI-Driven Testing & CI/CD](https://www.linkedin.com/jobs/view/4481479824/) | Convene | Pasig, Philippines | Full-time | Undisclosed | 514 |
| [Automation Test Engineer](https://www.linkedin.com/jobs/view/4380444931/) | VALTES Advanced Technology | Makati, Philippines | Full-time | Undisclosed | 1,868 |

The third posting's published date was March 5, 2026. Results must not be described
as newly posted merely because this collector returned them today. Unknown salary
fields remain null, and the collector does not promise remote-only jobs.

## Reproduce

```powershell
.\.venv\Scripts\cv-tailor.exe --json jobs search "python automation" --sources linkedin-guest --limit 3
```

The `linkedin-guest` source is experimental and excluded from default scans. It
reuses the tested LinkedIn parsers, normalizes Philippine posting links, uses
ten-result offsets, fetches descriptions by numeric ID, and stops on access
refusals rather than attempting sign-in or challenge workarounds. The normal
`linkedin` source continues to honor its robots stop.

The fixture suite covers result limits, pacing, absent credentials/cookies,
pagination, repeated-page stopping, deduplication, removed jobs, HTTP failures,
redirect refusals, connection failures, explicit empty HTML and challenge pages.
These controlled cases do not make LinkedIn's live relevance behavior reliable.

LinkedIn documents an [AI-powered job search](https://www.linkedin.com/help/linkedin/answer/a6889044/)
that interprets intent and is replacing classic member search. That documentation
does not establish the semantics of its undocumented guest endpoint; the unrelated
live results above remain an observed limitation rather than an explained guarantee.
