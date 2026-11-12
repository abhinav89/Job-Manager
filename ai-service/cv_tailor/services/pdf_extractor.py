"""
Advanced Multi-Column PDF Extractor for DealOS Job Manager.

Detects column gutters, headers, and sidebars using exact word bounding boxes,
preventing cross-column text interweaving that destroys resume experience and section parsing.
"""

from typing import List, Tuple, Dict, Any, Optional
import io
import re

def extract_text_and_urls_from_pdf(content: bytes) -> Tuple[str, List[str]]:
    """
    Extracts text from a PDF with layout-aware multi-column boundary detection,
    and returns (text, extra_urls).
    """
    extra_urls: List[str] = []

    # 1. Extract URLs from PDF annotations using pypdf
    try:
        from pypdf import PdfReader
        pypdf_reader = PdfReader(io.BytesIO(content))
        for page in pypdf_reader.pages:
            if "/Annots" in page:
                annots = page["/Annots"]
                if annots:
                    for a in annots:
                        try:
                            obj = a.get_object() if hasattr(a, "get_object") else a
                            if "/A" in obj and "/URI" in obj["/A"]:
                                url = obj["/A"]["/URI"]
                                if url and isinstance(url, str) and url.startswith("http"):
                                    extra_urls.append(url)
                        except Exception:
                            continue
    except Exception:
        pass

    # 2. Layout-aware text extraction using pdfplumber with column boundary detection
    text_parts: List[str] = []
    used_pdfplumber = False

    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = _extract_page_with_column_detection(page)
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())
            used_pdfplumber = True
    except Exception:
        used_pdfplumber = False

    # 3. Fallback to pypdf if pdfplumber is unavailable or returned empty
    if not used_pdfplumber or not "".join(text_parts).strip():
        text_parts = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    text_parts.append(t.strip())
        except Exception:
            pass

    full_text = "\n\n".join(text_parts)
    return full_text, extra_urls


def _extract_page_with_column_detection(page) -> str:
    """
    Analyzes word coordinates on a PDF page to detect column boundaries and gutters.
    If multiple columns exist, extracts columns separately to prevent line interweaving.
    """
    try:
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=True
        )
    except Exception:
        return page.extract_text() or ""

    if not words:
        return page.extract_text() or ""

    width = float(page.width)
    height = float(page.height)

    # Detect header zone (top 15-20% where name and contact details usually reside)
    # Check if top words span across wide center
    header_threshold = min(120.0, height * 0.18)
    
    # Body words
    body_words = [w for w in words if w["top"] >= header_threshold]
    
    if len(body_words) < 25:
        # Too sparse to be a multi-column body, use standard extraction
        return page.extract_text() or ""

    # Check for a vertical gutter between 20% and 80% of page width
    # In a multi-column document, there is a horizontal gap with zero word overlaps
    min_x_check = width * 0.18
    max_x_check = width * 0.82

    # Find the right edge of words on left, and left edge of words on right
    # Scan potential split lines at 2pt increments
    best_split = None
    max_gutter_width = 0.0

    # Sort body words by left edge
    x_step = 4.0
    current_x = min_x_check
    
    while current_x <= max_x_check:
        # Check a potential gutter starting at current_x
        # Find if any word intersects this vertical slice
        intersecting = [w for w in body_words if w["x0"] < current_x and w["x1"] > current_x]
        if not intersecting:
            # We found an empty slice! Measure how wide this empty gutter is
            left_words = [w for w in body_words if w["x1"] <= current_x]
            right_words = [w for w in body_words if w["x0"] >= current_x]
            
            if len(left_words) >= 10 and len(right_words) >= 15:
                max_left_x1 = max(w["x1"] for w in left_words)
                min_right_x0 = min(w["x0"] for w in right_words)
                gutter = min_right_x0 - max_left_x1
                if gutter >= 12.0 and gutter > max_gutter_width:
                    max_gutter_width = gutter
                    best_split = (max_left_x1 + min_right_x0) / 2.0
        current_x += x_step

    # If a clear column gutter was found, crop and extract each column separately!
    if best_split is not None and max_gutter_width >= 12.0:
        header_box = (0, 0, width, header_threshold)
        left_box = (0, header_threshold, best_split, height)
        right_box = (best_split, header_threshold, width, height)

        header_text = ""
        left_text = ""
        right_text = ""

        try:
            h_crop = page.crop(header_box)
            header_text = h_crop.extract_text(layout=True) or h_crop.extract_text() or ""
        except Exception:
            pass

        try:
            l_crop = page.crop(left_box)
            left_text = l_crop.extract_text(layout=True) or l_crop.extract_text() or ""
        except Exception:
            pass

        try:
            r_crop = page.crop(right_box)
            right_text = r_crop.extract_text(layout=True) or r_crop.extract_text() or ""
        except Exception:
            pass

        # Identify which column has Experience vs Skills/Education
        exp_keywords = [
            "experience", "work history", "employment", "professional experience"
        ]
        left_has_exp = any(kw in left_text.lower() for kw in exp_keywords)
        right_has_exp = any(kw in right_text.lower() for kw in exp_keywords)

        # We assemble the text such that the primary Experience column is fully contiguous
        # If right column has experience (typical sidebar layout), header -> right column -> left column
        if right_has_exp and not left_has_exp:
            combined = f"{header_text}\n\n{right_text}\n\n{left_text}"
        else:
            combined = f"{header_text}\n\n{left_text}\n\n{right_text}"

        return combined.strip()

    # Standard layout fallback
    return page.extract_text(layout=True) or page.extract_text() or ""
