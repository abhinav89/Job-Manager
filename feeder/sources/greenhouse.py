"""
Greenhouse ATS Public Board Feeder.
Pulls live job openings from top enterprise companies using Greenhouse ATS.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

DEFAULT_GREENHOUSE_COMPANIES = [
    {"name": "Stripe", "token": "stripe"},
    {"name": "Figma", "token": "figma"},
    {"name": "Databricks", "token": "databricks"},
    {"name": "Cloudflare", "token": "cloudflare"},
    {"name": "Instacart", "token": "instacart"},
]


def clean_html(raw_html: str) -> str:
    """Strip basic HTML tags for clean text."""
    clean = re.sub(r"<[^>]+>", " ", raw_html or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:4000]


def fetch_greenhouse_jobs(company_name: str, token: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Fetch live jobs from Greenhouse board API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    jobs: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code != 200:
            logger.warning(f"Greenhouse board {token} returned HTTP {resp.status_code}")
            return []

        data = resp.json()
        raw_jobs = data.get("jobs", [])[:limit]

        for rj in raw_jobs:
            title = rj.get("title", "").strip()
            loc = (rj.get("location") or {}).get("name", "Remote / Flexible")
            job_url = rj.get("absolute_url", "")
            raw_content = rj.get("content", "")
            cleaned_desc = clean_html(raw_content)

            # Heuristic skills from title and description
            skills = []
            lower_desc = (title + " " + cleaned_desc).lower()
            keyword_bank = [
                "Python", "SQL", "Excel", "Financial Modeling", "Corporate Strategy",
                "FP&A", "Accounting", "React", "TypeScript", "Data Analysis",
                "Product Management", "Operations", "Consulting", "Program Management"
            ]
            for kw in keyword_bank:
                if kw.lower() in lower_desc:
                    skills.append(kw)

            # Work arrangement
            work_arrangement = "Hybrid"
            if "remote" in loc.lower() or "remote" in title.lower():
                work_arrangement = "Remote"

            jobs.append({
                "company_name": company_name,
                "job_title": title,
                "job_url": job_url,
                "source": f"Greenhouse ({company_name})",
                "source_category": "greenhouse",
                "location": loc,
                "work_arrangement": work_arrangement,
                "job_type": "Full-time",
                "seniority": "Senior" if any(w in title.lower() for w in ["senior", "sr", "lead", "director", "head"]) else "Mid",
                "experience_years_min": 5 if any(w in title.lower() for w in ["senior", "lead", "manager"]) else 3,
                "experience_years_max": 8,
                "salary_range": "Competitive Market Rate",
                "required_skills": skills[:8],
                "job_description": cleaned_desc[:2500],
            })
    except Exception as e:
        logger.error(f"Error fetching greenhouse jobs for {company_name}: {e}")

    return jobs
