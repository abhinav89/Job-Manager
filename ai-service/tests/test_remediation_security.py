from fastapi.testclient import TestClient

def test_localhost_boundary(local_workspace):
    from cv_tailor.main import app
    with TestClient(app) as client:
        assert client.get("/api/workspace").status_code == 200
        assert client.get("/api/workspace", headers={"host": "attacker.example"}).status_code == 403
        assert client.post("/api/tracker", headers={"origin": "https://attacker.example"}, json={"company_name":"A","job_title":"B"}).status_code == 403
        assert client.get("/api/auth/me").status_code == 404
        assert client.post("/api/auth/register", json={}).status_code == 404
        assert client.get("/api/admin/users").status_code == 404
        assert client.post("/api/generate", json={}).status_code == 409
        assert client.post("/api/assistant/conversations/1/messages", json={"content":"Hi"}).status_code == 409


def test_static_navigation_receives_rsc_payload(local_workspace, tmp_path, monkeypatch):
    from cv_tailor import main
    assets = tmp_path / "assets"
    (assets / "generate").mkdir(parents=True)
    (assets / "generate/index.txt").write_text("static flight payload", encoding="utf-8")
    monkeypatch.setattr(main, "assets_dir", lambda: assets)
    with TestClient(main.app) as client:
        response = client.get("/generate/?_rsc=example", headers={"rsc": "1"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/x-component")
        assert response.text == "static flight payload"
