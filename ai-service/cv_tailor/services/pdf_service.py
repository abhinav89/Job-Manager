import os
import io
import re
import logging

logger = logging.getLogger(__name__)

class PDFCompilationError(RuntimeError):
    def __init__(self, message, status_code=422):
        super().__init__(message)
        self.status_code = status_code


def pdf_page_count(pdf_bytes: bytes) -> int:
    from pypdf import PdfReader
    return len(PdfReader(io.BytesIO(pdf_bytes)).pages)


def apply_single_page_autofit(latex_code: str) -> str:
    """
    Applies deterministic LaTeX layout compression rules to ensure the output fits on 1 page.
    """
    # 1. Compress Margins (Geometry)
    if r"\usepackage" in latex_code and "geometry" in latex_code:
        latex_code = re.sub(
            r"\\usepackage\[.*?\]\{geometry\}",
            r"\\usepackage[margin=0.4in,top=0.35in,bottom=0.35in]{geometry}",
            latex_code
        )
    else:
        latex_code = latex_code.replace(
            r"\begin{document}",
            r"\usepackage[margin=0.4in,top=0.35in,bottom=0.35in]{geometry}" + "\n" + r"\begin{document}"
        )

    # 2. Inject Line Spacing Compression
    if r"\linespread" not in latex_code:
        latex_code = latex_code.replace(
            r"\begin{document}",
            r"\linespread{0.93}" + "\n" + r"\begin{document}"
        )

    # 3. Compress Enumitem List Spacing
    enumitem_config = (
        r"\usepackage{enumitem}" + "\n"
        r"\setlist{nosep, topsep=1pt, partopsep=0pt, parsep=0pt, itemsep=1pt, leftmargin=*}" + "\n"
    )
    if r"\usepackage{enumitem}" not in latex_code:
        latex_code = latex_code.replace(r"\begin{document}", enumitem_config + r"\begin{document}")
    elif r"\setlist{nosep" not in latex_code:
        latex_code = latex_code.replace(r"\begin{document}", enumitem_config.split("\n", 1)[1] + r"\begin{document}")

    # 4. Compress Section Title Spacing if titlesec package is used
    if r"\usepackage{titlesec}" in latex_code and r"\titlespacing" not in latex_code:
        title_spacing = r"\titlespacing*{\section}{0pt}{4pt}{2pt}" + "\n"
        latex_code = latex_code.replace(r"\begin{document}", title_spacing + r"\begin{document}")

    return latex_code


def compile_latex_to_pdf(latex: str, fast_preview: bool = False) -> bytes:
    from base64 import b64decode
    from cv_tailor.services.sandbox import run_isolated, SandboxUnavailable
    engine = os.getenv("PDF_LATEX_ENGINE", "tectonic").strip().lower()
    if engine not in {"tectonic", "xelatex"}:
        raise PDFCompilationError("PDF_LATEX_ENGINE must be tectonic or xelatex.")
    try:
        result = run_isolated("pdf", {"latex": latex, "engine": engine}, 120)
        if result.get("error"):
            raise PDFCompilationError(result["error"])
        pdf = b64decode(result["pdf_b64"], validate=True)
        if not pdf.startswith(b"%PDF-"):
            raise PDFCompilationError("The compiler did not return a PDF.")
        return pdf
    except SandboxUnavailable as exc:
        raise PDFCompilationError(str(exc), status_code=503) from exc
    except (TimeoutError, ValueError, KeyError) as exc:
        raise PDFCompilationError(str(exc)) from exc
