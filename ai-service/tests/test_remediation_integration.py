"""Opt-in checks against real containers and a dedicated Postgres test schema."""
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

from database import Base
from models import database_models as models
from routers import assistant_routes as routes
from services.code_service import run_python_code
from services.pdf_service import compile_latex_to_pdf, pdf_page_count
from services.latex_assembly import assemble_latex
from services.ats_check import ats_check
from schema_changes import PRESETS, apply_schema_changes
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
        from services.sandbox import run_isolated
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


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Requires a dedicated Postgres test database")
class PostgresTurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = "audit_" + uuid4().hex
        cls.control = create_engine(os.environ["TEST_DATABASE_URL"])
        with cls.control.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{cls.schema}"'))
        cls.engine = create_engine(os.environ["TEST_DATABASE_URL"], pool_size=2, max_overflow=0, pool_timeout=2,
            connect_args={"options": f"-c search_path={cls.schema}"})
        apply_schema_changes(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        with cls.control.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{cls.schema}" CASCADE'))
        cls.control.dispose()

    def setUp(self):
        with Session(self.engine) as db:
            user = models.User(email=uuid4().hex + "@example.com")
            db.add(user)
            db.flush()
            self.user_id = user.id
            self.conversations = []
            for _ in range(3):
                conversation = models.AssistantConversation(user_id=user.id, title="Test")
                db.add(conversation)
                db.flush()
                self.conversations.append(conversation.id)
            db.commit()
        self.request = SimpleNamespace(session={"user_id": self.user_id})

    def send(self, conversation, key, message="Hello"):
        async def execute():
            with Session(self.engine) as db:
                return await routes.send_message.__wrapped__(conversation, routes.SendMessage(content=message, request_id=key), self.request, db)
        return execute()

    def test_pool_is_free_during_external_work_and_duplicates_do_not_repeat(self):
        async def execute():
            barrier = asyncio.Event()
            started = []
            async def agent(ctx, history):
                self.assertIsNone(ctx.db)
                started.append(ctx.conversation.id)
                await barrier.wait()
                ctx.save_draft("cover_letter", "Grounded letter")
                return "Ready"
            with patch.object(routes, "run_career_agent", side_effect=agent):
                tasks = [asyncio.create_task(self.send(cid, "request")) for cid in self.conversations]
                for _ in range(100):
                    if len(started) == 3:
                        break
                    await asyncio.sleep(.01)
                self.assertEqual(len(started), 3)
                self.assertEqual(self.engine.pool.checkedout(), 0)
                with Session(self.engine) as db:
                    self.assertEqual(db.execute(text("SELECT 1")).scalar(), 1)
                for key, message in (("request", "Hello"), ("request", "Different content"), ("another", "Hello")):
                    with self.assertRaises(HTTPException) as error:
                        await self.send(self.conversations[0], key, message)
                    self.assertEqual(error.exception.status_code, 409)
                barrier.set()
                results = await asyncio.gather(*tasks)
                repeated = await self.send(self.conversations[0], "request")
                self.assertEqual(repeated, results[0])
                self.assertEqual(len(started), 3)
        asyncio.run(execute())

    def test_failed_or_cancelled_turn_does_not_publish_partial_drafts(self):
        async def execute():
            async def fail(ctx, _):
                ctx.save_draft("cover_letter", "Partial")
                raise RuntimeError("provider failed")
            with patch.object(routes, "run_career_agent", side_effect=fail), self.assertRaises(HTTPException):
                await self.send(self.conversations[0], "failed")
            started = asyncio.Event()
            async def wait(ctx, _):
                ctx.save_draft("cover_letter", "Partial")
                started.set()
                await asyncio.Event().wait()
            with patch.object(routes, "run_career_agent", side_effect=wait):
                task = asyncio.create_task(self.send(self.conversations[1], "cancelled"))
                await started.wait()
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            with Session(self.engine) as db:
                self.assertEqual(db.query(models.AssistantDraft).filter(models.AssistantDraft.conversation_id.in_(self.conversations)).count(), 0)
                states = {row.request_key: row.status for row in db.query(models.AssistantTurn).filter(models.AssistantTurn.conversation_id.in_(self.conversations))}
                self.assertEqual(states, {"failed": "failed", "cancelled": "cancelled"})
                self.assertTrue(all(c.active_request_key is None for c in db.query(models.AssistantConversation).filter(models.AssistantConversation.id.in_(self.conversations))))
        asyncio.run(execute())

    def test_upgrade_and_initialization_share_schema_and_seeds(self):
        with self.engine.begin() as connection:
            connection.execute(text("ALTER TABLE assistant_conversations DROP COLUMN active_request_key"))
        apply_schema_changes(self.engine)
        apply_schema_changes(self.engine)
        with Session(self.engine) as db:
            self.assertEqual(db.query(models.ResumePreset).count(), len(PRESETS))
            self.assertIsNone(db.get(models.AssistantConversation, self.conversations[0]).active_request_key)

    def test_final_database_failure_rolls_back_reply_and_drafts(self):
        async def agent(ctx, _):
            ctx.save_draft("cover_letter", "Staged result")
            return "Ready"
        with Session(self.engine) as db:
            def fail_draft_write(session, *_):
                if any(isinstance(row, models.AssistantDraft) for row in session.new):
                    raise RuntimeError("simulated draft persistence failure")
            event.listen(db, "before_flush", fail_draft_write)
            with patch.object(routes, "run_career_agent", side_effect=agent), self.assertRaises(HTTPException):
                asyncio.run(routes.send_message.__wrapped__(self.conversations[0], routes.SendMessage(content="Create a letter", request_id="write-failure"), self.request, db))
            event.remove(db, "before_flush", fail_draft_write)
            self.assertEqual(db.query(models.AssistantDraft).filter_by(conversation_id=self.conversations[0]).count(), 0)
            self.assertEqual(db.query(models.AssistantMessage).filter_by(conversation_id=self.conversations[0], role="assistant").count(), 0)
            self.assertEqual(db.query(models.AssistantTurn).filter_by(conversation_id=self.conversations[0], request_key="write-failure").one().status, "failed")

    def test_explicit_cancellation_rejects_late_worker_results(self):
        async def execute():
            started, release = asyncio.Event(), asyncio.Event()
            async def agent(ctx, _):
                started.set()
                await release.wait()
                ctx.save_draft("cover_letter", "Late result")
                return "Ready"
            with patch.object(routes, "run_career_agent", side_effect=agent):
                task = asyncio.create_task(self.send(self.conversations[0], "explicit-cancel"))
                await started.wait()
                with Session(self.engine) as db:
                    self.assertEqual(routes.cancel_message(self.conversations[0], "explicit-cancel", self.request, db)["status"], "cancelled")
                release.set()
                with self.assertRaises(HTTPException) as error:
                    await task
                self.assertEqual(error.exception.status_code, 409)
            with Session(self.engine) as db:
                self.assertEqual(db.query(models.AssistantDraft).filter_by(conversation_id=self.conversations[0]).count(), 0)
                self.assertEqual(db.query(models.AssistantTurn).filter_by(conversation_id=self.conversations[0], request_key="explicit-cancel").one().status, "cancelled")
        asyncio.run(execute())
