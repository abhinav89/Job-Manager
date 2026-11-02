"""Exercise the real GenAI SDK serializer without paid network requests."""
import json
import unittest
from unittest.mock import patch

import httpx
from google import genai

from models.ai_responses import ResumeContent
from services import llm_service


class GeminiSchemaTransportTests(unittest.TestCase):
    def test_strict_nested_resume_schema_uses_the_json_schema_wire_field(self):
        seen = []
        fixture = {"summary": "Python developer", "experience": [], "projects": [], "skills": [], "certifications": ""}

        def respond(request):
            config = json.loads(request.content)["generationConfig"]
            seen.append(config)
            if "responseSchema" in config:
                return httpx.Response(400, json={"error": {"code": 400, "status": "INVALID_ARGUMENT",
                    "message": 'Invalid JSON payload received. Unknown name "additional_properties" at generation_config.response_schema: Cannot find field.'}})
            self.assertEqual(config["responseJsonSchema"], ResumeContent.model_json_schema())
            self.assertFalse(config["responseJsonSchema"]["additionalProperties"])
            self.assertFalse(config["responseJsonSchema"]["$defs"]["ResumeExperience"]["additionalProperties"])
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"text": json.dumps(fixture)}]}}]})

        with genai.Client(api_key="fixture-key", http_options={"client_args": {"transport": httpx.MockTransport(respond)}}) as client:
            with patch.object(llm_service, "_get_client", return_value=client):
                result = llm_service.complete_structured("Fixture resume", ResumeContent, provider="gemini")
        self.assertEqual(result.model_dump(), fixture)
        self.assertEqual(len(seen), 1)
