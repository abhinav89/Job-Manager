import io
import json
import socket
import unittest
import asyncio
import threading
import sys
from types import SimpleNamespace
from unittest.mock import patch, Mock, AsyncMock

from models.ai_responses import ClaimVerification
from services import llm_service
from services.conversation_evidence import LIMIT, select_user_evidence
from services.latex_assembly import _escape_latex, assemble_latex
from services.safe_fetch import UnsafeURL, public_addresses, fetch_job_text
from services.spot_edit_service import _grounding, rewrite_blocks, verify_grounded_rewrite
from services.ats_check import ats_check
from test_latex_assembly import make_profile, EMPTY_AI_CONTENT
from test_spot_edit_service import make_profile as spot_profile, make_request


class WorkerAdmissionTests(unittest.TestCase):
    def test_cancelled_awaits_keep_capacity_until_the_work_finishes(self):
        from fastapi import HTTPException
        from services.external_work import run_blocking
        release = threading.Event()
        all_started = threading.Event()
        guard = threading.Lock()
        started = 0
        finished = 0
        def work():
            nonlocal started, finished
            with guard:
                started += 1
                if started == 8:
                    all_started.set()
            release.wait(10)
            with guard:
                finished += 1
        async def execute():
            tasks = [asyncio.create_task(run_blocking(work)) for _ in range(8)]
            try:
                for _ in range(200):
                    if all_started.is_set():
                        break
                    await asyncio.sleep(.01)
                self.assertTrue(all_started.is_set())
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                with self.assertRaises(HTTPException) as error:
                    await run_blocking(lambda: None)
                self.assertEqual(error.exception.status_code, 503)
            finally:
                release.set()
                await asyncio.gather(*tasks, return_exceptions=True)
            for _ in range(200):
                if finished == 8:
                    break
                await asyncio.sleep(.01)
            self.assertEqual(finished, 8)
            self.assertEqual(await run_blocking(lambda: "available"), "available")
        asyncio.run(execute())


class FetchTests(unittest.TestCase):
    def test_nonpublic_and_mapped_addresses_are_rejected(self):
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "::ffff:127.0.0.1", "fc00::1", "0.0.0.0", "224.0.0.1"):
            with self.subTest(address=address), patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, "", (address, 80))]):
                with self.assertRaises(UnsafeURL):
                    public_addresses("example.com", 80)

    def test_all_resolved_addresses_must_be_public(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 0, "", (ip, 80)) for ip in ("1.1.1.1", "127.0.0.1")]):
            with self.assertRaises(UnsafeURL):
                public_addresses("example.com", 80)

    def test_invalid_scheme_and_credentials_never_connect(self):
        with patch("socket.create_connection") as connect:
            for url in ("file:///etc/passwd", "http://user:password@example.com/", "http://example.com\r\nX-Test:foo"):
                with self.assertRaises(UnsafeURL):
                    fetch_job_text(url)
            connect.assert_not_called()

    def test_public_connection_is_pinned_and_redirect_is_revalidated(self):
        response = Mock(status=302)
        response.getheader.return_value = "http://127.0.0.1/metadata"
        connection = Mock()
        connection.getresponse.return_value = response
        with patch("services.safe_fetch.public_addresses", side_effect=[["1.1.1.1"], UnsafeURL("private")]), patch("http.client.HTTPConnection", return_value=connection), patch("socket.create_connection") as connect:
            with self.assertRaisesRegex(UnsafeURL, "private"):
                fetch_job_text("http://example.com")
            connect.assert_called_once_with(("1.1.1.1", 80), timeout=unittest.mock.ANY)
            connection.close.assert_called_once()

    def test_response_bound_and_visible_text(self):
        response = Mock(status=200)
        response.getheader.return_value = "identity"
        connection = Mock()
        connection.getresponse.return_value = response
        with patch("services.safe_fetch.public_addresses", return_value=["1.1.1.1"]), patch("http.client.HTTPConnection", return_value=connection), patch("socket.create_connection"):
            response.read1.side_effect = [b"<script>secret instruction</script><main>Job details</main>", b""]
            self.assertEqual(fetch_job_text("http://example.com"), "Job details")
            response.read1.side_effect = [b"12345"]
            with patch("services.safe_fetch.MAX_BYTES", 4), self.assertRaisesRegex(UnsafeURL, "size limit"):
                fetch_job_text("http://example.com")


