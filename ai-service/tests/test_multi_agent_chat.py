import asyncio
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from models import database_models as models
from routers import assistant_routes as routes
from services.career_agent import CareerToolContext, run_career_agent
from services.career_tools import create_career_tools
from services.job_search_agent import create_job_search_tools


class MultiAgentChatTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(models.User(id=1, email="test@example.com", _legacy_credits=0))
        self.db.commit()
        self.request = SimpleNamespace(session={"user_id": 1})
        self.cid = routes.create_conversation(routes.ConversationCreate(), self.request, self.db)["id"]
        self.conversation = self.db.get(models.AssistantConversation, self.cid)
        self.ctx = CareerToolContext(self.db, 1, self.conversation, None, None, "")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_search_stores_results_and_selection_is_scoped_to_conversation(self):
        search = create_job_search_tools(self.ctx)[0]
        jobs = [{"job_title": "Engineer", "company_name": "Example", "job_description": "Build APIs", "job_url": "https://example.com/job"}]
        with patch("services.job_search_agent.fetch_remote_jobs", new=AsyncMock(return_value=(jobs, {"Example": "ok"}))) as fetch:
            result = asyncio.run(search("Python", "", ""))
        self.assertEqual(fetch.await_args.kwargs["query"], "Python")
        self.assertEqual(result["jobs"], jobs)
        select = next(tool for tool in create_career_tools(self.ctx) if tool.__name__ == "select_search_result")
        self.assertEqual(select(1, result["search_id"])["draft"]["content"], "Build APIs")
        self.assertEqual(select(2, result["search_id"])["error"], "That result is not in the latest search.")
        other = models.AssistantConversation(user_id=1, title="Other")
        self.db.add(other)
        self.db.flush()
        other_ctx = CareerToolContext(self.db, 1, other, None, None, "")
        other_select = next(tool for tool in create_career_tools(other_ctx) if tool.__name__ == "select_search_result")
        self.assertIn("error", other_select(1, result["search_id"]))

    def test_stream_delivers_activity_before_final_and_saves_it(self):
        async def fake_agent(ctx, transcript):
            ctx.activity_callback({"tool": "search_jobs", "label": "Searching job sources", "status": "started"})
            await asyncio.sleep(0)
            ctx.activity_callback({"tool": "search_jobs", "label": "Searching job sources", "status": "completed"})
            return "Found some jobs."

        async def collect():
            response = await routes.stream_message.__wrapped__(self.cid, routes.SendMessage(content="Find jobs", request_id="stream-1"), self.request, self.db)
            return [json.loads(line) async for line in response.body_iterator]

        with patch.object(routes, "run_career_agent", side_effect=fake_agent):
            events = asyncio.run(collect())
        self.assertEqual([event["type"] for event in events], ["activity", "activity", "complete"])
        details = events[-1]["conversation"]
        activity = next(draft for draft in details["drafts"] if draft["type"] == "agent_activity")
        self.assertEqual(len(json.loads(activity["content"])), 2)
        self.assertEqual(activity["metadata"]["assistant_message_id"], details["messages"][-1]["id"])

    def test_company_research_is_used_for_both_documents_only_for_selected_job(self):
        self.ctx.profile = models.Profile(user_id=1, first_name="Alex", last_name="Example", email="test@example.com", mobile_no="")
        self.db.add(self.ctx.profile)
        self.db.flush()
        self.ctx.save_draft("job_context", "Build APIs", {"company": "Example"})
        tools = {tool.__name__: tool for tool in create_career_tools(self.ctx)}
        with patch("services.career_tools.grounded_research", return_value=("The company builds developer tools.", [{"url": "https://example.com"}])):
            tools["research_company"]("Example company")
        with patch("services.career_tools.llm_service.generate_cover_letter", return_value="Letter") as letter, \
             patch("services.career_tools.llm_service.generate_latex_resume", return_value="Latex") as resume, \
             patch("services.career_tools.compile_latex_to_pdf", return_value=b"pdf"), \
             patch("services.career_tools.pdf_page_count", return_value=1):
            tools["draft_cover_letter"]("", "")
            tools["tailor_resume"]("", "")
            self.assertIn("developer tools", letter.call_args.kwargs["instructions"])
            self.assertIn("developer tools", resume.call_args.kwargs["instructions"])
            self.ctx.save_draft("job_context", "A different role", {"company": "Other"})
            tools["draft_cover_letter"]("", "")
            self.assertNotIn("developer tools", letter.call_args.kwargs["instructions"])

    def test_career_agent_delegates_to_search_agent_and_records_tools(self):
        from google.adk.models.google_llm import Gemini
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types

        calls = []
        async def fake_model(model, request, stream=False):
            calls.append(request)
            if len(calls) == 1:
                part = types.Part(function_call=types.FunctionCall(name="job_search_agent", args={"request": "Find Python jobs"}))
            elif len(calls) == 2:
                part = types.Part(function_call=types.FunctionCall(name="search_jobs", args={"keyword": "Python", "sources": "", "job_types": ""}))
            elif len(calls) == 3:
                part = types.Part(text="Found a Python role.")
            else:
                part = types.Part(text="Here is a Python role.")
            yield LlmResponse(content=types.Content(role="model", parts=[part]))

        activity = []
        self.ctx.activity_callback = activity.append
        jobs = [{"job_title": "Python engineer", "company_name": "Example", "job_description": "Build APIs"}]
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}), patch.object(Gemini, "generate_content_async", fake_model), \
             patch("services.job_search_agent.fetch_remote_jobs", new=AsyncMock(return_value=(jobs, {"Example": "ok"}))):
            reply = asyncio.run(run_career_agent(self.ctx, [{"role": "user", "content": "Find Python jobs"}]))
        self.assertEqual(reply, "Here is a Python role.")
        self.assertIn(("search_jobs", "started"), [(item["tool"], item["status"]) for item in activity])
        self.assertIn(("search_jobs", "completed"), [(item["tool"], item["status"]) for item in activity])


if __name__ == "__main__":
    unittest.main()
