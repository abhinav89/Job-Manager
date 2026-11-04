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
