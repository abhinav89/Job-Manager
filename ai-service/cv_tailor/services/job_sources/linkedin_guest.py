"""Explicit guest access, outside the normal LinkedIn collector's robots stop.

LinkedIn disallows these paths in robots.txt. This experimental source only runs
when selected, uses no account session, and cannot guarantee keyword relevance.
"""
import asyncio
import time

import httpx

from . import linkedin
from .common import USER_AGENT, JobSourceError, _check_response


async def fetch_jobs(query="", limit=5):
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("LinkedIn limit must be an integer from 1 to 50")
    limit = min(limit, linkedin.PAGE_SIZE * linkedin.MAX_PAGES)
    jobs, seen = [], set()
    incomplete = False
    next_request_at = 0
    async with httpx.AsyncClient(timeout=20, follow_redirects=False,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"}) as client:
        async def fetch(url):
            nonlocal next_request_at
            wait = max(0, next_request_at - time.monotonic())
            if wait:
                await asyncio.sleep(wait)
            # Guest endpoints do not need cookies, including anonymous ones.
            client.cookies.clear()
            try:
                response = await client.get(url)
            except httpx.RequestError as exc:
                raise JobSourceError("network_error", "LinkedIn could not be reached") from exc
            next_request_at = time.monotonic() + 3
            if response.is_redirect:
                raise JobSourceError("blocked", "LinkedIn redirected the guest request")
            _check_response(response)
            if response.status_code != 200:
                raise JobSourceError("layout_changed", "LinkedIn returned no guest HTML")
            return response.text

        for page in range(linkedin.MAX_PAGES):
            try:
                candidates = linkedin.parse_search(await fetch(linkedin.search_url(query, page)))
            except JobSourceError as exc:
                return jobs, "partial" if jobs else exc.status
            fresh = [job for job in candidates if job.get("source_job_id") not in seen]
            if not fresh:
                break
            for job in fresh:
                identifier = job.get("source_job_id")
                if not identifier or not identifier.isdigit():
                    incomplete = True
                    continue
                if identifier in seen:
                    continue
                seen.add(identifier)
                try:
                    html = await fetch(f"{linkedin.BASE_URL}/jobs-guest/jobs/api/jobPosting/{identifier}")
                    job = linkedin.parse_detail(html, job)
                except JobSourceError as exc:
                    if exc.status == "not_found":
                        continue
                    jobs.append(job)
                    if exc.status != "layout_changed":
                        return jobs, "partial"
                    incomplete = True
                else:
                    jobs.append(job)
                if len(jobs) >= limit:
                    return jobs, "partial" if incomplete else "ok"
            if len(candidates) < linkedin.PAGE_SIZE:
                break
    return jobs, "partial" if incomplete else ("ok" if jobs else "no_results")
