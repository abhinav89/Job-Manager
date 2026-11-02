from cv_tailor.services.external_work import run_blocking
from cv_tailor.services.snapshots import profile_snapshot, resume_snapshot

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from cv_tailor.database import get_db
from cv_tailor.dependencies import get_workspace_id
from cv_tailor.routers.database_routes import PROFILE_LOAD_OPTIONS
from cv_tailor.models import database_models as db_models
from cv_tailor.models.schemas import GenerateRequest, GenerateCoverLetterRequest, SpotEditRequest
from cv_tailor.services.llm_service import generate_latex_resume, generate_cover_letter, UnsupportedPersonalClaims
from cv_tailor.services.spot_edit_service import rewrite_blocks
from cv_tailor.services.pdf_service import PDFCompilationError, compile_latex_to_pdf, pdf_page_count, apply_single_page_autofit
from cv_tailor.limiter import limiter
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/generate",
    tags=["generate"],
    dependencies=[Depends(get_workspace_id)],
)


def require_one_page(pdf_bytes: bytes) -> None:
    pages = pdf_page_count(pdf_bytes)
    if pages != 1:
        raise HTTPException(
            status_code=422,
            detail=f"Generated resume must be exactly one page; the current output is {pages} pages.",
        )


def get_profile_or_404(db: Session, workspace_id: int) -> db_models.Profile:
    profile = db.query(db_models.Profile).options(*PROFILE_LOAD_OPTIONS).filter(
        db_models.Profile.workspace_id == workspace_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


async def _generate_resume(profile, data: GenerateRequest, preset, history):
    try:
        return await run_blocking(generate_latex_resume, profile, data.jd, data.template_id,
            preset_slug=data.preset_slug, preset_config=preset, historical_evidence=history)
    except HTTPException:
        raise
    except UnsupportedPersonalClaims as exc:
        findings = "; ".join(exc.findings) or "The checker could not identify support for one or more personal claims."
        raise HTTPException(status_code=502, detail="The generated resume still includes claims the checker couldn't support. Claims to review: " + findings) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume generation failed")
        raise HTTPException(status_code=502, detail="The AI service couldn't generate your resume. Please try again.") from exc


@router.get("/templates")
async def get_templates():
    return [
        {
            "id": "classic",
            "name": "Classic Professional",
            "description": "A traditional, single-column layout perfect for corporate and finance roles."
        },
        {
            "id": "modern",
            "name": "Modern Tech",
            "description": "A sleek, contemporary layout with subtle color accents and clean typography."
        }
    ]


class CompileLatexRequest(BaseModel):
    latex: str = Field(min_length=1, max_length=200000)
    auto_fit: bool = False


@router.post("/cv")
@limiter.limit("3/minute")
async def generate_cv(data: GenerateRequest, request: Request, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, get_workspace_id(request))
    plain, preset, history = resume_snapshot(db, profile, data.jd, data.preset_slug)
    latex_code = await _generate_resume(plain, data, preset, history)
    
    return {"latex": latex_code}

@router.post("/pdf")
@limiter.limit("3/minute")
async def generate_pdf(data: GenerateRequest, request: Request, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, get_workspace_id(request))
    plain, preset, history = resume_snapshot(db, profile, data.jd, data.preset_slug)
    latex_code = await _generate_resume(plain, data, preset, history)

    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, latex_code)
    except PDFCompilationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    require_one_page(pdf_bytes)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=tailored_resume.pdf"}
    )


@router.post("/compile")
@limiter.limit("10/minute")
async def compile_latex(data: CompileLatexRequest, request: Request):
    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, data.latex)
    except PDFCompilationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    require_one_page(pdf_bytes)

    return Response(content=pdf_bytes, media_type="application/pdf")

from cv_tailor.services.docx_service import convert_latex_to_docx


@router.post("/export/docx")
@limiter.limit("10/minute")
async def export_docx(data: CompileLatexRequest, request: Request):
    try:
        docx_bytes = await run_blocking(convert_latex_to_docx, data.latex)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {exc}") from exc

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=tailored_resume.docx"}
    )


@router.post("/compile-with-check")
@limiter.limit("10/minute")
async def compile_latex_with_check(data: CompileLatexRequest, request: Request):
    latex_code = data.latex
    auto_fitted = False

    if data.auto_fit:
        latex_code = apply_single_page_autofit(latex_code)
        auto_fitted = True

    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, latex_code)
    except PDFCompilationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    pages = pdf_page_count(pdf_bytes)

    if pages > 1 and not auto_fitted:
        header_fallback = request.headers.get("X-Auto-Fit-Fallback") == "true"
        if data.auto_fit or header_fallback:
            tightened = apply_single_page_autofit(latex_code)
            try:
                pdf_bytes_tight = await run_blocking(compile_latex_to_pdf, tightened)
                pages_tight = pdf_page_count(pdf_bytes_tight)
                pdf_bytes = pdf_bytes_tight
                pages = pages_tight
                latex_code = tightened
                auto_fitted = True
            except Exception:
                pass

    from cv_tailor.services.ats_check import ats_check
    import base64
    ats_result = await run_blocking(ats_check, pdf_bytes, None)
    
    return {
        "pdf_b64": base64.b64encode(pdf_bytes).decode("utf-8"),
        "ats": ats_result,
        "num_pages": pages,
        "auto_fitted": auto_fitted,
        "latex": latex_code if auto_fitted else None
    }


@router.post("/compile-preview")
@limiter.limit("30/minute")
async def compile_latex_preview(data: CompileLatexRequest, request: Request):
    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, data.latex, True)
    except PDFCompilationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    pages = pdf_page_count(pdf_bytes)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": "inline; filename=preview.pdf",
            "X-PDF-Pages": str(pages),
        },
    )

@router.post("/ats-check")
@limiter.limit("5/minute")
async def generate_ats_check(data: GenerateRequest, request: Request, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, get_workspace_id(request))
    plain, preset, history = resume_snapshot(db, profile, data.jd, data.preset_slug)
    latex_code = await _generate_resume(plain, data, preset, history)
    
    try:
        pdf_bytes = await run_blocking(compile_latex_to_pdf, latex_code)
    except PDFCompilationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    require_one_page(pdf_bytes)
        
    preset_section_order = preset.get("section_order") if preset else None
            
    from cv_tailor.services.ats_check import ats_check
    import base64
    ats_result = await run_blocking(ats_check, pdf_bytes, preset_section_order)
    
    return {
        "latex": latex_code,
        "pdf_b64": base64.b64encode(pdf_bytes).decode("utf-8"),
        "ats": ats_result
    }


@router.post("/cover-letter")
@limiter.limit("3/minute")
async def generate_cl(data: GenerateCoverLetterRequest, request: Request, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, get_workspace_id(request))
    plain = profile_snapshot(profile)
    db.rollback()
    cover_letter_content = await run_blocking(generate_cover_letter, plain, data.jd, data.company_name)

    return {"cover_letter": cover_letter_content}


@router.post("/spot-edit")
@limiter.limit("10/minute")
async def spot_edit(data: SpotEditRequest, request: Request, db: Session = Depends(get_db)):
    """Rewrite the selected Blocks only."""
    profile = get_profile_or_404(db, get_workspace_id(request))
    plain = profile_snapshot(profile)
    db.rollback()
    try:
        blocks = await run_blocking(rewrite_blocks, plain, data)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Spot edit failed: {exc}") from exc

    return {"blocks": blocks}
