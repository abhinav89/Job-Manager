import base64
import os
import unittest
from unittest.mock import patch
from services.pdf_service import PDFCompilationError, compile_latex_to_pdf
from services.sandbox import SandboxUnavailable


class PdfEngineTests(unittest.TestCase):
    def test_engine_is_forwarded_only_to_isolated_compiler(self):
        for engine in ("tectonic", "xelatex"):
            with patch.dict(os.environ, {"PDF_LATEX_ENGINE": engine}), patch("services.sandbox.run_isolated", return_value={"pdf_b64": base64.b64encode(b"%PDF-test").decode()}) as run:
                self.assertEqual(compile_latex_to_pdf("latex", fast_preview=True), b"%PDF-test")
                run.assert_called_once_with("pdf", {"latex": "latex", "engine": engine}, 120)

    def test_unavailable_isolation_has_no_host_fallback(self):
        with patch("services.sandbox.run_isolated", side_effect=SandboxUnavailable("Unavailable")):
            with self.assertRaisesRegex(PDFCompilationError, "Unavailable"):
                compile_latex_to_pdf("latex")

    def test_invalid_engine_or_invalid_pdf_is_rejected(self):
        with patch.dict(os.environ, {"PDF_LATEX_ENGINE": "unknown"}):
            with self.assertRaises(PDFCompilationError):
                compile_latex_to_pdf("latex")
        with patch.dict(os.environ, {"PDF_LATEX_ENGINE": "tectonic"}), patch("services.sandbox.run_isolated", return_value={"pdf_b64": base64.b64encode(b"invalid").decode()}):
            with self.assertRaises(PDFCompilationError):
                compile_latex_to_pdf("latex")
