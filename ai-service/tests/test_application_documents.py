from fastapi.testclient import TestClient
import pytest


def test_saved_preparation_is_scoped_to_its_application(local_workspace):
    from cv_tailor.main import app
    w = local_workspace
    job = w.application_add({"company_name": "Acme", "job_title": "Engineer"})
    other = w.application_add({"company_name": "Other", "job_title": "Engineer"})
    expected = [w.import_draft(kind, {"content": kind}, job["id"])["id"]
                for kind in ("interview_plan", "cheat_sheet")]
    research = w.import_draft("research", {"content": "Role research.", "sources": [
        {"title": "Official role", "url": "https://example.com/job"}]}, job["id"])
    expected.append(research["id"])
    w.import_draft("interview_plan", {"content": "Other application."}, other["id"])
    w.import_draft("interview_plan", {"content": "General preparation."})
    with TestClient(app) as client:
        result = client.get(f"/api/tracker/{job['id']}/documents")
        assert result.status_code == 200
        assert {draft["id"] for draft in result.json()} == set(expected)
        assert client.get("/api/tracker/9999/documents").status_code == 404
        assert client.post(f"/api/tracker/{other['id']}/documents/{research['id']}/revise",
                           json={"content": "Wrong application."}).status_code == 404


@pytest.mark.parametrize("kind", ["interview_plan", "cheat_sheet", "research"])
def test_edit_keeps_history_sources_and_exported_content(local_workspace, kind):
    from cv_tailor.main import app
    w = local_workspace
    job = w.application_add({"company_name": "Acme", "job_title": "Engineer"})
    payload = {"content": "Original notes."}
    sources = [{"title": "Official role", "url": "https://example.com/job"}]
    if kind == "research":
        payload["sources"] = sources
    original = w.import_draft(kind, payload, job["id"], evidence=["I use Python."])
    path = f"/api/tracker/{job['id']}/documents/{original['id']}/revise"
    with TestClient(app) as client:
        headers = {"Idempotency-Key": f"edit-{kind}"}
        response = client.post(path, json={"content": "Updated notes."}, headers=headers)
        assert response.status_code == 200, response.text
        revised = response.json()
        assert revised["id"] != original["id"]
        assert revised["metadata"]["parent_id"] == original["id"]
        assert revised["metadata"]["conversation_evidence"] == ["I use Python."]
        assert revised["metadata"]["structured_content"]["content"] == "Updated notes."
        assert w.draft_get(original["id"])["content"] == "Original notes."
        assert client.post(path, json={"content": "Updated notes."}, headers=headers).json()["id"] == revised["id"]
        assert len(w.drafts_list(job["id"])) == 2
        assert client.post(path, json={"content": "Stale edit."}).status_code == 409
        if kind == "research":
            assert revised["metadata"]["sources"] == sources
            assert revised["metadata"]["structured_content"]["sources"] == sources
        assert w.application_get(job["id"])["revision"] == job["revision"]
        assert w.draft_get(revised["id"])["content"] == "Updated notes."
        assert w.export_draft(revised["id"], "text").decode() == "Updated notes."


def test_empty_and_non_document_edits_are_rejected(local_workspace, profile_payload):
    from cv_tailor.main import app
    w = local_workspace
    w.profile_save(profile_payload)
    job = w.application_add({"company_name": "Acme", "job_title": "Engineer"})
    draft = w.import_draft("interview_plan", {"content": "Original notes."}, job["id"])
    letter = w.import_draft("cover_letter", {"content": "I use Python."}, job["id"])
    with TestClient(app) as client:
        path = f"/api/tracker/{job['id']}/documents/{draft['id']}/revise"
        for content in ("", "   ", "x" * 100001):
            assert client.post(path, json={"content": content}).status_code == 422
        assert client.post(f"/api/tracker/{job['id']}/documents/{letter['id']}/revise",
                           json={"content": "Use the cover-letter editor."}).status_code == 422
        assert len(w.drafts_list(job["id"])) == 2
        assert len(client.get(f"/api/tracker/{job['id']}/documents").json()) == 1
