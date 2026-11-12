from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from cv_tailor.database import get_db
from cv_tailor.dependencies import get_workspace_id
from cv_tailor.models import database_models as db_models
from cv_tailor.services.job_scraper_service import fetch_remote_jobs, default_source_ids
from cv_tailor.services.job_repository_service import job_repo_service, compute_job_match
from cv_tailor import workspace as w

router = APIRouter(prefix="/scraper", tags=["scraper"])

class ImportJobRequest(BaseModel):
    company_name: str
    job_title: str
    job_url: Optional[str] = ""
    source: Optional[str] = ""
    job_description: Optional[str] = ""
    short_description: Optional[str] = ""
    location: Optional[str] = None
    salary_range: Optional[str] = ""
    job_type: Optional[str] = None
    status: Optional[str] = "To Review"
    priority: Optional[str] = "Medium"
    match_score: Optional[int] = None
    match_analysis: Optional[Dict[str, Any]] = None

class ParseJobRequest(BaseModel):
    url: Optional[str] = ""
    job_text: Optional[str] = ""
    company_name: Optional[str] = ""
    job_title: Optional[str] = ""


@router.get("/companies")
def get_tracked_companies():
    """Return the master list of tracked companies, career pages, and ATS types."""
    return {
        "status": "success",
        "companies": job_repo_service.list_companies()
    }


@router.get("/jobs")
def get_repository_jobs(
    keyword: Optional[str] = None,
    location: Optional[str] = None,
    work_model: Optional[str] = None,
    seniority: Optional[str] = None,
    company: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    request: Request = None,
):
    """
    Search and filter jobs from the central repository.
    Calculates transparent match scores and evidence against the current user profile.
    """
    profile = None
    try:
        profile = w.profile_get()
    except Exception:
        pass

    jobs = job_repo_service.list_jobs(
        query=keyword,
        location=location,
        work_model=work_model,
        seniority=seniority,
        company=company,
        source=source,
        min_score=min_score,
        profile=profile,
    )

    return {
        "status": "success",
        "total": len(jobs),
        "jobs": jobs,
        "filters_applied": {
            "keyword": keyword,
            "location": location,
            "work_model": work_model,
            "seniority": seniority,
            "company": company,
            "source": source,
            "min_score": min_score,
        }
    }


@router.post("/parse-url")
def parse_job_url_or_text(payload: ParseJobRequest, request: Request):
    """
    Manual intake helper: parses provided URL or raw JD text, extracts metadata,
    and returns structured job details with profile fit analysis.
    """
    text = (payload.job_text or "").strip()
    url = (payload.url or "").strip()
    company = (payload.company_name or "").strip()
    title = (payload.job_title or "").strip()

    if not text and not url:
        raise HTTPException(status_code=400, detail="Please provide either a job URL or job description text.")

    # Basic heuristic extraction if title/company not provided
    if not title and text:
        first_line = text.split("\n")[0][:80].strip()
        title = first_line or "Job Opening"
    elif not title and url:
        # derive from url slug
        slug = url.split("?")[0].rstrip("/").split("/")[-1].replace("-", " ").title()
        title = slug or "Target Role"

    if not company:
        if "deloitte" in url.lower():
            company = "Deloitte"
        elif "mckinsey" in url.lower():
            company = "McKinsey"
        elif "greenhouse" in url.lower() or "lever" in url.lower():
            parts = url.replace("https://", "").replace("http://", "").split("/")
            company = parts[1].replace("-", " ").title() if len(parts) > 1 else "Employer"
        elif "linkedin" in url.lower():
            company = "LinkedIn Employer"
        else:
            company = "Target Company"

    profile = None
    try:
        profile = w.profile_get()
    except Exception:
        pass

    job_obj = {
        "company_name": company,
        "job_title": title,
        "job_url": url,
        "source": "Manual Intake / URL",
        "job_description": text or f"Direct job intake from {url}",
        "short_description": text[:200] if text else f"Opening at {company}",
        "location": "Location upon review",
        "work_arrangement": "Hybrid / Review",
        "job_type": "Full-time",
        "seniority": "Senior",
        "salary_range": "Competitive",
    }

    match_analysis = compute_job_match(job_obj, profile)
    job_obj["match_score"] = match_analysis["score"]
    job_obj["match_analysis"] = match_analysis

    return {
        "status": "success",
        "job": job_obj
    }


@router.get("/discover")
async def discover_jobs(
    keyword: Optional[str] = None,
    preset_slug: Optional[str] = None,
    sources: Optional[str] = None,
    job_types: Optional[str] = None,
    request: Request = None,
):
    get_workspace_id(request)

    active_preset = preset_slug.strip() if preset_slug and preset_slug.strip() else ""
    search_keyword = keyword.strip() if keyword and keyword.strip() else active_preset.replace("-", " ")
    if not search_keyword or search_keyword == "blank":
        search_keyword = "remote developer"

    source_list = (
        [s.strip() for s in sources.split(",") if s.strip()]
        if sources is not None
        else default_source_ids()
    )
    type_list = [t.strip() for t in job_types.split(",") if t.strip()] if job_types else []

    raw_jobs, source_status = await fetch_remote_jobs(
        query=search_keyword,
        sources=source_list,
        job_types=type_list,
        limit=12
    )

    return {
        "search_keyword": search_keyword,
        "active_preset": active_preset,
        "source_status": source_status,
        "total": len(raw_jobs),
        "jobs": raw_jobs
    }


@router.post("/import")
async def import_scraped_job(payload: ImportJobRequest, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    
    new_job = db_models.JobApplication(
        workspace_id=workspace_id,
        company_name=payload.company_name,
        job_title=payload.job_title,
        job_url=payload.job_url,
        job_source=payload.source or None,
        job_description=payload.job_description,
        short_description=payload.short_description or (payload.job_description[:200] if payload.job_description else ""),
        location=payload.location,
        salary_range=payload.salary_range or "",
        job_type=payload.job_type,
        status=payload.status or "To Review",
        priority=payload.priority or "Medium",
        match_score=payload.match_score,
        match_analysis=payload.match_analysis
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return {
        "status": "success",
        "job_id": new_job.id,
        "message": f"Job saved to tracker under '{new_job.status}'"
    }
