import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from cv_tailor.database import Base
from cv_tailor.models import database_models as models
from cv_tailor.routers import assistant_routes as routes
from cv_tailor.services.career_agent import CareerToolContext
from cv_tailor.services.career_tracker_tools import create_tracker_tools


class CareerTrackerTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([models.Workspace(id=1),
                         models.JobApplication(id=7, workspace_id=1, company_name="A", job_title="Engineer", status="Interview")])
        self.db.commit()
        self.request = SimpleNamespace(session={"workspace_id": 1})
        info = routes.create_conversation(routes.ConversationCreate(), self.request, self.db)
        self.conversation = self.db.get(models.AssistantConversation, info["id"])
        self.ctx = CareerToolContext(self.db, 1, self.conversation, None, None, "I built workflows")
        self.tools = {tool.__name__: tool for tool in create_tracker_tools(self.ctx, lambda _: ("A job description", "A"), lambda _: "Assessment")}

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def confirm(self, draft):
        self.db.commit()
        return routes.confirm_tracker_action(self.conversation.id, draft["id"], self.request, self.db)

    def test_add_requires_details_and_confirmation_and_links_conversation(self):
        add = self.tools["propose_add_application"]
        self.assertIn("error", add("A", "Engineer", "Details", ""))
        draft = add("A", "Engineer", "Details", "unknown")["draft"]
        self.assertEqual(self.db.query(models.JobApplication).count(), 1)
        result = self.confirm(draft)
        job = self.db.get(models.JobApplication, result["conversation"]["job_id"])
        self.assertEqual(job.job_source, "unknown")
        with self.assertRaises(HTTPException):
            self.confirm(draft)

    def test_archive_is_reversible_and_does_not_change_status(self):
        propose = self.tools["propose_application_change"]
        self.assertIn("error", propose(8, "archive"))
        draft = propose(7, "archive")["draft"]
        self.assertFalse(self.db.get(models.JobApplication, 7).is_archived)
        self.confirm(draft)
        self.assertTrue(self.db.get(models.JobApplication, 7).is_archived)
        self.assertEqual(self.db.get(models.JobApplication, 7).status, "Interview")
        self.confirm(propose(7, "restore")["draft"])
        self.assertFalse(self.db.get(models.JobApplication, 7).is_archived)

    def test_delete_needs_explicit_confirmation(self):
        self.assertIn("error", self.tools["propose_application_change"](99, "delete"))
        draft = self.tools["propose_application_change"](7, "delete")["draft"]
        self.assertIsNotNone(self.db.get(models.JobApplication, 7))
        self.confirm(draft)
        self.assertIsNone(self.db.get(models.JobApplication, 7))

    def test_fit_uses_confirmed_profile_and_conversation_and_saves_result(self):
        self.ctx.profile = object()
        serialized = SimpleNamespace(model_dump_json=lambda: '{"skills":["Python"]}')
        prompts = []
        tools = {tool.__name__: tool for tool in create_tracker_tools(self.ctx, lambda _: ("Job requirements", "A"), lambda prompt: prompts.append(prompt) or "Supported: Python")}
        with patch("cv_tailor.services.career_tracker_tools.verify_personal_claims"), patch("cv_tailor.services.career_tracker_tools.db_profile_to_schema", return_value=serialized) as profile:
            result = tools["analyze_job_fit"]()
        profile.assert_called_with(self.ctx.profile, confirmed_skills_only=True)
        self.assertEqual(result["draft"]["type"], "job_fit")
        self.assertIn("I built workflows", prompts[0])
        self.assertIn("lack of evidence is not a known gap", prompts[0])

    def test_failed_fit_does_not_create_a_fake_result(self):
        self.ctx.profile = object()
        serialized = SimpleNamespace(model_dump_json=lambda: "{}")
        def fail(_):
            raise RuntimeError("provider unavailable")
        tools = {tool.__name__: tool for tool in create_tracker_tools(self.ctx, lambda _: ("Job requirements", "A"), fail)}
        with patch("cv_tailor.services.career_tracker_tools.db_profile_to_schema", return_value=serialized):
            result = tools["analyze_job_fit"]()
        self.assertEqual(result["status"], "error")
        self.assertIsNone(self.ctx.latest_draft("job_fit"))

    def test_fit_rejects_scores_and_apply_skip_verdicts(self):
        self.ctx.profile = object()
        serialized = SimpleNamespace(model_dump_json=lambda: "{}")
        for text in ("Fit: 80%", "Overall rating: 8/10", "Match score: 90", "**Verdict:** Apply", "Recommendation: skip"):
            with self.subTest(text=text), patch("cv_tailor.services.career_tracker_tools.db_profile_to_schema", return_value=serialized), patch("cv_tailor.services.career_tracker_tools.verify_personal_claims"):
                tools = {tool.__name__: tool for tool in create_tracker_tools(self.ctx, lambda _: ("Job requirements", "A"), lambda _: text)}
                self.assertEqual(tools["analyze_job_fit"]()["status"], "error")
                self.assertIsNone(self.ctx.latest_draft("job_fit"))

    def test_delete_linked_application_also_deletes_conversation(self):
        self.conversation.job_id = 7
        self.db.commit()
        draft = self.tools["propose_application_change"](7, "delete")["draft"]
        conversation_id = self.conversation.id
        result = self.confirm(draft)
        self.assertTrue(result["conversation_deleted"])
        self.assertIsNone(self.db.get(models.JobApplication, 7))
        self.assertIsNone(self.db.get(models.AssistantConversation, conversation_id))


if __name__ == "__main__":
    unittest.main()