class EvidenceTests(unittest.TestCase):
    def test_latest_user_correction_survives_both_old_limits(self):
        history = [{"role": "user", "content": "I used Java."}, {"role": "user", "content": "old " * 7000},
                   {"role": "assistant", "content": "Invented experience"},
                   {"role": "user", "content": "Correction: I used Python, not Java."}]
        selected = select_user_evidence(history)
        self.assertLessEqual(len(selected), LIMIT)
        self.assertIn("Correction: I used Python", selected)
        self.assertNotIn("Invented experience", selected)
        self.assertNotIn("I used Java.", selected)

    def test_oversized_turn_is_explicitly_truncated(self):
        selected = select_user_evidence([{"role": "user", "content": "x" * 20000 + " latest fact"}])
        self.assertLessEqual(len(selected), LIMIT)
        self.assertIn("truncated", selected)
        self.assertTrue(selected.endswith("latest fact"))

    def test_generation_and_verification_receive_the_identical_selected_window(self):
        selected = select_user_evidence([{"role": "user", "content": "old " * 7000},
            {"role": "user", "content": "recent " * 1600}, {"role": "user", "content": "Correction: I use Python."}])
        prompts = []
        replies = iter(['{"summary":"Python developer","experience":[],"projects":[],"skills":[],"certifications":""}', '{"supported":true,"unsupported":[]}'])
        def completion(prompt):
            prompts.append(prompt)
            return next(replies)
        llm_service.generate_latex_resume(make_profile(), "Developer", conversation_evidence=selected, complete_fn=completion)
        self.assertEqual(len(prompts), 2)
        self.assertTrue(all(selected in prompt for prompt in prompts))


class ScraperTests(unittest.TestCase):
    def test_search_encodes_reserved_characters_and_keeps_missing_description_empty(self):
        from services import job_scraper_service as scraper
        html = '<div class="jobpost-cat-box"><h4>Remote engineer</h4><a href="/jobseekers/info/1">View</a></div>'
        with patch.object(scraper, "_httpx_get", new=AsyncMock(return_value=html)) as fetch:
            jobs, status = asyncio.run(scraper.fetch_onlinejobs_ph("C++ & Python"))
        self.assertIn("jobkeyword=C%2B%2B+%26+Python", fetch.await_args.args[0])
        self.assertEqual(status, "ok")
        self.assertEqual(jobs[0]["job_description"], "")

    def test_browser_fetches_respect_the_concurrency_bound(self):
        from services import job_scraper_service as scraper
        async def execute():
            release, ready = asyncio.Event(), asyncio.Event()
            active = maximum = 0
            async def fetch(*args, **kwargs):
                nonlocal active, maximum
                active += 1
                maximum = max(maximum, active)
                if active == 2:
                    ready.set()
                await release.wait()
                active -= 1
                return SimpleNamespace(body=b"Job details")
            fake = SimpleNamespace(StealthyFetcher=SimpleNamespace(async_fetch=fetch))
            with patch.dict(sys.modules, {"scrapling.fetchers": fake}), patch.object(scraper, "_browser_slots", asyncio.Semaphore(2)):
                tasks = [asyncio.create_task(scraper.scrape_scrapling("https://example.com")) for _ in range(5)]
                try:
                    await asyncio.wait_for(ready.wait(), 2)
                    self.assertEqual(active, 2)
                finally:
                    release.set()
                self.assertEqual(await asyncio.gather(*tasks), ["Job details"] * 5)
            self.assertEqual(maximum, 2)
        asyncio.run(execute())


class StructuredTests(unittest.TestCase):
    def test_full_schema_and_no_fence_slicing(self):
        valid = '{"supported":true,"unsupported":[]}'
        self.assertTrue(llm_service.complete_structured("prompt", ClaimVerification, complete_fn=lambda _: valid).supported)
        for raw in ("```json\n" + valid + "\n```", '{"supported":"true","unsupported":[]}', '{"supported":true}', "", valid[:-1]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                llm_service.complete_structured("prompt", ClaimVerification, complete_fn=lambda _: raw)

    def test_gemini_schema_and_finish_reason_are_checked(self):
        response = SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")], text='{"supported":true,"unsupported":[]}')
        client = Mock()
        client.models.generate_content.return_value = response
        with patch.object(llm_service, "_get_client", return_value=client):
            self.assertTrue(llm_service.complete_structured("prompt", ClaimVerification, provider="gemini").supported)
            config = client.models.generate_content.call_args.kwargs["config"]
            self.assertIsNone(config.response_schema)
            self.assertEqual(config.response_json_schema, ClaimVerification.model_json_schema())
            response.candidates[0].finish_reason = "MAX_TOKENS"
            with self.assertRaises(ValueError):
                llm_service.complete_structured("prompt", ClaimVerification, provider="gemini")

    def test_openai_refusal_is_not_a_valid_result(self):
        client = Mock()
        client.chat.completions.parse.return_value = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(refusal="refused", parsed=None))])
        with patch.object(llm_service, "_get_client", return_value=client), self.assertRaises(ValueError):
            llm_service.complete_structured("prompt", ClaimVerification, provider="openai")


