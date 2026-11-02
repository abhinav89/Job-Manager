from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from routers.database_routes import PROFILE_LOAD_OPTIONS
from services.snapshots import resume_snapshot, profile_snapshot
from services.external_work import run_blocking
from routers.generate_routes import require_one_page
from typing import List
from datetime import datetime
from database import get_db
from dependencies import get_current_user_id
from models import database_models as db_models
from models.schemas import JobApplicationCreate, JobApplicationUpdate
from pydantic import BaseModel as PydanticBaseModel
from services.pdf_service import PDFCompilationError, compile_latex_to_pdf

router = APIRouter(prefix="/tracker", tags=["tracker"])

def get_job_for_user(db: Session, job_id: int, user_id: int) -> db_models.JobApplication:
    job = db.query(db_models.JobApplication).filter(
        db_models.JobApplication.id == job_id,
        db_models.JobApplication.user_id == user_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def serialize_job(job: db_models.JobApplication, include_details: bool = True) -> dict:
    data = {
        "id": job.id,
        "company_name": job.company_name,
        "job_title": job.job_title,
        "job_url": job.job_url,
        "job_source": job.job_source,
        "is_archived": job.is_archived,
        "short_description": job.short_description,
        "has_pdf": bool(job.has_pdf),
        "pdf_generated_at": job.pdf_generated_at.isoformat() if job.pdf_generated_at else None,
        "status": job.status,
        "date_applied": job.date_applied.isoformat() if job.date_applied else None,
        "follow_up_date": job.follow_up_date.isoformat() if job.follow_up_date else None,
        "job_type": job.job_type,
        "location": job.location,
        "salary_range": job.salary_range,
        "priority": job.priority,
        "template_id": job.template_id or "classic",
    }
    if include_details:
        data.update({
            "job_description": job.job_description,
            "notes": job.notes,
            "cover_letter": job.cover_letter,
        })
    return data


# Lightweight projection for the list view — deliberately excludes job_description,
# notes, cover_letter, latex_source, and pdf_data (large blob columns) so listing
# jobs doesn't pull them for every row. Detail/write endpoints use serialize_job
# on the full ORM object instead.
TRACKER_LIST_COLUMNS = (
    db_models.JobApplication.id,
    db_models.JobApplication.company_name,
    db_models.JobApplication.job_title,
    db_models.JobApplication.job_url,
    db_models.JobApplication.job_source,
    db_models.JobApplication.is_archived,
    db_models.JobApplication.short_description,
    db_models.JobApplication.pdf_data.isnot(None).label("has_pdf"),
    db_models.JobApplication.pdf_generated_at,
    db_models.JobApplication.status,
    db_models.JobApplication.date_applied,
    db_models.JobApplication.follow_up_date,
    db_models.JobApplication.job_type,
    db_models.JobApplication.location,
    db_models.JobApplication.salary_range,
    db_models.JobApplication.priority,
    db_models.JobApplication.template_id,
)

def serialize_job_row(row) -> dict:
    data = dict(row._mapping)
    data["pdf_generated_at"] = data["pdf_generated_at"].isoformat() if data["pdf_generated_at"] else None
    data["date_applied"] = data["date_applied"].isoformat() if data["date_applied"] else None
    data["follow_up_date"] = data["follow_up_date"].isoformat() if data["follow_up_date"] else None
    data["template_id"] = data["template_id"] or "classic"
    return data

@router.get("")
async def get_all_jobs(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    jobs = db.query(*TRACKER_LIST_COLUMNS).filter(
        db_models.JobApplication.user_id == user_id
    ).order_by(db_models.JobApplication.created_at.desc()).all()
    return [serialize_job_row(j) for j in jobs]

@router.post("")
async def create_job(data: JobApplicationCreate, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    job = db_models.JobApplication(user_id=user_id, **data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return serialize_job(job)

@router.patch("/{job_id}")
async def update_job(job_id: int, data: JobApplicationUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    job = get_job_for_user(db, job_id, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return serialize_job(job)

@router.delete("/{job_id}")
async def delete_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    job = get_job_for_user(db, job_id, user_id)
    db.delete(job)
    db.commit()
    return {"status": "success"}

@router.get("/stats")
async def get_stats(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    rows = db.query(
        db_models.JobApplication.status,
        func.count(db_models.JobApplication.id),
    ).filter(
        db_models.JobApplication.user_id == user_id
    ).group_by(db_models.JobApplication.status).all()
    stats = {status: count for status, count in rows}
    return {"total": sum(stats.values()), "by_status": stats}


@router.get("/{job_id}/details")
async def get_job_details(job_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    job = get_job_for_user(db, job_id, user_id)
    return serialize_job(job, include_details=True)

# ── PDF + LaTeX endpoints ─────────────────────────────────────────

@router.post("/{job_id}/generate-pdf")
async def generate_pdf_for_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)

    job = get_job_for_user(db, job_id, user_id)
    if not job.job_description:
        raise HTTPException(status_code=400, detail="No job description found for this job")

    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from services.llm_service import generate_latex_resume

    profile = db.query(db_models.Profile).options(*PROFILE_LOAD_OPTIONS).filter(db_models.Profile.user_id == user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — fill in your profile first")

    # 1. Generate LaTeX
    jd, template, preset_slug = job.job_description, job.template_id or "classic", profile.preset_slug
    plain, preset, history = resume_snapshot(db, profile, jd, preset_slug)
    latex_code = await run_blocking(generate_latex_resume, plain, jd, template_id=template, preset_slug=preset_slug, preset_config=preset, historical_evidence=history)

    # 2. Compile PDF with the Python-managed Tectonic binary
    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, latex_code)
    except PDFCompilationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    require_one_page(pdf_bytes)
    job = get_job_for_user(db, job_id, user_id)
    # 3. Save both LaTeX and PDF to DB
    job.latex_source = latex_code
    job.pdf_data = pdf_bytes
    job.pdf_generated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "PDF generated and saved"}

@router.post("/{job_id}/generate-cover-letter")
async def generate_cover_letter_for_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)

    job = get_job_for_user(db, job_id, user_id)
    if not job.job_description:
        raise HTTPException(status_code=400, detail="No job description found for this job")

    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from services.llm_service import generate_cover_letter

    profile = db.query(db_models.Profile).options(*PROFILE_LOAD_OPTIONS).filter(db_models.Profile.user_id == user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — fill in your profile first")

    # Generate cover letter
    jd, company = job.job_description, job.company_name
    plain = profile_snapshot(profile)
    db.rollback()
    cover_letter_content = await run_blocking(generate_cover_letter, plain, jd, company)
    job = get_job_for_user(db, job_id, user_id)

    # Save to DB
    job.cover_letter = cover_letter_content
    db.commit()

    return {"status": "success", "cover_letter": cover_letter_content}

@router.get("/{job_id}/pdf")
async def get_pdf(job_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    job = get_job_for_user(db, job_id, user_id)
    db.refresh(job, ["pdf_data"])
    if not job.pdf_data:
        raise HTTPException(status_code=404, detail="No PDF found for this job")
    return Response(
        content=job.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={job.company_name}_resume.pdf"}
    )

@router.get("/{job_id}/latex")
async def get_latex(job_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    job = get_job_for_user(db, job_id, user_id)
    if not job.latex_source:
        raise HTTPException(status_code=404, detail="No CV generated for this job yet")
    return {"latex": job.latex_source}

class SaveLatexRequest(PydanticBaseModel):
    latex: str

@router.patch("/{job_id}/latex")
async def save_latex(job_id: int, data: SaveLatexRequest, request: Request, db: Session = Depends(get_db)):
    """Save edited LaTeX back to DB and recompile PDF."""
    user_id = get_current_user_id(request)
    job = get_job_for_user(db, job_id, user_id)

    # External compilation runs without a checked-out DB connection.
    db.rollback()

    # Recompile PDF from new LaTeX
    pdf_updated = False
    compilation_error = None
    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, data.latex)
        require_one_page(pdf_bytes)
        job = get_job_for_user(db, job_id, user_id)
        job.pdf_data = pdf_bytes
        job.pdf_generated_at = datetime.utcnow()
        pdf_updated = True
    except PDFCompilationError as exc:
        compilation_error = str(exc)

    job = get_job_for_user(db, job_id, user_id)
    job.latex_source = data.latex
    db.commit()
    response = {"status": "success", "pdf_updated": pdf_updated}
    if compilation_error:
        response["error"] = compilation_error
    return response

class FetchJobRequest(PydanticBaseModel):
    url: str

@router.post("/fetch-job-details")
def fetch_job_details(data: FetchJobRequest, request: Request):
    user_id = get_current_user_id(request)
    
    from services.safe_fetch import fetch_job_text, UnsafeURL
    from services.llm_service import extract_job_details

    try:
        details = extract_job_details(fetch_job_text(data.url))
        return {"status": "success", "data": details}
    except UnsafeURL as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The job details could not be extracted. Please try again.") from exc
