"""
Feeder API Routes for Job-Manager.
Enables independent feeder scripts, scrapers, and external sources (Greenhouse, Lever, RSS, LinkedIn)
to ingest verified jobs into the Job-Manager central database.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends

from cv_tailor.services.job_repository_service import job_repo_service, compute_job_match
from cv_tailor import workspace as w

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feeder", tags=["feeder"])


class IngestJobItem(BaseModel):
    company_name: str
    job_title: str
    job_url: str
    source: str = "External Feeder"
    source_category: str = "feeder"
    location: str = "Remote / Flexible"
    work_arrangement: str = "Hybrid"
    job_type: str = "Full-time"
    seniority: str = "Mid"
    experience_years_min: Optional[int] = 3
    experience_years_max: Optional[int] = 7
    salary_range: Optional[str] = "Competitive"
    date_posted: Optional[str] = None
    is_early_applicant: bool = False
    required_skills: List[str] = Field(default_factory=list)
    job_description: Optional[str] = None


class BatchIngestPayload(BaseModel):
    source_name: str = "Custom Feeder"
    jobs: List[IngestJobItem]


@router.get("/status")
def feeder_status():
    """Returns feeder engine status, total repository jobs, and tracked companies."""
    jobs = job_repo_service._jobs
    sources = set(j.get("source", "Unknown") for j in jobs)
    return {
        "status": "healthy",
        "total_jobs": len(jobs),
        "total_companies": len(job_repo_service._companies),
        "active_sources": sorted(list(sources)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/jobs/ingest")
def ingest_jobs(payload: BatchIngestPayload):
    """
    Ingest a batch of jobs from an external feeder script.
    Deduplicates against existing listings, calculates fit against active profile,
    and stores in the central jobs repository.
    """
    if not payload.jobs:
        raise HTTPException(status_code=400, detail="Empty jobs payload.")

    profile = None
    try:
        profile = w.profile_get()
    except Exception:
        profile = None

    added = 0
    updated = 0
    results = []

    for item in payload.jobs:
        job_dict = item.model_dump()
        if not job_dict.get("date_posted"):
            job_dict["date_posted"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Compute match analysis
        match = compute_job_match(job_dict, profile)
        job_dict["match_score"] = match["score"]
        job_dict["match_percent"] = match["score_percent"]
        job_dict["match_label"] = match["label"]
        job_dict["match_analysis"] = match

        res = job_repo_service.add_job(job_dict)
        results.append({
            "id": res.get("id"),
            "company_name": res.get("company_name"),
            "job_title": res.get("job_title"),
            "match_score": res.get("match_score"),
        })
        added += 1

    return {
        "status": "success",
        "ingested_count": added,
        "source": payload.source_name,
        "jobs": results,
    }
