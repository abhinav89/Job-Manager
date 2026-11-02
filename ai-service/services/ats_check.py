import io
import shutil
import subprocess
from pypdf import PdfReader

def ats_check(pdf_bytes: bytes, preset_section_order: list[str] | None = None) -> dict:
    warnings = []
    extracted_text = ""
    
    # Try pdftotext (poppler)
    has_pdftotext = shutil.which("pdftotext") is not None
    if has_pdftotext:
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        
        try:
            result = subprocess.run(["pdftotext", "-layout", tmp_path, "-"], capture_output=True, text=True, check=True)
            extracted_text = result.stdout
        except Exception as e:
            warnings.append(f"pdftotext failed: {str(e)}; used pypdf fallback — order check less reliable.")
            has_pdftotext = False
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    if not has_pdftotext:
        if not warnings:
            warnings.append("pdftotext (poppler) not found; used pypdf fallback — order check less reliable.")
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            extracted_text = "\n".join(page.extract_text() for page in reader.pages)
        except Exception as e:
            warnings.append(f"Failed to extract text using pypdf: {str(e)}")
            return {"pass": False, "warnings": warnings, "extracted_text": ""}

    import re
    aliases = {"work experience": "experience", "skills": "technical skills", "professional summary": "summary", "profile": "summary"}
    conventional = {"summary", "education", "experience", "projects", "technical skills", "certifications"}
    headings = []
    for line in extracted_text.splitlines():
        heading = re.sub(r"\s+", " ", line).strip().lower()
        heading = aliases.get(heading, heading)
        if heading in conventional:
            headings.append(heading)
    errors = []
    if preset_section_order:
        expected = [aliases.get(h.lower(), h.lower()) for h in preset_section_order]
        optional = {"projects", "certifications"}
        for heading in expected:
            if heading not in conventional:
                errors.append(f"Heading '{heading}' may not be ATS-recognized.")
            elif heading not in headings and heading not in optional:
                errors.append(f"Required heading not found in extracted text: {heading}.")
        present_expected = [h for h in expected if h in headings]
        present_actual = [h for h in headings if h in expected]
        if present_actual != present_expected:
            errors.append(f"Section headings out of order: expected {preset_section_order}.")
    try:
        num_pages = max(1, len(PdfReader(io.BytesIO(pdf_bytes)).pages))
    except Exception:
        num_pages = 1
    if len(re.sub(r"\s+", " ", extracted_text).strip()) < 50 * num_pages:
        errors.append("Very little selectable text extracted; PDF may contain image-based text.")
    if not headings:
        errors.append("No ATS-conventional section headings found on standalone lines.")
    return {"pass": not errors, "warnings": warnings + errors, "extracted_text": extracted_text}
