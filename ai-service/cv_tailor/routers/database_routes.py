from fastapi import APIRouter, Request, UploadFile, File
from cv_tailor import workspace as w
from cv_tailor.models.schemas import UserProfile
from cv_tailor.services.profile_service import PROFILE_LOAD_OPTIONS, serialize_profile

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me")
def load_current_profile():
    return w.profile_get()

@router.post("/save")
def save_profile(data: UserProfile):
    return w.profile_save(data.model_dump(), data.revision)

@router.post("/auto-fill-resume")
async def auto_fill_resume(file: UploadFile = File(...)):
    from cv_tailor.config import require_ai
    from cv_tailor.services.llm_service import extract_profile_from_resume
    from cv_tailor.services.external_work import run_blocking
    from pypdf import PdfReader
    import io
    require_ai()
    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(await file.read())).pages)
    if not text.strip():
        raise w.WorkspaceError("No selectable text in this PDF. Use your CLI agent's OCR or supply text.")
    return {"status": "success", "data": await run_blocking(extract_profile_from_resume, text[:64000])}
