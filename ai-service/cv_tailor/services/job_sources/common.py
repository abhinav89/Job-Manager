"""Small shared transport and record helpers for public job pages."""
import asyncio
import json
import re
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "CVTailorJobCollector/0.1 (public job research)"
ALLOWED_HOSTS = {"www.linkedin.com", "ph.jobstreet.com", "www.indeed.com", "ph.indeed.com"}
_robots_cache = {}
_next_request_at = {}


class JobSourceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def plain_text(value):
    if value is None:
        return ""
    soup = BeautifulSoup(str(value), "html.parser")
    for tag in soup.select("script, style"):
        tag.decompose()
    return re.sub(r"\s+([,.;:!?])", r"\1", soup.get_text(" ", strip=True))


def job_record(*, source, job_title, job_url, company_name=None, location=None,
               salary_range=None, job_description="", job_type=None,
               source_job_id=None, posted_at=None):
    title = plain_text(job_title)
    url = str(job_url or "").strip()
    if not title or urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).hostname:
        raise ValueError("A job needs a title and an absolute posting URL")
    description = plain_text(job_description)
    return {
        "company_name": plain_text(company_name) or None,
        "job_title": title, "job_url": url,
        "location": plain_text(location) or None,
        "salary_range": plain_text(salary_range) or None,
        "job_description": description,
        "short_description": description[:200],
        "job_type": plain_text(job_type) or None,
        "source": source,
        "source_job_id": str(source_job_id) if source_job_id is not None else None,
        "posted_at": str(posted_at) if posted_at is not None else None,
    }


def parse_json_ld_jobs(html, source):
    """Read explicit schema.org JobPosting data; do not infer missing fields."""
    def nodes(value):
        if isinstance(value, list):
            for item in value:
                yield from nodes(item)
        elif isinstance(value, dict):
            kind = value.get("@type", [])
            if kind == "JobPosting" or isinstance(kind, list) and "JobPosting" in kind:
                yield value
            else:
                for item in value.values():
                    if isinstance(item, (list, dict)):
                        yield from nodes(item)

    def place(value):
        if isinstance(value, list):
            return "; ".join(filter(None, (place(item) for item in value)))
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            return ""
        address = value.get("address", value)
        if isinstance(address, str):
            return address
        if not isinstance(address, dict):
            return ""
        parts = [address.get(key) for key in ("addressLocality", "addressRegion", "addressCountry")]
        return ", ".join(str(part.get("name", "") if isinstance(part, dict) else part)
                         for part in parts if part) or str(value.get("name") or "")

    jobs = []
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        for posting in nodes(data):
            organization = posting.get("hiringOrganization")
            organization = organization.get("name") if isinstance(organization, dict) else None
            location = place(posting.get("jobLocation"))
            if posting.get("jobLocationType") == "TELECOMMUTE":
                restrictions = place(posting.get("applicantLocationRequirements"))
                location = "Remote" + (f" ({restrictions or location})" if restrictions or location else "")
            salary = posting.get("baseSalary")
            salary_text = salary if isinstance(salary, str) else None
            if isinstance(salary, dict):
                value = salary.get("value")
                if isinstance(value, dict):
                    amount = value.get("value")
                    prefix = ""
                    if amount is None and value.get("minValue") is not None and value.get("maxValue") is not None:
                        amount = f'{value["minValue"]}–{value["maxValue"]}'
                    elif amount is None and value.get("minValue") is not None:
                        amount, prefix = value["minValue"], "From "
                    elif amount is None and value.get("maxValue") is not None:
                        amount, prefix = value["maxValue"], "Up to "
                    if amount is not None:
                        salary_text = prefix + " ".join(str(part) for part in (salary.get("currency"), amount) if part is not None)
                        if value.get("unitText"):
                            salary_text += f' / {value["unitText"]}'
                elif isinstance(value, (int, float, str)):
                    salary_text = " ".join(str(part) for part in (salary.get("currency"), value) if part is not None)
            identifier = posting.get("identifier")
            if isinstance(identifier, dict):
                identifier = identifier.get("value")
            kind = posting.get("employmentType")
            if isinstance(kind, list):
                kind = ", ".join(str(item) for item in kind)
            try:
                jobs.append(job_record(source=source, job_title=posting.get("title"), job_url=posting.get("url"),
                    company_name=organization, location=location, salary_range=salary_text,
                    job_description=posting.get("description"), job_type=kind,
                    source_job_id=identifier, posted_at=posting.get("datePosted")))
            except ValueError:
                continue
    return jobs