class StagedAgentTests(unittest.TestCase):
    def test_native_runner_uses_plain_staged_tools_and_role_preserving_history(self):
        import asyncio
        from google.adk.models.google_llm import Gemini
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types
        from services.career_agent import CareerToolContext, run_career_agent
        requests = []
        async def model(_, request, stream=False):
            requests.append(request)
            part = types.Part(function_call=types.FunctionCall(name="research_company", args={"query": "Acme company"})) if len(requests) == 1 else types.Part(text="Company research is available.")
            yield LlmResponse(content=types.Content(role="model", parts=[part]))
        context = CareerToolContext(None, 1, SimpleNamespace(id=1, job_id=None), None, None, "Research Acme", staged=True)
        history = [{"role": "user", "content": "Research Acme"}, {"role": "assistant", "content": "Which topic?"}, {"role": "user", "content": "Its product."}]
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fixture"}), patch.object(Gemini, "generate_content_async", model), patch("services.career_tools.grounded_research", return_value=("Acme builds tools.", [{"title": "Acme", "url": "https://example.com"}])):
            result = asyncio.run(run_career_agent(context, history))
        self.assertEqual(result, "Company research is available.")
        self.assertEqual(context.created_drafts[0].type, "research")
        self.assertIsNone(context.db)
        turns = [(item.role, " ".join(part.text or "" for part in item.parts)) for item in requests[0].contents]
        self.assertIn(("model", "Which topic?"), turns)
        self.assertEqual(sum(text == "Its product." for _, text in turns), 1)

    def test_failed_parallel_tools_only_discard_their_own_drafts(self):
        import time
        from concurrent.futures import ThreadPoolExecutor
        from services.career_agent import CareerToolContext
        ctx = CareerToolContext(None, 1, SimpleNamespace(id=1, job_id=None), None, None, "", staged=True)
        def execute(index):
            def action():
                ctx.save_draft("research", str(index))
                time.sleep(.002)
                return {"error": "failed"} if index % 2 else {"status": "success"}
            return ctx.run_action(action)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(execute, range(20)))
        self.assertCountEqual([draft.content for draft in ctx.created_drafts], [str(index) for index in range(0, 20, 2)])


class GroundingTests(unittest.TestCase):
    def test_nonnumeric_claims_and_reassigned_metrics_have_factual_gate(self):
        for claim in ("Led the engineering department", "Managed 20 employees"):
            with patch("services.spot_edit_service.complete_structured", return_value=ClaimVerification(supported=False, unsupported=["Not supported by source"])) as verify:
                with self.assertRaisesRegex(ValueError, "unsupported personal claims"):
                    verify_grounded_rewrite(claim, "Served 20 clients in a support role.")
                self.assertIn("Served 20 clients", verify.call_args.args[0])

    def test_existing_block_is_not_numeric_evidence(self):
        request = make_request(instruction="Make concise", blocks=[{"id": "bullet:0", "kind": "bullet", "section": "Experience", "text": "Led 50 people", "entry_title": "AgentGenius AI", "entry_subtitle": "AI Engineer"}])
        with patch("services.spot_edit_service.complete", return_value=json.dumps({"blocks": [{"id": "bullet:0", "text": "Managed 50 people", "note": ""}]})):
            with self.assertRaisesRegex(ValueError, "unsupported number"):
                rewrite_blocks(spot_profile(), request)

    def test_unconfirmed_skills_and_dates_are_excluded(self):
        profile = spot_profile()
        profile.skills.append(SimpleNamespace(skill_name="Unconfirmed", is_confirmed=False))
        profile.experience[0].date_range = "2023 - 2025"
        summary = make_request(blocks=[{"id": "summary", "kind": "summary", "section": "Summary", "text": "Engineer"}]).blocks[0]
        evidence = _grounding(profile, summary)
        self.assertNotIn("Unconfirmed", evidence)
        self.assertNotIn("2025", evidence)
        self.assertIn("SMB clients", evidence)

    def test_duplicate_company_uses_role_and_ambiguous_matches_fail(self):
        profile = spot_profile()
        profile.experience.append(SimpleNamespace(company="AgentGenius AI", job_title="Support Engineer", description="Resolved 100 tickets"))
        block = make_request().blocks[0]
        self.assertNotIn("100 tickets", _grounding(profile, block))
        profile.experience.append(SimpleNamespace(company="AgentGenius AI Studio", job_title=block.entry_subtitle, description="Unrelated achievement"))
        self.assertNotIn("Unrelated achievement", _grounding(profile, block))
        block.entry_subtitle = None
        with self.assertRaisesRegex(ValueError, "More than one"):
            _grounding(profile, block)


