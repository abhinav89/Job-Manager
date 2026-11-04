"""Explicitly selected PH website JSON search, separate from the HTML collector.

This is JobStreet's website endpoint, not SEEK's partner API. It needs no login,
but is undocumented and disallowed by the site's robots rules for our crawler.
It is therefore excluded from default scans and only runs when selected.
"""
import asyncio
from urllib.parse import urlencode

import httpx

from .common import USER_AGENT, JobSourceError, job_record, plain_text

API_URL = "https://ph.jobstreet.com/api/jobsearch/v5/search"
SOURCE = "JobStreet PH"
MAX_PAGES = 3


def search_url(query="", page=1, page_size=20):
    return f"{API_URL}?{urlencode({'siteKey': 'PH-Main', 'keywords': query.strip() or 'developer', 'pageSize': page_size, 'page': page})}"


def parse_results(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise JobSourceError("layout_changed", "JobStreet JSON search returned an unrecognized response")
    if not payload["data"]:
        if payload.get("totalCount") == 0:
            return []
        raise JobSourceError("layout_changed", "JobStreet returned no records without an explicit empty-search count")
    jobs, seen = [], set()
    for item in payload["data"]:
        if not isinstance(item, dict):
            continue
        identifier = item.get("id")
        title = item.get("title")
        if isinstance(identifier, bool) or not str(identifier or "").isdigit() or not isinstance(title, str) or not title.strip():
            continue
        identifier = str(identifier)
        if identifier in seen:
            continue
        locations = item.get("locations")
        locations = locations if isinstance(locations, list) else []
        # Do not accept accidentally cross-market data under a PH source label.
        countries = {entry.get("countryCode") for entry in locations if isinstance(entry, dict) and entry.get("countryCode")}
        if countries and "PH" not in countries:
            continue
        location = "; ".join(str(entry["label"]) for entry in locations if isinstance(entry, dict) and entry.get("label")) or None
        advertiser = item.get("advertiser")
        advertiser = advertiser if isinstance(advertiser, dict) else {}
        types = item.get("workTypes")
        types = ", ".join(value for value in types if isinstance(value, str)) if isinstance(types, list) else None
        job = job_record(source=SOURCE, source_job_id=identifier, job_title=title,
            job_url=f"https://ph.jobstreet.com/job/{identifier}",
            company_name=advertiser.get("description") or item.get("companyName"),
            location=location, salary_range=item.get("salaryLabel"), job_type=types,
            posted_at=item.get("listingDate"))
        job["short_description"] = plain_text(item.get("teaser"))
        arrangements = item.get("workArrangements")
        if isinstance(arrangements, dict) and isinstance(arrangements.get("data"), list):
            labels = [entry.get("label", {}).get("text") for entry in arrangements["data"]
                      if isinstance(entry, dict) and isinstance(entry.get("label"), dict)]
            job["work_arrangement"] = ", ".join(value for value in labels if isinstance(value, str)) or None
        jobs.append(job)
        seen.add(identifier)
    if not jobs:
        raise JobSourceError("layout_changed", "JobStreet JSON records lacked usable PH job identities")
    return jobs


async def fetch_jobs(query="", limit=5):
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("JobStreet limit must be an integer from 1 to 50")
    page_size = min(limit, 20)
    jobs, seen = [], set()
    async with httpx.AsyncClient(timeout=20, follow_redirects=False,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"}) as client:
        for page in range(1, MAX_PAGES + 1):
            if page > 1:
                await asyncio.sleep(2)
            try:
                response = await client.get(search_url(query, page, page_size))
                if response.status_code == 429:
                    raise JobSourceError("rate_limited", "JobStreet rate-limited the JSON search")
                if response.status_code in {401, 403, 999} or response.is_redirect:
                    raise JobSourceError("blocked", "JobStreet refused the JSON search")
                if response.status_code in {404, 410}:
                    raise JobSourceError("not_found", "JobStreet JSON search is unavailable")
                if response.status_code != 200:
                    raise JobSourceError("network_error", f"JobStreet returned HTTP {response.status_code}")
                if "json" not in response.headers.get("content-type", "").casefold():
                    raise JobSourceError("blocked", "JobStreet returned a non-JSON response")
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise JobSourceError("layout_changed", "JobStreet returned invalid JSON") from exc
                candidates = parse_results(payload)
            except httpx.RequestError:
                return jobs, "partial" if jobs else "network_error"
            except JobSourceError as exc:
                return jobs, "partial" if jobs else exc.status
            fresh = [job for job in candidates if job["source_job_id"] not in seen]
            if not fresh:
                break
            for job in fresh:
                seen.add(job["source_job_id"])
                jobs.append(job)
                if len(jobs) >= limit:
                    return jobs, "ok"
            if len(payload["data"]) < page_size:
                break
            total = payload.get("totalCount")
            if type(total) is int and page * page_size >= total:
                break
    return jobs, "ok" if jobs else "no_results"