def _check_response(response, *, robots=False):
    if response.status_code == 429:
        raise JobSourceError("rate_limited", "The source rate-limited this request")
    if response.status_code in {401, 403, 999}:
        raise JobSourceError("blocked", "The source refused public access")
    if response.status_code in {404, 410} and not robots:
        raise JobSourceError("not_found", "The posting or search page is unavailable")
    if response.status_code >= 400:
        raise JobSourceError("network_error", f"Source returned HTTP {response.status_code}")
    if urlsplit(str(response.url)).hostname not in ALLOWED_HOSTS:
        raise JobSourceError("blocked", "The source redirected outside its public job site")
    title = BeautifulSoup(response.text, "html.parser").title
    heading = title.get_text(" ", strip=True).casefold() if title else ""
    if any(marker in heading for marker in ("just a moment", "access denied", "security check", "verify you are human")):
        raise JobSourceError("blocked", "The source returned an access challenge")


async def fetch_public_html(url):
    """Fetch an allowed public URL, honoring robots rules and per-host pacing."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS or parts.username or parts.password:
        raise JobSourceError("blocked", "URL is outside the supported public job sources")
    origin = f"https://{parts.hostname}"
    try:
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": USER_AGENT}, follow_redirects=False) as client:
            async def get_public(target, rules=None, delay=2):
                for _ in range(4):
                    if rules is not None and not rules.can_fetch(USER_AGENT, target):
                        raise JobSourceError("robots_disallowed", "The source's robots rules disallow this page")
                    now = time.monotonic()
                    wait = max(0, _next_request_at.get(origin, 0) - now)
                    _next_request_at[origin] = now + wait + delay
                    if wait:
                        await asyncio.sleep(wait)
                    response = await client.get(target)
                    if response.is_redirect:
                        target = urljoin(target, response.headers.get("location", ""))
                        destination = urlsplit(target)
                        if destination.scheme != "https" or destination.hostname != parts.hostname or destination.username or destination.password:
                            raise JobSourceError("blocked", "The source redirected outside the requested host")
                        continue
                    return response
                raise JobSourceError("blocked", "Too many redirects from the source")

            cached = _robots_cache.get(origin)
            robots_fetched = False
            if cached and time.monotonic() - cached[0] < 300:
                rules = cached[1]
            else:
                response = await get_public(f"{origin}/robots.txt")
                rules = RobotFileParser()
                if response.status_code == 404:
                    rules.parse([])
                else:
                    _check_response(response, robots=True)
                    if "<html" in response.text[:1000].casefold():
                        raise JobSourceError("blocked", "Could not read the source's robots rules")
                    rules.parse(response.text.splitlines())
                _robots_cache[origin] = (time.monotonic(), rules)
                robots_fetched = True
            if not rules.can_fetch(USER_AGENT, url):
                raise JobSourceError("robots_disallowed", "The source's robots rules disallow this search")
            delay = max(2, rules.crawl_delay(USER_AGENT) or 0)
            rate = rules.request_rate(USER_AGENT)
            if rate and rate.requests:
                delay = max(delay, rate.seconds / rate.requests)
            if robots_fetched:
                _next_request_at[origin] = max(_next_request_at.get(origin, 0), time.monotonic() + delay)
            response = await get_public(url, rules=rules, delay=delay)
            _check_response(response)
            return response.text
    except httpx.RequestError as exc:
        raise JobSourceError("network_error", "The source could not be reached") from exc
