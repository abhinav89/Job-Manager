"""Collect public JobStreet Philippines listings without a signed-in session."""
from __future__ import annotations

import json
import re
from urllib.parse import urlencode, urljoin, urlparse

from bs4 import BeautifulSoup

from .common import JobSourceError, fetch_public_html, job_record, parse_json_ld_jobs, plain_text

SOURCE = "JobStreet PH"
BASE_URL = "https://ph.jobstreet.com"
MAX_PAGES = 3


def search_url(query: str = "", page: int = 1) -> str:
    params = {"keywords": query.strip() or "developer"}
    if page > 1:
        params["page"] = str(page)
    return f"{BASE_URL}/jobs?{urlencode(params)}"


def _job_url(value: str | None) -> tuple[str, str] | None:
    parsed = urlparse(urljoin(BASE_URL, value or ""))
    match = re.match(r"^/job/(\d+)(?:/|$)", parsed.path)
    if parsed.hostname not in {"ph.jobstreet.com", "www.jobstreet.com.ph", "jobstreet.com.ph"} or not match:
        return None
    return f"{BASE_URL}/job/{match.group(1)}", match.group(1)


def _text(container, selector: str) -> str | None:
    element = container.select_one(selector)
    return element.get_text(" ", strip=True) or None if element else None


def _check_page(soup: BeautifulSoup) -> None:
    title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
    if any(marker in title for marker in ("just a moment", "access denied", "security check")) or soup.select_one("#challenge-form, #cf-challenge-running"):
        raise JobSourceError("blocked", "JobStreet returned an access challenge")


def _embedded_jobs(soup: BeautifulSoup) -> list[dict]:
    """Read only job-like records from the page's public hydration data."""
    documents = []
    for script in soup.select("script"):
        raw = script.string or script.get_text()
        if script.get("id") == "__NEXT_DATA__":
            try:
                documents.append(json.loads(raw))
            except (ValueError, TypeError):
                continue
        elif "SEEK_REDUX_DATA" in raw:
            match = re.search(r"(?:window\.)?SEEK_REDUX_DATA\s*=\s*", raw)
            if match:
                try:
                    documents.append(json.JSONDecoder().raw_decode(raw[match.end():])[0])
                except ValueError:
                    continue

    jobs = []

    def visit(value):
        if isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            title, identifier = value.get("title"), value.get("id")
            advertiser = value.get("advertiser")
            if isinstance(title, str) and title.strip() and isinstance(identifier, (str, int)) and str(identifier).isdigit() and isinstance(advertiser, dict):
                locations = value.get("locations") or []
                location = ", ".join(str(loc["label"]) for loc in locations if isinstance(loc, dict) and loc.get("label")) if isinstance(locations, list) else None
                location_data = value.get("location")
                if not location and isinstance(location_data, dict):
                    location = location_data.get("label") or location_data.get("name")
                record = job_record(
                    source=SOURCE, source_job_id=str(identifier),
                    job_title=title.strip(), job_url=f"{BASE_URL}/job/{identifier}",
                    company_name=advertiser.get("description") or advertiser.get("name"),
                    location=location or None, salary_range=value.get("salaryLabel") or None,
                    job_type=value.get("workType") if isinstance(value.get("workType"), str) else None,
                    posted_at=value.get("listingDate") or None,
                )
                record["short_description"] = plain_text(value.get("teaser") or "")
                jobs.append(record)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    visit(child)

    for document in documents:
        visit(document)
    return jobs


def parse_search_results(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    _check_page(soup)
    jobs = []
    for card in soup.select('article[data-testid="job-card"], article[data-job-id], article:has(a[data-automation="jobTitle"])'):
        link = card.select_one('a[data-automation="jobTitle"], a[data-testid="job-title"]')
        target = _job_url(link.get("href")) if link else None
        title = link.get_text(" ", strip=True) if link else ""
        if not target or not title:
            continue
        url, identifier = target
        record = job_record(
            source=SOURCE, source_job_id=identifier, job_title=title, job_url=url,
            company_name=_text(card, '[data-automation="jobCompany"]'),
            location=_text(card, '[data-automation="jobLocation"]'),
            salary_range=_text(card, '[data-automation="jobSalary"]'),
            job_type=_text(card, '[data-automation="jobWorkType"], [data-automation="jobType"]'),
        )
        record["short_description"] = _text(card, '[data-automation="jobShortDescription"]') or ""
        jobs.append(record)
    if not jobs:
        jobs = _embedded_jobs(soup)
    if not jobs:
        for job in parse_json_ld_jobs(html, SOURCE):
            target = _job_url(job.get("job_url"))
            if target:
                jobs.append({**job, "job_url": target[0], "source_job_id": target[1]})
    if jobs:
        return list({job["job_url"]: job for job in jobs}.values())
    text = soup.get_text(" ", strip=True).lower()
    if any(marker in text for marker in ("no jobs found", "no matching jobs", "we couldn't find any jobs", "we couldn’t find any jobs")) or re.search(r"\b0 jobs found\b", text):
        return []
    raise JobSourceError("layout_changed", "JobStreet returned no recognizable listings or empty-results marker")


def parse_job_details(html: str, job: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    _check_page(soup)
    for detail in parse_json_ld_jobs(html, SOURCE):
        target = _job_url(detail.get("job_url"))
        if target and target[0] == job["job_url"] and detail.get("job_description"):
            return {**job, **{key: value for key, value in detail.items() if value is not None and value != ""}, "source_job_id": target[1]}
    description = _text(soup, '[data-automation="jobAdDetails"], [data-testid="job-details"]')
    if description:
        return {**job, "job_description": description, "short_description": description[:200],
                "salary_range": _text(soup, '[data-automation="jobSalary"]') or job.get("salary_range"),
                "job_type": _text(soup, '[data-automation="jobWorkType"], [data-automation="jobType"]') or job.get("job_type")}
    raise JobSourceError("layout_changed", "JobStreet detail page is missing its description")


async def fetch_jobs(query: str = "", limit: int = 5, *, fetch_details: bool = True) -> tuple[list[dict], str]:
    if limit <= 0:
        return [], "no_results"
    limit = min(limit, 50)
    jobs, seen = [], set()
    incomplete = False
    try:
        for page in range(1, MAX_PAGES + 1):
            candidates = parse_search_results(await fetch_public_html(search_url(query, page)))
            fresh = [job for job in candidates if job["job_url"] not in seen]
            if not fresh:
                break
            for job in fresh:
                seen.add(job["job_url"])
                if fetch_details and not job.get("job_description"):
                    try:
                        job = parse_job_details(await fetch_public_html(job["job_url"]), job)
                    except JobSourceError as exc:
                        if exc.status == "not_found":
                            continue
                        incomplete = True
                jobs.append(job)
                if len(jobs) >= limit:
                    return jobs, "partial" if incomplete else "ok"
    except JobSourceError as exc:
        return jobs, "partial" if jobs else exc.status
    return jobs, "partial" if incomplete else ("ok" if jobs else "no_results")
