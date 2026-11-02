import asyncio
import io
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pypdf import PdfWriter, PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from models import database_models as models
from models.schemas import LoginRequest, RegisterRequest
from routers import auth_routes, generate_routes, code_routes, interview_routes


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([models.User(id=1, email="ONE@example.com", is_verified=True),
                         models.User(id=2, email="two@example.com", is_verified=True)])
        self.db.add_all([models.Profile(user_id=1, first_name="One"), models.Profile(user_id=2, first_name="Two")])
        self.db.commit()
        app = FastAPI()
        @app.middleware("http")
        async def session(request, call_next):
            request.scope["session"] = {"user_id": 1} if request.headers.get("x-test-user") else {}
            return await call_next(request)
        app.include_router(generate_routes.router)
        app.include_router(code_routes.router)
        app.include_router(interview_routes.router)
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def test_generation_helpers_require_auth(self):
        for path in ("templates", "compile", "compile-preview", "export/docx"):
            response = self.client.get("/generate/templates") if path == "templates" else self.client.post("/generate/" + path, json={"latex": "x"})
            self.assertEqual(response.status_code, 401, path)

    def test_email_cannot_select_another_users_profile(self):
        with patch.object(generate_routes, "generate_latex_resume", return_value="latex") as generate:
            response = self.client.post("/generate/cv", headers={"x-test-user": "1"}, json={"email": "two@example.com", "jd": "job"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(generate.call_args.args[0].user_id, 1)

    def test_practice_auth_context_and_busy_status(self):
        self.assertEqual(self.client.get("/interview/questions").status_code, 401)
        self.assertEqual(self.client.post("/interview/questions", json={}).status_code, 401)
        self.assertEqual(self.client.get("/code/problems").status_code, 401)
        with patch.object(interview_routes, "get_questions", return_value=["Context question"]) as questions:
            response = self.client.post("/interview/questions", headers={"x-test-user": "1"}, json={"job_title": "Engineer", "jd": "Long job details" * 1000})
        self.assertEqual(response.status_code, 200)
        questions.assert_called_once_with(job_title="Engineer", jd="Long job details" * 1000)
        with patch.object(code_routes, "run_blocking", side_effect=HTTPException(status_code=503, detail="Service busy")):
            response = self.client.post("/code/hint", headers={"x-test-user": "1"}, json={"problem_title": "Test", "problem_description": "Details", "current_code": "", "hint_level": 1})
        self.assertEqual(response.status_code, 503)

    def test_compile_returns_pdf(self):
        buffer = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(612, 792)
        writer.write(buffer)
        with patch.object(generate_routes, "compile_latex_to_pdf", return_value=buffer.getvalue()):
            response = self.client.post("/generate/compile", headers={"x-test-user": "1"}, json={"latex": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertEqual(len(PdfReader(io.BytesIO(response.content)).pages), 1)

    def test_resume_provider_failure_returns_a_controlled_json_error(self):
        with patch.object(generate_routes, "generate_latex_resume", side_effect=RuntimeError("private provider failure")), TestClient(self.client.app, raise_server_exceptions=False) as client:
            response = client.post("/generate/ats-check", headers={"x-test-user": "1"}, json={"email": "one@example.com", "jd": "Build Python tools"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("generate", response.json()["detail"].lower())
        self.assertNotIn("private provider failure", response.text)

    def test_rejected_resume_explains_the_claims_that_need_review(self):
        from services.llm_service import UnsupportedPersonalClaims
        rejected = UnsupportedPersonalClaims(["Team leadership is absent from the profile.", "The 30% improvement is not supported."])
        with patch.object(generate_routes, "generate_latex_resume", side_effect=rejected), patch.object(generate_routes, "compile_latex_to_pdf") as compile_pdf:
            response = self.client.post("/generate/ats-check", headers={"x-test-user": "1"}, json={"email": "one@example.com", "jd": "Build tools"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("Team leadership", response.json()["detail"])
        self.assertIn("30% improvement", response.json()["detail"])
        self.assertNotIn("Add more details or try again", response.json()["detail"])
        compile_pdf.assert_not_called()

    def test_legacy_password_cannot_be_claimed_on_login(self):
        request = SimpleNamespace(session={})
        with self.assertRaises(HTTPException) as error:
            asyncio.run(auth_routes.login.__wrapped__(LoginRequest(email=" one@EXAMPLE.com ", password="new-password"), request, self.db))
        self.assertEqual(error.exception.status_code, 401)
        self.assertIsNone(self.db.get(models.User, 1).hashed_password)

    def test_short_registration_password_rejected_before_writes(self):
        with self.assertRaises(HTTPException) as error:
            asyncio.run(auth_routes.register.__wrapped__(RegisterRequest(email="new@example.com", password="short"), SimpleNamespace(), self.db))
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(self.db.query(models.User).count(), 2)
