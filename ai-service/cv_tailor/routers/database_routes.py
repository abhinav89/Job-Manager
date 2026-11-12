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

@router.post("/reset")
def reset_profile():
    """Resets user profile to a clean, fresh state."""
    return w.profile_reset()

@router.post("/auto-fill-resume")
async def auto_fill_resume(file: UploadFile = File(...)):
    from cv_tailor.config import ai_enabled
    from cv_tailor.services.llm_service import extract_profile_from_resume
    from cv_tailor.services.heuristic_parser import parse_resume_text_heuristic
    from cv_tailor.services.external_work import run_blocking
    import io

    filename = (file.filename or "resume.pdf").lower()
    content = await file.read()
    text = ""

    extra_urls = []
    if filename.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        paragraphs.append(row_text)
            text = "\n".join(paragraphs)
        except Exception as exc:
            raise w.WorkspaceError(f"Could not read DOCX document: {exc}")
    else:
        try:
            from cv_tailor.services.pdf_extractor import extract_text_and_urls_from_pdf
            text, pdf_urls = extract_text_and_urls_from_pdf(content)
            if pdf_urls:
                extra_urls.extend(pdf_urls)
        except Exception as exc:
            raise w.WorkspaceError(f"Could not parse PDF file: {exc}")

    if not text.strip():
        raise w.WorkspaceError("No selectable text in this document. Please ensure it contains selectable text.")

    parsed = None
    if ai_enabled():
        try:
            parsed = await run_blocking(extract_profile_from_resume, text[:64000])
        except Exception:
            parsed = None

    if not parsed:
        parsed = parse_resume_text_heuristic(text, extra_urls=extra_urls)
    elif extra_urls:
        if not parsed.get("linkedin"):
            for u in extra_urls:
                if "linkedin.com" in u.lower():
                    parsed["linkedin"] = u
                    break

    # Automatically save parsed profile into the workspace so the app immediately reflects it
    try:
        current = w.profile_get()
        rev = current.get("revision", 1) if isinstance(current, dict) else 1
        saved = w.profile_save(parsed, rev)
        return {"status": "success", "data": saved, "message": "Resume uploaded and profile updated."}
    except Exception:
        return {"status": "success", "data": parsed, "message": "Resume parsed successfully."}
