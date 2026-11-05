import asyncio
from urllib.parse import quote_plus, urlsplit, urlunsplit
import re
import json
import httpx
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

_browser_slots = asyncio.Semaphore(2)

# On-site signals used to enforce remote-only filtering.
ONSITE_SIGNALS = ["on-site", "onsite", "on site", "in office", "in-office", "office based", "office-based"]


def _is_remote_posting(text: str) -> bool:
    low = (text or "").lower()
    if any(sig in low for sig in ONSITE_SIGNALS):
        # Allow if it also explicitly says remote/hybrid
        if "remote" in low or "hybrid" in low:
            return True
        return False
    return True


# Retained for callers of the existing optional browser adapter. The new source
# helpers use job_sources.common and do not fall back to this transport.
async def scrape_scrapling(url: str, timeout: int = 25) -> Optional[str]:
    try:
        from scrapling.fetchers import StealthyFetcher
        async with _browser_slots:
            resp = await StealthyFetcher.async_fetch(
                url, headless=True, block_webrtc=True, timeout=timeout
            )
        body = getattr(resp, "body", b"") or b""
        return body.decode("utf-8", errors="ignore") if isinstance(body, bytes) else str(body)
    except Exception as err:
        print(f"[scrapling] fetch failed for {url}: {err}")
        return None


# ── httpx helpers ────────────────────────────────────────────────
async def _httpx_get(url: str, timeout: int = 10) -> Optional[str]:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
        try:
            resp = await client.get(url)
            return resp.text if resp.status_code == 200 else None
        except Exception as err:
            print(f"[httpx] fetch failed for {url}: {err}")
            return None


# ── Source: OnlineJobs.ph (httpx) ────────────────────────────────
async def fetch_onlinejobs_ph(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    search_term = quote_plus(query.strip() or "developer")
    url = f"https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword={search_term}"
    html = await _httpx_get(url)
    if not html:
        return [], "no_results"
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".jobpost-cat-box")
    jobs = []
    for card in cards:
        title_el = card.select_one("h4, h3, h5")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        badge_el = card.select_one(".badge")
        job_type = badge_el.get_text(strip=True) if badge_el else "Full Time"
        if badge_el and badge_el.text in title:
            title = title.replace(badge_el.text, "").strip()
        salary_el = card.select_one("dd")
        salary = salary_el.get_text(strip=True) if salary_el else "Competitive"
        if salary and salary.isdigit():
            salary = f"${salary} / month"
        desc_el = card.select_one(".desc")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        link_el = card.select_one('a[href*="/jobseekers/info/"]') or card.select_one('a[href*="jobseekers"]')
        href = link_el["href"] if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.onlinejobs.ph{href}"
        if not _is_remote_posting(f"{title} {desc}"):
            continue
        jobs.append({
            "company_name": "OnlineJobs Employer",
            "job_title": title or "Position",
            "job_url": href or url,
            "location": "Remote (Philippines / Global)",
            "salary_range": salary,
            "job_description": desc,
            "short_description": (desc[:200] + "...") if len(desc) > 200 else (desc or f"Position for {title}."),
            "job_type": job_type,
            "source": "OnlineJobs.ph",
        })
        if len(jobs) >= limit:
            break
    return jobs, ("ok" if jobs else "no_results")


