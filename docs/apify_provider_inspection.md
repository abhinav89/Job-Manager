# Public Actor inspection — November 5, 2026

The following established Actors were inspected through their published Store
documentation and unauthenticated Actor metadata. No paid Actor runs, source-code
access controls, account sessions, or private build artifacts were accessed.

| Actor | Public contract observations | Source visibility |
| --- | --- | --- |
| [misceres/indeed-scraper](https://apify.com/misceres/indeed-scraper) | Advertises position, country, location and result-limit inputs. Publishes example job output and an error-item format. | Public metadata reports `isSourceCodeHidden: true`. |
| [bebity/linkedin-jobs-scraper](https://apify.com/bebity/linkedin-jobs-scraper) | Advertises job-search URLs/filters, structured job records, and collection without LinkedIn credentials. | Public metadata reports `isSourceCodeHidden: true`. |
| [curious_coder/linkedin-jobs-scraper](https://apify.com/curious_coder/linkedin-jobs-scraper) | Advertises search URLs or keyword/location inputs, detail extraction, and mapping some legacy filters into search terms. | Public metadata reports `isSourceCodeHidden: true`. |

Metadata was read at `https://api.apify.com/v2/acts/OWNER~ACTOR`. The source-hidden
flag means the public contract does not reveal the implementation, endpoints,
network infrastructure, or site-access behavior. The Store pages make differing
claims about LinkedIn's supported filters. Those claims have not been independently
validated, and no closed-source Actor has been reproduced here. A compatibility
adapter can map public inputs/outputs without claiming to clone the hidden code.

## JobStreet alternative that was actually tested

[Career Ops' provider](https://github.com/career-ops-hq/career-ops/blob/1eaa2038358cdc47cdf82d9236e00d5f7f5d79b7/providers/jobstreet.mjs)
revealed the website JSON search path. Its inspected allowlist does not include
the Philippine hostname. A separate bounded request using `ph.jobstreet.com` and
`siteKey=PH-Main` returned JSON containing Philippine locations, employer names,
job IDs, titles, employment types and advertised salary text.

This proves the PH endpoint returned usable public data from this machine during
the test, without site credentials. It does not prove that these hosted LinkedIn
or Indeed Actors use the same technique. The endpoint is undocumented and the PH
robots rules disallow its path; CV Tailor therefore exposes it only as the
explicitly selected experimental `jobstreet-json` source, outside default scans.

## LinkedIn and Indeed follow-up

The MIT-licensed [JobSpy implementation](https://github.com/speedyapply/JobSpy/tree/68b88d6909a2342ad75fbb945c4204a3a7ed6665/jobspy)
was inspected as an independent open-source reference. It is not the hidden source
of any of the Apify Actors above. No third-party package was installed or executed.

- LinkedIn uses the public guest search endpoint already targeted by our helper.
  A direct, unauthenticated research request for `python automation` in the
  Philippines returned HTTP 200 with ten cards. The first card's guest detail
  endpoint returned HTTP 200 and a 2,205-character description. Our existing detail
  parser recognized the description and explicit full-time employment type.
- Live cards used `ph.linkedin.com` posting links. The helper now accepts this
  exact hostname, normalizes it to `www.linkedin.com`, and uses ten-result offsets.
  Lookalike hostnames remain rejected. JobSpy also reports that logged-out search
  ignores the remote/work-type filter; our helper no longer sends or promises it.
- LinkedIn's robots rules disallow both guest paths for this collector. These
  research requests demonstrate technical availability at the time of the test;
  they do not change the normal helper's robots stop. The separate, explicitly
  selected `linkedin-guest` source now uses those paths; see the
  [live validation](linkedin_guest_validation.md) for its tested behavior and
  keyword-relevance limitation.
- JobSpy's Indeed implementation posts a GraphQL search to
  `https://apis.indeed.com/graphql` with a hardcoded `indeed-api-key` and mobile-app
  headers. A separate request without a key returned HTTP 401 with
  `UNAUTHENTICATED` and `An API Key is required.` The third-party key was not used,
  copied into CV Tailor, or included in research output. This method is therefore
  not evidence of anonymous Indeed access.
- Indeed's [documented integration flow](https://docs.indeed.com/getstarted/integrate-and-call-apis)
  requires a partner app and OAuth credentials. Its example also shows that an
  authenticated client can lack access to the job-retrieval service. A future
  direct adapter needs credentials and search access issued for this integration,
  or a separately configured provider; neither was added in this research pass.

Requests used ordinary HTTP without site sessions, proxies, browser impersonation,
or challenge solving. These small probes do not establish sustained access,
complete search coverage, or production reliability. The existing Indeed HTML
collector still reports its observed refusal rather than returning fabricated jobs.
