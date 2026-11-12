from fastapi import APIRouter, Request, UploadFile, File
from cv_tailor import workspace as w
from cv_tailor.models.schemas import UserProfile
from cv_tailor.services.profile_service import PROFILE_LOAD_OPTIONS, serialize_profile

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me")
def load_current_profile():
    try:
        return w.profile_get()
    except w.WorkspaceError as e:
        if getattr(e, "code", None) == "not_found" or e.status == 404:
            return {
                "id": None,
                "revision": 1,
                "first_name": "",
                "last_name": "",
                "mobile_no": "",
                "email": "",
                "linkedin": "",
                "github": "",
                "portfolio": "",
                "preset_slug": "blank",
                "preferred_template": "classic",
                "education": [],
                "experience": [],
                "projects": [],
                "skills": [],
                "certifications": [],
            }
        raise

@router.post("/save")
def save_profile(data: UserProfile):
    return w.profile_save(data.model_dump(), data.revision)

@router.post("/auto-fill-resume")
async def auto_fill_resume(file: UploadFile = File(...)):
    from cv_tailor.config import ai_enabled
    from cv_tailor.services.llm_service import extract_profile_from_resume
    from cv_tailor.services.heuristic_parser import parse_resume_text_heuristic
    from cv_tailor.services.external_work import run_blocking
    from pypdf import PdfReader
    import io

    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not text.strip():
        raise w.WorkspaceError("No selectable text in this PDF. Please ensure the PDF has selectable text.")

    if ai_enabled():
        try:
            parsed = await run_blocking(extract_profile_from_resume, text[:64000])
            return {"status": "success", "data": parsed}
        except Exception:
            pass

    # Heuristic parsing fallback when AI mode is external or API key not set
    parsed = parse_resume_text_heuristic(text)
    return {"status": "success", "data": parsed}