# ── Website-specific public collectors ──────────────────────────
async def fetch_linkedin_ph(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    from cv_tailor.services.job_sources.linkedin import fetch_jobs
    return await fetch_jobs(query, limit=limit)


# ── Source: RemoteOK (httpx API) ─────────────────────────────────
async def fetch_remoteok_jobs(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    html = await _httpx_get("https://remoteok.com/api")
    if not html:
        return [], "blocked"
    try:
        import json
        raw_jobs = json.loads(html)
        if isinstance(raw_jobs, list) and len(raw_jobs) > 1:
            raw_jobs = raw_jobs[1:]
    except Exception:
        return [], "no_results"
    query_terms = [t.lower() for t in query.strip().split() if t]
    filtered, seen = [], set()
    for job in raw_jobs:
        if not isinstance(job, dict):
            continue
        title = job.get("position", "")
        company = job.get("company", "")
        tags = " ".join(job.get("tags", []))
        desc = job.get("description", "")
        if not _is_remote_posting(f"{title} {tags} {desc}"):
            continue
        search_blob = f"{title} {company} {tags} {desc}".lower()
        if query_terms and not any(term in search_blob for term in query_terms):
            continue
        key = f"{company.lower()}_{title.lower()}"
        if key in seen:
            continue
        seen.add(key)
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        if salary_min and salary_max:
            salary_str = f"${salary_min:,} - ${salary_max:,} / yr"
        elif salary_min:
            salary_str = f"From ${salary_min:,} / yr"
        else:
            salary_str = "Competitive / Unspecified"
        filtered.append({
            "company_name": company or "Remote Company",
            "job_title": title or "Position",
            "job_url": job.get("url") or job.get("apply_url") or "",
            "location": job.get("location") or "Remote",
            "salary_range": salary_str,
            "job_description": desc[:4000] if desc else "",
            "short_description": (desc[:200] + "...") if desc and len(desc) > 200 else (title or ""),
            "job_type": "Full-Time (Remote)",
            "source": "RemoteOK",
        })
        if len(filtered) >= limit:
            break
    return filtered, ("ok" if filtered else "no_results")


# ── Source: WeWorkRemotely (httpx RSS) ───────────────────────────
async def fetch_weworkremotely_jobs(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    html = await _httpx_get("https://weworkremotely.com/remote-jobs.rss")
    if not html:
        return [], "blocked"
    try:
        root = ET.fromstring(html)
    except Exception:
        return [], "no_results"
    query_terms = [t.lower() for t in query.strip().split() if t]
    jobs = []
    for item in root.findall(".//item"):
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        desc = item.find("description").text if item.find("description") is not None else ""
        if not _is_remote_posting(f"{title} {desc}"):
            continue
        search_blob = f"{title} {desc}".lower()
        if query_terms and not any(term in search_blob for term in query_terms):
            continue
        parts = title.split(":", 1)
        company = parts[0].strip() if len(parts) > 1 else "Remote Employer"
        job_title = parts[1].strip() if len(parts) > 1 else title
        soup = BeautifulSoup(desc, "html.parser")
        clean_desc = soup.get_text(strip=True)
        jobs.append({
            "company_name": company,
            "job_title": job_title,
            "job_url": link,
            "location": "Remote (Global)",
            "salary_range": "Competitive",
            "job_description": clean_desc[:4000],
            "short_description": clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc,
            "job_type": "Full-Time (Remote)",
            "source": "WeWorkRemotely",
        })
        if len(jobs) >= limit:
            break
    return jobs, ("ok" if jobs else "no_results")


# ── Source: Remotive (httpx API) ─────────────────────────────────
async def fetch_remotive_jobs(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    url = "https://remotive.com/api/remote-jobs?limit=50"
    if query.strip():
        url += f"&search={query.strip().replace(' ', '%20')}"
    html = await _httpx_get(url)
    if not html:
        return [], "blocked"
    try:
        import json
        data = json.loads(html)
        raw_jobs = data.get("jobs", []) if isinstance(data, dict) else []
    except Exception:
        return [], "no_results"
    jobs = []
    for job in raw_jobs:
        title = job.get("title", "")
        company = job.get("company_name", "")
        desc = job.get("description", "")
        if not _is_remote_posting(f"{title} {desc} {job.get('candidate_required_location','')}"):
            continue
        jobs.append({
            "company_name": company or "Remote Company",
            "job_title": title or "Position",
            "job_url": job.get("url") or "",
            "location": job.get("candidate_required_location") or "Remote",
            "salary_range": job.get("salary") or "Competitive",
            "job_description": desc[:4000] if desc else "",
            "short_description": (desc[:200] + "...") if desc and len(desc) > 200 else (title or ""),
            "job_type": "Full-Time (Remote)",
            "source": "Remotive",
        })
        if len(jobs) >= limit:
            break
    return jobs, ("ok" if jobs else "no_results")


# ── Source: Arbeitnow public job feed ─────────────────────────────
async def fetch_arbeitnow_jobs(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    raw = await _httpx_get("https://www.arbeitnow.com/api/job-board-api")
    if not raw:
        return [], "blocked"
    try:
        data = json.loads(raw)
        postings = data.get("data", []) if isinstance(data, dict) else []
        if not isinstance(postings, list):
            return [], "error"
    except (ValueError, TypeError):
        return [], "error"
    terms = query.casefold().split()
    jobs = []
    for item in postings:
        if not isinstance(item, dict) or item.get("remote") is not True:
            continue
        title = str(item.get("title") or "").strip()
        company = str(item.get("company_name") or "").strip()
        url = str(item.get("url") or "").strip()
        if not title or not company or not url.startswith(("https://", "http://")):
            continue
        description = BeautifulSoup(str(item.get("description") or ""), "html.parser").get_text(" ", strip=True)
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        search_text = " ".join([title, company, description, *[str(tag) for tag in tags]]).casefold()
        if terms and not all(term in search_text for term in terms):
            continue
        job_types = item.get("job_types") if isinstance(item.get("job_types"), list) else []
        jobs.append({
            "company_name": company,
            "job_title": title,
            "job_url": url,
            "location": str(item.get("location") or "Remote; location not specified"),
            "salary_range": "Not specified",
            "job_description": description[:6000],
            "short_description": description[:200],
            "job_type": ", ".join(str(value) for value in job_types) or "Not specified",
            "source": "Arbeitnow",
        })
        if len(jobs) >= limit:
            break
    return jobs, "ok" if jobs else "no_results"


async def fetch_jobstreet_ph(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    from cv_tailor.services.job_sources.jobstreet import fetch_jobs
    return await fetch_jobs(query, limit=limit)


async def fetch_linkedin_guest(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    from cv_tailor.services.job_sources.linkedin_guest import fetch_jobs
    return await fetch_jobs(query, limit=limit)


async def fetch_jobstreet_json(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    from cv_tailor.services.job_sources.jobstreet_json import fetch_jobs
    return await fetch_jobs(query, limit=limit)


async def fetch_indeed_us(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    from cv_tailor.services.job_sources.indeed import fetch_jobs
    return await fetch_jobs(query, limit=limit, country="us")


async def fetch_indeed_ph(query: str = "", limit: int = 5) -> Tuple[List[Dict[str, Any]], str]:
    from cv_tailor.services.job_sources.indeed import fetch_jobs
    return await fetch_jobs(query, limit=limit, country="ph")


# ── Source registry ──────────────────────────────────────────────
SOURCE_REGISTRY = {
    "onlinejobs": ("OnlineJobs.ph", fetch_onlinejobs_ph, "httpx"),
    "linkedin": ("LinkedIn PH", fetch_linkedin_ph, "httpx"),
    "linkedin-guest": ("LinkedIn PH (Guest)", fetch_linkedin_guest, "httpx"),
    "remoteok": ("RemoteOK", fetch_remoteok_jobs, "httpx"),
    "weworkremotely": ("WeWorkRemotely", fetch_weworkremotely_jobs, "httpx"),
    "remotive": ("Remotive", fetch_remotive_jobs, "httpx"),
    "arbeitnow": ("Arbeitnow", fetch_arbeitnow_jobs, "httpx"),
    "jobstreet": ("JobStreet PH", fetch_jobstreet_ph, "httpx"),
    "jobstreet-json": ("JobStreet PH (JSON)", fetch_jobstreet_json, "httpx"),
    "indeed-us": ("Indeed (US)", fetch_indeed_us, "httpx"),
    "indeed-ph": ("Indeed (PH)", fetch_indeed_ph, "httpx"),
}


def default_source_ids():
    """Experimental website endpoints must be explicitly selected."""
    return [key for key in SOURCE_REGISTRY if key not in {"jobstreet-json", "linkedin-guest"}]


async def fetch_remote_jobs(
    query: str = "",
    sources: List[str] = None,
    job_types: List[str] = None,
    limit: int = 15,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Hybrid aggregator. Returns (jobs, source_status)."""
    if limit < 1:
        return [], {}
    requested = list(dict.fromkeys(sources)) if sources is not None else default_source_ids()
    active = [source for source in requested if source in SOURCE_REGISTRY]
    per_source_limit = min(limit, max(4, limit // max(1, len(active))))

    tasks = []
    for s in active:
        _, fn, _ = SOURCE_REGISTRY[s]
        tasks.append(fn(query, limit=per_source_limit))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[Dict[str, Any]] = []
    seen = set()
    source_status: Dict[str, str] = {}
    source_jobs = []

    for s, res in zip(active, results):
        label, _, _ = SOURCE_REGISTRY[s]
        if isinstance(res, Exception):
            source_status[label] = "error"
            continue
        jobs, status = res
        source_status[label] = status
        source_jobs.append(iter(jobs))

    # Interleave providers so the global limit does not hide later sources.
    normalize_type = lambda value: re.sub(r"[\s_-]+", "", value.casefold())
    allowed_types = [normalize_type(t) for t in (job_types or []) if t]
    while source_jobs and len(all_jobs) < limit:
        remaining = []
        for jobs in source_jobs:
            job = next(jobs, None)
            if job is None:
                continue
            remaining.append(jobs)
            if allowed_types and not any(at in normalize_type(job.get("job_type") or "") for at in allowed_types):
                continue
            source = job.get("source") or ""
            if job.get("source_job_id"):
                key = (source, "id", job["source_job_id"])
            elif job.get("job_url"):
                parts = urlsplit(job["job_url"])
                key = (source, "url", urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, "")))
            else:
                key = (source, "title", (job.get("company_name") or "").casefold(), job["job_title"].casefold())
            if key not in seen:
                seen.add(key)
                all_jobs.append(job)
            if len(all_jobs) >= limit:
                break
        source_jobs = remaining

    return all_jobs, source_status
