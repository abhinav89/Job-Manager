from fastapi.testclient import TestClient

def test_cli_and_api_share_records(local_workspace, profile_payload):
    from cv_tailor.main import app
    w=local_workspace
    w.profile_save(profile_payload)
    job=w.application_add({"company_name":"Acme","job_title":"Developer"})
    with TestClient(app) as client:
        assert client.get("/api/tracker").json()[0]["id"] == job["id"]
        response=client.patch(f"/api/tracker/{job['id']}",json={"status":"Interview","revision":1})
        assert response.status_code == 200, response.text
        assert w.application_get(job["id"])["status"] == "Interview"
        assert client.patch(f"/api/tracker/{job['id']}",json={"status":"Offer","revision":1}).status_code == 409
        conversation=client.post("/api/assistant/conversations",json={"job_id":job["id"]}).json()
        w.import_draft("cover_letter",{"content":"I use Python."},job["id"])
        detail=client.get(f"/api/assistant/conversations/{conversation['id']}").json()
        assert detail["drafts"][0]["type"] == "cover_letter"
