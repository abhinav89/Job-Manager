"""Opt-in checks against real containers and native document execution."""
import asyncio
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from pypdf import PdfReader
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import Session

from cv_tailor.database import Base
from cv_tailor.models import database_models as models
from cv_tailor.routers import assistant_routes as routes
from cv_tailor.services.code_service import run_python_code
from cv_tailor.services.pdf_service import compile_latex_to_pdf, pdf_page_count
from cv_tailor.services.latex_assembly import assemble_latex
from cv_tailor.services.ats_check import ats_check
from cv_tailor.schema_changes import PRESETS, apply_schema_changes
from test_latex_assembly import make_profile


@unittest.skipUnless(os.getenv("RUN_SANDBOX_TESTS") == "1", "Requires provisioned sandbox images")
class SandboxIntegrationTests(unittest.TestCase):
    def setUp(self):
        backend = patch.dict(os.environ, {"EXECUTION_BACKEND": "docker"})
        backend.start()
        self.addCleanup(backend.stop)

    def test_python_cannot_access_host_environment_files_or_network(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as sentinel:
            sentinel.write("host-only-sentinel")
            path = sentinel.name
        try:
            code = f'''import os, socket
from pathlib import Path
print(os.getenv("AUDIT_HOST_SECRET"))
print(Path({path!r}).exists())
try:
    socket.create_connection(("1.1.1.1", 80), timeout=.3)
    print("NETWORK ALLOWED")
except OSError:
    print("NETWORK DENIED")
try:
    Path("/opt/worker.py").write_text("modified")
    print("WRITE ALLOWED")
except OSError:
    print("WRITE DENIED")
print(os.geteuid())
print(Path("/sys/fs/cgroup/pids.max").read_text().strip())
print(Path("/sys/fs/cgroup/memory.max").read_text().strip())
'''
            with patch.dict(os.environ, {"AUDIT_HOST_SECRET": "must-not-leak"}):
                result = run_python_code(code)
            self.assertEqual(result["stdout"].splitlines(), ["None", "False", "NETWORK DENIED", "WRITE DENIED", "65534", "32", "536870912"])
        finally:
            Path(path).unlink()

    def test_timeout_removes_child_processes_and_output_is_bounded(self):
        from cv_tailor.services.sandbox import run_isolated
        result = run_isolated("python", {"code": "import os,time\nif os.fork() == 0: time.sleep(60)\ntime.sleep(60)"}, 1)
        self.assertTrue(result["timed_out"])
        result = run_python_code("print('x' * 2000000)")
        self.assertLessEqual(len(result["stdout"]), 1024 * 1024)
        remaining = subprocess.run(["docker", "ps", "--all", "--filter", "ancestor=cv-tailor-python:1", "--format", "{{.ID}}"], capture_output=True, text=True, check=True)
        self.assertEqual(remaining.stdout.strip(), "")

    def test_real_pdf_matrix_and_literal_characters(self):
        profile = make_profile(first_name="Jane {", last_name="Doe}", email="jane_test@example.com",
            education=[{"school_name": "School & College", "course": "Course #1", "location": "Remote", "date_range": "2020 - 2024", "description": "Study $ and %"}])
        content = {"summary": "Engineer building reliable applications with Python & SQL. Literal {braces}, #tags, 50% and $ values.",
            "experience": [{"company": "Acme & Co", "location": "Remote", "title": "Engineer", "date": "2024 - 2026", "bullets": ["Built reliable reporting tools and automated weekly tasks."]}],
            "projects": [{"name": "Project_One", "tech": "Python & SQL", "date": "2026", "bullets": ["Built a reporting application."]}],
            "skills": {"Tools": "Python, SQL"}, "certifications": "Certificate #1"}
        for engine in ("tectonic", "xelatex"):
            for preset in PRESETS:
                for template in ("classic", "modern"):
                    for optional in (True, False):
                        with self.subTest(engine=engine, preset=preset["slug"], template=template, optional=optional), patch.dict(os.environ, {"PDF_LATEX_ENGINE": engine}):
                            data = content if optional else {**content, "projects": [], "certifications": ""}
                            latex = assemble_latex(profile, data, template, preset["section_order"])
                            pdf = compile_latex_to_pdf(latex)
                            self.assertEqual(pdf_page_count(pdf), 1)
                            result = ats_check(pdf, preset["section_order"])
                            self.assertTrue(result["pass"], result["warnings"])
                            extracted = " ".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
                            for literal in ("braces", "Acme & Co", "Project_One" if optional else "Python"):
                                self.assertIn(literal, extracted)

    def test_raw_tex_cannot_read_a_host_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as sentinel:
            sentinel.write("host-secret-never-in-pdf")
            path = sentinel.name
        try:
            # The same absolute path would be readable by a host compiler.
            latex = r"\documentclass{article}\begin{document}\IfFileExists{" + Path(path).as_posix() + r"}{\input{" + Path(path).as_posix() + r"}}{Host file unavailable}\end{document}"
            for engine in ("tectonic", "xelatex"):
                with patch.dict(os.environ, {"PDF_LATEX_ENGINE": engine}):
                    pdf = compile_latex_to_pdf(latex)
                    self.assertNotIn("host-secret-never-in-pdf", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())
        finally:
            Path(path).unlink()
