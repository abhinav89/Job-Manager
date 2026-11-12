"""
India Job Board Source Feeder.
Extracts verified jobs from the running india-jobboard API (port 8000)
and maps them into the Job-Manager format.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

DEFAULT_INDIA_JOBBOARD_URL = "http://localhost:8000/api/jobs"


def parse_experience_years(exp_str: Optional[str]) -> tuple[int, int]:
    """Parse experience strings like '6-9 years', '5-10 Yrs', '10+ Yrs', '0-2' into (min, max)."""
    if not exp_str:
        return 3, 8
    clean = exp_str.lower()
    range_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', clean)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))
    plus_match = re.search(r'(\d+)\s*\+', clean)
    if plus_match:
        base = int(plus_match.group(1))
        return base, base + 5
    single_match = re.search(r'\b(\d+)\b', clean)
    if single_match:
        val = int(single_match.group(1))
        return val, val + 4
    return 3, 8


def map_india_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map a job record from india-jobboard to Job-Manager IngestJobItem format."""
    title = (raw.get("title") or "Professional Role").strip()
    company = (raw.get("company_name") or "Corporate").strip()
    if company in ["-", "Confidential (iimjobs)", ""]:
        company = "Confidential Employer"

    loc_city = (raw.get("location_city") or "").strip()
    loc_raw = (raw.get("location_raw") or "").strip()
    location = loc_city if loc_city else loc_raw or "India"
    if "india" not in location.lower() and location.lower() not in ["pan india", "remote"]:
        location = f"{location}, India"

    work_mode = (raw.get("work_mode") or "Onsite").strip()
    exp_level = raw.get("experience_level") or ""
    exp_min, exp_max = parse_experience_years(exp_level)

    snippet = (raw.get("snippet") or "").strip()
    apply_url = (raw.get("apply_url") or "").strip()
    source_id = raw.get("source_identifier") or "india_jobboard"

    # Seniority estimation
    title_lower = title.lower()
    if any(k in title_lower for k in ["director", "head", "vp", "avp", "founder", "lead", "principal"]):
        seniority = "Director / Lead"
    elif any(k in title_lower for k in ["senior", "sr", "manager"]):
        seniority = "Senior"
    elif any(k in title_lower for k in ["associate", "analyst", "specialist"]):
        seniority = "Mid"
    else:
        seniority = "Mid"

    # Extract salary if mentioned in snippet (e.g. "6-8 LPA", "₹30-40 Lakhs")
    salary = "Competitive"
    salary_match = re.search(r'(\d+(?:\.\d+)?\s*(?:-|to)\s*\d+(?:\.\d+)?\s*(?:LPA|Lacs|Lakhs|Cr))', snippet, re.IGNORECASE)
    if salary_match:
        salary = f"₹{salary_match.group(1)}"

    # Required skills heuristic extraction
    skills = []
    skill_keywords = [
        "Strategy", "Finance", "Investment Banking", "Private Equity", "Venture Capital",
        "M&A", "Valuation", "Due Diligence", "Financial Modeling", "Corporate Development",
        "P&L", "Revenue Growth", "Operations", "Product Management", "AI", "Machine Learning",
        "Python", "SQL", "FP&A", "Consulting", "Enterprise Sales", "B2B Sales", "GTM",
        "Supply Chain", "HR", "Talent Acquisition", "Risk Management", "Credit"
    ]
    combined_text = f"{title} {snippet}"
    for sk in skill_keywords:
        if re.search(rf'\b{re.escape(sk)}\b', combined_text, re.IGNORECASE):
            skills.append(sk)

    posted_at = raw.get("posted_at")
    date_str = str(posted_at)[:10] if posted_at else "2026-11-12"

    return {
        "company_name": company,
        "job_title": title,
        "job_url": apply_url or "https://dealflow.flowscareers.com",
        "source": f"India Job Board ({source_id})",
        "source_category": "india_jobboard",
        "location": location,
        "work_arrangement": work_mode,
        "job_type": "Full-time",
        "seniority": seniority,
        "experience_years_min": exp_min,
        "experience_years_max": exp_max,
        "salary_range": salary,
        "date_posted": date_str,
        "is_early_applicant": True,
        "required_skills": skills[:8],
        "job_description": snippet or f"{title} at {company}. Verified opportunity from India Job Board.",
    }


def fetch_india_jobboard_jobs(
    base_url: str = DEFAULT_INDIA_JOBBOARD_URL,
    max_pages: Optional[int] = None,
    page_limit: int = 100
) -> List[Dict[str, Any]]:
    """Fetch all verified jobs across pages from the running india-jobboard API."""
    jobs: List[Dict[str, Any]] = []
    try:
        resp = requests.get(f"{base_url}?limit={page_limit}&page=1", timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Failed to connect to india-jobboard on {base_url}: HTTP {resp.status_code}")
            return []

        data = resp.json()
        total = data.get("total", 0)
        total_pages = data.get("total_pages", 1)
        if max_pages:
            total_pages = min(total_pages, max_pages)

        logger.info(f"Connecting to india-jobboard... Found {total} jobs across {total_pages} pages.")

        for p in range(1, total_pages + 1):
            page_resp = requests.get(f"{base_url}?limit={page_limit}&page={p}", timeout=10)
            if page_resp.status_code == 200:
                items = page_resp.json().get("items", [])
                for it in items:
                    jobs.append(map_india_job(it))
                logger.info(f"Fetched page {p}/{total_pages} ({len(items)} jobs, total fetched: {len(jobs)})")
            else:
                logger.warning(f"Error fetching page {p}: HTTP {page_resp.status_code}")

        return jobs
    except Exception as exc:
        logger.error(f"Error communicating with india-jobboard: {exc}")
        return []
