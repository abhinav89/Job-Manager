import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cv_tailor.services import jev_job_matching as matching
from cv_tailor.services.job_search_agent import create_job_search_tools


class FakeContext:
    profile = None
    user_evidence = "I want remote work"

    def __init__(self):
        self.created_drafts = []
        self.db = None
        self.drafts = []
        self.activity = []
        self.activity_callback = self.activity.append

    def save_draft(self, kind, content, metadata):
        self.drafts.append({"type": kind, "content": content, "metadata": metadata})
        return {"id": 7}


class JevMatchingTests(unittest.TestCase):
    def test_ranking_batches_questions_and_excludes_contact_fields(self):
        jobs = [{"job_title": "Analyst", "job_description": "Some analysis work. " * 8},
                {"job_title": "Automation", "job_description": "Build Python automation. " * 8}]
        seen = {}

        def respond(request):
            seen["body"] = json.loads(request.content)
            seen["authorization"] = request.headers["Authorization"]
            answers = {}
            for name in seen["body"]["questions"]:
                index = int(name.split("_")[1])
                dim = name.split("_")[2]
                choice = {"role": ["different", "related"], "experience": ["unclear", "supported"],
                          "preferences": ["unknown", "consistent"]}[dim][index]
                answers[name] = {"type": "choice", "choice": choice, "confidence": 0.9}
            return httpx.Response(200, json={"answers": answers})

        real_client = httpx.AsyncClient
        with patch.object(matching.httpx, "AsyncClient", side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs)):
            ranked = asyncio.run(matching.rank_jobs(jobs, "Python automation", {
                "email": "private@example.com", "first_name": "Private", "mobile_no": "123",
                "skills": [{"skill_name": "Python", "is_confirmed": True}],
                "projects": [{"name": "Scripts", "description": "Python automation", "link": "https://private.example"}],
            }, "remote", "test-key"))
        self.assertEqual([job["job_title"] for job in ranked], ["Automation", "Analyst"])
        self.assertEqual(len(seen["body"]["questions"]), 6)
        serialized = json.dumps(seen["body"])
        self.assertNotIn("private@example.com", serialized)
        self.assertNotIn("https://private.example", serialized)
        self.assertEqual(seen["authorization"], "Bearer test-key")
        self.assertEqual(ranked[0]["jev_match"]["experience"], "supported")

    def test_missing_evidence_remains_unknown_even_if_model_claims_match(self):
        jobs = [{"job_title": "Engineer", "job_description": "No details"}]
        answers = {f"job_0_{dimension}": {"choice": value, "confidence": 0.9}
                   for dimension, value in {"role": "related", "experience": "supported", "preferences": "consistent"}.items()}
        real_client = httpx.AsyncClient
        with patch.object(matching.httpx, "AsyncClient", side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"answers": answers})), **kwargs)):
            result = asyncio.run(matching.rank_jobs(jobs, "engineer", None, "", "key"))
        self.assertEqual(result[0]["jev_match"]["experience"], "unclear")
        self.assertEqual(result[0]["jev_match"]["preferences"], "unknown")

    def test_one_failed_question_does_not_discard_other_judgments(self):
        jobs = [{"job_title": "Engineer", "job_description": "Build Python tools remotely. " * 8}]
        answers = {"job_0_role": {"choice": "related", "confidence": .9},
                   "job_0_experience": {"error": "question failed"},
                   "job_0_preferences": {"choice": "consistent", "confidence": .9}}
        real_client = httpx.AsyncClient
        with patch.object(matching.httpx, "AsyncClient", side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"answers": answers})), **kwargs)):
            result = asyncio.run(matching.rank_jobs(jobs, "engineer", {"skills": [{"skill_name": "Python"}]}, "remote work", "key"))
        self.assertEqual(result[0]["jev_match"], {"role": "related", "experience": "unclear", "preferences": "consistent"})

    def test_search_uses_jev_order_and_preserves_selection_order(self):
        ctx = FakeContext()
        jobs = [{"job_title": "First"}, {"job_title": "Second"}]
        ranked = [{"job_title": "Second", "jev_match": {"role": "related"}}, {"job_title": "First"}]
        with patch("cv_tailor.services.job_search_agent.configured_key", return_value="key"), \
             patch("cv_tailor.services.job_search_agent.fetch_remote_jobs", new=AsyncMock(return_value=(jobs, {"site": "ok"}))), \
             patch("cv_tailor.services.job_search_agent.rank_jobs", new=AsyncMock(return_value=ranked)) as rank:
            result = asyncio.run(create_job_search_tools(ctx)[0]("Python", preferences="remote work"))
        self.assertEqual(result["jobs"], ranked)
        self.assertEqual(json.loads(ctx.drafts[0]["content"]), ranked)
        self.assertEqual(ctx.drafts[0]["metadata"]["matching_status"], "completed")
        self.assertEqual(rank.await_args.args[3], "remote work")
        self.assertEqual([event["status"] for event in ctx.activity], ["started", "completed"])

    def test_failure_and_missing_key_keep_all_results(self):
        jobs = [{"job_title": "First"}, {"job_title": "Second"}]
        for key, expected in [("", "not_configured"), ("key", "unavailable")]:
            ctx = FakeContext()
            with patch("cv_tailor.services.job_search_agent.configured_key", return_value=key), \
                 patch("cv_tailor.services.job_search_agent.fetch_remote_jobs", new=AsyncMock(return_value=(jobs, {}))), \
                 patch("cv_tailor.services.job_search_agent.rank_jobs", new=AsyncMock(side_effect=RuntimeError("private detail"))):
                result = asyncio.run(create_job_search_tools(ctx)[0]("Python"))
            self.assertEqual(result["jobs"], jobs)
            self.assertEqual(result["matching_status"], expected)
            self.assertNotIn("private detail", json.dumps(result))
            if key:
                self.assertEqual(ctx.activity[-1]["status"], "failed")

    def test_unverified_preferences_are_not_sent_to_jev(self):
        ctx = FakeContext()
        jobs = [{"job_title": "Engineer"}]
        with patch("cv_tailor.services.job_search_agent.configured_key", return_value="key"), \
             patch("cv_tailor.services.job_search_agent.fetch_remote_jobs", new=AsyncMock(return_value=(jobs, {}))), \
             patch("cv_tailor.services.job_search_agent.rank_jobs", new=AsyncMock(return_value=jobs)) as rank:
            asyncio.run(create_job_search_tools(ctx)[0]("Python", preferences="invented preference"))
        self.assertEqual(rank.await_args.args[3], "")


if __name__ == "__main__":
    unittest.main()
