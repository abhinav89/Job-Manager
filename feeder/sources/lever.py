"""
Lever ATS Public Board Feeder.
Pulls live job postings from companies using Lever.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

DEFAULT_LEVER_COMPANIES = [
    {"name": "Spotify", "token": "spotify"},
    {"name": "Netflix", "token": "netflix"},
    {"name": "Atlassian", "token": "atlassian"},
]


def clean_text(raw: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", raw or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:4000]


def fetch_lever_jobs(company_name: str, token: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Fetch live jobs from Lever postings API."""
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    jobs: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code != 200:
            logger.warning(f"Lever board {token} returned HTTP {resp.status_code}")
            return []

        postings = resp.json()[:limit]

        for p in postings:
            title = p.get("text", "").strip()
            cats = p.get("categories") or {}
            loc = cats.get("location") or "Remote / Flexible"
            workplace_type = cats.get("workplaceType") or "hybrid"
            job_url = p.get("hostedUrl", "")
            desc = clean_text(p.get("descriptionPlain") or p.get("description") or "")

            skills = []
            lower_desc = (title + " " + desc).lower()
            keyword_bank = [
                "Strategy", "Finance", "Analysis", "Consulting", "Management",
                "Python", "SQL", "Excel", "Operations", "Product"
            ]
            for kw in keyword_bank:
                if kw.lower() in lower_desc:
                    skills.append(kw)

            jobs.append({
                "company_name": company_name,
                "job_title": title,
                "job_url": job_url,
                "source": f"Lever ({company_name})",
                "source_category": "lever",
                "location": loc,
                "work_arrangement": "Remote" if "remote" in workplace_type.lower() or "remote" in loc.lower() else "Hybrid",
                "job_type": "Full-time",
                "seniority": "Senior" if any(w in title.lower() for w in ["sr", "senior", "director", "lead"]) else "Mid",
                "experience_years_min": 4,
                "experience_years_max": 8,
                "salary_range": "Competitive",
                "required_skills": skills[:8],
                "job_description": desc[:2500],
            })
    except Exception as e:
        logger.error(f"Error fetching Lever jobs for {company_name}: {e}")

    return jobs
