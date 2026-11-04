"""Parse public LinkedIn job pages and collect only where access is permitted."""

import re
from urllib.parse import urlencode, urljoin, urlsplit

from bs4 import BeautifulSoup

from .common import (
    JobSourceError,
    fetch_public_html,
    job_record,
    parse_json_ld_jobs,
    plain_text,
)

SOURCE = "LinkedIn"
BASE_URL = "https://www.linkedin.com"
PAGE_SIZE = 10
MAX_PAGES = 4


def search_url(query: str = "", page: int = 0) -> str:
    params = {
        "keywords": query.strip() or "developer",
        "location": "Philippines",
        "start": page * PAGE_SIZE,
    }
    return f"{BASE_URL}/jobs-guest/jobs/api/seeMoreJobPostings/search?{urlencode(params)}"


def _posting_url(href: str) -> tuple[str, str | None] | None:
    try:
        parsed = urlsplit(urljoin(BASE_URL, href))
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.hostname not in ("linkedin.com", "www.linkedin.com", "ph.linkedin.com"):
        return None
    if not parsed.path.startswith("/jobs/view/"):
        return None
    identity = re.search(r"(?:/view/|-)(\d+)/?$", parsed.path)
    source_id = identity.group(1) if identity else None
    path = f"/jobs/view/{source_id}/" if source_id else parsed.path
    return BASE_URL + path, source_id


def parse_search(html: str) -> list[dict]:
    if re.fullmatch(r"\s*<!DOCTYPE html>\s*<!---->\s*", html, re.IGNORECASE):
        return []
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    seen = set()
    cards = soup.select(".base-search-card, .job-search-card")
    for card in cards:
        title = card.select_one(".base-search-card__title, h3")
        link = card.select_one("a.base-card__full-link, a.base-search-card__full-link, a[href*='/jobs/view/']")
        if not title or not plain_text(str(title)) or not link or not link.get("href"):
            continue
        posting = _posting_url(link["href"])
        if not posting or posting[0] in seen:
            continue
        company = card.select_one(".base-search-card__subtitle, h4")
        location = card.select_one(".job-search-card__location, .job-search-card__location-text")
        salary = card.select_one(".job-search-card__salary-info")
        posted = card.select_one("time[datetime]")
        jobs.append(job_record(
            source=SOURCE,
            job_title=plain_text(str(title)),
            job_url=posting[0],
            company_name=plain_text(str(company)) if company else None,
            location=plain_text(str(location)) if location else None,
            salary_range=plain_text(str(salary)) if salary else None,
            source_job_id=posting[1],
            posted_at=posted.get("datetime") if posted else None,
        ))
        seen.add(posting[0])
    if jobs:
        return jobs
    structured = []
    for item in parse_json_ld_jobs(html, SOURCE):
        posting = _posting_url(item["job_url"])
        if posting:
            item["job_url"], item["source_job_id"] = posting
            structured.append(item)
    if structured:
        return structured
    text = plain_text(html).casefold()
    if any(marker in text for marker in ("no matching jobs found", "no jobs found", "no results found")) or re.search(r"\b0\s+(?:jobs|results)\b", text):
        return []
    if soup.select_one(".authwall, form[action*='/uas/login'], form[action*='/checkpoint/']"):
        raise JobSourceError("blocked", "LinkedIn returned a sign-in or verification page")
    raise JobSourceError("layout_changed", "LinkedIn returned no recognizable job cards or empty-search marker")


def parse_detail(html: str, job: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = plain_text(html).casefold()
    if "this job is no longer available" in text:
        raise JobSourceError("not_found", "LinkedIn job is no longer available")
    result = dict(job)
    structured = parse_json_ld_jobs(html, SOURCE)
    for item in structured:
        posting = _posting_url(item["job_url"])
        same_id = item.get("source_job_id") and item["source_job_id"] == job.get("source_job_id")
        if same_id or posting and posting[0] == job["job_url"]:
            for field in ("company_name", "location", "salary_range", "job_description", "job_type", "posted_at"):
                if item.get(field):
                    result[field] = item[field]
            break
    description = soup.select_one(".show-more-less-html__markup, .description__text, .jobs-description__content")
    if description:
        result["job_description"] = plain_text(str(description))
    if not result.get("job_description"):
        if soup.select_one(".authwall, form[action*='/uas/login'], form[action*='/checkpoint/']"):
            raise JobSourceError("blocked", "LinkedIn returned a sign-in or verification page")
        raise JobSourceError("layout_changed", "LinkedIn job page has no recognizable description")
    for item in soup.select(".description__job-criteria-item"):
        heading = item.select_one(".description__job-criteria-subheader, h3")
        value = item.select_one(".description__job-criteria-text")
        if heading and value and plain_text(str(heading)).casefold() == "employment type":
            result["job_type"] = plain_text(str(value)) or None
    salary = soup.select_one(".compensation__salary, .salary-main-rail__data-body")
    if salary:
        result["salary_range"] = plain_text(str(salary)) or None
    result["short_description"] = result["job_description"][:200]
    return result


async def fetch_jobs(query: str = "", limit: int = 5) -> tuple[list[dict], str]:
    """Collect at most 40 PH listings, preserving access failures."""
    if limit < 1:
        return [], "no_results"
    limit = min(limit, PAGE_SIZE * MAX_PAGES)
    jobs = []
    seen = set()
    incomplete = False
    for page in range(MAX_PAGES):
        try:
            candidates = parse_search(await fetch_public_html(search_url(query, page)))
        except JobSourceError as exc:
            return jobs, "partial" if jobs else exc.status
        if not candidates:
            break
        for job in candidates:
            identity = job.get("source_job_id") or job["job_url"]
            if identity in seen:
                continue
            seen.add(identity)
            try:
                job = parse_detail(await fetch_public_html(job["job_url"]), job)
            except JobSourceError as exc:
                if exc.status == "not_found":
                    continue
                incomplete = True
            jobs.append(job)
            if len(jobs) >= limit:
                return jobs, "partial" if incomplete else "ok"
        if len(candidates) < PAGE_SIZE:
            break
    return jobs, "partial" if incomplete else ("ok" if jobs else "no_results")
