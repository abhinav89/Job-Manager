"""Bounded collection of publicly accessible Indeed job postings."""

import json
import math
import re
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from bs4 import BeautifulSoup

from .common import JobSourceError, fetch_public_html, job_record, parse_json_ld_jobs, plain_text


HOSTS = {"ph": "https://ph.indeed.com", "us": "https://www.indeed.com"}
LABELS = {"ph": "Indeed (PH)", "us": "Indeed (US)"}


def search_url(query: str, country: str = "ph", page: int = 0) -> str:
    if country not in HOSTS:
        raise ValueError("Indeed country must be ph or us")
    return f"{HOSTS[country]}/jobs?{urlencode({'q': query.strip() or 'developer', 'l': 'Philippines' if country == 'ph' else 'United States', 'start': page * 10})}"


def _identity(href: str, key: str | None, country: str, *, allow_key_only: bool = False) -> tuple[str, str | None]:
    href = href.strip()
    if not href and not allow_key_only:
        return "", None
    parsed = urlparse(urljoin(HOSTS[country], href))
    if parsed.scheme != "https" or parsed.netloc.casefold() not in {"ph.indeed.com", "www.indeed.com", "indeed.com"}:
        return "", None
    key = key or parse_qs(parsed.query).get("jk", [None])[0] or parse_qs(parsed.query).get("vjk", [None])[0]
    if key and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", str(key)):
        return f"{HOSTS[country]}/viewjob?{urlencode({'jk': key})}", str(key)
    if parsed.path.startswith(("/viewjob", "/rc/clk", "/pagead/clk")):
        return parsed.geturl(), None
    return "", None


def _text(node) -> str | None:
    return node.get_text(" ", strip=True) or None if node else None


def _embedded_results(soup):
    """Read public job-card state; never execute scripts from a posting."""
    marker = re.compile(r'(?:window\.)?mosaic\.providerData\s*\[\s*["\']mosaic-provider-jobcards["\']\s*\]\s*=\s*')
    for script in soup.find_all("script"):
        raw = script.string or script.get_text()
        match = marker.search(raw)
        if not match:
            continue
        try:
            data, _ = json.JSONDecoder().raw_decode(raw[match.end():])
        except (ValueError, TypeError):
            continue
        model = data.get("mosaicProviderJobCardsModel", {}) if isinstance(data, dict) else {}
        results = model.get("results", []) if isinstance(model, dict) else []
        for result in results if isinstance(results, list) else []:
            if isinstance(result, dict):
                yield result


def parse_search(html: str, country: str = "ph") -> list[dict]:
    if country not in HOSTS:
        raise ValueError("Indeed country must be ph or us")
    soup = BeautifulSoup(html, "html.parser")
    heading = " ".join(node.get_text(" ", strip=True) for node in soup.select("title, h1")).casefold()
    if any(marker in heading for marker in ("access denied", "just a moment", "verify you are human", "additional verification", "security check")) or soup.select_one("#challenge-form, #captcha, .g-recaptcha"):
        raise JobSourceError("blocked", "Indeed returned an access challenge")
    jobs = []
    seen = set()

    def add(record):
        if record.get("job_title") and record.get("job_url") and record["job_url"] not in seen:
            seen.add(record["job_url"])
            jobs.append(record)

    for card in soup.select(".job_seen_beacon, .jobsearch-ResultsList > li, .jobCard"):
        link = card.select_one("a.jcs-JobTitle, h2.jobTitle a, h2 a[href], a[data-jk]")
        if link is None:
            continue
        url, key = _identity(str(link.get("href") or ""), link.get("data-jk") or card.get("data-jk"), country)
        title = str(link.get("title") or _text(link) or "").strip()
        if not title or not url:
            continue
        record = job_record(
            source=LABELS[country], job_title=title, job_url=url, source_job_id=key,
            company_name=_text(card.select_one("[data-testid='company-name'], .companyName")),
            location=_text(card.select_one("[data-testid='text-location'], .companyLocation")),
            salary_range=_text(card.select_one(".salary-snippet-container, .salary-snippet, .salaryOnly")),
            job_type=_text(card.select_one("[data-testid='job-type']")),
        )
        record["short_description"] = _text(card.select_one(".job-snippet, [data-testid='jobsnippet_footer']")) or ""
        add(record)
    for item in _embedded_results(soup):
        url, key = _identity(str(item.get("viewJobLink") or ""), item.get("jobkey") or item.get("jobKey") or item.get("jk"), country, allow_key_only=True)
        title = plain_text(str(item.get("title") or ""))
        if not url or not title:
            continue
        salary = item.get("extractedSalary")
        record = job_record(
            source=LABELS[country], job_title=title, job_url=url, source_job_id=key,
            company_name=plain_text(str(item.get("company") or "")) or None,
            location=plain_text(str(item.get("formattedLocation") or "")) or None,
            salary_range=salary.get("salaryText") if isinstance(salary, dict) else None,
        )
        record["short_description"] = plain_text(str(item.get("snippet") or ""))
        add(record)
    for record in parse_json_ld_jobs(html, LABELS[country]):
        url, key = _identity(record.get("job_url") or "", record.get("source_job_id"), country)
        if url:
            record.update(job_url=url, source_job_id=key)
            add(record)
    if jobs:
        return jobs
    text = soup.get_text(" ", strip=True).casefold()
    if soup.select_one(".jobsearch-NoResult-messageContainer") or any(marker in text for marker in ("did not match any jobs", "no jobs found")) or re.search(r"\b0\s+jobs?\s+found\b", text):
        return []
    raise JobSourceError("layout_changed", "Indeed returned no recognizable jobs or explicit empty-results message")


def parse_detail(html: str, job: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    description = soup.select_one("#jobDescriptionText, #jobDescription, [data-testid='jobDescriptionText']")
    if description is not None and _text(description):
        return {**job, "job_description": description.get_text("\n", strip=True)}
    country = "us" if job["source"] == LABELS["us"] else "ph"
    for record in parse_json_ld_jobs(html, job["source"]):
        url, _ = _identity(record.get("job_url") or "", record.get("source_job_id"), country)
        if url == job["job_url"] and record.get("job_description"):
            return {**job, **{key: value for key, value in record.items() if value is not None and key not in {"job_url", "source_job_id", "source"}}}
    raise JobSourceError("layout_changed", "Indeed job page has no recognizable full description")


async def fetch_jobs(query: str = "", limit: int = 5, *, country: str = "ph", fetch_details: bool = True) -> tuple[list[dict], str]:
    if country not in HOSTS:
        raise ValueError("Indeed country must be ph or us")
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("Indeed limit must be an integer from 1 to 50")
    jobs, seen = [], set()
    status = "ok"
    for page in range(min(3, max(1, math.ceil(limit / 10)))):
        try:
            page_jobs = parse_search(await fetch_public_html(search_url(query, country, page)), country)
        except JobSourceError as exc:
            return jobs, "partial" if jobs else exc.status
        if not page_jobs:
            break
        fresh = [job for job in page_jobs if job["job_url"] not in seen]
        if not fresh:
            break
        for job in fresh:
            seen.add(job["job_url"])
            if fetch_details and not job.get("job_description"):
                try:
                    job = parse_detail(await fetch_public_html(job["job_url"]), job)
                except JobSourceError as exc:
                    if exc.status == "not_found":
                        continue
                    status = "partial"
            jobs.append(job)
            if len(jobs) >= limit:
                return jobs, status
        if len(page_jobs) < 10:
            break
    return jobs, status if jobs else "no_results"