class LatexTests(unittest.TestCase):
    def test_escaping_is_lossless_for_literal_braces(self):
        self.assertEqual(_escape_latex(None), "")
        self.assertEqual(_escape_latex(r"{A&B} \ %_"), r"\{A\&B\} \textbackslash{} \%\_")

    def test_preset_order_omits_optional_sections(self):
        doc = assemble_latex(make_profile(), {**EMPTY_AI_CONTENT, "summary": "Literal {braces} & value"}, section_order=["Summary", "Experience", "Technical Skills", "Education", "Certifications"])
        self.assertLess(doc.index(r"\section{Experience}"), doc.index(r"\section{Education}"))
        self.assertNotIn(r"\section{Projects}", doc)
        self.assertIn(r"Literal \{braces\} \& value", doc)

    def test_ats_fallback_warning_does_not_fail_valid_headings(self):
        from reportlab.pdfgen import canvas
        out = io.BytesIO()
        pdf = canvas.Canvas(out)
        for y, line in enumerate(["Summary", "Experienced engineer building useful applications and reporting systems.", "Experience", "Worked on reliable tools and clear documentation.", "Technical Skills", "Python and SQL", "Education", "University"]):
            pdf.drawString(30, 750-y*20, line)
        pdf.save()
        with patch("services.ats_check.shutil.which", return_value=None):
            result = ats_check(out.getvalue(), ["Summary", "Experience", "Technical Skills", "Education", "Projects", "Certifications"])
            self.assertTrue(result["pass"], result["warnings"])
            wrong = ats_check(out.getvalue(), ["Education", "Experience", "Summary"])
            self.assertFalse(wrong["pass"])


class ExportTests(unittest.TestCase):
    def test_docx_contains_multiline_heading_values_without_color_names(self):
        from docx import Document
        from services.docx_service import convert_latex_to_docx
        source = r"""\begin{document}
\section{Experience}
\resumeSubheading
{\textbf{Acme \& Co}}{Remote}
{Engineer}{2024 - 2026}
\small{\color{textColor}Built reliable reports.}
\end{document}"""
        doc = Document(io.BytesIO(convert_latex_to_docx(source)))
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        self.assertIn("Acme & Co | Remote | Engineer | 2024 - 2026", text)
        self.assertIn("Built reliable reports.", text)
        self.assertNotIn("textColor", text)

    def test_cheat_sheet_pdf_removes_markdown_markers(self):
        from services.career_documents import cheat_sheet_pdf
        from pypdf import PdfReader
        pdf = cheat_sheet_pdf("# Preparation\n**Supported result**\n~~Old emphasis~~\n[Company](https://example.com)\n```text\nPlain notes\n```")
        text = PdfReader(io.BytesIO(pdf)).pages[0].extract_text()
        self.assertIn("Supported result", text)
        self.assertIn("https://example.com", text)
        for marker in ("**", "~~", "```", "[Company]", "# Preparation"):
            self.assertNotIn(marker, text)


class ProfilePersistenceTests(unittest.TestCase):
    def test_profile_id_template_and_education_dates_survive_older_client_save(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from database import Base
        from models import database_models as models
        from models.schemas import UserProfile
        from routers.database_routes import save_profile_data
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(models.User(id=1, email="jane@example.com"))
            profile = models.Profile(user_id=1, preferred_template="modern")
            db.add(profile)
            db.flush()
            original_id = profile.id
            db.add(models.Education(profile_id=profile.id, school_name="University", course="Engineering", location="Remote", date_range="2020 - 2024"))
            db.commit()
            incoming = UserProfile(first_name="Jane", last_name="Doe", mobile_no="", email="jane@example.com",
                education=[{"school_name": "University", "course": "Engineering", "location": "Remote"}], experience=[], projects=[], skills=[])
            with patch("routers.database_routes.resolve_preset", return_value=None):
                save_profile_data(db, 1, incoming)
            stored = db.query(models.Profile).filter_by(user_id=1).one()
            self.assertEqual(stored.id, original_id)
            self.assertEqual(stored.preferred_template, "modern")
            self.assertEqual(stored.education[0].date_range, "2020 - 2024")
        engine.dispose()

    def test_job_serializer_does_not_fetch_deferred_pdf_bytes(self):
        from sqlalchemy import create_engine, inspect, event
        from sqlalchemy.orm import Session
        from database import Base
        from models import database_models as models
        from routers.tracker_routes import serialize_job
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(models.User(id=1, email="jane@example.com"))
            db.add(models.JobApplication(user_id=1, company_name="Acme", job_title="Engineer", pdf_data=b"PDF bytes"))
            db.commit()
            db.expunge_all()
            job = db.query(models.JobApplication).one()
            self.assertIn("pdf_data", inspect(job).unloaded)
            statements = []
            def record(*args):
                statements.append(args[2])
            event.listen(engine, "before_cursor_execute", record)
            self.assertTrue(serialize_job(job)["has_pdf"])
            self.assertEqual(statements, [])
            event.remove(engine, "before_cursor_execute", record)
        engine.dispose()
