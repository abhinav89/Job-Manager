from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from cv_tailor.routers.database_routes import PROFILE_LOAD_OPTIONS
from cv_tailor.services.snapshots import resume_snapshot, profile_snapshot
from cv_tailor.services.external_work import run_blocking
from cv_tailor.routers.generate_routes import require_one_page
from typing import List
from datetime import date, datetime
from cv_tailor.database import get_db
from cv_tailor.dependencies import get_workspace_id
from cv_tailor.models import database_models as db_models
from cv_tailor.models.schemas import JobApplicationCreate, JobApplicationUpdate
from pydantic import BaseModel as PydanticBaseModel, Field
from cv_tailor.services.pdf_service import PDFCompilationError, compile_latex_to_pdf

router = APIRouter(prefix="/tracker", tags=["tracker"])

from cv_tailor import workspace as w

serialize_job = w.application_dict

def get_job_for_user(db, job_id, workspace_id=1):
    return w.require(db.get(db_models.JobApplication, job_id), "Application")

@router.get("")
def get_all_jobs(status: str | None = None, company: str | None = None, archived: bool | None = None):
    return w.applications_list(status, company, archived)

@router.post("")
def create_job(data: JobApplicationCreate, request: Request):
    return w.application_add(data.model_dump(exclude_unset=True), request.headers.get("Idempotency-Key"))

@router.patch("/{job_id}")
def update_job(job_id: int, data: JobApplicationUpdate, request: Request):
    return w.application_update(job_id, data.model_dump(exclude_unset=True), data.revision, request.headers.get("Idempotency-Key"))

@router.delete("/{job_id}")
def delete_job(job_id: int, revision: int, request: Request):
    return w.application_delete(job_id, revision, request.headers.get("Idempotency-Key"))

@router.get("/stats")
def get_stats():
    return w.application_stats()

@router.get("/insights")
def get_insights(include_archived: bool = False, as_of: date | None = None):
    from cv_tailor.services.application_insights import application_insights
    return application_insights(include_archived, as_of)

@router.get("/{job_id}/details")
def get_job_details(job_id: int):
    return w.application_get(job_id)


class DocumentRevision(PydanticBaseModel):
    content: str = Field(min_length=1, max_length=100000)


@router.get("/{job_id}/documents")
def get_application_documents(job_id: int):
    from cv_tailor.services.application_documents import list_documents
    return list_documents(job_id)


@router.post("/{job_id}/documents/{draft_id}/revise")
def revise_application_document(job_id: int, draft_id: int, data: DocumentRevision, request: Request):
    from cv_tailor.services.application_documents import revise_document
    return revise_document(job_id, draft_id, data.content, request.headers.get("Idempotency-Key"))

# ── PDF + LaTeX endpoints ─────────────────────────────────────────

@router.post("/{job_id}/generate-pdf")
async def generate_pdf_for_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)

    job = get_job_for_user(db, job_id, workspace_id)
    if not job.job_description:
        raise HTTPException(status_code=400, detail="No job description found for this job")

    user = db.query(db_models.Workspace).filter(db_models.Workspace.id == workspace_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    from cv_tailor.services.llm_service import generate_latex_resume

    profile = db.query(db_models.Profile).options(*PROFILE_LOAD_OPTIONS).filter(db_models.Profile.workspace_id == user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — fill in your profile first")

    expected_revision = job.revision
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
    db.rollback()
    db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    job = get_job_for_user(db, job_id, workspace_id)
    w.check_revision(job, expected_revision)
    # 3. Save both LaTeX and PDF to DB
    job.latex_source = latex_code
    job.pdf_data = pdf_bytes
    job.pdf_generated_at = datetime.utcnow()
    job.revision += 1
    db.commit()

    return {"status": "success", "message": "PDF generated and saved"}

@router.post("/{job_id}/generate-cover-letter")
async def generate_cover_letter_for_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)

    job = get_job_for_user(db, job_id, workspace_id)
    if not job.job_description:
        raise HTTPException(status_code=400, detail="No job description found for this job")

    user = db.query(db_models.Workspace).filter(db_models.Workspace.id == workspace_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    from cv_tailor.services.llm_service import generate_cover_letter

    profile = db.query(db_models.Profile).options(*PROFILE_LOAD_OPTIONS).filter(db_models.Profile.workspace_id == user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — fill in your profile first")

    # Generate cover letter
    jd, company = job.job_description, job.company_name
    expected_revision = job.revision
    plain = profile_snapshot(profile)
    db.rollback()
    cover_letter_content = await run_blocking(generate_cover_letter, plain, jd, company)
    job = get_job_for_user(db, job_id, workspace_id)

    # Save to DB
    job.cover_letter = cover_letter_content
    db.commit()

    return {"status": "success", "cover_letter": cover_letter_content}

@router.get("/{job_id}/pdf")
async def get_pdf(job_id: int, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    job = get_job_for_user(db, job_id, workspace_id)
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
    workspace_id = get_workspace_id(request)
    job = get_job_for_user(db, job_id, workspace_id)
    if not job.latex_source:
        raise HTTPException(status_code=404, detail="No CV generated for this job yet")
    return {"latex": job.latex_source, "revision": job.revision}

class SaveLatexRequest(PydanticBaseModel):
    latex: str
    revision: int

@router.patch("/{job_id}/latex")
async def save_latex(job_id: int, data: SaveLatexRequest):
    return await run_blocking(w.save_latex, job_id, data.latex, data.revision)

class FetchJobRequest(PydanticBaseModel):
    url: str

@router.post("/fetch-job-details")
def fetch_job_details(data: FetchJobRequest, request: Request):
    workspace_id = get_workspace_id(request)

    from cv_tailor.services.safe_fetch import fetch_job_text, UnsafeURL
    from cv_tailor.services.llm_service import extract_job_details

    try:
        details = extract_job_details(fetch_job_text(data.url))
        return {"status": "success", "data": details}
    except UnsafeURL as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The job details could not be extracted. Please try again.") from exc
